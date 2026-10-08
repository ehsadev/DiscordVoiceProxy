import os
from pathlib import Path
import sys

APP_DATA = (
    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    / "DiscordVoiceProxyManager"
)
LOG_DIR = APP_DATA / "logs"
BACKUP_DIR = APP_DATA / "backups"
MANIFEST_DIR = APP_DATA / "manifests"
for p in (APP_DATA, LOG_DIR, BACKUP_DIR, MANIFEST_DIR):
    p.mkdir(parents=True, exist_ok=True)

DISCORD_ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "Discord"


def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent.parent / relative_path
