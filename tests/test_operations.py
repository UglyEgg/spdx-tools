# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for higher-level operations helpers."""

import time
from pathlib import Path
from typing import Optional

import pytest

from spdx_headers.core import create_header
from spdx_headers.data import LicenseData, LicenseEntry, load_license_data
from spdx_headers.operations import (
    auto_fix_headers,
    check_headers,
    extract_license,
    filter_licenses,
    show_license,
)


def test_show_license_uses_temp_file() -> None:
    license_data = load_license_data()
    opened_paths: list[Path] = []

    def fake_opener(path: Path) -> None:
        opened_paths.append(path)

    show_license(
        "MIT",
        license_data,
        open_in_editor=fake_opener,
        cleanup_delay=0.01,
    )

    assert opened_paths, "Expected the show command to invoke the editor callback"
    temp_path = opened_paths[0]
    time.sleep(0.05)
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


def test_check_headers_reports_detected_license(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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
    (src_dir / "module.py").write_text(f"{header}print('ok')\n", encoding="utf-8")

    exit_code = check_headers(src_dir)

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Detected SPDX license identifier: MIT" in captured.out


def test_check_headers_lists_files_when_multiple_identifiers(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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
    (src_dir / "alpha.py").write_text(f"{header_mit}print('a')\n", encoding="utf-8")
    (src_dir / "beta.py").write_text(f"{header_gpl}print('b')\n", encoding="utf-8")
    (src_dir / "missing.py").write_text("print('missing')\n", encoding="utf-8")

    exit_code = check_headers(src_dir)

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Detected SPDX license identifiers:" in captured.out
    assert f"{src_dir / 'alpha.py'} - MIT" in captured.out
    assert f"{src_dir / 'beta.py'} - GPL-3.0-only" in captured.out


def _make_license_data_with_text(license_text: str) -> LicenseData:
    license_entry: LicenseEntry = {
        "name": "MIT License",
        "deprecated": False,
        "osi_approved": True,
        "fsf_libre": True,
        "header_template": "#\n#\n# {license_name}\n",
        "license_text": license_text,
    }
    license_data: LicenseData = {
        "metadata": {
            "spdx_version": "test",
            "generated_at": "now",
            "license_count": 1,
        },
        "licenses": {
            "MIT": license_entry,
        },
    }
    return license_data


def test_extract_license_writes_full_text(tmp_path: Path) -> None:
    repo_path = tmp_path
    license_data = _make_license_data_with_text("MIT LICENSE TEXT\n")

    extract_license("MIT", license_data, repo_path)

    license_file = repo_path / "LICENSE"
    assert license_file.exists()
    assert license_file.read_text(encoding="utf-8") == "MIT LICENSE TEXT\n"


def test_extract_license_avoids_overwriting_existing_license(tmp_path: Path) -> None:
    repo_path = tmp_path
    license_data = _make_license_data_with_text("MIT LICENSE TEXT\n")

    existing = repo_path / "LICENSE"
    existing.write_text("existing content\n", encoding="utf-8")

    extract_license("MIT", license_data, repo_path, dry_run=False)

    assert existing.read_text(encoding="utf-8") == "existing content\n"
    suffixed = repo_path / "LICENSE-MIT"
    assert suffixed.exists()
    assert suffixed.read_text(encoding="utf-8") == "MIT LICENSE TEXT\n"


def test_extract_license_falls_back_to_placeholder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_path = tmp_path
    license_data = _make_license_data_with_text("unused\n")

    def fake_resolve(_license_key: str, _license_entry: object) -> Optional[str]:
        return None

    monkeypatch.setattr(
        "spdx_headers.operations._resolve_license_text",
        fake_resolve,
    )

    extract_license("MIT", license_data, repo_path, dry_run=False)

    license_file = repo_path / "LICENSE"
    content = license_file.read_text(encoding="utf-8")
    assert "https://spdx.org/licenses/MIT.html" in content


def test_extract_license_wraps_long_lines(tmp_path: Path) -> None:
    repo_path = tmp_path
    long_paragraph = (
        "This is an intentionally long sentence designed to exceed seventy-nine characters "
        "once it is written to disk, ensuring the wrapping logic inserts hard newlines at "
        "appropriate boundaries without disrupting the paragraph spacing that already exists."
    )
    license_text = f"{long_paragraph}\n\nSecond paragraph stays separated."
    license_data = _make_license_data_with_text(f"{license_text}\n")

    extract_license("MIT", license_data, repo_path, dry_run=False)

    content = (repo_path / "LICENSE").read_text(encoding="utf-8")
    lines = content.splitlines()
    assert "" in lines, "Expected blank line preserved between paragraphs"
    assert all(len(line) <= 79 for line in lines if line), "Expected wrapped lines"


def test_extract_license_preserves_indented_blocks(tmp_path: Path) -> None:
    repo_path = tmp_path
    license_text = (
        "First paragraph that should be wrapped because it is quite verbose and needs "
        "to demonstrate the behaviour of the wrapping function while remaining readable.\n"
        "\n"
        "    THIS IS AN INDENTED BLOCK THAT SHOULD BE PRESERVED EXACTLY AS WRITTEN\n"
        "    EVEN IF IT IS LONGER THAN SEVENTY-NINE CHARACTERS BECAUSE IT IS PRE-FORMATTED.\n"
    )
    license_data = _make_license_data_with_text(license_text)

    extract_license("MIT", license_data, repo_path, dry_run=False)

    content = (repo_path / "LICENSE").read_text(encoding="utf-8")
    lines = content.splitlines()
    indented_lines = [line for line in lines if line.startswith("    ")]
    assert indented_lines, "Expected indented block to remain indented"
    assert all(len(line) <= 79 for line in indented_lines if line.strip())
