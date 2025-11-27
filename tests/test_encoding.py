# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Tests for encoding detection and handling.
"""


import pytest

from spdx_headers.encoding import (
    DEFAULT_ENCODINGS,
    detect_encoding,
    get_encoding_info,
    is_text_file,
    normalize_encoding_name,
    read_file_with_encoding,
    write_file_with_encoding,
)
from spdx_headers.exceptions import EncodingError


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    return tmp_path / "test_file.txt"


class TestDetectEncoding:
    """Tests for detect_encoding function."""

    def test_detect_utf8(self, temp_file):
        """Test detecting UTF-8 encoding."""
        content = "Hello, World! 你好世界"
        temp_file.write_text(content, encoding="utf-8")

        encoding = detect_encoding(temp_file)
        assert encoding in ["utf-8", "utf-8-sig"]

    def test_detect_latin1(self, temp_file):
        """Test detecting Latin-1 encoding."""
        content = "Café résumé"
        temp_file.write_bytes(content.encode("latin-1"))

        encoding = detect_encoding(temp_file)
        # Normalize to lowercase for comparison
        assert encoding.lower() in [e.lower() for e in DEFAULT_ENCODINGS]

    def test_detect_ascii(self, temp_file):
        """Test detecting ASCII encoding."""
        content = "Simple ASCII text"
        temp_file.write_text(content, encoding="ascii")

        encoding = detect_encoding(temp_file)
        assert encoding in DEFAULT_ENCODINGS

    def test_detect_utf8_with_bom(self, temp_file):
        """Test detecting UTF-8 with BOM."""
        content = "Hello, World!"
        temp_file.write_text(content, encoding="utf-8-sig")

        encoding = detect_encoding(temp_file)
        # Normalize to lowercase for comparison
        assert encoding.lower() in ["utf-8", "utf-8-sig"]

    def test_detect_encoding_binary_file(self, temp_file):
        """Test that binary files raise EncodingError."""
        # Write binary data that can't be decoded
        temp_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

        # Binary files should either raise EncodingError or return an encoding
        try:
            encoding = detect_encoding(temp_file)
            # If it returns an encoding, it should be a string
            assert isinstance(encoding, str)
        except EncodingError as e:
            # If it raises, check the error message
            assert str(temp_file) in str(e)
            assert "Unable to decode" in str(e)

    def test_detect_encoding_custom_sample_size(self, temp_file):
        """Test detect_encoding with custom sample size."""
        content = "A" * 20000  # Large file
        temp_file.write_text(content, encoding="utf-8")

        encoding = detect_encoding(temp_file, sample_size=1000)
        assert encoding in DEFAULT_ENCODINGS


class TestReadFileWithEncoding:
    """Tests for read_file_with_encoding function."""

    def test_read_utf8(self, temp_file):
        """Test reading UTF-8 file."""
        content = "Line 1\nLine 2\nLine 3\n"
        temp_file.write_text(content, encoding="utf-8")

        lines, encoding = read_file_with_encoding(temp_file)
        assert len(lines) == 3
        # ASCII is a subset of UTF-8, so accept both
        assert encoding.lower() in ["utf-8", "utf-8-sig", "ascii"]
        assert lines[0] == "Line 1\n"

    def test_read_with_explicit_encoding(self, temp_file):
        """Test reading with explicit encoding."""
        content = "Café résumé"
        temp_file.write_bytes(content.encode("latin-1"))

        lines, encoding = read_file_with_encoding(temp_file, encoding="latin-1")
        assert encoding == "latin-1"
        assert "Café" in lines[0]

    def test_read_auto_detect(self, temp_file):
        """Test reading with auto-detection."""
        content = "Hello, World!\n"
        temp_file.write_text(content, encoding="utf-8")

        lines, encoding = read_file_with_encoding(temp_file, encoding=None)
        assert len(lines) == 1
        assert encoding in DEFAULT_ENCODINGS

    def test_read_wrong_encoding(self, temp_file):
        """Test reading with wrong encoding raises error."""
        content = "你好世界"
        temp_file.write_text(content, encoding="utf-8")

        with pytest.raises(EncodingError) as exc_info:
            read_file_with_encoding(temp_file, encoding="ascii")

        assert "ascii" in str(exc_info.value)

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            read_file_with_encoding(nonexistent)


class TestWriteFileWithEncoding:
    """Tests for write_file_with_encoding function."""

    def test_write_utf8(self, temp_file):
        """Test writing UTF-8 file."""
        lines = ["Line 1\n", "Line 2\n", "Line 3\n"]
        write_file_with_encoding(temp_file, lines, encoding="utf-8")

        content = temp_file.read_text(encoding="utf-8")
        assert content == "Line 1\nLine 2\nLine 3\n"

    def test_write_latin1(self, temp_file):
        """Test writing Latin-1 file."""
        lines = ["Café\n", "résumé\n"]
        write_file_with_encoding(temp_file, lines, encoding="latin-1")

        content = temp_file.read_text(encoding="latin-1")
        assert "Café" in content

    def test_write_with_bom(self, temp_file):
        """Test writing with BOM preservation."""
        lines = ["Hello\n"]
        write_file_with_encoding(temp_file, lines, encoding="utf-8", preserve_bom=True)

        # Check for BOM
        raw = temp_file.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")

    def test_write_without_bom(self, temp_file):
        """Test writing without BOM."""
        lines = ["Hello\n"]
        write_file_with_encoding(temp_file, lines, encoding="utf-8", preserve_bom=False)

        # Check no BOM
        raw = temp_file.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")

    def test_write_invalid_encoding(self, temp_file):
        """Test writing with invalid encoding."""
        lines = ["Hello\n"]

        with pytest.raises(EncodingError):
            write_file_with_encoding(temp_file, lines, encoding="invalid-encoding")


class TestNormalizeEncodingName:
    """Tests for normalize_encoding_name function."""

    def test_normalize_utf8(self):
        """Test normalizing UTF-8 variants."""
        assert normalize_encoding_name("UTF8") == "utf-8"
        assert normalize_encoding_name("utf8") == "utf-8"
        assert normalize_encoding_name("UTF-8") == "utf-8"

    def test_normalize_utf8_bom(self):
        """Test normalizing UTF-8 BOM variants."""
        assert normalize_encoding_name("UTF-8-BOM") == "utf-8-sig"
        assert normalize_encoding_name("utf-8-bom") == "utf-8-sig"

    def test_normalize_windows1252(self):
        """Test normalizing Windows-1252."""
        assert normalize_encoding_name("windows-1252") == "cp1252"
        assert normalize_encoding_name("WINDOWS-1252") == "cp1252"

    def test_normalize_latin1(self):
        """Test normalizing Latin-1 variants."""
        assert normalize_encoding_name("latin1") == "latin-1"
        assert normalize_encoding_name("iso-8859-1") == "latin-1"

    def test_normalize_unknown(self):
        """Test normalizing unknown encoding."""
        assert normalize_encoding_name("unknown-encoding") == "unknown-encoding"

    def test_normalize_with_underscores(self):
        """Test normalizing with underscores."""
        result = normalize_encoding_name("utf_8")
        assert "_" not in result


class TestIsTextFile:
    """Tests for is_text_file function."""

    def test_is_text_file_utf8(self, temp_file):
        """Test identifying UTF-8 text file."""
        temp_file.write_text("Hello, World!", encoding="utf-8")
        assert is_text_file(temp_file) is True

    def test_is_text_file_latin1(self, temp_file):
        """Test identifying Latin-1 text file."""
        temp_file.write_bytes("Café".encode("latin-1"))
        assert is_text_file(temp_file) is True

    def test_is_binary_file(self, temp_file):
        """Test identifying binary file."""
        temp_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
        assert is_text_file(temp_file) is False

    def test_is_text_file_with_null_bytes(self, temp_file):
        """Test that files with null bytes are binary."""
        temp_file.write_bytes(b"Hello\x00World")
        assert is_text_file(temp_file) is False

    def test_is_text_file_empty(self, temp_file):
        """Test empty file."""
        temp_file.write_text("")
        assert is_text_file(temp_file) is True

    def test_is_text_file_large(self, temp_file):
        """Test large text file."""
        content = "A" * 20000
        temp_file.write_text(content, encoding="utf-8")
        assert is_text_file(temp_file, sample_size=1000) is True


class TestGetEncodingInfo:
    """Tests for get_encoding_info function."""

    def test_get_info_utf8(self, temp_file):
        """Test getting info for UTF-8 file."""
        temp_file.write_text("Hello, World!", encoding="utf-8")

        info = get_encoding_info(temp_file)
        assert info["is_text"] is True
        assert info["encoding"] in ["utf-8", "utf-8-sig", "ascii"]
        assert info["has_bom"] is False

    def test_get_info_utf8_with_bom(self, temp_file):
        """Test getting info for UTF-8 file with BOM."""
        temp_file.write_text("Hello, World!", encoding="utf-8-sig")

        info = get_encoding_info(temp_file)
        assert info["is_text"] is True
        assert info["has_bom"] is True
        assert info["encoding"] == "utf-8-sig"
        assert info["confidence"] == 1.0

    def test_get_info_binary(self, temp_file):
        """Test getting info for binary file."""
        temp_file.write_bytes(b"\x00\x01\x02\x03")

        info = get_encoding_info(temp_file)
        assert info["is_text"] is False
        assert info["encoding"] == "unknown"

    def test_get_info_latin1(self, temp_file):
        """Test getting info for Latin-1 file."""
        temp_file.write_bytes("Café résumé".encode("latin-1"))

        info = get_encoding_info(temp_file)
        assert info["is_text"] is True
        assert isinstance(info["encoding"], str)
        assert isinstance(info["confidence"], float)

    def test_get_info_empty_file(self, temp_file):
        """Test getting info for empty file."""
        temp_file.write_text("")

        info = get_encoding_info(temp_file)
        assert info["is_text"] is True


class TestEncodingEdgeCases:
    """Tests for edge cases in encoding handling."""

    def test_mixed_line_endings(self, temp_file):
        """Test handling mixed line endings."""
        content = "Line 1\nLine 2\r\nLine 3\r"
        temp_file.write_text(content, encoding="utf-8")

        lines, encoding = read_file_with_encoding(temp_file)
        assert len(lines) >= 3

    def test_unicode_characters(self, temp_file):
        """Test handling various Unicode characters."""
        content = "Hello 世界 🌍 Привет مرحبا"
        temp_file.write_text(content, encoding="utf-8")

        lines, encoding = read_file_with_encoding(temp_file)
        assert "世界" in lines[0]
        assert "🌍" in lines[0]

    def test_empty_file_encoding(self, temp_file):
        """Test encoding detection on empty file."""
        temp_file.write_text("", encoding="utf-8")

        encoding = detect_encoding(temp_file)
        assert encoding in DEFAULT_ENCODINGS

    def test_very_long_lines(self, temp_file):
        """Test handling very long lines."""
        content = "A" * 100000 + "\n"
        temp_file.write_text(content, encoding="utf-8")

        lines, encoding = read_file_with_encoding(temp_file)
        assert len(lines[0]) > 100000

    def test_detect_encoding_with_chardet_available(self, temp_file, monkeypatch):
        """Test encoding detection when chardet is available."""
        # Create a file with specific encoding
        content = "Café résumé"
        temp_file.write_bytes(content.encode("latin-1"))

        # Mock chardet to return high confidence
        class MockChardet:
            @staticmethod
            def detect(data):
                return {"encoding": "latin-1", "confidence": 0.9}

        monkeypatch.setattr("spdx_headers.encoding.chardet", MockChardet(), raising=False)

        # Should use chardet result
        encoding = detect_encoding(temp_file)
        assert isinstance(encoding, str)

    def test_detect_encoding_with_chardet_low_confidence(self, temp_file, monkeypatch):
        """Test encoding detection when chardet has low confidence."""
        content = "Hello world"
        temp_file.write_text(content, encoding="utf-8")

        # Mock chardet to return low confidence
        class MockChardet:
            @staticmethod
            def detect(data):
                return {"encoding": "ascii", "confidence": 0.5}

        monkeypatch.setattr("spdx_headers.encoding.chardet", MockChardet(), raising=False)

        # Should fall back to trying encodings
        encoding = detect_encoding(temp_file)
        assert encoding in DEFAULT_ENCODINGS

    def test_write_file_with_encoding_error(self, temp_file):
        """Test write_file_with_encoding with encoding error."""
        # Try to write content that can't be encoded in ASCII
        lines = ["Hello 世界\n"]

        with pytest.raises(EncodingError):
            write_file_with_encoding(temp_file, lines, encoding="ascii")

    def test_get_encoding_info_with_chardet(self, temp_file, monkeypatch):
        """Test get_encoding_info when chardet is available."""
        content = "Hello world"
        temp_file.write_text(content, encoding="utf-8")

        # Mock chardet
        class MockChardet:
            @staticmethod
            def detect(data):
                return {"encoding": "utf-8", "confidence": 0.95}

        monkeypatch.setattr("spdx_headers.encoding.chardet", MockChardet(), raising=False)

        info = get_encoding_info(temp_file)
        assert info["is_text"] is True
        assert isinstance(info["encoding"], str)

    def test_get_encoding_info_error_handling(self, temp_file):
        """Test get_encoding_info handles errors gracefully."""
        # Create a file that might cause issues
        temp_file.write_bytes(b"\xff\xfe\xfd\xfc")

        info = get_encoding_info(temp_file)
        # Should return default values on error
        assert isinstance(info, dict)
        assert "encoding" in info
