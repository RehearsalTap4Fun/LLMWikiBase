"""Transactional file replacement for generated K1 activity-index outputs."""

import os
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
from typing import Callable


Replace = Callable[[Path, Path], None]


@dataclass
class _StagedOutput:
    target: Path
    temporary: Path
    backup: Path | None = None


@dataclass
class _StagedDeletion:
    target: Path
    backup: Path | None = None


def write_batch_atomic(
    outputs: dict[Path, str],
    replace: Replace = os.replace,
    *,
    deletions: tuple[Path, ...] = (),
) -> None:
    """Install all rendered outputs, restoring earlier targets if installation fails.

    Every replacement and deletion is staged before any target changes. The
    mapping's insertion order is deliberate: deletions are installed immediately
    before its final state output, so state is never advanced ahead of the
    corresponding Markdown files.
    """
    deletion_paths = tuple(Path(path) for path in deletions)
    _reject_conflicting_targets(outputs, deletion_paths)
    _reject_symlink_targets((*outputs, *deletion_paths))
    staged_outputs: list[_StagedOutput] = []
    staged_deletions: list[_StagedDeletion] = []
    active_error = False
    try:
        for target, text in outputs.items():
            staged_output = _stage_output(Path(target), text)
            staged_outputs.append(staged_output)
        for target in deletion_paths:
            staged_deletions.append(_stage_deletion(target))

        _install_staged(staged_outputs, staged_deletions, replace)
    except BaseException:
        active_error = True
        raise
    finally:
        _cleanup(staged_outputs, staged_deletions, suppress_errors=active_error)


def _reject_conflicting_targets(
    outputs: dict[Path, str], deletions: tuple[Path, ...]
) -> None:
    targets = (*outputs, *deletions)
    normalized = [Path(target).resolve(strict=False) for target in targets]
    if len(normalized) != len(set(normalized)):
        raise ValueError("duplicate replacement/deletion target")


def _reject_symlink_targets(targets) -> None:
    for target in targets:
        target_path = Path(target)
        if target_path.is_symlink():
            raise ValueError(f"output target is a symlink: {target_path}")


def _stage_output(target: Path, text: str) -> _StagedOutput:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _write_temporary(target.parent, target.name, text)
    staged = _StagedOutput(target=target, temporary=temporary)
    try:
        if target.exists():
            staged.backup = _copy_backup(target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return staged


def _stage_deletion(target: Path) -> _StagedDeletion:
    staged = _StagedDeletion(target=target)
    if not target.exists():
        return staged
    if not target.is_file():
        raise ValueError(f"deletion target is not a file: {target}")
    staged.backup = _copy_backup(target)
    return staged


def _write_temporary(parent: Path, name: str, text: str) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{name}.", suffix=".k1-activity-tmp", dir=parent, text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _copy_backup(target: Path) -> Path:
    descriptor, backup_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".k1-activity-backup", dir=target.parent
    )
    os.close(descriptor)
    backup = Path(backup_name)
    try:
        shutil.copyfile(target, backup)
    except BaseException:
        backup.unlink(missing_ok=True)
        raise
    return backup


def _install_staged(
    outputs: list[_StagedOutput],
    deletions: list[_StagedDeletion],
    replace: Replace,
) -> None:
    operations: list[_StagedOutput | _StagedDeletion] = [
        *outputs[:-1],
        *deletions,
        *outputs[-1:],
    ]
    applied: list[_StagedOutput | _StagedDeletion] = []
    try:
        for operation in operations:
            if isinstance(operation, _StagedOutput):
                replace(operation.temporary, operation.target)
            elif operation.backup is not None:
                operation.target.unlink()
            applied.append(operation)
    except BaseException as error:
        try:
            _rollback(applied, replace)
        except BaseException as rollback_error:
            raise error from rollback_error
        raise


def _rollback(
    applied: list[_StagedOutput | _StagedDeletion], replace: Replace
) -> None:
    rollback_error: BaseException | None = None
    for operation in reversed(applied):
        try:
            if isinstance(operation, _StagedDeletion):
                if operation.backup is not None:
                    _restore_backup(operation.backup, operation.target, replace)
            elif operation.backup is None:
                operation.target.unlink()
            else:
                _restore_backup(operation.backup, operation.target, replace)
        except BaseException as error:
            if rollback_error is None:
                rollback_error = error
    if rollback_error is not None:
        raise rollback_error


def _restore_backup(backup: Path, target: Path, replace: Replace) -> None:
    try:
        replace(backup, target)
    except OSError:
        os.replace(backup, target)


def _cleanup(
    outputs: list[_StagedOutput],
    deletions: list[_StagedDeletion],
    *,
    suppress_errors: bool,
) -> None:
    cleanup_error: OSError | None = None
    for staged_output in outputs:
        for path in (staged_output.temporary, staged_output.backup):
            if path is None:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError as error:
                if cleanup_error is None:
                    cleanup_error = error
    for staged_deletion in deletions:
        if staged_deletion.backup is None:
            continue
        try:
            staged_deletion.backup.unlink(missing_ok=True)
        except OSError as error:
            if cleanup_error is None:
                cleanup_error = error
    if cleanup_error is not None and not suppress_errors:
        raise cleanup_error
