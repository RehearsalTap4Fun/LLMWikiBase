import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest

from tools.k1_activity_index.crawl import IncompleteTreeError
from tools.k1_activity_index.models import ConfluenceCommandError, PageUnavailableError
from tools.k1_activity_index.service import SyncConfig, sync_index
from tools.k1_activity_index.query import search_index
from tools.k1_activity_index.transaction import write_batch_atomic as real_write_batch_atomic


def _child(page_id, title, version=1):
    return {
        "id": page_id,
        "title": title,
        "status": "current",
        "space": "KEFU",
        "version": version,
        "url": f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
    }


class FakeClient:
    def __init__(self, responses=None, pages=None):
        self.responses = responses or {
            "73598402": {"total": 1, "results": [_child("100", "K1 主题A")]},
            "100": {"total": 1, "results": [_child("101", "主题A商店")]},
            "101": {"total": 0, "results": []},
        }
        self.pages = pages or {
            "100": {"id": "100", "title": "K1 主题A", "body": "合成活动说明。"},
            "101": {"id": "101", "title": "主题A商店", "body": "合成商店规则。"},
        }
        self.page_calls = []
        self.base_url = "https://wiki.example.test"

    def check(self):
        return None

    def children(self, page_id, limit):
        return self.responses[page_id]

    def page(self, page_id):
        self.page_calls.append(page_id)
        value = self.pages[page_id]
        if isinstance(value, Exception):
            raise value
        return value


def _config(tmp_path, dry_run=False, validate_only=False, mark_reviewed=()):
    return SyncConfig(
        root_page_id="73598402",
        wiki_work_dir=tmp_path / "wiki" / "work",
        state_path=tmp_path / ".cache" / "k1-activity-index" / "state.json",
        review_report_path=tmp_path / ".cache" / "k1-activity-index" / "review-report.json",
        child_limit=1000,
        dry_run=dry_run,
        validate_only=validate_only,
        mark_reviewed=mark_reviewed,
    )


def _two_topic_client():
    responses = {
        "73598402": {
            "total": 2,
            "results": [_child("100", "K1 Topic A"), _child("200", "K1 Topic B")],
        },
        "100": {"total": 0, "results": []},
        "200": {"total": 0, "results": []},
    }
    pages = {
        "100": {"id": "100", "title": "K1 Topic A", "body": ""},
        "200": {"id": "200", "title": "K1 Topic B", "body": ""},
    }
    return FakeClient(responses=responses, pages=pages)


def _topic_moved_under_100_client():
    responses = {
        "73598402": {
            "total": 1,
            "results": [_child("100", "K1 Topic A")],
        },
        "100": {"total": 1, "results": [_child("200", "K1 Topic B")]},
        "200": {"total": 0, "results": []},
    }
    pages = {
        "100": {"id": "100", "title": "K1 Topic A", "body": ""},
        "200": {"id": "200", "title": "K1 Topic B", "body": ""},
    }
    return FakeClient(responses=responses, pages=pages)


def test_first_sync_writes_catalog_topic_state_and_review_report(tmp_path: Path):
    config = _config(tmp_path)
    report = sync_index(
        config,
        FakeClient(),
        lambda: "2026-07-29T12:00:00+08:00",
    )

    assert report.topic_count == 1
    assert report.page_count == 2
    assert (config.wiki_work_dir / "k1-activity-catalog.md").exists()
    assert (config.wiki_work_dir / "k1-activities" / "k1-activity-100.md").exists()
    state_text = config.state_path.read_text(encoding="utf-8")
    assert "合成活动说明" not in state_text
    assert json.loads(state_text)["complete"] is True
    assert report.truncated is False
    report_data = json.loads(config.review_report_path.read_text(encoding="utf-8"))
    assert report_data["review_needed"] == ["100", "101"]
    assert report_data["complete"] is True


def test_config_reparse_ancestor_is_rejected_before_client_or_clock(tmp_path: Path, monkeypatch):
    import os
    from types import SimpleNamespace

    config = _config(tmp_path)
    junction = config.wiki_work_dir
    real_lstat = os.lstat

    def fake_lstat(path):
        if Path(path) == junction:
            return SimpleNamespace(st_mode=0o040755, st_file_attributes=0x400)
        return real_lstat(path)

    monkeypatch.setattr(os, "lstat", fake_lstat)

    class ExplodingClient:
        def __getattr__(self, name):
            raise AssertionError(f"unsafe config accessed client attribute {name}")

    with pytest.raises(ValueError, match="reparse"):
        sync_index(
            config,
            ExplodingClient(),
            lambda: (_ for _ in ()).throw(AssertionError("unsafe config called clock")),
        )


def test_second_sync_skips_bodies_when_versions_are_unchanged(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    second_client = FakeClient()

    sync_index(config, second_client, lambda: "2026-07-29T13:00:00+08:00")

    assert second_client.page_calls == []


def test_dry_run_checks_tree_without_fetching_body_or_writing(tmp_path: Path):
    config = _config(tmp_path, dry_run=True)
    client = FakeClient()

    report = sync_index(config, client, lambda: "2026-07-29T12:00:00+08:00")

    assert report.dry_run is True
    assert client.page_calls == []
    assert not config.state_path.exists()


def test_non_numeric_root_page_id_is_rejected_before_client_access(tmp_path: Path):
    config = replace(_config(tmp_path), root_page_id=r"..\73598402")

    class ExplodingClient:
        def __getattr__(self, name):
            raise AssertionError(f"invalid root accessed client attribute {name}")

    with pytest.raises(ValueError, match="ASCII digits"):
        sync_index(
            config,
            ExplodingClient(),
            lambda: (_ for _ in ()).throw(AssertionError("invalid root called clock")),
        )

    assert not config.state_path.exists()


def test_page_id_cannot_escape_the_configured_topic_output_root(tmp_path: Path):
    bad_id = "segment/../../../outside"
    client = FakeClient(
        responses={
            "73598402": {"total": 1, "results": [_child(bad_id, "K1 Unsafe")]},
            bad_id: {"total": 0, "results": []},
        },
        pages={bad_id: {"id": bad_id, "title": "K1 Unsafe", "body": ""}},
    )

    with pytest.raises(ValueError, match="ASCII digits"):
        sync_index(
            _config(tmp_path),
            client,
            lambda: "2026-07-29T12:00:00+08:00",
        )

    assert client.page_calls == []
    assert not (tmp_path / "wiki" / "outside.md").exists()


def test_snapshot_url_must_match_configured_confluence_host_before_body_or_write(tmp_path: Path):
    unsafe = _child("100", "K1 Unsafe")
    unsafe["url"] = "https://evil.example.test/pages/viewpage.action?pageId=100"
    client = FakeClient(
        responses={
            "73598402": {"total": 1, "results": [unsafe]},
            "100": {"total": 0, "results": []},
        },
        pages={"100": {"id": "100", "title": "K1 Unsafe", "body": ""}},
    )

    with pytest.raises(ValueError, match="Confluence host"):
        sync_index(_config(tmp_path), client, lambda: "2026-07-29T12:00:00+08:00")

    assert client.page_calls == []


@pytest.mark.parametrize(
    "bad_id",
    (
        "segment/../999",
        r"segment\..\999",
        r"segment/..\999",
    ),
)
def test_non_numeric_page_id_is_rejected_before_body_fetch_or_in_directory_overwrite(
    tmp_path: Path, bad_id: str
):
    config = _config(tmp_path)
    topic_dir = config.wiki_work_dir / "k1-activities"
    topic_dir.mkdir(parents=True)
    unmanaged = topic_dir / "999.md"
    unmanaged.write_text("unmanaged sentinel", encoding="utf-8")
    client = FakeClient(
        responses={
            "73598402": {"total": 1, "results": [_child(bad_id, "K1 Unsafe")]},
            bad_id: {"total": 0, "results": []},
        },
        pages={bad_id: {"id": bad_id, "title": "K1 Unsafe", "body": ""}},
    )

    with pytest.raises(ValueError, match="ASCII digits"):
        sync_index(
            config,
            client,
            lambda: "2026-07-29T12:00:00+08:00",
        )

    assert client.page_calls == []
    assert unmanaged.read_text(encoding="utf-8") == "unmanaged sentinel"
    assert not config.state_path.exists()


def test_catalog_orders_topics_by_normalized_title_before_page_id(tmp_path: Path):
    responses = {
        "73598402": {
            "total": 2,
            "results": [_child("100", "K1 Beta"), _child("200", "K1 Alpha")],
        },
        "100": {"total": 0, "results": []},
        "200": {"total": 0, "results": []},
    }
    pages = {
        "100": {"id": "100", "title": "K1 Beta", "body": ""},
        "200": {"id": "200", "title": "K1 Alpha", "body": ""},
    }
    config = _config(tmp_path)

    sync_index(
        config,
        FakeClient(responses=responses, pages=pages),
        lambda: "2026-07-29T12:00:00+08:00",
    )

    catalog = (config.wiki_work_dir / "k1-activity-catalog.md").read_text(encoding="utf-8")
    assert catalog.index("| 200 | K1 Alpha |") < catalog.index("| 100 | K1 Beta |")


def test_version_change_fetches_only_changed_page_and_preserves_curated_summary(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    topic_path = config.wiki_work_dir / "k1-activities" / "k1-activity-100.md"
    edited = topic_path.read_text(encoding="utf-8").replace(
        "主题A主题活动，包含商店/兑换等子活动入口。",
        "人工确认后的主题摘要。",
    )
    topic_path.write_text(edited, encoding="utf-8")
    changed_responses = {
        "73598402": {"total": 1, "results": [_child("100", "K1 主题A")]},
        "100": {"total": 1, "results": [_child("101", "主题A商店", version=2)]},
        "101": {"total": 0, "results": []},
    }
    changed_client = FakeClient(responses=changed_responses)

    sync_index(config, changed_client, lambda: "2026-07-29T13:00:00+08:00")

    assert changed_client.page_calls == ["101"]
    assert "人工确认后的主题摘要。" in topic_path.read_text(encoding="utf-8")


def test_sync_two_renames_reload_and_find_intermediate_topic_and_child_aliases(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    topic_path = config.wiki_work_dir / "k1-activities" / "k1-activity-100.md"
    first_text = topic_path.read_text(encoding="utf-8")
    curated_start = first_text.index("<!-- K1-ACTIVITY-CURATED:START -->")
    curated_end = first_text.index("<!-- K1-ACTIVITY-CURATED:END -->") + len("<!-- K1-ACTIVITY-CURATED:END -->")
    curated = first_text[curated_start:curated_end]

    def renamed(topic_title, child_title, version):
        return FakeClient(
            responses={
                "73598402": {"total": 1, "results": [_child("100", topic_title, version)]},
                "100": {"total": 1, "results": [_child("101", child_title, version)]},
                "101": {"total": 0, "results": []},
            },
            pages={
                "100": {"id": "100", "title": topic_title, "body": ""},
                "101": {"id": "101", "title": child_title, "body": ""},
            },
        )

    sync_index(config, renamed("K1 主题B", "主题B商店", 2), lambda: "2026-07-29T13:00:00+08:00")
    sync_index(config, renamed("K1 主题C", "主题C商店", 3), lambda: "2026-07-29T14:00:00+08:00")

    reloaded = topic_path.read_text(encoding="utf-8")
    assert reloaded[reloaded.index("<!-- K1-ACTIVITY-CURATED:START -->"):reloaded.index("<!-- K1-ACTIVITY-CURATED:END -->") + len("<!-- K1-ACTIVITY-CURATED:END -->")] == curated
    topic_hit = search_index(topic_path.parent, "主题B")[0]
    child_hit = search_index(topic_path.parent, "主题B商店")[0]
    assert topic_hit.match_kind == "alias-exact"
    assert child_hit.match_kind == "child-alias-exact"
    assert child_hit.child_page_id == "101"


def test_incomplete_tree_leaves_existing_outputs_unchanged(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    catalog = config.wiki_work_dir / "k1-activity-catalog.md"
    original_catalog = catalog.read_text(encoding="utf-8")
    original_state = config.state_path.read_text(encoding="utf-8")
    broken = FakeClient(
        responses={
            "73598402": {"total": 2, "results": [_child("100", "K1 主题A")]},
        }
    )

    with pytest.raises(IncompleteTreeError):
        sync_index(config, broken, lambda: "2026-07-29T13:00:00+08:00")

    assert catalog.read_text(encoding="utf-8") == original_catalog
    assert config.state_path.read_text(encoding="utf-8") == original_state


def test_topic_moved_under_another_topic_removes_only_stale_managed_file(
    tmp_path: Path,
):
    config = _config(tmp_path)
    sync_index(config, _two_topic_client(), lambda: "2026-07-29T12:00:00+08:00")
    topic_dir = config.wiki_work_dir / "k1-activities"
    stale = topic_dir / "k1-activity-200.md"
    nonmatching = topic_dir / "k1-activity-not-managed.md"
    nonmatching.write_text("unmanaged sentinel", encoding="utf-8")

    sync_index(
        config,
        _topic_moved_under_100_client(),
        lambda: "2026-07-29T13:00:00+08:00",
    )

    assert not stale.exists()
    assert nonmatching.read_text(encoding="utf-8") == "unmanaged sentinel"
    report = sync_index(
        _config(tmp_path, validate_only=True),
        None,
        lambda: "unused",
    )
    assert report.topic_count == 1
    assert report.page_count == 2


def test_state_install_failure_restores_stale_topic_and_all_previous_outputs(
    tmp_path: Path, monkeypatch
):
    config = _config(tmp_path)
    sync_index(config, _two_topic_client(), lambda: "2026-07-29T12:00:00+08:00")
    topic_dir = config.wiki_work_dir / "k1-activities"
    topic_a = topic_dir / "k1-activity-100.md"
    stale = topic_dir / "k1-activity-200.md"
    catalog = config.wiki_work_dir / "k1-activity-catalog.md"
    tracked_paths = (topic_a, stale, catalog, config.review_report_path, config.state_path)
    previous = {path: path.read_text(encoding="utf-8") for path in tracked_paths}
    deleted_targets = []
    real_unlink = Path.unlink

    def recording_unlink(path, *args, **kwargs):
        if path == stale:
            deleted_targets.append(path)
        return real_unlink(path, *args, **kwargs)

    def fail_state_replace(source, target):
        if Path(target) == config.state_path:
            raise OSError("synthetic state install failure")
        Path(source).replace(target)

    def failing_batch(outputs, *, deletions=()):
        return real_write_batch_atomic(
            outputs,
            replace=fail_state_replace,
            deletions=deletions,
        )

    monkeypatch.setattr(Path, "unlink", recording_unlink)
    monkeypatch.setattr("tools.k1_activity_index.service.write_batch_atomic", failing_batch)

    with pytest.raises(OSError, match="synthetic state"):
        sync_index(
            config,
            _topic_moved_under_100_client(),
            lambda: "2026-07-29T13:00:00+08:00",
        )

    assert deleted_targets == [stale]
    assert {path: path.read_text(encoding="utf-8") for path in tracked_paths} == previous
    assert not tuple(topic_dir.glob("*.k1-activity-tmp"))
    assert not tuple(topic_dir.glob("*.k1-activity-backup"))


def test_403_is_recorded_but_transient_error_aborts(tmp_path: Path):
    config = _config(tmp_path)
    unavailable = FakeClient(
        pages={
            "100": {"id": "100", "title": "K1 主题A", "body": "合成活动说明。"},
            "101": PageUnavailableError("101", 403),
        }
    )
    sync_index(config, unavailable, lambda: "2026-07-29T12:00:00+08:00")
    assert '"availability": "inaccessible"' in config.state_path.read_text(encoding="utf-8")

    second_root = tmp_path / "transient"
    transient_config = _config(second_root)
    transient = FakeClient(
        pages={
            "100": {"id": "100", "title": "K1 主题A", "body": "合成活动说明。"},
            "101": ConfluenceCommandError("synthetic network failure"),
        }
    )
    with pytest.raises(ConfluenceCommandError, match="synthetic"):
        sync_index(
            transient_config,
            transient,
            lambda: "2026-07-29T12:00:00+08:00",
        )
    assert not transient_config.state_path.exists()


def test_non_403_or_404_unavailable_error_aborts_without_writing(tmp_path: Path):
    config = _config(tmp_path)
    client = FakeClient(
        pages={
            "100": {"id": "100", "title": "K1 主题A", "body": "活动说明。"},
            "101": PageUnavailableError("101", 500),
        }
    )

    with pytest.raises(PageUnavailableError) as error:
        sync_index(config, client, lambda: "2026-07-29T12:00:00+08:00")

    assert error.value.status_code == 500
    assert not config.state_path.exists()


def test_inaccessible_page_is_retried_even_when_version_is_unchanged(tmp_path: Path):
    config = _config(tmp_path)
    first = FakeClient(
        pages={
            "100": {"id": "100", "title": "K1 主题A", "body": "活动说明。"},
            "101": PageUnavailableError("101", 404),
        }
    )
    sync_index(config, first, lambda: "2026-07-29T12:00:00+08:00")
    recovered = FakeClient()

    report = sync_index(config, recovered, lambda: "2026-07-29T13:00:00+08:00")

    assert recovered.page_calls == ["101"]
    assert report.inaccessible_count == 0
    assert report.review_needed == ("100", "101")


def test_validate_only_reads_local_outputs_without_using_client(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")

    class ExplodingClient:
        def __getattr__(self, name):
            raise AssertionError(f"validate-only accessed client attribute {name}")

    report = sync_index(
        _config(tmp_path, validate_only=True),
        ExplodingClient(),
        lambda: (_ for _ in ()).throw(AssertionError("validate-only called clock")),
    )

    assert report.topic_count == 1
    assert report.page_count == 2


def test_validate_only_rejects_a_corrupt_topic_without_using_client(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    topic_path = config.wiki_work_dir / "k1-activities" / "k1-activity-100.md"
    topic_path.write_text(
        topic_path.read_text(encoding="utf-8").replace(
            "<!-- K1-ACTIVITY-GENERATED:END -->", ""
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="generated end"):
        sync_index(
            _config(tmp_path, validate_only=True),
            None,
            lambda: "unused",
        )


def test_validate_only_rejects_malformed_catalog_curated_sections(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    catalog_path = config.wiki_work_dir / "k1-activity-catalog.md"
    catalog_path.write_text(
        catalog_path.read_text(encoding="utf-8").replace("## 使用说明", "## 非法标题"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="catalog curated"):
        sync_index(_config(tmp_path, validate_only=True), None, lambda: "unused")


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (lambda text: "\n".join(line for line in text.splitlines() if not line.startswith("| 101 |")) + "\n", "descendant"),
        (lambda text: text.replace("pageId=101", "pageId=999", 1), "metadata"),
        (lambda text: text.replace(' | ["K1 主题A","主题A商店"] | 1 | current |', ' | ["K1 主题A","主题A商店"] | 9 | current |', 1), "metadata"),
    ),
)
def test_validate_only_reconciles_every_descendant_row(tmp_path: Path, mutation, expected):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    topic_path = config.wiki_work_dir / "k1-activities" / "k1-activity-100.md"
    topic_path.write_text(mutation(topic_path.read_text(encoding="utf-8")), encoding="utf-8")

    with pytest.raises(ValueError, match=expected):
        sync_index(_config(tmp_path, validate_only=True), None, lambda: "unused")


def test_validate_only_rejects_cross_topic_duplicate_ownership(tmp_path: Path):
    config = _config(tmp_path)
    client = _two_topic_client()
    client.responses["100"] = {"total": 1, "results": [_child("101", "Shared child")]}
    client.responses["101"] = {"total": 0, "results": []}
    client.pages["101"] = {"id": "101", "title": "Shared child", "body": ""}
    sync_index(config, client, lambda: "2026-07-29T12:00:00+08:00")
    topic_a = config.wiki_work_dir / "k1-activities" / "k1-activity-100.md"
    topic_b = config.wiki_work_dir / "k1-activities" / "k1-activity-200.md"
    row = next(line for line in topic_a.read_text(encoding="utf-8").splitlines() if line.startswith("| 101 |"))
    text_b = topic_b.read_text(encoding="utf-8")
    separator = next(line for line in text_b.splitlines() if line.startswith("| --- |") and line.count("|") > 5)
    topic_b.write_text(text_b.replace(separator, separator + "\n" + row, 1), encoding="utf-8")

    with pytest.raises(ValueError, match="ownership|topic"):
        sync_index(_config(tmp_path, validate_only=True), None, lambda: "unused")


def test_validate_only_rejects_catalog_row_mismatch(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    catalog = config.wiki_work_dir / "k1-activity-catalog.md"
    catalog.write_text(catalog.read_text(encoding="utf-8").replace("| 100 |", "| 999 |", 1), encoding="utf-8")

    with pytest.raises(ValueError, match="catalog"):
        sync_index(_config(tmp_path, validate_only=True), None, lambda: "unused")


@pytest.mark.parametrize(
    "mutation",
    (
        lambda text: text.replace("| 版本 | 1 |", "| 版本 | 9 |", 1),
        lambda text: text.replace("pageId=100", "pageId=999", 1),
    ),
)
def test_validate_only_rejects_topic_root_version_or_url_mismatch(tmp_path: Path, mutation):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    topic = config.wiki_work_dir / "k1-activities" / "k1-activity-100.md"
    topic.write_text(mutation(topic.read_text(encoding="utf-8")), encoding="utf-8")

    with pytest.raises(ValueError, match="root|source|metadata"):
        sync_index(_config(tmp_path, validate_only=True), None, lambda: "unused")


def test_mark_reviewed_is_rendered_and_state_is_installed_last(tmp_path: Path, monkeypatch):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    targets = []

    def recording_write(outputs, *, deletions=()):
        assert deletions == ()
        targets.extend(outputs)
        for path, text in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    monkeypatch.setattr("tools.k1_activity_index.service.write_batch_atomic", recording_write)
    reviewed_config = _config(tmp_path, mark_reviewed=("100", "101"))

    report = sync_index(
        reviewed_config,
        FakeClient(),
        lambda: "2026-07-29T13:00:00+08:00",
    )

    assert report.review_needed == ()
    assert targets[-1] == config.state_path
    assert json.loads(config.review_report_path.read_text(encoding="utf-8"))["review_needed"] == []


def test_cli_validate_only_prints_json_and_returns_explicit_status(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    script = Path(__file__).parents[1] / "tools" / "sync_k1_activity_index.py"
    command = [
        sys.executable,
        str(script),
        "--validate-only",
        "--wiki-work-dir",
        str(config.wiki_work_dir),
        "--state-path",
        str(config.state_path),
        "--review-report-path",
        str(config.review_report_path),
    ]

    success = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert success.returncode == 0
    assert json.loads(success.stdout)["status"] == "ok"

    config.state_path.unlink()
    failure = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert failure.returncode == 1
    failure_data = json.loads(failure.stdout)
    assert failure_data["status"] == "error"
    assert failure_data["paths"]["state"] == str(config.state_path)
    assert "message" not in failure_data
    assert failure.stderr == "K1 activity sync failed (state-invalid).\n"


def test_cli_dry_run_uses_fake_confluence_without_fetching_or_writing(
    tmp_path: Path, monkeypatch
):
    fake_cli = tmp_path / "fake_confluence.pyz"
    with ZipFile(fake_cli, "w") as archive:
        archive.writestr("__main__.py", "import json\nprint(json.dumps({}))\n")
        archive.writestr("confluence_skill/__init__.py", "")
        archive.writestr(
            "confluence_skill/client.py",
            "class ConfluenceClient:\n"
            "    def get(self, path, params=None):\n"
            "        if '/73598402/' in path:\n"
            "            pages = [{'id': '100', 'title': 'K1 Topic', 'status': 'current', 'space': {'key': 'KEFU'}, 'version': {'number': 1}, '_links': {'webui': '/pages/viewpage.action?pageId=100'}}]\n"
            "        elif '/100/' in path:\n"
            "            pages = []\n"
            "        else:\n"
            "            raise RuntimeError('unexpected body fetch')\n"
            "        start, limit = params['start'], params['limit']\n"
            "        results = pages[start:start + limit]\n"
            "        return {'total': len(pages), 'start': start, 'limit': limit, 'size': len(results), '_links': {'base': 'https://wiki.example.test'}, 'results': results}\n",
        )
    for name, value in {
        "CONFLUENCE_URL": "https://wiki.example.test",
        "CONFLUENCE_EMAIL": "user@example.test",
        "CONFLUENCE_API_TOKEN": "secret-value",
    }.items():
        monkeypatch.setenv(name, value)
    config = _config(tmp_path / "outputs", dry_run=True)
    script = Path(__file__).parents[1] / "tools" / "sync_k1_activity_index.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--dry-run",
            "--confluence-cli",
            str(fake_cli),
            "--wiki-work-dir",
            str(config.wiki_work_dir),
            "--state-path",
            str(config.state_path),
            "--review-report-path",
            str(config.review_report_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["dry_run"] is True
    assert not config.state_path.exists()


def test_cli_connection_failure_returns_redacted_json(tmp_path: Path, monkeypatch):
    fake_cli = tmp_path / "failing_confluence.py"
    fake_cli.write_text(
        """import os
import sys

print("connection failed for " + os.environ["CONFLUENCE_API_TOKEN"], file=sys.stderr)
raise SystemExit(1)
""",
        encoding="utf-8",
    )
    secret = "never-print-this-token"
    for name, value in {
        "CONFLUENCE_URL": "https://wiki.example.test",
        "CONFLUENCE_EMAIL": "user@example.test",
        "CONFLUENCE_API_TOKEN": secret,
    }.items():
        monkeypatch.setenv(name, value)
    config = _config(tmp_path / "outputs")
    script = Path(__file__).parents[1] / "tools" / "sync_k1_activity_index.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--confluence-cli",
            str(fake_cli),
            "--wiki-work-dir",
            str(config.wiki_work_dir),
            "--state-path",
            str(config.state_path),
            "--review-report-path",
            str(config.review_report_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert set(payload) == {"status", "error_code", "root_page_id", "paths"}
    assert secret not in result.stdout + result.stderr
    assert "Authorization:" not in result.stdout + result.stderr
    assert "Cookie:" not in result.stdout + result.stderr
