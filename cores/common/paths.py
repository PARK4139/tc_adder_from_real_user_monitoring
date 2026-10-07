"""Project-owned runtime paths; never import a sibling project's runtime."""

from pathlib import Path

from win32com.shell import shell, shellcon

D_ROOT = Path(__file__).resolve().parents[2]
# Match the shared Desktop/Temp convention using Windows' actual known folder.
D_TEMP = Path(shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None, 0)) / "Temp"
