from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeStatus:
    installed: bool
    version: str | None = None
    raw: str = ""
