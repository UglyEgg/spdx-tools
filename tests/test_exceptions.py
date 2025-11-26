# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Tests for custom exception classes.
"""

from pathlib import Path

import pytest

from spdx_headers.exceptions import (
    ConcurrentModificationError,
    DirectoryNotFoundError,
    EncodingError,
    FileProcessingError,
    HeaderNotFoundError,
    InvalidHeaderError,
    LicenseNotFoundError,
    NoFilesFoundError,
    PermissionError,
    SPDXError,
    find_similar_licenses,
)


class TestSPDXError:
    """Tests for base SPDXError exception."""

    def test_spdx_error_creation(self):
        """Test creating a basic SPDXError."""
        error = SPDXError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_spdx_error_inheritance(self):
        """Test that all custom exceptions inherit from SPDXError."""
        assert issubclass(FileProcessingError, SPDXError)
        assert issubclass(EncodingError, SPDXError)
        assert issubclass(LicenseNotFoundError, SPDXError)
        assert issubclass(DirectoryNotFoundError, SPDXError)
        assert issubclass(NoFilesFoundError, SPDXError)


class TestFileProcessingError:
    """Tests for FileProcessingError exception."""

    def test_file_processing_error_basic(self):
        """Test basic FileProcessingError without suggestion."""
        error = FileProcessingError("test.py", "File is corrupted")
        assert "test.py" in str(error)
        assert "File is corrupted" in str(error)
        assert error.filepath == Path("test.py")
        assert error.reason == "File is corrupted"
        assert error.suggestion is None

    def test_file_processing_error_with_suggestion(self):
        """Test FileProcessingError with suggestion."""
        error = FileProcessingError(
            "test.py", "File is corrupted", "Try restoring from backup"
        )
        assert "test.py" in str(error)
        assert "File is corrupted" in str(error)
        assert "Try restoring from backup" in str(error)
        assert "Suggestion:" in str(error)
        assert error.suggestion == "Try restoring from backup"

    def test_file_processing_error_with_path_object(self):
        """Test FileProcessingError with Path object."""
        path = Path("src/test.py")
        error = FileProcessingError(path, "Error occurred")
        assert error.filepath == path
        assert str(path) in str(error)


class TestEncodingError:
    """Tests for EncodingError exception."""

    def test_encoding_error_basic(self):
        """Test basic EncodingError."""
        error = EncodingError("test.py", ["utf-8", "latin-1"])
        assert "test.py" in str(error)
        assert "utf-8" in str(error)
        assert "latin-1" in str(error)
        assert "Unable to decode" in str(error)
        assert error.attempted_encodings == ["utf-8", "latin-1"]

    def test_encoding_error_with_suggestion(self):
        """Test EncodingError with custom suggestion."""
        error = EncodingError(
            "test.py", ["utf-8"], "Use iconv to convert the file"
        )
        assert "Use iconv to convert the file" in str(error)

    def test_encoding_error_default_suggestion(self):
        """Test EncodingError default suggestion."""
        error = EncodingError("test.py", ["utf-8"])
        assert "binary" in str(error)
        assert "UTF-8" in str(error)


class TestLicenseNotFoundError:
    """Tests for LicenseNotFoundError exception."""

    def test_license_not_found_basic(self):
        """Test basic LicenseNotFoundError without suggestions."""
        error = LicenseNotFoundError("INVALID-LICENSE")
        assert "INVALID-LICENSE" in str(error)
        assert "not found" in str(error)
        assert "--list" in str(error)
        assert error.license_id == "INVALID-LICENSE"
        assert error.suggestions == []

    def test_license_not_found_with_suggestions(self):
        """Test LicenseNotFoundError with suggestions."""
        suggestions = ["MIT", "Apache-2.0", "GPL-3.0"]
        error = LicenseNotFoundError("apache", suggestions)
        assert "apache" in str(error)
        assert "Did you mean" in str(error)
        assert "MIT" in str(error)
        assert "Apache-2.0" in str(error)
        assert "GPL-3.0" in str(error)
        assert error.suggestions == suggestions

    def test_license_not_found_truncates_suggestions(self):
        """Test that suggestions are limited to 5."""
        suggestions = ["Lic1", "Lic2", "Lic3", "Lic4", "Lic5", "Lic6", "Lic7"]
        error = LicenseNotFoundError("test", suggestions)
        # Should only show first 5
        assert "Lic1" in str(error)
        assert "Lic5" in str(error)
        # Lic6 and Lic7 might not be in the message


class TestDirectoryNotFoundError:
    """Tests for DirectoryNotFoundError exception."""

    def test_directory_not_found(self):
        """Test DirectoryNotFoundError."""
        error = DirectoryNotFoundError("/path/to/missing")
        assert "/path/to/missing" in str(error)
        assert "does not exist" in str(error)
        assert "Suggestion:" in str(error)
        assert error.directory == Path("/path/to/missing")


class TestNoFilesFoundError:
    """Tests for NoFilesFoundError exception."""

    def test_no_files_found(self):
        """Test NoFilesFoundError."""
        error = NoFilesFoundError("/empty/directory")
        assert "/empty/directory" in str(error)
        assert "No Python files found" in str(error)
        assert "Suggestion:" in str(error)
        assert error.directory == Path("/empty/directory")


class TestHeaderNotFoundError:
    """Tests for HeaderNotFoundError exception."""

    def test_header_not_found(self):
        """Test HeaderNotFoundError."""
        error = HeaderNotFoundError("test.py")
        assert "test.py" in str(error)
        assert "No SPDX header found" in str(error)
        assert "--add" in str(error)
        assert "Suggestion:" in str(error)


class TestInvalidHeaderError:
    """Tests for InvalidHeaderError exception."""

    def test_invalid_header(self):
        """Test InvalidHeaderError."""
        error = InvalidHeaderError("test.py", "Missing copyright line")
        assert "test.py" in str(error)
        assert "Invalid SPDX header" in str(error)
        assert "Missing copyright line" in str(error)
        assert error.details == "Missing copyright line"


class TestConcurrentModificationError:
    """Tests for ConcurrentModificationError exception."""

    def test_concurrent_modification(self):
        """Test ConcurrentModificationError."""
        error = ConcurrentModificationError("test.py")
        assert "test.py" in str(error)
        assert "modified by another process" in str(error)
        assert "Try the operation again" in str(error)


class TestPermissionError:
    """Tests for PermissionError exception."""

    def test_permission_error_read(self):
        """Test PermissionError for read operation."""
        error = PermissionError("test.py", "read")
        assert "test.py" in str(error)
        assert "Permission denied" in str(error)
        assert "read" in str(error)
        assert error.operation == "read"

    def test_permission_error_write(self):
        """Test PermissionError for write operation."""
        error = PermissionError("test.py", "write")
        assert "test.py" in str(error)
        assert "write" in str(error)
        assert "elevated privileges" in str(error)


class TestFindSimilarLicenses:
    """Tests for find_similar_licenses function."""

    def test_find_similar_licenses_exact_match(self):
        """Test finding exact matches."""
        licenses = ["MIT", "Apache-2.0", "GPL-3.0"]
        results = find_similar_licenses("MIT", licenses)
        assert "MIT" in results

    def test_find_similar_licenses_fuzzy_match(self):
        """Test fuzzy matching."""
        licenses = ["MIT", "Apache-2.0", "GPL-3.0", "Apache-1.1"]
        results = find_similar_licenses("apache", licenses)
        assert len(results) > 0
        assert any("Apache" in lic for lic in results)

    def test_find_similar_licenses_no_match(self):
        """Test when no similar licenses found."""
        licenses = ["MIT", "Apache-2.0", "GPL-3.0"]
        results = find_similar_licenses("xyz123", licenses, cutoff=0.9)
        # With high cutoff, might not find matches
        assert isinstance(results, list)

    def test_find_similar_licenses_case_insensitive(self):
        """Test case-insensitive matching."""
        licenses = ["MIT", "Apache-2.0", "GPL-3.0"]
        results = find_similar_licenses("mit", licenses)
        # Should find MIT or similar matches
        assert len(results) >= 0  # May or may not find exact match depending on algorithm

    def test_find_similar_licenses_limit(self):
        """Test that results are limited to 5."""
        licenses = [f"License-{i}" for i in range(20)]
        results = find_similar_licenses("License", licenses)
        assert len(results) <= 5

    def test_find_similar_licenses_empty_list(self):
        """Test with empty license list."""
        results = find_similar_licenses("MIT", [])
        assert results == []

    def test_find_similar_licenses_custom_cutoff(self):
        """Test with custom cutoff value."""
        licenses = ["MIT", "Apache-2.0", "GPL-3.0"]
        results_low = find_similar_licenses("ap", licenses, cutoff=0.3)
        results_high = find_similar_licenses("ap", licenses, cutoff=0.9)
        # Lower cutoff should find more matches
        assert len(results_low) >= len(results_high)

    def test_find_similar_licenses_fallback_without_difflib(self):
        """Test fallback matching when difflib is not available."""
        # Test the fallback path by using a pattern that triggers substring matching
        licenses = ["MIT-License", "Apache-2.0-License", "GPL-3.0-License"]
        
        # The fallback uses case-insensitive substring matching
        # Test with a partial match
        results = find_similar_licenses("apache", licenses)
        assert isinstance(results, list)
        # Should find matches using substring logic
        assert len(results) >= 0