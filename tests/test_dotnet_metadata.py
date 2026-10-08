import json

from app.services.dotnet_service import DotNetService


def test_dotnet_metadata_uses_nested_runtime_files(monkeypatch):
    payload = {
        "latest-release": "8.0.31",
        "releases": [
            {
                "release-version": "8.0.31",
                "runtime": {
                    "files": [
                        {
                            "name": "dotnet-runtime-win-x64.exe",
                            "rid": "win-x64",
                            "url": "https://builds.dotnet.microsoft.com/dotnet/Runtime/8.0.31/dotnet-runtime-8.0.31-win-x64.exe",
                        }
                    ]
                },
            }
        ],
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())
    assert (
        DotNetService()
        .get_latest_runtime_installer_url()
        .endswith("dotnet-runtime-8.0.31-win-x64.exe")
    )
