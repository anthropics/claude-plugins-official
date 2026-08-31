---
description: Run the full hardware verification loop (build → flash → evidence → probes)
---

Run the full flashgate verification loop for this project and report the
exit code and what failed, if anything:

```bash
flashgate verify --all-probes ${FLASHGATE_BOARD:+--board "$FLASHGATE_BOARD"} ; echo "exit=$?"
```

Interpret for the user:
- exit 0: the board itself confirms the current tree boots and the
  probed features work
- exit 1/2: build or flash failure — show the tail of the output
- exit 3: board stayed silent (dead loop before the banner / no
  signature published)
- exit 4: error string on serial
- exit 5: the board runs a different tree than the working copy (rebuild)
- exit 6: environment (ST-Link / serial / toolchain) — suggest
  `flashgate doctor`
- exit 7: a probe failed — show the step transcript and the assertion
