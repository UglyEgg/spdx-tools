# Usage Guide

Welcome to `spdx-headers`! This document dives deeper into the CLI experience than the quick start in the README. You’ll find examples for common workflows, explanations of each command, and troubleshooting tips.

## Getting Started

Install the tool from PyPI:

```bash
pip install spdx-headers
```

or work inside the repository:

```bash
git clone https://github.com/uglyegg/spdx-tools.git
cd spdx-tools
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

The executable `spdx-headers` becomes available on your `PATH`. All commands support `--help` to display usage information.

## Commands Overview

### Add Headers

```bash
spdx-headers --add MIT
```

- Adds the MIT SPDX header to every Python file under the inferred `src/` directory (or project root if no `src/` exists).
- Automatically honours shebang lines, placing the SPDX header below them.
- Use `--path /some/project` to operate on a different repository.
- Includes copyright information based on `pyproject.toml`’s first author entry.
- Combine with `--extract` to create a `LICENSE-MIT` file alongside header insertion.

### Change Headers

```bash
spdx-headers --change GPL-3.0-only
```

- Replaces existing SPDX headers with a new license identifier.
- Only files already containing headers are modified.

### Remove Headers

```bash
spdx-headers --remove
```

- Deletes SPDX header blocks from all Python files.
- Useful when migrating a repository or before bulk regeneration.

### Verify vs. Check

```bash
spdx-headers --verify
spdx-headers --check
spdx-headers --check --fix
```

- `--verify` prints a report but always returns exit code 0.
- `--check` is CI-friendly: exit code 0 when compliant, 1 otherwise, and prints detected SPDX identifiers (including per-file details when multiple licenses are present).
- `--check --fix` tries to add missing headers automatically:
  - Scans existing files for SPDX identifiers.
  - If a single license dominates, missing files inherit that identifier.
  - Prints a success message if everything is fixed; otherwise leaves a list of files to review manually.
- Pass `--dry-run` to see which files would be updated without touching disk.

### List Licenses

```bash
spdx-headers --list
spdx-headers --list Apache
```

- Lists all SPDX identifiers bundled with the tool.
- When a keyword is provided, filters identifiers and shows “Matched licenses: X of Y total” to provide context.

### Extract Licenses

```bash
spdx-headers --extract Apache
spdx-headers --add Apache-2.0 --extract
```

- `--extract KEYWORD` writes license texts for every identifier matching the keyword, using `LICENSE` (or suffixed filenames when `LICENSE` already exists).
- Combine `--extract` with `--add` or `--change` to update headers and persist the corresponding license text at the same time.
- Output files are hard-wrapped to 79 characters to stay friendly to terminals and diffs.

### Show License

```bash
spdx-headers --show MIT
spdx-headers --show MIT --keep-temp
```

- Writes a temporary license summary and opens it with the system default viewer (`open`, `xdg-open`, `start`, etc.).
- By default the temporary file is deleted after 30 seconds; override with `--keep-temp` to leave it on disk (the CLI prints the file path).

### Update License Data

```bash
spdx-headers --update
```

- Refreshes the bundled `spdx_license_data.json` by downloading the latest SPDX license list. Requires network access.

## Advanced Options

- `--path PATH` – operate on a different repository. Useful when invoking `spdx-headers` from automation.
- `--data-file FILE` – supply a custom SPDX license data file.
- `--dry-run` – compatible with most commands; prints intended actions without writing changes.

## Troubleshooting

- **Missing SPDX headers keep failing:** run `spdx-headers --check --fix` first, then commit the changes.
- **Multiple licenses detected:** auto-fix cannot infer a unique license; run `--add LICENSE` explicitly, or refactor file headers yourself.
- **Type checking errors:** install all optional dependencies (e.g., `pip install spdx-headers[dev]`) to get stub packages for requests and others.

## Additional Resources

- Read the [pre-commit integration guide](pre-commit.md) for repository-level enforcement.
- Consult the [SPDX License List](https://spdx.org/licenses/) if you’re unsure about identifier names.
