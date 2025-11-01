# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Command-line interface for SPDX header management.
"""

import argparse
import os
import sys

from .core import find_src_directory, get_copyright_info
from .data import DEFAULT_DATA_FILE, load_license_data, update_license_data
from .operations import (
    add_header_to_py_files,
    auto_fix_headers,
    change_header_in_py_files,
    check_headers,
    extract_license,
    filter_licenses,
    remove_header_from_py_files,
    show_license,
    verify_spdx_headers,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage SPDX headers in Python source files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -a GPL-3.0-only -p /path/to/repo
  %(prog)s -c MIT -p /path/to/repo --dry-run
  %(prog)s -v -p /path/to/repo
  %(prog)s -s MIT
  %(prog)s --check -p /path/to/repo
        """,
    )

    # Operation group
    operation_group = parser.add_mutually_exclusive_group(required=False)
    operation_group.add_argument(
        "-a",
        "--add",
        type=str,
        metavar="LICENSE",
        help="Add an SPDX header for the specified LICENSE to all Python files.",
    )
    operation_group.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove the SPDX header from all Python files.",
    )
    operation_group.add_argument(
        "-c",
        "--change",
        type=str,
        metavar="LICENSE",
        help="Change the SPDX license identifier in all Python files to the specified LICENSE.",
    )
    operation_group.add_argument(
        "-v",
        "--verify",
        action="store_true",
        help="Verify that all Python files have a valid SPDX header.",
    )
    operation_group.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update the SPDX license data file.",
    )
    operation_group.add_argument(
        "--check",
        action="store_true",
        help="Check for missing headers and exit with error code if found.",
    )
    operation_group.add_argument(
        "-s",
        "--show",
        type=str,
        metavar="LICENSE",
        help="Display the LICENSE text using the system default editor.",
    )

    # Extract option can be combined with add or change
    parser.add_argument(
        "-e",
        "--extract",
        nargs="?",
        const="",
        default=None,
        metavar="KEYWORD",
        help=(
            "Extract license text to the repository root. "
            "Combine with -a/-c to write the chosen license, or supply KEYWORD to "
            "select licenses by keyword."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making modifications.",
    )

    parser.add_argument(
        "-l",
        "--list",
        nargs="?",
        const="",
        metavar="KEYWORD",
        help="List available license keywords, optionally filtering by KEYWORD.",
    )

    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="When combined with --check, attempt to add missing headers automatically.",
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="When showing a license, keep the temporary file instead of deleting it.",
    )

    # Add repository path option
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        default=".",
        help="Specify the repository path to operate on. Defaults to the current directory.",
    )

    # Add data file path option
    parser.add_argument(
        "-d",
        "--data-file",
        type=str,
        default=None,
        help=f"Path to the SPDX license data file. Defaults to {DEFAULT_DATA_FILE}",
    )

    args = parser.parse_args()

    # Handle update request first
    if args.update:
        update_license_data(args.data_file)
        return 0

    # Load the license data
    license_data = load_license_data(args.data_file)

    # Use the specified repository path
    repo_path = os.path.abspath(args.path)

    # Get copyright information
    year, name, email = get_copyright_info(repo_path)

    # Find the source directory
    src_dir = find_src_directory(repo_path)

    if args.fix and not args.check:
        print("Error: The --fix option must be used together with --check.")
        sys.exit(2)

    extract_arg = args.extract

    if args.list is not None:
        keyword_raw = args.list.strip() if args.list is not None else ""
        keyword = keyword_raw or None
        matching_licenses = filter_licenses(license_data, keyword)
        total_licenses = license_data["metadata"]["license_count"]

        if matching_licenses:
            print("Available license keywords:")
            print(f"SPDX version: {license_data['metadata']['spdx_version']}")
            print(f"Generated: {license_data['metadata']['generated_at']}")
            if keyword:
                print(f"Filter: {keyword}")
                print(
                    f"Matched licenses: {len(matching_licenses)} of {total_licenses} total"
                )
            else:
                print(f"Total licenses: {total_licenses}")
            print("\nLicenses:")

            for license_key, details in matching_licenses:
                deprecated = " (deprecated)" if details.get("deprecated", False) else ""
                osi = " [OSI]" if details.get("osi_approved", False) else ""
                fsf = " [FSF]" if details.get("fsf_libre", False) else ""
                print(
                    f"- {license_key}{deprecated}{osi}{fsf}: {details.get('name', '')}"
                )
        else:
            if keyword:
                print(f"No licenses found matching keyword '{keyword}'.")
            else:
                print("No licenses available.")
        return 0
    elif args.add:
        add_header_to_py_files(
            src_dir, args.add, license_data, year, name, email, args.dry_run
        )
        # If extract is also specified, extract the license file
        if extract_arg is not None:
            target_license = args.add if extract_arg == "" else extract_arg
            extract_license(target_license, license_data, repo_path, args.dry_run)
        return 0
    elif args.change:
        change_header_in_py_files(
            src_dir, args.change, license_data, year, name, email, args.dry_run
        )
        # If extract is also specified, extract the license file
        if extract_arg is not None:
            target_license = args.change if extract_arg == "" else extract_arg
            extract_license(target_license, license_data, repo_path, args.dry_run)
        return 0
    elif args.show:
        cleanup_delay = None if args.keep_temp else 30.0
        show_license(args.show, license_data, cleanup_delay=cleanup_delay)
        return 0
    elif args.remove:
        remove_header_from_py_files(src_dir, args.dry_run)
        return 0
    elif args.verify:
        verify_spdx_headers(src_dir)
        return 0
    elif args.check:
        exit_code = check_headers(src_dir)
        if exit_code != 0 and args.fix:
            success = auto_fix_headers(
                src_dir, license_data, year, name, email, args.dry_run
            )
            if success:
                exit_code = check_headers(src_dir)
        return exit_code
    elif extract_arg is not None:
        if extract_arg == "":
            print(
                "Error: Provide a license keyword when using --extract without --add or --change."
            )
            return 2

        keyword = extract_arg.strip()
        matching_licenses = filter_licenses(license_data, keyword)

        if not matching_licenses:
            print(f"No licenses found matching keyword '{keyword}'.")
            return 1

        extracted_count = 0
        for license_key, _details in matching_licenses:
            extract_license(license_key, license_data, repo_path, args.dry_run)
            extracted_count += 1

        if extracted_count > 1:
            print(f"✓ Extracted {extracted_count} licenses matching '{keyword}'.")
        else:
            print(f"✓ Extracted license matching '{keyword}'.")
        return 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
