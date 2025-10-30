
# SPDX Headers

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE-GPL-3.0-only)

`spdx-headers` is a command-line tool for auditing and maintaining SPDX license headers in Python projects. It can add, verify, and update SPDX headers, extract license texts, and integrates seamlessly with `pre-commit`.

## Table of Contents
1. [Features](#features)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Commands](#core-commands)
5. [Using As a Pre-Commit Hook](#using-as-a-pre-commit-hook)
6. [Documentation](#documentation)
7. [Contributing](#contributing)
8. [License](#license)

## Features

- **Automated SPDX management** – add, change, remove, or verify headers across your Python sources.
- **Auto-fix missing headers** – infer the repository’s SPDX identifier and repair files automatically.
- **SPDX license data updates** – fetches the latest license list directly from SPDX.
- **Pre-commit integration** – ships with a hook that can block commits or auto-fix issues.
- **License extraction** – generate LICENSE files by SPDX identifier.
- **Dry-run support** – inspect changes before applying them.
- **Typed codebase** – includes `py.typed` for first-class type checking.

## Installation

```bash
pip install spdx-headers
```

Alternatively, to work from source:

```bash
git clone https://github.com/uglyegg/spdx-tools.git
cd spdx-tools
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

## Quick Start

```bash
# Add GPL-3.0-only headers to all Python files
spdx-headers --add GPL-3.0-only

# Verify all files have valid SPDX headers
spdx-headers --verify

# Check (CI friendly) and auto-fix missing headers when possible
spdx-headers --check --fix

# List SPDX identifiers containing “Apache”
spdx-headers --list Apache

# Extract the MIT license into LICENSE-MIT
spdx-headers --extract --add MIT --dry-run
```

## Core Commands

| Command | Description |
| --- | --- |
| `spdx-headers --add LICENSE` | Add the specified SPDX header to all Python files. |
| `spdx-headers --change LICENSE` | Replace existing headers with the specified SPDX identifier. |
| `spdx-headers --remove` | Remove SPDX headers from all Python files. |
| `spdx-headers --verify` | Print a report of files missing headers (no exit code). |
| `spdx-headers --check [--fix]` | Return exit code 0/1 depending on compliance; `--fix` attempts auto-repair. |
| `spdx-headers --list [KEYWORD]` | List available SPDX identifiers, optionally filtering by keyword. |
| `spdx-headers --show LICENSE` | Display a license summary using the system’s default viewer. |
| `spdx-headers --extract --add LICENSE` | Extract the license text into `LICENSE-<id>`. |
| `spdx-headers --update` | Download the latest SPDX license data. |

See [`docs/usage.md`](docs/usage.md) for a comprehensive walkthrough.

## Using As a Pre-Commit Hook

`spdx-headers` ships with a pre-commit hook that checks for (and can auto-fix) missing headers. Add the following to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/uglyegg/spdx-tools
  rev: v0.1.0
  hooks:
    - id: spdx-header-check
```

The bundled configuration automatically runs `spdx-headers --check --fix`, so files missing a header are rewritten when the repository has a consistent SPDX identifier. See [`docs/pre-commit.md`](docs/pre-commit.md) for advanced configuration.

## Documentation

- [`docs/usage.md`](docs/usage.md) – extended CLI usage guide, tips, and examples.
- [`docs/pre-commit.md`](docs/pre-commit.md) – integrating the tool with `pre-commit`.

## Contributing

Contributions are welcome! Please open an issue or pull request. When submitting changes:

1. Run `make check` to execute formatting, lint, mypy, and test suites.
2. Update or add documentation in `docs/` if behaviour changes.
3. Add tests covering new functionality.

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0-only). See the `LICENSE-*` files for details. License texts can be generated via `spdx-headers --extract`.
