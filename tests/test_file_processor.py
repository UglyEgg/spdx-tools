# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Comprehensive tests for FileProcessor class to achieve high coverage.
"""

import stat

import pytest

from spdx_headers.core import FileProcessor


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary Python file for testing."""
    file = tmp_path / "test.py"
    return file


class TestFileProcessorBasics:
    """Test basic FileProcessor functionality."""

    def test_init(self, temp_file):
        """Test FileProcessor initialization."""
        processor = FileProcessor(temp_file)
        assert processor.filepath == temp_file
        assert processor.lines == []
        assert processor.shebang is None
        assert processor.header == []
        assert processor.content == []
        assert processor._loaded is False
        assert processor._modified is False

    def test_load_simple_file(self, temp_file):
        """Test loading a simple Python file."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()

        assert processor._loaded is True
        assert len(processor.lines) == 1
        assert processor.content == ["print('hello')\n"]

    def test_load_with_shebang(self, temp_file):
        """Test loading file with shebang."""
        content = "#!/usr/bin/env python3\nprint('hello')\n"
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        assert processor.shebang == "#!/usr/bin/env python3\n"
        assert processor.content == ["print('hello')\n"]

    def test_load_with_header(self, temp_file):
        """Test loading file with SPDX header."""
        content = (
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        assert len(processor.header) == 3  # 2 header lines + blank
        assert processor.content == ["print('hello')\n"]

    def test_load_with_shebang_and_header(self, temp_file):
        """Test loading file with both shebang and header."""
        content = (
            "#!/usr/bin/env python3\n"
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        assert processor.shebang == "#!/usr/bin/env python3\n"
        assert len(processor.header) == 3
        assert processor.content == ["print('hello')\n"]

    def test_load_empty_file(self, temp_file):
        """Test loading an empty file."""
        temp_file.write_text("")

        processor = FileProcessor(temp_file)
        processor.load()

        assert processor._loaded is True
        assert processor.lines == []
        assert processor.content == []

    def test_load_only_once(self, temp_file):
        """Test that load() only loads once."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()
        first_lines = processor.lines.copy()

        # Modify file after loading
        temp_file.write_text("print('world')\n")

        # Load again - should not reload
        processor.load()
        assert processor.lines == first_lines

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file raises error."""
        nonexistent = tmp_path / "does_not_exist.py"

        processor = FileProcessor(nonexistent)
        with pytest.raises(OSError) as exc_info:
            processor.load()

        assert "Failed to read" in str(exc_info.value)


class TestFileProcessorHeaderDetection:
    """Test header detection functionality."""

    def test_has_header_true(self, temp_file):
        """Test has_header returns True when header exists."""
        content = (
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        assert processor.has_header() is True

    def test_has_header_false(self, temp_file):
        """Test has_header returns False when no header."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        assert processor.has_header() is False

    def test_has_header_loads_file(self, temp_file):
        """Test has_header loads file if not loaded."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        assert processor._loaded is False
        processor.has_header()
        assert processor._loaded is True


class TestFileProcessorHeaderManipulation:
    """Test header manipulation methods."""

    def test_add_header(self, temp_file):
        """Test adding a header."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()

        new_header = "# SPDX-FileCopyrightText: 2025 Test\n# SPDX-License-Identifier: MIT\n\n"
        processor.add_header(new_header)

        assert processor._modified is True
        assert len(processor.header) == 3

    def test_add_header_replaces_existing(self, temp_file):
        """Test adding header replaces existing one."""
        content = (
            "# SPDX-FileCopyrightText: 2025 Old\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        new_header = (
            "# SPDX-FileCopyrightText: 2025 New\n" "# SPDX-License-Identifier: Apache-2.0\n\n"
        )
        processor.add_header(new_header)

        assert "New" in "".join(processor.header)
        assert "Apache-2.0" in "".join(processor.header)

    def test_add_header_loads_if_needed(self, temp_file):
        """Test add_header loads file if not loaded."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        assert processor._loaded is False

        processor.add_header("# Header\n")
        assert processor._loaded is True

    def test_remove_header(self, temp_file):
        """Test removing a header."""
        content = (
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()
        processor.remove_header()

        assert processor._modified is True
        assert processor.header == []

    def test_remove_header_when_none_exists(self, temp_file):
        """Test removing header when none exists."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()
        processor.remove_header()

        assert processor._modified is False
        assert processor.header == []

    def test_remove_header_loads_if_needed(self, temp_file):
        """Test remove_header loads file if not loaded."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.remove_header()

        assert processor._loaded is True


class TestFileProcessorGetContent:
    """Test get_content method."""

    def test_get_content_simple(self, temp_file):
        """Test getting content from simple file."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        content = processor.get_content()

        assert content == "print('hello')\n"

    def test_get_content_with_shebang(self, temp_file):
        """Test getting content with shebang."""
        content = "#!/usr/bin/env python3\nprint('hello')\n"
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        result = processor.get_content()

        assert result == content

    def test_get_content_with_header(self, temp_file):
        """Test getting content with header."""
        content = (
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        result = processor.get_content()

        assert result == content

    def test_get_content_loads_if_needed(self, temp_file):
        """Test get_content loads file if not loaded."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.get_content()

        assert processor._loaded is True


class TestFileProcessorSave:
    """Test save functionality with atomic writes."""

    def test_save_creates_file(self, temp_file):
        """Test save creates new file."""
        processor = FileProcessor(temp_file)
        processor.lines = ["print('hello')\n"]
        processor.content = ["print('hello')\n"]
        processor._loaded = True
        processor._modified = True

        processor.save()

        assert temp_file.exists()
        assert temp_file.read_text() == "print('hello')\n"

    def test_save_with_shebang(self, temp_file):
        """Test save preserves shebang."""
        processor = FileProcessor(temp_file)
        processor.shebang = "#!/usr/bin/env python3\n"
        processor.content = ["print('hello')\n"]
        processor._loaded = True
        processor._modified = True

        processor.save()

        content = temp_file.read_text()
        assert content.startswith("#!/usr/bin/env python3\n")

    def test_save_with_header(self, temp_file):
        """Test save includes header."""
        processor = FileProcessor(temp_file)
        processor.header = ["# Header\n", "\n"]
        processor.content = ["print('hello')\n"]
        processor._loaded = True
        processor._modified = True

        processor.save()

        content = temp_file.read_text()
        assert "# Header\n" in content

    def test_save_preserves_permissions(self, temp_file):
        """Test save preserves file permissions."""
        temp_file.write_text("print('hello')\n")
        temp_file.chmod(0o755)
        original_mode = temp_file.stat().st_mode

        processor = FileProcessor(temp_file)
        processor.load()
        processor.add_header("# Header\n")
        processor.save()

        new_mode = temp_file.stat().st_mode
        assert stat.S_IMODE(new_mode) == stat.S_IMODE(original_mode)

    def test_save_not_modified_skips(self, temp_file):
        """Test save skips if not modified."""
        temp_file.write_text("print('hello')\n")
        original_content = temp_file.read_text()

        processor = FileProcessor(temp_file)
        processor.load()
        processor.save()  # Not modified

        assert temp_file.read_text() == original_content

    def test_save_force_writes_anyway(self, temp_file):
        """Test save with force=True writes even if not modified."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()
        processor.save(force=True)

        assert temp_file.exists()

    def test_save_not_loaded_skips(self, temp_file):
        """Test save skips if file not loaded."""
        processor = FileProcessor(temp_file)
        processor.save()

        assert not temp_file.exists()

    def test_save_cleans_up_on_error(self, temp_file, monkeypatch):
        """Test save cleans up temporary file on error."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()
        processor._modified = True

        # Mock shutil.move to raise an error
        def mock_move(*args, **kwargs):
            raise OSError("Simulated error")

        monkeypatch.setattr("shutil.move", mock_move)

        with pytest.raises(OSError):
            processor.save()

        # Check no temp files left (cleanup should have happened)
        temp_files = list(temp_file.parent.glob(".test.py.*.tmp"))
        assert len(temp_files) == 0


class TestFileProcessorIsModified:
    """Test is_modified method."""

    def test_is_modified_false_initially(self, temp_file):
        """Test is_modified is False initially."""
        processor = FileProcessor(temp_file)
        assert processor.is_modified() is False

    def test_is_modified_true_after_add(self, temp_file):
        """Test is_modified is True after adding header."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()
        processor.add_header("# Header\n")

        assert processor.is_modified() is True

    def test_is_modified_true_after_remove(self, temp_file):
        """Test is_modified is True after removing header."""
        content = "# SPDX-FileCopyrightText: 2025 Test\nprint('hello')\n"
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()
        processor.remove_header()

        assert processor.is_modified() is True

    def test_is_modified_false_after_save(self, temp_file):
        """Test is_modified is False after save."""
        temp_file.write_text("print('hello')\n")

        processor = FileProcessor(temp_file)
        processor.load()
        processor.add_header("# Header\n")
        processor.save()

        assert processor.is_modified() is False


class TestFileProcessorEdgeCases:
    """Test edge cases and error conditions."""

    def test_parse_structure_with_comments_before_header(self, temp_file):
        """Test parsing file with comments before SPDX header."""
        content = (
            "# Regular comment\n"
            "# Another comment\n"
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        # Comments before SPDX should not be in header
        assert "Regular comment" not in "".join(processor.header)

    def test_parse_structure_with_blank_lines_in_header(self, temp_file):
        """Test parsing header with blank lines."""
        content = (
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "#\n"
            "# SPDX-License-Identifier: MIT\n"
            "\n"
            "print('hello')\n"
        )
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        assert len(processor.header) == 4  # Including blank lines

    def test_multiline_content(self, temp_file):
        """Test handling multiline content."""
        content = "def hello():\n" "    print('hello')\n" "    return True\n"
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        assert len(processor.content) == 3

    def test_unicode_content(self, temp_file):
        """Test handling Unicode content."""
        content = "print('Hello 世界 🌍')\n"
        temp_file.write_text(content, encoding="utf-8")

        processor = FileProcessor(temp_file)
        processor.load()

        assert "世界" in processor.get_content()
        assert "🌍" in processor.get_content()

    def test_very_long_file(self, temp_file):
        """Test handling very long files."""
        lines = [f"# Line {i}\n" for i in range(10000)]
        temp_file.write_text("".join(lines))

        processor = FileProcessor(temp_file)
        processor.load()

        assert len(processor.lines) == 10000

    def test_file_with_only_shebang(self, temp_file):
        """Test file with only shebang."""
        temp_file.write_text("#!/usr/bin/env python3\n")

        processor = FileProcessor(temp_file)
        processor.load()

        assert processor.shebang == "#!/usr/bin/env python3\n"
        assert processor.content == []

    def test_file_with_only_header(self, temp_file):
        """Test file with only header, no code."""
        content = "# SPDX-FileCopyrightText: 2025 Test\n" "# SPDX-License-Identifier: MIT\n"
        temp_file.write_text(content)

        processor = FileProcessor(temp_file)
        processor.load()

        assert len(processor.header) > 0
        assert processor.content == []
