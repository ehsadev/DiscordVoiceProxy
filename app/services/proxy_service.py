import shutil
import tempfile
from pathlib import Path

from app.models.proxy import ProxyConfiguration, ProxyState, ProxyStatus
from app.services.backup_service import BackupService
from app.services.github_service import GitHubService


class ProxyService:
    REQUIRED = ("DWrite.dll", "force-proxy.dll", "proxy.txt")

    def __init__(
        self, github: GitHubService | None = None, backup: BackupService | None = None
    ):
        self.github = github or GitHubService()
        self.backup = backup or BackupService()

    def parse_config(self, path: Path) -> ProxyConfiguration | None:
        if not path.is_file():
            return None
        values = {}
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
        host = values.get("SOCKS5_PROXY_ADDRESS", "")
        port = values.get("SOCKS5_PROXY_PORT", "")
        try:
            port_i = int(port)
        except (TypeError, ValueError):
            return None
        if not host or not 1 <= port_i <= 65535:
            return None
        return ProxyConfiguration(
            host,
            port_i,
            values.get("SOCKS5_PROXY_LOGIN") or None,
            values.get("SOCKS5_PROXY_PASSWORD") or None,
        )

    def write_config(self, path: Path, cfg: ProxyConfiguration) -> None:
        lines = [f"SOCKS5_PROXY_ADDRESS={cfg.host}", f"SOCKS5_PROXY_PORT={cfg.port}"]
        if cfg.username:
            lines.append(f"SOCKS5_PROXY_LOGIN={cfg.username}")
        if cfg.password:
            lines.append(f"SOCKS5_PROXY_PASSWORD={cfg.password}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def status(self, app_dir: Path | None) -> ProxyStatus:
        if not app_dir or not app_dir.is_dir():
            return ProxyStatus(
                ProxyState.NOT_INSTALLED,
                None,
                message="Discord application directory not found",
            )
        d = (app_dir / "DWrite.dll").is_file()
        f = (app_dir / "force-proxy.dll").is_file()
        c = (app_dir / "proxy.txt").is_file()
        if not (d or f or c):
            return ProxyStatus(ProxyState.NOT_INSTALLED, str(app_dir), d, f, c)
        if not (d and f and c):
            return ProxyStatus(ProxyState.PARTIAL, str(app_dir), d, f, c)
        if not self.parse_config(app_dir / "proxy.txt"):
            return ProxyStatus(ProxyState.INVALID_CONFIGURATION, str(app_dir), d, f, c)
        return ProxyStatus(ProxyState.INSTALLED, str(app_dir), d, f, c)

    def install(self, app_dir: Path, cfg: ProxyConfiguration, progress=None) -> None:
        if not app_dir.is_dir():
            raise FileNotFoundError("Discord app directory not found")
        self.backup.prepare(app_dir, ["DWrite.dll", "force-proxy.dll"])
        release = self.github.get_latest_release()
        by_name = {a.name.lower(): a for a in release.assets}
        d_asset = by_name.get("dwrite.dll")
        f_asset = by_name.get("force-proxy.dll")
        if not d_asset or not f_asset:
            raise RuntimeError(
                "Latest GitHub release does not contain required DLL assets"
            )
        with tempfile.TemporaryDirectory(prefix="discord-proxy-") as td:
            td_path = Path(td)
            d_tmp, f_tmp = td_path / "DWrite.dll", td_path / "force-proxy.dll"
            self.github.download_asset(d_asset, d_tmp, progress)
            self.github.download_asset(f_asset, f_tmp, progress)
            shutil.copy2(d_tmp, app_dir / "DWrite.dll")
            shutil.copy2(f_tmp, app_dir / "force-proxy.dll")
        self.write_config(app_dir / "proxy.txt", cfg)
        st = self.status(app_dir)
        if st.state != ProxyState.INSTALLED:
            raise RuntimeError(f"Proxy verification failed: {st.state.value}")

    def remove(self, app_dir: Path) -> None:
        self.backup.restore_and_remove(app_dir, ["DWrite.dll", "force-proxy.dll"])
        st = self.status(app_dir)
        if st.state != ProxyState.NOT_INSTALLED:
            raise RuntimeError("Proxy removal could not be verified")
