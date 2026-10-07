"""Family-local HPE990 path definitions."""

from pathlib import Path

from win32com.shell import shell, shellcon

from cores.common.paths import D_ROOT, D_TEMP


class Hpe990Folders:
    def __init__(self) -> None:
        self.D_HPE990 = Path(__file__).resolve().parents[1]
        self.D_HPE990_RULES = self.D_HPE990 / "rules"
        self.D_HPE990_ISSUES = self.D_HPE990 / "issues"
        self.D_HPE990_CONFIGS = self.D_HPE990 / "configs"
        self.D_HPE990_RUNTIME = D_TEMP / "hpe990" / "runtime"
        self.D_HPE990_BUILD = D_TEMP / "hpe990" / "build"
        self.D_HPE990_VISUAL_BUILD = self.D_HPE990_BUILD / "visual"
        self.D_HPE990_EVIDENCE = D_TEMP / "hpe990" / "evidence"
        self.D_AUTO_EMULATOR_OUTPUT = D_ROOT
        self.F_HPE990_VISUAL = self.D_HPE990_VISUAL_BUILD / "release/hpe990-visual.exe"
        self.F_HPE990_UI_REGISTRY = self.D_HPE990_RUNTIME / "ui-elements.sqlite3"
        self.F_HPE990_STEP_TEMPLATES = self.D_HPE990_CONFIGS / "ui_step_templates.json"
        self.F_HPE990_STEP_BINDINGS = self.D_HPE990_CONFIGS / "ui_step_bindings.json"


hpe990_folders = Hpe990Folders()

F_HPE990_FAMILIES = hpe990_folders.D_HPE990_RULES / "families.md"
F_HPE990_PRIORITY = hpe990_folders.D_HPE990_ISSUES / "priority.md"
F_HPE990_SHORTCUT = (
    Path(shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_PROGRAMS, None, 0))
    / "Huvitz_pc"
    / "HPE990"
    / "HPE990.lnk"
)
F_HPE990_SESSION = hpe990_folders.D_HPE990_RUNTIME / "session.json"
F_HPE990_LOCK = hpe990_folders.D_HPE990_RUNTIME / "lifecycle.lock"
F_HPE990_EVENTS = hpe990_folders.D_HPE990_RUNTIME / "lifecycle.jsonl"
F_AUTO_EMULATOR_RUNTIME = hpe990_folders.D_AUTO_EMULATOR_OUTPUT / "auto_emulator.exe"
F_HPE990_RELEASES = hpe990_folders.D_HPE990 / "configs" / "releases.json"
