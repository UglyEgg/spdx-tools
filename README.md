
# SPDX Headers

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![License Compliance](https://github.com/UglyEgg/spdx-tools/actions/workflows/license-check.yml/badge.svg)](https://github.com/UglyEgg/spdx-tools/actions/workflows/license-check.yml)

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
- **Flexible license viewing** – preview SPDX license summaries and optionally keep the generated files for reference.

## Installation

```bash
pip install spdx-headers
```

### Working from Source (with uv)

The development workflow relies on [uv](https://github.com/astral-sh/uv) for dependency management. Install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: pipx install uv
```

Then clone the repository and install dependencies:

```bash
git clone https://github.com/uglyegg/spdx-tools.git
cd spdx-tools
uv sync --dev
uv run pre-commit install
```

## Quick Start

```bash
# Add AGPL-3.0-or-later headers to all Python files
spdx-headers --add AGPL-3.0-or-later

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
| `spdx-headers --check [--fix]` | Return exit code 0/1 depending on compliance; `--fix` attempts auto-repair and the command reports detected SPDX identifiers (listing files if multiple licenses are found). |
| `spdx-headers --list [KEYWORD]` | List available SPDX identifiers, optionally filtering by keyword. |
| `spdx-headers --show LICENSE [--keep-temp]` | Display a license summary using the system’s default viewer (optionally keep the temp file). |
| `spdx-headers --extract [KEYWORD] [--add LICENSE]` | Extract license text for identifiers matching `KEYWORD`; combine with `--add`/`--change` to write headers and license text together. |
| `spdx-headers --update` | Download the latest SPDX license data. |

See [`docs/usage.md`](docs/usage.md) for a comprehensive walkthrough.

## Using As a Pre-Commit Hook

`spdx-headers` ships with a pre-commit hook that checks for (and can auto-fix) missing headers. Add the following to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/uglyegg/spdx-tools
  rev: v1.0.0
  hooks:
    - id: spdx-header-check
```

The bundled configuration automatically runs `spdx-headers --check --fix`, so files missing a header are rewritten when the repository has a consistent SPDX identifier. See [`docs/pre-commit.md`](docs/pre-commit.md) for advanced configuration.

## Documentation

- [`docs/usage.md`](docs/usage.md) – extended CLI usage guide, tips, and examples.
- [`docs/pre-commit.md`](docs/pre-commit.md) – integrating the tool with `pre-commit`.
- [`docs/github-actions.md`](docs/github-actions.md) – integrating the tool with GitHub Workflows.
- [`docs/dev-workflow`](docs/dev-workflow.md) – workflow when working on development for this application.

## Contributing

Contributions are welcome! Please open an issue or pull request. When submitting changes:

1. Run `make check` to execute formatting, lint, mypy, and test suites.
2. Update or add documentation in `docs/` if behaviour changes.
3. Add tests covering new functionality.

## License

This project is licensed under the GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See the `LICENSE` file for details. Additional license texts can be generated via `spdx-headers --extract`.
