use serde_json::{json, Value};
use std::{
    env, fs, thread,
    time::{Duration, Instant},
};

#[repr(C)]
#[derive(Default, PartialEq, Debug)]
struct Rect {
    left: i32,
    top: i32,
    right: i32,
    bottom: i32,
}

#[link(name = "user32")]
extern "system" {
    fn IsWindow(hwnd: isize) -> i32;
    fn IsWindowVisible(hwnd: isize) -> i32;
    fn IsWindowEnabled(hwnd: isize) -> i32;
    fn GetWindowThreadProcessId(hwnd: isize, pid: *mut u32) -> u32;
    fn GetWindowRect(hwnd: isize, rect: *mut Rect) -> i32;
    fn PostMessageW(hwnd: isize, msg: u32, wparam: usize, lparam: isize) -> i32;
}

fn position(point: [i32; 2]) -> Result<isize, String> {
    if point.iter().any(|v| !(-32768..=32767).contains(v)) {
        return Err("Client coordinates exceed signed 16-bit message range".into());
    }
    Ok(((point[0] as u16 as u32) | ((point[1] as u16 as u32) << 16)) as isize)
}

fn interpolate(start: [i32; 2], end: [i32; 2], step: u32, steps: u32) -> [i32; 2] {
    std::array::from_fn(|i| {
        (start[i] as f64 + (end[i] - start[i]) as f64 * step as f64 / steps as f64).round() as i32
    })
}

fn valid(node: &Value, pid: u32) -> Result<(), String> {
    let hwnd = node["hwnd"].as_i64().ok_or("Missing HWND")? as isize;
    let mut actual = 0;
    let mut rect = Rect::default();
    unsafe {
        GetWindowThreadProcessId(hwnd, &mut actual);
        if IsWindow(hwnd) == 0
            || actual != pid
            || IsWindowVisible(hwnd) == 0
            || IsWindowEnabled(hwnd) == 0
        {
            return Err("Target is stale, foreign, hidden or disabled".into());
        }
        if GetWindowRect(hwnd, &mut rect) == 0 {
            return Err("Cannot read target bounds".into());
        }
    }
    let expected = &node["rect"];
    if [rect.left, rect.top, rect.right, rect.bottom]
        .iter()
        .enumerate()
        .any(|(i, v)| expected[i].as_i64() != Some(*v as i64))
    {
        return Err("Target geometry changed during drag".into());
    }
    Ok(())
}

fn drag(request: &Value) -> Value {
    let started = Instant::now();
    let mut posted = 0;
    let mut released = false;
    let mut last = [0, 0];
    let source = &request["source"];
    let target = &request["target"];
    let hwnd = source["hwnd"].as_i64().unwrap_or(0) as isize;
    let pid = request["pid"].as_u64().unwrap_or(0) as u32;
    let result = (|| -> Result<(), String> {
        let duration = request["duration_ms"].as_u64().ok_or("Missing duration")?;
        if !(50..=5000).contains(&duration) {
            return Err("Duration must be 50..5000ms".into());
        }
        let point = |key: &str| -> Result<[i32; 2], String> {
            let mut point = [0, 0];
            for (i, value) in point.iter_mut().enumerate() {
                *value = i32::try_from(request[key][i].as_i64().ok_or("Missing point")?)
                    .map_err(|_| "Invalid point")?;
            }
            position(point)?;
            Ok(point)
        };
        let start = point("start_client")?;
        let end = point("end_client")?;
        last = start;
        valid(source, pid)?;
        valid(target, pid)?;
        if unsafe { PostMessageW(hwnd, 0x0200, 0, position(start)?) } == 0 {
            return Err("Initial mouse-move rejected".into());
        }
        posted += 1;
        if unsafe { PostMessageW(hwnd, 0x0201, 1, position(start)?) } == 0 {
            return Err("Button-down rejected".into());
        }
        posted += 1;
        let steps = duration.div_ceil(16) as u32;
        for step in 1..=steps {
            let deadline = Duration::from_millis(duration * step as u64 / steps as u64);
            if let Some(wait) = deadline.checked_sub(started.elapsed()) {
                thread::sleep(wait);
            }
            valid(source, pid)?;
            valid(target, pid)?;
            last = interpolate(start, end, step, steps);
            if unsafe { PostMessageW(hwnd, 0x0200, 1, position(last)?) } == 0 {
                return Err("Mouse-move rejected".into());
            }
            posted += 1;
        }
        Ok(())
    })();
    let mut actual_pid = 0;
    unsafe {
        GetWindowThreadProcessId(hwnd, &mut actual_pid);
    }
    if actual_pid == pid && unsafe { IsWindow(hwnd) } != 0 {
        if let Ok(point) = position(last) {
            released = unsafe { PostMessageW(hwnd, 0x0202, 0, point) } != 0;
        }
    }
    json!({"ok":result.is_ok() && released,"error":result.err(),"button_release_posted":released,
           "messages_posted":posted,"elapsed_ms":started.elapsed().as_secs_f64()*1000.0,
           "method":"process_scoped_postmessage","scope":"Delivery receipt; application result requires before/after validation"})
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let request: Value = serde_json::from_slice(&fs::read(
        env::args().nth(1).ok_or("Request JSON required")?,
    )?)?;
    let result = drag(&request);
    println!("{result}");
    if result["ok"] != true {
        std::process::exit(1);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn signed_coordinates_pack_without_wrap() {
        assert_eq!(position([-1, -2]).unwrap() as u32, 0xfffeffff);
        assert!(position([32768, 0]).is_err());
    }
    #[test]
    fn path_has_exact_endpoints_and_uniform_middle() {
        assert_eq!(interpolate([10, 20], [90, 60], 0, 10), [10, 20]);
        assert_eq!(interpolate([10, 20], [90, 60], 5, 10), [50, 40]);
        assert_eq!(interpolate([10, 20], [90, 60], 10, 10), [90, 60]);
    }
    #[test]
    fn malformed_request_cannot_post_a_drag() {
        let result = drag(&json!({"duration_ms":1}));
        assert_eq!(result["ok"], false);
        assert_eq!(result["messages_posted"], 0);
    }
}
