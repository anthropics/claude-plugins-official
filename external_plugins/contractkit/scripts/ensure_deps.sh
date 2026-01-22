#!/usr/bin/env bash
set -euo pipefail

# Install Foundry dependencies for a project

if [ ! -f "foundry.toml" ]; then
    echo "Error: No foundry.toml found. Run this from a Foundry project directory."
    exit 1
fi

echo "Installing dependencies..."

# Install OpenZeppelin contracts if not present
if [ ! -d "lib/openzeppelin-contracts" ]; then
    echo "Installing OpenZeppelin contracts..."
    forge install OpenZeppelin/openzeppelin-contracts --no-commit
fi

# Install forge-std if not present
if [ ! -d "lib/forge-std" ]; then
    echo "Installing forge-std..."
    forge install foundry-rs/forge-std --no-commit
fi

echo "Dependencies installed."
