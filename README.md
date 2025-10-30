
# SPDX Headers

A command-line tool for managing SPDX headers in Python source files.

## Features

- **Add SPDX headers** to Python files with proper copyright information
- **Update existing headers** with new license information
- **Remove headers** when needed
- **Verify compliance** across your entire codebase
- **Pre-commit hook integration** for automated checking
- **Dry-run mode** to preview changes before applying them
- **License extraction** to generate LICENSE files
- **Automatic copyright detection** from `pyproject.toml`

## Installation

```bash
pip install spdx-headers
```

## Quick Start
```bash
# Add GPL-3.0-only headers to all Python files
spdx-headers --add GPL-3.0-only

# Verify all files have headers
spdx-headers --verify

# List available licenses
spdx-headers --list
```

## Features
- Add, remove, or change SPDX headers in Python files
- Support for all official SPDX license identifiers
- Automatic copyright information detection from pyproject.toml
- Dry-run mode for safe testing
- Pre-commit hook integration
- License file extraction
