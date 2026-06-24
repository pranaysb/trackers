# ------------------------------------------------------------------------
# Trackers
# Copyright (c) 2026 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from trackers.utils.downloader import _extract_zip


def _create_in_memory_zip(files: dict[str, str]) -> io.BytesIO:
    """Helper to create a zip file in memory for testing."""
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    mem_zip.seek(0)
    return mem_zip


def test_extract_zip_normal(tmp_path: Path) -> None:
    """Test extracting a normal zip file with safe paths."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    zip_path = tmp_path / "test.zip"
    mem_zip = _create_in_memory_zip({"safe.txt": "content", "dir/safe2.txt": "content2"})
    zip_path.write_bytes(mem_zip.read())

    _extract_zip(zip_path, out_dir)

    assert (out_dir / "safe.txt").exists()
    assert (out_dir / "safe.txt").read_text() == "content"
    assert (out_dir / "dir" / "safe2.txt").exists()


def test_extract_zip_path_traversal(tmp_path: Path) -> None:
    """Test that path traversals (../) raise a ValueError."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    zip_path = tmp_path / "test_traversal.zip"
    mem_zip = _create_in_memory_zip({"../evil.txt": "content"})
    zip_path.write_bytes(mem_zip.read())

    with pytest.raises(ValueError, match="unsafe path"):
        _extract_zip(zip_path, out_dir)

    assert not (tmp_path / "evil.txt").exists()


def test_extract_zip_absolute_path(tmp_path: Path) -> None:
    """Test that absolute paths in zip raise a ValueError."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    zip_path = tmp_path / "test_absolute.zip"
    # An absolute path starts with / on posix, but on Windows it could be C:\\ etc.
    # We will test with /evil.txt.
    mem_zip = _create_in_memory_zip({"/evil.txt": "content"})
    zip_path.write_bytes(mem_zip.read())

    with pytest.raises(ValueError, match="unsafe path"):
        _extract_zip(zip_path, out_dir)
