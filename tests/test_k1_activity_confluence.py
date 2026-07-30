import subprocess
import json
import os
from pathlib import Path

import pytest

from tools.k1_activity_index.confluence import (
    CliConfluenceClient,
    ConfluenceCommandError,
    resolve_confluence_environment,
)
from tools.k1_activity_index.models import PageUnavailableError


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


def _bridge_page(page_id: str) -> dict:
    return {
        "id": page_id,
        "title": f"Page {page_id}",
        "status": "current",
        "space": "KEFU",
        "version": 1,
        "url": f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
    }


def test_children_adapter_pages_until_real_server_total_is_complete(tmp_path: Path):
    calls: list[int] = []

    def runner(command, **kwargs):
        start = int(command[command.index("--start") + 1])
        limit = int(command[command.index("--limit") + 1])
        calls.append(start)
        all_pages = [_bridge_page(str(page_id)) for page_id in range(100, 105)]
        results = all_pages[start : start + limit]
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "total": 5,
                    "start": start,
                    "limit": limit,
                    "size": len(results),
                    "has_next": start + len(results) < 5,
                    "results": results,
                }
            ),
            stderr="",
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

    response = client.children("73598402", 2)

    assert calls == [0, 2, 4]
    assert response["total"] == 5
    assert response["complete"] is True
    assert [page["id"] for page in response["results"]] == ["100", "101", "102", "103", "104"]


@pytest.mark.parametrize(
    "second_page",
    (
        {"total": 6, "start": 2, "limit": 2, "size": 2, "has_next": True},
        {"total": 5, "start": 1, "limit": 2, "size": 2, "has_next": True},
        {"total": 5, "start": 2, "limit": 2, "size": 0, "has_next": True},
    ),
)
def test_children_adapter_fails_closed_on_inconsistent_pagination(tmp_path: Path, second_page):
    def runner(command, **kwargs):
        start = int(command[command.index("--start") + 1])
        if start == 0:
            payload = {
                "total": 5,
                "start": 0,
                "limit": 2,
                "size": 2,
                "has_next": True,
                "results": [_bridge_page("100"), _bridge_page("101")],
            }
        else:
            payload = dict(second_page)
            payload["results"] = (
                [] if payload["size"] == 0 else [_bridge_page("102"), _bridge_page("103")]
            )
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    client = CliConfluenceClient(
        cli_path=tmp_path / "confluence.pyz",
        environment={"CONFLUENCE_URL": "https://wiki.example.test"},
        runner=runner,
    )

    with pytest.raises(ConfluenceCommandError) as error:
        client.children("73598402", 2)

    assert getattr(error.value, "code", None) == "incomplete-pagination"


def test_children_adapter_rejects_url_on_a_different_host(tmp_path: Path):
    page = _bridge_page("100")
    page["url"] = "https://evil.example.test/pages/viewpage.action?pageId=100"

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"total": 1, "start": 0, "limit": 10, "size": 1, "has_next": False, "results": [page]}),
            "",
        )

    client = CliConfluenceClient(
        tmp_path / "confluence.pyz",
        {"CONFLUENCE_URL": "https://wiki.example.test"},
        runner,
    )

    with pytest.raises(ConfluenceCommandError) as error:
        client.children("73598402", 10)

    assert error.value.code == "unsafe-url"


def test_children_adapter_requires_explicit_next_cursor_when_total_is_unavailable(tmp_path: Path):
    def runner(command, **kwargs):
        start = int(command[command.index("--start") + 1])
        results = [_bridge_page("100"), _bridge_page("101")] if start == 0 else [_bridge_page("102")]
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(
                {
                    "total": None,
                    "start": start,
                    "limit": 2,
                    "size": len(results),
                    "has_next": start == 0,
                    "next_start": None,
                    "next_limit": None,
                    "results": results,
                }
            ),
            "",
        )

    client = CliConfluenceClient(
        tmp_path / "confluence.pyz",
        {"CONFLUENCE_URL": "https://wiki.example.test"},
        runner,
    )

    with pytest.raises(ConfluenceCommandError) as error:
        client.children("73598402", 2)

    assert error.value.code == "incomplete-pagination"


def test_every_subprocess_uses_cleaned_private_temp_with_non_writable_log_path(tmp_path: Path):
    fake_cli = tmp_path / "fake_cli.py"
    fake_cli.write_text(
        "import json, os, pathlib\n"
        "log = pathlib.Path(os.environ['TEMP']) / 'confluence-skill.log'\n"
        "try:\n"
        "    log.write_text('SENSITIVE RESPONSE BODY', encoding='utf-8')\n"
        "except OSError:\n"
        "    pass\n"
        "print(json.dumps({}))\n",
        encoding="utf-8",
    )
    system_log = Path(os.environ.get("TEMP", str(tmp_path))) / "confluence-skill.log"
    before = system_log.read_bytes() if system_log.is_file() else None
    observed_private_temps: list[Path] = []

    def runner(command, **kwargs):
        private_temp = Path(kwargs["env"]["TEMP"])
        observed_private_temps.append(private_temp)
        assert private_temp == Path(kwargs["env"]["TMP"])
        assert (private_temp / "confluence-skill.log").is_dir()
        return subprocess.run(command, **kwargs)

    client = CliConfluenceClient(
        cli_path=fake_cli,
        environment={"CONFLUENCE_URL": "https://wiki.example.test"},
        runner=runner,
    )
    client.check()

    assert observed_private_temps and all(not path.exists() for path in observed_private_temps)
    assert (system_log.read_bytes() if system_log.is_file() else None) == before


def test_bridge_integration_preserves_total_across_multiple_raw_api_pages(tmp_path: Path):
    skill_root = tmp_path / "synthetic_skill"
    package = skill_root / "confluence_skill"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "client.py").write_text(
        "import os, pathlib\n"
        "class ConfluenceClient:\n"
        "    def get(self, path, params=None):\n"
        "        log = pathlib.Path(os.environ['TEMP']) / 'confluence-skill.log'\n"
        "        try:\n"
        "            log.write_text('PRIVATE BODY', encoding='utf-8')\n"
        "        except OSError:\n"
        "            pass\n"
        "        start, limit, total = params['start'], params['limit'], 5\n"
        "        ids = [str(value) for value in range(100, 105)][start:start + limit]\n"
        "        return {'start': start, 'limit': limit, 'size': len(ids), "
        "'_links': {'base': 'https://wiki.example.test', 'next': ('/rest/api/content/73598402/child/page?start=' + str(start + len(ids)) + '&limit=' + str(limit)) if start + len(ids) < total else None}, "
        "'results': [{'id': page_id, 'title': 'Page ' + page_id, 'status': 'current', "
        "'space': {'key': 'KEFU'}, 'version': {'number': 7}, "
        "'_links': {'webui': '/pages/viewpage.action?pageId=' + page_id}} for page_id in ids]}\n",
        encoding="utf-8",
    )
    client = CliConfluenceClient(
        cli_path=skill_root,
        environment={"CONFLUENCE_URL": "https://wiki.example.test"},
    )

    response = client.children("73598402", 2)

    assert response["total"] == 5
    assert response["complete"] is True
    assert [page["id"] for page in response["results"]] == ["100", "101", "102", "103", "104"]


@pytest.mark.parametrize(
    ("diagnostic", "status"),
    (("Error: HTTP 403: forbidden", 403), ('Error: {"statusCode": 404}', 404)),
)
def test_page_unavailable_accepts_only_one_explicit_http_status(tmp_path: Path, diagnostic: str, status: int):
    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", diagnostic)

    client = CliConfluenceClient(tmp_path / "confluence.pyz", {}, runner)

    with pytest.raises(PageUnavailableError) as error:
        client.page("9001")

    assert error.value.status_code == status


@pytest.mark.parametrize(
    "diagnostic",
    (
        "pageId=403404 failed with HTTP 500",
        'HTTP 403 then {"statusCode": 500}',
        'HTTP 404 then {"statusCode": 404}',
        "network request for pageId 404 failed",
    ),
)
def test_page_unavailable_rejects_incidental_conflicting_or_multiple_statuses(tmp_path: Path, diagnostic: str):
    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", diagnostic)

    client = CliConfluenceClient(tmp_path / "confluence.pyz", {}, runner)

    with pytest.raises(ConfluenceCommandError) as error:
        client.page("403404")

    assert not isinstance(error.value, PageUnavailableError)
    assert diagnostic not in str(error.value)


def test_cli_error_never_propagates_basic_bearer_cookie_multiline_or_encoded_credentials(tmp_path: Path):
    secrets = (
        "Basic dXNlcjpzZWNyZXQ=",
        "Bearer eyJhbGciOiJIUzI1NiJ9.secret",
        "Cookie: session=raw-cookie-value",
        "token%3Draw%2Bencoded%2Fvalue",
        "pageId=403404",
    )

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "\n".join(secrets))

    client = CliConfluenceClient(tmp_path / "confluence.pyz", {}, runner)

    with pytest.raises(ConfluenceCommandError) as error:
        client.check()

    rendered = str(error.value)
    assert rendered == "Confluence command failed"
    assert all(value not in rendered for value in secrets)
