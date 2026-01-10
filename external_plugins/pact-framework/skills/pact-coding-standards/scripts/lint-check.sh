#!/bin/bash
# ============================================================================
# PACT Coding Standards - Lint Check Script
# ============================================================================
# Location: ~/.claude/skills/pact-coding-standards/scripts/lint-check.sh
# Purpose: Run appropriate linter based on detected project type
# Usage: ./lint-check.sh [directory]
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directory to check (default to current)
DIR="${1:-.}"

echo "Running lint check in: $DIR"
echo "----------------------------------------"

# Detect project type and run appropriate linter
if [ -f "$DIR/package.json" ]; then
    echo -e "${GREEN}Detected: Node.js/JavaScript project${NC}"

    # Check for lint script in package.json
    if grep -q '"lint"' "$DIR/package.json"; then
        echo "Running: npm run lint"
        cd "$DIR" && npm run lint 2>&1 || {
            echo -e "${RED}Linting issues found${NC}"
            exit 1
        }
    elif [ -f "$DIR/.eslintrc.js" ] || [ -f "$DIR/.eslintrc.json" ] || [ -f "$DIR/eslint.config.js" ]; then
        echo "Running: npx eslint ."
        cd "$DIR" && npx eslint . --ext .js,.jsx,.ts,.tsx 2>&1 || {
            echo -e "${RED}Linting issues found${NC}"
            exit 1
        }
    else
        echo -e "${YELLOW}No ESLint configuration found${NC}"
        echo "Consider adding ESLint: npm init @eslint/config"
    fi

elif [ -f "$DIR/pyproject.toml" ] || [ -f "$DIR/setup.py" ]; then
    echo -e "${GREEN}Detected: Python project${NC}"

    # Try different Python linters
    if command -v ruff &> /dev/null; then
        echo "Running: ruff check"
        cd "$DIR" && ruff check . 2>&1 || {
            echo -e "${RED}Linting issues found${NC}"
            exit 1
        }
    elif command -v flake8 &> /dev/null; then
        echo "Running: flake8"
        cd "$DIR" && python -m flake8 . 2>&1 || {
            echo -e "${RED}Linting issues found${NC}"
            exit 1
        }
    elif command -v pylint &> /dev/null; then
        echo "Running: pylint"
        cd "$DIR" && pylint **/*.py 2>&1 || {
            echo -e "${RED}Linting issues found${NC}"
            exit 1
        }
    else
        echo -e "${YELLOW}No Python linter found${NC}"
        echo "Consider installing: pip install ruff"
    fi

elif [ -f "$DIR/go.mod" ]; then
    echo -e "${GREEN}Detected: Go project${NC}"

    echo "Running: go vet"
    cd "$DIR" && go vet ./... 2>&1 || {
        echo -e "${RED}Go vet found issues${NC}"
        exit 1
    }

    if command -v golangci-lint &> /dev/null; then
        echo "Running: golangci-lint"
        cd "$DIR" && golangci-lint run 2>&1 || {
            echo -e "${RED}Linting issues found${NC}"
            exit 1
        }
    fi

elif [ -f "$DIR/Cargo.toml" ]; then
    echo -e "${GREEN}Detected: Rust project${NC}"

    echo "Running: cargo clippy"
    cd "$DIR" && cargo clippy -- -D warnings 2>&1 || {
        echo -e "${RED}Clippy found issues${NC}"
        exit 1
    }

else
    echo -e "${YELLOW}No recognized project type found${NC}"
    echo "Supported project types:"
    echo "  - Node.js (package.json)"
    echo "  - Python (pyproject.toml or setup.py)"
    echo "  - Go (go.mod)"
    echo "  - Rust (Cargo.toml)"
    exit 0
fi

echo "----------------------------------------"
echo -e "${GREEN}Lint check passed!${NC}"
