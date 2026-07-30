"""Safe, deterministic Markdown pages for the K1 activity index."""

from dataclasses import dataclass, replace
from datetime import date
import json
import re
from urllib.parse import parse_qs, urlparse

from .models import PageState


CURATED_START = "<!-- K1-ACTIVITY-CURATED:START -->"
CURATED_END = "<!-- K1-ACTIVITY-CURATED:END -->"
GENERATED_START = "<!-- K1-ACTIVITY-GENERATED:START -->"
GENERATED_END = "<!-- K1-ACTIVITY-GENERATED:END -->"

_REQUIRED_FRONTMATTER = (
    "title",
    "type",
    "domain",
    "source",
    "date",
    "confidence",
    "tags",
    "links",
)
_FORBIDDEN_FRONTMATTER = {"body", "content", "html", "token", "password", "api_token", "credentials"}
_FORBIDDEN_MARKERS = ("copied-body", "confluence-body", "storage-format")
_HISTORICAL_WORDS = ("历史", "过期", "废弃", "删除", "旧", "historical", "expired", "obsolete", "deleted")
_CHILD_COLUMNS = (
    "pageId",
    "标题",
    "版本",
    "状态",
    "角色",
    "摘要",
    "topicId",
    "父页面 ID",
    "旧标题",
    "可访问性",
    "需要复核",
    "Wiki 更新时间",
    "回源",
)


@dataclass(frozen=True)
class CuratedTopic:
    summary: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    links: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class ChildEntry:
    page: PageState
    role: str
    summary: str


@dataclass(frozen=True)
class TopicDocument:
    topic: PageState
    curated: CuratedTopic
    children: tuple[ChildEntry, ...]
    synced_at: str


@dataclass(frozen=True)
class ParsedTopic:
    curated: CuratedTopic
    children: dict[str, ChildEntry]


def parse_topic_page(text: str) -> ParsedTopic:
    """Parse a generated topic page without accepting unsafe partial documents."""
    curated_region = _extract_single_region(text, CURATED_START, CURATED_END, "curated")
    generated_region = _extract_single_region(text, GENERATED_START, GENERATED_END, "generated")
    if text.index(CURATED_START) > text.index(GENERATED_START):
        raise ValueError("curated region must precede generated region")
    _reject_unsafe_document_content(text)
    frontmatter = _parse_frontmatter(text)
    missing = tuple(key for key in _REQUIRED_FRONTMATTER if key not in frontmatter)
    if missing:
        raise ValueError(f"frontmatter missing required keys: {', '.join(missing)}")
    _reject_forbidden_frontmatter(frontmatter)
    curated = _parse_curated(curated_region, frontmatter)
    return ParsedTopic(curated=curated, children=_parse_children(generated_region))


def render_topic_page(document: TopicDocument, existing_text: str | None = None) -> str:
    """Render one topic, retaining only a valid existing curated region verbatim."""
    if existing_text is None:
        curated_region = _render_curated(document.curated)
        previous_children: dict[str, ChildEntry] = {}
    else:
        parsed = parse_topic_page(existing_text)
        curated_region = _extract_single_region(existing_text, CURATED_START, CURATED_END, "curated")
        previous_children = parsed.children

    children = _preserved_children(document.children, previous_children)
    frontmatter = _render_frontmatter(
        title=document.topic.title,
        source=document.topic.url,
        synced_at=document.synced_at,
        confidence=_confidence(document.topic, document.curated),
        tags=document.curated.tags,
        links=document.curated.links,
    )
    return "\n\n".join((frontmatter, curated_region, _render_generated(document, children))) + "\n"


def render_catalog(
    documents: tuple[TopicDocument, ...], synced_at: str, existing_text: str | None = None
) -> str:
    """Render the catalog while preserving a valid human-maintained introduction."""
    if existing_text is None:
        curated_region = _render_catalog_curated()
    else:
        frontmatter = _parse_frontmatter(existing_text)
        missing = tuple(key for key in _REQUIRED_FRONTMATTER if key not in frontmatter)
        if missing:
            raise ValueError(f"frontmatter missing required keys: {', '.join(missing)}")
        _reject_forbidden_frontmatter(frontmatter)
        curated_region = _extract_single_region(existing_text, CURATED_START, CURATED_END, "curated")
        _extract_single_region(existing_text, GENERATED_START, GENERATED_END, "generated")
        _reject_unsafe_document_content(existing_text)

    frontmatter = _render_frontmatter(
        title="K1 活动索引",
        source="Confluence K1 activity root",
        synced_at=synced_at,
        confidence="medium",
        tags=("K1", "活动", "Confluence"),
        links=(),
    )
    groups = (
        ("当前可用", tuple(document for document in documents if _catalog_group(document) == "current")),
        ("历史/过期", tuple(document for document in documents if _catalog_group(document) == "historical")),
        ("不可访问", tuple(document for document in documents if _catalog_group(document) == "inaccessible")),
    )
    lines = [GENERATED_START, "## 索引元数据", f"- 同步时间：{_cell(synced_at)}", ""]
    for heading, group in groups:
        lines.extend((f"## {heading}", "| pageId | 主题 | 摘要 | 回源 |", "| --- | --- | --- | --- |"))
        for document in sorted(group, key=lambda item: _id_key(item.topic.page_id)):
            lines.append(
                "| {page_id} | {title} | {summary} | {url} |".format(
                    page_id=_cell(document.topic.page_id),
                    title=_cell(document.topic.title),
                    summary=_cell(document.curated.summary),
                    url=_cell(document.topic.url),
                )
            )
        lines.append("")
    lines.append(GENERATED_END)
    return "\n\n".join((frontmatter, curated_region, "\n".join(lines))) + "\n"


def validate_topic_page(text: str, expected_page_id: str) -> tuple[str, ...]:
    """Return every identifiable structural error without modifying the page."""
    errors: list[str] = []
    try:
        frontmatter = _parse_frontmatter(text)
    except ValueError as error:
        return (str(error),)

    for key in _REQUIRED_FRONTMATTER:
        if key not in frontmatter:
            errors.append(f"missing frontmatter key: {key}")
    for key in frontmatter:
        if key.casefold() in _FORBIDDEN_FRONTMATTER:
            errors.append(f"forbidden frontmatter key: {key}")
    source = frontmatter.get("source")
    if isinstance(source, str) and _source_page_id(source) != expected_page_id:
        errors.append(f"source pageId does not match expected pageId: {expected_page_id}")

    for marker, label in ((CURATED_START, "curated start"), (CURATED_END, "curated end"), (GENERATED_START, "generated start"), (GENERATED_END, "generated end")):
        if text.count(marker) != 1:
            errors.append(f"missing or duplicated {label} marker")
    if any(marker in text.casefold() for marker in (*_FORBIDDEN_MARKERS, "k1-activity-body")):
        errors.append("forbidden copied-body marker")
    try:
        generated = _extract_single_region(text, GENERATED_START, GENERATED_END, "generated")
        _parse_children(generated)
    except ValueError as error:
        errors.append(str(error))
        return tuple(errors)

    seen: set[str] = set()
    for row in _child_rows(generated):
        page_id = row[0]
        if page_id in seen:
            errors.append(f"duplicate descendant pageId: {page_id}")
        seen.add(page_id)
        if len(row) > 6 and row[6] != expected_page_id:
            errors.append(f"descendant topic ID differs from root: {page_id}")
    return tuple(errors)


def _render_frontmatter(
    *, title: str, source: str, synced_at: str, confidence: str, tags: tuple[str, ...], links: tuple[str, ...]
) -> str:
    payload = {
        "title": title,
        "type": "source-summary",
        "domain": "work",
        "source": source,
        "date": _date_part(synced_at),
        "confidence": confidence,
        "tags": list(tags),
        "links": list(links),
    }
    return "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in payload.items()) + "\n---"


def _render_curated(curated: CuratedTopic) -> str:
    return "\n".join(
        (
            CURATED_START,
            "## 主题摘要",
            curated.summary,
            "",
            "## 别名",
            *_bullets(curated.aliases),
            "",
            "## 语义标签",
            *_bullets(curated.tags),
            "",
            "## 关联页面",
            *_bullets(curated.links),
            "",
            "## 人工备注",
            curated.notes,
            CURATED_END,
        )
    )


def _render_catalog_curated() -> str:
    return "\n".join(
        (
            CURATED_START,
            "## 使用说明",
            "本目录由 Confluence 页面元数据生成。",
            "",
            "## 人工备注",
            "",
            CURATED_END,
        )
    )


def _render_generated(document: TopicDocument, children: tuple[ChildEntry, ...]) -> str:
    topic = document.topic
    lines = [
        GENERATED_START,
        "## 根页面元数据",
        "| 字段 | 值 |",
        "| --- | --- |",
        f"| 根页面 ID | {_cell(topic.page_id)} |",
        f"| 主题 ID | {_cell(topic.topic_id)} |",
        f"| Space | {_cell(topic.space)} |",
        f"| 状态 | {_cell(topic.status)} |",
        f"| 可访问性 | {_cell(topic.availability)} |",
        f"| Wiki 更新时间 | {_cell(topic.wiki_updated_at or '未知')} |",
        f"| 同步时间 | {_cell(document.synced_at)} |",
        f"| 需要复核 | {_yes_no(topic.review_needed)} |",
        f"| 旧标题 | {_cell('；'.join(topic.aliases) or '无')} |",
        "",
        "## 子页面",
        "| " + " | ".join(_CHILD_COLUMNS) + " |",
        "| " + " | ".join("---" for _ in _CHILD_COLUMNS) + " |",
    ]
    for child in sorted(children, key=lambda item: _id_key(item.page.page_id)):
        page = child.page
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    page.page_id,
                    page.title,
                    str(page.version),
                    page.status,
                    child.role,
                    child.summary,
                    page.topic_id,
                    page.parent_id,
                    "；".join(page.aliases) or "无",
                    page.availability,
                    _yes_no(page.review_needed),
                    page.wiki_updated_at or "未知",
                    page.url,
                )
            )
            + " |"
        )
    lines.extend(("", "## 回源", f"[{_cell(topic.title)}]({_cell(topic.url)})", GENERATED_END))
    return "\n".join(lines)


def _parse_frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---\n"):
        raise ValueError("malformed frontmatter: opening delimiter is missing")
    closing = text.find("\n---", 4)
    if closing < 0:
        raise ValueError("malformed frontmatter: closing delimiter is missing")
    body = text[4:closing]
    if not text[closing + 4 :].startswith("\n"):
        raise ValueError("malformed frontmatter: closing delimiter is invalid")
    values: dict[str, object] = {}
    for line in body.splitlines():
        if not line or ":" not in line:
            raise ValueError("malformed frontmatter entry")
        key, encoded = line.split(":", 1)
        key = key.strip()
        if not key or key in values:
            raise ValueError("malformed frontmatter key")
        try:
            values[key] = json.loads(encoded.strip())
        except json.JSONDecodeError as error:
            raise ValueError("malformed frontmatter value") from error
    return values


def _extract_single_region(text: str, start: str, end: str, label: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"missing or duplicated {label} markers")
    start_at = text.index(start)
    end_at = text.index(end)
    if end_at < start_at:
        raise ValueError(f"malformed {label} markers")
    return text[start_at : end_at + len(end)]


def _reject_unsafe_document_content(text: str) -> None:
    lowered = text.casefold()
    if any(marker in lowered for marker in (*_FORBIDDEN_MARKERS, "k1-activity-body")):
        raise ValueError("forbidden copied-body marker")
    frontmatter_end = text.find("\n---", 4)
    curated_start, curated_end = text.index(CURATED_START), text.index(CURATED_END) + len(CURATED_END)
    generated_start, generated_end = text.index(GENERATED_START), text.index(GENERATED_END) + len(GENERATED_END)
    unmanaged = (
        text[frontmatter_end + 4 : curated_start],
        text[curated_end:generated_start],
        text[generated_end:],
    )
    if any(part.strip() for part in unmanaged):
        raise ValueError("unmanaged content outside protected regions")


def _parse_curated(region: str, frontmatter: dict[str, object]) -> CuratedTopic:
    content = region[len(CURATED_START) : -len(CURATED_END)].strip("\r\n")
    sections = _named_sections(content, ("主题摘要", "别名", "语义标签", "关联页面", "人工备注"))
    aliases = _parse_bullets(sections["别名"], "别名")
    tags = _parse_bullets(sections["语义标签"], "语义标签")
    links = _parse_bullets(sections["关联页面"], "关联页面")
    if not isinstance(frontmatter["tags"], list) or not isinstance(frontmatter["links"], list):
        raise ValueError("malformed frontmatter list")
    return CuratedTopic(
        summary=sections["主题摘要"], aliases=aliases, tags=tags, links=links, notes=sections["人工备注"]
    )


def _named_sections(content: str, names: tuple[str, ...]) -> dict[str, str]:
    heading = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(heading.finditer(content))
    found = [match.group(1) for match in matches]
    if tuple(found) != names:
        raise ValueError("malformed curated sections")
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        if content[start : start + 1] == "\n":
            start += 1
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[match.group(1)] = content[start:end].rstrip("\n")
    return sections


def _parse_bullets(value: str, label: str) -> tuple[str, ...]:
    if not value:
        return ()
    lines = value.splitlines()
    if any(not line.startswith("- ") for line in lines):
        raise ValueError(f"malformed curated {label}")
    return tuple(line[2:] for line in lines)


def _parse_children(region: str) -> dict[str, ChildEntry]:
    children: dict[str, ChildEntry] = {}
    for row in _child_rows(region):
        if len(row) != len(_CHILD_COLUMNS):
            raise ValueError("malformed descendant row")
        page_id, title, version, status, role, summary, topic_id, parent_id, aliases, availability, review, updated_at, url = row
        if page_id in children:
            raise ValueError(f"duplicate descendant pageId: {page_id}")
        try:
            page_version = int(version)
        except ValueError as error:
            raise ValueError("malformed descendant version") from error
        children[page_id] = ChildEntry(
            page=PageState(
                page_id=page_id,
                title=title,
                status=status,
                space="",
                version=page_version,
                url=url,
                parent_id=parent_id,
                path=(title,),
                topic_id=topic_id,
                wiki_updated_at=None if updated_at == "未知" else updated_at,
                aliases=() if aliases == "无" else tuple(aliases.split("；")),
                availability=availability,
                review_needed=review == "是",
            ),
            role=role,
            summary=summary,
        )
    return children


def _child_rows(region: str) -> tuple[tuple[str, ...], ...]:
    section_start = region.find("## 子页面\n")
    if section_start < 0:
        raise ValueError("missing descendant table")
    section = region[section_start + len("## 子页面\n") :]
    section = section.split("\n## ", 1)[0]
    lines = section.splitlines()
    if len(lines) < 2 or _split_row(lines[0]) != _CHILD_COLUMNS:
        raise ValueError("malformed descendant header")
    if not lines[1].startswith("|"):
        raise ValueError("malformed descendant separator")
    rows: list[tuple[str, ...]] = []
    for line in lines[2:]:
        if not line.strip():
            continue
        if not line.startswith("|"):
            raise ValueError("malformed descendant row")
        rows.append(_split_row(line))
    return tuple(rows)


def _split_row(line: str) -> tuple[str, ...]:
    if not line.startswith("|") or not line.rstrip().endswith("|"):
        raise ValueError("malformed Markdown table row")
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for character in line.strip()[1:-1]:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return tuple(cells)


def _preserved_children(children: tuple[ChildEntry, ...], previous: dict[str, ChildEntry]) -> tuple[ChildEntry, ...]:
    merged: list[ChildEntry] = []
    for child in children:
        old = previous.get(child.page.page_id)
        if old is not None and old.page.version == child.page.version:
            merged.append(replace(child, summary=old.summary))
        else:
            merged.append(child)
    return tuple(merged)


def _catalog_group(document: TopicDocument) -> str:
    if document.topic.availability != "available":
        return "inaccessible"
    if _is_historical(document.topic, document.curated):
        return "historical"
    return "current"


def _confidence(topic: PageState, curated: CuratedTopic) -> str:
    return "low" if _is_historical(topic, curated) else "medium"


def _is_historical(topic: PageState, curated: CuratedTopic) -> bool:
    searchable = " ".join((topic.title, *curated.tags)).casefold()
    return any(word.casefold() in searchable for word in _HISTORICAL_WORDS)


def _date_part(timestamp: str) -> str:
    candidate = timestamp[:10]
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError as error:
        raise ValueError("synced_at must begin with an ISO date") from error


def _source_page_id(source: str) -> str | None:
    return parse_qs(urlparse(source).query).get("pageId", [None])[0]


def _reject_forbidden_frontmatter(frontmatter: dict[str, object]) -> None:
    for key in frontmatter:
        if key.casefold() in _FORBIDDEN_FRONTMATTER:
            raise ValueError(f"forbidden frontmatter key: {key}")


def _bullets(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"- {value}" for value in values)


def _cell(value: object) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _yes_no(value: bool) -> str:
    return "是" if value else "否"


def _id_key(page_id: str) -> tuple[int, int | str]:
    try:
        return (0, int(page_id))
    except ValueError:
        return (1, page_id)
