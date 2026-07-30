import json

import pytest

from tools.k1_activity_index.models import CrawlSnapshot, IndexState, PageRecord
from tools.k1_activity_index.state import (
    compute_next_state,
    dump_state,
    load_state,
    mark_reviewed,
    mark_unavailable,
)


def _record(page_id="100", title="主题A", version=1, parent_id="73598402"):
    return PageRecord(
        page_id=page_id,
        title=title,
        status="current",
        space="KEFU",
        version=version,
        url=f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
        parent_id=parent_id,
        path=(title,),
        topic_id="100",
    )


def _snapshot(records, root="73598402"):
    return CrawlSnapshot(root, {record.page_id: record for record in records}, {root: tuple(record.page_id for record in records)})


def test_rename_keeps_old_title_as_alias_and_requires_review():
    first, _ = compute_next_state(IndexState.empty("73598402"), _snapshot([_record()]), "2026-07-29T10:00:00+08:00")
    second, changes = compute_next_state(first, _snapshot([_record(title="主题A新名", version=2)]), "2026-07-29T11:00:00+08:00")

    assert second.pages["100"].aliases == ("主题A",)
    assert second.pages["100"].review_needed is True
    assert changes.renamed_ids == ("100",)
    assert changes.content_ids == ("100",)


def test_missing_page_is_retained_without_body_or_credentials():
    first, _ = compute_next_state(IndexState.empty("73598402"), _snapshot([_record()]), "2026-07-29T10:00:00+08:00")
    second, _ = compute_next_state(first, _snapshot([]), "2026-07-29T11:00:00+08:00")

    payload = dump_state(second)
    assert second.pages["100"].availability == "missing-from-root"
    assert '"body"' not in payload
    assert "CONFLUENCE_API_TOKEN" not in payload


def test_missing_page_is_reported_only_when_it_first_disappears():
    first, _ = compute_next_state(IndexState.empty("root"), _snapshot([_record("100", parent_id="root")], root="root"), "first")
    missing, first_changes = compute_next_state(first, _snapshot([], root="root"), "second")
    still_missing, second_changes = compute_next_state(missing, _snapshot([], root="root"), "third")

    assert first_changes.missing_ids == ("100",)
    assert still_missing.pages["100"].availability == "missing-from-root"
    assert second_changes.missing_ids == ()


def test_changes_are_deterministically_sorted_and_track_moves_and_versions():
    previous, _ = compute_next_state(
        IndexState.empty("root"),
        _snapshot([_record("10", parent_id="root"), _record("2", parent_id="root")], root="root"),
        "first",
    )
    current, changes = compute_next_state(
        previous,
        _snapshot([_record("10", version=2, parent_id="other"), _record("2", parent_id="root"), _record("abc", parent_id="root")], root="root"),
        "second",
    )

    assert changes.new_ids == ("abc",)
    assert changes.version_changed_ids == ("10",)
    assert changes.moved_ids == ("10",)
    assert changes.content_ids == ("10", "abc")
    assert current.pages["10"].review_needed is True


def test_dump_state_is_stable_for_mixed_ids_and_page_insertion_order():
    state_a, _ = compute_next_state(
        IndexState.empty("root"),
        _snapshot([_record("10", parent_id="root"), _record("abc", parent_id="root"), _record("2", parent_id="root")], root="root"),
        "now",
    )
    state_b, _ = compute_next_state(
        IndexState.empty("root"),
        _snapshot([_record("2", parent_id="root"), _record("10", parent_id="root"), _record("abc", parent_id="root")], root="root"),
        "now",
    )

    assert dump_state(state_a) == dump_state(state_b)
    assert list(json.loads(dump_state(state_a))["pages"]) == ["10", "2", "abc"]


def test_unavailable_and_review_mutations_preserve_metadata():
    state, _ = compute_next_state(IndexState.empty("root"), _snapshot([_record("2", parent_id="root"), _record("10", parent_id="root")], root="root"), "first")

    unavailable = mark_unavailable(state, "2", 403)
    reviewed = mark_reviewed(unavailable, ["10", "missing", "2"])

    assert unavailable.pages["2"].availability == "unavailable-403"
    assert unavailable.pages["2"].title == "主题A"
    assert reviewed.pages["2"].review_needed is False
    assert reviewed.pages["10"].review_needed is False


def test_state_round_trip_and_load_missing_file(tmp_path):
    path = tmp_path / "state.json"
    assert load_state(path, "root") == IndexState.empty("root")
    state, _ = compute_next_state(IndexState.empty("root"), _snapshot([_record("10", parent_id="root")], root="root"), "now")
    path.write_text(dump_state(state), encoding="utf-8")

    assert load_state(path, "root") == state


def test_dump_state_rejects_forbidden_keys(monkeypatch):
    state = IndexState.empty("root")
    monkeypatch.setattr("tools.k1_activity_index.state._to_payload", lambda _: {"token": "secret"})

    with pytest.raises(ValueError, match="forbidden"):
        dump_state(state)
