#!/usr/bin/env bash
set -euo pipefail

# Deploy to local Anvil chain

RPC_URL="${LOCAL_RPC_URL:-http://127.0.0.1:8545}"

if [ ! -f "script/Deploy.s.sol" ]; then
    echo "Error: script/Deploy.s.sol not found"
    exit 1
fi

echo "Deploying to local chain at $RPC_URL..."
echo

forge script script/Deploy.s.sol \
    --rpc-url "$RPC_URL" \
    --broadcast \
    -vvv

echo
echo "Deployment complete. Check broadcast/ for transaction details."
