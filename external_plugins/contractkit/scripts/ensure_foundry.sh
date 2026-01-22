#!/usr/bin/env bash
set -euo pipefail

# Check if Foundry tools are installed

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 not found"
        return 1
    fi
    echo "Found: $1 ($(command -v "$1"))"
    return 0
}

echo "Checking Foundry installation..."
echo

missing=0

check_command forge || missing=1
check_command anvil || missing=1
check_command cast || missing=1

echo

if [ $missing -eq 1 ]; then
    echo "Foundry tools are missing. Install with:"
    echo
    echo "  curl -L https://foundry.paradigm.xyz | bash"
    echo "  foundryup"
    echo
    exit 1
fi

echo "Foundry installation verified."
forge --version
