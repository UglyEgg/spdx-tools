#!/usr/bin/env python3
"""
Automate release version bumps by updating CHANGELOG.md.

Usage examples:
    python scripts/bump_version.py                # bump patch version
    python scripts/bump_version.py --part minor   # bump minor version
    python scripts/bump_version.py --set 1.2.0    # set explicit version

The script:
1. Calculates the new version based on the previous release entry.
2. Moves "Unreleased" notes into a dated release section.
3. Refreshes comparison links at the bottom of the changelog.

Note: Because this project uses `hatch-vcs`, publish a release by tagging
      the repository after running this script (e.g., `git tag vX.Y.Z`).
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"


def semver_bump(version: str, part: str) -> str:
    major, minor, patch = version.split(".")
    major_i, minor_i, patch_i = int(major), int(minor), int(patch)

    if part == "major":
        major_i += 1
        minor_i = 0
        patch_i = 0
    elif part == "minor":
        minor_i += 1
        patch_i = 0
    else:
        patch_i += 1

    return f"{major_i}.{minor_i}.{patch_i}"


def parse_changelog() -> Tuple[List[str], int, int, str]:
    """Read the changelog and return lines, start/end indexes, and previous version."""
    lines = CHANGELOG_PATH.read_text(encoding="utf-8").splitlines(keepends=True)

    try:
        unreleased_idx = next(
            i for i, line in enumerate(lines) if line.startswith("## [Unreleased]")
        )
    except StopIteration as exc:
        raise RuntimeError("Changelog must contain '## [Unreleased]' section.") from exc

    try:
        next_heading_idx = next(
            i
            for i in range(unreleased_idx + 1, len(lines))
            if lines[i].startswith("## [")
        )
    except StopIteration:
        next_heading_idx = len(lines)

    previous_version_line = lines[next_heading_idx].strip()
    if not previous_version_line.startswith("## ["):
        raise RuntimeError("Unable to determine previous release from changelog.")
    previous_version = previous_version_line.split("]")[0].split("[", 1)[1]

    return lines, unreleased_idx, next_heading_idx, previous_version


def sanitize_unreleased_section(section: List[str]) -> List[str]:
    """Trim leading/trailing blank lines from the section."""
    start = 0
    while start < len(section) and section[start].strip() == "":
        start += 1
    end = len(section)
    while end > start and section[end - 1].strip() == "":
        end -= 1
    return section[start:end]


def build_unreleased_template() -> List[str]:
    """Return a default scaffold for the Unreleased section."""
    return [
        "\n",
        "### Added\n",
        "-\n",
        "\n",
        "### Changed\n",
        "-\n",
        "\n",
        "### Fixed\n",
        "-\n",
        "\n",
    ]


def update_changelog(new_version: str) -> str:
    lines, unreleased_idx, next_heading_idx, previous_version = parse_changelog()
    unreleased_section = sanitize_unreleased_section(
        lines[unreleased_idx + 1 : next_heading_idx]
    )

    release_heading = [
        f"## [{new_version}] - {dt.date.today():%Y-%m-%d}\n",
        "\n",
    ]
    release_block = ["\n"] + release_heading + unreleased_section + ["\n"]

    new_unreleased = build_unreleased_template()

    updated_lines = (
        lines[: unreleased_idx + 1]
        + new_unreleased
        + release_block
        + lines[next_heading_idx:]
    )

    # Update link references
    link_inserted = False
    for i, line in enumerate(updated_lines):
        if line.startswith("[unreleased]:"):
            updated_lines[
                i
            ] = f"[unreleased]: https://github.com/uglyegg/spdx-tools/compare/v{new_version}...HEAD\n"
            if not link_inserted:
                updated_lines.insert(
                    i + 1,
                    f"[{new_version}]: https://github.com/uglyegg/spdx-tools/compare/v{previous_version}...v{new_version}\n",
                )
                link_inserted = True
            break

    CHANGELOG_PATH.write_text("".join(updated_lines), encoding="utf-8")
    return previous_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a new project version.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--part",
        choices=("major", "minor", "patch"),
        help="Semantic version part to bump (default: patch).",
    )
    group.add_argument(
        "--set",
        dest="explicit",
        help="Set an explicit version (e.g., 1.2.0).",
    )
    args = parser.parse_args()

    _, _, _, previous_version = parse_changelog()
    current_version = previous_version

    if args.explicit:
        new_version = args.explicit
    else:
        part = args.part or "patch"
        new_version = semver_bump(current_version, part)

    prev = update_changelog(new_version)
    print(f"Prepared release notes for {new_version} (previous: {prev}).")
    print("Next steps:")
    print(f"  git commit -am 'Release v{new_version}'")
    print(f"  git tag v{new_version}")
    print("  git push origin main --tags")


if __name__ == "__main__":
    main()
