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


def write_batch_atomic(outputs: dict[Path, str], replace: Replace = os.replace) -> None:
    """Install all rendered outputs, restoring earlier targets if installation fails.

    Every output is staged before any existing target is replaced.  The mapping's
    insertion order is deliberate: callers place the state file last so it is
    never advanced ahead of the corresponding Markdown files.
    """
    staged: list[_StagedOutput] = []
    active_error = False
    try:
        for target, text in outputs.items():
            staged_output = _stage_output(Path(target), text)
            staged.append(staged_output)

        _install_staged(staged, replace)
    except BaseException:
        active_error = True
        raise
    finally:
        _cleanup(staged, suppress_errors=active_error)


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


def _install_staged(staged: list[_StagedOutput], replace: Replace) -> None:
    replaced: list[_StagedOutput] = []
    try:
        for staged_output in staged:
            replace(staged_output.temporary, staged_output.target)
            replaced.append(staged_output)
    except BaseException as error:
        try:
            _rollback(replaced, replace)
        except BaseException as rollback_error:
            raise error from rollback_error
        raise


def _rollback(replaced: list[_StagedOutput], replace: Replace) -> None:
    rollback_error: BaseException | None = None
    for staged_output in reversed(replaced):
        try:
            if staged_output.backup is None:
                staged_output.target.unlink()
            else:
                _restore_backup(staged_output.backup, staged_output.target, replace)
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


def _cleanup(staged: list[_StagedOutput], *, suppress_errors: bool) -> None:
    cleanup_error: OSError | None = None
    for staged_output in staged:
        for path in (staged_output.temporary, staged_output.backup):
            if path is None:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError as error:
                if cleanup_error is None:
                    cleanup_error = error
    if cleanup_error is not None and not suppress_errors:
        raise cleanup_error
