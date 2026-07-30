import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Mapping

from .models import ConfluenceCommandError, PageUnavailableError
from .url_safety import validate_page_url


REQUIRED_ENV = (
    "CONFLUENCE_URL",
    "CONFLUENCE_EMAIL",
    "CONFLUENCE_API_TOKEN",
)


def resolve_confluence_environment(
    process_env: Mapping[str, str], user_reader: Callable[[str], str | None]
) -> dict[str, str]:
    resolved = {}
    for name in REQUIRED_ENV:
        value = process_env.get(name) or user_reader(name)
        if not value:
            raise ConfluenceCommandError(f"Missing environment variable: {name}")
        resolved[name] = value
    return resolved


class CliConfluenceClient:
    def __init__(
        self,
        cli_path: Path,
        environment: Mapping[str, str] | None = None,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._cli_path = Path(cli_path)
        self._environment = dict(environment) if environment is not None else dict(os.environ)
        self._runner = runner
        self._bridge_path = Path(__file__).with_name("confluence_bridge.py")

    @property
    def base_url(self) -> str | None:
        return self._environment.get("CONFLUENCE_URL")

    def check(self) -> None:
        self._run(("check",))

    def children(self, page_id: str, limit: int) -> dict:
        if limit <= 0:
            raise ValueError("child page size must be greater than zero")
        results: list[dict] = []
        seen_ids: set[str] = set()
        start = 0
        expected_total: int | None = None
        total_mode: bool | None = None
        while True:
            page = self._run_bridge_children(page_id, start, limit)
            raw_total = page.get("total")
            has_total = raw_total is not None
            if total_mode is None:
                total_mode = has_total
            elif has_total != total_mode:
                raise _pagination_error()
            total = _strict_non_negative_int(raw_total) if has_total else None
            response_start = _strict_non_negative_int(page.get("start"))
            response_limit = _strict_positive_int(page.get("limit"))
            size = _strict_non_negative_int(page.get("size"))
            page_results = page.get("results")
            has_next = page.get("has_next")
            next_start = page.get("next_start")
            next_limit = page.get("next_limit")
            if not isinstance(page_results, list) or not isinstance(has_next, bool):
                raise _pagination_error()
            if response_start != start or size != len(page_results) or size > response_limit:
                raise _pagination_error()
            if total is not None:
                if expected_total is None:
                    expected_total = total
                elif total != expected_total:
                    raise _pagination_error()
                if start + size > total or has_next != (start + size < total):
                    raise _pagination_error()
            if has_next and size == 0:
                raise _pagination_error()
            if has_next:
                if total is None and (next_start is None or next_limit is None):
                    raise _pagination_error()
                if next_start is not None and _strict_non_negative_int(next_start) != start + size:
                    raise _pagination_error()
                if next_limit is not None and _strict_positive_int(next_limit) != response_limit:
                    raise _pagination_error()
            elif next_start is not None or next_limit is not None:
                raise _pagination_error()
            for item in page_results:
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    raise _pagination_error()
                if item["id"] in seen_ids:
                    raise _pagination_error()
                if self.base_url is not None:
                    try:
                        validate_page_url(str(item.get("url", "")), item["id"], self.base_url)
                    except ValueError as error:
                        raise ConfluenceCommandError(
                            "Confluence returned an unsafe page URL", code="unsafe-url"
                        ) from error
                seen_ids.add(item["id"])
                results.append(item)
            if not has_next:
                break
            start = start + size if next_start is None else next_start
        if expected_total is not None and len(results) != expected_total:
            raise _pagination_error()
        return {"total": len(results), "results": results, "complete": True}

    def page(self, page_id: str) -> dict:
        return self._run(("page", "get", page_id), unavailable_page_id=page_id)

    def _run(self, arguments: tuple[str, ...], unavailable_page_id: str | None = None) -> dict:
        command = [sys.executable, str(self._cli_path), *arguments]
        result = self._invoke(command)
        if result.returncode != 0:
            if unavailable_page_id is not None:
                status_code = self._unavailable_status(result.stderr)
                if status_code is not None:
                    raise PageUnavailableError(unavailable_page_id, status_code)
            raise ConfluenceCommandError()
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ConfluenceCommandError(code="invalid-json") from error

    def _run_bridge_children(self, page_id: str, start: int, limit: int) -> dict:
        command = [
            sys.executable,
            str(self._bridge_path),
            "--confluence-cli",
            str(self._cli_path),
            "children",
            page_id,
            "--start",
            str(start),
            "--limit",
            str(limit),
        ]
        result = self._invoke(command)
        if result.returncode != 0:
            raise ConfluenceCommandError(code="confluence-bridge-failed")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ConfluenceCommandError(code="invalid-json") from error
        if not isinstance(payload, dict):
            raise ConfluenceCommandError(code="invalid-json")
        return payload

    def _invoke(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="k1-confluence-") as private_temp_name:
            private_temp = Path(private_temp_name)
            (private_temp / "confluence-skill.log").mkdir()
            environment = self._environment.copy()
            for name in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT"):
                if name not in environment and os.environ.get(name):
                    environment[name] = os.environ[name]
            environment["PYTHONIOENCODING"] = "utf-8"
            environment["TEMP"] = str(private_temp)
            environment["TMP"] = str(private_temp)
            return self._runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
            )

    @staticmethod
    def _unavailable_status(stderr: str) -> int | None:
        matches = [
            *re.findall(r"\bHTTP(?:\s+status)?\s*[:=]?\s*([1-5][0-9]{2})\b", stderr, re.IGNORECASE),
            *re.findall(r'["\']statusCode["\']\s*:\s*([1-5][0-9]{2})\b', stderr),
        ]
        if len(matches) != 1:
            return None
        status_code = int(matches[0])
        return status_code if status_code in (403, 404) else None

    def _redact(self, message: str) -> str:
        for value in self._environment.values():
            if value:
                message = message.replace(value, "***")
        return message


def _strict_non_negative_int(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _pagination_error()
    return value


def _strict_positive_int(value) -> int:
    result = _strict_non_negative_int(value)
    if result == 0:
        raise _pagination_error()
    return result


def _pagination_error() -> ConfluenceCommandError:
    return ConfluenceCommandError(
        "Confluence child pagination is incomplete or inconsistent",
        code="incomplete-pagination",
    )
