# Discord Voice Proxy Manager

A PySide6 Windows GUI manager for the official `runetfreedom/discord-voice-proxy` release. It does not implement or rebuild the proxy DLLs.

## Run from source

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.main
```

## Build

Run PowerShell:

```powershell
.\build.ps1
```

## Notes

- Requires Windows and a Discord installation under `%LOCALAPPDATA%\Discord`.
- Downloads `DWrite.dll` and `force-proxy.dll` only from the official GitHub release API.
- Requires `Microsoft.NETCore.App 8.x` rather than the Windows Desktop runtime.
- Backups/manifests are stored under `%LOCALAPPDATA%\DiscordVoiceProxyManager`.
- The manager never injects a DLL, patches Discord, or implements a proxy.
