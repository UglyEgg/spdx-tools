# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

-

### Changed

-

### Fixed

-

## [1.0.1] - 2025-11-01

### Added

- guardrails for missing `_version.py`
- `.markdownlint.json` to suppress annoying warnings
- markdown linting

### Changed

- removed `version.py`, a Hatch generated file, from version control
- added universal `info` check in `Makefile.template`

### Fixed

- executable script permissions
- make bump-version regEx issue
- uv based commands in build.sh & release.sh
- improved PyPi publishing supprt & doc
- miscellaneous QoL tweaks and minor errors

## [1.0.0] - 2025-11-01

### Added

- Initial release of the `spdx-headers` CLI for managing SPDX headers.
- Commands to add, remove, change, verify, check, and extract SPDX headers.
- SPDX license list download helpers and placeholder extraction support.
- Pre-commit integration and CLI documentation.

[unreleased]: https://github.com/uglyegg/spdx-tools/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/uglyegg/spdx-tools/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/uglyegg/spdx-tools/releases/tag/v1.0.0
