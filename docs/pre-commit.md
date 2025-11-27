# Pre-Commit Integration

`spdx-headers` ships with a ready-to-use `pre-commit` hook that can both check and auto-fix missing SPDX headers. This document explains how to install, configure, and customize the hook in your projects.

## Requirements

- [`pre-commit`](https://pre-commit.com/) installed locally.
- Network access the first time hooks are fetched.
- Python 3.9+ (matches the CLI’s supported versions).

Install `pre-commit` if you don’t have it yet:

```bash
pip install pre-commit
```

## Quick Setup

Add the following entry to your repository’s `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/uglyegg/spdx-tools
    rev: v1.0.0 # pin to a tagged release for reproducibility
    hooks:
      - id: spdx-header-check
```

Then run:

```bash
pre-commit install
pre-commit run --all-files   # optional initial pass
```

The bundled hook executes:

```shell
./scripts/spdx_headers_cli.py --check --fix
```

It blocks commits when headers are missing and attempts to repair them automatically by inferring the repository’s SPDX license identifier.

## Customizing the Hook

You can pass additional arguments via `args` in your `.pre-commit-config.yaml`. For example, to run in dry-run mode or specify a different path:

```yaml
repos:
  - repo: https://github.com/uglyegg/spdx-tools
    rev: v1.0.0
    hooks:
      - id: spdx-header-check
        args: ["--check", "--fix", "--dry-run", "--path", "backend"]
```

> **Note:** The tool ignores filenames passed by `pre-commit` and always scans the target repository path. This ensures it handles cross-file operations consistently (e.g., inferring a license from multiple sources).

## Working in CI

To run the hook in CI, install `pre-commit` and execute:

```bash
pre-commit run --all-files
```

Alternatively, call the CLI directly:

```bash
spdx-headers --check --fix
```

This approach can be convenient when hooking into existing pipelines or when running inside Docker containers.

## Troubleshooting

- **Auto-fix doesn’t run:** Ensure there’s a single SPDX identifier across your repository. If multiple licenses exist, the tool cannot determine which one to apply.
- **Permission errors:** `pre-commit` caches environments under `~/.cache/pre-commit`. If your environment is read-only, set `PRE_COMMIT_HOME` to a writable directory.
- **Missing stubs for mypy:** Install dev dependencies (`pip install spdx-headers[dev]`) or add stub packages manually (`pip install types-requests`).

## Example Workflow

1. Developer runs `git commit`.
2. The `spdx-header-check` hook runs `spdx-headers --check --fix`.
3. If missing headers are detected, the hook rewrites files and exits with code 1, asking the developer to stage the new headers.
4. After staging the auto-fixed files, the commit succeeds.

By integrating `spdx-headers` with `pre-commit`, you ensure your repository stays compliant with SPDX header requirements without manual policing.
