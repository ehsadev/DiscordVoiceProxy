from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DiscordInstallation:
    root: Path
    app_directory: Path
    executable: Path
    version: str
