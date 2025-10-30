#!/bin/bash
# File: /home/uglyegg/Repos/spdx_tools/scripts/release.sh

set -e

echo "Releasing spdx-headers to PyPI..."

# Build first
./scripts/build.sh

# Upload to PyPI
python -m twine upload dist/*

echo "Release complete!"
