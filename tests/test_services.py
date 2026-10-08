from pathlib import Path

from app.models.proxy import ProxyConfiguration, ProxyState
from app.services.proxy_service import ProxyService


def test_proxy_config_roundtrip(tmp_path: Path):
    s = ProxyService()
    p = tmp_path / "proxy.txt"
    c = ProxyConfiguration("127.0.0.1", 10808, "u", "p")
    s.write_config(p, c)
    assert s.parse_config(p) == c


def test_status(tmp_path: Path):
    s = ProxyService()
    assert s.status(tmp_path).state == ProxyState.NOT_INSTALLED
    (tmp_path / "DWrite.dll").write_bytes(b"x")
    assert s.status(tmp_path).state == ProxyState.PARTIAL
