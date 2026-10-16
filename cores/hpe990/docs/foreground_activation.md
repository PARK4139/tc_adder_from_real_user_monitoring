# Emulator foreground activation

Call `hpe990_ui_activate(session_id, ui_id)` with a currently observed native UI ID. This activates the root and focuses the requested control without sending application keys. A minimized root is restored first; recollect it before subsequent input. `hpe990_window_minimize` accepts an enabled native root and preserves the running session.

The Rust worker creates its message queue and temporarily connects it to both the current foreground thread and the target thread. Connections remain alive through foreground verification, focus verification and key delivery. RAII disconnects them on success or error. `hpe990_ui_keys` uses the same activation path and checks foreground and focus before each chord.

Receipts record `activation_trace`: observed foreground, root, thread/desktop handles, attachment results, `SetForegroundWindow` return value and verified focus. API delivery receipts do not prove an application feature worked. Use a subsequent collection and BDD assertion for that result. Each request and receipt is stored in external evidence; Real Activity Monitoring records requested/observed/failed action markers.

In the observed failure, attaching only to the foreground thread produced a zero `SetForegroundWindow` return value. Connecting the target thread as well and retaining the connections produced a matching foreground and focus. This identifies a failure in the worker's input-queue lifecycle; it does not establish a universal Windows policy bypass.

Unknown UI IDs, hidden/disabled targets and changed native identities are rejected. Foreground/focus failure stops key delivery and reports `activation_required`. Only keys marked as owned by this operation are released after a failure. The worker does not send synthetic Alt, click captions, change the registry or change the global foreground timeout.

Different desktops, security boundaries, active menus and competing user input can still prevent activation. [Windows restricts foreground changes](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow); [input queue attachment](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput) requires compatible threads/desktops and resets keyboard state. These conditions require separate verification before extending the supported environment.
