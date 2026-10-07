"""HWND-anchored visual evidence for Qt items without accessible/native identities."""

import asyncio
import hashlib
import json
import subprocess
import sys
import traceback
from pathlib import Path

if __name__ == "__main__":
    sys.coinit_flags = 0
    from winrt.runtime import ApartmentType, init_apartment

    init_apartment(ApartmentType.MULTI_THREADED)

from cores.hpe990.common.paths import hpe990_folders


async def recognize(path: str) -> list[dict]:
    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import (
        BitmapAlphaMode,
        BitmapDecoder,
        BitmapPixelFormat,
        SoftwareBitmap,
    )
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage import FileAccessMode, StorageFile

    engine = OcrEngine.try_create_from_language(Language("en-US"))
    if engine is None:
        engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise RuntimeError("No installed Windows OCR recognizer is available")
    file = await StorageFile.get_file_from_path_async(path)
    stream = await file.open_async(FileAccessMode.READ)
    try:
        decoder = await BitmapDecoder.create_async(stream)
        original = await decoder.get_software_bitmap_async()
        bitmap = SoftwareBitmap.convert_with_alpha(
            original, BitmapPixelFormat.BGRA8, BitmapAlphaMode.IGNORE
        )
        try:
            result = await engine.recognize_async(bitmap)
            lines = []
            for line in result.lines:
                words = list(line.words)
                rects = [word.bounding_rect for word in words]
                if not rects:
                    continue
                lines.append(
                    {
                        "text": line.text,
                        "ocr_language": engine.recognizer_language.language_tag,
                        "rect": [
                            min(r.x for r in rects),
                            min(r.y for r in rects),
                            max(r.x + r.width for r in rects),
                            max(r.y + r.height for r in rects),
                        ],
                    }
                )
            return lines
        finally:
            bitmap.close()
            original.close()
    finally:
        stream.close()


def link_frames(lines: list[dict], frames: list[list[int]]) -> list[dict]:
    """Associate observed frames with nearby left labels, leaving ambiguity explicit."""
    fields = []
    for rect in frames:
        left, top, right, bottom = rect
        center = (top + bottom) / 2
        candidates = [
            line
            for line in lines
            if line["rect"][2] < left and abs((line["rect"][1] + line["rect"][3]) / 2 - center) < 12
        ]
        candidates.sort(key=lambda line: left - line["rect"][2])
        label = candidates[0]["text"] if candidates else None
        inside = [
            line["text"]
            for line in lines
            if left <= line["rect"][0] <= right and top <= line["rect"][1] <= bottom
        ]
        fields.append(
            {
                "name": label,
                "rect": rect,
                "control_type": "input_field_candidate",
                "observed_text": " ".join(inside),
                "label_candidates": [line["text"] for line in candidates],
                "enabled": None,
                "readonly": None,
                "value": None,
            }
        )
    return fields


def worker_collect_visual(captures: list[dict], roots: list[dict], include_disabled=False) -> dict:
    binary = hpe990_folders.F_HPE990_VISUAL
    elements, observations, errors = [], [], []
    by_handle = {root["hwnd"]: root for root in roots}
    for capture in captures:
        root = by_handle[capture["hwnd"]]
        if not root["enabled"] and not include_disabled:
            continue
        try:
            ocr_path = str(Path(capture["path"]).with_suffix(".ocr.png"))
            frames = subprocess.run(
                [str(binary), capture["path"], ocr_path],
                capture_output=True,
                check=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            geometry = json.loads(frames.stdout)
            lines = asyncio.run(recognize(ocr_path))
            for line in lines:
                line["rect"] = [value / 3 for value in line["rect"]]
            items = link_frames(lines, geometry["frames"])
            items += [
                {
                    "name": line["text"],
                    "rect": line["rect"],
                    "control_type": "text",
                    "value": None,
                    "enabled": None,
                    "readonly": None,
                }
                for line in lines
            ]
            for item in items:
                key = json.dumps([root["hwnd"], item["rect"], item["name"], item["control_type"]])
                item.update(
                    {
                        "id": "visual:" + hashlib.sha256(key.encode()).hexdigest()[:24],
                        "backend": "visual",
                        "root_hwnd": root["hwnd"],
                        "hwnd": None,
                        "pid": root["pid"],
                        "rect_space": "root_screenshot_pixels",
                        "screenshot": capture["path"],
                        "screenshot_sha256": capture["sha256"],
                        "semantic_state_verified": False,
                    }
                )
            elements.extend(items)
            observations.append(
                {
                    "root_hwnd": root["hwnd"],
                    "ocr_lines": len(lines),
                    "input_frame_candidates": len(geometry["frames"]),
                    "rust_geometry_elapsed_ms": geometry["elapsed_ms"],
                    "ocr_language": lines[0]["ocr_language"] if lines else None,
                }
            )
        except Exception as error:
            errors.append(
                {
                    "root_hwnd": root["hwnd"],
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                }
            )
    return {
        "backend": "visual",
        "elements": elements,
        "observations": observations,
        "errors": errors,
        "scope": "Visible screenshot evidence only; candidates have no native identity or verified semantic state",
    }


def collect_visual_elements(
    captures: list[dict], roots: list[dict], include_disabled=False
) -> dict:
    if not captures:
        return {"backend": "visual", "elements": [], "observations": [], "errors": []}
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cores.hpe990.functions.visual_elements",
                json.dumps(captures),
                json.dumps(roots),
                json.dumps(include_disabled),
            ],
            capture_output=True,
            check=True,
            stdin=subprocess.DEVNULL,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return json.loads(result.stdout.decode("utf-8"))
    except (subprocess.SubprocessError, ValueError) as error:
        details = (
            error.stderr.decode("utf-8", errors="replace")[-1000:]
            if getattr(error, "stderr", None)
            else type(error).__name__
        )
        return {"backend": "visual", "elements": [], "observations": [], "errors": [details]}


if __name__ == "__main__":
    sys.stdout.buffer.write(
        json.dumps(
            worker_collect_visual(
                json.loads(sys.argv[1]),
                json.loads(sys.argv[2]),
                json.loads(sys.argv[3]) if len(sys.argv) > 3 else False,
            ),
            ensure_ascii=False,
        ).encode("utf-8")
    )
