"""MCP lifecycle operations for the fixed, family-owned Emulator target."""

from cores.hpe990.functions.lifecycle import (
    close_emulator,
    emulator_status,
    launch_emulator,
    stop_session,
)


def hpe990_launch(timeout_seconds: float = 30.0) -> dict:
    """Launch HPE990, click the identified Continue control, and wait for its Edger screen.

    Reuse an existing session instead of starting another process. Return process,
    shortcut, session, window and runtime evidence information. No arbitrary executable
    paths or arguments are accepted. A timeout is an error, not a successful launch.
    """
    return launch_emulator(timeout_seconds)


def hpe990_status() -> dict:
    """Read HPE990 process/window status without launching or controlling the application."""
    return emulator_status()


def hpe990_close(session_id: str, timeout_seconds: float = 15.0) -> dict:
    """Request normal WM_CLOSE for the exact session started by this project.

    Refuse existing sessions adopted from outside this project. Do not force-kill
    processes or dismiss application confirmation dialogs. Return closed=false if
    the application remains alive after the timeout.
    """
    return close_emulator(session_id, timeout_seconds)


def hpe990_stop(session_id: str, force: bool = False, timeout_seconds: float = 15.0) -> dict:
    """Stop this project's exact owned application session. Default requests normal close.

    Explicit force=true terminates only identity-checked owned HPE990 processes and
    reports exit_method=explicit_force; it never shuts down Windows or unrelated apps.
    """
    return stop_session(session_id, force, timeout_seconds)
