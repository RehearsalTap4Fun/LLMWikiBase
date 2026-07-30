import subprocess
from pathlib import Path

import pytest

from tools.k1_activity_index.confluence import (
    CliConfluenceClient,
    ConfluenceCommandError,
    resolve_confluence_environment,
)


def test_environment_falls_back_to_windows_user_scope():
    user_values = {
        "CONFLUENCE_URL": "https://wiki.example.test",
        "CONFLUENCE_EMAIL": "user@example.test",
        "CONFLUENCE_API_TOKEN": "secret-value",
    }
    resolved = resolve_confluence_environment({}, lambda name: user_values.get(name))
    assert resolved == user_values


def test_cli_sets_utf8_and_never_exposes_token(tmp_path: Path):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 1, stdout="", stderr="Error: request failed for secret-value"
        )

    client = CliConfluenceClient(
        cli_path=tmp_path / "confluence.pyz",
        environment={
            "CONFLUENCE_URL": "https://wiki.example.test",
            "CONFLUENCE_EMAIL": "user@example.test",
            "CONFLUENCE_API_TOKEN": "secret-value",
        },
        runner=runner,
    )
    with pytest.raises(ConfluenceCommandError) as error:
        client.check()

    assert "secret-value" not in str(error.value)
    assert calls[0][1]["env"]["PYTHONIOENCODING"] == "utf-8"
