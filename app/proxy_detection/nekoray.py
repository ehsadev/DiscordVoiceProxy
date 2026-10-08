import json
from pathlib import Path

from app.models.proxy import ProxyConfiguration

from .base import ProxyDetector
from .probe import is_socks5


class NekoRayDetector(ProxyDetector):
    name = "NekoRay / NekoBox"
    homePath = Path.home()
    roots = [
        homePath / "AppData/Roaming/nekoray",
        homePath / "AppData/Roaming/nekobox",
        homePath / "AppData/Local/nekoray",
        homePath / "AppData/Local/nekobox",
        homePath / ".config/nekoray",
    ]
    common_ports = (2080, 10808, 1080, 7890, 7891)

    def detect(self):
        for root in self.roots:
            if not root.exists():
                continue
            for f in root.rglob("*.json"):
                if f.stat().st_size > 8 * 1024 * 1024:
                    continue
                try:
                    data = json.loads(
                        f.read_text(encoding="utf-8-sig", errors="ignore")
                    )
                except Exception:
                    continue
                port = self._find_port(data)
                if port and is_socks5("127.0.0.1", port):
                    return ProxyConfiguration("127.0.0.1", port)
        for port in self.common_ports:
            if is_socks5("127.0.0.1", port):
                return ProxyConfiguration("127.0.0.1", port)
        return None

    def _find_port(self, obj):
        if isinstance(obj, dict):
            typ = str(obj.get("type", obj.get("protocol", ""))).lower()
            for key in ("socks_port", "socksPort", "mixed_port", "mixedPort"):
                value = obj.get(key)
                if isinstance(value, int) and 1 <= value <= 65535:
                    return value
                if (
                    isinstance(value, str)
                    and value.isdigit()
                    and 1 <= int(value) <= 65535
                ):
                    return int(value)
            if typ in ("socks", "socks5", "mixed"):
                for key in ("port", "listen_port", "listenPort"):
                    value = obj.get(key)
                    if isinstance(value, int) and 1 <= value <= 65535:
                        return value
            for value in obj.values():
                result = self._find_port(value)
                if result:
                    return result
        elif isinstance(obj, list):
            for value in obj:
                result = self._find_port(value)
                if result:
                    return result
        return None
