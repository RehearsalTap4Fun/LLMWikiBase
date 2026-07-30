"""Narrow subprocess bridge to the installed Confluence Skill's raw GET client."""

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import parse_qs, urljoin, urlparse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confluence-cli", type=Path, required=True)
    subcommands = parser.add_subparsers(dest="command", required=True)
    children = subcommands.add_parser("children")
    children.add_argument("page_id")
    children.add_argument("--start", type=int, required=True)
    children.add_argument("--limit", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if not arguments.page_id.isascii() or not arguments.page_id.isdigit():
        return _error("invalid-page-id")
    if arguments.start < 0 or arguments.limit <= 0:
        return _error("invalid-pagination")
    try:
        sys.path.insert(0, str(arguments.confluence_cli))
        from confluence_skill.client import ConfluenceClient

        response = ConfluenceClient().get(
            f"/content/{arguments.page_id}/child/page",
            params={
                "start": arguments.start,
                "limit": arguments.limit,
                "expand": "space,version,history.lastUpdated",
            },
        )
        payload = _normalize_page(response, arguments.page_id)
    except BaseException:
        return _error("upstream-request-failed")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


def _normalize_page(response: object, page_id: str) -> dict:
    if not isinstance(response, dict):
        raise ValueError("invalid response")
    results = response.get("results")
    links = response.get("_links")
    if not isinstance(results, list) or not isinstance(links, dict):
        raise ValueError("invalid response")
    total = _optional_integer(response, "total", minimum=0)
    start = _integer(response, "start", minimum=0)
    limit = _integer(response, "limit", minimum=1)
    size = _integer(response, "size", minimum=0)
    if size != len(results):
        raise ValueError("invalid response")
    base_url = str(links.get("base") or os.environ.get("CONFLUENCE_URL") or "")
    normalized = [_normalize_result(item, base_url) for item in results]
    next_start, next_limit = _next_cursor(links.get("next"), page_id, base_url)
    return {
        "total": total,
        "start": start,
        "limit": limit,
        "size": size,
        "has_next": bool(links.get("next")),
        "next_start": next_start,
        "next_limit": next_limit,
        "results": normalized,
    }


def _normalize_result(item: object, base_url: str) -> dict:
    if not isinstance(item, dict):
        raise ValueError("invalid result")
    space = item.get("space")
    version = item.get("version")
    links = item.get("_links")
    if not isinstance(space, dict) or not isinstance(version, dict) or not isinstance(links, dict):
        raise ValueError("invalid result")
    page_id = str(item["id"])
    webui = links.get("webui")
    if not isinstance(webui, str):
        raise ValueError("invalid result")
    history = item.get("history")
    last_updated = history.get("lastUpdated") if isinstance(history, dict) else None
    updated_at = last_updated.get("when") if isinstance(last_updated, dict) else None
    return {
        "id": page_id,
        "title": str(item["title"]),
        "status": str(item["status"]),
        "space": str(space["key"]),
        "version": _integer(version, "number", minimum=1),
        "url": urljoin(base_url.rstrip("/") + "/", webui.lstrip("/")),
        "wiki_updated_at": updated_at if isinstance(updated_at, str) else None,
    }


def _integer(mapping: dict, key: str, *, minimum: int) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError("invalid integer")
    return value


def _optional_integer(mapping: dict, key: str, *, minimum: int) -> int | None:
    if key not in mapping:
        return None
    return _integer(mapping, key, minimum=minimum)


def _next_cursor(value: object, page_id: str, base_url: str) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    if not isinstance(value, str):
        raise ValueError("invalid next link")
    parsed = urlparse(value)
    if parsed.fragment or parsed.username is not None or parsed.password is not None:
        raise ValueError("invalid next link")
    if parsed.netloc:
        base = urlparse(base_url)
        if parsed.scheme.casefold() != "https" or parsed.hostname != base.hostname:
            raise ValueError("invalid next link")
    if not parsed.path.endswith(f"/content/{page_id}/child/page"):
        raise ValueError("invalid next link")
    query = parse_qs(parsed.query, keep_blank_values=True)
    starts = query.get("start", [])
    limits = query.get("limit", [])
    if len(starts) != 1 or len(limits) != 1:
        raise ValueError("invalid next link")
    try:
        start = int(starts[0])
        limit = int(limits[0])
    except ValueError as error:
        raise ValueError("invalid next link") from error
    if start < 0 or limit <= 0:
        raise ValueError("invalid next link")
    return start, limit


def _error(code: str) -> int:
    print(json.dumps({"status": "error", "error_code": code}, sort_keys=True))
    print(f"Confluence bridge failed ({code}).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
