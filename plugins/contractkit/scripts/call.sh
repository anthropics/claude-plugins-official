#!/usr/bin/env bash
set -euo pipefail

# Call a contract function using cast

usage() {
    echo "Usage: $0 <address> <function_sig> [args...]"
    echo
    echo "Examples:"
    echo "  $0 0x123... 'balanceOf(address)' 0xabc..."
    echo "  $0 0x123... 'name()'"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
fi

ADDRESS="$1"
FUNCTION_SIG="$2"
shift 2

RPC_URL="${LOCAL_RPC_URL:-http://127.0.0.1:8545}"

echo "Calling $FUNCTION_SIG on $ADDRESS"
echo "RPC: $RPC_URL"
echo

cast call "$ADDRESS" "$FUNCTION_SIG" "$@" --rpc-url "$RPC_URL"
