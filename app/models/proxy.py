from dataclasses import dataclass
from enum import Enum


class ProxyState(str, Enum):
    NOT_INSTALLED = "NOT_INSTALLED"
    PARTIAL = "PARTIAL"
    INSTALLED = "INSTALLED"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    NEEDS_REPAIR = "NEEDS_REPAIR"


@dataclass(slots=True)
class ProxyConfiguration:
    host: str
    port: int
    username: str | None = None
    password: str | None = None


@dataclass(slots=True)
class ProxyStatus:
    state: ProxyState
    directory: str | None
    dwrite: bool = False
    force_proxy: bool = False
    config: bool = False
    message: str = ""
