"""Restart keeps review settings and stops only the recorded process."""

import json
import subprocess
import sys

import psutil
import pytest

from cores.hpe990.scripts import share_tc_review as server


def test_stop_previous_waits_for_recorded_process(tmp_path):
    stop = tmp_path / "stop"
    code = (
        "import pathlib, sys, time; p = pathlib.Path(sys.argv[1]); "
        "exec('while not p.exists(): time.sleep(0.02)')"
    )
    child = subprocess.Popen([sys.executable, "-c", code, str(stop)])
    try:
        process = psutil.Process(child.pid)
        record = {
            "pid": child.pid,
            "create_time": process.create_time(),
            "program": process.exe(),
        }
        server.stop_previous(record, stop)
        assert child.wait(timeout=2) == 0
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=2)


def test_reused_pid_does_not_receive_stop(tmp_path):
    process = psutil.Process()
    stop = tmp_path / "stop"
    server.stop_previous(
        {"pid": process.pid, "create_time": process.create_time() - 1, "program": process.exe()},
        stop,
    )
    assert not stop.exists()


@pytest.mark.parametrize(
    "overrides,expected",
    [
        ([], ("172.20.13.185", 9998)),
        (["--bind", "192.168.1.2", "--port", "9997"], ("192.168.1.2", 9997)),
    ],
)
def test_restart_restores_settings_before_start(tmp_path, monkeypatch, overrides, expected):
    record = {"url": "http://172.20.13.185:9998/tc-up-validation/", "token": "team-review"}
    (tmp_path / "tc-review-share.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(server.hpe990_folders, "D_HPE990_RUNTIME", tmp_path)
    monkeypatch.setattr(server.hpe990_folders, "D_HPE990_EVIDENCE", tmp_path)
    monkeypatch.setattr(sys, "argv", ["share_tc_review", *overrides])
    stopped = []
    monkeypatch.setattr(server, "stop_previous", lambda old, stop: stopped.append(old))
    monkeypatch.setattr(server, "load_review_source", lambda: "source")
    monkeypatch.setattr(
        server,
        "render_review",
        lambda source, *args, **kwargs: ('<html lang="ko"></html>', {}),
    )
    monkeypatch.setattr(server.threading.Thread, "start", lambda self: None)

    class Started(Exception):
        pass

    def start(address, handler):
        assert stopped == [record]
        assert address == expected
        raise Started

    monkeypatch.setattr(server, "ThreadingHTTPServer", start)
    with pytest.raises(Started):
        server.main()
