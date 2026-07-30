"""Synchronization orchestration for the K1 Confluence activity index."""

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re

from .crawl import crawl_tree
from .markdown import (
    ChildEntry,
    CuratedTopic,
    ParsedTopic,
    TopicDocument,
    parse_catalog_page,
    parse_existing_topic_page,
    parse_topic_page,
    render_catalog,
    render_topic_page,
    validate_catalog_page,
    validate_topic_page,
)
from .models import ChangeSet, IndexState, PageState, PageUnavailableError
from .path_safety import absolute_unresolved, assert_safe_path, assert_within
from .semantics import draft_page_semantics, draft_topic_summary, normalize_label
from .state import (
    compute_next_state,
    dump_state,
    load_state,
    mark_reviewed,
    mark_unavailable,
)
from .transaction import write_batch_atomic
from .url_safety import validate_page_url


_MANAGED_TOPIC_FILENAME = re.compile(r"^k1-activity-([0-9]+)\.md$", re.ASCII)


@dataclass(frozen=True)
class SyncConfig:
    root_page_id: str
    wiki_work_dir: Path
    state_path: Path
    review_report_path: Path
    child_limit: int
    dry_run: bool
    validate_only: bool
    mark_reviewed: tuple[str, ...]


@dataclass(frozen=True)
class SyncReport:
    root_page_id: str
    topic_count: int
    page_count: int
    new_count: int
    changed_count: int
    missing_count: int
    inaccessible_count: int
    review_needed: tuple[str, ...]
    truncated: bool
    dry_run: bool


def sync_index(config: SyncConfig, client, now) -> SyncReport:
    _validate_page_id(config.root_page_id)
    _validate_config_paths(config)
    if config.validate_only:
        return validate_existing_index(config)

    synced_at = now()
    previous = load_state(config.state_path, config.root_page_id)
    existing_topics = load_existing_topic_documents(config.wiki_work_dir, allow_legacy=True)
    client.check()
    snapshot = crawl_tree(client, config.root_page_id, config.child_limit)
    _validate_confluence_page_ids(snapshot.root_page_id, snapshot.pages)
    _validate_snapshot_urls(snapshot.pages, getattr(client, "base_url", None))
    next_state, changes = compute_next_state(previous, snapshot, synced_at)

    bodies: dict[str, str] = {}
    if not config.dry_run:
        for page_id in changes.content_ids:
            try:
                bodies[page_id] = client.page(page_id).get("body", "")
            except PageUnavailableError as error:
                if error.status_code not in (403, 404):
                    raise
                next_state = mark_unavailable(
                    next_state,
                    page_id,
                    error.status_code,
                )

    next_state = mark_reviewed(next_state, config.mark_reviewed)
    documents = build_topic_documents(
        next_state,
        existing_topics,
        bodies,
        synced_at,
    )
    outputs = render_and_validate_outputs(config, documents, next_state)
    report = build_sync_report(next_state, changes, documents, config.dry_run)
    stale_topic_paths = _stale_topic_paths(
        config.wiki_work_dir,
        existing_topics,
        documents,
    )
    bodies.clear()

    if not config.dry_run:
        write_batch_atomic(outputs, deletions=stale_topic_paths)
    return report


def load_existing_topic_documents(
    wiki_work_dir: Path, *, allow_legacy: bool = False
) -> dict[str, ParsedTopic]:
    topic_dir = Path(wiki_work_dir) / "k1-activities"
    if not topic_dir.exists():
        return {}

    parsed: dict[str, ParsedTopic] = {}
    for path in sorted(topic_dir.glob("k1-activity-*.md"), key=lambda item: item.name):
        match = _MANAGED_TOPIC_FILENAME.fullmatch(path.name)
        if match is None:
            continue
        if path.is_symlink():
            raise ValueError(f"topic document is a symlink: {path}")
        assert_safe_path(path)
        page_id = match.group(1)
        text = path.read_text(encoding="utf-8")
        if allow_legacy:
            parsed_topic = parse_existing_topic_page(text)
        else:
            errors = validate_topic_page(text, page_id)
            if errors:
                raise ValueError(_validation_message(path, errors))
            parsed_topic = parse_topic_page(text)
        if parsed_topic.root.page_id != page_id:
            raise ValueError(f"topic root metadata mismatches filename: {path}")
        parsed[page_id] = parsed_topic
    return parsed


def build_topic_documents(
    state: IndexState,
    existing_topics: dict[str, ParsedTopic],
    bodies: dict[str, str],
    synced_at: str,
) -> tuple[TopicDocument, ...]:
    topics = tuple(
        sorted(
            (page for page in state.pages.values() if page.page_id == page.topic_id),
            key=_page_key,
        )
    )
    documents: list[TopicDocument] = []
    for topic in topics:
        existing = existing_topics.get(topic.page_id)
        previous_children = existing.children if existing is not None else {}
        children: list[ChildEntry] = []
        descendants = sorted(
            (
                page
                for page in state.pages.values()
                if page.topic_id == topic.page_id and page.page_id != topic.page_id
            ),
            key=_page_key,
        )
        for page in descendants:
            previous = previous_children.get(page.page_id)
            if (
                previous is not None
                and page.page_id not in bodies
                and previous.page.version == page.version
            ):
                children.append(
                    ChildEntry(page=page, role=previous.role, summary=previous.summary)
                )
            else:
                draft = draft_page_semantics(page, bodies.get(page.page_id, ""))
                children.append(
                    ChildEntry(page=page, role=draft.role, summary=draft.summary)
                )

        if existing is not None:
            curated = existing.curated
        else:
            topic_draft = draft_page_semantics(topic, bodies.get(topic.page_id, ""))
            curated = CuratedTopic(
                summary=draft_topic_summary(topic, children),
                aliases=_unique((*topic.aliases, *topic_draft.aliases)),
                tags=topic_draft.tags,
                links=("[[k1-activity-catalog]]", "[[k1-confluence-routing]]"),
                notes="",
            )
        documents.append(
            TopicDocument(
                topic=topic,
                curated=curated,
                children=tuple(children),
                synced_at=synced_at,
            )
        )
    return tuple(documents)


def render_and_validate_outputs(
    config: SyncConfig,
    documents: tuple[TopicDocument, ...],
    state: IndexState,
) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for document in documents:
        path = _topic_output_path(config.wiki_work_dir, document.topic.page_id)
        existing = None
        if path.exists():
            if path.is_symlink():
                raise ValueError(f"output target is a symlink: {path}")
            existing = path.read_text(encoding="utf-8")
        rendered = render_topic_page(document, existing_text=existing)
        errors = validate_topic_page(rendered, document.topic.page_id)
        if errors:
            raise ValueError(_validation_message(path, errors))
        _insert_output(outputs, path, rendered)

    catalog_path = Path(config.wiki_work_dir) / "k1-activity-catalog.md"
    existing_catalog = None
    if catalog_path.exists():
        if catalog_path.is_symlink():
            raise ValueError(f"output target is a symlink: {catalog_path}")
        existing_catalog = catalog_path.read_text(encoding="utf-8")
    catalog = render_catalog(
        documents,
        state.synced_at or "1970-01-01T00:00:00+00:00",
        existing_text=existing_catalog,
    )
    catalog_errors = validate_catalog_page(catalog)
    if catalog_errors:
        raise ValueError(_validation_message(catalog_path, catalog_errors))
    _insert_output(outputs, catalog_path, catalog)

    review_payload = {
        "root_page_id": state.root_page_id,
        "synced_at": state.synced_at,
        "review_needed": list(_review_needed(state)),
        "missing": list(_ids_with_availability(state, "missing-from-root")),
        "inaccessible": list(_inaccessible_ids(state)),
        "complete": state.complete,
        "truncated": not state.complete,
    }
    _insert_output(
        outputs,
        Path(config.review_report_path),
        json.dumps(review_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _insert_output(outputs, Path(config.state_path), dump_state(_persistable_state(state)))
    return outputs


def validate_existing_index(config: SyncConfig) -> SyncReport:
    state_path = Path(config.state_path)
    if not state_path.exists():
        raise ValueError(f"state file does not exist: {state_path}")
    state = load_state(state_path, config.root_page_id)
    if not state.complete:
        raise ValueError("state completeness has not been verified")
    _validate_state_structure(state)
    existing_topics = load_existing_topic_documents(config.wiki_work_dir)
    expected_ids = {
        page.page_id for page in state.pages.values() if page.page_id == page.topic_id
    }
    actual_ids = set(existing_topics)
    if expected_ids != actual_ids:
        missing = _sorted_ids(expected_ids - actual_ids)
        unexpected = _sorted_ids(actual_ids - expected_ids)
        raise ValueError(
            "topic documents differ from state "
            f"(missing={list(missing)}, unexpected={list(unexpected)})"
        )
    _reconcile_topic_documents(state, existing_topics)

    catalog_path = Path(config.wiki_work_dir) / "k1-activity-catalog.md"
    if not catalog_path.exists():
        raise ValueError(f"catalog does not exist: {catalog_path}")
    if catalog_path.is_symlink():
        raise ValueError(f"catalog is a symlink: {catalog_path}")
    catalog_errors = validate_catalog_page(catalog_path.read_text(encoding="utf-8"))
    if catalog_errors:
        raise ValueError(_validation_message(catalog_path, catalog_errors))
    catalog_entries = parse_catalog_page(catalog_path.read_text(encoding="utf-8"))
    _reconcile_catalog(state, existing_topics, catalog_entries)
    return SyncReport(
        root_page_id=state.root_page_id,
        topic_count=len(expected_ids),
        page_count=len(state.pages),
        new_count=0,
        changed_count=0,
        missing_count=len(_ids_with_availability(state, "missing-from-root")),
        inaccessible_count=len(_inaccessible_ids(state)),
        review_needed=_review_needed(state),
        truncated=not state.complete,
        dry_run=False,
    )


def build_sync_report(
    state: IndexState,
    changes: ChangeSet,
    documents: tuple[TopicDocument, ...],
    dry_run: bool,
) -> SyncReport:
    changed_ids = (
        set(changes.version_changed_ids)
        | set(changes.renamed_ids)
        | set(changes.moved_ids)
    ) - set(changes.new_ids)
    return SyncReport(
        root_page_id=state.root_page_id,
        topic_count=len(documents),
        page_count=len(state.pages),
        new_count=len(changes.new_ids),
        changed_count=len(changed_ids),
        missing_count=len(_ids_with_availability(state, "missing-from-root")),
        inaccessible_count=len(_inaccessible_ids(state)),
        review_needed=_review_needed(state),
        truncated=not state.complete,
        dry_run=dry_run,
    )


def _validation_message(path: Path, errors: tuple[str, ...]) -> str:
    return f"invalid activity document {path}: {'; '.join(errors)}"


def _stale_topic_paths(
    wiki_work_dir: Path,
    existing_topics: dict[str, ParsedTopic],
    documents: tuple[TopicDocument, ...],
) -> tuple[Path, ...]:
    current_ids = {document.topic.page_id for document in documents}
    stale_ids = _sorted_ids(set(existing_topics) - current_ids)
    return tuple(_topic_output_path(wiki_work_dir, page_id) for page_id in stale_ids)


def _topic_output_path(wiki_work_dir: Path, page_id: str) -> Path:
    _validate_page_id(page_id)
    topic_root = absolute_unresolved(Path(wiki_work_dir) / "k1-activities")
    assert_safe_path(topic_root)
    candidate = absolute_unresolved(topic_root / f"k1-activity-{page_id}.md")
    assert_within(candidate, topic_root)
    assert_safe_path(candidate)
    return candidate


def _validate_config_paths(config: SyncConfig) -> None:
    wiki_work_dir = Path(config.wiki_work_dir)
    paths = (
        wiki_work_dir,
        wiki_work_dir / "k1-activities",
        wiki_work_dir / "k1-activity-catalog.md",
        Path(config.state_path),
        Path(config.review_report_path),
    )
    for path in paths:
        assert_safe_path(path)


def _validate_confluence_page_ids(root_page_id: str, pages: dict[str, object]) -> None:
    _validate_page_id(root_page_id)
    for page_id in pages:
        _validate_page_id(page_id)


def _validate_snapshot_urls(pages: dict[str, PageState], base_url: str | None) -> None:
    if not base_url:
        raise ValueError("configured Confluence host is unavailable")
    for page_id, page in pages.items():
        try:
            validate_page_url(page.url, page_id, base_url)
        except ValueError as error:
            raise ValueError(f"Confluence host/URL validation failed for pageId {page_id}") from error


def _validate_page_id(page_id: str) -> None:
    if not page_id or not page_id.isascii() or not page_id.isdigit():
        raise ValueError(
            f"Confluence pageId must contain ASCII digits only: {page_id!r}"
        )


def _insert_output(outputs: dict[Path, str], path: Path, text: str) -> None:
    normalized = Path(path).resolve(strict=False)
    if any(existing.resolve(strict=False) == normalized for existing in outputs):
        raise ValueError(f"duplicate output target: {path}")
    outputs[Path(path)] = text


def _unique(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _page_key(page: PageState) -> tuple[str, tuple[int, int | str]]:
    return (normalize_label(page.title).casefold(), _id_key(page.page_id))


def _id_key(page_id: str) -> tuple[int, int | str]:
    try:
        return (0, int(page_id))
    except ValueError:
        return (1, page_id)


def _sorted_ids(page_ids) -> tuple[str, ...]:
    return tuple(sorted(page_ids, key=_id_key))


def _review_needed(state: IndexState) -> tuple[str, ...]:
    return _sorted_ids(
        page.page_id for page in state.pages.values() if page.review_needed
    )


def _ids_with_availability(state: IndexState, availability: str) -> tuple[str, ...]:
    return _sorted_ids(
        page.page_id
        for page in state.pages.values()
        if page.availability == availability
    )


def _inaccessible_ids(state: IndexState) -> tuple[str, ...]:
    return _sorted_ids(
        page.page_id
        for page in state.pages.values()
        if page.availability == "inaccessible"
        or page.availability.startswith("unavailable-")
    )


def _persistable_state(state: IndexState) -> IndexState:
    pages = {
        page_id: (
            replace(page, availability="inaccessible")
            if page.availability.startswith("unavailable-")
            else page
        )
        for page_id, page in state.pages.items()
    }
    return replace(state, pages=pages)


def _validate_state_structure(state: IndexState) -> None:
    for key, page in state.pages.items():
        if key != page.page_id:
            raise ValueError(f"state page key differs from pageId: {key}")
        if not page.path or page.path[-1] != page.title:
            raise ValueError(f"state page path/title mismatch: {page.page_id}")
        topic = state.pages.get(page.topic_id)
        if topic is None or topic.page_id != topic.topic_id:
            raise ValueError(f"state topic ownership is invalid: {page.page_id}")
        if page.page_id == page.topic_id:
            if page.parent_id != state.root_page_id or page.path != (page.title,):
                raise ValueError(f"state topic root metadata is invalid: {page.page_id}")
        else:
            parent = state.pages.get(page.parent_id)
            if parent is None or parent.topic_id != page.topic_id:
                raise ValueError(f"state descendant ownership is invalid: {page.page_id}")
            if page.path != (*parent.path, page.title):
                raise ValueError(f"state descendant path is invalid: {page.page_id}")


def _reconcile_topic_documents(
    state: IndexState, topics: dict[str, ParsedTopic]
) -> None:
    ownership: dict[str, str] = {}
    for topic_id, parsed in topics.items():
        expected_root = state.pages[topic_id]
        if (
            _page_signature(parsed.root) != _page_signature(expected_root)
            or parsed.root.space != expected_root.space
        ):
            raise ValueError(f"topic root metadata mismatch: {topic_id}")
        if parsed.synced_at != state.synced_at:
            raise ValueError(f"topic sync time metadata mismatch: {topic_id}")
        expected_children = {
            page.page_id: page
            for page in state.pages.values()
            if page.topic_id == topic_id and page.page_id != topic_id
        }
        if set(parsed.children) != set(expected_children):
            raise ValueError(f"descendant rows differ from state for topic: {topic_id}")
        if parsed.descendant_count != len(expected_children):
            raise ValueError(f"descendant count differs from state for topic: {topic_id}")
        for page_id, child in parsed.children.items():
            previous_owner = ownership.setdefault(page_id, topic_id)
            if previous_owner != topic_id:
                raise ValueError(f"descendant has duplicate cross-topic ownership: {page_id}")
            if _page_signature(child.page) != _page_signature(expected_children[page_id]):
                raise ValueError(f"descendant metadata mismatch: {page_id}")
    expected_descendants = {
        page.page_id for page in state.pages.values() if page.page_id != page.topic_id
    }
    if set(ownership) != expected_descendants:
        raise ValueError("descendant ownership differs from state")


def _reconcile_catalog(state: IndexState, topics: dict[str, ParsedTopic], entries) -> None:
    if set(entries) != set(topics):
        raise ValueError("catalog topic rows differ from state")
    for topic_id, parsed in topics.items():
        topic = state.pages[topic_id]
        entry = entries[topic_id]
        expected_tags = tuple(
            tag for tag in parsed.curated.tags if tag not in {"K1", "活动", "历史"}
        )
        expected = (
            topic.page_id,
            topic.title,
            tuple(dict.fromkeys((*parsed.curated.aliases, *topic.aliases))),
            f"[[k1-activity-{topic.page_id}]]",
            parsed.curated.summary,
            expected_tags,
            topic.status,
            topic.availability,
            len(parsed.children),
            topic.version,
            state.synced_at,
            topic.url,
        )
        actual = (
            entry.page_id,
            entry.title,
            entry.aliases,
            entry.local_wikilink,
            entry.summary,
            entry.mechanism_tags,
            entry.status,
            entry.availability,
            entry.descendant_count,
            entry.version,
            entry.synced_at,
            entry.url,
        )
        if actual != expected:
            raise ValueError(f"catalog metadata mismatch: {topic_id}")


def _page_signature(page: PageState) -> tuple:
    return (
        page.page_id,
        page.topic_id,
        page.parent_id,
        page.title,
        page.aliases,
        page.path,
        page.version,
        page.url,
        page.availability,
        page.review_needed,
        page.status,
        page.wiki_updated_at,
    )
