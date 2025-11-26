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

from .data import LicenseData
from .data import load_license_data as _load_license_data
from .data import update_license_data as _update_license_data

PathLike = Union[str, Path]

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


def _extract_spdx_header_from_lines(lines: List[str]) -> List[str]:
    header_candidates: List[str] = []
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


def extract_spdx_header(filepath: PathLike) -> List[str]:
    """Extract the SPDX header from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()
        return _extract_spdx_header_from_lines(lines)
    except OSError:
        return []


def remove_spdx_header(filepath: PathLike) -> Tuple[List[str], bool]:
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

            new_lines: List[str] = []
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
