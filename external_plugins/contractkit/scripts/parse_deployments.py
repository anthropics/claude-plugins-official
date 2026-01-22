#!/usr/bin/env python3
"""Parse Forge broadcast output and write deployment addresses."""

import json
import sys
from pathlib import Path


def find_latest_broadcast(network: str = "31337") -> Path | None:
    """Find the latest broadcast run file for a network."""
    broadcast_dir = Path("broadcast")
    if not broadcast_dir.exists():
        return None

    # Look for run-latest.json in any script subdirectory
    for run_file in broadcast_dir.glob(f"*/{network}/run-latest.json"):
        return run_file

    return None


def parse_broadcast(broadcast_file: Path) -> dict:
    """Parse broadcast file and extract contract addresses."""
    with open(broadcast_file) as f:
        data = json.load(f)

    deployments = {}
    for tx in data.get("transactions", []):
        if tx.get("transactionType") == "CREATE":
            name = tx.get("contractName", "Unknown")
            address = tx.get("contractAddress")
            if address:
                deployments[name] = address

    return deployments


def write_deployments(deployments: dict, network: str, output_dir: Path):
    """Write deployments to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{network}.json"

    # Merge with existing if present
    existing = {}
    if output_file.exists():
        with open(output_file) as f:
            existing = json.load(f)

    existing.update(deployments)

    with open(output_file, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"Wrote deployments to {output_file}")
    for name, addr in deployments.items():
        print(f"  {name}: {addr}")


def main():
    network = sys.argv[1] if len(sys.argv) > 1 else "local"

    # Map network names to chain IDs
    chain_ids = {
        "local": "31337",
        "sepolia": "11155111",
    }

    chain_id = chain_ids.get(network, network)

    broadcast_file = find_latest_broadcast(chain_id)
    if not broadcast_file:
        print(f"No broadcast found for network {network} (chain {chain_id})")
        sys.exit(1)

    print(f"Parsing {broadcast_file}...")
    deployments = parse_broadcast(broadcast_file)

    if not deployments:
        print("No contract deployments found")
        sys.exit(1)

    write_deployments(deployments, network, Path("deployments"))


if __name__ == "__main__":
    main()
