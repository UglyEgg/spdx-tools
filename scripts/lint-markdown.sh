#!/bin/bash

# Markdown Linting Script with Multiple Output Formats
# This script provides 4 different output formats for markdown linting results

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default output format
FORMAT="${1:-compact}"

# Function to get all markdown files (excluding ignored directories)
get_markdown_files() {
    find . -name "*.md" \
        -not -path "./.git/*" \
        -not -path "./.venv/*" \
        -not -path "./venv/*" \
        -not -path "./env/*" \
        -not -path "./.uv/*" \
        -not -path "./.uv-cache/*" \
        -not -path "./build/*" \
        -not -path "./dist/*" \
        -not -path "./*.egg-info/*" \
        -not -path "./.pytest_cache/*" \
        -not -path "./node_modules/*" \
        -not -name "MARKDOWN_LINTING_QUICK_REFERENCE.md" \
        -not -name "MARKDOWN_LINTING_IMPROVEMENTS_SUMMARY.md" \
        -not -path "./docs/MARKDOWN_LINTING.md" \
        | sort
}

# Function to lint a single file and capture output
lint_file() {
    local file="$1"
    markdownlint-cli2 "$file" --config .markdownlint.json 2>&1 | grep -v "^markdownlint-cli2" | grep -v "^Finding:" | grep -v "^Linting:" | grep -v "^Summary:"
}

# Function to parse error line
parse_error() {
    local line="$1"
    # Extract: filename:line:col error MD### description
    if [[ $line =~ ^(.+):([0-9]+):?([0-9]*)?[[:space:]]+(error|warning)[[:space:]]+([A-Z0-9]+)/([a-z-]+)[[:space:]]+(.+)$ ]]; then
        echo "${BASH_REMATCH[1]}|${BASH_REMATCH[2]}|${BASH_REMATCH[3]}|${BASH_REMATCH[5]}|${BASH_REMATCH[6]}|${BASH_REMATCH[7]}"
    elif [[ $line =~ ^(.+):([0-9]+)[[:space:]]+(error|warning)[[:space:]]+([A-Z0-9]+)/([a-z-]+)[[:space:]]+(.+)$ ]]; then
        echo "${BASH_REMATCH[1]}|${BASH_REMATCH[2]}||${BASH_REMATCH[4]}|${BASH_REMATCH[5]}|${BASH_REMATCH[6]}"
    fi
}

# Format 1: Compact - One line per error with colors
format_compact() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Results (Compact Format)${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_errors=0
    local files_with_errors=0

    while IFS= read -r file; do
        local output=$(lint_file "$file")
        if echo "$output" | grep -q "error"; then
            ((files_with_errors++))
            while IFS= read -r line; do
                if [[ $line =~ error ]]; then
                    ((total_errors++))
                    local parsed=$(parse_error "$line")
                    if [ -n "$parsed" ]; then
                        IFS='|' read -r fname lnum col rule_id rule_name desc <<< "$parsed"
                        echo -e "${RED}✗${NC} ${BOLD}$fname${NC}:${YELLOW}$lnum${NC} ${CYAN}[$rule_id]${NC} $desc"
                    else
                        echo -e "${RED}✗${NC} $line"
                    fi
                fi
            done <<< "$output"
        fi
    done < <(get_markdown_files)

    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ All markdown files passed linting!${NC}"
    else
        echo -e "${RED}${BOLD}Found $total_errors error(s) in $files_with_errors file(s)${NC}"
        echo -e "${YELLOW}Run with 'grouped' format for better organization${NC}"
    fi
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Format 2: Grouped - Errors grouped by file
format_grouped() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Results (Grouped by File)${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_errors=0
    local files_with_errors=0

    while IFS= read -r file; do
        local output=$(lint_file "$file")
        if echo "$output" | grep -q "error"; then
            ((files_with_errors++))
            echo -e "${BOLD}${YELLOW}📄 $file${NC}"

            local file_errors=0
            while IFS= read -r line; do
                if [[ $line =~ error ]]; then
                    ((total_errors++))
                    ((file_errors++))
                    local parsed=$(parse_error "$line")
                    if [ -n "$parsed" ]; then
                        IFS='|' read -r fname lnum col rule_id rule_name desc <<< "$parsed"
                        echo -e "   ${RED}✗${NC} Line ${YELLOW}$lnum${NC} ${CYAN}[$rule_id]${NC} $desc"
                    else
                        echo -e "   ${RED}✗${NC} $line"
                    fi
                fi
            done <<< "$output"
            echo -e "   ${BOLD}Errors in this file: ${RED}$file_errors${NC}"
            echo ""
        fi
    done < <(get_markdown_files)

    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ All markdown files passed linting!${NC}"
    else
        echo -e "${RED}${BOLD}Summary: $total_errors error(s) in $files_with_errors file(s)${NC}"
    fi
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Format 3: Detailed - Full error details with context
format_detailed() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Results (Detailed Format)${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_errors=0
    local files_with_errors=0

    while IFS= read -r file; do
        local output=$(lint_file "$file")
        if echo "$output" | grep -q "error"; then
            ((files_with_errors++))
            echo -e "${BOLD}${YELLOW}╔════════════════════════════════════════════════════════════════════${NC}"
            echo -e "${BOLD}${YELLOW}║ 📄 File: $file${NC}"
            echo -e "${BOLD}${YELLOW}╚════════════════════════════════════════════════════════════════════${NC}"
            echo ""

            local file_errors=0
            while IFS= read -r line; do
                if [[ $line =~ error ]]; then
                    ((total_errors++))
                    ((file_errors++))
                    local parsed=$(parse_error "$line")
                    if [ -n "$parsed" ]; then
                        IFS='|' read -r fname lnum col rule_id rule_name desc <<< "$parsed"
                        echo -e "${RED}  ✗ Error #$file_errors${NC}"
                        echo -e "    ${BOLD}Location:${NC} Line ${YELLOW}$lnum${NC}$([ -n "$col" ] && echo ", Column $col")"
                        echo -e "    ${BOLD}Rule:${NC}     ${CYAN}$rule_id${NC} ($rule_name)"
                        echo -e "    ${BOLD}Issue:${NC}    $desc"
                        echo ""
                    else
                        echo -e "${RED}  ✗ Error #$file_errors${NC}"
                        echo -e "    $line"
                        echo ""
                    fi
                fi
            done <<< "$output"
            echo -e "${BOLD}  Total errors in this file: ${RED}$file_errors${NC}"
            echo ""
        fi
    done < <(get_markdown_files)

    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ All markdown files passed linting!${NC}"
    else
        echo -e "${RED}${BOLD}SUMMARY${NC}"
        echo -e "  Total errors: ${RED}$total_errors${NC}"
        echo -e "  Files affected: ${RED}$files_with_errors${NC}"
    fi
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Format 4: Summary - Just counts and file list
format_summary() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Summary${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_errors=0
    local files_with_errors=0
    local -A file_error_counts

    while IFS= read -r file; do
        local output=$(lint_file "$file")
        if echo "$output" | grep -q "error"; then
            ((files_with_errors++))
            local file_errors=$(echo "$output" | grep -c "error")
            file_error_counts["$file"]=$file_errors
            total_errors=$((total_errors + file_errors))
        fi
    done < <(get_markdown_files)

    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ All markdown files passed linting!${NC}"
        echo ""
        local total_files=$(get_markdown_files | wc -l)
        echo -e "  Files checked: ${GREEN}$total_files${NC}"
    else
        echo -e "${RED}${BOLD}✗ Linting found issues${NC}"
        echo ""
        echo -e "${BOLD}Statistics:${NC}"
        echo -e "  Total errors: ${RED}$total_errors${NC}"
        echo -e "  Files with errors: ${RED}$files_with_errors${NC}"
        echo ""
        echo -e "${BOLD}Files needing fixes:${NC}"
        for file in "${!file_error_counts[@]}"; do
            echo -e "  ${RED}✗${NC} ${BOLD}$file${NC} (${RED}${file_error_counts[$file]}${NC} error(s))"
        done
        echo ""
        echo -e "${YELLOW}💡 Tip: Run with 'grouped' or 'detailed' format to see specific errors${NC}"
    fi

    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Main execution
case "$FORMAT" in
    compact)
        format_compact
        ;;
    grouped)
        format_grouped
        ;;
    detailed)
        format_detailed
        ;;
    summary)
        format_summary
        ;;
    *)
        echo -e "${RED}Error: Unknown format '$FORMAT'${NC}"
        echo ""
        echo "Usage: $0 [format]"
        echo ""
        echo "Available formats:"
        echo "  compact  - One line per error (default)"
        echo "  grouped  - Errors grouped by file"
        echo "  detailed - Full error details with context"
        echo "  summary  - Just counts and file list"
        exit 1
        ;;
esac

exit $?
