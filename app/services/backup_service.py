import json
import shutil
from pathlib import Path

from app.utils.paths import BACKUP_DIR, MANIFEST_DIR


class BackupService:
    def _manifest_path(self, discord_dir: Path) -> Path:
        safe = discord_dir.name.replace("/", "_")
        return MANIFEST_DIR / f"{safe}.json"

    def load(self, discord_dir: Path) -> dict | None:
        p = self._manifest_path(discord_dir)
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def prepare(self, discord_dir: Path, names: list[str]) -> dict:
        manifest = self.load(discord_dir) or {
            "discord_directory": str(discord_dir),
            "files": {},
        }
        backup_root = BACKUP_DIR / discord_dir.name
        backup_root.mkdir(parents=True, exist_ok=True)
        for name in names:
            if name in manifest["files"]:
                continue
            target = discord_dir / name
            entry = {"existed": target.exists(), "backup": None}
            if target.exists():
                backup = backup_root / name
                shutil.copy2(target, backup)
                entry["backup"] = str(backup)
            manifest["files"][name] = entry
        self._manifest_path(discord_dir).write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return manifest

    def restore_and_remove(self, discord_dir: Path, names: list[str]) -> None:
        manifest = self.load(discord_dir)
        if not manifest:
            raise FileNotFoundError("Installation manifest not found")
        for name in names:
            entry = manifest.get("files", {}).get(name)
            target = discord_dir / name
            if not entry:
                continue
            backup = entry.get("backup")
            if entry.get("existed") and backup and Path(backup).is_file():
                shutil.copy2(backup, target)
            else:
                target.unlink(missing_ok=True)
        # proxy.txt is manager-created and is never treated as an original file.
        (discord_dir / "proxy.txt").unlink(missing_ok=True)
        self._manifest_path(discord_dir).unlink(missing_ok=True)
