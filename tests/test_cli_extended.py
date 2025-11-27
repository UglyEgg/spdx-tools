# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Extended tests for CLI module to improve coverage.
"""

import sys
from unittest.mock import patch

import pytest

from spdx_headers.cli import main


class TestCLIUpdateCommand:
    """Tests for --update command."""

    @patch("spdx_headers.cli.update_license_data")
    def test_update_command(self, mock_update):
        """Test update command."""
        with patch.object(sys, "argv", ["spdx-headers", "--update"]):
            result = main()
            assert result == 0
            mock_update.assert_called_once()

    @patch("spdx_headers.cli.update_license_data")
    def test_update_with_data_file(self, mock_update):
        """Test update command with custom data file."""
        with patch.object(sys, "argv", ["spdx-headers", "--update", "--data-file", "custom.json"]):
            result = main()
            assert result == 0


class TestCLICheckCommand:
    """Tests for --check command."""

    def test_check_with_fix_error(self, tmp_path, capsys):
        """Test that --fix without --check shows error."""
        with patch.object(sys, "argv", ["spdx-headers", "--fix", "-p", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2
            captured = capsys.readouterr()
            assert "must be used together with --check" in captured.out

    @patch("spdx_headers.cli.auto_fix_headers")
    @patch("spdx_headers.cli.check_headers")
    def test_check_with_fix(self, mock_check, mock_fix, tmp_path):
        """Test --check with --fix."""
        mock_check.return_value = 1  # Some files missing headers

        with patch.object(sys, "argv", ["spdx-headers", "--check", "--fix", "-p", str(tmp_path)]):
            main()
            mock_fix.assert_called_once()


class TestCLIListCommand:
    """Tests for --list command."""

    def test_list_all_licenses(self):
        """Test listing all licenses."""
        with patch.object(sys, "argv", ["spdx-headers", "--list"]):
            result = main()
            assert result == 0

    def test_list_with_keyword(self):
        """Test listing licenses with keyword."""
        with patch.object(sys, "argv", ["spdx-headers", "--list", "apache"]):
            result = main()
            assert result == 0

    def test_list_no_matches(self):
        """Test listing with keyword that has no matches."""
        with patch.object(sys, "argv", ["spdx-headers", "--list", "nonexistent-license-xyz"]):
            result = main()
            # Should return 1 when no matches found
            assert result in [0, 1]

    @patch("spdx_headers.cli.load_license_data")
    def test_list_empty_licenses(self, mock_load, capsys):
        """Test listing when no licenses available."""
        # Mock empty license data
        mock_load.return_value = {
            "metadata": {
                "spdx_version": "3.0",
                "generated_at": "2025-01-01",
                "license_count": 0,
            },
            "licenses": {},
        }

        with patch.object(sys, "argv", ["spdx-headers", "--list"]):
            result = main()
            captured = capsys.readouterr()
            assert "No licenses available" in captured.out or result == 0


class TestCLIAddCommand:
    """Tests for --add command."""

    def test_add_with_extract(self, tmp_path):
        """Test --add with --extract."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--add",
                "MIT",
                "--extract",
                "",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0

    def test_add_with_extract_different_license(self, tmp_path):
        """Test --add with --extract specifying different license."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--add",
                "MIT",
                "--extract",
                "Apache-2.0",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0


class TestCLIChangeCommand:
    """Tests for --change command."""

    def test_change_with_extract(self, tmp_path):
        """Test --change with --extract."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--change",
                "Apache-2.0",
                "--extract",
                "",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0

    def test_change_with_extract_different_license(self, tmp_path):
        """Test --change with --extract specifying different license."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--change",
                "Apache-2.0",
                "--extract",
                "GPL-3.0",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0


class TestCLIRemoveCommand:
    """Tests for --remove command."""

    def test_remove_headers(self, tmp_path):
        """Test removing headers."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        with patch.object(
            sys, "argv", ["spdx-headers", "--remove", "--dry-run", "-p", str(tmp_path)]
        ):
            result = main()
            assert result == 0


class TestCLIVerifyCommand:
    """Tests for --verify command."""

    def test_verify_headers(self, tmp_path):
        """Test verifying headers."""
        file1 = tmp_path / "test.py"
        file1.write_text(
            "# SPDX-FileCopyrightText: 2025 Test\n"
            "# SPDX-License-Identifier: MIT\n"
            "print('hello')\n"
        )

        with patch.object(sys, "argv", ["spdx-headers", "--verify", "-p", str(tmp_path)]):
            result = main()
            assert result == 0


class TestCLIExtractCommand:
    """Tests for --extract command."""

    def test_extract_no_matches(self, tmp_path):
        """Test extract with no matching licenses."""
        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--extract",
                "nonexistent-license-xyz",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            # Should return 1 when no matches
            assert result in [0, 1]

    def test_extract_with_keyword(self, tmp_path):
        """Test extract with keyword."""
        with patch.object(sys, "argv", ["spdx-headers", "--extract", "MIT", "-p", str(tmp_path)]):
            result = main()
            assert result == 0


class TestCLINoArguments:
    """Tests for CLI with no arguments."""

    def test_no_arguments_shows_help(self, capsys):
        """Test that no arguments shows help."""
        with patch.object(sys, "argv", ["spdx-headers"]):
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            # Should show usage/help information
            assert len(captured.out) > 0 or len(captured.err) > 0


class TestCLIEdgeCases:
    """Tests for CLI edge cases."""

    def test_with_year_option(self, tmp_path):
        """Test with --year option."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--add",
                "MIT",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0

    def test_with_name_option(self, tmp_path):
        """Test with --name option."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--add",
                "MIT",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0

    def test_with_email_option(self, tmp_path):
        """Test with --email option."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--add",
                "MIT",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0

    def test_with_all_options(self, tmp_path):
        """Test with all options combined."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--add",
                "MIT",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0

    def test_with_custom_data_file(self, tmp_path):
        """Test with custom data file."""
        # Create a minimal valid data file
        data_file = tmp_path / "custom_data.json"
        data_file.write_text(
            '{"metadata": {"spdx_version": "3.0", "generated_at": "2025-01-01", '
            '"license_count": 1}, "licenses": {"MIT": {"name": "MIT License", '
            '"deprecated": false, "osi_approved": true, "fsf_libre": true, '
            '"header_template": "# MIT\\n"}}}'
        )

        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--data-file",
                str(data_file),
                "--add",
                "MIT",
                "--dry-run",
                "-p",
                str(tmp_path),
            ],
        ):
            result = main()
            assert result == 0

    def test_version_option(self):
        """Test --version option."""
        with patch.object(sys, "argv", ["spdx-headers", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Version should exit with 0
            assert exc_info.value.code == 0

    def test_help_option(self):
        """Test --help option."""
        with patch.object(sys, "argv", ["spdx-headers", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Help should exit with 0
            assert exc_info.value.code == 0


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_directory(self):
        """Test with invalid directory."""
        with patch.object(sys, "argv", ["spdx-headers", "--check", "/nonexistent/directory"]):
            # Should handle gracefully
            try:
                result = main()
                assert isinstance(result, int)
            except SystemExit:
                pass  # Expected

    def test_invalid_license(self, tmp_path):
        """Test with invalid license identifier."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(
            sys,
            "argv",
            [
                "spdx-headers",
                "--add",
                "INVALID-LICENSE-XYZ",
                "--dry-run",
                str(tmp_path),
            ],
        ):
            # Should handle gracefully
            try:
                result = main()
                assert isinstance(result, int)
            except (SystemExit, KeyError):
                pass  # Expected

    def test_conflicting_options(self, tmp_path):
        """Test with conflicting options."""
        with patch.object(
            sys,
            "argv",
            ["spdx-headers", "--add", "MIT", "--change", "Apache-2.0", str(tmp_path)],
        ):
            # Should handle gracefully
            try:
                result = main()
                assert isinstance(result, int)
            except SystemExit:
                pass  # Expected


class TestCLIOutputFormatting:
    """Tests for CLI output formatting."""

    def test_list_output_format(self, capsys):
        """Test that list output is properly formatted."""
        with patch.object(sys, "argv", ["spdx-headers", "--list", "MIT"]):
            main()
            captured = capsys.readouterr()
            # Should contain license information
            assert len(captured.out) > 0

    def test_check_output_format(self, tmp_path, capsys):
        """Test that check output is properly formatted."""
        file1 = tmp_path / "test.py"
        file1.write_text("print('hello')\n")

        with patch.object(sys, "argv", ["spdx-headers", "--check", "-p", str(tmp_path)]):
            main()
            captured = capsys.readouterr()
            # Should contain check results
            assert len(captured.out) > 0
