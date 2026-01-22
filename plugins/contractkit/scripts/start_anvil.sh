#!/usr/bin/env bash
set -euo pipefail

# Start Anvil local blockchain

PORT="${ANVIL_PORT:-8545}"

echo "Starting Anvil on port $PORT..."
echo
echo "RPC URL: http://127.0.0.1:$PORT"
echo
echo "Default accounts available for testing."
echo "Press Ctrl+C to stop."
echo

anvil --port "$PORT"
