# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
File operations for SPDX header management.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
from pathlib import Path
from typing import Any, Callable, Union
from urllib.parse import quote_plus

from .core import (
    LICENSE_PATTERN,
    FileProcessor,
    create_header,
    find_python_files,
    has_spdx_header,
)
from .data import LicenseData, LicenseEntry
from .encoding import read_file_with_encoding, write_file_with_encoding
from .exceptions import (
    EncodingError,
    FileProcessingError,
    LicenseNotFoundError,
    find_similar_licenses,
)

PathLike = Union[str, Path]
OpenEditorCallback = Callable[[Path], None]


def _build_license_placeholder(license_key: str, license_name: str) -> str:
    encoded_key = quote_plus(license_key)
    return (
        f"{license_name} ({license_key})\n"
        "\n"
        "The full license text is not bundled with this tool.\n"
        "Refer to the official SPDX listing for the authoritative text:\n"
        f"https://spdx.org/licenses/{encoded_key}.html\n"
    )


def _resolve_license_text(license_key: str, license_entry: LicenseEntry) -> str | None:
    """Return the full license text from cached data or by downloading it."""
    cached_text = license_entry.get("license_text")
    if isinstance(cached_text, str) and cached_text.strip():
        return cached_text

    try:
        import requests
    except ImportError:
        return None

    text_url = (
        "https://raw.githubusercontent.com/spdx/license-list-data/main/text/"
        f"{quote_plus(license_key)}.txt"
    )

    try:
        response = requests.get(text_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return None

    return response.text


_BULLET_PATTERN = re.compile(r"^(([-*•]|[0-9]+\.)\s+)")


def _wrap_license_text(text: str, width: int = 79) -> str:
    """Hard-wrap license text while preserving blank lines and indentation."""
    has_trailing_newline = text.endswith("\n")

    def flush_paragraph(buffer: list[str]) -> list[str]:
        if not buffer:
            return []

        first_line = buffer[0]
        indent_match = re.match(r"^\s*", first_line)
        indent = indent_match.group(0) if indent_match else ""
        stripped_lines = [line.strip() for line in buffer]
        paragraph_text = " ".join(stripped_lines)

        wrapper_kwargs: dict[str, Any] = {
            "width": width,
            "break_long_words": False,
            "break_on_hyphens": False,
        }

        first_after_indent = first_line[len(indent) :]
        bullet_match = _BULLET_PATTERN.match(first_after_indent)

        if bullet_match:
            bullet_prefix = indent + bullet_match.group(1)
            wrapper_kwargs.update(
                initial_indent=bullet_prefix,
                subsequent_indent=indent + " " * len(bullet_match.group(1)),
            )
            paragraph_text = paragraph_text[len(bullet_match.group(1)) :].lstrip()
            if not paragraph_text:
                return [bullet_prefix.rstrip()]
        elif indent:
            wrapper_kwargs.update(initial_indent=indent, subsequent_indent=indent)

        wrapper = textwrap.TextWrapper(**wrapper_kwargs)
        return wrapper.fill(paragraph_text).splitlines()

    lines = text.replace("\r\n", "\n").split("\n")
    wrapped_lines: list[str] = []
    paragraph: list[str] = []

    for line in lines:
        if not line.strip():
            wrapped_lines.extend(flush_paragraph(paragraph))
            paragraph = []
            wrapped_lines.append("")
            continue

        paragraph.append(line)

    wrapped_lines.extend(flush_paragraph(paragraph))

    result = "\n".join(wrapped_lines)
    if has_trailing_newline and not result.endswith("\n"):
        result += "\n"
    return result


def check_missing_headers(directory: PathLike, dry_run: bool = False) -> list[str]:
    """
    Check for Python files missing SPDX headers.
    Returns list of files without headers.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        print(f"Error: The directory '{directory}' does not exist.")
        raise FileNotFoundError(directory)

    missing_headers: list[str] = []
    python_files = find_python_files(directory)

    for filepath in python_files:
        if not has_spdx_header(filepath):
            missing_headers.append(filepath)
            if dry_run:
                print(f"Missing SPDX header: {filepath}")

    return missing_headers


def _collect_license_identifiers(directory: PathLike) -> list[tuple[str, str]]:
    identifiers: list[tuple[str, str]] = []
    for filepath in find_python_files(directory):
        if not has_spdx_header(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as file_handle:
                for line in file_handle:
                    match = LICENSE_PATTERN.search(line)
                    if match:
                        identifiers.append((filepath, match.group("identifier")))
                        break
        except OSError:
            continue
    return identifiers


def auto_fix_headers(
    directory: PathLike,
    license_data: LicenseData,
    year: str,
    name: str,
    email: str,
    dry_run: bool = False,
) -> bool:
    """Attempt to add missing headers by inferring a single license identifier."""

    missing_files = check_missing_headers(directory, dry_run=True)
    if not missing_files:
        print("✓ No missing SPDX headers detected – nothing to fix.")
        return True

    identifiers = _collect_license_identifiers(directory)
    unique_identifiers = {identifier for _, identifier in identifiers}

    if not unique_identifiers:
        print("✗ Unable to determine an SPDX license to apply automatically.")
        return False

    if len(unique_identifiers) > 1:
        print(
            "✗ Multiple SPDX licenses detected. "
            "Specify a license explicitly with --add or --change."
        )
        return False

    inferred_license = next(iter(unique_identifiers))
    if inferred_license not in license_data["licenses"]:
        print(f"✗ Inferred license '{inferred_license}' is not present in loaded license data.")
        return False

    print(f"Attempting to add SPDX headers using inferred license '{inferred_license}'.")
    add_header_to_py_files(
        directory, inferred_license, license_data, year, name, email, dry_run=dry_run
    )

    remaining = check_missing_headers(directory, dry_run=True)
    if not remaining:
        print("✓ Successfully added missing SPDX headers.")
        return True

    print("✗ Some files are still missing SPDX headers. Review the output above for details.")
    return False


def add_header_to_single_file(
    filepath: PathLike,
    license_key: str,
    license_data: LicenseData,
    year: str,
    name: str,
    email: str,
    dry_run: bool = False,
) -> None:
    """Add SPDX header to a single Python file.

    Args:
        filepath: Path to the Python file
        license_key: SPDX license identifier
        license_data: License database
        year: Copyright year
        name: Copyright holder name
        email: Copyright holder email
        dry_run: If True, show what would be done without making changes
    """
    # Validate license exists
    if license_key not in license_data["licenses"]:
        available_licenses = list(license_data["licenses"].keys())
        suggestions = find_similar_licenses(license_key, available_licenses)
        raise LicenseNotFoundError(license_key, suggestions)

    header_to_add = create_header(license_data, license_key, year, name, email)
    if header_to_add is None:
        raise FileProcessingError(
            filepath,
            f"No header template available for '{license_key}'",
            "Check the license data file or update it with 'spdx-headers --update'",
        )

    # Check if file already has header
    if has_spdx_header(filepath):
        if not dry_run:
            print(f"ℹ️  File already has SPDX header: {filepath}")
        else:
            print(f"ℹ️  File already has SPDX header: {filepath}")
        return

    if dry_run:
        print(f"Would add header to: {filepath}")
    else:
        try:
            # Read file with encoding detection
            lines, encoding = read_file_with_encoding(Path(filepath))

            # Check for shebang line
            shebang = ""
            if lines and lines[0].startswith("#!"):
                shebang = lines[0]
                lines = lines[1:]

            # Insert the header
            new_content = shebang + header_to_add + "".join(lines)

            # Write back with detected encoding
            write_file_with_encoding(Path(filepath), [new_content], encoding)
            print(f"✅ Added header to: {filepath}")

        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")


def change_header_in_single_file(
    filepath: PathLike,
    license_key: str,
    license_data: LicenseData,
    year: str,
    name: str,
    email: str,
    dry_run: bool = False,
) -> None:
    """Change SPDX header in a single Python file.

    Args:
        filepath: Path to the Python file
        license_key: SPDX license identifier
        license_data: License database
        year: Copyright year
        name: Copyright holder name
        email: Copyright holder email
        dry_run: If True, show what would be done without making changes
    """
    # Validate license exists
    if license_key not in license_data["licenses"]:
        print(f"Error: License keyword '{license_key}' is not supported.")
        return

    # Check if file has header to change
    if not has_spdx_header(filepath):
        if dry_run:
            print(f"Would skip (no header to change): {filepath}")
        else:
            print(f"u2139ufe0f File has no SPDX header to change: {filepath}")
        return

    header_to_add = create_header(license_data, license_key, year, name, email)
    if header_to_add is None:
        print(f"Error: No header template available for '{license_key}'.")
        return

    if dry_run:
        print(f"Would change header in: {filepath}")
    else:
        try:
            # Single-pass processing with atomic write
            processor = FileProcessor(filepath)
            processor.load()

            if processor.has_header():
                processor.add_header(header_to_add)
                processor.save()
                print(f"u2713 Changed header in: {filepath}")
            else:
                print(f"u2139ufe0f File has no SPDX header to change: {filepath}")

        except Exception as e:
            print(f"u274c Error processing {filepath}: {e}")


def remove_header_from_single_file(
    filepath: PathLike,
    dry_run: bool = False,
) -> None:
    """Remove SPDX header from a single Python file.

    Args:
        filepath: Path to the Python file
        dry_run: If True, show what would be done without making changes
    """
    # Check if file has header to remove
    if not has_spdx_header(filepath):
        if dry_run:
            print(f"Would skip (no header to remove): {filepath}")
        else:
            print(f"u2139ufe0f File has no SPDX header to remove: {filepath}")
        return

    if dry_run:
        print(f"Would remove header from: {filepath}")
    else:
        try:
            # Single-pass processing with atomic write
            processor = FileProcessor(filepath)
            processor.load()

            if processor.has_header():
                processor.remove_header()
                processor.save()
                print(f"u2713 Removed header from: {filepath}")
            else:
                print(f"u2139ufe0f File has no SPDX header to remove: {filepath}")

        except Exception as e:
            print(f"u274c Error processing {filepath}: {e}")


def verify_spdx_header_in_single_file(
    filepath: PathLike,
) -> None:
    """Verify SPDX header in a single Python file.

    Args:
        filepath: Path to the Python file
    """
    if has_spdx_header(filepath):
        print(f"u2713 Valid SPDX header found in: {filepath}")
    else:
        print(f"u2717 Missing SPDX header in: {filepath}")


def verify_spdx_headers(directory: PathLike) -> None:
    """Verify SPDX headers in all Python files."""
    missing_files = check_missing_headers(directory)

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

    identifiers_with_files = _collect_license_identifiers(directory)
    identifiers = sorted({identifier for _, identifier in identifiers_with_files})

    if identifiers:
        if len(identifiers) > 1:
            print("Detected SPDX license identifiers:")
            for path, identifier in sorted(identifiers_with_files):
                print(f"  - {path} - {identifier}")
        else:
            print(f"Detected SPDX license identifier: {identifiers[0]}")
    else:
        print("Detected SPDX license identifiers: none found.")

    if not missing_files:
        print("✓ All Python files have valid SPDX headers.")
        return 0
    else:
        print("✗ The following files are missing SPDX headers:")
        for file in missing_files:
            print(f"  - {file}")
        print(f"\nFound {len(missing_files)} files without SPDX headers.")
        return 1


def add_header_to_py_files(
    directory: PathLike,
    license_key: str,
    license_data: LicenseData,
    year: str,
    name: str,
    email: str,
    dry_run: bool = False,
) -> None:
    """Add SPDX headers to Python files with improved error handling.

    Args:
        directory: Directory containing Python files to process
        license_key: SPDX license identifier (e.g., 'MIT', 'Apache-2.0')
        license_data: License database containing license information
        year: Copyright year
        name: Copyright holder name
        email: Copyright holder email
        dry_run: If True, show what would be done without making changes

    Raises:
        LicenseNotFoundError: If the license_key is not in the database
        FileProcessingError: If header template is not available
        EncodingError: If file encoding cannot be determined
    """
    # Validate license exists
    if license_key not in license_data["licenses"]:
        # Find similar licenses
        available_licenses = list(license_data["licenses"].keys())
        suggestions = find_similar_licenses(license_key, available_licenses)
        raise LicenseNotFoundError(license_key, suggestions)

    header_to_add = create_header(license_data, license_key, year, name, email)
    if header_to_add is None:
        raise FileProcessingError(
            directory,
            f"No header template available for '{license_key}'",
            "Check the license data file or update it with 'spdx-headers --update'",
        )

    python_files = find_python_files(directory)

    files_to_modify: list[str] = []
    errors: list[tuple[str, str]] = []

    for filepath in python_files:
        # Quick check without loading full file
        if has_spdx_header(filepath):
            continue

        if dry_run:
            print(f"Would add header to: {filepath}")
            files_to_modify.append(filepath)
        else:
            try:
                # Read file with encoding detection
                lines, encoding = read_file_with_encoding(Path(filepath))

                # Check for shebang line
                shebang = ""
                if lines and lines[0].startswith("#!"):
                    shebang = lines.pop(0)

                # Prepare new content
                new_lines: list[str] = []
                if shebang:
                    new_lines.append(shebang)
                new_lines.extend(header_to_add.splitlines(keepends=True))
                new_lines.extend(lines)

                # Write back to file with same encoding
                write_file_with_encoding(Path(filepath), new_lines, encoding)
                print(f"✓ Added header to: {filepath}")
                files_to_modify.append(filepath)

            except EncodingError as exc:
                error_msg = f"Encoding error: {exc.reason}"
                errors.append((filepath, error_msg))
                print(f"✗ {filepath}: {error_msg}")

            except (OSError, PermissionError) as exc:
                error_msg = str(exc)
                errors.append((filepath, error_msg))
                print(f"✗ Error processing '{filepath}': {error_msg}")

    if dry_run and files_to_modify:
        print(f"\nWould modify {len(files_to_modify)} files")

    if errors:
        print(f"\n⚠ Encountered {len(errors)} errors during processing")
        print("Run with --verbose for more details")


def change_header_in_py_files(
    directory: PathLike,
    license_key: str,
    license_data: LicenseData,
    year: str,
    name: str,
    email: str,
    dry_run: bool = False,
) -> None:
    """Change SPDX headers in Python files using single-pass processing."""
    if license_key not in license_data["licenses"]:
        print(f"Error: License keyword '{license_key}' is not supported.")
        return

    header_to_add = create_header(license_data, license_key, year, name, email)
    if header_to_add is None:
        print(f"Error: No header template available for '{license_key}'.")
        return
    python_files = find_python_files(directory)

    files_to_modify: list[str] = []

    for filepath in python_files:
        # Quick check without loading full file
        if not has_spdx_header(filepath):
            continue

        if dry_run:
            print(f"Would change header in: {filepath}")
            files_to_modify.append(filepath)
        else:
            try:
                # Single-pass processing with atomic write
                processor = FileProcessor(filepath)
                processor.load()

                if processor.has_header():
                    processor.add_header(header_to_add)
                    processor.save()
                    print(f"✓ Changed header in: {filepath}")
                    files_to_modify.append(filepath)
                else:
                    print(f"⚠ No SPDX header found in: {filepath}")

            except OSError as exc:
                print(f"✗ Error processing file '{filepath}': {exc}")

    if dry_run and files_to_modify:
        print(f"\nWould modify {len(files_to_modify)} files")


def remove_header_from_py_files(directory: PathLike, dry_run: bool = False) -> None:
    """Remove SPDX headers from Python files using single-pass processing."""
    python_files = find_python_files(directory)

    files_to_modify: list[str] = []

    for filepath in python_files:
        # Quick check without loading full file
        if not has_spdx_header(filepath):
            continue

        if dry_run:
            print(f"Would remove header from: {filepath}")
            files_to_modify.append(filepath)
        else:
            try:
                # Single-pass processing with atomic write
                processor = FileProcessor(filepath)
                processor.load()

                if processor.has_header():
                    processor.remove_header()
                    processor.save()
                    print(f"✓ Removed header from: {filepath}")
                    files_to_modify.append(filepath)
                else:
                    print(f"⚠ No SPDX header found in: {filepath}")

            except OSError as exc:
                print(f"✗ Error processing file '{filepath}': {exc}")

    if dry_run and files_to_modify:
        print(f"\nWould modify {len(files_to_modify)} files")


def filter_licenses(
    license_data: LicenseData, keyword: str | None = None
) -> list[tuple[str, LicenseEntry]]:
    """Return a sorted list of licenses optionally filtered by keyword."""
    sorted_licenses = sorted(license_data["licenses"].items(), key=lambda item: item[0])

    if not keyword:
        return sorted_licenses

    keyword_lower = keyword.lower()
    filtered = [
        (license_key, details)
        for license_key, details in sorted_licenses
        if keyword_lower in license_key.lower() or keyword_lower in details.get("name", "").lower()
    ]
    return filtered


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

    license_text = _resolve_license_text(license_key, license_info)
    used_placeholder = False

    if not license_text:
        used_placeholder = True
        license_text = _build_license_placeholder(license_key, license_name)

    target_path = Path(repo_path)
    preferred_path = target_path / "LICENSE"
    preferred_exists = preferred_path.exists()
    license_file_path = (
        preferred_path if not preferred_exists else target_path / f"LICENSE-{license_key}"
    )

    if dry_run:
        print(f"Would extract license to: {license_file_path}")
        if preferred_exists:
            print("  (existing LICENSE detected; using suffixed filename)")
        if used_placeholder:
            print("  (placeholder text; unable to retrieve full license text)")
    else:
        formatted_text = _wrap_license_text(license_text)
        try:
            with open(license_file_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(formatted_text)
            print(f"✓ Extracted license to: {license_file_path}")
            if preferred_exists:
                print("Info: Existing LICENSE preserved; wrote suffixed file instead.")
            if used_placeholder:
                print("⚠ Full license text unavailable – placeholder file was generated.")
        except OSError as exc:
            print(f"✗ Error extracting license to '{license_file_path}': {exc}")


def _default_open_editor(path: Path) -> None:
    """Open the given path with the system default editor/viewer."""
    if sys.platform.startswith("darwin"):
        try:
            subprocess.run(["open", str(path)], check=True)
        except subprocess.CalledProcessError as exc:
            raise OSError(f"'open' failed with exit code {exc.returncode}") from exc
        else:
            return

    if os.name == "nt":
        startfile = getattr(os, "startfile", None)
        if startfile is None:  # pragma: no cover - defensive
            raise OSError("Opening files is not supported on this platform.")
        try:
            startfile(str(path))
        except OSError as exc:  # pragma: no cover - Windows only
            raise OSError("Launching default application failed.") from exc
        return

    opener = shutil.which("xdg-open") or shutil.which("gio") or shutil.which("wslview")
    if opener:
        try:
            subprocess.run([opener, str(path)], check=True)
        except subprocess.CalledProcessError as exc:
            raise OSError(f"'{opener}' failed with exit code {exc.returncode}") from exc
        return

    raise OSError("Could not determine a method to open files on this system.")


def show_license(
    license_key: str,
    license_data: LicenseData,
    open_in_editor: OpenEditorCallback | None = None,
    cleanup_delay: float | None = 30.0,
) -> None:
    """Display the selected license text using the system's default editor."""
    if license_key not in license_data["licenses"]:
        print(f"Error: License keyword '{license_key}' is not supported.")
        return

    license_info = license_data["licenses"][license_key]
    license_name = license_info.get("name", license_key)

    license_text = _build_license_placeholder(license_key, license_name)

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=f"-{license_key}.txt", delete=False
    ) as tmp_file:
        tmp_file.write(license_text)
        temp_path = Path(tmp_file.name)

    opener = open_in_editor or _default_open_editor

    timer: threading.Timer | None = None
    try:
        opener(temp_path)
        if cleanup_delay is not None:
            timer = threading.Timer(cleanup_delay, temp_path.unlink, kwargs={"missing_ok": True})
            timer.start()
    except OSError as exc:
        print(f"✗ Error opening license viewer: {exc}")
        temp_path.unlink(missing_ok=True)
        if timer is not None:
            timer.cancel()
    else:
        print(f"✓ Displaying license '{license_key}' in the default editor.")
        if cleanup_delay is None:
            print(f"  Temporary file preserved at: {temp_path}")
