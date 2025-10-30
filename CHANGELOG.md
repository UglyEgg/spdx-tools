
# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--fix` option for automatic SPDX header repair.
- Auto-inference logic to determine a repository’s SPDX license from existing files.
- CLI documentation (`docs/usage.md`) and pre-commit guide (`docs/pre-commit.md`).
- `py.typed` marker for downstream type checkers.
- New tests covering CLI auto-fix behaviour and error handling in license data updates.

### Changed
- `--list` output clarifies the number of matched licenses.
- Pre-commit hook now runs with `--check --fix` for convenience.

### Fixed
- Missing SPDX headers in generated `_version.py` file.
- mypy compatibility issues introduced by typed fixtures.

## [0.1.0] - 2025-10-30

### Added
- Initial release of `spdx-headers` CLI.
- Commands to add, remove, change, verify, and check SPDX headers.
- SPDX license list download and extraction helpers.
- Pre-commit hook for enforcing SPDX compliance.

[unreleased]: https://github.com/uglyegg/spdx-tools/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/uglyegg/spdx-tools/releases/tag/v0.1.0
