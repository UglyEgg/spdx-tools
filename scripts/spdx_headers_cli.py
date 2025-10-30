#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Run the spdx_headers CLI without installing the package.

This helper keeps local tooling (for example pre-commit hooks) working when the
project uses the ``src`` layout.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"

    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from spdx_headers.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
