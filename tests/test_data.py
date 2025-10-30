# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for SPDX license data utilities."""

import sys
import types
from pathlib import Path

import pytest

from spdx_headers.data import update_license_data


def test_update_license_data_network_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_requests = types.ModuleType("requests")

    class FakeRequestException(Exception):
        pass

    def fake_get(*_: object, **__: object) -> None:
        raise FakeRequestException("network down")

    setattr(fake_requests, "RequestException", FakeRequestException)
    setattr(fake_requests, "get", fake_get)

    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    with pytest.raises(SystemExit) as excinfo:
        update_license_data(tmp_path / "licenses.json")

    assert "Error downloading SPDX license data" in str(excinfo.value)


def test_update_license_data_invalid_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_requests = types.ModuleType("requests")

    class FakeRequestException(Exception):
        pass

    class FakeResponse:
        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def json() -> None:
            raise ValueError("bad json")

    def fake_get(*_: object, **__: object) -> FakeResponse:
        return FakeResponse()

    setattr(fake_requests, "RequestException", FakeRequestException)
    setattr(fake_requests, "get", fake_get)

    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    with pytest.raises(SystemExit) as excinfo:
        update_license_data(tmp_path / "licenses.json")

    assert "Error processing SPDX license data" in str(excinfo.value)
