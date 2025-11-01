# Using `spdx-headers` in GitHub Actions

This document shows how to run the `spdx-headers` CLI inside a GitHub Actions workflow to keep license headers consistent.

## Example workflow

Create `.github/workflows/license-check.yml` with the following contents:

```yaml
name: License Compliance

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  spdx-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install project
        run: |
          python -m pip install --upgrade pip
          pip install .[dev]

      - name: Check SPDX headers
        run: python -m spdx_headers.cli --check --fix --path .
```

### What this workflow does

- Checks out the repository.
- Installs Python 3.11 and caches pip downloads for faster reruns.
- Installs the project (including dev extras) so the CLI is available.
- Runs `spdx-headers --check --fix` to ensure SPDX headers are present; if headers can be auto-added they will be, and the job fails so you can commit the changes.

## Tips

- If your repository doesn’t ship dev extras, change the install command to `pip install .`.
- For monorepos, adjust `--path` to the specific subdirectory containing sources.
- Pair this workflow with the pre-commit hook described in `docs/pre-commit.md` for local enforcement.
