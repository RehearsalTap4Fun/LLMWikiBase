"""Safe, deterministic Markdown pages for the K1 activity index."""

from dataclasses import dataclass, replace
from datetime import date
import json
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .models import PageState
from .semantics import normalize_label


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
    "层级路径",
    "版本",
    "状态",
    "角色",
    "摘要",
    "topicId",
    "父页面 ID",
    "别名",
    "可访问性",
    "需要复核",
    "Wiki 更新时间",
    "回源",
)
_CATALOG_COLUMNS = (
    "pageId",
    "主题",
    "别名",
    "本地页面",
    "摘要",
    "机制标签",
    "状态",
    "可访问性",
    "后代数",
    "根版本",
    "同步时间",
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
    root: PageState
    synced_at: str
    descendant_count: int


@dataclass(frozen=True)
class CatalogEntry:
    page_id: str
    title: str
    aliases: tuple[str, ...]
    local_wikilink: str
    summary: str
    mechanism_tags: tuple[str, ...]
    status: str
    availability: str
    descendant_count: int
    version: int
    synced_at: str
    url: str


def parse_topic_page(text: str, *, allow_legacy: bool = False) -> ParsedTopic:
    """Parse a generated topic page without accepting unsafe partial documents."""
    layout = _protected_layout(text)
    curated_region = _region_from_layout(text, layout, "curated")
    generated_region = _region_from_layout(text, layout, "generated")
    _reject_unsafe_document_content(text, layout)
    frontmatter = _parse_frontmatter(text)
    missing = tuple(key for key in _REQUIRED_FRONTMATTER if key not in frontmatter)
    if missing:
        raise ValueError(f"frontmatter missing required keys: {', '.join(missing)}")
    _reject_forbidden_frontmatter(frontmatter)
    frontmatter_errors = _frontmatter_errors(frontmatter)
    if frontmatter_errors:
        raise ValueError(frontmatter_errors[0])
    curated = _parse_curated(curated_region, frontmatter)
    children = _parse_children(generated_region, allow_legacy=allow_legacy)
    root, synced_at, descendant_count = _parse_root(
        generated_region,
        frontmatter,
        children,
        allow_legacy=allow_legacy,
    )
    _validate_topic_urls(root, children, source_url=frontmatter.get("source"))
    return ParsedTopic(
        curated=curated,
        children=children,
        root=root,
        synced_at=synced_at,
        descendant_count=descendant_count,
    )


def parse_existing_topic_page(text: str) -> ParsedTopic:
    """Parse current output strictly, allowing only the one known pre-model schema for migration."""
    try:
        return parse_topic_page(text)
    except ValueError:
        if "| 旧标题 |" not in text or "| 层级路径 |" in text:
            raise
        return parse_topic_page(text, allow_legacy=True)


def parse_catalog_page(text: str) -> dict[str, CatalogEntry]:
    frontmatter = _parse_frontmatter(text)
    errors = _frontmatter_errors(frontmatter)
    if errors:
        raise ValueError(errors[0])
    source = frontmatter.get("source")
    if not isinstance(source, str):
        raise ValueError("catalog source URL is invalid")
    root_host = _validate_confluence_url(source, _source_page_id(source), label="catalog source URL")
    layout = _protected_layout(text)
    _reject_unsafe_document_content(text, layout)
    generated = _region_from_layout(text, layout, "generated")
    content = generated[len(GENERATED_START) : -len(GENERATED_END)].strip("\r\n")
    sections = _named_sections(content, ("索引元数据", "当前可用", "历史/过期", "不可访问"))
    entries: dict[str, CatalogEntry] = {}
    for name in ("当前可用", "历史/过期", "不可访问"):
        for row in _table_rows(sections[name], _CATALOG_COLUMNS):
            entry = _catalog_entry(row)
            if entry.page_id in entries:
                raise ValueError(f"duplicate catalog pageId: {entry.page_id}")
            _validate_confluence_url(
                entry.url,
                entry.page_id,
                expected_host=root_host,
                label="catalog row URL",
            )
            entries[entry.page_id] = entry
    return entries


def render_topic_page(document: TopicDocument, existing_text: str | None = None) -> str:
    """Render one topic, retaining only a valid existing curated region verbatim."""
    if existing_text is None:
        curated_region = _render_curated(document.curated)
        previous_children: dict[str, ChildEntry] = {}
    else:
        parsed = parse_existing_topic_page(existing_text)
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
        layout = _protected_layout(existing_text)
        curated_region = _region_from_layout(existing_text, layout, "curated")
        _reject_unsafe_document_content(existing_text, layout)

    frontmatter = _render_frontmatter(
        title="K1 活动索引",
        source=_catalog_root_url(documents),
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
        lines.extend((f"## {heading}", "| " + " | ".join(_CATALOG_COLUMNS) + " |", "| " + " | ".join("---" for _ in _CATALOG_COLUMNS) + " |"))
        for document in sorted(group, key=lambda item: _page_key(item.topic)):
            lines.append(
                "| "
                + " | ".join(
                    _cell(value)
                    for value in (
                        document.topic.page_id,
                        document.topic.title,
                        _json_list(tuple(dict.fromkeys((*document.curated.aliases, *document.topic.aliases)))),
                        f"[[k1-activity-{document.topic.page_id}]]",
                        document.curated.summary,
                        _json_list(_mechanism_tags(document.curated.tags)),
                        document.topic.status,
                        document.topic.availability,
                        str(len(document.children)),
                        str(document.topic.version),
                        synced_at,
                        document.topic.url,
                    )
                )
                + " |"
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
    errors.extend(_frontmatter_errors(frontmatter))
    source = frontmatter.get("source")
    if isinstance(source, str):
        try:
            _validate_confluence_url(source, expected_page_id, label="source URL")
        except ValueError as error:
            errors.append(str(error))

    try:
        layout = _protected_layout(text)
    except ValueError as error:
        errors.append(str(error))
        return tuple(errors)
    try:
        _reject_unsafe_document_content(text, layout)
    except ValueError as error:
        errors.append(str(error))
    try:
        curated = _region_from_layout(text, layout, "curated")
        _parse_curated(curated, frontmatter)
    except ValueError as error:
        errors.append(str(error))
    try:
        generated = _region_from_layout(text, layout, "generated")
        children = _parse_children(generated)
        root, _, descendant_count = _parse_root(generated, frontmatter, children)
        if root.page_id != expected_page_id:
            errors.append(f"root pageId does not match expected pageId: {expected_page_id}")
        if descendant_count != len(children):
            errors.append("descendant count does not match descendant rows")
    except ValueError as error:
        errors.append(str(error))
        return tuple(errors)
    try:
        _validate_topic_urls(root, children, source_url=source)
    except ValueError as error:
        errors.append(str(error))

    seen: set[str] = set()
    for row in _child_rows(generated):
        page_id = row[0]
        if page_id in seen:
            errors.append(f"duplicate descendant pageId: {page_id}")
        seen.add(page_id)
        if len(row) > 7 and row[7] != expected_page_id:
            errors.append(f"descendant topic ID differs from root: {page_id}")
    return tuple(errors)


def validate_catalog_page(text: str) -> tuple[str, ...]:
    """Return structural catalog errors without rewriting the document."""
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
    errors.extend(_frontmatter_errors(frontmatter))
    try:
        layout = _protected_layout(text)
    except ValueError as error:
        errors.append(str(error))
        return tuple(errors)
    try:
        _reject_unsafe_document_content(text, layout)
    except ValueError as error:
        errors.append(str(error))
    try:
        curated = _region_from_layout(text, layout, "curated")
        content = curated[len(CURATED_START) : -len(CURATED_END)].strip("\r\n")
        _named_sections(content, ("使用说明", "人工备注"))
    except ValueError as error:
        errors.append(f"malformed catalog curated sections: {error}")
    try:
        generated = _region_from_layout(text, layout, "generated")
        content = generated[len(GENERATED_START) : -len(GENERATED_END)].strip(
            "\r\n"
        )
        _named_sections(
            content,
            ("索引元数据", "当前可用", "历史/过期", "不可访问"),
        )
    except ValueError as error:
        errors.append(f"malformed catalog generated sections: {error}")
    if not errors:
        try:
            parse_catalog_page(text)
        except ValueError as error:
            errors.append(f"malformed catalog rows: {error}")
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
        f"| 标题 | {_cell(topic.title)} |",
        f"| 主题 ID | {_cell(topic.topic_id)} |",
        f"| 父页面 ID | {_cell(topic.parent_id)} |",
        f"| 层级路径 | {_cell(_json_list(topic.path))} |",
        f"| 版本 | {_cell(topic.version)} |",
        f"| Space | {_cell(topic.space)} |",
        f"| 状态 | {_cell(topic.status)} |",
        f"| 可访问性 | {_cell(topic.availability)} |",
        f"| Wiki 更新时间 | {_cell(topic.wiki_updated_at or '未知')} |",
        f"| 同步时间 | {_cell(document.synced_at)} |",
        f"| 需要复核 | {_yes_no(topic.review_needed)} |",
        f"| 别名 | {_cell(_json_list(topic.aliases))} |",
        f"| 回源 URL | {_cell(topic.url)} |",
        f"| 后代页面数 | {len(children)} |",
        "",
        "## 子页面",
        "| " + " | ".join(_CHILD_COLUMNS) + " |",
        "| " + " | ".join("---" for _ in _CHILD_COLUMNS) + " |",
    ]
    for child in sorted(children, key=lambda item: _page_key(item.page)):
        page = child.page
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    page.page_id,
                    page.title,
                    _json_list(page.path),
                    str(page.version),
                    page.status,
                    child.role,
                    child.summary,
                    page.topic_id,
                    page.parent_id,
                    _json_list(page.aliases),
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
    body_start, body_end, _ = _frontmatter_bounds(text)
    body = text[body_start:body_end]
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


def _frontmatter_bounds(text: str) -> tuple[int, int, int]:
    opening = re.match(r"---\r?\n", text)
    if opening is None:
        raise ValueError("malformed frontmatter: opening delimiter is missing")
    closing = re.search(r"\r?\n---(?=\r?\n)", text[opening.end() :])
    if closing is None:
        raise ValueError("malformed frontmatter: closing delimiter is missing")
    closing_start = opening.end() + closing.start()
    closing_end = opening.end() + closing.end()
    return opening.end(), closing_start, closing_end


def _extract_single_region(text: str, start: str, end: str, label: str) -> str:
    layout = _protected_layout(text)
    expected = (CURATED_START, CURATED_END, "curated") if label == "curated" else (GENERATED_START, GENERATED_END, "generated")
    if (start, end, label) != expected:
        raise ValueError("unknown protected region")
    return _region_from_layout(text, layout, label)


def _protected_layout(text: str) -> tuple[int, int, int, int]:
    markers = (
        (CURATED_START, "curated start"),
        (CURATED_END, "curated end"),
        (GENERATED_START, "generated start"),
        (GENERATED_END, "generated end"),
    )
    positions: list[int] = []
    for marker, label in markers:
        if text.count(marker) != 1:
            raise ValueError(f"missing or duplicated {label} marker")
        positions.append(text.index(marker))
    curated_start, curated_end, generated_start, generated_end = positions
    if not curated_start < curated_end < generated_start < generated_end:
        raise ValueError("malformed protected marker order")
    return curated_start, curated_end, generated_start, generated_end


def _region_from_layout(text: str, layout: tuple[int, int, int, int], label: str) -> str:
    curated_start, curated_end, generated_start, generated_end = layout
    if label == "curated":
        return text[curated_start : curated_end + len(CURATED_END)]
    if label == "generated":
        return text[generated_start : generated_end + len(GENERATED_END)]
    raise ValueError("unknown protected region")


def _reject_unsafe_document_content(text: str, layout: tuple[int, int, int, int]) -> None:
    lowered = text.casefold()
    if any(marker in lowered for marker in (*_FORBIDDEN_MARKERS, "k1-activity-body")):
        raise ValueError("forbidden copied-body marker")
    _, _, frontmatter_end = _frontmatter_bounds(text)
    curated_start, curated_end, generated_start, generated_end = layout
    unmanaged = (
        text[frontmatter_end:curated_start],
        text[curated_end + len(CURATED_END) : generated_start],
        text[generated_end + len(GENERATED_END) :],
    )
    if any(part.strip() for part in unmanaged):
        raise ValueError("unmanaged content outside protected regions")


def _parse_curated(region: str, frontmatter: dict[str, object]) -> CuratedTopic:
    content = region[len(CURATED_START) : -len(CURATED_END)].strip("\r\n")
    sections = _named_sections(content, ("主题摘要", "别名", "语义标签", "关联页面", "人工备注"))
    aliases = _parse_bullets(sections["别名"], "别名")
    tags = _parse_bullets(sections["语义标签"], "语义标签")
    links = _parse_bullets(sections["关联页面"], "关联页面")
    if not isinstance(frontmatter.get("tags"), list) or not isinstance(frontmatter.get("links"), list):
        raise ValueError("malformed frontmatter list")
    return CuratedTopic(
        summary=sections["主题摘要"], aliases=aliases, tags=tags, links=links, notes=sections["人工备注"]
    )


def _named_sections(content: str, names: tuple[str, ...]) -> dict[str, str]:
    heading = re.compile(r"^## (.+?)\r?$", re.MULTILINE)
    matches = list(heading.finditer(content))
    found = [match.group(1) for match in matches]
    if tuple(found) != names:
        raise ValueError("malformed curated sections")
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        if content[start : start + 2] == "\r\n":
            start += 2
        elif content[start : start + 1] == "\n":
            start += 1
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[match.group(1)] = content[start:end].rstrip("\r\n")
    return sections


def _parse_bullets(value: str, label: str) -> tuple[str, ...]:
    if not value:
        return ()
    lines = value.splitlines()
    if any(not line.startswith("- ") for line in lines):
        raise ValueError(f"malformed curated {label}")
    return tuple(line[2:] for line in lines)


def _parse_children(region: str, *, allow_legacy: bool = False) -> dict[str, ChildEntry]:
    children: dict[str, ChildEntry] = {}
    for row in _child_rows(region, allow_legacy=allow_legacy):
        if len(row) == len(_CHILD_COLUMNS):
            (
                page_id,
                title,
                encoded_path,
                version,
                status,
                role,
                summary,
                topic_id,
                parent_id,
                encoded_aliases,
                availability,
                review,
                updated_at,
                url,
            ) = row
            path = _decode_string_list(encoded_path, "descendant path")
            aliases = _decode_string_list(encoded_aliases, "descendant aliases")
        elif allow_legacy and len(row) == 13:
            page_id, title, version, status, role, summary, topic_id, parent_id, legacy_aliases, availability, review, updated_at, url = row
            path = (title,)
            aliases = () if legacy_aliases == "无" else tuple(legacy_aliases.split("；"))
        else:
            raise ValueError("malformed descendant row")
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
                path=path,
                topic_id=topic_id,
                wiki_updated_at=None if updated_at == "未知" else updated_at,
                aliases=aliases,
                availability=availability,
                review_needed=review == "是",
            ),
            role=role,
            summary=summary,
        )
    return children


def _child_rows(region: str, *, allow_legacy: bool = False) -> tuple[tuple[str, ...], ...]:
    section_heading = re.search(r"^## 子页面\r?\n", region, re.MULTILINE)
    if section_heading is None:
        raise ValueError("missing descendant table")
    section = region[section_heading.end() :]
    section = re.split(r"\r?\n## ", section, maxsplit=1)[0]
    lines = section.splitlines()
    header = _split_row(lines[0]) if lines else ()
    legacy_columns = tuple(column for column in _CHILD_COLUMNS if column != "层级路径")
    legacy_columns = tuple("旧标题" if column == "别名" else column for column in legacy_columns)
    if len(lines) < 2 or (
        header != _CHILD_COLUMNS and not (allow_legacy and header == legacy_columns)
    ):
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


def _parse_root(
    region: str,
    frontmatter: dict[str, object],
    children: dict[str, ChildEntry],
    *,
    allow_legacy: bool = False,
) -> tuple[PageState, str, int]:
    table = _root_table(region)
    required = (
        "根页面 ID",
        "标题",
        "主题 ID",
        "父页面 ID",
        "层级路径",
        "版本",
        "Space",
        "状态",
        "可访问性",
        "Wiki 更新时间",
        "同步时间",
        "需要复核",
        "别名",
        "回源 URL",
        "后代页面数",
    )
    if not allow_legacy and tuple(table) != required:
        raise ValueError("malformed root metadata")
    if allow_legacy and not all(key in table for key in ("根页面 ID", "主题 ID", "Space", "状态", "可访问性", "同步时间", "需要复核")):
        raise ValueError("malformed root metadata")
    title = table.get("标题", frontmatter.get("title"))
    url = table.get("回源 URL", frontmatter.get("source"))
    if not isinstance(title, str) or not isinstance(url, str):
        raise ValueError("malformed root metadata")
    page_id = table["根页面 ID"]
    try:
        version = int(table.get("版本", "0"))
        descendant_count = int(table.get("后代页面数", str(len(children))))
    except ValueError as error:
        raise ValueError("malformed root metadata integer") from error
    if version < 1 and not allow_legacy:
        raise ValueError("malformed root metadata version")
    path = (
        _decode_string_list(table["层级路径"], "root path")
        if "层级路径" in table
        else (title,)
    )
    aliases = (
        _decode_string_list(table["别名"], "root aliases")
        if "别名" in table
        else (() if table.get("旧标题", "无") == "无" else tuple(table["旧标题"].split("；")))
    )
    updated_at = table.get("Wiki 更新时间", "未知")
    root = PageState(
        page_id=page_id,
        title=title,
        status=table["状态"],
        space=table["Space"],
        version=version,
        url=url,
        parent_id=table.get("父页面 ID", ""),
        path=path,
        topic_id=table["主题 ID"],
        wiki_updated_at=None if updated_at == "未知" else updated_at,
        aliases=aliases,
        availability=table["可访问性"],
        review_needed=_parse_yes_no(table["需要复核"]),
    )
    return root, table["同步时间"], descendant_count


def _root_table(region: str) -> dict[str, str]:
    heading = re.search(r"^## 根页面元数据\r?\n", region, re.MULTILINE)
    if heading is None:
        raise ValueError("missing root metadata")
    section = re.split(r"\r?\n## ", region[heading.end() :], maxsplit=1)[0]
    rows = _table_rows(section, ("字段", "值"))
    table: dict[str, str] = {}
    for key, value in rows:
        if key in table:
            raise ValueError(f"duplicate root metadata field: {key}")
        table[key] = value
    return table


def _table_rows(section: str, header: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    lines = [line for line in section.splitlines() if line.strip()]
    if len(lines) < 2 or _split_row(lines[0]) != header:
        raise ValueError("malformed Markdown table header")
    separator = _split_row(lines[1])
    if len(separator) != len(header) or any(cell != "---" for cell in separator):
        raise ValueError("malformed Markdown table separator")
    rows = tuple(_split_row(line) for line in lines[2:])
    if any(len(row) != len(header) for row in rows):
        raise ValueError("malformed Markdown table row")
    return rows


def _split_row(line: str) -> tuple[str, ...]:
    if not line.startswith("|") or not line.rstrip().endswith("|"):
        raise ValueError("malformed Markdown table row")
    cells: list[str] = []
    current: list[str] = []
    content = line.strip()[1:-1]
    index = 0
    while index < len(content):
        character = content[index]
        if character == "\\" and index + 1 < len(content) and content[index + 1] == "|":
            current.append(content[index + 1])
            index += 2
            continue
        elif character == "|":
            cells.append(_trim_table_padding("".join(current)))
            current = []
        else:
            current.append(character)
        index += 1
    cells.append(_trim_table_padding("".join(current)))
    return tuple(cells)


def _trim_table_padding(value: str) -> str:
    if value.startswith(" "):
        value = value[1:]
    if value.endswith(" "):
        value = value[:-1]
    return value


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
    values = [value for key, value in parse_qsl(urlparse(source).query, keep_blank_values=True) if key == "pageId"]
    return values[0] if len(values) == 1 else None


def _frontmatter_errors(frontmatter: dict[str, object]) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(frontmatter.get("title"), str) or not str(frontmatter.get("title", "")).strip():
        errors.append("frontmatter title must be a non-empty string")
    if frontmatter.get("type") != "source-summary":
        errors.append("frontmatter type must be source-summary")
    if frontmatter.get("domain") != "work":
        errors.append("frontmatter domain must be work")
    if frontmatter.get("confidence") not in {"high", "medium", "low"}:
        errors.append("frontmatter confidence is invalid")
    encoded_date = frontmatter.get("date")
    if not isinstance(encoded_date, str):
        errors.append("frontmatter date must be an ISO date string")
    else:
        try:
            parsed_date = date.fromisoformat(encoded_date)
            if parsed_date.isoformat() != encoded_date:
                raise ValueError
        except ValueError:
            errors.append("frontmatter date must be an ISO date string")
    source = frontmatter.get("source")
    if not isinstance(source, str) or not source:
        errors.append("frontmatter source must be a non-empty string")
    for key in ("tags", "links"):
        value = frontmatter.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) or "\n" in item or "\r" in item for item in value):
            errors.append(f"frontmatter {key} must be a string list")
    links = frontmatter.get("links")
    if isinstance(links, list) and all(isinstance(item, str) for item in links):
        if any(re.fullmatch(r"\[\[[^\[\]\r\n|()]+\]\]", link) is None for link in links):
            errors.append("frontmatter links contain an unsafe wikilink")
    return tuple(errors)


def _validate_confluence_url(
    url: str,
    expected_page_id: str | None,
    *,
    expected_host: str | None = None,
    label: str,
) -> str:
    parsed = urlparse(url)
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.path != "/pages/viewpage.action"
    ):
        raise ValueError(f"{label} is not a safe HTTPS Confluence URL")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError(f"{label} is not a safe HTTPS Confluence URL") from error
    if port not in (None, 443):
        raise ValueError(f"{label} is not a safe HTTPS Confluence URL")
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    if expected_page_id is None or pairs != [("pageId", expected_page_id)]:
        if label == "source URL":
            raise ValueError("source pageId is missing, duplicated, or mismatched (source URL)")
        raise ValueError(f"{label} pageId is missing, duplicated, or mismatched")
    host = parsed.hostname.casefold().rstrip(".")
    if expected_host is not None and host != expected_host:
        raise ValueError(f"{label} differs from the configured Confluence host")
    return host


def _validate_topic_urls(
    root: PageState,
    children: dict[str, ChildEntry],
    *,
    source_url: object = None,
) -> None:
    host = _validate_confluence_url(root.url, root.page_id, label="source URL")
    if source_url is not None:
        if not isinstance(source_url, str):
            raise ValueError("source URL is invalid")
        source_host = _validate_confluence_url(source_url, root.page_id, label="source URL")
        if source_host != host or source_url != root.url:
            raise ValueError("source URL differs from the configured Confluence host or root URL")
    for child in children.values():
        _validate_confluence_url(
            child.page.url,
            child.page.page_id,
            expected_host=host,
            label="descendant metadata URL",
        )


def _catalog_root_url(documents: tuple[TopicDocument, ...]) -> str:
    if not documents:
        raise ValueError("cannot render catalog without a Confluence host")
    parsed = urlparse(documents[0].topic.url)
    host = _validate_confluence_url(
        documents[0].topic.url,
        documents[0].topic.page_id,
        label="catalog topic URL",
    )
    for document in documents[1:]:
        _validate_confluence_url(
            document.topic.url,
            document.topic.page_id,
            expected_host=host,
            label="catalog topic URL",
        )
    return urlunparse(("https", parsed.netloc, "/pages/viewpage.action", "", urlencode({"pageId": "73598402"}), ""))


def _catalog_entry(row: tuple[str, ...]) -> CatalogEntry:
    (
        page_id,
        title,
        encoded_aliases,
        local_wikilink,
        summary,
        encoded_tags,
        status,
        availability,
        descendant_count,
        version,
        synced_at,
        url,
    ) = row
    if local_wikilink != f"[[k1-activity-{page_id}]]":
        raise ValueError(f"catalog local wikilink mismatches pageId: {page_id}")
    try:
        parsed_count = int(descendant_count)
        parsed_version = int(version)
    except ValueError as error:
        raise ValueError("catalog count/version is malformed") from error
    if parsed_count < 0 or parsed_version < 1:
        raise ValueError("catalog count/version is malformed")
    return CatalogEntry(
        page_id=page_id,
        title=title,
        aliases=_decode_string_list(encoded_aliases, "catalog aliases"),
        local_wikilink=local_wikilink,
        summary=summary,
        mechanism_tags=_decode_string_list(encoded_tags, "catalog mechanism tags"),
        status=status,
        availability=availability,
        descendant_count=parsed_count,
        version=parsed_version,
        synced_at=synced_at,
        url=url,
    )


def _mechanism_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(tag for tag in tags if tag not in {"K1", "活动", "历史"})


def _json_list(values) -> str:
    return json.dumps(list(values), ensure_ascii=False, separators=(",", ":"))


def _decode_string_list(value: str, label: str) -> tuple[str, ...]:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"malformed {label}") from error
    if not isinstance(decoded, list) or any(not isinstance(item, str) for item in decoded):
        raise ValueError(f"malformed {label}")
    return tuple(decoded)


def _parse_yes_no(value: str) -> bool:
    if value == "是":
        return True
    if value == "否":
        return False
    raise ValueError("malformed review flag")


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


def _page_key(page: PageState) -> tuple[str, tuple[int, int | str]]:
    return (normalize_label(page.title).casefold(), _id_key(page.page_id))
