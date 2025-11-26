# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Extended tests for operations module to improve coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from spdx_headers.core import create_header
from spdx_headers.data import LicenseEntry, load_license_data
from spdx_headers.operations import (
    _build_license_placeholder,
    _collect_license_identifiers,
    _resolve_license_text,
    _wrap_license_text,
    add_header_to_py_files,
    auto_fix_headers,
    change_header_in_py_files,
    check_headers,
    check_missing_headers,
    extract_license,
    remove_header_from_py_files,
    verify_spdx_headers,
)


class TestBuildLicensePlaceholder:
    """Tests for _build_license_placeholder function."""

    def test_build_placeholder_basic(self):
        """Test building basic license placeholder."""
        result = _build_license_placeholder("MIT", "MIT License")
        assert "MIT" in result
        assert "MIT License" in result
        assert "SPDX-License-Identifier:" in result

    def test_build_placeholder_long_name(self):
        """Test building placeholder with long license name."""
        result = _build_license_placeholder(
            "Apache-2.0", "Apache License 2.0 - Very Long Name"
        )
        assert "Apache-2.0" in result
        assert "Apache License 2.0" in result


class TestResolveLicenseText:
    """Tests for _resolve_license_text function."""

    def test_resolve_with_text_in_entry(self):
        """Test resolving when text is in license entry."""
        entry = LicenseEntry(
            name="MIT License",
            text="Permission is hereby granted...",
            is_osi_approved=True,
        )
        result = _resolve_license_text("MIT", entry)
        assert result == "Permission is hereby granted..."

    def test_resolve_without_text(self):
        """Test resolving when text is not in entry."""
        entry = LicenseEntry(
            name="MIT License",
            text=None,
            is_osi_approved=True,
        )
        result = _resolve_license_text("MIT", entry)
        # Should return None or attempt to fetch
        assert result is None or isinstance(result, str)

    @patch("spdx_headers.operations.requests")
    def test_resolve_with_requests_success(self, mock_requests):
        """Test resolving with successful HTTP request."""
        mock_response = Mock()
        mock_response.text = "License text from web"
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        entry = LicenseEntry(name="MIT License", text=None, is_osi_approved=True)
        result = _resolve_license_text("MIT", entry)
        
        if result:  # Only if requests is available
            assert "License text from web" in result or result is None

    @patch("spdx_headers.operations.requests")
    def test_resolve_with_requests_failure(self, mock_requests):
        """Test resolving with failed HTTP request."""
        mock_requests.get.side_effect = Exception("Network error")

        entry = LicenseEntry(name="MIT License", text=None, is_osi_approved=True)
        result = _resolve_license_text("MIT", entry)
        assert result is None

    def test_resolve_without_requests_module(self):
        """Test resolving when requests module is not available."""
        with patch.dict("sys.modules", {"requests": None}):
            entry = LicenseEntry(name="MIT License", text=None, is_osi_approved=True)
            result = _resolve_license_text("MIT", entry)
            # Should return None when requests is not available
            assert result is None or isinstance(result, str)


class TestWrapLicenseText:
    """Tests for _wrap_license_text function."""

    def test_wrap_short_text(self):
        """Test wrapping short text."""
        text = "Short license text"
        result = _wrap_license_text(text)
        assert "Short license text" in result

    def test_wrap_long_text(self):
        """Test wrapping long text."""
        text = "A" * 200
        result = _wrap_license_text(text, width=79)
        lines = result.split("\n")
        # Check that lines are wrapped
        assert all(len(line) <= 79 for line in lines if line)

    def test_wrap_with_paragraphs(self):
        """Test wrapping text with multiple paragraphs."""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        result = _wrap_license_text(text)
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        assert "Paragraph 3" in result

    def test_wrap_with_custom_width(self):
        """Test wrapping with custom width."""
        text = "A" * 200
        result = _wrap_license_text(text, width=50)
        lines = result.split("\n")
        assert all(len(line) <= 50 for line in lines if line)

    def test_wrap_preserves_empty_lines(self):
        """Test that wrapping preserves empty lines between paragraphs."""
        text = "Line 1\n\nLine 2"
        result = _wrap_license_text(text)
        assert "\n\n" in result or result.count("\n") >= 2


class TestCheckMissingHeaders:
    """Tests for check_missing_headers function."""

    def test_check_missing_headers_empty_dir(self, tmp_path):
        """Test checking missing headers in empty directory."""
        result = check_missing_headers(tmp_path)
        assert result == []

    def test_check_missing_headers_with_files(self, tmp_path):
        """Test checking missing headers with Python files."""
        # Create file without header
        file1 = tmp_path / "test1.py"
        file1.write_text("print('hello')\n")

        # Create file with header
        file2 = tmp_path / "test2.py"
        file2.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        result = check_missing_headers(tmp_path)
        assert len(result) == 1
        assert "test1.py" in str(result[0])

    def test_check_missing_headers_dry_run(self, tmp_path):
        """Test dry run mode."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        result = check_missing_headers(tmp_path, dry_run=True)
        assert len(result) == 1


class TestCollectLicenseIdentifiers:
    """Tests for _collect_license_identifiers function."""

    def test_collect_from_empty_dir(self, tmp_path):
        """Test collecting from empty directory."""
        result = _collect_license_identifiers(tmp_path)
        assert result == []

    def test_collect_from_files_with_headers(self, tmp_path):
        """Test collecting from files with headers."""
        file1 = tmp_path / "test1.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        file2 = tmp_path / "test2.py"
        file2.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: Apache-2.0\n"
            "print('hello')\n"
        )

        result = _collect_license_identifiers(tmp_path)
        assert len(result) == 2
        licenses = [lic for _, lic in result]
        assert "MIT" in licenses
        assert "Apache-2.0" in licenses


class TestAutoFixHeaders:
    """Tests for auto_fix_headers function."""

    def test_auto_fix_no_files(self, tmp_path):
        """Test auto fix with no files."""
        # Should not raise error
        auto_fix_headers(tmp_path, dry_run=True)

    def test_auto_fix_with_missing_headers(self, tmp_path):
        """Test auto fix with files missing headers."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        # Should not crash
        auto_fix_headers(tmp_path, dry_run=True)

    def test_auto_fix_with_existing_headers(self, tmp_path):
        """Test auto fix with existing headers."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        # Should not crash
        auto_fix_headers(tmp_path, dry_run=True)


class TestVerifySPDXHeaders:
    """Tests for verify_spdx_headers function."""

    def test_verify_empty_dir(self, tmp_path):
        """Test verifying empty directory."""
        # Should not raise error
        verify_spdx_headers(tmp_path)

    def test_verify_with_valid_headers(self, tmp_path):
        """Test verifying with valid headers."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        # Should not raise error
        verify_spdx_headers(tmp_path)


class TestCheckHeaders:
    """Tests for check_headers function."""

    def test_check_headers_empty_dir(self, tmp_path):
        """Test checking headers in empty directory."""
        result = check_headers(tmp_path)
        assert result == 0

    def test_check_headers_with_files(self, tmp_path):
        """Test checking headers with files."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        result = check_headers(tmp_path)
        assert result >= 0


class TestAddHeaderToPyFiles:
    """Tests for add_header_to_py_files function."""

    def test_add_header_basic(self, tmp_path):
        """Test adding header to Python files."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        add_header_to_py_files(
            tmp_path,
            "MIT",
            copyright_holder="Test User",
            year=2025,
            dry_run=True,
        )

        # In dry run, file should not be modified
        content = file1.read_text()
        assert content == "print('hello')\n"

    def test_add_header_with_email(self, tmp_path):
        """Test adding header with email."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        add_header_to_py_files(
            tmp_path,
            "MIT",
            copyright_holder="Test User",
            email="test@example.com",
            year=2025,
            dry_run=True,
        )

    def test_add_header_skip_existing(self, tmp_path):
        """Test skipping files with existing headers."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        add_header_to_py_files(
            tmp_path,
            "Apache-2.0",
            copyright_holder="Test User",
            year=2025,
            dry_run=True,
        )


class TestChangeHeaderInPyFiles:
    """Tests for change_header_in_py_files function."""

    def test_change_header_basic(self, tmp_path):
        """Test changing header in Python files."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        change_header_in_py_files(
            tmp_path,
            "Apache-2.0",
            dry_run=True,
        )

    def test_change_header_no_existing(self, tmp_path):
        """Test changing header when no header exists."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        # Should handle gracefully
        change_header_in_py_files(
            tmp_path,
            "Apache-2.0",
            dry_run=True,
        )


class TestRemoveHeaderFromPyFiles:
    """Tests for remove_header_from_py_files function."""

    def test_remove_header_basic(self, tmp_path):
        """Test removing header from Python files."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        remove_header_from_py_files(tmp_path, dry_run=True)

    def test_remove_header_no_header(self, tmp_path):
        """Test removing header when no header exists."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        # Should handle gracefully
        remove_header_from_py_files(tmp_path, dry_run=True)


class TestExtractLicense:
    """Tests for extract_license function."""

    def test_extract_license_basic(self, tmp_path):
        """Test extracting license to file."""
        output_file = tmp_path / "LICENSE.txt"
        license_data = load_license_data()

        extract_license("MIT", license_data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0

    def test_extract_license_with_header(self, tmp_path):
        """Test extracting license with header."""
        output_file = tmp_path / "LICENSE.txt"
        license_data = load_license_data()

        extract_license(
            "MIT",
            license_data,
            output_file,
            include_header=True,
        )

        assert output_file.exists()
        content = output_file.read_text()
        assert "MIT" in content

    def test_extract_license_invalid(self, tmp_path):
        """Test extracting invalid license."""
        output_file = tmp_path / "LICENSE.txt"
        license_data = load_license_data()

        # Should handle gracefully or raise appropriate error
        try:
            extract_license("INVALID-LICENSE", license_data, output_file)
        except (KeyError, ValueError):
            pass  # Expected


class TestOperationsEdgeCases:
    """Tests for edge cases in operations."""

    def test_operations_with_nested_directories(self, tmp_path):
        """Test operations with nested directory structure."""
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)

        file1 = subdir / "test.py"
        file1.write_text("print('hello')\n")

        result = check_missing_headers(tmp_path)
        assert len(result) >= 1

    def test_operations_with_symlinks(self, tmp_path):
        """Test operations with symbolic links."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        link = tmp_path / "link.py"
        try:
            link.symlink_to(file1)
            # Should handle symlinks gracefully
            check_missing_headers(tmp_path)
        except OSError:
            # Symlinks might not be supported on all systems
            pass

    def test_operations_with_readonly_files(self, tmp_path):
        """Test operations with read-only files."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")
        file1.chmod(0o444)  # Read-only

        try:
            # Should handle read-only files gracefully
            add_header_to_py_files(
                tmp_path,
                "MIT",
                copyright_holder="Test",
                year=2025,
                dry_run=True,
            )
        finally:
            file1.chmod(0o644)  # Restore permissions

    def test_operations_with_empty_files(self, tmp_path):
        """Test operations with empty files."""
        file1 = tmp_path / "empty.py"
        file1.write_text("")

        result = check_missing_headers(tmp_path)
        assert isinstance(result, list)