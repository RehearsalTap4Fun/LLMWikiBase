import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest

from tools.k1_activity_index.crawl import IncompleteTreeError
from tools.k1_activity_index.models import ConfluenceCommandError, PageUnavailableError
from tools.k1_activity_index.service import SyncConfig, sync_index
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
    report_data = json.loads(config.review_report_path.read_text(encoding="utf-8"))
    assert report_data["review_needed"] == ["100", "101"]


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
    assert str(config.state_path) in failure_data["message"]


def test_cli_dry_run_uses_fake_confluence_without_fetching_or_writing(
    tmp_path: Path, monkeypatch
):
    fake_cli = tmp_path / "fake_confluence.py"
    fake_cli.write_text(
        """import json
import sys

arguments = sys.argv[1:]
if arguments == ["check"]:
    payload = {}
elif arguments[:3] == ["page", "children", "73598402"]:
    payload = {
        "total": 1,
        "results": [{
            "id": "100", "title": "K1 Topic", "status": "current",
            "space": "KEFU", "version": 1,
            "url": "https://wiki.example.test/pages/viewpage.action?pageId=100"
        }],
    }
elif arguments[:3] == ["page", "children", "100"]:
    payload = {"total": 0, "results": []}
else:
    raise SystemExit("unexpected body fetch")
print(json.dumps(payload))
""",
        encoding="utf-8",
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
    assert json.loads(result.stdout)["status"] == "error"
    assert secret not in result.stdout
