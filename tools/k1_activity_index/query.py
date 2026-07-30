"""Offline search and intent routing for managed K1 activity topic pages."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import parse_qs, urlparse

from .markdown import parse_topic_page, validate_topic_page


SCORES = {
    "topic-exact": 100,
    "alias-exact": 95,
    "child-exact": 90,
    "topic-child-combination": 88,
    "title-partial": 80,
    "all-tags": 70,
    "summary": 50,
}

_MANAGED_TOPIC = re.compile(r"k1-activity-([0-9]+)\.md\Z", re.ASCII)
_COMBINATION_DELIMITER = re.compile(r"[\s+,，、]+")


@dataclass(frozen=True)
class SearchChild:
    page_id: str
    title: str
    role: str
    summary: str
    wiki_url: str


@dataclass(frozen=True)
class SearchDocument:
    page_id: str
    topic_title: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    summary: str
    local_path: Path
    wiki_url: str
    children: tuple[SearchChild, ...]


@dataclass(frozen=True)
class SearchHit:
    score: int
    match_kind: str
    topic_page_id: str
    topic_title: str
    child_page_id: str | None
    child_title: str | None
    local_path: Path
    wiki_url: str


def load_search_documents(activity_dir: Path) -> tuple[SearchDocument, ...]:
    """Load only validated, managed pages from one configured activity directory."""
    configured_root = Path(activity_dir)
    if configured_root.is_symlink():
        raise ValueError(f"activity directory is a symlink: {configured_root}")
    root = configured_root.resolve(strict=False)
    if not root.exists():
        raise FileNotFoundError(f"activity directory does not exist: {configured_root}")
    if not root.is_dir():
        raise ValueError(f"activity directory is not a directory: {root}")
    if root.is_symlink():
        raise ValueError(f"activity directory is a symlink: {root}")

    documents: list[SearchDocument] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        match = _MANAGED_TOPIC.fullmatch(path.name)
        if match is None:
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"managed topic is not a regular file: {path}")
        resolved = path.resolve(strict=True)
        if resolved.parent != root:
            raise ValueError(f"managed topic resolves outside activity directory: {path}")

        page_id = match.group(1)
        text = resolved.read_text(encoding="utf-8")
        errors = validate_topic_page(text, page_id)
        if errors:
            raise ValueError(f"invalid activity document {resolved}: {'; '.join(errors)}")
        parsed = parse_topic_page(text)
        title, wiki_url = _topic_metadata(text, page_id)
        children = tuple(
            SearchChild(
                page_id=child.page.page_id,
                title=child.page.title,
                role=child.role,
                summary=child.summary,
                wiki_url=child.page.url,
            )
            for child in sorted(
                parsed.children.values(), key=lambda item: (_normalize(item.page.title), _page_id_key(item.page.page_id))
            )
        )
        documents.append(
            SearchDocument(
                page_id=page_id,
                topic_title=title,
                aliases=parsed.curated.aliases,
                tags=parsed.curated.tags,
                summary=parsed.curated.summary,
                local_path=resolved,
                wiki_url=wiki_url,
                children=children,
            )
        )
    return tuple(sorted(documents, key=lambda item: (_normalize(item.topic_title), _page_id_key(item.page_id))))


def search_index(activity_dir: Path, query: str, limit: int = 10) -> tuple[SearchHit, ...]:
    """Return deterministic, non-lossy top-ranked local routing candidates."""
    if limit < 0:
        raise ValueError("limit must not be negative")
    if limit == 0:
        return ()
    normalized_query = _normalize(query)
    terms = _query_terms(query)
    if not normalized_query:
        return ()

    candidates: dict[tuple[str, str | None], SearchHit] = {}
    for document in load_search_documents(activity_dir):
        _score_document(candidates, document, normalized_query, terms)

    ranked = tuple(sorted(candidates.values(), key=_hit_key))
    if len(ranked) <= limit:
        return ranked
    cutoff = ranked[limit - 1].score
    return tuple(hit for hit in ranked if hit.score >= cutoff)


def _score_document(
    candidates: dict[tuple[str, str | None], SearchHit],
    document: SearchDocument,
    query: str,
    terms: tuple[str, ...],
) -> None:
    topic_title = _normalize(document.topic_title)
    aliases = tuple(_normalize(alias) for alias in document.aliases)
    if query == topic_title:
        _add_hit(candidates, document, None, "topic-exact")
    if any(query == alias for alias in aliases):
        _add_hit(candidates, document, None, "alias-exact")

    for child in document.children:
        child_title = _normalize(child.title)
        if query == child_title:
            _add_hit(candidates, document, child, "child-exact")
        if len(terms) > 1 and _is_topic_child_combination(document, child, terms):
            _add_hit(candidates, document, child, "topic-child-combination")

    if _contains(topic_title, query) or any(_contains(alias, query) for alias in aliases):
        _add_hit(candidates, document, None, "title-partial")
    for child in document.children:
        if _contains(_normalize(child.title), query):
            _add_hit(candidates, document, child, "title-partial")

    tag_text = _normalize(" ".join(document.tags))
    if terms and all(_contains(tag_text, term) for term in terms):
        _add_hit(candidates, document, None, "all-tags")

    if _contains(_normalize(document.summary), query) or _terms_in(_normalize(document.summary), terms):
        _add_hit(candidates, document, None, "summary")
    for child in document.children:
        summary = _normalize(child.summary)
        if _contains(summary, query) or _terms_in(summary, terms):
            _add_hit(candidates, document, child, "summary")


def _is_topic_child_combination(
    document: SearchDocument, child: SearchChild, terms: tuple[str, ...]
) -> bool:
    topic_text = _normalize(" ".join((document.topic_title, *document.aliases)))
    child_text = _normalize(" ".join((child.title, child.role, child.summary)))
    topic_terms = [term for term in terms if _contains(topic_text, term)]
    child_terms = [term for term in terms if not _contains(topic_text, term) and _contains(child_text, term)]
    return bool(topic_terms and child_terms) and len(topic_terms) + len(child_terms) == len(terms)


def _add_hit(
    candidates: dict[tuple[str, str | None], SearchHit],
    document: SearchDocument,
    child: SearchChild | None,
    match_kind: str,
) -> None:
    hit = SearchHit(
        score=SCORES[match_kind],
        match_kind=match_kind,
        topic_page_id=document.page_id,
        topic_title=document.topic_title,
        child_page_id=None if child is None else child.page_id,
        child_title=None if child is None else child.title,
        local_path=document.local_path,
        wiki_url=document.wiki_url if child is None else child.wiki_url,
    )
    key = (hit.topic_page_id, hit.child_page_id)
    previous = candidates.get(key)
    if previous is None or hit.score > previous.score:
        candidates[key] = hit


def _topic_metadata(text: str, expected_page_id: str) -> tuple[str, str]:
    frontmatter = re.match(r"\A---\r?\n(?P<body>.*?)\r?\n---\r?\n", text, re.DOTALL)
    if frontmatter is None:
        raise ValueError("malformed frontmatter")
    values: dict[str, object] = {}
    for line in frontmatter.group("body").splitlines():
        key, separator, encoded = line.partition(":")
        if not separator:
            raise ValueError("malformed frontmatter")
        values[key.strip()] = json.loads(encoded.strip())
    title = values.get("title")
    wiki_url = values.get("source")
    if not isinstance(title, str) or not isinstance(wiki_url, str):
        raise ValueError("topic frontmatter must contain title and source strings")
    page_ids = parse_qs(urlparse(wiki_url).query).get("pageId", ())
    if tuple(page_ids) != (expected_page_id,):
        raise ValueError(f"topic source pageId does not match filename: {expected_page_id}")
    return title, wiki_url


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = "".join(normalized.split())
    if normalized.startswith("k1"):
        normalized = normalized[2:]
    return normalized


def _query_terms(query: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", query).casefold()
    return tuple(term for part in _COMBINATION_DELIMITER.split(normalized) if (term := _normalize(part)))


def _contains(text: str, query: str) -> bool:
    return bool(query) and query in text


def _terms_in(text: str, terms: tuple[str, ...]) -> bool:
    return bool(terms) and all(_contains(text, term) for term in terms)


def _hit_key(hit: SearchHit) -> tuple[int, str, str, tuple[int, int | str]]:
    return (
        -hit.score,
        _normalize(hit.topic_title),
        "" if hit.child_title is None else _normalize(hit.child_title),
        _page_id_key(hit.child_page_id or hit.topic_page_id),
    )


def _page_id_key(page_id: str) -> tuple[int, int | str]:
    return (0, int(page_id)) if page_id.isdecimal() else (1, page_id)
