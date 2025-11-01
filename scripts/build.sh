#!/bin/bash

set -euo pipefail

VERSION=$(python - <<'PY'
import pathlib, re

data = pathlib.Path("src/spdx_headers/_version.py").read_text()
match = re.search(r'__version__\s*=\s*version\s*=\s*"([^"]+)"', data)
if not match:
    raise SystemExit("Unable to determine package version from _version.py")
print(match.group(1))
PY
)

echo "Building spdx-headers package (version ${VERSION})…"

# Ensure required tooling is available
python -m pip install --quiet --upgrade pip build twine

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build source distribution and wheel
python -m build

# Verify metadata renders correctly on PyPI
python -m twine check dist/*

echo "Build complete. Files in dist/:"
ls -la dist/
