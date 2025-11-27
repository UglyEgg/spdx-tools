#!/bin/bash

# Markdown Linting Summary Script with Multiple Output Formats
# This script provides 4 different summary formats for markdown linting results

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default output format
FORMAT="${1:-table}"

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

# Function to count errors by rule
count_errors_by_rule() {
    local -n rules_ref=$1
    local -n counts_ref=$2

    while IFS= read -r file; do
        local output=$(lint_file "$file")
        while IFS= read -r line; do
            if [[ $line =~ error[[:space:]]+([A-Z0-9]+)/ ]]; then
                local rule="${BASH_REMATCH[1]}"
                if [[ ! " ${rules_ref[@]} " =~ " ${rule} " ]]; then
                    rules_ref+=("$rule")
                fi
                counts_ref["$rule"]=$((${counts_ref["$rule"]:-0} + 1))
            fi
        done <<< "$output"
    done < <(get_markdown_files)
}

# Format 1: Table - Organized table view
format_table() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Summary (Table View)${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_errors=0
    local files_with_errors=0
    local -A file_error_counts

    # Collect data
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
        # Print table header
        echo -e "${BOLD}┌─────────────────────────────────────────────────────────┬──────────┐${NC}"
        echo -e "${BOLD}│ File                                                    │  Errors  │${NC}"
        echo -e "${BOLD}├─────────────────────────────────────────────────────────┼──────────┤${NC}"

        # Print table rows
        for file in $(printf '%s\n' "${!file_error_counts[@]}" | sort); do
            local errors=${file_error_counts[$file]}
            local display_file="$file"

            # Truncate filename if too long
            if [ ${#display_file} -gt 55 ]; then
                display_file="...${display_file: -52}"
            fi

            printf "${BOLD}│${NC} %-55s ${BOLD}│${NC} ${RED}%6d${NC}   ${BOLD}│${NC}\n" "$display_file" "$errors"
        done

        echo -e "${BOLD}├─────────────────────────────────────────────────────────┼──────────┤${NC}"
        printf "${BOLD}│${NC} %-55s ${BOLD}│${NC} ${RED}%6d${NC}   ${BOLD}│${NC}\n" "TOTAL" "$total_errors"
        echo -e "${BOLD}└─────────────────────────────────────────────────────────┴──────────┘${NC}"
        echo ""
        echo -e "${YELLOW}💡 Run 'make lint-markdown grouped' to see detailed errors${NC}"
    fi

    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Format 2: Stats - Statistical breakdown
format_stats() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Statistics${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_files=$(get_markdown_files | wc -l)
    local total_errors=0
    local files_with_errors=0
    local -a rules
    local -A rule_counts

    # Collect data
    while IFS= read -r file; do
        local output=$(lint_file "$file")
        if echo "$output" | grep -q "error"; then
            ((files_with_errors++))
            local file_errors=$(echo "$output" | grep -c "error")
            total_errors=$((total_errors + file_errors))

            # Count by rule
            while IFS= read -r line; do
                if [[ $line =~ error[[:space:]]+([A-Z0-9]+)/ ]]; then
                    local rule="${BASH_REMATCH[1]}"
                    if [[ ! " ${rules[@]} " =~ " ${rule} " ]]; then
                        rules+=("$rule")
                    fi
                    rule_counts["$rule"]=$((${rule_counts["$rule"]:-0} + 1))
                fi
            done <<< "$output"
        fi
    done < <(get_markdown_files)

    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ Perfect! All markdown files passed linting!${NC}"
        echo ""
        echo -e "${BOLD}📊 Statistics:${NC}"
        echo -e "  Files checked: ${GREEN}$total_files${NC}"
        echo -e "  Files with errors: ${GREEN}0${NC}"
        echo -e "  Total errors: ${GREEN}0${NC}"
    else
        echo -e "${BOLD}📊 Overall Statistics:${NC}"
        echo -e "  Total files checked: ${CYAN}$total_files${NC}"
        echo -e "  Files with errors: ${RED}$files_with_errors${NC} (${YELLOW}$(( files_with_errors * 100 / total_files ))%${NC})"
        echo -e "  Files passing: ${GREEN}$(( total_files - files_with_errors ))${NC} (${GREEN}$(( (total_files - files_with_errors) * 100 / total_files ))%${NC})"
        echo -e "  Total errors: ${RED}$total_errors${NC}"
        echo -e "  Average errors per file: ${YELLOW}$(( total_errors / files_with_errors ))${NC}"
        echo ""

        echo -e "${BOLD}📋 Errors by Rule:${NC}"
        for rule in $(printf '%s\n' "${rules[@]}" | sort); do
            local count=${rule_counts[$rule]}
            local percentage=$(( count * 100 / total_errors ))
            printf "  ${CYAN}%-8s${NC} ${RED}%3d${NC} errors (${YELLOW}%3d%%${NC})\n" "$rule" "$count" "$percentage"
        done
        echo ""

        echo -e "${YELLOW}💡 Focus on fixing ${CYAN}${rules[0]}${NC} errors first for maximum impact${NC}"
    fi

    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Format 3: Tree - Hierarchical tree view
format_tree() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Tree View${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_errors=0
    local files_with_errors=0
    local -A dir_errors
    local -A file_error_counts

    # Collect data
    while IFS= read -r file; do
        local output=$(lint_file "$file")
        if echo "$output" | grep -q "error"; then
            ((files_with_errors++))
            local file_errors=$(echo "$output" | grep -c "error")
            file_error_counts["$file"]=$file_errors
            total_errors=$((total_errors + file_errors))

            # Track directory errors
            local dir=$(dirname "$file")
            dir_errors["$dir"]=$((${dir_errors["$dir"]:-0} + file_errors))
        fi
    done < <(get_markdown_files)

    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ All markdown files passed linting!${NC}"
        echo ""
        local total_files=$(get_markdown_files | wc -l)
        echo -e "  Files checked: ${GREEN}$total_files${NC}"
    else
        echo -e "${BOLD}Project Root${NC} ${RED}($total_errors errors)${NC}"
        echo "│"

        # Get unique directories
        local -a dirs=($(printf '%s\n' "${!dir_errors[@]}" | sort))
        local dir_count=${#dirs[@]}

        for i in "${!dirs[@]}"; do
            local dir="${dirs[$i]}"
            local dir_error_count=${dir_errors[$dir]}
            local is_last=$((i == dir_count - 1))

            if [ "$is_last" = "1" ]; then
                echo -e "└── ${BOLD}${YELLOW}$dir/${NC} ${RED}($dir_error_count errors)${NC}"
                local prefix="    "
            else
                echo -e "├── ${BOLD}${YELLOW}$dir/${NC} ${RED}($dir_error_count errors)${NC}"
                local prefix="│   "
            fi

            # List files in this directory
            local -a dir_files=()
            for file in "${!file_error_counts[@]}"; do
                if [[ $(dirname "$file") == "$dir" ]]; then
                    dir_files+=("$file")
                fi
            done

            local file_count=${#dir_files[@]}
            for j in "${!dir_files[@]}"; do
                local file="${dir_files[$j]}"
                local file_errors=${file_error_counts[$file]}
                local filename=$(basename "$file")
                local is_last_file=$((j == file_count - 1))

                if [ "$is_last_file" = "1" ]; then
                    echo -e "${prefix}└── ${filename} ${RED}($file_errors errors)${NC}"
                else
                    echo -e "${prefix}├── ${filename} ${RED}($file_errors errors)${NC}"
                fi
            done
        done

        echo ""
        echo -e "${YELLOW}💡 Use 'make lint-markdown grouped' to see specific errors${NC}"
    fi

    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Format 4: Quick - Minimal output for CI/CD
format_quick() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}Markdown Linting Quick Check${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local total_errors=0
    local files_with_errors=0

    while IFS= read -r file; do
        local output=$(lint_file "$file")
        if echo "$output" | grep -q "error"; then
            ((files_with_errors++))
            local file_errors=$(echo "$output" | grep -c "error")
            total_errors=$((total_errors + file_errors))
        fi
    done < <(get_markdown_files)

    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ PASS${NC} - All markdown files are valid"
    else
        echo -e "${RED}${BOLD}✗ FAIL${NC} - Found $total_errors error(s) in $files_with_errors file(s)"
        echo ""
        echo -e "${BOLD}Quick Fix Guide:${NC}"
        echo -e "  1. Run: ${CYAN}make lint-markdown grouped${NC}"
        echo -e "  2. Fix errors in each file"
        echo -e "  3. Run: ${CYAN}make lint-markdown${NC} to verify"
    fi

    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return $total_errors
}

# Main execution
case "$FORMAT" in
    table)
        format_table
        ;;
    stats)
        format_stats
        ;;
    tree)
        format_tree
        ;;
    quick)
        format_quick
        ;;
    *)
        echo -e "${RED}Error: Unknown format '$FORMAT'${NC}"
        echo ""
        echo "Usage: $0 [format]"
        echo ""
        echo "Available formats:"
        echo "  table - Organized table view (default)"
        echo "  stats - Statistical breakdown with percentages"
        echo "  tree  - Hierarchical tree view by directory"
        echo "  quick - Minimal output for CI/CD pipelines"
        exit 1
        ;;
esac

exit $?
