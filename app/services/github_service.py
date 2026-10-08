import hashlib
from dataclasses import dataclass
from pathlib import Path

import httpx

API = "https://api.github.com/repos/runetfreedom/discord-voice-proxy/releases/latest"
ALLOWED_HOST = "github.com"


@dataclass(slots=True)
class ReleaseAsset:
    name: str
    url: str
    size: int
    digest: str | None = None


@dataclass(slots=True)
class Release:
    tag: str
    name: str
    assets: list[ReleaseAsset]


class GitHubService:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def get_latest_release(self) -> Release:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "DiscordVoiceProxyManager/1.0",
        }
        with httpx.Client(
            timeout=self.timeout, follow_redirects=True, headers=headers
        ) as client:
            r = client.get(API)
            r.raise_for_status()
            data = r.json()
        assets = [
            ReleaseAsset(
                a["name"],
                a["browser_download_url"],
                int(a.get("size", 0)),
                a.get("digest"),
            )
            for a in data.get("assets", [])
        ]
        return Release(data.get("tag_name", ""), data.get("name", ""), assets)

    def get_release_assets(self) -> list[ReleaseAsset]:
        return self.get_latest_release().assets

    def download_asset(
        self, asset: ReleaseAsset, destination: Path, progress=None
    ) -> None:
        if not asset.url.startswith("https://github.com/"):
            raise ValueError("Refusing download from an untrusted host")
        destination.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256()
        headers = {"User-Agent": "DiscordVoiceProxyManager/1.0"}
        with httpx.stream(
            "GET",
            asset.url,
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers,
        ) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", asset.size or 0))
            done = 0
            with destination.open("wb") as f:
                for chunk in r.iter_bytes(1024 * 1024):
                    f.write(chunk)
                    h.update(chunk)
                    done += len(chunk)
                    if progress:
                        progress(done, total)
        if asset.digest:
            expected = asset.digest.split(":", 1)[-1].lower()
            if h.hexdigest().lower() != expected:
                destination.unlink(missing_ok=True)
                raise ValueError(f"SHA-256 mismatch for {asset.name}")
