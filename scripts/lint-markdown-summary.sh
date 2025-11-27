#!/bin/bash

# Lint all markdown files with file-by-file breakdown
# This provides detailed error reporting for each file

echo "Running markdown lint with detailed breakdown..."

# Create a temporary file to collect all errors
TEMP_FILE=$(mktemp)
ERROR_COUNT=0

# Get all markdown files in the project, excluding common ignore directories
find . -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "./.pytest_cache/*" | sort | while read -r file; do
    # Check each file individually and collect errors
    if markdownlint-cli2 "$file" --config .markdownlint.json 2>/dev/null | grep -q "error"; then
        echo "=== Errors in $file ===" >> "$TEMP_FILE"
        markdownlint-cli2 "$file" --config .markdownlint.json 2>&1 | grep "error" >> "$TEMP_FILE"
        echo "" >> "$TEMP_FILE"
    fi
done

# Display the collected errors
if [ -s "$TEMP_FILE" ]; then
    echo "Markdown linting found errors:"
    echo "============================="
    cat "$TEMP_FILE"
    
    # Count total errors
    ERROR_COUNT=$(grep -c "error" "$TEMP_FILE")
    echo "============================="
    echo "Total errors: $ERROR_COUNT"
    echo "============================="
    
    # Clean up
    rm "$TEMP_FILE"
    exit 1
else
    echo "✅ All markdown files passed linting!"
    rm "$TEMP_FILE"
    exit 0
fi