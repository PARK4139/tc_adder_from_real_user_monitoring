"""Family-local paths for auto_emulator tool acceptance tests."""

from pathlib import Path


class AutoEmulatorFolders:
    def __init__(self) -> None:
        self.D_AUTO_EMULATOR = Path(__file__).resolve().parents[1]
        self.D_AUTO_EMULATOR_RULES = self.D_AUTO_EMULATOR / "rules"
        self.D_AUTO_EMULATOR_ISSUES = self.D_AUTO_EMULATOR / "issues"
        self.D_AUTO_EMULATOR_CONFIGS = self.D_AUTO_EMULATOR / "configs"
        self.D_AUTO_EMULATOR_BDD = self.D_AUTO_EMULATOR / "tests/bdd"
        self.F_AUTO_EMULATOR_BDD = self.D_AUTO_EMULATOR_CONFIGS / "one_shot_bdd.json"


auto_emulator_folders = AutoEmulatorFolders()
