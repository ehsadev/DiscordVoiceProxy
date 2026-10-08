import json
import platform
import subprocess
import urllib.request
from pathlib import Path

from app.models.runtime import RuntimeStatus

METADATA_URL = (
    "https://builds.dotnet.microsoft.com/dotnet/release-metadata/8.0/releases.json"
)


class DotNetService:
    def status(self) -> RuntimeStatus:
        commands = []
        dotnet = self._find_dotnet()
        if dotnet:
            commands.append([str(dotnet), "--list-runtimes"])
        commands.append(["dotnet", "--list-runtimes"])

        seen = set()
        for command in commands:
            key = tuple(command)
            if key in seen:
                continue
            seen.add(key)
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                versions = []
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if (
                        len(parts) >= 2
                        and parts[0] == "Microsoft.NETCore.App"
                        and parts[1].startswith("8.")
                    ):
                        versions.append(parts[1])
                raw = result.stdout + (("\n" + result.stderr) if result.stderr else "")
                if versions:
                    return RuntimeStatus(
                        True, max(versions, key=self._version_key), raw
                    )
            except (FileNotFoundError, subprocess.SubprocessError):
                continue

        return RuntimeStatus(False, None, "Microsoft.NETCore.App 8.x was not detected")

    @staticmethod
    def _version_key(version: str):
        try:
            return tuple(int(x) for x in version.split("."))
        except ValueError:
            return (0,)

    @staticmethod
    def _find_dotnet() -> Path | None:
        candidates = [
            Path(r"C:\Program Files\dotnet\dotnet.exe"),
            Path(r"C:\Program Files (x86)\dotnet\dotnet.exe"),
        ]
        for p in candidates:
            if p.is_file():
                return p
        return None

    @staticmethod
    def get_windows_rid() -> str:
        """Return the Windows Runtime Identifier for the current machine."""

        machine = platform.machine().lower()

        if machine in ("amd64", "x86_64"):
            return "win-x64"

        if machine in ("x86", "i386", "i686"):
            return "win-x86"

        if machine in ("arm64", "aarch64"):
            return "win-arm64"

        raise RuntimeError(f"Unsupported Windows architecture: {machine}")

    def get_latest_runtime_installer_url(self) -> str:
        """Return Microsoft's official .NET 8 runtime installer
        matching the current Windows architecture.
        """

        rid = self.get_windows_rid()
        expected_name = f"dotnet-runtime-{rid}.exe"

        req = urllib.request.Request(
            METADATA_URL,
            headers={"User-Agent": "DiscordVoiceProxyManager/1.0"},
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.load(response)

        latest = data.get("latest-release")
        releases = data.get("releases", [])

        # Prefer the exact latest release advertised by Microsoft.
        candidates = [
            release for release in releases if release.get("release-version") == latest
        ]

        # Be resilient if metadata is temporarily inconsistent.
        if not candidates:
            candidates = releases

        for release in candidates:
            runtime = release.get("runtime") or {}
            files = runtime.get("files") or release.get("files") or []

            for file in files:
                name = str(file.get("name", "")).lower()
                file_rid = str(file.get("rid", "")).lower()
                url = str(file.get("url", ""))

                if (
                    file_rid == rid
                    and name == expected_name.lower()
                    and url.startswith("https://builds.dotnet.microsoft.com/")
                ):
                    return url

        raise RuntimeError(
            f"Microsoft .NET 8 runtime installer was not found "
            f"for Windows architecture: {rid}"
        )

    # def get_latest_runtime_installer_url(self) -> str:
    #     """Return Microsoft's official .NET 8 x64 runtime EXE.

    #     The release metadata is nested under `release.runtime.files`.
    #     Older code incorrectly searched `release.files`, which made the
    #     installer appear to be missing even though Microsoft published it.
    #     """
    #     req = urllib.request.Request(
    #         METADATA_URL,
    #         headers={"User-Agent": "DiscordVoiceProxyManager/1.0"},
    #     )
    #     with urllib.request.urlopen(req, timeout=30) as response:
    #         data = json.load(response)

    #     latest = data.get("latest-release")
    #     releases = data.get("releases", [])

    #     # Prefer the exact latest release advertised by the metadata.
    #     candidates = [
    #         release for release in releases if release.get("release-version") == latest
    #     ]
    #     # Be resilient if the metadata is temporarily inconsistent.
    #     if not candidates:
    #         candidates = releases

    #     for release in candidates:
    #         runtime = release.get("runtime") or {}
    #         files = runtime.get("files") or release.get("files") or []
    #         for file in files:
    #             name = str(file.get("name", "")).lower()
    #             rid = str(file.get("rid", "")).lower()
    #             url = str(file.get("url", ""))
    #             if (
    #                 rid == "win-x64"
    #                 and name == "dotnet-runtime-win-x64.exe"
    #                 and url.startswith("https://builds.dotnet.microsoft.com/")
    #             ):
    #                 return url

    #     raise RuntimeError(
    #         "Microsoft .NET 8 x64 runtime installer was not found in release metadata"
    #     )

    def download_installer(self, destination: Path, progress=None) -> None:
        url = self.get_latest_runtime_installer_url()
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DiscordVoiceProxyManager/1.0"},
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (
            urllib.request.urlopen(req, timeout=120) as response,
            destination.open("wb") as f,
        ):
            total = int(response.headers.get("Content-Length", "0"))
            done = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)

    def install_and_verify(self, installer: Path) -> RuntimeStatus:
        if not installer.is_file():
            raise FileNotFoundError(".NET runtime installer was not downloaded")

        result = subprocess.run(
            [str(installer), "/install", "/quiet", "/norestart"],
            check=False,
            timeout=600,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        # 0 = success, 3010 = success/reboot required.
        if result.returncode not in (0, 3010):
            raise RuntimeError(
                f".NET installer failed with exit code {result.returncode}"
            )

        status = self.status()
        if not status.installed:
            raise RuntimeError(
                ".NET installer finished, but Microsoft.NETCore.App 8.x was not detected"
            )
        return status
