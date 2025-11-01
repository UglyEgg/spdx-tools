# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# GNU Affero General Public License v3.0 or later

"""
Data management for SPDX license information.
"""

from __future__ import annotations

import datetime
import json
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


def load_license_data(data_file_path: Optional[PathLike] = None) -> LicenseData:
    """Load the SPDX license data from the JSON file."""
    resolved_path = (
        Path(data_file_path) if data_file_path is not None else DEFAULT_DATA_FILE
    )

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


def update_license_data(data_file_path: Optional[PathLike] = None) -> None:
    """Update the SPDX license data file by downloading from the official source."""
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - dependency missing at runtime
        raise SystemExit(
            "Error: requests library is required for updating license data.\n"
            "Install it with: pip install requests"
        ) from exc

    resolved_path = (
        Path(data_file_path) if data_file_path is not None else DEFAULT_DATA_FILE
    )

    print("Downloading SPDX license data...")
    try:
        response = requests.get(
            "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json",
            timeout=30,
        )
        response.raise_for_status()

        spdx_data = cast(Mapping[str, Any], response.json())
        licenses_section = cast(
            Iterable[Mapping[str, Any]], spdx_data.get("licenses", [])
        )
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

        print(f"✓ Successfully updated SPDX license data at {resolved_path}")
        print(f"  Downloaded {license_data['metadata']['license_count']} licenses")

    except requests.RequestException as exc:
        raise SystemExit(f"Error downloading SPDX license data: {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise SystemExit(f"Error processing SPDX license data: {exc}") from exc
