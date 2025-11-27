#!/bin/bash

# Lint all markdown files and show consolidated error reporting
# This addresses the issue where markdownlint-cli2 shows errors in groups

echo "Running markdown lint on all files..."

# Use markdownlint-cli2 to lint all files at once for better performance
# This will show all errors together instead of in groups
markdownlint-cli2 "**/*.md" --config .markdownlint.json