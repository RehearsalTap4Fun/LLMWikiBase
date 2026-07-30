"""Synchronization orchestration for the K1 Confluence activity index."""

from dataclasses import dataclass, replace
import json
from pathlib import Path

from .crawl import crawl_tree
from .markdown import (
    ChildEntry,
    CuratedTopic,
    ParsedTopic,
    TopicDocument,
    parse_topic_page,
    render_catalog,
    render_topic_page,
    validate_catalog_page,
    validate_topic_page,
)
from .models import ChangeSet, IndexState, PageState, PageUnavailableError
from .semantics import draft_page_semantics, draft_topic_summary, normalize_label
from .state import (
    compute_next_state,
    dump_state,
    load_state,
    mark_reviewed,
    mark_unavailable,
)
from .transaction import write_batch_atomic


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
    if config.validate_only:
        return validate_existing_index(config)

    synced_at = now()
    previous = load_state(config.state_path, config.root_page_id)
    existing_topics = load_existing_topic_documents(config.wiki_work_dir)
    client.check()
    snapshot = crawl_tree(client, config.root_page_id, config.child_limit)
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
    bodies.clear()

    if not config.dry_run:
        write_batch_atomic(outputs)
    return report


def load_existing_topic_documents(wiki_work_dir: Path) -> dict[str, ParsedTopic]:
    topic_dir = Path(wiki_work_dir) / "k1-activities"
    if not topic_dir.exists():
        return {}

    parsed: dict[str, ParsedTopic] = {}
    for path in sorted(topic_dir.glob("k1-activity-*.md"), key=lambda item: item.name):
        if path.is_symlink():
            raise ValueError(f"topic document is a symlink: {path}")
        page_id = path.stem.removeprefix("k1-activity-")
        if not page_id:
            raise ValueError(f"topic filename has no pageId: {path}")
        text = path.read_text(encoding="utf-8")
        errors = validate_topic_page(text, page_id)
        if errors:
            raise ValueError(_validation_message(path, errors))
        parsed[page_id] = parse_topic_page(text)
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

    catalog_path = Path(config.wiki_work_dir) / "k1-activity-catalog.md"
    if not catalog_path.exists():
        raise ValueError(f"catalog does not exist: {catalog_path}")
    if catalog_path.is_symlink():
        raise ValueError(f"catalog is a symlink: {catalog_path}")
    catalog_errors = validate_catalog_page(catalog_path.read_text(encoding="utf-8"))
    if catalog_errors:
        raise ValueError(_validation_message(catalog_path, catalog_errors))
    return SyncReport(
        root_page_id=state.root_page_id,
        topic_count=len(expected_ids),
        page_count=len(state.pages),
        new_count=0,
        changed_count=0,
        missing_count=len(_ids_with_availability(state, "missing-from-root")),
        inaccessible_count=len(_inaccessible_ids(state)),
        review_needed=_review_needed(state),
        truncated=False,
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
        truncated=False,
        dry_run=dry_run,
    )


def _validation_message(path: Path, errors: tuple[str, ...]) -> str:
    return f"invalid activity document {path}: {'; '.join(errors)}"


def _topic_output_path(wiki_work_dir: Path, page_id: str) -> Path:
    topic_root = (Path(wiki_work_dir) / "k1-activities").resolve(strict=False)
    candidate = (topic_root / f"k1-activity-{page_id}.md").resolve(strict=False)
    if candidate.parent != topic_root:
        raise ValueError(f"pageId resolves outside topic output root: {page_id}")
    return candidate


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
