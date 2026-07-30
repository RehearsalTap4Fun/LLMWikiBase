import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.k1_activity_index.path_safety import assert_safe_path
from tools.k1_activity_index.transaction import write_batch_atomic


def test_path_safety_rejects_mocked_windows_reparse_ancestor(tmp_path: Path, monkeypatch):
    junction = tmp_path / "junction"
    target = junction / "nested" / "state.json"
    real_lstat = os.lstat

    def fake_lstat(path):
        if Path(path) == junction:
            return SimpleNamespace(st_mode=0o040755, st_file_attributes=0x400)
        return real_lstat(path)

    monkeypatch.setattr(os, "lstat", fake_lstat)

    with pytest.raises(ValueError, match="reparse"):
        assert_safe_path(target)


def test_transaction_rejects_reparse_ancestor_before_creating_or_deleting(tmp_path: Path, monkeypatch):
    junction = tmp_path / "junction"
    target = junction / "catalog.md"
    stale = junction / "stale.md"
    real_lstat = os.lstat

    def fake_lstat(path):
        if Path(path) == junction:
            return SimpleNamespace(st_mode=0o040755, st_file_attributes=0x400)
        return real_lstat(path)

    monkeypatch.setattr(os, "lstat", fake_lstat)

    with pytest.raises(ValueError, match="reparse"):
        write_batch_atomic({target: "new"}, deletions=(stale,))

    assert not junction.exists()


def test_path_safety_rejects_real_symlink_ancestor_when_supported(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlinks unavailable: {error}")

    with pytest.raises(ValueError, match="reparse|symlink"):
        assert_safe_path(link / "state.json")
