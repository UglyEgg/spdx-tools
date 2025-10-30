# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for higher-level operations helpers."""

from pathlib import Path

from spdx_headers.core import create_header
from spdx_headers.data import load_license_data
from spdx_headers.operations import auto_fix_headers, filter_licenses, show_license


def test_show_license_uses_temp_file() -> None:
    license_data = load_license_data()
    opened_paths: list[Path] = []

    def fake_opener(path: Path) -> None:
        opened_paths.append(path)

    show_license("MIT", license_data, open_in_editor=fake_opener)

    assert opened_paths, "Expected the show command to invoke the editor callback"
    temp_path = opened_paths[0]
    assert not temp_path.exists()


def test_filter_licenses_with_keyword() -> None:
    license_data = load_license_data()
    matches = filter_licenses(license_data, "apache")
    assert matches
    keys = [key for key, _ in matches]
    assert "Apache-2.0" in keys


def test_filter_licenses_no_matches() -> None:
    license_data = load_license_data()
    matches = filter_licenses(license_data, "nonexistent")
    assert matches == []


def test_auto_fix_headers_adds_missing(tmp_path: Path) -> None:
    license_data = load_license_data()
    header = create_header(
        license_data,
        "MIT",
        year="2025",
        name="Test User",
        email="test@example.com",
    )
    assert header is not None

    src_dir = tmp_path / "pkg"
    src_dir.mkdir()

    existing_file = src_dir / "existing.py"
    existing_file.write_text(f"{header}print('existing')\n", encoding="utf-8")

    missing_file = src_dir / "missing.py"
    missing_file.write_text("print('missing')\n", encoding="utf-8")

    success = auto_fix_headers(
        src_dir,
        license_data,
        year="2025",
        name="Test User",
        email="test@example.com",
    )

    assert success is True
    content = missing_file.read_text(encoding="utf-8")
    assert "SPDX-License-Identifier: MIT" in content


def test_auto_fix_headers_multiple_licenses(tmp_path: Path) -> None:
    license_data = load_license_data()

    header_mit = create_header(
        license_data,
        "MIT",
        year="2025",
        name="Test User",
        email="test@example.com",
    )
    header_gpl = create_header(
        license_data,
        "GPL-3.0-only",
        year="2025",
        name="Test User",
        email="test@example.com",
    )
    assert header_mit and header_gpl

    src_dir = tmp_path / "pkg"
    src_dir.mkdir()

    (src_dir / "file1.py").write_text(f"{header_mit}print('one')\n", encoding="utf-8")
    (src_dir / "file2.py").write_text(f"{header_gpl}print('two')\n", encoding="utf-8")
    missing_file = src_dir / "missing.py"
    missing_file.write_text("print('missing')\n", encoding="utf-8")

    success = auto_fix_headers(
        src_dir,
        license_data,
        year="2025",
        name="Test User",
        email="test@example.com",
    )

    assert success is False
    content = missing_file.read_text(encoding="utf-8")
    assert "SPDX-License-Identifier" not in content
