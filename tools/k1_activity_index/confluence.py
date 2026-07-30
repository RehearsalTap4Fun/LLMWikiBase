import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping

from .models import ConfluenceCommandError, PageUnavailableError


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

    def check(self) -> None:
        self._run(("check",))

    def children(self, page_id: str, limit: int) -> dict:
        return self._run(("page", "children", page_id, "--limit", str(limit)))

    def page(self, page_id: str) -> dict:
        return self._run(("page", "get", page_id), unavailable_page_id=page_id)

    def _run(self, arguments: tuple[str, ...], unavailable_page_id: str | None = None) -> dict:
        command = [sys.executable, str(self._cli_path), *arguments]
        environment = self._environment.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        result = self._runner(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )
        if result.returncode != 0:
            if unavailable_page_id is not None:
                status_code = self._unavailable_status(result.stderr)
                if status_code is not None:
                    raise PageUnavailableError(unavailable_page_id, status_code)
            raise ConfluenceCommandError(self._redact(result.stderr or result.stdout))
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ConfluenceCommandError(self._redact(f"Invalid JSON from Confluence CLI: {error}")) from error

    @staticmethod
    def _unavailable_status(stderr: str) -> int | None:
        for status_code in (403, 404):
            if str(status_code) in stderr:
                return status_code
        return None

    def _redact(self, message: str) -> str:
        for value in self._environment.values():
            if value:
                message = message.replace(value, "***")
        return message
