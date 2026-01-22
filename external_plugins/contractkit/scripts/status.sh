#!/usr/bin/env bash
set -euo pipefail

# Show project status and deployment info

echo "=== Project Status ==="
echo

if [ -f "foundry.toml" ]; then
    echo "Project: $(basename "$(pwd)")"
else
    echo "Error: Not in a Foundry project directory"
    exit 1
fi

echo

# Check local chain
echo "=== Local Chain ==="
RPC_URL="${LOCAL_RPC_URL:-http://127.0.0.1:8545}"
if curl -s -X POST -H "Content-Type: application/json" \
    --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    "$RPC_URL" > /dev/null 2>&1; then
    echo "Status: Running at $RPC_URL"
    BLOCK=$(cast block-number --rpc-url "$RPC_URL" 2>/dev/null || echo "unknown")
    echo "Block: $BLOCK"
else
    echo "Status: Not running"
fi

echo

# Check deployments
echo "=== Deployments ==="
if [ -d "deployments" ]; then
    for file in deployments/*.json; do
        if [ -f "$file" ]; then
            echo "Found: $file"
        fi
    done
    if [ ! "$(ls -A deployments/*.json 2>/dev/null)" ]; then
        echo "No deployments found"
    fi
else
    echo "No deployments directory"
fi

echo

# Check broadcast
echo "=== Recent Broadcasts ==="
if [ -d "broadcast" ]; then
    find broadcast -name "run-latest.json" -type f 2>/dev/null | head -5 || echo "No broadcasts found"
else
    echo "No broadcast directory"
fi
