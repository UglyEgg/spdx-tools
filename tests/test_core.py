# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for core SPDX header helpers."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from spdx_headers.core import (
    check_headers,
    create_header,
    has_spdx_header,
    remove_spdx_header,
)
from spdx_headers.data import load_license_data


def test_has_spdx_header_detects_present_header(tmp_path: Path) -> None:
    license_data = load_license_data()
    header = create_header(
        license_data,
        "MIT",
        year="2025",
        name="Test User",
        email="test@example.com",
    )
    assert header is not None
    assert "MIT License" in header
    source_path = tmp_path / "module.py"
    source_path.write_text(f"{header}print('hello world')\n", encoding="utf-8")

    assert has_spdx_header(str(source_path))


def test_remove_spdx_header_strips_header(tmp_path: Path) -> None:
    license_data = load_license_data()
    header = create_header(
        license_data,
        "GPL-3.0-only",
        year="2025",
        name="Test User",
        email="test@example.com",
    )
    assert header is not None
    source_path = tmp_path / "module.py"
    source_path.write_text(f"{header}print('clean')\n", encoding="utf-8")

    new_lines, had_header = remove_spdx_header(str(source_path))

    assert had_header is True
    assert "SPDX-License-Identifier" not in "".join(new_lines)


def test_check_headers_missing_directory(capsys: "pytest.CaptureFixture[str]") -> None:
    exit_code = check_headers("nonexistent-dir-for-test")

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "does not exist" in captured.out
