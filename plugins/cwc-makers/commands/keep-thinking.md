---
description: Onboard a Code-with-Claude Makers Cardputer — clone the build-with-claude repo, flash firmware, and install the Claude Buddy apps.
disable-model-invocation: true
---

The user has a Cardputer-Adv from claude.com/cwc-makers plugged in over USB-C.

1. Clone or update https://github.com/moremas/build-with-claude in the current directory.
2. Invoke the `m5-onboard` skill and follow it to run `onboard/scripts/onboard.py --apps buddy` from the clone, surfacing the download-mode button prompt to the user.
3. When done, tell the user how to launch Claude Buddy and ask what they want to build next (see the `cardputer-buddy` skill for iterating).
