# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# GNU Affero General Public License v3.0 or later

"""
Generate SPDX license data file from the official SPDX license list.
"""

import argparse

from .data import DEFAULT_DATA_FILE, update_license_data


def main() -> None:
    """Generate SPDX license data file."""
    parser = argparse.ArgumentParser(
        description="Generate SPDX license data file from the official SPDX license list."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help=f"Output file path. Defaults to {DEFAULT_DATA_FILE}",
    )

    args = parser.parse_args()

    update_license_data(args.output)


if __name__ == "__main__":
    main()
