"""Advance the observed HPE990 trial dialog using its native Qt child control."""

import time

import win32api
import win32con
import win32gui
import win32process


def continue_buttons(windows: list[dict]) -> list[int]:
    found = set()
    for window in windows:

        def inspect(hwnd, _):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if (
                pid == window["pid"]
                and win32gui.IsWindowVisible(hwnd)
                and win32gui.GetWindowText(hwnd) == "pushButton_continue"
            ):
                found.add(hwnd)

        win32gui.EnumChildWindows(window["hwnd"], inspect, None)
    return sorted(found)


def click_continue(hwnd: int) -> dict:
    if not win32gui.IsWindowEnabled(hwnd):
        raise RuntimeError("HPE990 Continue is disabled")
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    point = win32api.MAKELONG((right - left) // 2, (bottom - top) // 2)
    # Qt renders this button as QWidget, so BM_CLICK is not applicable.
    # Deliver mouse messages to the identified child; do not move the user's cursor.
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, point)
    return {
        "control_name": "pushButton_continue",
        "hwnd": hwnd,
        "requested_at_monotonic": time.monotonic(),
    }
