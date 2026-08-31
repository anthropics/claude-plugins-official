---
description: Check hardware prerequisites (ST-Link, console serial, toolchain)
---

Check whether flashgate can see everything it needs on this machine:

```bash
flashgate doctor ${FLASHGATE_BOARD:+--board "$FLASHGATE_BOARD"}
```

Explain any red line to the user: missing ST-Link (USB/power/driver),
unresolved console port (adapter unplugged, or vid/pid hint in the board
profile doesn't match — set `serial.port` or `$FLASHGATE_SERIAL_PORT`),
missing toolchain (STM32Cube bundles or PATH). The `on-board` line, when
present, is the firmware identity read live from RAM over the debug
probe.
