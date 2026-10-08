import json
import os
import subprocess
from pathlib import Path

from app.models.proxy import ProxyConfiguration

from .base import ProxyDetector
from .probe import is_socks5


class V2RayNDetector(ProxyDetector):
    name = "v2rayN"
    common_ports = (10808, 1080, 10809, 10801, 2080, 7890, 7891)

    def detect(self):
        # v2rayN is portable and may live anywhere. Prefer the running
        # executable's directory, then inspect common/user-selected locations.
        roots = self._candidate_roots()

        for root in roots:
            for config in self._candidate_configs(root):
                data = self._read_json(config)
                if data is None:
                    continue
                for host, port in self._find_endpoints(data):
                    if is_socks5(host, port):
                        return ProxyConfiguration(host, port)

        # If v2rayN has enabled Windows system proxy, the registry can reveal
        # a custom SOCKS endpoint even when the portable app directory cannot.
        registry = self._system_proxy_socks()
        if registry and is_socks5(*registry):
            return ProxyConfiguration(*registry)

        # Configuration may be unavailable while v2rayN is running. Probe
        # likely local SOCKS ports as a safe fallback.
        for port in self.common_ports:
            if is_socks5("127.0.0.1", port):
                return ProxyConfiguration("127.0.0.1", port)
        return None

    def _candidate_roots(self):
        roots = []
        running = self._running_executable_dirs()
        roots.extend(running)
        home = Path.home()
        roots.extend(
            [
                home / "AppData/Roaming/2dust/v2rayN",
                home / "AppData/Local/2dust/v2rayN",
                home / "AppData/Roaming/v2rayN",
                home / "AppData/Local/v2rayN",
                home / ".config/v2rayN",
            ]
        )

        # Portable installations often keep guiConfigs next to v2rayN.exe.
        # Also inspect directories explicitly stored in PATH.
        for entry in os.environ.get("PATH", "").split(os.pathsep):
            if entry:
                roots.append(Path(entry))

        unique = []
        seen = set()
        for root in roots:
            try:
                key = str(root.resolve()).lower()
            except OSError:
                key = str(root).lower()
            if key not in seen and root.exists():
                seen.add(key)
                unique.append(root)
        return unique

    def _candidate_configs(self, root: Path):
        candidates = [
            root / "guiConfigs" / "guiNConfig.json",
            root / "guiNConfig.json",
            root / "config.json",
            root / "guiConfigs" / "config.json",
        ]
        # Don't recursively scan an arbitrary drive. Only search a known
        # application root and keep the scan shallow.
        try:
            for path in root.glob("guiConfigs/*.json"):
                candidates.append(path)
        except OSError:
            pass
        unique = []
        seen = set()
        for path in candidates:
            if path.is_file() and path not in seen:
                seen.add(path)
                unique.append(path)
        return unique

    @staticmethod
    def _read_json(path: Path):
        try:
            if path.stat().st_size > 8 * 1024 * 1024:
                return None
            return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
        except (OSError, ValueError):
            return None

    def _find_endpoints(self, obj, inherited_host="127.0.0.1"):
        if isinstance(obj, dict):
            host = (
                obj.get("listen")
                or obj.get("listenAddress")
                or obj.get("address")
                or inherited_host
            )
            if str(host) in ("0.0.0.0", "::", "[::]"):
                host = "127.0.0.1"
            protocol = str(obj.get("protocol", obj.get("type", ""))).lower()

            # Current v2rayN uses an Inbound object with LocalPort.
            for key in (
                "LocalPort",
                "localPort",
                "socksPort",
                "socks5Port",
                "socks_port",
                "mixedPort",
                "mixed_port",
            ):
                port = self._port(obj.get(key))
                if port and (
                    key.lower().startswith("socks")
                    or "mixed" in key.lower()
                    or key.lower() == "localport"
                ):
                    yield str(host), port

            if protocol in ("socks", "socks5", "mixed"):
                for key in (
                    "port",
                    "listen_port",
                    "listenPort",
                    "LocalPort",
                    "localPort",
                ):
                    port = self._port(obj.get(key))
                    if port:
                        yield str(host), port

            for key, value in obj.items():
                child_host = (
                    host
                    if key.lower() in ("listen", "listenaddress", "address")
                    else inherited_host
                )
                yield from self._find_endpoints(value, child_host)

        elif isinstance(obj, list):
            for value in obj:
                yield from self._find_endpoints(value, inherited_host)

    @staticmethod
    def _system_proxy_socks():
        if os.name != "nt":
            return None
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            )
            value, _ = winreg.QueryValueEx(key, "ProxyServer")
            winreg.CloseKey(key)
            text = str(value)
            # Examples: socks=127.0.0.1:10808;http=... or 127.0.0.1:10808
            for part in text.split(";"):
                part = part.strip()
                if part.lower().startswith("socks="):
                    part = part.split("=", 1)[1]
                elif "=" in part:
                    continue
                if ":" in part:
                    host, port = part.rsplit(":", 1)
                    try:
                        port = int(port)
                    except ValueError:
                        continue
                    if 1 <= port <= 65535:
                        return host or "127.0.0.1", port
        except (OSError, ImportError):
            pass
        return None

    @staticmethod
    def _port(value):
        try:
            port = int(value)
            return port if 1 <= port <= 65535 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _running_executable_dirs():
        if os.name != "nt":
            return []
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq v2rayN.exe", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if not result.stdout.strip() or "v2rayN.exe" not in result.stdout:
                return []

            # tasklist doesn't expose executable paths. Ask PowerShell only
            # when the process is actually running.
            ps = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-Process -Name v2rayN -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path)",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            dirs = []
            for line in ps.stdout.splitlines():
                if line.strip():
                    try:
                        dirs.append(Path(line.strip()).parent)
                    except OSError:
                        pass
            return dirs
        except (OSError, subprocess.SubprocessError):
            return []
