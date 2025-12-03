# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

-

### Changed

-

### Fixed

-

## [1.5.1] - 2025-12-03

### Fixed

- -change, --remove, --verify, and --check operations work with --file now

## [1.5.0] - 2025-12-02

### Added

- Ability to work on individual file
- Support for repo-root specification
- Tests to support the new & improved functionality

### Changed

- Various documentation tweaks
- Enhanced path specification flexibility

### Fixed

- Scripts/bump_version.py multiple QoL tweaks
- Logic for path was overriding -p, --path specification
- Correct copyright author detection from pyproject.toml

## [1.0.3] - 2025-12-02

### Fixed

- Missing \_version.py in generated PyPi whl

## [1.0.2] - 2024-11-27

### Added

- Comprehensive test suite with 241 tests achieving 81% code coverage
- Examples directory with benchmark scripts

### Changed

- Modernized path handling to use pathlib throughout codebase
- Updated dependencies: removed unused beautifulsoup4 and tomli, added chardet
- Improved code quality to 99.5% Python style guide compliance
- Enhanced docstrings for better API documentation
- Streamlined Makefile by removing rarely-used convenience targets

### Fixed

- Fixed `make help` displaying "Makefile.template" instead of actual command names
- Fixed `make lint` isort error with auto-generated \_version.py file
- Resolved dependency mismatches in pyproject.toml

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

[unreleased]: https://github.com/uglyegg/spdx-tools/compare/v1.5.1...HEAD
[1.5.1]: https://github.com/uglyegg/spdx-tools/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/uglyegg/spdx-tools/compare/v1.0.3...v1.5.0
[1.0.3]: https://github.com/uglyegg/spdx-tools/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/uglyegg/spdx-tools/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/uglyegg/spdx-tools/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/uglyegg/spdx-tools/releases/tag/v1.0.0
