---
name: server-setup
description: "Use when the user or agent needs a cloud server, VM, VPS, or compute instance. Triggers on: server setup, spin up a server, provision a vps, deploy to a server, I need a machine, launch an instance, run this on a server."
---

# MachineMarket Server Setup

Provision a VPS on MachineMarket end-to-end: configure, pay USDC on Base, get SSH credentials.

## Step 1: Choose Mode

Ask the user ONE question:

- **Auto** — You (the agent) decide everything based on the current project context. No follow-up questions. Go straight to payment.
- **Interactive** — Walk the user through each config choice one at a time.

## Step 2: Configure

### Auto mode

Analyze the workspace and decide silently:

| Config | How to decide |
|--------|---------------|
| Template | `package.json` → `node`. `requirements.txt` / `pyproject.toml` → `python`. Agent framework configs → `agent`. Else → `base` |
| Tier | Simple script/bot → `Nano`. Web app / API → `Small`. Multi-service / builds → `Medium`. Heavy compute / DB → `Large` |
| Duration | Quick test → `1h`. Dev server → `24h`. Staging → `7d`. Long-running → `30d` |
| Region | Default `fsn1`. US-based user → `ash` or `hil` |

Announce your choices and reasoning in one short paragraph, then proceed.

### Interactive mode

Ask one at a time using AskUserQuestion:

1. **Template**: base (Ubuntu 24.04), node (Node.js 22 + pnpm), python (Python 3.12 + CUDA), agent (OpenClaw + tmux)
2. **Tier**: Nano (2 vCPU / 4 GB / $0.015/hr), Small (4 vCPU / 8 GB / $0.028/hr), Medium (8 vCPU / 16 GB / $0.055/hr), Large (16 vCPU / 32 GB / $0.105/hr)
3. **Duration**: 1h, 24h, 7d, 30d
4. **Region**: Falkenstein DE (fsn1), Nuremberg DE (nbg1), Helsinki FI (hel1), Ashburn US (ash), Hillsboro US (hil)

## Step 3: Show Cost

Formula: `tier_hourly_rate * duration_hours`

Duration map: 1h=1, 24h=24, 7d=168, 30d=720

Display total in USDC before proceeding.

## Step 4: Payment

Detect payment method in priority order:

### Path A: WALLET_PRIVATE_KEY env var + `cast` installed

Auto-send USDC:

```bash
cast wallet address --private-key $WALLET_PRIVATE_KEY
cast send 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 \
  "transfer(address,uint256)(bool)" \
  0x8997292508bAbbe5B40d28a89588a5926d342992 \
  <amount_in_smallest_unit> \
  --rpc-url https://mainnet.base.org \
  --private-key $WALLET_PRIVATE_KEY
```

Amount = cost * 1000000 (USDC has 6 decimals). Extract tx hash. Wait 30s for 12+ confirmations.

### Path B: `moonpay` CLI in PATH

Use MoonPay CLI to send USDC from the agent's wallet. Check balance, swap ETH→USDC if needed, transfer to MachineMarket wallet. Extract tx hash.

### Path C: Manual fallback

Show payment details:
- **Chain**: Base (8453)
- **USDC contract**: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- **Recipient**: `0x8997292508bAbbe5B40d28a89588a5926d342992`
- **Amount**: calculated USDC cost

Print a ready-to-copy `cast send` command. Ask user to paste the tx hash.

## Step 5: Spawn

```bash
curl -s -X POST https://machinemarket.ai/api/v1/spawn \
  -H "Content-Type: application/json" \
  -d '{"tier":"<tier>","template":"<template>","duration":"<duration>","region":"<region>","tx_hash":"<tx_hash>","wallet_address":"<wallet_address>"}'
```

Override base URL with `MACHINEMARKET_API_URL` env var if set.

## Step 6: Display Results

Show: Instance ID, IP address, `ssh root@<ip>`, SSH private key (save to temp file if generated), expiry, cost.

If status is `"provisioning"`, poll `GET /v1/instances/<id>` every 10s until `"running"`.

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 402 | Payment invalid | Wait 30s, retry, or check basescan.org |
| 409 | TX already used | Send a new USDC transfer |
| 429 | Wallet limit (10) | Destroy old instances first |
| 502 | Provisioning failed | Retry in ~1 minute |

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `MACHINEMARKET_API_URL` | No | Default: `https://machinemarket.ai` |
| `WALLET_PRIVATE_KEY` | No | Auto-execute payment |
| `WALLET_ADDRESS` | No | Derived from key if unset |
