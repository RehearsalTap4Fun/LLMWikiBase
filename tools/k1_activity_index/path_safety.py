"""Filesystem path safety checks for K1 activity-index inputs and outputs."""

import os
from pathlib import Path
import stat


_FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def assert_safe_path(path: str | Path) -> None:
    """Reject a symlink/junction/reparse point anywhere in an existing path prefix."""
    candidate = Path(os.path.abspath(os.fspath(path)))
    for component in _prefixes(candidate):
        try:
            metadata = os.lstat(component)
        except FileNotFoundError:
            continue
        attributes = getattr(metadata, "st_file_attributes", 0)
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"path contains a symlink: {component}")
        if attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"path contains a reparse point: {component}")


def absolute_unresolved(path: str | Path) -> Path:
    """Make a path absolute without resolving links or reparse points."""
    return Path(os.path.abspath(os.fspath(path)))


def assert_within(path: str | Path, root: str | Path) -> None:
    candidate = absolute_unresolved(path)
    boundary = absolute_unresolved(root)
    try:
        candidate.relative_to(boundary)
    except ValueError as error:
        raise ValueError(f"path is outside the configured root: {candidate}") from error


def _prefixes(path: Path) -> tuple[Path, ...]:
    prefixes: list[Path] = []
    current = path
    while True:
        prefixes.append(current)
        if current.parent == current:
            break
        current = current.parent
    return tuple(reversed(prefixes))
