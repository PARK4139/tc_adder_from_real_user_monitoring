"""A painted but blank Qt tool must not silently count as readable evidence."""

from types import SimpleNamespace

import pytest
from PIL import Image

from cores.hpe990.functions import ui


@pytest.mark.parametrize(
    "window_class,fallback_nonuniform,expected_method,expected_flags,border,desktop_nonuniform",
    [
        ("QTool", True, "BitBlt", [], False, False),
        ("QPopup", False, "PrintWindow", ["uniform_pixels_after_fallback"], False, False),
        ("QWidget", True, "BitBlt", [], False, False),
        ("QPopup", True, "BitBlt", [], True, False),
        ("QPopup", False, "PrintWindow", ["uniform_pixels_after_fallback"], True, False),
        (
            "QTool",
            False,
            "DesktopBitBlt",
            ["desktop_region_requires_visibility_review"],
            False,
            True,
        ),
        (
            "QWidget",
            False,
            "DesktopBitBlt",
            ["desktop_region_requires_visibility_review"],
            False,
            True,
        ),
    ],
)
def test_uniform_painted_popup_preserves_original_and_reports_fallback(
    monkeypatch,
    tmp_path,
    window_class,
    fallback_nonuniform,
    expected_method,
    expected_flags,
    border,
    desktop_nonuniform,
):
    size = 12 if border else 2
    pixels = bytearray([255, 255, 255, 0] * size * size)
    if border:
        for y in range(size):
            for x in range(size):
                if min(x, y, size - 1 - x, size - 1 - y) < 3:
                    pixels[(y * size + x) * 4 : (y * size + x) * 4 + 4] = bytes([200, 200, 200, 0])
    point = (size // 2, size // 2) if border else (0, 0)
    released = []
    bitmap = SimpleNamespace(
        CreateCompatibleBitmap=lambda *a: None,
        GetBitmapBits=lambda *a: bytes(pixels),
        GetHandle=lambda: 123,
    )

    desktop = SimpleNamespace(DeleteDC=lambda: released.append("desktop"))

    def blit(*a):
        if (a[2] is desktop and desktop_nonuniform) or (
            a[2] is not desktop and fallback_nonuniform
        ):
            offset = (point[1] * size + point[0]) * 4
            pixels[offset : offset + 4] = bytes([0, 0, 0, 0])

    target = SimpleNamespace(
        GetSafeHdc=lambda: 2,
        SelectObject=lambda *a: None,
        BitBlt=blit,
        DeleteDC=lambda: released.append("target"),
    )
    source = SimpleNamespace(
        CreateCompatibleDC=lambda: target, DeleteDC=lambda: released.append("source")
    )
    monkeypatch.setattr(ui.win32gui, "GetWindowRect", lambda _: (0, 0, size, size))
    monkeypatch.setattr(ui.win32gui, "GetWindowDC", lambda _: 1)
    monkeypatch.setattr(ui.win32gui, "GetDC", lambda _: 3)
    monkeypatch.setattr(ui.win32gui, "GetClassName", lambda _: window_class)
    monkeypatch.setattr(ui.win32gui, "DeleteObject", lambda _: released.append("bitmap"))
    monkeypatch.setattr(
        ui.win32gui,
        "ReleaseDC",
        lambda hwnd, dc: released.append("screen-release" if hwnd == 0 else "window"),
    )
    monkeypatch.setattr(
        ui.win32ui, "CreateDCFromHandle", lambda handle: desktop if handle == 3 else source
    )
    monkeypatch.setattr(ui.win32ui, "CreateBitmap", lambda: bitmap)
    monkeypatch.setattr(ui.ctypes.windll.user32, "PrintWindow", lambda *a: 1)

    result = ui._capture(5, tmp_path / "tool.png")
    assert result["method"] == expected_method
    assert result.get("quality_flags", []) == expected_flags
    assert released == (
        (["desktop", "screen-release"] if not fallback_nonuniform else [])
        + ["bitmap", "target", "source", "window"]
    )
    final = Image.open(result["path"])
    primary = Image.open(result["primary_path"])
    content = primary.crop((3, 3, size - 3, size - 3)) if border else primary
    assert content.getextrema() == ((255, 255),) * 3
    assert result["fallback_reason"] == (
        "uniform_popup_print_window"
        if window_class in ("QTool", "QPopup")
        else "uniform_window_print_window"
    )
    if not fallback_nonuniform:
        assert Image.open(result["window_dc_path"]).getpixel(point) == (255, 255, 255)
    assert final.getpixel(point) == (
        (0, 0, 0) if expected_method in ("BitBlt", "DesktopBitBlt") else (255, 255, 255)
    )
