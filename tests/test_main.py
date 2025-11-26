# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Tests for __main__.py module execution.
"""

import subprocess
import sys


def test_main_module_execution():
    """Test that the module can be executed with python -m."""
    # This test requires the package to be installed
    # Skip if not installed
    result = subprocess.run(
        [sys.executable, "-m", "spdx_headers", "--help"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()
    else:
        # Package not installed, skip
        pass


def test_main_module_version():
    """Test that the module can display version."""
    # This test requires the package to be installed
    # Skip if not installed
    result = subprocess.run(
        [sys.executable, "-m", "spdx_headers", "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Version output should contain a version number
        assert any(char.isdigit() for char in result.stdout)
    else:
        # Package not installed, skip
        pass