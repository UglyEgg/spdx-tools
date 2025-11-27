# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Encoding detection and handling for SPDX header management.

This module provides utilities for detecting file encodings and reading
files with automatic encoding detection.
"""

from __future__ import annotations

from pathlib import Path

from .exceptions import EncodingError

# Common encodings to try, in order of preference
DEFAULT_ENCODINGS = [
    "utf-8",
    "utf-8-sig",  # UTF-8 with BOM
    "latin-1",
    "cp1252",  # Windows-1252
    "iso-8859-1",
    "ascii",
]


def detect_encoding(filepath: Path, sample_size: int = 10000) -> str:
    """Detect the encoding of a file.

    Tries to detect encoding using chardet if available, otherwise
    falls back to trying common encodings.

    Args:
        filepath: Path to the file
        sample_size: Number of bytes to read for detection

    Returns:
        Detected encoding name

    Raises:
        EncodingError: If encoding cannot be detected

    Example:
        >>> encoding = detect_encoding(Path("file.py"))
        >>> print(f"Detected encoding: {encoding}")
    """
    # Try chardet if available
    try:
        import chardet

        with open(filepath, "rb") as f:
            raw_data = f.read(sample_size)

        result = chardet.detect(raw_data)
        if result and result.get("encoding"):
            encoding = str(result["encoding"])
            confidence = result.get("confidence", 0)

            # Only use chardet result if confidence is high enough
            if confidence > 0.7:
                return encoding

    except ImportError:
        pass  # chardet not available, use fallback
    except Exception:
        pass  # chardet failed, use fallback

    # Fallback: try common encodings
    for encoding in DEFAULT_ENCODINGS:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                f.read()  # Try to read the entire file
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue

    # If all encodings fail, raise error
    raise EncodingError(filepath, DEFAULT_ENCODINGS)


def read_file_with_encoding(filepath: Path, encoding: str | None = None) -> tuple[list[str], str]:
    """Read a file with automatic encoding detection.

    Args:
        filepath: Path to the file
        encoding: Optional encoding to use. If None, will auto-detect.

    Returns:
        Tuple of (lines, encoding_used)

    Raises:
        EncodingError: If file cannot be decoded
        FileNotFoundError: If file doesn't exist

    Example:
        >>> lines, encoding = read_file_with_encoding(Path("file.py"))
        >>> print(f"Read {len(lines)} lines using {encoding}")
    """
    if encoding is None:
        encoding = detect_encoding(filepath)

    try:
        with open(filepath, "r", encoding=encoding) as f:
            lines = f.readlines()
        return lines, encoding
    except UnicodeDecodeError as exc:
        raise EncodingError(
            filepath,
            [encoding],
            f"File could not be decoded with {encoding}. " "Try specifying a different encoding.",
        ) from exc


def write_file_with_encoding(
    filepath: Path,
    lines: list[str],
    encoding: str = "utf-8",
    preserve_bom: bool = False,
) -> None:
    """Write a file with specified encoding.

    Args:
        filepath: Path to the file
        lines: Lines to write
        encoding: Encoding to use (default: utf-8)
        preserve_bom: Whether to preserve BOM for UTF-8

    Raises:
        EncodingError: If content cannot be encoded

    Example:
        >>> lines = ["# Header\\n", "print('hello')\\n"]
        >>> write_file_with_encoding(Path("file.py"), lines)
    """
    # Handle UTF-8 BOM
    if preserve_bom and encoding.lower() in ("utf-8", "utf8"):
        encoding = "utf-8-sig"

    try:
        with open(filepath, "w", encoding=encoding) as f:
            f.writelines(lines)
    except (UnicodeEncodeError, LookupError) as exc:
        raise EncodingError(
            filepath,
            [encoding],
            f"Content could not be encoded with {encoding}.",
        ) from exc


def normalize_encoding_name(encoding: str) -> str:
    """Normalize encoding name to a standard form.

    Args:
        encoding: Encoding name to normalize

    Returns:
        Normalized encoding name

    Example:
        >>> normalize_encoding_name("UTF8")
        'utf-8'
        >>> normalize_encoding_name("windows-1252")
        'cp1252'
    """
    encoding = encoding.lower().replace("_", "-")

    # Common aliases
    aliases = {
        "utf8": "utf-8",
        "utf-8-bom": "utf-8-sig",
        "windows-1252": "cp1252",
        "latin1": "latin-1",
        "iso-8859-1": "latin-1",
    }

    return aliases.get(encoding, encoding)


def is_text_file(filepath: Path, sample_size: int = 8192) -> bool:
    """Check if a file is likely a text file.

    Args:
        filepath: Path to the file
        sample_size: Number of bytes to check

    Returns:
        True if file appears to be text, False otherwise

    Example:
        >>> if is_text_file(Path("file.py")):
        ...     print("Text file")
    """
    try:
        with open(filepath, "rb") as f:
            sample = f.read(sample_size)

        # Check for null bytes (common in binary files)
        if b"\x00" in sample:
            return False

        # Try to decode as UTF-8
        try:
            sample.decode("utf-8")
            return True
        except UnicodeDecodeError:
            pass

        # Try other common encodings
        for encoding in ["latin-1", "cp1252"]:
            try:
                sample.decode(encoding)
                return True
            except UnicodeDecodeError:
                continue

        return False

    except Exception:
        return False


def get_encoding_info(filepath: Path) -> dict[str, str | bool | float]:
    """Get detailed encoding information about a file.

    Args:
        filepath: Path to the file

    Returns:
        Dictionary with encoding information

    Example:
        >>> info = get_encoding_info(Path("file.py"))
        >>> print(f"Encoding: {info['encoding']}")
        >>> print(f"Has BOM: {info['has_bom']}")
    """
    info: dict[str, str | bool | float] = {
        "encoding": "unknown",
        "has_bom": False,
        "is_text": False,
        "confidence": 0.0,
    }

    try:
        # Check if it's a text file
        info["is_text"] = is_text_file(filepath)

        if not info["is_text"]:
            return info

        # Check for BOM
        with open(filepath, "rb") as f:
            start = f.read(4)

        if start.startswith(b"\xef\xbb\xbf"):
            info["has_bom"] = True
            info["encoding"] = "utf-8-sig"
            info["confidence"] = 1.0
            return info

        # Detect encoding
        try:
            import chardet

            with open(filepath, "rb") as f:
                raw_data = f.read(10000)

            result = chardet.detect(raw_data)
            if result:
                info["encoding"] = str(result.get("encoding", "unknown"))
                info["confidence"] = float(result.get("confidence", 0.0))
                return info

        except ImportError:
            pass

        # Fallback detection
        encoding = detect_encoding(filepath)
        info["encoding"] = encoding
        info["confidence"] = 0.8

    except Exception:
        pass

    return info
