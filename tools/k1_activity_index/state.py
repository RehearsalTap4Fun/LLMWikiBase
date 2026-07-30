"""Metadata-only persisted state for the K1 activity index."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .models import ChangeSet, CrawlSnapshot, IndexState, PageRecord, PageState


_FORBIDDEN_KEYS = {"body", "content", "html", "token", "password", "api_token"}


def _id_key(page_id: str) -> tuple[int, int | str]:
    try:
        return (0, int(page_id))
    except ValueError:
        return (1, page_id)


def _sorted_ids(ids: set[str] | list[str]) -> tuple[str, ...]:
    return tuple(sorted(ids, key=_id_key))


def _from_record(record: PageRecord, aliases: tuple[str, ...] = (), review_needed: bool = True) -> PageState:
    return PageState(
        page_id=record.page_id,
        title=record.title,
        status=record.status,
        space=record.space,
        version=record.version,
        url=record.url,
        parent_id=record.parent_id,
        path=record.path,
        topic_id=record.topic_id,
        wiki_updated_at=record.wiki_updated_at,
        aliases=aliases,
        availability="available",
        review_needed=review_needed,
    )


def compute_next_state(previous: IndexState, snapshot: CrawlSnapshot, synced_at: str) -> tuple[IndexState, ChangeSet]:
    """Merge a crawl snapshot into state without persisting page content."""
    if previous.root_page_id != snapshot.root_page_id:
        raise ValueError("snapshot root_page_id does not match state")

    pages: dict[str, PageState] = {}
    new_ids: set[str] = set()
    version_changed_ids: set[str] = set()
    renamed_ids: set[str] = set()
    moved_ids: set[str] = set()
    missing_ids: set[str] = set()

    for page_id, record in snapshot.pages.items():
        old = previous.pages.get(page_id)
        if old is None:
            pages[page_id] = _from_record(record)
            new_ids.add(page_id)
            continue

        renamed = old.title != record.title
        moved = old.parent_id != record.parent_id
        version_changed = old.version != record.version
        aliases = old.aliases
        if renamed and old.title not in aliases:
            aliases = aliases + (old.title,)
        if renamed:
            renamed_ids.add(page_id)
        if moved:
            moved_ids.add(page_id)
        if version_changed:
            version_changed_ids.add(page_id)
        pages[page_id] = _from_record(
            record,
            aliases=aliases,
            review_needed=old.review_needed or renamed or moved or version_changed,
        )

    for page_id, old in previous.pages.items():
        if page_id not in pages:
            pages[page_id] = replace(old, availability="missing-from-root")
            if old.availability != "missing-from-root":
                missing_ids.add(page_id)

    content_ids = new_ids | version_changed_ids | renamed_ids | moved_ids
    changes = ChangeSet(
        new_ids=_sorted_ids(new_ids),
        version_changed_ids=_sorted_ids(version_changed_ids),
        renamed_ids=_sorted_ids(renamed_ids),
        moved_ids=_sorted_ids(moved_ids),
        missing_ids=_sorted_ids(missing_ids),
        content_ids=_sorted_ids(content_ids),
    )
    return IndexState(1, previous.root_page_id, synced_at, pages), changes


def mark_unavailable(state: IndexState, page_id: str, status_code: int) -> IndexState:
    """Retain page metadata while recording an unavailable HTTP response."""
    if page_id not in state.pages:
        return state
    pages = dict(state.pages)
    pages[page_id] = replace(pages[page_id], availability=f"unavailable-{status_code}")
    return replace(state, pages=pages)


def mark_reviewed(state: IndexState, page_ids: list[str] | tuple[str, ...]) -> IndexState:
    """Clear review flags for state records that still exist."""
    pages = dict(state.pages)
    for page_id in page_ids:
        if page_id in pages:
            pages[page_id] = replace(pages[page_id], review_needed=False)
    return replace(state, pages=pages)


def _to_payload(state: IndexState) -> dict[str, Any]:
    return {
        "schema_version": state.schema_version,
        "root_page_id": state.root_page_id,
        "synced_at": state.synced_at,
        "pages": {
            page_id: {
                "page_id": page.page_id,
                "title": page.title,
                "status": page.status,
                "space": page.space,
                "version": page.version,
                "url": page.url,
                "parent_id": page.parent_id,
                "path": list(page.path),
                "topic_id": page.topic_id,
                "wiki_updated_at": page.wiki_updated_at,
                "aliases": list(page.aliases),
                "availability": page.availability,
                "review_needed": page.review_needed,
            }
            for page_id, page in state.pages.items()
        },
    }


def _reject_forbidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in _FORBIDDEN_KEYS:
                raise ValueError(f"forbidden persisted key: {key}")
            _reject_forbidden_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_forbidden_keys(child)


def dump_state(state: IndexState) -> str:
    payload = _to_payload(state)
    _reject_forbidden_keys(payload)
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_state(path: str | Path, root_page_id: str) -> IndexState:
    """Load a state file, returning a fresh v1 state if it does not yet exist."""
    state_path = Path(path)
    if not state_path.exists():
        return IndexState.empty(root_page_id)

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    _reject_forbidden_keys(payload)
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported state schema version")
    if payload.get("root_page_id") != root_page_id:
        raise ValueError("state root_page_id does not match requested root")
    pages = {
        page_id: PageState(
            page_id=data["page_id"], title=data["title"], status=data["status"],
            space=data["space"], version=data["version"], url=data["url"],
            parent_id=data["parent_id"], path=tuple(data["path"]), topic_id=data["topic_id"],
            wiki_updated_at=data.get("wiki_updated_at"), aliases=tuple(data.get("aliases", [])),
            availability=data["availability"], review_needed=data["review_needed"],
        )
        for page_id, data in payload["pages"].items()
    }
    return IndexState(1, root_page_id, payload.get("synced_at"), pages)
