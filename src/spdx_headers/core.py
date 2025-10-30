#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
A command-line tool for managing SPDX headers in Python source files.

This script can add, remove, change, or verify SPDX headers in all Python files
within a repository's source directory. It supports pre-commit hook integration
for automated compliance checking.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path
from typing import List, Tuple, Union

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    try:
        import tomli as tomllib
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive guard
        raise ModuleNotFoundError(
            "tomli is required when running on Python < 3.11. "
            "Install it with 'pip install tomli'."
        ) from exc

from .data import DEFAULT_DATA_FILE, LicenseData
from .data import load_license_data as _load_license_data
from .data import update_license_data as _update_license_data

PathLike = Union[str, Path]


def load_license_data(data_file_path: PathLike | None = None) -> LicenseData:
    """Load the SPDX license data from the JSON file."""
    return _load_license_data(data_file_path)


def update_license_data(data_file_path: PathLike | None = None) -> None:
    """Update the SPDX license data file by downloading from the official source."""
    _update_license_data(data_file_path)


def find_src_directory(repo_path: PathLike) -> str:
    """Find the source directory in the repository."""
    base_path = Path(repo_path)
    candidate_dirs = [base_path / "src", base_path / "lib", base_path]

    for candidate in candidate_dirs:
        if candidate.is_dir() and any(candidate.rglob("*.py")):
            return str(candidate)

    return str(base_path)


def get_copyright_info(repo_path: PathLike) -> Tuple[str, str, str]:
    """Get copyright information from pyproject.toml if available."""
    copyright_year = str(datetime.date.today().year)
    copyright_name = "John Doe"
    copyright_email = "jdoe@geocities.com"

    pyproject_path = Path(repo_path) / "pyproject.toml"

    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as file_handle:
                pyproject_data = tomllib.load(file_handle)

            project_section = pyproject_data.get("project", {})
            authors = project_section.get("authors", [])
            if isinstance(authors, list) and authors:
                first_author = authors[0]
                if isinstance(first_author, dict):
                    name_candidate = first_author.get("name", copyright_name)
                    if isinstance(name_candidate, str) and name_candidate:
                        copyright_name = name_candidate
                    email_candidate = first_author.get("email", copyright_email)
                    if isinstance(email_candidate, str) and email_candidate:
                        copyright_email = email_candidate
        except Exception as exc:  # pragma: no cover - defensive guard
            print(f"Warning: Could not read pyproject.toml: {exc}")

    return copyright_year, copyright_name, copyright_email


def find_python_files(directory: PathLike) -> List[str]:
    """Find all Python files in the directory."""
    python_files: List[str] = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".py"):
                python_files.append(os.path.join(root, filename))
    return python_files


def has_spdx_header(filepath: PathLike) -> bool:
    """Check if a file has an SPDX header."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            content = file_handle.read(512)  # Read first 512 chars
        return (
            "SPDX-FileCopyrightText" in content and "SPDX-License-Identifier" in content
        )
    except OSError:
        return False


def extract_spdx_header(filepath: PathLike) -> List[str]:
    """Extract the SPDX header from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()

        header_lines: List[str] = []
        in_header = False

        for line in lines:
            if "SPDX-FileCopyrightText" in line or "SPDX-License-Identifier" in line:
                in_header = True

            if in_header:
                header_lines.append(line)
                # Stop after the license identifier and any following blank lines
                if "SPDX-License-Identifier" in line:
                    # Include any blank lines after the header
                    continue
                elif line.strip() == "" and header_lines:
                    continue
                elif line.strip() != "" and "SPDX-" not in line:
                    break

        return header_lines
    except OSError:
        return []


def remove_spdx_header(filepath: PathLike) -> Tuple[List[str], bool]:
    """Remove the SPDX header from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()

        # Find the end of the SPDX header
        new_lines: List[str] = []
        skip_until_content = False
        found_header = False

        for line in lines:
            if "SPDX-FileCopyrightText" in line or "SPDX-License-Identifier" in line:
                found_header = True
                skip_until_content = True
                continue

            if skip_until_content:
                if line.strip() == "" or line.startswith("#"):
                    continue
                else:
                    skip_until_content = False

            if not skip_until_content:
                new_lines.append(line)

        return new_lines, found_header
    except OSError:
        return [], False


def check_missing_headers(directory: PathLike, dry_run: bool = False) -> List[str]:
    """
    Check for Python files missing SPDX headers.
    Returns list of files without headers.
    """
    if not os.path.isdir(directory):
        message = f"Error: The directory '{directory}' does not exist."
        print(message)
        raise FileNotFoundError(message)

    missing_headers: List[str] = []
    python_files = find_python_files(directory)

    for filepath in python_files:
        if not has_spdx_header(filepath):
            missing_headers.append(filepath)
            if dry_run:
                print(f"Missing SPDX header: {filepath}")

    return missing_headers


def verify_spdx_headers(directory: PathLike) -> None:
    """Verify SPDX headers in all Python files."""
    try:
        missing_files = check_missing_headers(directory)
    except FileNotFoundError:
        print("✗ Unable to verify SPDX headers.")
        return

    if not missing_files:
        print("✓ All Python files have valid SPDX headers.")
    else:
        print("✗ The following files are missing SPDX headers:")
        for file in missing_files:
            print(f"  - {file}")
        print(f"\nFound {len(missing_files)} files without SPDX headers.")


def check_headers(directory: PathLike) -> int:
    """
    Check for missing headers and return appropriate exit code for pre-commit hooks.
    Returns 0 if all files have headers, 1 if any are missing.
    """
    try:
        missing_files = check_missing_headers(directory)
    except FileNotFoundError:
        return 1

    if not missing_files:
        print("✓ All Python files have valid SPDX headers.")
        return 0
    else:
        print("✗ The following files are missing SPDX headers:")
        for file in missing_files:
            print(f"  - {file}")
        print(f"\nFound {len(missing_files)} files without SPDX headers.")
        return 1


def create_header(
    license_data: LicenseData,
    license_key: str,
    year: str,
    name: str,
    email: str,
) -> str | None:
    """Create a header for the specified license with copyright information."""
    if license_key not in license_data["licenses"]:
        return None

    license_entry = license_data["licenses"][license_key]
    template = license_entry["header_template"]
    return template.format(
        year=year,
        name=name,
        email=email,
        license_name=license_entry.get("name", "").strip(),
    )


def add_header_to_py_files(
    directory: PathLike,
    license_key: str,
    license_data: LicenseData,
    year: str,
    name: str,
    email: str,
    dry_run: bool = False,
) -> None:
    """Add SPDX headers to Python files, optionally in dry-run mode."""
    if license_key not in license_data["licenses"]:
        print(f"Error: License keyword '{license_key}' is not supported.")
        return

    header_to_add = create_header(license_data, license_key, year, name, email)
    if header_to_add is None:
        print(f"Error: No header template available for '{license_key}'.")
        return
    python_files = find_python_files(directory)

    files_to_modify: List[str] = []

    for filepath in python_files:
        if has_spdx_header(filepath):
            continue

        if dry_run:
            print(f"Would add header to: {filepath}")
            files_to_modify.append(filepath)
        else:
            try:
                with open(filepath, "r", encoding="utf-8") as file_handle:
                    lines = file_handle.readlines()

                # Check for shebang line
                shebang = ""
                if lines and lines[0].startswith("#!"):
                    shebang = lines.pop(0)

                # Prepare new content
                new_lines: List[str] = []
                if shebang:
                    new_lines.append(shebang)
                new_lines.extend(header_to_add.splitlines(keepends=True))
                new_lines.extend(lines)

                # Write back to file
                with open(filepath, "w", encoding="utf-8") as file_handle:
                    file_handle.writelines(new_lines)
                print(f"✓ Added header to: {filepath}")
                files_to_modify.append(filepath)

            except OSError as exc:
                print(f"✗ Error processing file '{filepath}': {exc}")

    if dry_run and files_to_modify:
        print(f"\nWould modify {len(files_to_modify)} files")


def change_header_in_py_files(
    directory: PathLike,
    license_key: str,
    license_data: LicenseData,
    year: str,
    name: str,
    email: str,
    dry_run: bool = False,
) -> None:
    """Change SPDX headers in Python files to a new license."""
    if license_key not in license_data["licenses"]:
        print(f"Error: License keyword '{license_key}' is not supported.")
        return

    header_to_add = create_header(license_data, license_key, year, name, email)
    if header_to_add is None:
        print(f"Error: No header template available for '{license_key}'.")
        return
    python_files = find_python_files(directory)

    files_to_modify: List[str] = []

    for filepath in python_files:
        if not has_spdx_header(filepath):
            continue

        if dry_run:
            print(f"Would change header in: {filepath}")
            files_to_modify.append(filepath)
        else:
            try:
                # Remove existing header
                new_lines, had_header = remove_spdx_header(filepath)

                if had_header:
                    # Check for shebang line
                    shebang = ""
                    if new_lines and new_lines[0].startswith("#!"):
                        shebang = new_lines.pop(0)

                    # Prepare new content
                    final_lines = []
                    if shebang:
                        final_lines.append(shebang)
                    final_lines.extend(header_to_add.splitlines(keepends=True))
                    final_lines.extend(new_lines)

                    # Write back to file
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.writelines(final_lines)
                    print(f"✓ Changed header in: {filepath}")
                    files_to_modify.append(filepath)
                else:
                    print(f"⚠ No SPDX header found in: {filepath}")

            except OSError as exc:
                print(f"✗ Error processing file '{filepath}': {exc}")

    if dry_run and files_to_modify:
        print(f"\nWould modify {len(files_to_modify)} files")


def remove_header_from_py_files(directory: PathLike, dry_run: bool = False) -> None:
    """Remove SPDX headers from Python files."""
    python_files = find_python_files(directory)

    files_to_modify: List[str] = []

    for filepath in python_files:
        if not has_spdx_header(filepath):
            continue

        if dry_run:
            print(f"Would remove header from: {filepath}")
            files_to_modify.append(filepath)
        else:
            try:
                new_lines, had_header = remove_spdx_header(filepath)

                if had_header:
                    # Write back to file
                    with open(filepath, "w", encoding="utf-8") as file_handle:
                        file_handle.writelines(new_lines)
                    print(f"✓ Removed header from: {filepath}")
                    files_to_modify.append(filepath)
                else:
                    print(f"⚠ No SPDX header found in: {filepath}")

            except OSError as exc:
                print(f"✗ Error processing file '{filepath}': {exc}")

    if dry_run and files_to_modify:
        print(f"\nWould modify {len(files_to_modify)} files")


def extract_license(
    license_key: str,
    license_data: LicenseData,
    repo_path: PathLike,
    dry_run: bool = False,
) -> None:
    """Extract the license text to the repository root."""
    if license_key not in license_data["licenses"]:
        print(f"Error: License keyword '{license_key}' is not supported.")
        return

    # Get the license text from the SPDX data
    license_info = license_data["licenses"][license_key]
    license_name = license_info.get("name", license_key)

    # Create a simple license file
    license_text = f"""SPDX-License-Identifier: {license_key}

{license_name}
"""

    license_file_path = Path(repo_path) / f"LICENSE-{license_key}"

    if dry_run:
        print(f"Would extract license to: {license_file_path}")
    else:
        try:
            with open(license_file_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(license_text)
            print(f"✓ Extracted license to: {license_file_path}")
        except OSError as exc:
            print(f"✗ Error extracting license to '{license_file_path}': {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage SPDX headers in Python source files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -a GPL-3.0-only -p /path/to/repo
  %(prog)s -c MIT -p /path/to/repo --dry-run
  %(prog)s -v -p /path/to/repo
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

    # Extract option can be combined with add or change
    parser.add_argument(
        "-e",
        "--extract",
        action="store_true",
        help="Extract the license file to the repository root. Can be combined with -a or -c.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making modifications.",
    )

    parser.add_argument(
        "-l", "--list", action="store_true", help="List available license keywords."
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
        return

    # Load the license data
    license_data = load_license_data(args.data_file)

    # Use the specified repository path
    repo_path = os.path.abspath(args.path)

    # Get copyright information
    year, name, email = get_copyright_info(repo_path)

    # Find the source directory
    src_dir = find_src_directory(repo_path)

    if args.list:
        print("Available license keywords:")
        print(f"SPDX version: {license_data['metadata']['spdx_version']}")
        print(f"Generated: {license_data['metadata']['generated_at']}")
        print(f"Total licenses: {license_data['metadata']['license_count']}")
        print("\nLicenses:")

        # Sort licenses by identifier
        sorted_licenses = sorted(license_data["licenses"].items(), key=lambda x: x[0])

        for license_key, details in sorted_licenses:
            deprecated = " (deprecated)" if details.get("deprecated", False) else ""
            osi = " [OSI]" if details.get("osi_approved", False) else ""
            fsf = " [FSF]" if details.get("fsf_libre", False) else ""
            print(f"- {license_key}{deprecated}{osi}{fsf}: {details.get('name', '')}")

    elif args.add:
        add_header_to_py_files(
            src_dir, args.add, license_data, year, name, email, args.dry_run
        )
        # If extract is also specified, extract the license file
        if args.extract:
            extract_license(args.add, license_data, repo_path, args.dry_run)
    elif args.change:
        change_header_in_py_files(
            src_dir, args.change, license_data, year, name, email, args.dry_run
        )
        # If extract is also specified, extract the license file
        if args.extract:
            extract_license(args.change, license_data, repo_path, args.dry_run)
    elif args.remove:
        remove_header_from_py_files(src_dir, args.dry_run)
    elif args.verify:
        verify_spdx_headers(src_dir)
    elif args.check:
        exit_code = check_headers(src_dir)
        sys.exit(exit_code)
    elif args.extract:
        # If only extract is specified, show an error
        print("Error: The --extract option must be used with either --add or --change.")
        parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
