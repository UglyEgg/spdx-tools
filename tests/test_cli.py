# SPDX-FileCopyrightText: 2025 Richard Majewski <uglyegg@entropy.quest>
#
# SPDX-License-Identifier: GPL-3.0-only

"""CLI behaviour tests."""

import sys
from pathlib import Path
from typing import Any, Dict, Iterator

import pytest

from spdx_headers import cli
from spdx_headers.core import create_header
from spdx_headers.data import load_license_data


def _add_src_path() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _restore_cli_env() -> Iterator[None]:
    """Ensure sys.path and sys.argv are restored between tests."""
    _add_src_path()
    original = sys.argv[:]
    try:
        yield
    finally:
        sys.argv = original


restore_cli_env = pytest.fixture(autouse=True)(_restore_cli_env)


def test_cli_list_with_filter(capsys: pytest.CaptureFixture[str]) -> None:
    sys.argv = ["spdx-headers", "--list", "Apache-2.0"]

    cli.main()
    captured = capsys.readouterr()
    assert "Filter: Apache-2.0" in captured.out
    assert "Matched licenses:" in captured.out
    assert "of" in captured.out
    assert "- Apache-2.0" in captured.out


def test_cli_list_no_matches(capsys: pytest.CaptureFixture[str]) -> None:
    sys.argv = ["spdx-headers", "--list", "nope-license"]

    cli.main()
    captured = capsys.readouterr()
    assert "No licenses found matching keyword 'nope-license'." in captured.out


def test_cli_show_invokes_operation(monkeypatch: pytest.MonkeyPatch) -> None:
    sys.argv = ["spdx-headers", "--show", "MIT"]
    called: Dict[str, Any] = {}

    def fake_show(
        license_key: str, license_data: Any, *args: Any, **kwargs: Any
    ) -> None:
        called["license_key"] = license_key
        called["license_data"] = license_data

    monkeypatch.setattr(cli, "show_license", fake_show)

    cli.main()

    assert called["license_key"] == "MIT"
    assert "licenses" in called["license_data"]


def test_cli_check_fix_adds_headers(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project_root = tmp_path
    src_dir = project_root / "src"
    src_dir.mkdir()

    license_data = load_license_data()
    header = create_header(
        license_data,
        "MIT",
        year="2025",
        name="Test User",
        email="test@example.com",
    )
    assert header is not None

    (src_dir / "existing.py").write_text(
        f"{header}print('existing')\n", encoding="utf-8"
    )
    missing_file = src_dir / "missing.py"
    missing_file.write_text("print('missing')\n", encoding="utf-8")

    sys.argv = [
        "spdx-headers",
        "--check",
        "--fix",
        "--path",
        str(project_root),
    ]

    with pytest.raises(SystemExit) as excinfo:
        cli.main()

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "Successfully added missing SPDX headers" in captured.out
    content = missing_file.read_text(encoding="utf-8")
    assert "SPDX-License-Identifier: MIT" in content
