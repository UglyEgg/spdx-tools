# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
SPDX Headers - A tool for managing SPDX headers in Python source files.
"""

from __future__ import annotations

import warnings

try:
    from ._version import __version__
except ModuleNotFoundError:  # pragma: no cover - generated file missing
    warnings.warn(
        "src/spdx_headers/_version.py is missing. "
        "Regenerate it with `python scripts/bump_version.py --set <version>`.",
        RuntimeWarning,
    )
    __version__ = "0.0.0+unknown"

# Provide both __version__ and version for compatibility with callers expecting either.
version = __version__

__all__ = ["__version__", "version"]
