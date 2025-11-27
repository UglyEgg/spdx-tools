#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Core functionality for managing SPDX headers in Python source files.

This module provides the foundational functions for SPDX header management,
including file discovery, header detection, and copyright information extraction.
The actual header manipulation operations are in the operations module.
"""

from __future__ import annotations

import configparser
import datetime
import os
import re
import shutil
import tempfile
from pathlib import Path

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

from .data import LicenseData
from .data import load_license_data as _load_license_data
from .data import update_license_data as _update_license_data

PathLike = str | Path

EXCLUDED_FILENAMES = {"_version.py"}
CONFIG_FILENAME = ".spdx-headers.ini"


def _load_exclusions(directory: PathLike) -> set[str]:
    config = configparser.ConfigParser()
    config_path = Path(directory) / CONFIG_FILENAME

    exclusions = set(EXCLUDED_FILENAMES)
    if config_path.is_file():
        config.read(config_path)
        values = config.get("spdx-headers", "exclude", fallback="").split()
        exclusions.update(value.strip() for value in values if value.strip())
    return exclusions


LICENSE_PATTERN = re.compile(
    r"SPDX-License-Identifier:\s*(?P<identifier>[\w\.\-+/:]+)", re.IGNORECASE
)


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


def get_copyright_info(repo_path: PathLike) -> tuple[str, str, str]:
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


def find_python_files(directory: PathLike) -> list[str]:
    """Find all Python files in the directory."""
    python_files: list[str] = []
    exclusions = _load_exclusions(directory)
    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.endswith(".py"):
                continue
            if filename in exclusions:
                continue
            python_files.append(os.path.join(root, filename))
    return python_files


def has_spdx_header(filepath: PathLike) -> bool:
    """Return True if the file contains an SPDX license identifier near the top."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            content = file_handle.read(2048)
    except OSError:
        return False

    return bool(LICENSE_PATTERN.search(content))


def _extract_spdx_header_from_lines(lines: list[str]) -> list[str]:
    header_candidates: list[str] = []
    spdx_found = False

    for index, line in enumerate(lines):
        if index == 0 and line.startswith("#!"):
            continue

        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            if "SPDX" in line:
                spdx_found = True
            if spdx_found or stripped.startswith("#"):
                header_candidates.append(line)
            else:
                break
        else:
            break

    return header_candidates if spdx_found else []


def extract_spdx_header(filepath: PathLike) -> list[str]:
    """Extract the SPDX header from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()
        return _extract_spdx_header_from_lines(lines)
    except OSError:
        return []


def remove_spdx_header(filepath: PathLike) -> tuple[list[str], bool]:
    """Remove SPDX header from file, return new lines and whether header was found."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()

        header_lines = _extract_spdx_header_from_lines(lines)
        if header_lines:
            header_length = len(header_lines)
            index = 0
            for i, line in enumerate(lines):
                if line in header_lines:
                    index = i
                    break

            new_lines: list[str] = []
            prefix_end = 1 if (lines and lines[0].startswith("#!")) else 0
            new_lines.extend(lines[:prefix_end])
            new_lines.extend(lines[index + header_length :])
            return new_lines, True

        return lines, False
    except OSError:
        return [], False


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
    context = {
        "year": year,
        "name": name,
        "email": email,
        "license_name": license_entry.get("name", "").strip(),
        "license_key": license_key,
    }

    template = license_entry.get("header_template", "")
    header: str
    try:
        header = template.format(**context)
    except KeyError:
        header = ""

    if "SPDX-License-Identifier" not in header:
        lines = [
            f"# SPDX-FileCopyrightText: {context['year']} {context['name']} <{context['email']}>",
            f"# SPDX-License-Identifier: {context['license_key']}",
        ]
        header = "\n".join(lines) + "\n\n"
    else:
        header = header.rstrip("\n") + "\n\n"

    return header


class FileProcessor:
    """Single-pass file processor for SPDX headers with atomic writes.

    This class optimizes file I/O by:
    1. Reading the file only once
    2. Parsing structure (shebang, header, content) in memory
    3. Allowing multiple operations without re-reading
    4. Writing atomically to prevent corruption

    Example:
        processor = FileProcessor(filepath)
        processor.load()
        if not processor.has_header():
            processor.add_header(new_header)
            processor.save()
    """

    def __init__(self, filepath: PathLike):
        """Initialize the file processor.

        Args:
            filepath: Path to the Python file to process
        """
        self.filepath = Path(filepath)
        self.lines: list[str] = []
        self.shebang: str | None = None
        self.header: list[str] = []
        self.content: list[str] = []
        self._loaded = False
        self._modified = False

    def load(self) -> None:
        """Load and parse the file structure.

        Reads the file once and parses it into:
        - shebang (if present)
        - SPDX header (if present)
        - content (rest of the file)
        """
        if self._loaded:
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.lines = f.readlines()
        except OSError as exc:
            raise OSError(f"Failed to read {self.filepath}: {exc}") from exc

        self._parse_structure()
        self._loaded = True

    def _parse_structure(self) -> None:
        """Parse file structure into shebang, header, and content."""
        if not self.lines:
            return

        lines = self.lines.copy()

        # Extract shebang
        if lines and lines[0].startswith("#!"):
            self.shebang = lines.pop(0)

        # Extract SPDX header
        header_lines = []
        in_header = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check if this is part of the header
            if stripped.startswith("#"):
                if "SPDX" in line:
                    in_header = True
                if in_header:
                    header_lines.append(line)
                else:
                    # Comment before SPDX header, not part of header
                    break
            elif stripped == "":
                # Blank line - include if we're in header
                if in_header:
                    header_lines.append(line)
                elif header_lines:
                    # Blank line after header, stop
                    break
            else:
                # Non-comment, non-blank line - header ends
                break

        if header_lines:
            self.header = header_lines
            self.content = lines[len(header_lines) :]
        else:
            self.content = lines

    def has_header(self) -> bool:
        """Check if file has an SPDX header.

        Returns:
            True if SPDX header is present, False otherwise
        """
        if not self._loaded:
            self.load()
        return bool(self.header)

    def add_header(self, new_header: str) -> None:
        """Add or replace SPDX header.

        Args:
            new_header: The header text to add (should include newlines)
        """
        if not self._loaded:
            self.load()

        self.header = new_header.splitlines(keepends=True)
        self._modified = True

    def remove_header(self) -> None:
        """Remove the SPDX header."""
        if not self._loaded:
            self.load()

        if self.header:
            self.header = []
            self._modified = True

    def get_content(self) -> str:
        """Get the complete file content as a string.

        Returns:
            The complete file content with shebang, header, and content
        """
        if not self._loaded:
            self.load()

        result = []
        if self.shebang:
            result.append(self.shebang)
        result.extend(self.header)
        result.extend(self.content)

        return "".join(result)

    def save(self, force: bool = False) -> None:
        """Save the file with atomic write operation.

        Uses a temporary file and atomic move to prevent corruption.
        Preserves file permissions.

        Args:
            force: If True, save even if not modified

        Raises:
            OSError: If file operations fail
        """
        if not self._loaded:
            return

        if not self._modified and not force:
            return

        # Build final content
        result = []
        if self.shebang:
            result.append(self.shebang)
        result.extend(self.header)
        result.extend(self.content)

        # Atomic write using temporary file
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.filepath.parent,
            prefix=f".{self.filepath.name}.",
            suffix=".tmp",
        )

        try:
            # Write to temporary file
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.writelines(result)

            # Preserve permissions if original file exists
            if self.filepath.exists():
                shutil.copystat(self.filepath, temp_path)

            # Atomic move
            shutil.move(temp_path, self.filepath)
            self._modified = False

        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise

    def is_modified(self) -> bool:
        """Check if the file has been modified.

        Returns:
            True if modifications have been made, False otherwise
        """
        return self._modified
