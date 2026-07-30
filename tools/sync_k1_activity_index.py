"""Command-line entry point for synchronizing the K1 activity index."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.k1_activity_index.confluence import (  # noqa: E402
    CliConfluenceClient,
    REQUIRED_ENV,
    resolve_confluence_environment,
)
from tools.k1_activity_index.models import ConfluenceCommandError  # noqa: E402
from tools.k1_activity_index.service import SyncConfig, sync_index  # noqa: E402


DEFAULT_ROOT_PAGE_ID = "73598402"
DEFAULT_CHILD_LIMIT = 1000


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronize the K1 Confluence activity index")
    parser.add_argument("--root-page-id", default=DEFAULT_ROOT_PAGE_ID)
    parser.add_argument("--child-limit", type=int, default=DEFAULT_CHILD_LIMIT)
    parser.add_argument("--wiki-work-dir", type=Path, default=REPOSITORY_ROOT / "wiki" / "work")
    parser.add_argument(
        "--state-path",
        type=Path,
        default=REPOSITORY_ROOT / ".cache" / "k1-activity-index" / "state.json",
    )
    parser.add_argument(
        "--review-report-path",
        type=Path,
        default=REPOSITORY_ROOT / ".cache" / "k1-activity-index" / "review-report.json",
    )
    parser.add_argument("--confluence-cli", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--validate-only", action="store_true")
    parser.add_argument("--mark-reviewed", action="append", default=[], metavar="PAGE_ID")
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdout()
    arguments = _parser().parse_args(argv)
    config = SyncConfig(
        root_page_id=str(arguments.root_page_id),
        wiki_work_dir=arguments.wiki_work_dir.resolve(strict=False),
        state_path=arguments.state_path.resolve(strict=False),
        review_report_path=arguments.review_report_path.resolve(strict=False),
        child_limit=arguments.child_limit,
        dry_run=arguments.dry_run,
        validate_only=arguments.validate_only,
        mark_reviewed=tuple(str(page_id) for page_id in arguments.mark_reviewed),
    )
    resolved_environment: dict[str, str] = {}
    try:
        if config.child_limit <= 0:
            raise ValueError("child limit must be greater than zero")
        if config.validate_only and config.mark_reviewed:
            raise ValueError("--mark-reviewed cannot be combined with --validate-only")

        client = None
        if not config.validate_only:
            cli_path = _confluence_cli_path(arguments.confluence_cli)
            if not cli_path.is_file():
                raise ConfluenceCommandError(f"Confluence CLI does not exist: {cli_path}")
            resolved_environment = resolve_confluence_environment(
                os.environ,
                _read_user_environment,
            )
            client = CliConfluenceClient(
                cli_path,
                _client_environment(resolved_environment),
            )

        report = sync_index(config, client, _now)
        _print_json(_success_payload(config, report))
        return 0
    except Exception as error:
        _print_json(
            {
                "status": "error",
                "error_type": type(error).__name__,
                "message": _safe_message(error, resolved_environment),
                "root_page_id": config.root_page_id,
                "paths": _paths_payload(config),
            }
        )
        return 1


def _confluence_cli_path(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve(strict=False)
    user_profile = os.environ.get("USERPROFILE")
    profile_path = Path(user_profile) if user_profile else Path.home()
    return (profile_path / ".skills" / "confluence" / "scripts" / "confluence.pyz").resolve(
        strict=False
    )


def _read_user_environment(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value) if value else None
    except OSError:
        return None


def _client_environment(credentials: dict[str, str]) -> dict[str, str]:
    environment = dict(credentials)
    for name in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _success_payload(config: SyncConfig, report) -> dict:
    return {
        "status": "ok",
        "root_page_id": report.root_page_id,
        "topic_count": report.topic_count,
        "page_count": report.page_count,
        "new_count": report.new_count,
        "changed_count": report.changed_count,
        "missing_count": report.missing_count,
        "inaccessible_count": report.inaccessible_count,
        "review_needed": list(report.review_needed),
        "truncated": report.truncated,
        "dry_run": report.dry_run,
        "validate_only": config.validate_only,
        "paths": _paths_payload(config),
    }


def _paths_payload(config: SyncConfig) -> dict[str, str]:
    return {
        "wiki_work_dir": str(config.wiki_work_dir),
        "state": str(config.state_path),
        "review_report": str(config.review_report_path),
    }


def _safe_message(error: Exception, resolved_environment: dict[str, str]) -> str:
    message = str(error) or type(error).__name__
    secret_values = [
        value
        for name in REQUIRED_ENV
        for value in (resolved_environment.get(name), os.environ.get(name))
        if value
    ]
    for value in secret_values:
        message = message.replace(value, "***")
    return message


def _configure_utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
