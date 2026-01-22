#!/usr/bin/env bash
set -euo pipefail

# Deploy to Sepolia testnet

if [ -z "${SEPOLIA_RPC_URL:-}" ]; then
    echo "Error: SEPOLIA_RPC_URL environment variable not set"
    echo "Set it in your .env file or export it"
    exit 1
fi

if [ ! -f "script/Deploy.s.sol" ]; then
    echo "Error: script/Deploy.s.sol not found"
    exit 1
fi

echo "Deploying to Sepolia..."
echo "RPC: $SEPOLIA_RPC_URL"
echo

VERIFY_FLAG=""
if [ -n "${ETHERSCAN_API_KEY:-}" ]; then
    VERIFY_FLAG="--verify"
    echo "Etherscan verification enabled"
fi

forge script script/Deploy.s.sol \
    --rpc-url "$SEPOLIA_RPC_URL" \
    --broadcast \
    $VERIFY_FLAG \
    -vvv

echo
echo "Deployment complete. Check broadcast/ for transaction details."
