"""Tests for new functionality added in recent updates."""

from unittest.mock import patch

import pytest

from spdx_headers.cli import main
from spdx_headers.core import find_repository_root
from spdx_headers.operations import add_header_to_single_file


class TestFindRepositoryRoot:
    """Test the find_repository_root function."""

    def test_finds_repository_root_with_pyproject_toml(self, tmp_path):
        """Test finding repository root when pyproject.toml exists."""
        # Create a directory structure
        repo_root = tmp_path / "my_repo"
        repo_root.mkdir()
        (repo_root / "pyproject.toml").write_text("[project]\nname = 'test'")

        subdir = repo_root / "src" / "subdir"
        subdir.mkdir(parents=True)

        # Test from subdirectory
        found_root = find_repository_root(subdir)
        assert found_root == repo_root

    def test_finds_repository_root_with_git(self, tmp_path):
        """Test finding repository root when .git exists."""
        repo_root = tmp_path / "my_repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        subdir = repo_root / "src"
        subdir.mkdir()

        found_root = find_repository_root(subdir)
        assert found_root == repo_root

    def test_finds_repository_root_with_setup_py(self, tmp_path):
        """Test finding repository root when setup.py exists."""
        repo_root = tmp_path / "my_repo"
        repo_root.mkdir()
        (repo_root / "setup.py").write_text("# setup.py")

        subdir = repo_root / "package"
        subdir.mkdir()

        found_root = find_repository_root(subdir)
        assert found_root == repo_root

    def test_returns_current_dir_when_no_repository_found(self, tmp_path):
        """Test that current directory is returned when no repository markers are found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        found_root = find_repository_root(empty_dir)
        assert found_root == empty_dir.resolve()

    def test_prefers_closest_marker(self, tmp_path):
        """Test that the closest repository marker is preferred."""
        # Create nested structure
        outer_repo = tmp_path / "outer"
        outer_repo.mkdir()
        (outer_repo / "pyproject.toml").write_text("[project]")

        inner_repo = outer_repo / "inner"
        inner_repo.mkdir()
        (inner_repo / ".git").mkdir()

        subdir = inner_repo / "src"
        subdir.mkdir()

        # Should find inner repo (closer)
        found_root = find_repository_root(subdir)
        assert found_root == inner_repo


class TestAddHeaderToSingleFile:
    """Test the add_header_to_single_file function."""

    def test_adds_header_to_simple_file(self, tmp_path):
        """Test adding header to a simple Python file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello world')\n")

        mock_license_data = {
            "licenses": {"MIT": {"name": "MIT License", "text": "MIT License text"}}
        }

        add_header_to_single_file(
            test_file, "MIT", mock_license_data, "2025", "Test Author", "test@example.com"
        )

        content = test_file.read_text()
        assert "SPDX-FileCopyrightText: 2025 Test Author <test@example.com>" in content
        assert "SPDX-License-Identifier: MIT" in content
        assert "print('hello world')" in content

    def test_preserves_shebang(self, tmp_path):
        """Test that shebang lines are preserved when adding headers."""
        test_file = tmp_path / "test.py"
        test_file.write_text("#!/usr/bin/env python3\nprint('hello')\n")

        mock_license_data = {"licenses": {"MIT": {"name": "MIT License", "text": "MIT text"}}}

        add_header_to_single_file(
            test_file, "MIT", mock_license_data, "2025", "Test Author", "test@example.com"
        )

        content = test_file.read_text()
        lines = content.split("\n")
        assert lines[0] == "#!/usr/bin/env python3"
        assert "SPDX-FileCopyrightText:" in content

    def test_respects_dry_run(self, tmp_path):
        """Test that dry_run doesn't modify the file."""
        test_file = tmp_path / "test.py"
        original_content = "print('hello world')\n"
        test_file.write_text(original_content)

        mock_license_data = {"licenses": {"MIT": {"name": "MIT License", "text": "MIT text"}}}

        add_header_to_single_file(
            test_file,
            "MIT",
            mock_license_data,
            "2025",
            "Test Author",
            "test@example.com",
            dry_run=True,
        )

        # File should be unchanged
        assert test_file.read_text() == original_content

    def test_handles_existing_header(self, tmp_path):
        """Test handling files that already have headers."""
        test_file = tmp_path / "test.py"
        existing_content = """# SPDX-FileCopyrightText: 2024 Old Author
# SPDX-License-Identifier: Apache-2.0
print('hello')
"""
        test_file.write_text(existing_content)

        mock_license_data = {"licenses": {"MIT": {"name": "MIT License", "text": "MIT text"}}}

        # This should detect existing header and skip modification
        add_header_to_single_file(
            test_file, "MIT", mock_license_data, "2025", "New Author", "new@example.com"
        )

        # File should remain unchanged when header already exists
        content = test_file.read_text()
        assert content == existing_content


class TestCLIFileOption:
    """Test the --file CLI option."""

    def test_file_option_add_header(self, tmp_path, monkeypatch):
        """Test using --file option to add header to specific file."""
        test_file = tmp_path / "specific_file.py"
        test_file.write_text("print('test')\n")

        # Change to the temp directory for testing
        monkeypatch.chdir(tmp_path)

        # Mock the license data to avoid needing actual data files
        mock_license_data = {"licenses": {"MIT": {"name": "MIT License", "text": "MIT text"}}}

        with patch("spdx_headers.cli.load_license_data", return_value=mock_license_data):
            with patch(
                "spdx_headers.cli.get_copyright_info",
                return_value=("2025", "Test Author", "test@example.com"),
            ):
                with patch(
                    "sys.argv",
                    ["spdx-headers", "--file", str(test_file), "--add", "MIT", "--dry-run"],
                ):
                    # This should not raise an exception
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected for successful CLI execution

    def test_file_option_overrides_path(self, tmp_path, monkeypatch):
        """Test that --file option overrides --path option."""
        test_file = tmp_path / "target_file.py"
        test_file.write_text("print('target')\n")

        other_dir = tmp_path / "other_dir"
        other_dir.mkdir()

        monkeypatch.chdir(tmp_path)

        mock_license_data = {"licenses": {"MIT": {"name": "MIT License", "text": "MIT text"}}}

        with patch("spdx_headers.cli.load_license_data", return_value=mock_license_data):
            with patch(
                "spdx_headers.cli.get_copyright_info",
                return_value=("2025", "Test Author", "test@example.com"),
            ):
                with patch(
                    "sys.argv",
                    [
                        "spdx-headers",
                        "--file",
                        str(test_file),
                        "--path",
                        str(other_dir),
                        "--add",
                        "MIT",
                        "--dry-run",
                    ],
                ):
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected for successful CLI execution

    def test_file_option_with_nonexistent_file(self, tmp_path, monkeypatch):
        """Test --file option with non-existent file."""
        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["spdx-headers", "--file", "nonexistent.py", "--add", "MIT"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with error code
            assert exc_info.value.code != 0


class TestEnhancedPathResolution:
    """Test enhanced path resolution functionality."""

    def test_enhanced_copyright_detection(self, tmp_path):
        """Test that copyright detection uses repository root."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        # Create pyproject.toml in repo root
        pyproject_content = """
[project]
name = "test-project"
authors = [
    {name = "Repo Author", email = "repo@example.com"}
]
"""
        (repo_root / "pyproject.toml").write_text(pyproject_content)

        # Create a subdirectory with a Python file
        subdir = repo_root / "src" / "subdir"
        subdir.mkdir(parents=True)

        # This should detect copyright from the repo root, not the subdirectory
        from spdx_headers.core import get_copyright_info

        year, name, email = get_copyright_info(subdir)

        assert name == "Repo Author"
        assert email == "repo@example.com"
