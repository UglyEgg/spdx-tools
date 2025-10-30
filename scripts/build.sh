#!/bin/bash
# File: /home/uglyegg/Repos/spdx_tools/scripts/build.sh

set -e

echo "Building spdx-headers package..."

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

echo "Build complete. Files in dist/:"
ls -la dist/
