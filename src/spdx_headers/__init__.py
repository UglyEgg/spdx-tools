# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
SPDX Headers - A tool for managing SPDX headers in Python source files.
"""

from ._version import __version__

# Provide both __version__ and version for compatibility with callers expecting either.
version = __version__

__all__ = ["__version__", "version"]
