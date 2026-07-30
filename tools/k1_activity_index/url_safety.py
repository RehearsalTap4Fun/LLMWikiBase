"""Strict URL validation shared by live sync boundaries."""

from urllib.parse import parse_qsl, urlparse


def normalized_confluence_host(base_url: str) -> str:
    parsed = urlparse(base_url)
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.query
        or parsed.path not in ("", "/")
    ):
        raise ValueError("configured Confluence URL must be an HTTPS origin")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("configured Confluence URL must be an HTTPS origin") from error
    if port not in (None, 443):
        raise ValueError("configured Confluence URL must be an HTTPS origin")
    return parsed.hostname.casefold().rstrip(".")


def validate_page_url(url: str, page_id: str, expected_base_url: str) -> None:
    parsed = urlparse(url)
    expected_host = normalized_confluence_host(expected_base_url)
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.hostname.casefold().rstrip(".") != expected_host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.path != "/pages/viewpage.action"
    ):
        raise ValueError("page URL differs from the configured Confluence host")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("page URL differs from the configured Confluence host") from error
    if port not in (None, 443):
        raise ValueError("page URL differs from the configured Confluence host")
    if parse_qsl(parsed.query, keep_blank_values=True) != [("pageId", page_id)]:
        raise ValueError("page URL has a missing, duplicated, or mismatched pageId")
