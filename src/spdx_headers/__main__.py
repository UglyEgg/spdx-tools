# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Allow running spdx_headers as a module with python -m spdx_headers
"""

from .cli import main

if __name__ == "__main__":
    main()
