from pathlib import Path
import tempfile

import pytest

from tools.k1_activity_index.transaction import write_batch_atomic


def test_batch_replaces_every_target(tmp_path: Path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.json"
    first.write_text("old", encoding="utf-8")

    write_batch_atomic({first: "new", second: '{"ok": true}\n'})

    assert first.read_text(encoding="utf-8") == "new"
    assert second.read_text(encoding="utf-8") == '{"ok": true}\n'
    assert {path.name for path in tmp_path.iterdir()} == {"first.md", "second.json"}


def test_batch_rolls_back_after_replace_failure(tmp_path: Path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("old-first", encoding="utf-8")
    second.write_text("old-second", encoding="utf-8")
    calls = 0

    def failing_replace(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic replace failure")
        Path(source).replace(target)

    with pytest.raises(OSError, match="synthetic"):
        write_batch_atomic(
            {first: "new-first", second: "new-second"},
            replace=failing_replace,
        )

    assert first.read_text(encoding="utf-8") == "old-first"
    assert second.read_text(encoding="utf-8") == "old-second"
    assert {path.name for path in tmp_path.iterdir()} == {"first.md", "second.md"}


def test_batch_replaces_three_targets_in_caller_order_with_state_last(tmp_path: Path):
    topic = tmp_path / "topic.md"
    catalog = tmp_path / "catalog.md"
    state = tmp_path / "state.json"
    replace_targets = []

    def recording_replace(source, target):
        replace_targets.append(Path(target))
        Path(source).replace(target)

    write_batch_atomic(
        {topic: "new-topic", catalog: "new-catalog", state: "new-state"},
        replace=recording_replace,
    )

    assert replace_targets == [topic, catalog, state]
    assert topic.read_text(encoding="utf-8") == "new-topic"
    assert catalog.read_text(encoding="utf-8") == "new-catalog"
    assert state.read_text(encoding="utf-8") == "new-state"


def test_batch_preflights_every_target_before_replacing_any_target(tmp_path: Path):
    catalog = tmp_path / "catalog.md"
    blocked_parent = tmp_path / "not-a-directory"
    catalog.write_text("old-catalog", encoding="utf-8")
    blocked_parent.write_text("blocks staging", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_batch_atomic(
            {catalog: "new-catalog", blocked_parent / "state.json": "new-state"},
        )

    assert catalog.read_text(encoding="utf-8") == "old-catalog"


def test_batch_cleans_staging_files_when_backup_preflight_fails(tmp_path: Path, monkeypatch):
    catalog = tmp_path / "catalog.md"
    state = tmp_path / "state.json"
    state.write_text("old-state", encoding="utf-8")

    def fail_backup(source, target):
        raise OSError("synthetic backup failure")

    monkeypatch.setattr("tools.k1_activity_index.transaction.shutil.copyfile", fail_backup)

    with pytest.raises(OSError, match="synthetic backup failure"):
        write_batch_atomic({catalog: "new-catalog", state: "new-state"})

    assert not catalog.exists()
    assert state.read_text(encoding="utf-8") == "old-state"
    assert tuple(tmp_path.iterdir()) == (state,)


def test_batch_removes_new_target_when_a_later_replace_fails(tmp_path: Path):
    catalog = tmp_path / "catalog.md"
    state = tmp_path / "state.json"
    state.write_text("old-state", encoding="utf-8")
    calls = 0

    def failing_second_replace(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic state failure")
        Path(source).replace(target)

    with pytest.raises(OSError, match="synthetic state failure"):
        write_batch_atomic(
            {catalog: "new-catalog", state: "new-state"},
            replace=failing_second_replace,
        )

    assert not catalog.exists()
    assert state.read_text(encoding="utf-8") == "old-state"
    assert {path.name for path in tmp_path.iterdir()} == {"state.json"}


def test_batch_recovers_when_the_injected_replace_keeps_failing(tmp_path: Path):
    catalog = tmp_path / "catalog.md"
    state = tmp_path / "state.json"
    catalog.write_text("old-catalog", encoding="utf-8")
    state.write_text("old-state", encoding="utf-8")
    calls = 0

    def replace_once_then_fail(source, target):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise OSError("persistent synthetic replace failure")
        Path(source).replace(target)

    with pytest.raises(OSError, match="persistent synthetic replace failure"):
        write_batch_atomic(
            {catalog: "new-catalog", state: "new-state"},
            replace=replace_once_then_fail,
        )

    assert catalog.read_text(encoding="utf-8") == "old-catalog"
    assert state.read_text(encoding="utf-8") == "old-state"


def test_batch_rejects_a_symlink_target_before_staging_or_replacing(tmp_path: Path, monkeypatch):
    catalog = tmp_path / "catalog.md"
    symlink_target = tmp_path / "state.json"
    catalog.write_text("old-catalog", encoding="utf-8")
    real_is_symlink = Path.is_symlink
    real_mkstemp = tempfile.mkstemp
    staging_calls = []
    replace_targets = []

    def simulated_is_symlink(path):
        return path == symlink_target or real_is_symlink(path)

    def recording_mkstemp(*args, **kwargs):
        staging_calls.append(kwargs.get("dir"))
        return real_mkstemp(*args, **kwargs)

    def recording_replace(source, target):
        replace_targets.append(Path(target))
        Path(source).replace(target)

    monkeypatch.setattr(Path, "is_symlink", simulated_is_symlink)
    monkeypatch.setattr("tools.k1_activity_index.transaction.tempfile.mkstemp", recording_mkstemp)

    with pytest.raises(ValueError, match="symlink"):
        write_batch_atomic(
            {catalog: "new-catalog", symlink_target: "new-state"},
            replace=recording_replace,
        )

    assert staging_calls == []
    assert replace_targets == []
    assert catalog.read_text(encoding="utf-8") == "old-catalog"
    assert not symlink_target.exists()
    assert {path.name for path in tmp_path.iterdir()} == {"catalog.md"}
