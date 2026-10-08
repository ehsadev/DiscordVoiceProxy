import json
from pathlib import Path

from app.models.proxy import ProxyConfiguration

from .base import ProxyDetector
from .probe import is_socks5


class InvisibleManDetector(ProxyDetector):
    name = "Invisible Man - XRay"
    roots = [
        Path.home() / "AppData/Roaming/Invisible Man",
        Path.home() / "AppData/Local/Invisible Man",
        Path.home() / "AppData/Roaming/Invisible Man - XRay",
    ]
    common_ports = (1080, 10808, 2080, 7890)

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
                port = self._find_socks_port(data)
                if port and is_socks5("127.0.0.1", port):
                    return ProxyConfiguration("127.0.0.1", port)
        for port in self.common_ports:
            if is_socks5("127.0.0.1", port):
                return ProxyConfiguration("127.0.0.1", port)
        return None

    def _find_socks_port(self, obj):
        if isinstance(obj, dict):
            protocol = str(obj.get("protocol", obj.get("type", ""))).lower()
            if protocol in ("socks", "socks5"):
                for key in ("port", "listen_port", "listenPort"):
                    value = obj.get(key)
                    if isinstance(value, int) and 1 <= value <= 65535:
                        return value
            for value in obj.values():
                result = self._find_socks_port(value)
                if result:
                    return result
        elif isinstance(obj, list):
            for value in obj:
                result = self._find_socks_port(value)
                if result:
                    return result
        return None
