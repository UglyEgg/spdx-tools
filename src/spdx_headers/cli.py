# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Command-line interface for SPDX header management.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import (
    find_repository_root,
    find_src_directory,
    get_copyright_info,
    has_spdx_header,
)
from .data import DEFAULT_DATA_FILE, load_license_data, update_license_data
from .operations import (
    add_header_to_py_files,
    add_header_to_single_file,
    auto_fix_headers,
    change_header_in_py_files,
    change_header_in_single_file,
    check_headers,
    extract_license,
    filter_licenses,
    remove_header_from_py_files,
    remove_header_from_single_file,
    show_license,
    verify_spdx_header_in_single_file,
    verify_spdx_headers,
)


def main() -> int:
    """Main entry point for the spdx-headers CLI tool.

    Parses command-line arguments and executes the requested operation
    for managing SPDX headers in Python source files.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description="Manage SPDX headers in Python source files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Operation group
    primary_actions = parser.add_argument_group("Primary actions")
    operation_group = primary_actions.add_mutually_exclusive_group(required=False)
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
    extraction_group = parser.add_argument_group("License extraction and listing")
    extraction_group.add_argument(
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

    extraction_group.add_argument(
        "-l",
        "--list",
        nargs="?",
        const="",
        metavar="KEYWORD",
        help="List available license keywords, optionally filtering by KEYWORD.",
    )

    extraction_group.add_argument(
        "--keep-temp",
        action="store_true",
        help="When showing a license, keep the temporary file instead of deleting it.",
    )

    execution_group = parser.add_argument_group("Execution control")
    execution_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making modifications.",
    )

    execution_group.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="When combined with --check, attempt to add missing headers automatically.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version and exit.",
    )

    # Add repository path option
    path_group = parser.add_argument_group("Paths")
    path_group.add_argument(
        "-p",
        "--path",
        type=str,
        default=None,
        help=(
            "Specify the directory path to operate on. "
            "Defaults to auto-detected source directory."
        ),
    )

    path_group.add_argument(
        "--file",
        type=str,
        default=None,
        help="Specify an individual Python file to operate on. Overrides --path.",
    )

    # Add data file path option
    path_group.add_argument(
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

    # Handle file vs directory targeting
    if args.file:
        # Individual file mode
        target_file = str(Path(args.file).resolve())
        if not target_file.endswith(".py"):
            print(f"Error: {args.file} is not a Python file (.py extension required)")
            sys.exit(1)
        if not Path(target_file).exists():
            print(f"Error: File {args.file} not found")
            sys.exit(1)

        # For individual files, use the file's directory for copyright detection
        file_dir = str(Path(target_file).parent)
        repo_path = file_dir
        src_dir = file_dir
        target_mode = "file"
    else:
        # Directory mode
        target_mode = "directory"
        if args.path:
            # User specified a path
            repo_path = str(Path(args.path).resolve())
        else:
            # Auto-detect repository root and then find source directory
            repo_root = find_repository_root(".")
            src_dir = find_src_directory(repo_root)
            repo_path = src_dir

        # Find the source directory if not already set
        if "src_dir" not in locals():
            src_dir = find_src_directory(repo_path)

    # Get copyright information (always from repository root)
    year, name, email = get_copyright_info(repo_path)

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
                print(f"Matched licenses: {len(matching_licenses)} of {total_licenses} total")
            else:
                print(f"Total licenses: {total_licenses}")
            print("\nLicenses:")

            for license_key, details in matching_licenses:
                deprecated = " (deprecated)" if details.get("deprecated", False) else ""
                osi = " [OSI]" if details.get("osi_approved", False) else ""
                fsf = " [FSF]" if details.get("fsf_libre", False) else ""
                print(f"- {license_key}{deprecated}{osi}{fsf}: {details.get('name', '')}")
        else:
            if keyword:
                print(f"No licenses found matching keyword '{keyword}'.")
            else:
                print("No licenses available.")
        return 0
    elif args.add:
        if target_mode == "file":
            add_header_to_single_file(
                target_file, args.add, license_data, year, name, email, args.dry_run
            )
        else:
            add_header_to_py_files(
                src_dir, args.add, license_data, year, name, email, args.dry_run
            )

        # If extract is also specified, extract the license file
        if extract_arg is not None:
            target_license = args.add if extract_arg == "" else extract_arg
            extract_license(target_license, license_data, repo_path, args.dry_run)
        return 0
    elif args.change:
        if target_mode == "file":
            change_header_in_single_file(
                target_file, args.change, license_data, year, name, email, args.dry_run
            )
        else:
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
        if target_mode == "file":
            remove_header_from_single_file(target_file, args.dry_run)
        else:
            remove_header_from_py_files(src_dir, args.dry_run)
        return 0
    elif args.verify:
        if target_mode == "file":
            verify_spdx_header_in_single_file(target_file)
        else:
            verify_spdx_headers(src_dir)
        return 0
    elif args.check:
        if target_mode == "file":
            # For single file checking, we check if header is present
            if has_spdx_header(target_file):
                print(f"\u2713 Valid SPDX header found in: {target_file}")
                exit_code = 0
            else:
                print(f"\u2717 Missing SPDX header in: {target_file}")
                exit_code = 1

            if exit_code != 0 and args.fix:
                # Use MIT as default license for --check --fix
                license_to_use = "MIT"
                add_header_to_single_file(
                    target_file, license_to_use, license_data, year, name, email, args.dry_run
                )
                if not args.dry_run:
                    # Re-check after fixing
                    if has_spdx_header(target_file):
                        print(f"\u2713 Fixed: Added SPDX header to: {target_file}")
                        exit_code = 0
        else:
            exit_code = check_headers(src_dir)
            if exit_code != 0 and args.fix:
                success = auto_fix_headers(src_dir, license_data, year, name, email, args.dry_run)
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
