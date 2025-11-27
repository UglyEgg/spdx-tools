# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Data management for SPDX license information.
"""

from __future__ import annotations

import datetime
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, TypedDict, Union, cast

PathLike = Union[str, Path]


class _LicenseEntryRequired(TypedDict):
    name: str
    deprecated: bool
    osi_approved: bool
    fsf_libre: bool
    header_template: str


class LicenseEntry(_LicenseEntryRequired, total=False):
    license_text: str


class LicenseMetadata(TypedDict):
    spdx_version: str
    generated_at: str
    license_count: int


class LicenseData(TypedDict):
    metadata: LicenseMetadata
    licenses: Dict[str, LicenseEntry]


# Default location for the SPDX license data file
DEFAULT_DATA_FILE = Path(__file__).parent / "data" / "spdx_license_data.json"


@lru_cache(maxsize=8)
def _load_license_data_cached(resolved_path: Path) -> LicenseData:
    """Internal cached function to load license data.

    This function is cached to avoid repeated JSON parsing of the same file.
    The cache is keyed by the resolved file path.

    Args:
        resolved_path: Resolved path to the license data file

    Returns:
        Loaded license data

    Raises:
        SystemExit: If file not found or invalid JSON
    """
    try:
        with resolved_path.open("r", encoding="utf-8") as file_handle:
            data = cast(LicenseData, json.load(file_handle))
        return data
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Error: SPDX license data file not found at {resolved_path}\n"
            "Run 'python -m spdx_headers.generate_data' to generate the data file."
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Error: Invalid JSON in SPDX license data file at {resolved_path}"
        ) from exc


def load_license_data(data_file_path: Optional[PathLike] = None) -> LicenseData:
    """Load the SPDX license data from the JSON file.

    This function uses an LRU cache to avoid repeated parsing of the same
    license data file. The cache is automatically managed and will store
    up to 8 different license data files.

    Args:
        data_file_path: Optional path to license data file.
                       Defaults to bundled data file.

    Returns:
        Loaded license data dictionary

    Raises:
        SystemExit: If file not found or contains invalid JSON

    Note:
        The cache is cleared when update_license_data() is called to ensure
        fresh data is loaded after updates.
    """
    resolved_path = Path(data_file_path) if data_file_path is not None else DEFAULT_DATA_FILE
    return _load_license_data_cached(resolved_path)


def update_license_data(data_file_path: Optional[PathLike] = None) -> None:
    """Update the SPDX license data file by downloading from the official source."""
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - dependency missing at runtime
        raise SystemExit(
            "Error: requests library is required for updating license data.\n"
            "Install it with: pip install requests"
        ) from exc

    resolved_path = Path(data_file_path) if data_file_path is not None else DEFAULT_DATA_FILE

    print("Downloading SPDX license data...")
    try:
        response = requests.get(
            "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json",
            timeout=30,
        )
        response.raise_for_status()

        spdx_data = cast(Mapping[str, Any], response.json())
        licenses_section = cast(Iterable[Mapping[str, Any]], spdx_data.get("licenses", []))
        licenses_list = list(licenses_section)

        license_data: LicenseData = {
            "metadata": {
                "spdx_version": str(spdx_data.get("licenseListVersion", "unknown")),
                "generated_at": datetime.datetime.now().isoformat(),
                "license_count": len(licenses_list),
            },
            "licenses": {},
        }

        for license_info in licenses_list:
            license_id = license_info.get("licenseId")
            if not isinstance(license_id, str):
                continue

            entry: LicenseEntry = {
                "name": str(license_info.get("name", "")),
                "deprecated": bool(license_info.get("isDeprecatedLicenseId", False)),
                "osi_approved": bool(license_info.get("isOsiApproved", False)),
                "fsf_libre": bool(license_info.get("isFsfLibre", False)),
                "header_template": ("#\n" "#\n" "# {license_name}\n"),
            }
            license_text = license_info.get("licenseText")
            if isinstance(license_text, str) and license_text.strip():
                entry["license_text"] = license_text

            license_data["licenses"][license_id] = entry

        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        with resolved_path.open("w", encoding="utf-8") as file_handle:
            json.dump(license_data, file_handle, indent=2)

        # Clear the cache after updating to ensure fresh data is loaded
        _load_license_data_cached.cache_clear()

        print(f"✓ Successfully updated SPDX license data at {resolved_path}")
        print(f"  Downloaded {license_data['metadata']['license_count']} licenses")
        print("  Cache cleared - fresh data will be loaded on next access")

    except requests.RequestException as exc:
        raise SystemExit(f"Error downloading SPDX license data: {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise SystemExit(f"Error processing SPDX license data: {exc}") from exc


def clear_license_data_cache() -> None:
    """Clear the license data cache.

    This function clears the internal LRU cache used by load_license_data().
    Call this if you need to force a reload of license data, for example
    after manually modifying the license data file.

    Example:
        >>> from spdx_headers.data import clear_license_data_cache
        >>> clear_license_data_cache()
        >>> data = load_license_data()  # Will reload from disk
    """
    _load_license_data_cached.cache_clear()


def get_cache_info() -> Dict[str, Optional[int]]:
    """Get information about the license data cache.

    Returns a dictionary with cache statistics including:
    - hits: Number of cache hits
    - misses: Number of cache misses
    - maxsize: Maximum cache size
    - currsize: Current cache size

    Returns:
        Dictionary with cache statistics

    Example:
        >>> from spdx_headers.data import get_cache_info
        >>> info = get_cache_info()
        >>> print(f"Cache hits: {info['hits']}, misses: {info['misses']}")
    """
    cache_info = _load_license_data_cached.cache_info()
    return {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "maxsize": cache_info.maxsize,
        "currsize": cache_info.currsize,
    }
