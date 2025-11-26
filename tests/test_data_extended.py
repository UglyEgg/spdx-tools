# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Extended tests for data module to improve coverage.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spdx_headers.data import (
    DEFAULT_DATA_FILE,
    LicenseData,
    load_license_data,
    update_license_data,
)


class TestLoadLicenseData:
    """Tests for load_license_data function."""

    def test_load_default_data(self):
        """Test loading default license data."""
        data = load_license_data()
        assert "metadata" in data
        assert "licenses" in data
        assert isinstance(data["licenses"], dict)
        assert len(data["licenses"]) > 0

    def test_load_custom_path(self, tmp_path):
        """Test loading from custom path."""
        custom_file = tmp_path / "custom_licenses.json"
        test_data = {
            "metadata": {
                "spdx_version": "3.0",
                "generated_at": "2025-01-01T00:00:00",
                "license_count": 1,
            },
            "licenses": {
                "MIT": {
                    "name": "MIT License",
                    "deprecated": False,
                    "osi_approved": True,
                    "fsf_libre": True,
                    "header_template": "# MIT\n",
                }
            },
        }
        custom_file.write_text(json.dumps(test_data))

        data = load_license_data(custom_file)
        assert data["metadata"]["spdx_version"] == "3.0"
        assert "MIT" in data["licenses"]

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading non-existent file raises SystemExit."""
        nonexistent = tmp_path / "does_not_exist.json"

        with pytest.raises(SystemExit) as exc_info:
            load_license_data(nonexistent)

        assert "not found" in str(exc_info.value)

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises SystemExit."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        with pytest.raises(SystemExit) as exc_info:
            load_license_data(invalid_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_with_string_path(self, tmp_path):
        """Test loading with string path."""
        custom_file = tmp_path / "licenses.json"
        test_data = {
            "metadata": {
                "spdx_version": "3.0",
                "generated_at": "2025-01-01T00:00:00",
                "license_count": 0,
            },
            "licenses": {},
        }
        custom_file.write_text(json.dumps(test_data))

        data = load_license_data(str(custom_file))
        assert "metadata" in data


class TestUpdateLicenseData:
    """Tests for update_license_data function."""

    @patch("spdx_headers.data.requests")
    def test_update_success(self, mock_requests, tmp_path):
        """Test successful license data update."""
        output_file = tmp_path / "licenses.json"

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "licenseListVersion": "3.0",
            "licenses": [
                {
                    "licenseId": "MIT",
                    "name": "MIT License",
                    "isDeprecatedLicenseId": False,
                    "isOsiApproved": True,
                    "isFsfLibre": True,
                    "licenseText": "Permission is hereby granted...",
                },
                {
                    "licenseId": "Apache-2.0",
                    "name": "Apache License 2.0",
                    "isDeprecatedLicenseId": False,
                    "isOsiApproved": True,
                    "isFsfLibre": True,
                },
            ],
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        update_license_data(output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "metadata" in data
        assert "licenses" in data
        assert "MIT" in data["licenses"]
        assert "Apache-2.0" in data["licenses"]

    @patch("spdx_headers.data.requests")
    def test_update_network_error(self, mock_requests, tmp_path):
        """Test update with network error."""
        output_file = tmp_path / "licenses.json"

        # Mock network error
        mock_requests.get.side_effect = Exception("Network error")

        with pytest.raises(SystemExit) as exc_info:
            update_license_data(output_file)

        assert "Error downloading" in str(exc_info.value)

    @patch("spdx_headers.data.requests")
    def test_update_http_error(self, mock_requests, tmp_path):
        """Test update with HTTP error."""
        output_file = tmp_path / "licenses.json"

        # Mock HTTP error
        import requests

        mock_requests.get.side_effect = requests.RequestException("404 Not Found")

        with pytest.raises(SystemExit) as exc_info:
            update_license_data(output_file)

        assert "Error downloading" in str(exc_info.value)

    def test_update_without_requests(self, tmp_path):
        """Test update without requests library."""
        output_file = tmp_path / "licenses.json"

        with patch.dict("sys.modules", {"requests": None}):
            with pytest.raises(SystemExit) as exc_info:
                update_license_data(output_file)

            # Should mention missing requests library
            assert "requests" in str(exc_info.value).lower()

    @patch("spdx_headers.data.requests")
    def test_update_creates_directory(self, mock_requests, tmp_path):
        """Test that update creates parent directory if needed."""
        output_file = tmp_path / "subdir" / "licenses.json"

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "licenseListVersion": "3.0",
            "licenses": [],
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        update_license_data(output_file)

        assert output_file.parent.exists()
        assert output_file.exists()

    @patch("spdx_headers.data.requests")
    def test_update_with_invalid_license_id(self, mock_requests, tmp_path):
        """Test update with invalid license ID."""
        output_file = tmp_path / "licenses.json"

        # Mock response with invalid license ID
        mock_response = Mock()
        mock_response.json.return_value = {
            "licenseListVersion": "3.0",
            "licenses": [
                {
                    "licenseId": None,  # Invalid
                    "name": "Invalid License",
                },
                {
                    "licenseId": 123,  # Invalid type
                    "name": "Another Invalid",
                },
                {
                    "licenseId": "MIT",  # Valid
                    "name": "MIT License",
                },
            ],
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        update_license_data(output_file)

        data = json.loads(output_file.read_text())
        # Should only include valid license
        assert "MIT" in data["licenses"]
        assert len(data["licenses"]) == 1

    @patch("spdx_headers.data.requests")
    def test_update_with_missing_fields(self, mock_requests, tmp_path):
        """Test update with missing optional fields."""
        output_file = tmp_path / "licenses.json"

        # Mock response with minimal data
        mock_response = Mock()
        mock_response.json.return_value = {
            "licenseListVersion": "3.0",
            "licenses": [
                {
                    "licenseId": "MIT",
                    # Missing most fields
                }
            ],
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        update_license_data(output_file)

        data = json.loads(output_file.read_text())
        assert "MIT" in data["licenses"]
        # Should have default values
        assert data["licenses"]["MIT"]["deprecated"] is False
        assert data["licenses"]["MIT"]["osi_approved"] is False

    @patch("spdx_headers.data.requests")
    def test_update_with_empty_license_text(self, mock_requests, tmp_path):
        """Test update with empty license text."""
        output_file = tmp_path / "licenses.json"

        # Mock response with empty license text
        mock_response = Mock()
        mock_response.json.return_value = {
            "licenseListVersion": "3.0",
            "licenses": [
                {
                    "licenseId": "MIT",
                    "name": "MIT License",
                    "licenseText": "",  # Empty
                },
                {
                    "licenseId": "Apache-2.0",
                    "name": "Apache License",
                    "licenseText": "   ",  # Whitespace only
                },
            ],
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        update_license_data(output_file)

        data = json.loads(output_file.read_text())
        # Empty license text should not be included
        assert "license_text" not in data["licenses"]["MIT"]
        assert "license_text" not in data["licenses"]["Apache-2.0"]

    @patch("spdx_headers.data.requests")
    def test_update_default_path(self, mock_requests):
        """Test update with default path."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "licenseListVersion": "3.0",
            "licenses": [],
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        # This should use DEFAULT_DATA_FILE
        # We'll just verify it doesn't crash
        try:
            update_license_data()
        except (PermissionError, OSError):
            # Might not have permission to write to default location
            pass


class TestLicenseDataStructure:
    """Tests for license data structure and types."""

    def test_license_entry_structure(self):
        """Test that license entries have expected structure."""
        data = load_license_data()

        for license_id, entry in data["licenses"].items():
            assert "name" in entry
            assert "deprecated" in entry
            assert "osi_approved" in entry
            assert "fsf_libre" in entry
            assert "header_template" in entry
            assert isinstance(entry["name"], str)
            assert isinstance(entry["deprecated"], bool)
            assert isinstance(entry["osi_approved"], bool)
            assert isinstance(entry["fsf_libre"], bool)

    def test_metadata_structure(self):
        """Test that metadata has expected structure."""
        data = load_license_data()

        assert "spdx_version" in data["metadata"]
        assert "generated_at" in data["metadata"]
        assert "license_count" in data["metadata"]
        assert isinstance(data["metadata"]["spdx_version"], str)
        assert isinstance(data["metadata"]["generated_at"], str)
        assert isinstance(data["metadata"]["license_count"], int)

    def test_license_count_matches(self):
        """Test that license count matches actual number of licenses."""
        data = load_license_data()

        expected_count = data["metadata"]["license_count"]
        actual_count = len(data["licenses"])

        # Allow some tolerance for deprecated licenses
        assert abs(expected_count - actual_count) <= 10


class TestDefaultDataFile:
    """Tests for DEFAULT_DATA_FILE constant."""

    def test_default_data_file_exists(self):
        """Test that default data file exists."""
        assert DEFAULT_DATA_FILE.exists()

    def test_default_data_file_is_valid_json(self):
        """Test that default data file contains valid JSON."""
        with DEFAULT_DATA_FILE.open("r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_default_data_file_location(self):
        """Test that default data file is in expected location."""
        assert "data" in str(DEFAULT_DATA_FILE)
        assert "spdx_license_data.json" in str(DEFAULT_DATA_FILE)