"""Behavioral tests for the offline K1 activity search."""

from pathlib import Path
import json
import subprocess
import sys
from unittest.mock import patch

import pytest

from tools.k1_activity_index.markdown import (
    ChildEntry,
    CuratedTopic,
    TopicDocument,
    render_topic_page,
)
from tools.k1_activity_index.models import PageState
from tools.k1_activity_index import query as query_module
from tools.k1_activity_index.query import load_search_documents, search_index


def _state(page_id, title, topic_id, parent_id):
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
        aliases=(),
        availability="available",
        review_needed=False,
    )


def _write_topic(directory, topic_id, title, aliases, children):
    topic = _state(topic_id, title, topic_id, "73598402")
    document = TopicDocument(
        topic=topic,
        curated=CuratedTopic(
            summary=f"{title}主题活动。",
            aliases=aliases,
            tags=("K1", "活动", "通行证", "商店/兑换"),
            links=("[[k1-activity-catalog]]",),
            notes="",
        ),
        children=tuple(
            ChildEntry(
                _state(page_id, child_title, topic_id, topic_id),
                role,
                f"{child_title}的{role}规则入口。",
            )
            for page_id, child_title, role in children
        ),
        synced_at="2026-07-29T12:00:00+08:00",
    )
    (directory / f"k1-activity-{topic_id}.md").write_text(
        render_topic_page(document), encoding="utf-8"
    )


@pytest.fixture
def activity_index(tmp_path: Path):
    directory = tmp_path / "k1-activities"
    directory.mkdir()
    _write_topic(
        directory,
        "248877776",
        "K1 盛夏假面",
        ("盛夏假面", "假面节"),
        (
            ("248877789", "K1 盛夏通行证", "通行证"),
            ("248877804", "K1盛夏宝铺", "商店/兑换"),
        ),
    )
    _write_topic(
        directory,
        "233086310",
        "K1 冬雪新年",
        ("冬雪新年",),
        (("300000001", "K1 冬雪通行证", "通行证"),),
    )
    return directory


def test_exact_topic_alias_and_child_title_have_specific_ranking(activity_index: Path):
    assert search_index(activity_index, "盛夏假面")[0].match_kind == "topic-exact"
    assert search_index(activity_index, "假面节")[0].match_kind == "alias-exact"
    child_hit = search_index(activity_index, "盛夏通行证")[0]
    assert child_hit.match_kind == "child-exact"
    assert child_hit.wiki_url.endswith("pageId=248877789")


def test_representative_match_kinds_have_fixed_score_weights(activity_index: Path):
    assert search_index(activity_index, "盛夏假面")[0].score == 100
    assert search_index(activity_index, "假面节")[0].score == 95
    assert search_index(activity_index, "盛夏通行证")[0].score == 90
    assert search_index(activity_index, "盛夏 + 商店")[0].score == 88
    assert search_index(activity_index, "盛夏")[0].score == 80
    assert search_index(activity_index, "活动")[0].score == 70
    assert search_index(activity_index, "主题")[0].score == 50


def test_theme_and_role_route_to_relevant_child(activity_index: Path):
    hit = search_index(activity_index, "盛夏 + 商店")[0]
    assert hit.topic_title == "K1 盛夏假面"
    assert hit.child_title == "K1盛夏宝铺"
    assert hit.wiki_url.endswith("pageId=248877804")


def test_equal_scores_keep_all_ambiguous_candidates(activity_index: Path):
    hits = search_index(activity_index, "通行证", limit=10)
    top_score = hits[0].score
    assert len([hit for hit in hits if hit.score == top_score]) == 2


def test_limit_preserves_tied_top_hits_in_deterministic_order(tmp_path: Path):
    directory = tmp_path / "k1-activities"
    directory.mkdir()
    _write_topic(directory, "20", "K1 Same", (), (("22", "K1 Pass", "role"),))
    _write_topic(directory, "10", "K1 Same", (), (("11", "K1 Pass", "role"),))

    hits = search_index(directory, "Pass", limit=1)

    assert [(hit.topic_page_id, hit.child_page_id) for hit in hits] == [("10", "11"), ("20", "22")]
    assert {hit.score for hit in hits} == {90}


def test_loader_rejects_unsafe_managed_topic_pages(activity_index: Path):
    (activity_index / "notes.md").write_text("unmanaged", encoding="utf-8")
    (activity_index / "k1-activity-999.md").write_text("unmanaged", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid activity document"):
        load_search_documents(activity_index)


def test_loader_ignores_unmanaged_files(activity_index: Path):
    (activity_index / "notes.md").write_text("unmanaged", encoding="utf-8")

    documents = load_search_documents(activity_index)

    assert [document.page_id for document in documents] == ["233086310", "248877776"]
    assert {child.page_id for child in documents[1].children} == {"248877789", "248877804"}


def test_loader_rejects_a_directory_symlink_before_resolving(activity_index: Path, tmp_path: Path):
    link = tmp_path / "activity-link"
    original_resolve = Path.resolve
    original_is_symlink = Path.is_symlink

    def fake_resolve(path, strict=False):
        if path == link:
            return activity_index
        return original_resolve(path, strict=strict)

    def fake_is_symlink(path):
        return path == link or original_is_symlink(path)

    with patch.object(query_module.Path, "resolve", fake_resolve), patch.object(
        query_module.Path, "is_symlink", fake_is_symlink
    ), pytest.raises(ValueError, match="activity directory is a symlink"):
        load_search_documents(link)


def test_missing_activity_directory_is_an_error_but_empty_directory_is_valid(tmp_path: Path):
    missing = tmp_path / "missing"
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(FileNotFoundError, match="activity directory does not exist"):
        load_search_documents(missing)
    assert load_search_documents(empty) == ()


def test_normalization_handles_k1_case_spacing_and_full_width_punctuation(activity_index: Path):
    hit = search_index(activity_index, " k1　盛夏＋商店 ")[0]

    assert hit.match_kind == "topic-child-combination"
    assert hit.child_page_id == "248877804"


def test_cli_json_is_body_free_and_returns_empty_success_for_no_match(activity_index: Path):
    script = Path(__file__).parents[1] / "tools" / "search_k1_activity.py"
    result = subprocess.run(
        [sys.executable, str(script), "盛夏 + 商店", "--activity-dir", str(activity_index), "--json"],
        text=True,
        capture_output=True,
        check=False,
        encoding="utf-8",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload[0]["child_page_id"] == "248877804"
    assert all("body" not in hit for hit in payload)

    missing = subprocess.run(
        [sys.executable, str(script), "不存在", "--activity-dir", str(activity_index), "--json"],
        text=True,
        capture_output=True,
        check=False,
        encoding="utf-8",
    )
    assert missing.returncode == 0
    assert json.loads(missing.stdout) == []


def test_cli_missing_activity_directory_returns_safe_json_error(tmp_path: Path):
    script = Path(__file__).parents[1] / "tools" / "search_k1_activity.py"
    result = subprocess.run(
        [sys.executable, str(script), "anything", "--activity-dir", str(tmp_path / "missing"), "--json"],
        text=True,
        capture_output=True,
        check=False,
        encoding="utf-8",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert "activity directory does not exist" in payload["message"]
