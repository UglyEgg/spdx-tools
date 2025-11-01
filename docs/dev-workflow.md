# Development Workflow

This document outlines the recommended workflow for contributing to `spdx-headers`, including local setup, testing, versioning, and release preparation.

## 1. Environment Setup

1. Install [uv](https://github.com/astral-sh/uv) (required by the Makefile):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: pipx install uv
   ```

2. Clone the repository and install dependencies using uv:

   ```bash
   git clone https://github.com/uglyegg/spdx-tools.git
   cd spdx-tools
   uv sync --dev
   uv run pre-commit install
   ```

The development extra installs formatting, linting, typing, and testing dependencies. Pre-commit will run the same checks locally that CI enforces.

## 2. Everyday Development Loop

1. Make changes on a feature branch.
2. Run the quick pipeline:

   ```bash
   make quick-check   # format, lint, tests
   ```

3. Optionally run the full suite:

   ```bash
   make check         # lint, mypy, pytest
   ```

4. Stage files and commit. Pre-commit hooks automatically run `spdx-headers --check --fix` to keep SPDX headers compliant.

## 3. Updating Documentation

- Update the README for new features.
- Add detailed guides under `docs/` as needed.
- Ensure `MANIFEST.in` includes relevant files so documentation ships with the package.

## 4. Version Bumping & Release Prep

Use the automated script via Make:

```bash
# Semantic bump (defaults to patch)
make bump-version part=minor

# Or set an explicit version
make bump-version version=1.2.0
```

The script:
- Updates `CHANGELOG.md` (moving “Unreleased” notes into a dated section, refreshing comparison links).
- Rewrites `src/spdx_headers/_version.py` with the new version (kept in sync with the changelog).

After bumping:

```bash
git status         # verify only intended files changed
git commit -am "Release v$(hatch version)"

# Tag the release so the publish script can verify it
git tag "v$(hatch version)"
```

Consider running the full pipeline once more (`make check`). The publish script will refuse to run unless the release tag exists and points at `HEAD`, which helps prevent publishing mismatched artifacts.

### Configuration hygiene

If the project needs to ignore generated/vendor files, keep a `.spdx-headers.ini` alongside the code. During code review, verify that new exclusions are justified, because they remove files from header enforcement. See `docs/configuration.md` for details.

## 5. Publishing (Optional)

If you intend to publish to PyPI:

```bash
# Optional dry-run against TestPyPI
make publish-test

# Publish to PyPI (runs full build + metadata checks)
make publish
```

The publish targets call `scripts/release.sh`, which refuses to proceed if the git tree is dirty, rebuilds packages, runs `twine check`, and then uploads with `twine`. Make sure your PyPI/TestPyPI credentials are configured (`~/.pypirc` or environment variables).

## 6. Pull Requests

Before opening a PR:
- Rebase onto `main`.
- Confirm `make check` passes.
- Document notable changes in `CHANGELOG.md` under “Unreleased”.
- Attach relevant docs/tests.

## 7. Useful Commands

| Command | Description |
| --- | --- |
| `make help` | Show available Make targets. |
| `make test` | Run pytest suite. |
| `make type-check` | Run mypy on the codebase. |
| `make update-spdx-data` | Refresh SPDX license data. |
| `make bump-version part=patch` | Bump version and update changelog. |

Following this workflow keeps the repository consistent, typed, and ready for releases with minimal manual overhead.
