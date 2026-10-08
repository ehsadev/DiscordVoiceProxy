import re
import subprocess
from pathlib import Path

from app.models.discord import DiscordInstallation
from app.utils.paths import DISCORD_ROOT

_VERSION_RE = re.compile(r"^app-(.+)$", re.IGNORECASE)


class DiscordService:
    def find_discord_root(self) -> Path | None:
        return DISCORD_ROOT if DISCORD_ROOT.is_dir() else None

    def find_latest_app_directory(self) -> Path | None:
        root = self.find_discord_root()
        if not root:
            return None
        candidates = []
        for p in root.iterdir():
            if (
                p.is_dir()
                and _VERSION_RE.match(p.name)
                and (p / "Discord.exe").is_file()
            ):
                candidates.append(p)
        if not candidates:
            return None

        def key(p: Path):
            s = p.name[4:]
            nums = tuple(int(x) for x in re.findall(r"\d+", s))
            return nums or (0,)

        return max(candidates, key=key)

    def find_discord_executable(self) -> Path | None:
        app = self.find_latest_app_directory()
        return app / "Discord.exe" if app else None

    def get_discord_version(self) -> str | None:
        app = self.find_latest_app_directory()
        if not app:
            return None
        return app.name[4:]

    def get_installation(self) -> DiscordInstallation | None:
        root = self.find_discord_root()
        app = self.find_latest_app_directory()
        if not root or not app:
            return None
        exe = app / "Discord.exe"
        return DiscordInstallation(root, app, exe, app.name[4:])

    def is_discord_running(self) -> bool:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Discord.exe"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return "Discord.exe".lower() in result.stdout.lower()
        except Exception:
            return False
