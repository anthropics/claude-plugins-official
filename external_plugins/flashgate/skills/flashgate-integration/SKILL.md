---
name: flashgate-integration
description: Connect a firmware project to flashgate hardware-in-the-loop verification. Use when the user wants their board/MCU project verified on real hardware by an agent, wants probes or a boot gate, or asks to "接入 flashgate / wire this board into flashgate".
---

# flashgate 固件对接 / Firmware Integration

flashgate verifies firmware on real hardware: build → flash over a debug
probe → board reports its identity → probes drive features and assert on
register readbacks. Integration is three independent levels; start at
level 1, add levels as needed. Full field reference and worked code:
`docs/GUIDE.md` sections 6–7 in the flashgate repository
(https://github.com/Lion-1209/flashgate).

## Prerequisites to check first

1. Is the `flashgate` CLI installed? Run `flashgate --version`. If missing:
   `pip install git+https://github.com/Lion-1209/flashgate`
2. Is there a board profile (yaml)? Look for `boards/*.yaml` in the
   firmware repo or `$FLASHGATE_BOARD`. If none exists, create one (level
   1 below creates a minimal one).
3. Debug probe wired (ST-Link or compatible) and a serial console
   (USB-TTL) if probes are wanted. `flashgate doctor` reports what it can
   see — run it before writing any code.

## Level 1 — boot banner (uart evidence)

Firmware: after peripheral init, before the RTOS/main loop, print one
line carrying a build-time version (never hand-written):

```c
printf("\r\nFLASHGATE-BOOT board=%s git=%s build=%s\r\n",
        "my-board", APP_GIT_SHA, APP_BUILD_ISO);
```

Generate `APP_GIT_SHA` / `APP_BUILD_ISO` at EVERY build (not configure
time): CMake custom target + script, or a Makefile rule — copy from
GUIDE 6.1. Add `-dirty` to the sha when `git status --porcelain` is
non-empty.

Host: board profile yaml with firmware dir/build/artifact, flash connect
and address, serial params, and `banner_regex` matching the line above.

Acceptance: `flashgate verify --evidence uart` exits 0.

## Level 2 — RAM signature (swd evidence, no serial cable)

Firmware: write a 64-byte struct at a FIXED address: magic 0xF1A5C0DE,
layout version 1, flags, git[16], build[24], CRC32 over the first 48
bytes (the final magic value is part of the CRC), reserved. Reference C
and linker-script section in GUIDE 6.2.

Address rules: RAM (survives reset), fixed section via linker script
(NOT a plain .bss variable), NOT cache-visible — use core-local RAM
(e.g. DTCM) or an MPU strongly-ordered region. AXI/AHB SRAM with a
D-cache enabled will look fine to the CPU and stale to the debugger.

Host: `evidence.signature.address` in the profile.

Acceptance: `flashgate verify --evidence swd` exits 0.

## Level 3 — probe commands (functional verification)

Firmware: line protocol over the console — one command in, one line out,
`OK ...` or `ERR ...`. Two rules that matter:
- SET commands reply with the value READ BACK from hardware, never an
  echo of the request (a silently-broken setter then fails the probe on
  step 1).
- QUERY commands report live register values (timer CCR, ADC, GPIO) —
  register readback is the hardest evidence available.

Complete polling/ISR receive code, dispatch loop, and the
firmware-string ↔ yaml-string mapping: GUIDE 6.3.

Host: `probes:` in the profile — steps of `send` / `expect` (regex over
one response line) / `assert` (over named capture groups, `and` only).
Assert deterministic quantities (state, ranges), never instantaneous
values.

Acceptance: `flashgate verify --all-probes` exits 0; sabotage a setter
with an early `return` and confirm the probe catches it (exit 7).

## Common pitfalls

- Serial port "access denied": a serial terminal holds the COM port.
- Clone ST-Link `DEV_USB_COMM_ERR`: flashgate auto-retries; re-plug USB
  if persistent.
- `cube-cmake not found`: a VSCode STM32 extension reconfigured the
  project; flashgate self-heals on the next build.
- Banner format changed on one side only → exit 3 with the regex shown.
