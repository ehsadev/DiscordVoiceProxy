import subprocess
from pathlib import Path


class LauncherService:
    def launch(self, executable: Path) -> None:
        subprocess.Popen([str(executable)], cwd=str(executable.parent), close_fds=True)
