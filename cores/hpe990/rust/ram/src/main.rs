//! Process-scoped WinEvent collection and native window-tree sampling.
use serde::Serialize;
use serde_json::{json, Value};
use std::os::windows::ffi::OsStrExt;
use std::{
    collections::BTreeMap,
    ffi::c_void,
    fs::{self, OpenOptions},
    io::{BufWriter, Write},
    path::PathBuf,
    sync::Mutex,
    thread,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

type Handle = *mut c_void;
#[repr(C)]
#[derive(Default)]
struct Rect {
    left: i32,
    top: i32,
    right: i32,
    bottom: i32,
}
#[repr(C)]
#[derive(Default)]
struct Msg {
    hwnd: Handle,
    message: u32,
    wparam: usize,
    lparam: isize,
    time: u32,
    x: i32,
    y: i32,
    private: u32,
}
#[link(name = "user32")]
extern "system" {
    fn EnumWindows(callback: extern "system" fn(Handle, isize) -> i32, param: isize) -> i32;
    fn EnumChildWindows(
        hwnd: Handle,
        callback: extern "system" fn(Handle, isize) -> i32,
        param: isize,
    ) -> i32;
    fn GetWindowThreadProcessId(hwnd: Handle, pid: *mut u32) -> u32;
    fn GetWindowTextW(hwnd: Handle, text: *mut u16, max: i32) -> i32;
    fn GetClassNameW(hwnd: Handle, text: *mut u16, max: i32) -> i32;
    fn GetWindowRect(hwnd: Handle, rect: *mut Rect) -> i32;
    fn GetParent(hwnd: Handle) -> Handle;
    fn GetWindow(hwnd: Handle, kind: u32) -> Handle;
    fn IsWindowVisible(hwnd: Handle) -> i32;
    fn IsWindowEnabled(hwnd: Handle) -> i32;
    fn GetWindowLongW(hwnd: Handle, index: i32) -> i32;
    fn GetWindowDC(hwnd: Handle) -> Handle;
    fn ReleaseDC(hwnd: Handle, dc: Handle) -> i32;
    fn SetWinEventHook(
        min: u32,
        max: u32,
        module: Handle,
        callback: extern "system" fn(Handle, u32, Handle, i32, i32, u32, u32),
        pid: u32,
        thread: u32,
        flags: u32,
    ) -> Handle;
    fn UnhookWinEvent(hook: Handle) -> i32;
    fn PeekMessageW(msg: *mut Msg, hwnd: Handle, min: u32, max: u32, remove: u32) -> i32;
    fn TranslateMessage(msg: *const Msg) -> i32;
    fn DispatchMessageW(msg: *const Msg) -> isize;
}
#[repr(C)]
struct BitmapInfo {
    size: u32,
    width: i32,
    height: i32,
    planes: u16,
    bits: u16,
    compression: u32,
    image_size: u32,
    x: i32,
    y: i32,
    colors: u32,
    important: u32,
    table: [u32; 1],
}
#[link(name = "gdi32")]
extern "system" {
    fn CreateCompatibleDC(dc: Handle) -> Handle;
    fn CreateCompatibleBitmap(dc: Handle, width: i32, height: i32) -> Handle;
    fn SelectObject(dc: Handle, object: Handle) -> Handle;
    fn BitBlt(
        dest: Handle,
        x: i32,
        y: i32,
        width: i32,
        height: i32,
        source: Handle,
        sx: i32,
        sy: i32,
        flags: u32,
    ) -> i32;
    fn GetDIBits(
        dc: Handle,
        bitmap: Handle,
        start: u32,
        lines: u32,
        data: *mut c_void,
        info: *mut BitmapInfo,
        usage: u32,
    ) -> i32;
    fn DeleteObject(object: Handle) -> i32;
    fn DeleteDC(dc: Handle) -> i32;
}
#[link(name = "kernel32")]
extern "system" {
    fn OpenProcess(access: u32, inherit: i32, pid: u32) -> Handle;
    fn WaitForSingleObject(handle: Handle, milliseconds: u32) -> u32;
    fn CloseHandle(handle: Handle) -> i32;
    fn GetTickCount() -> u32;
    fn MoveFileExW(existing: *const u16, new: *const u16, flags: u32) -> i32;
}
static EVENTS: Mutex<Vec<Value>> = Mutex::new(Vec::new());
static RUN_ID: Mutex<String> = Mutex::new(String::new());
fn now_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis()
}
extern "system" fn event(
    _: Handle,
    kind: u32,
    hwnd: Handle,
    object: i32,
    child: i32,
    thread: u32,
    time: u32,
) {
    let category = match kind {
        0x8000 => "create",
        0x8001 => "destroy",
        0x8002 => "show",
        0x8003 => "hide",
        0x8005 => "focus",
        0x800a => "state",
        0x800b => "location",
        0x800c => "name",
        0x800e => "value",
        3 => "foreground",
        4 => "menu_start",
        5 => "menu_end",
        6 => "popup_start",
        7 => "popup_end",
        0x10 => "dialog_start",
        0x11 => "dialog_end",
        _ => "other",
    };
    EVENTS
        .lock()
        .unwrap()
        .push(json!({"kind":"win_event","event_id":kind,
        "hwnd":hwnd as usize,"object_id":object,"child_id":child,"thread_id":thread,
        "source_tick_ms":time,"observed_unix_ms":now_ms(),"category":category,
        "delivery_latency_ms":unsafe{GetTickCount().wrapping_sub(time)}}));
}
#[derive(Serialize, Clone, PartialEq)]
struct Window {
    hwnd: usize,
    pid: u32,
    parent: usize,
    owner: usize,
    name: String,
    class_name: String,
    visible: bool,
    enabled: bool,
    rect: [i32; 4],
    visual_hash: Option<String>,
}
fn visual_hash(hwnd: Handle, width: i32, height: i32) -> Option<String> {
    if width <= 0 || height <= 0 || width as i64 * height as i64 > 16000000 {
        return None;
    }
    unsafe {
        let dc = GetWindowDC(hwnd);
        if dc.is_null() {
            return None;
        }
        let memory = CreateCompatibleDC(dc);
        let bitmap = CreateCompatibleBitmap(dc, width, height);
        if memory.is_null() || bitmap.is_null() {
            if !bitmap.is_null() {
                DeleteObject(bitmap);
            }
            if !memory.is_null() {
                DeleteDC(memory);
            }
            ReleaseDC(hwnd, dc);
            return None;
        }
        let old = SelectObject(memory, bitmap);
        let copied = BitBlt(memory, 0, 0, width, height, dc, 0, 0, 0x00cc0020);
        SelectObject(memory, old);
        let mut pixels = vec![0u8; (width as usize) * (height as usize) * 4];
        let mut info = BitmapInfo {
            size: 40,
            width,
            height: -height,
            planes: 1,
            bits: 32,
            compression: 0,
            image_size: 0,
            x: 0,
            y: 0,
            colors: 0,
            important: 0,
            table: [0],
        };
        let read = if copied != 0 {
            GetDIBits(
                memory,
                bitmap,
                0,
                height as u32,
                pixels.as_mut_ptr() as Handle,
                &mut info,
                0,
            )
        } else {
            0
        };
        DeleteObject(bitmap);
        DeleteDC(memory);
        ReleaseDC(hwnd, dc);
        if read == 0 {
            return None;
        }
        let mut hash = 14695981039346656037u64;
        // Hash all RGB bytes in native code: painted values need not have a native text event.
        for (i, byte) in pixels.iter().enumerate() {
            if i % 4 != 3 {
                hash ^= *byte as u64;
                hash = hash.wrapping_mul(1099511628211);
            }
        }
        Some(format!("{hash:016x}"))
    }
}
struct Context {
    pid: u32,
    windows: BTreeMap<usize, Window>,
}
extern "system" fn collect(hwnd: Handle, param: isize) -> i32 {
    unsafe {
        let context = &mut *(param as *mut Context);
        let mut pid = 0;
        GetWindowThreadProcessId(hwnd, &mut pid);
        if pid != context.pid {
            return 1;
        }
        let mut text = [0u16; 1024];
        let n = GetWindowTextW(hwnd, text.as_mut_ptr(), 1024);
        let name = String::from_utf16_lossy(&text[..n.max(0) as usize]);
        let n = GetClassNameW(hwnd, text.as_mut_ptr(), 1024);
        let class_name = String::from_utf16_lossy(&text[..n.max(0) as usize]);
        let mut rect = Rect::default();
        GetWindowRect(hwnd, &mut rect);
        let visible = IsWindowVisible(hwnd) != 0;
        let parent = if GetWindowLongW(hwnd, -16) as u32 & 0x40000000 != 0 {
            GetParent(hwnd) as usize
        } else {
            0
        };
        let hash = if visible && parent == 0 && class_name == "QWidget" {
            visual_hash(hwnd, rect.right - rect.left, rect.bottom - rect.top)
        } else {
            None
        };
        context.windows.insert(
            hwnd as usize,
            Window {
                hwnd: hwnd as usize,
                pid,
                parent,
                owner: GetWindow(hwnd, 4) as usize,
                name,
                class_name,
                visible,
                enabled: IsWindowEnabled(hwnd) != 0,
                rect: [rect.left, rect.top, rect.right, rect.bottom],
                visual_hash: hash,
            },
        );
    }
    1
}
extern "system" fn root(hwnd: Handle, param: isize) -> i32 {
    collect(hwnd, param);
    unsafe {
        let mut pid = 0;
        GetWindowThreadProcessId(hwnd, &mut pid);
        if pid == (*(param as *mut Context)).pid {
            EnumChildWindows(hwnd, collect, param);
        }
    }
    1
}
fn snapshot(pid: u32) -> BTreeMap<usize, Window> {
    let mut context = Context {
        pid,
        windows: BTreeMap::new(),
    };
    unsafe {
        EnumWindows(root, &mut context as *mut Context as isize);
    }
    context.windows
}
fn emit(writer: &mut BufWriter<std::fs::File>, seq: &mut u64, session: &str, mut record: Value) {
    *seq += 1;
    record["schema_version"] = json!(1);
    record["sequence"] = json!(*seq);
    record["run_id"] = json!(*RUN_ID.lock().unwrap());
    record["session_id"] = json!(session);
    record["observed_unix_ms"] = json!(now_ms());
    serde_json::to_writer(&mut *writer, &record).unwrap();
    writeln!(writer).unwrap();
}
fn main() {
    let args: Vec<String> = std::env::args().collect();
    assert_eq!(args.len(), 5, "pid session_id output_directory interval_ms");
    let pid: u32 = args[1].parse().unwrap();
    let session = &args[2];
    let directory = PathBuf::from(&args[3]);
    *RUN_ID.lock().unwrap() = directory.file_name().unwrap().to_string_lossy().to_string();
    let commands = directory.join("commands");
    let processed = directory.join("processed-commands");
    fs::create_dir_all(&commands).unwrap();
    fs::create_dir_all(&processed).unwrap();
    let interval: u64 = args[4].parse().unwrap();
    assert!((20..=1000).contains(&interval));
    fs::create_dir_all(&directory).unwrap();
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(directory.join("events.jsonl"))
        .unwrap();
    let mut writer = BufWriter::new(file);
    let mut seq = 0;
    let mut previous = BTreeMap::new();
    let mut scans = 0u64;
    let mut max_scan_us = 0u128;
    let mut max_gap_ms = 0u128;
    let mut max_event_latency_ms = 0u64;
    let mut snapshot_write_failures = 0u64;
    let mut stop_action_id: Option<String> = None;
    let start = Instant::now();
    let mut last = start;
    let mut next = start;
    unsafe {
        let process = OpenProcess(0x100000, 0, pid);
        assert!(!process.is_null(), "Cannot open target process");
        let hook = SetWinEventHook(1, 0x7fffffff, std::ptr::null_mut(), event, pid, 0, 0);
        assert!(!hook.is_null(), "Cannot register WinEvent hook");
        emit(
            &mut writer,
            &mut seq,
            session,
            json!({"kind":"monitor_started","pid":pid,"interval_ms":interval}),
        );
        let reason = loop {
            let mut msg = Msg::default();
            while PeekMessageW(&mut msg, std::ptr::null_mut(), 0, 0, 1) != 0 {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
            for record in EVENTS.lock().unwrap().drain(..) {
                max_event_latency_ms =
                    max_event_latency_ms.max(record["delivery_latency_ms"].as_u64().unwrap_or(0));
                emit(&mut writer, &mut seq, session, record);
            }
            for entry in fs::read_dir(&commands).unwrap().flatten() {
                let path = entry.path();
                if path.extension().and_then(|v| v.to_str()) != Some("json") {
                    continue;
                }
                if let Ok(bytes) = fs::read(&path) {
                    if let Ok(mut record) = serde_json::from_slice::<Value>(&bytes) {
                        if record["session_id"].as_str() == Some(session.as_str())
                            && record["kind"] == "control_action"
                        {
                            if record["action"] == "session_stop" && record["phase"] == "requested"
                            {
                                stop_action_id =
                                    record["action_id"].as_str().map(|s| s.to_string());
                            }
                            record["collector_received_unix_ms"] = json!(now_ms());
                            emit(&mut writer, &mut seq, session, record);
                        }
                    }
                }
                fs::rename(&path, processed.join(entry.file_name())).unwrap();
            }
            if Instant::now() >= next {
                let scan_start = Instant::now();
                max_gap_ms = max_gap_ms.max(scan_start.duration_since(last).as_millis());
                last = scan_start;
                let current = snapshot(pid);
                for (hwnd, window) in &current {
                    if previous.get(hwnd) != Some(window) {
                        let kind = if previous.contains_key(hwnd) {
                            "window_changed"
                        } else {
                            "window_created"
                        };
                        emit(
                            &mut writer,
                            &mut seq,
                            session,
                            json!({"kind":kind,"window":window,"previous":previous.get(hwnd)}),
                        );
                        if let Some(old) = previous.get(hwnd) {
                            if old.visual_hash != window.visual_hash && window.visual_hash.is_some()
                            {
                                emit(
                                    &mut writer,
                                    &mut seq,
                                    session,
                                    json!({"kind":"visual_changed","hwnd":hwnd,
                                    "previous_hash":old.visual_hash,"visual_hash":window.visual_hash,
                                    "method":"window_dc_rgb_fnv1a64","occlusion_sensitive":true}),
                                );
                            }
                        }
                    }
                }
                for (hwnd, window) in &previous {
                    if !current.contains_key(hwnd) {
                        emit(
                            &mut writer,
                            &mut seq,
                            session,
                            json!({"kind":"window_destroyed","window":window}),
                        );
                    }
                }
                previous = current;
                scans += 1;
                max_scan_us = max_scan_us.max(scan_start.elapsed().as_micros());
                let data = json!({"schema_version":1,"session_id":session,"pid":pid,"scan":scans,
                    "observed_unix_ms":now_ms(),"windows":previous.values().collect::<Vec<_>>()});
                let pending = directory.join("snapshot.pending.json");
                fs::write(&pending, serde_json::to_vec(&data).unwrap()).unwrap();
                let dest = directory.join("snapshot.json");
                let src: Vec<u16> = pending.as_os_str().encode_wide().chain(Some(0)).collect();
                let dst: Vec<u16> = dest.as_os_str().encode_wide().chain(Some(0)).collect();
                let mut published = false;
                for _ in 0..20 {
                    if MoveFileExW(src.as_ptr(), dst.as_ptr(), 1) != 0 {
                        published = true;
                        break;
                    }
                    thread::sleep(Duration::from_millis(2));
                }
                if !published {
                    snapshot_write_failures += 1;
                    emit(
                        &mut writer,
                        &mut seq,
                        session,
                        json!({"kind":"snapshot_write_failed","scan":scans}),
                    );
                }
                writer.flush().unwrap();
                next = Instant::now() + Duration::from_millis(interval);
            }
            if WaitForSingleObject(process, 0) == 0 {
                for window in previous.values() {
                    emit(
                        &mut writer,
                        &mut seq,
                        session,
                        json!({"kind":"window_destroyed","window":window,"source":"final_process_exit"}),
                    );
                }
                break "process_exited";
            }
            if directory.join("stop.request").exists() {
                break "requested";
            }
            thread::sleep(Duration::from_millis(5));
        };
        if reason == "process_exited" {
            if let Some(action_id) = &stop_action_id {
                emit(
                    &mut writer,
                    &mut seq,
                    session,
                    json!({"kind":"control_action","phase":"observed",
                    "action":"session_stop","action_id":action_id,"outcome":"process_exited"}),
                );
            }
        }
        emit(
            &mut writer,
            &mut seq,
            session,
            json!({"kind":"monitor_stopped","reason":reason}),
        );
        writer.flush().unwrap();
        UnhookWinEvent(hook);
        CloseHandle(process);
        fs::write(directory.join("ram-report.json"),serde_json::to_vec_pretty(&json!({
            "session_id":session,"pid":pid,"sequences":seq,"scans":scans,"duration_ms":start.elapsed().as_millis(),
            "max_scan_us":max_scan_us,"max_sampling_gap_ms":max_gap_ms,"stop_reason":reason,
            "scope":"process-scoped WinEvents and native HWND state; transient unsignalled UI changes below sampling interval may be missed",
            "interval_ms":interval,"queue_dropped":0,"max_win_event_delivery_latency_ms":max_event_latency_ms,
            "snapshot_write_failures":snapshot_write_failures,"run_id":*RUN_ID.lock().unwrap(),
            "visual_method":"window DC RGB hash, may be affected by occlusion; no assertion for unobserved sub-interval transients"
        })).unwrap()).unwrap();
    }
}
