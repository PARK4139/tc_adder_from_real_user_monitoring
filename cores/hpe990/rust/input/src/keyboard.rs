use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    fs,
    mem::size_of,
    path::PathBuf,
    thread,
    time::{Duration, SystemTime, UNIX_EPOCH},
};

#[repr(C)]
#[derive(Copy, Clone)]
struct Keyboard {
    vk: u16,
    scan: u16,
    flags: u32,
    time: u32,
    extra: usize,
}
#[repr(C)]
union Data {
    keyboard: Keyboard,
    padding: [u64; 4],
}
#[repr(C)]
struct Input {
    kind: u32,
    data: Data,
}
#[repr(C)]
#[derive(Default)]
struct Message {
    hwnd: isize,
    message: u32,
    wparam: usize,
    lparam: isize,
    time: u32,
    point: [i32; 2],
    private: u32,
}
#[link(name = "user32")]
extern "system" {
    fn SendInput(count: u32, inputs: *const Input, size: i32) -> u32;
    fn GetAsyncKeyState(vk: i32) -> i16;
    fn GetAncestor(hwnd: isize, flags: u32) -> isize;
    fn SetForegroundWindow(hwnd: isize) -> i32;
    fn GetForegroundWindow() -> isize;
    fn GetWindowThreadProcessId(hwnd: isize, pid: *mut u32) -> u32;
    fn AttachThreadInput(from: u32, to: u32, attach: i32) -> i32;
    fn SetFocus(hwnd: isize) -> isize;
    fn GetFocus() -> isize;
    fn PeekMessageW(msg: *mut Message, hwnd: isize, min: u32, max: u32, remove: u32) -> i32;
    fn GetThreadDesktop(thread: u32) -> isize;
    fn IsIconic(hwnd: isize) -> i32;
    fn ShowWindow(hwnd: isize, command: i32) -> i32;
}
#[link(name = "kernel32")]
extern "system" {
    fn GetCurrentThreadId() -> u32;
    fn GetCurrentProcessId() -> u32;
    fn ProcessIdToSessionId(pid: u32, session: *mut u32) -> i32;
}

fn note(trace: &mut Vec<Value>, mut event: Value) {
    event["observed_unix_ms"] = json!(SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64);
    trace.push(event);
}

fn reject_held_keys(all: &BTreeSet<u16>, pressed: impl Fn(i32) -> bool) -> Result<(), String> {
    for key in [0x10, 0x11, 0x12, 0x5b, 0x5c] {
        if pressed(key) {
            return Err("User modifier already held".into());
        }
    }
    for key in all {
        if pressed(*key as i32) {
            return Err("User target key already held".into());
        }
    }
    if (1..=254).any(pressed) {
        return Err("User input already held".into());
    }
    Ok(())
}

fn send(vk: u16, up: bool) -> Result<(), String> {
    let extended = matches!(vk, 0x21..=0x28 | 0x2d..=0x2e | 0x5b);
    let input = Input {
        kind: 1,
        data: Data {
            keyboard: Keyboard {
                vk,
                scan: 0,
                flags: (if up { 2 } else { 0 }) | u32::from(extended),
                time: 0,
                extra: 0,
            },
        },
    };
    if unsafe { SendInput(1, &input, size_of::<Input>() as i32) } != 1 {
        return Err("SendInput rejected (desktop/UIPI/focus must be inspected)".into());
    }
    Ok(())
}

struct Held(Vec<u16>, PathBuf);
struct Attached(Vec<(u32, u32)>);
impl Drop for Attached {
    fn drop(&mut self) {
        for (from, to) in self.0.drain(..).rev() {
            unsafe {
                AttachThreadInput(from, to, 0);
            }
        }
    }
}
impl Drop for Held {
    fn drop(&mut self) {
        for key in self.0.drain(..).rev() {
            if send(key, true).is_ok() {
                let _ = fs::remove_file(self.1.join(format!("{key}.held")));
            }
        }
    }
}

pub fn execute(request: &Value) -> Value {
    let mut sent = 0;
    let mut trace = Vec::new();
    let mut all = BTreeSet::new();
    let result = (|| -> Result<(), String> {
        let sequence = request["keys"].as_array().ok_or("Missing keys")?;
        let activation_only =
            matches!(request["operation"].as_str(), Some("activate" | "minimize"));
        if (sequence.is_empty() && !activation_only)
            || sequence.len() > 32
            || (activation_only && !sequence.is_empty())
        {
            return Err("Invalid sequence length".into());
        }
        let mut chords = Vec::new();
        for chord in sequence {
            let values = chord.as_array().ok_or("Invalid chord")?;
            if values.is_empty() || values.len() > 5 {
                return Err("Invalid chord length".into());
            }
            let mut keys = Vec::new();
            for value in values {
                let key = u16::try_from(value.as_u64().ok_or("Invalid virtual key")?)
                    .map_err(|_| "Invalid key")?;
                if !(1..=254).contains(&key) {
                    return Err("Invalid key".into());
                }
                keys.push(key);
                all.insert(key);
            }
            chords.push(keys);
        }
        if request["operation"] == "release_keys" {
            for key in &all {
                send(*key, true)?;
                if let Some(path) = request["held_keys_directory"].as_str() {
                    let _ = fs::remove_file(PathBuf::from(path).join(format!("{key}.held")));
                }
            }
            return Ok(());
        }
        let node = &request["source"];
        let pid = request["pid"].as_u64().ok_or("Missing PID")? as u32;
        super::valid(node, pid)?;
        reject_held_keys(&all, |key| unsafe { GetAsyncKeyState(key) } < 0)?;
        let ownership = PathBuf::from(
            request["held_keys_directory"]
                .as_str()
                .ok_or("Missing key ownership directory")?,
        );
        let hwnd = node["hwnd"].as_i64().ok_or("Missing HWND")? as isize;
        let root = unsafe { GetAncestor(hwnd, 2) };
        let initial_foreground = unsafe { GetForegroundWindow() };
        let mut initial_foreground_pid = 0;
        unsafe {
            GetWindowThreadProcessId(initial_foreground, &mut initial_foreground_pid);
        }
        note(
            &mut trace,
            json!({"stage":"preflight","foreground":initial_foreground,"foreground_pid":initial_foreground_pid,
            "target_root":root,"minimized":unsafe {IsIconic(root)} != 0}),
        );
        if request["operation"] == "minimize" {
            if root != hwnd {
                return Err("Minimize requires a root window".into());
            }
            unsafe {
                ShowWindow(root, 6);
            }
            note(
                &mut trace,
                json!({"stage":"minimize","root":root,"minimized":unsafe {IsIconic(root)} != 0}),
            );
            if unsafe { IsIconic(root) } == 0 {
                return Err("Window did not minimize".into());
            }
            return Ok(());
        }
        if unsafe { IsIconic(root) } != 0 {
            if !activation_only {
                return Err("Target minimized; activate and recollect first".into());
            }
            unsafe {
                ShowWindow(root, 9);
            }
            note(
                &mut trace,
                json!({"stage":"restore","root":root,"minimized_after":unsafe {IsIconic(root)} != 0}),
            );
        }
        let current_thread = unsafe { GetCurrentThreadId() };
        // Create the helper's message queue before attaching input queues.
        unsafe {
            PeekMessageW(&mut Message::default(), 0, 0, 0, 0);
        }
        let foreground = unsafe { GetForegroundWindow() };
        let mut foreground_pid = 0;
        let foreground_thread =
            unsafe { GetWindowThreadProcessId(foreground, &mut foreground_pid) };
        let mut actual_pid = 0;
        let target_thread = unsafe { GetWindowThreadProcessId(hwnd, &mut actual_pid) };
        let mut helper_session = 0;
        let mut target_session = 0;
        let helper_session_ok =
            unsafe { ProcessIdToSessionId(GetCurrentProcessId(), &mut helper_session) } != 0;
        let target_session_ok = unsafe { ProcessIdToSessionId(pid, &mut target_session) } != 0;
        note(
            &mut trace,
            json!({"stage":"session","helper_pid":unsafe {GetCurrentProcessId()},
            "helper_session":if helper_session_ok {Some(helper_session)} else {None},
            "target_session":if target_session_ok {Some(target_session)} else {None}}),
        );
        if actual_pid != pid {
            return Err("Target PID changed".into());
        }
        let mut connections = Attached(Vec::new());
        for thread_id in BTreeSet::from([foreground_thread, target_thread]) {
            if thread_id != 0 && thread_id != current_thread {
                let attached = unsafe { AttachThreadInput(current_thread, thread_id, 1) } != 0;
                note(
                    &mut trace,
                    json!({"stage":"attach", "from":current_thread,"to":thread_id,
                    "returned":attached,"helper_desktop":unsafe {GetThreadDesktop(current_thread)},
                    "other_desktop":unsafe {GetThreadDesktop(thread_id)}}),
                );
                if attached {
                    connections.0.push((current_thread, thread_id));
                } else {
                    return Err("Cannot attach activation input queue".into());
                }
            }
        }
        let activated = unsafe { SetForegroundWindow(root) };
        note(
            &mut trace,
            json!({"stage":"set_foreground", "helper_thread":current_thread,
            "foreground_before":foreground,"foreground_pid":foreground_pid,
            "foreground_thread":foreground_thread,"target_root":root,
            "target_thread":target_thread,"returned":activated,
            "foreground_immediate":unsafe { GetForegroundWindow() }}),
        );
        for _ in 0..20 {
            if unsafe { GetForegroundWindow() } == root {
                break;
            }
            thread::sleep(Duration::from_millis(25));
        }
        note(
            &mut trace,
            json!({"stage":"after_wait","foreground":unsafe { GetForegroundWindow() }}),
        );
        if unsafe { GetForegroundWindow() } != root {
            return Err("Cannot establish target foreground".into());
        }
        unsafe {
            SetFocus(hwnd);
        }
        let focused = unsafe { GetFocus() } == hwnd;
        note(
            &mut trace,
            json!({"stage":"focus","hwnd":hwnd,"actual_focus":unsafe {GetFocus()},"matched":focused}),
        );
        if !focused {
            return Err("Cannot establish target focus".into());
        }
        for keys in chords {
            super::valid(node, pid)?;
            reject_held_keys(&all, |key| unsafe { GetAsyncKeyState(key) } < 0)?;
            if unsafe { GetForegroundWindow() } != root || unsafe { GetFocus() } != hwnd {
                return Err("Foreground changed".into());
            }
            let mut held = Held(Vec::new(), ownership.clone());
            for key in keys {
                fs::write(ownership.join(format!("{key}.held")), b"").map_err(|e| e.to_string())?;
                held.0.push(key);
                send(key, false)?;
                sent += 1;
            }
            thread::sleep(Duration::from_millis(20));
            while let Some(key) = held.0.last().copied() {
                send(key, true)?;
                fs::remove_file(ownership.join(format!("{key}.held")))
                    .map_err(|e| e.to_string())?;
                held.0.pop();
            }
            thread::sleep(Duration::from_millis(30));
        }
        Ok(())
    })();
    let residual = all
        .iter()
        .filter(|key| unsafe { GetAsyncKeyState(**key as i32) } < 0)
        .count();
    json!({"ok": result.is_ok() && residual == 0, "error": result.err(),
           "key_downs_delivered": sent, "residual_keys": residual,
           "method": "foreground_guarded_sendinput", "application_result_verified": false,
           "activation_trace":trace})
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn input_matches_windows_x64_layout() {
        assert_eq!(size_of::<Input>(), 40);
    }
    #[test]
    fn invalid_keys_fail_before_input() {
        assert_eq!(execute(&json!({"keys":[[999]]}))["key_downs_delivered"], 0);
    }
    #[test]
    fn user_held_modifiers_and_target_keys_stop_before_input() {
        let keys = BTreeSet::from([0x41]);
        for held in [0x10, 0x11, 0x12, 0x5b, 0x5c, 0x41] {
            assert!(reject_held_keys(&keys, |key| key == held).is_err());
        }
        assert!(reject_held_keys(&keys, |_| false).is_ok());
        // Unrelated user input also blocks delivery; it is never released as ours.
        assert!(reject_held_keys(&keys, |key| key == 0x42).is_err());
        assert!(reject_held_keys(&keys, |key| key == 1).is_err());
    }
}
