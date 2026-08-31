# flashgate

The agent can't claim the firmware works — until the board says so.

flashgate is a hardware-in-the-loop verification gate for firmware work.
When the agent modifies watched firmware files (`.c/.h/.ld/.ioc`...) and
tries to finish, the Stop hook runs the full loop on real hardware:

```
build → flash over a debug probe → board reports its identity → functional probes → exit code
```

If any step fails, the stop is blocked and the agent receives the board's
own failure testimony (which probe step failed, what the hardware read
back) and the exact command to run. The same broken tree is blocked at
most twice, then released with a loud warning — the gate never wedges a
session and never silently gives up.

Two evidence channels, per bench:

- **UART banner** — the firmware prints its identity (git sha + build
  time, `-dirty` when the tree differs from HEAD) over the console; a
  passing verify proves the board runs exactly the working copy.
- **SWD signature** — the firmware publishes a 64-byte signed identity at
  a fixed RAM address, read through the debug probe alone. No serial
  cable needed for boot verification.

Functional probes send real commands over the console and assert on the
answers, including hardware register readbacks (e.g. timer CCR), with
set-command replies reporting read-back state — a silently broken setter
fails the probe on step one.

## Requirements

- Python 3.11+ and the flashgate CLI:
  `pip install git+https://github.com/Lion-1209/flashgate`
  (add `"[mcp]"` for the bundled MCP server)
- A debug probe (ST-Link) and, for probes, a USB-TTL adapter on the
  board's console UART. Toolchain is auto-discovered from STM32Cube
  bundles or PATH.
- A board profile (yaml) describing your firmware build, flash address,
  and evidence channels — set `FLASHGATE_BOARD` to its path. Complete
  three-level firmware integration recipe with copy-pasteable code:
  [docs/GUIDE.md](https://github.com/Lion-1209/flashgate/blob/main/docs/GUIDE.md).

## What's in the plugin

- Stop hook (`hooks/`) — the enforcement gate
- Skill `flashgate-integration` — guides an agent through wiring a new
  board into flashgate (banner / RAM signature / probe commands)
- Commands `/flashgate-verify` and `/flashgate-doctor`
- MCP server (board_info / doctor / build / flash / verify / probe /
  console_send / console_read)

## Try it with the bundled example

The repository ships a complete buildable example for the ALIENTEK Apollo
STM32H743 (banner + signature + probe protocol + six real-hardware
recordings, including a full session of an agent getting blocked,
diagnosing, and passing): <https://github.com/Lion-1209/flashgate>

MIT license. Windows-first; Linux/macOS untested.
