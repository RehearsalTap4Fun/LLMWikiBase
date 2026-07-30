from dataclasses import replace

import pytest

from tools.k1_activity_index.markdown import (
    ChildEntry,
    CuratedTopic,
    TopicDocument,
    parse_catalog_page,
    parse_topic_page,
    render_catalog,
    render_topic_page,
    validate_topic_page,
)
from tools.k1_activity_index.models import PageState


def _state(page_id, title, topic_id="100", parent_id="73598402", availability="available"):
    return PageState(
        page_id=page_id,
        title=title,
        status="current",
        space="KEFU",
        version=1,
        url=f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
        parent_id=parent_id,
        path=(title,),
        topic_id=topic_id,
        wiki_updated_at=None,
        aliases=("旧标题",),
        availability=availability,
        review_needed=True,
    )


def _document(page_id="100", title="K1 主题A", availability="available"):
    topic = _state(page_id, title, topic_id=page_id, availability=availability)
    child = replace(
        _state("101" + page_id, "主题A商店", topic_id=page_id, parent_id=page_id),
        path=(title, "主题A商店"),
        aliases=("旧商店名",),
    )
    return TopicDocument(
        topic=topic,
        curated=CuratedTopic(
            summary="主题A活动，包含商店入口。",
            aliases=("主题A",),
            tags=("K1", "活动", "商店/兑换"),
            links=("[[k1-activity-catalog]]", "[[k1-confluence-routing]]"),
            notes="",
        ),
        children=(ChildEntry(child, "商店/兑换", "主题A商店的商店/兑换规则入口。"),),
        synced_at="2026-07-29T12:00:00+08:00",
    )


def _region(text, start, end):
    return text[text.index(start) : text.index(end) + len(end)]


def test_rendered_page_has_required_frontmatter_and_no_body():
    rendered = render_topic_page(_document())

    assert validate_topic_page(rendered, "100") == ()
    assert "活动涉及服务器" not in rendered
    assert "3320214" not in rendered
    assert "Wiki 更新时间 | 未知" in rendered
    assert "| 版本 | 1 |" in rendered
    assert "| 后代页面数 | 1 |" in rendered
    parsed = parse_topic_page(rendered)
    assert parsed.root.version == 1
    assert parsed.root.path == ("K1 主题A",)
    assert parsed.children["101100"].page.path == ("K1 主题A", "主题A商店")
    assert parsed.children["101100"].page.aliases == ("旧商店名",)


def test_existing_curated_region_survives_rerender_byte_for_byte():
    first = render_topic_page(_document())
    edited = first.replace("主题A活动，包含商店入口。", "人工确认后的摘要。")
    parsed = parse_topic_page(edited)
    rerendered = render_topic_page(
        replace(_document(), curated=parsed.curated),
        existing_text=edited,
    )

    assert _region(rerendered, "<!-- K1-ACTIVITY-CURATED:START -->", "<!-- K1-ACTIVITY-CURATED:END -->") == _region(
        edited,
        "<!-- K1-ACTIVITY-CURATED:START -->",
        "<!-- K1-ACTIVITY-CURATED:END -->",
    )


def test_parser_rejects_missing_curated_end():
    broken = '---\ntitle: "x"\n---\n<!-- K1-ACTIVITY-CURATED:START -->'

    with pytest.raises(ValueError, match="curated"):
        parse_topic_page(broken)


def test_parser_rejects_duplicated_or_malformed_structure():
    page = render_topic_page(_document())

    with pytest.raises(ValueError, match="curated"):
        parse_topic_page(page + "\n<!-- K1-ACTIVITY-CURATED:START -->")
    with pytest.raises(ValueError, match="frontmatter"):
        parse_topic_page(page.replace('title: "K1 主题A"', "title: not-json"))


def test_parser_and_validator_reject_crossing_protected_markers():
    page = render_topic_page(_document())
    crossing = page.replace(
        "<!-- K1-ACTIVITY-CURATED:END -->\n\n<!-- K1-ACTIVITY-GENERATED:START -->",
        "<!-- K1-ACTIVITY-GENERATED:START -->\n<!-- K1-ACTIVITY-CURATED:END -->",
    )

    with pytest.raises(ValueError, match="protected marker order"):
        parse_topic_page(crossing)
    assert any("protected marker order" in error for error in validate_topic_page(crossing, "100"))


def test_crlf_page_parses_and_preserves_curated_region_byte_for_byte():
    page = render_topic_page(_document())
    crlf_page = page.replace("\n", "\r\n")
    parsed = parse_topic_page(crlf_page)

    rerendered = render_topic_page(replace(_document(), curated=parsed.curated), existing_text=crlf_page)

    assert _region(rerendered, "<!-- K1-ACTIVITY-CURATED:START -->", "<!-- K1-ACTIVITY-CURATED:END -->") == _region(
        crlf_page,
        "<!-- K1-ACTIVITY-CURATED:START -->",
        "<!-- K1-ACTIVITY-CURATED:END -->",
    )


def test_parser_rejects_unmanaged_or_copied_body_content():
    page = render_topic_page(_document())

    with pytest.raises(ValueError, match="unmanaged"):
        parse_topic_page(page.replace("<!-- K1-ACTIVITY-GENERATED:START -->", "人工段落\n<!-- K1-ACTIVITY-GENERATED:START -->"))
    with pytest.raises(ValueError, match="forbidden"):
        parse_topic_page(page + "<!-- K1-ACTIVITY-BODY:START -->")


def test_existing_child_summary_survives_when_child_version_is_unchanged():
    first = render_topic_page(_document())
    edited = first.replace("主题A商店的商店/兑换规则入口。", "人工核定的子页摘要。")
    parsed = parse_topic_page(edited)

    rerendered = render_topic_page(
        replace(_document(), children=tuple(parsed.children.values())),
        existing_text=edited,
    )

    assert "人工核定的子页摘要。" in rerendered


def test_backslashes_in_child_summary_round_trip_and_survive_rerender():
    summary = r"C:\manual\keep"
    document = replace(_document(), children=(ChildEntry(_document().children[0].page, "商店/兑换", summary),))
    first = render_topic_page(document)
    parsed = parse_topic_page(first)

    assert parsed.children["101100"].summary == summary
    rerendered = render_topic_page(document, existing_text=first)
    assert summary in rerendered


def test_child_title_trailing_nonbreaking_space_round_trips_exactly():
    child = replace(
        _document().children[0],
        page=replace(_document().children[0].page, title="联盟争霸赛活动\u00a0"),
    )

    parsed = parse_topic_page(render_topic_page(replace(_document(), children=(child,))))

    assert parsed.children[child.page.page_id].page.title == "联盟争霸赛活动\u00a0"


def test_render_escapes_markdown_table_cells_and_sorts_descendants():
    left = ChildEntry(_state("b", "B\n标题", topic_id="100", parent_id="100"), "角色|一", "摘要\n第二行")
    right = ChildEntry(_state("a", "A", topic_id="100", parent_id="100"), "角色", "摘要")
    rendered = render_topic_page(replace(_document(), children=(left, right)))

    assert rendered.index("| a |") < rendered.index("| b |")
    assert "B 标题" in rendered
    assert "角色\\|一" in rendered
    assert "摘要 第二行" in rendered


def test_validate_reports_explicit_errors_for_unsafe_and_inconsistent_pages():
    page = render_topic_page(_document())
    row = next(line for line in page.splitlines() if line.startswith("| 101100 |"))
    malformed = page.replace('source: "https://wiki.example.test/pages/viewpage.action?pageId=100"', 'source: "https://wiki.example.test/pages/viewpage.action?pageId=999"')
    malformed = malformed.replace(row, row.replace("| 100 | 100 |", "| 999 | 100 |"))
    malformed = malformed.replace("<!-- K1-ACTIVITY-GENERATED:END -->", "<!-- K1-ACTIVITY-GENERATED:END -->\n<!-- copied-body -->")

    errors = validate_topic_page(malformed, "100")

    assert any("source pageId" in error for error in errors)
    assert any("topic ID" in error for error in errors)
    assert any("forbidden" in error for error in errors)


def test_validate_rejects_duplicate_descendant_ids_and_forbidden_frontmatter():
    page = render_topic_page(_document())
    row = next(line for line in page.splitlines() if line.startswith("| 101100 |"))
    malformed = page.replace(row, f"{row}\n{row}").replace("---\n", "---\ntoken: \"secret\"\n", 1)

    errors = validate_topic_page(malformed, "100")

    assert any("duplicate descendant pageId" in error for error in errors)
    assert any("forbidden frontmatter key" in error for error in errors)


@pytest.mark.parametrize("missing_key", ("tags", "links"))
def test_validate_returns_diagnostic_when_required_curated_frontmatter_is_missing(missing_key):
    page = render_topic_page(_document())
    frontmatter_line = next(line for line in page.splitlines() if line.startswith(f"{missing_key}: "))
    malformed = page.replace(f"{frontmatter_line}\n", "", 1)

    errors = validate_topic_page(malformed, "100")

    assert f"missing frontmatter key: {missing_key}" in errors


def test_validate_reports_unmanaged_content_and_malformed_curated_sections():
    page = render_topic_page(_document())
    unmanaged = page.replace("<!-- K1-ACTIVITY-GENERATED:START -->", "人工段落\n<!-- K1-ACTIVITY-GENERATED:START -->")
    malformed_curated = page.replace("## 别名", "## 其他标题", 1)

    assert any("unmanaged" in error for error in validate_topic_page(unmanaged, "100"))
    assert any("curated sections" in error for error in validate_topic_page(malformed_curated, "100"))


def test_catalog_groups_historical_and_inaccessible_topics_and_preserves_intro():
    current = _document("100", "K1 当前活动")
    historical = replace(
        _document("200", "K1 旧活动"),
        curated=CuratedTopic("历史活动。", ("旧活动",), ("K1", "活动", "历史"), (), ""),
    )
    inaccessible = _document("300", "K1 不可访问活动", "inaccessible")
    catalog = render_catalog((current, historical, inaccessible), "2026-07-29T12:00:00+08:00")
    edited = catalog.replace("本目录由 Confluence 页面元数据生成。", "人工维护的目录导言。")

    rerendered = render_catalog((current, historical, inaccessible), "2026-07-30T12:00:00+08:00", edited)

    assert "## 当前可用" in rerendered
    assert "## 历史/过期" in rerendered
    assert "## 不可访问" in rerendered
    assert _region(rerendered, "<!-- K1-ACTIVITY-CURATED:START -->", "<!-- K1-ACTIVITY-CURATED:END -->") == _region(
        edited,
        "<!-- K1-ACTIVITY-CURATED:START -->",
        "<!-- K1-ACTIVITY-CURATED:END -->",
    )
    assert 'confidence: "low"' in render_topic_page(historical)
    parsed = parse_catalog_page(rerendered)
    assert parsed["100"].aliases == ("主题A", "旧标题")
    assert parsed["100"].local_wikilink == "[[k1-activity-100]]"
    assert parsed["100"].mechanism_tags == ("商店/兑换",)
    assert parsed["100"].availability == "available"
    assert parsed["100"].status == "current"
    assert parsed["100"].descendant_count == 1
    assert parsed["100"].synced_at == "2026-07-30T12:00:00+08:00"


@pytest.mark.parametrize(
    ("line_prefix", "replacement", "expected_error"),
    (
        ("type:", 'type: "concept"', "frontmatter type"),
        ("domain:", 'domain: "gaming"', "frontmatter domain"),
        ("confidence:", 'confidence: "certain"', "frontmatter confidence"),
        ("date:", 'date: "2026-02-30"', "frontmatter date"),
        ("tags:", 'tags: "K1"', "frontmatter tags"),
        ("links:", 'links: [1]', "frontmatter links"),
    ),
)
def test_frontmatter_validation_is_strict(line_prefix, replacement, expected_error):
    page = render_topic_page(_document())
    old_line = next(line for line in page.splitlines() if line.startswith(line_prefix))

    errors = validate_topic_page(page.replace(old_line, replacement, 1), "100")

    assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    "unsafe_source",
    (
        "http://wiki.example.test/pages/viewpage.action?pageId=100",
        "https://user@wiki.example.test/pages/viewpage.action?pageId=100",
        "https://wiki.example.test/pages/viewpage.action?pageId=100#fragment",
        "https://wiki.example.test/pages/viewpage.action?pageId=100&pageId=100",
        "https://evil.example.test/pages/viewpage.action?pageId=100",
    ),
)
def test_topic_validation_rejects_unsafe_or_mismatched_markdown_destinations(unsafe_source):
    page = render_topic_page(_document())
    source = 'https://wiki.example.test/pages/viewpage.action?pageId=100'
    if "evil.example" in unsafe_source:
        malformed = page.replace(
            source,
            unsafe_source,
            1,
        )
    else:
        malformed = page.replace(source, unsafe_source)

    errors = validate_topic_page(malformed, "100")

    assert any("source URL" in error or "Confluence host" in error for error in errors)
