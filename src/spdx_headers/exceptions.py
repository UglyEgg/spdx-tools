# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Custom exceptions for SPDX header management.

This module provides specific exception classes with helpful error messages
and suggestions for common issues.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional


class SPDXError(Exception):
    """Base exception for all SPDX-related errors."""

    pass


class FileProcessingError(SPDXError):
    """Error processing a file.

    Attributes:
        filepath: Path to the file that caused the error
        reason: Description of what went wrong
        suggestion: Optional suggestion for fixing the issue
    """

    def __init__(
        self,
        filepath: Path | str,
        reason: str,
        suggestion: Optional[str] = None,
    ):
        self.filepath = Path(filepath)
        self.reason = reason
        self.suggestion = suggestion

        message = f"Error processing '{self.filepath}': {reason}"
        if suggestion:
            message += f"\n\nSuggestion: {suggestion}"

        super().__init__(message)


class EncodingError(FileProcessingError):
    """Error related to file encoding.

    Raised when a file cannot be decoded with the expected encoding.
    """

    def __init__(
        self,
        filepath: Path | str,
        attempted_encodings: List[str],
        suggestion: Optional[str] = None,
    ):
        self.attempted_encodings = attempted_encodings

        reason = (
            f"Unable to decode file with encodings: {', '.join(attempted_encodings)}"
        )

        if not suggestion:
            suggestion = (
                "The file may be binary or use an unsupported encoding. "
                "Try converting the file to UTF-8 encoding."
            )

        super().__init__(filepath, reason, suggestion)


class LicenseNotFoundError(SPDXError):
    """License identifier not found in the license database.

    Attributes:
        license_id: The license identifier that was not found
        suggestions: List of similar license identifiers
    """

    def __init__(self, license_id: str, suggestions: Optional[List[str]] = None):
        self.license_id = license_id
        self.suggestions = suggestions or []

        message = f"License '{license_id}' not found in the SPDX license database."

        if suggestions:
            message += "\n\nDid you mean one of these?"
            for suggestion in suggestions[:5]:
                message += f"\n  • {suggestion}"
            message += (
                f"\n\nUse 'spdx-headers --list {license_id}' to search for licenses."
            )
        else:
            message += "\n\nUse 'spdx-headers --list' to see all available licenses."

        super().__init__(message)


class DirectoryNotFoundError(SPDXError):
    """Directory does not exist.

    Attributes:
        directory: Path to the directory that was not found
    """

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

        message = f"Directory '{self.directory}' does not exist."
        message += "\n\nSuggestion: Check the path and try again."

        super().__init__(message)


class NoFilesFoundError(SPDXError):
    """No Python files found in the directory.

    Attributes:
        directory: Path to the directory that was searched
    """

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

        message = f"No Python files found in '{self.directory}'."
        message += "\n\nSuggestion: Check that you're in the correct directory."

        super().__init__(message)


class HeaderNotFoundError(FileProcessingError):
    """SPDX header not found in file.

    Raised when attempting to modify a header that doesn't exist.
    """

    def __init__(self, filepath: Path | str):
        reason = "No SPDX header found"
        suggestion = "Use 'spdx-headers --add LICENSE' to add a header to this file."

        super().__init__(filepath, reason, suggestion)


class InvalidHeaderError(FileProcessingError):
    """SPDX header is invalid or malformed.

    Attributes:
        filepath: Path to the file with invalid header
        details: Details about what's wrong with the header
    """

    def __init__(self, filepath: Path | str, details: str):
        self.details = details

        reason = f"Invalid SPDX header: {details}"
        suggestion = "Check the SPDX header format and fix any issues."

        super().__init__(filepath, reason, suggestion)


class ConcurrentModificationError(FileProcessingError):
    """File was modified by another process during operation.

    Raised when a file changes between read and write operations.
    """

    def __init__(self, filepath: Path | str):
        reason = "File was modified by another process"
        suggestion = (
            "Try the operation again. If the problem persists, "
            "ensure no other processes are modifying the file."
        )

        super().__init__(filepath, reason, suggestion)


class PermissionError(FileProcessingError):
    """Insufficient permissions to access file.

    Raised when the user doesn't have permission to read or write a file.
    """

    def __init__(self, filepath: Path | str, operation: str):
        self.operation = operation

        reason = f"Permission denied for {operation}"
        suggestion = (
            f"Check file permissions and ensure you have {operation} access. "
            "You may need to run with elevated privileges."
        )

        super().__init__(filepath, reason, suggestion)


def find_similar_licenses(
    license_id: str, available_licenses: List[str], cutoff: float = 0.6
) -> List[str]:
    """Find similar license identifiers using fuzzy matching.

    Args:
        license_id: The license identifier to match
        available_licenses: List of available license identifiers
        cutoff: Similarity threshold (0.0 to 1.0)

    Returns:
        List of similar license identifiers, sorted by similarity

    Example:
        >>> licenses = ["MIT", "Apache-2.0", "GPL-3.0"]
        >>> find_similar_licenses("apache", licenses)
        ['Apache-2.0']
    """
    try:
        from difflib import get_close_matches

        return get_close_matches(license_id, available_licenses, n=5, cutoff=cutoff)
    except ImportError:
        # Fallback to simple case-insensitive substring matching
        license_lower = license_id.lower()
        matches = [
            lic
            for lic in available_licenses
            if license_lower in lic.lower() or lic.lower() in license_lower
        ]
        return sorted(matches)[:5]
