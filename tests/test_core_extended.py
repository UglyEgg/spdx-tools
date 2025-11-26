# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Extended tests for core module to improve coverage.
"""

from pathlib import Path

import pytest

from spdx_headers.core import (
    create_header,
    extract_spdx_header,
    has_spdx_header,
    remove_spdx_header,
    _extract_spdx_header_from_lines,
    find_python_files,
    find_src_directory,
    get_copyright_info,
)
from spdx_headers.data import load_license_data


@pytest.fixture
def license_data():
    """Load license data for tests."""
    return load_license_data()


class TestCreateHeader:
    """Tests for create_header function."""

    def test_create_header_basic(self, license_data):
        """Test creating basic header."""
        header = create_header(
            "MIT",
            license_data,
            copyright_holder="Test User",
            year=2025,
        )
        assert "SPDX-FileCopyrightText:" in header
        assert "SPDX-License-Identifier:" in header
        assert "MIT" in header
        assert "Test User" in header
        assert "2025" in header

    def test_create_header_with_email(self, license_data):
        """Test creating header with email."""
        header = create_header(
            "MIT",
            license_data,
            copyright_holder="Test User",
            email="test@example.com",
            year=2025,
        )
        assert "test@example.com" in header

    def test_create_header_without_email(self, license_data):
        """Test creating header without email."""
        header = create_header(
            "MIT",
            license_data,
            copyright_holder="Test User",
            year=2025,
        )
        assert "Test User" in header

    def test_create_header_different_licenses(self, license_data):
        """Test creating headers for different licenses."""
        licenses = ["MIT", "Apache-2.0", "GPL-3.0-or-later"]
        for license_id in licenses:
            if license_id in license_data["licenses"]:
                header = create_header(
                    license_id,
                    license_data,
                    copyright_holder="Test User",
                    year=2025,
                )
                assert license_id in header

    def test_create_header_invalid_license(self, license_data):
        """Test creating header with invalid license."""
        with pytest.raises(KeyError):
            create_header(
                "INVALID-LICENSE",
                license_data,
                copyright_holder="Test User",
                year=2025,
            )


class TestHasSPDXHeader:
    """Tests for has_spdx_header function."""

    def test_has_header_true(self, tmp_path):
        """Test detecting existing header."""
        file = tmp_path / "test.py"
        file.write_text(
            "# SPDX-FileCopyrightText: 2025 Test User\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        assert has_spdx_header(file) is True

    def test_has_header_false(self, tmp_path):
        """Test detecting missing header."""
        file = tmp_path / "test.py"
        file.write_text(
            "print('hello')\n"
            "print('world')\n"
        )
        assert has_spdx_header(file) is False

    def test_has_header_empty_file(self, tmp_path):
        """Test detecting header in empty file."""
        file = tmp_path / "test.py"
        file.write_text("")
        assert has_spdx_header(file) is False


class TestExtractSPDXHeader:
    """Tests for extract_spdx_header function."""

    def test_extract_header_basic(self, tmp_path):
        """Test extracting basic header."""
        file = tmp_path / "test.py"
        file.write_text(
            "# SPDX-FileCopyrightText: 2025 Test User\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        header = extract_spdx_header(file)
        assert any("SPDX-FileCopyrightText:" in line for line in header)
        assert any("SPDX-License-Identifier:" in line for line in header)

    def test_extract_header_no_header(self, tmp_path):
        """Test extracting from file without header."""
        file = tmp_path / "test.py"
        file.write_text(
            "print('hello')\n"
            "print('world')\n"
        )
        header = extract_spdx_header(file)
        assert header == []


class TestRemoveSPDXHeader:
    """Tests for remove_spdx_header function."""

    def test_remove_header_basic(self, tmp_path):
        """Test removing basic header."""
        file = tmp_path / "test.py"
        file.write_text(
            "# SPDX-FileCopyrightText: 2025 Test User\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        lines, had_header = remove_spdx_header(file)
        assert had_header is True
        content = "".join(lines)
        assert "SPDX-FileCopyrightText:" not in content
        assert "print('hello')" in content

    def test_remove_header_no_header(self, tmp_path):
        """Test removing header when none exists."""
        file = tmp_path / "test.py"
        file.write_text(
            "print('hello')\n"
            "print('world')\n"
        )
        lines, had_header = remove_spdx_header(file)
        assert had_header is False


class TestFindPythonFiles:
    """Tests for find_python_files function."""

    def test_find_python_files_basic(self, tmp_path):
        """Test finding Python files."""
        (tmp_path / "test1.py").write_text("print('hello')\n")
        (tmp_path / "test2.py").write_text("print('world')\n")
        (tmp_path / "readme.txt").write_text("Not a Python file\n")

        files = find_python_files(tmp_path)
        assert len(files) == 2
        assert any("test1.py" in f for f in files)
        assert any("test2.py" in f for f in files)

    def test_find_python_files_nested(self, tmp_path):
        """Test finding Python files in nested directories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "test1.py").write_text("print('hello')\n")
        (subdir / "test2.py").write_text("print('world')\n")

        files = find_python_files(tmp_path)
        assert len(files) == 2

    def test_find_python_files_empty_dir(self, tmp_path):
        """Test finding Python files in empty directory."""
        files = find_python_files(tmp_path)
        assert files == []


class TestFindSrcDirectory:
    """Tests for find_src_directory function."""

    def test_find_src_directory_exists(self, tmp_path):
        """Test finding src directory when it exists."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text("print('hello')\n")

        result = find_src_directory(tmp_path)
        assert "src" in result

    def test_find_src_directory_not_exists(self, tmp_path):
        """Test finding src directory when it doesn't exist."""
        result = find_src_directory(tmp_path)
        assert result == str(tmp_path)


class TestGetCopyrightInfo:
    """Tests for get_copyright_info function."""

    def test_get_copyright_info_basic(self, tmp_path):
        """Test getting copyright info."""
        year, name, email = get_copyright_info(tmp_path)
        assert isinstance(year, str)
        assert isinstance(name, str)
        assert isinstance(email, str)
        assert len(year) == 4  # Year should be 4 digits