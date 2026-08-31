#!/usr/bin/env python3
"""Claude Code Stop hook — the firmware verification gate.

Blocks the agent from ending its turn while watched firmware files changed
since the last HARDWARE-verified state. Wiring (Claude Code compatible
contract, works with any harness that honors it — coderio included):

    {"hooks": {"Stop": [{"hooks": [{
        "type": "command",
        "command": "python .../hooks/flashgate_stop.py --board .../boards/apollo-h743.yaml",
        "timeout": 600}]}]}}

stdin  : the Stop payload JSON (we only read stop_hook_active from it)
exit 0 : allow the stop
exit 2 : block — stderr is fed back to the agent as the reason to continue

Escalation (coderio VerifyGate semantics): the same broken tree is blocked
at most MAX_CONSECUTIVE_BLOCKS times, then released with a loud warning —
the gate never wedges a session and never silently gives up.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Allow running straight from a repo checkout (no pip install needed)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flashgate import gatestate                      # noqa: E402
from flashgate.board import BoardError, default_board_path, load_board  # noqa: E402

VERIFY_TIMEOUT_S = 480


def emit(msg: str) -> None:
    print(msg, file=sys.stderr)


def resolve_board_arg(board_arg: str | None) -> str | None:
    """Board profile: explicit arg > FLASHGATE_BOARD env > repo default."""
    source = board_arg or __import__("os").environ.get("FLASHGATE_BOARD")
    if source:
        return source
    default = default_board_path()
    return str(default) if default else None


def run_verify(board_arg: str) -> tuple[int, str]:
    exe = shutil.which("flashgate")
    cmd = [exe] if exe else [sys.executable, "-m", "flashgate"]
    cmd += ["--board", board_arg, "verify", "--all-probes"]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=VERIFY_TIMEOUT_S,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except (subprocess.TimeoutExpired, OSError) as exc:
        return 1, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", default=None,
                        help="board profile yaml (default: $FLASHGATE_BOARD, then repo default)")
    args = parser.parse_args()

    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            payload = {}
    except (json.JSONDecodeError, OSError):
        payload = {}
    if payload.get("stop_hook_active"):
        return 0            # already continuing because of a Stop hook: never loop

    board_arg = resolve_board_arg(args.board)
    if board_arg is None:
        emit("[flashgate] no board profile: set --board or $FLASHGATE_BOARD. "
             "Gate idle for this session.")
        return 0
    try:
        board = load_board(Path(board_arg))
    except BoardError as exc:
        emit(f"[flashgate] gate misconfigured, allowing stop: {exc}")
        return 0            # a broken gate must not wedge the session

    fw_dir = board.firmware_dir
    watched = gatestate.watched_paths(fw_dir, list(board.watch_globs))
    if not watched:
        return 0            # no firmware-relevant changes: nothing to gate

    fingerprint = gatestate.tree_fingerprint(fw_dir)
    state = gatestate.load_state(fw_dir)
    if state.get("verified_fingerprint") == fingerprint:
        return 0            # this exact tree state already passed on hardware

    emit(f"[flashgate] watched firmware changed ({len(watched)} file(s), "
         f"e.g. {watched[0]}) — running hardware verify...")
    rc, output = run_verify(board_arg)

    if rc == 0:
        gatestate.save_state(fw_dir, verified_fingerprint=fingerprint,
                             fingerprint=fingerprint, consecutive_blocks=0)
        emit(f"[flashgate] hardware verify PASS — stop allowed")
        return 0

    blocks = (state.get("consecutive_blocks", 0) + 1) \
        if state.get("fingerprint") == fingerprint else 1
    tail = "\n".join((output or "").strip().splitlines()[-3:])

    if blocks > gatestate.MAX_CONSECUTIVE_BLOCKS:
        gatestate.save_state(fw_dir, fingerprint=fingerprint,
                             consecutive_blocks=blocks)
        emit(f"[flashgate] WARNING: releasing after {gatestate.MAX_CONSECUTIVE_BLOCKS} "
             f"blocked stops — firmware changes are NOT hardware-verified (last rc={rc}).")
        return 0

    gatestate.save_state(fw_dir, fingerprint=fingerprint,
                         consecutive_blocks=blocks)
    emit(f"[flashgate] BLOCKED (attempt {blocks}/{gatestate.MAX_CONSECUTIVE_BLOCKS}): "
         f"firmware changes are not verified on hardware (verify rc={rc}).")
    emit(f"[flashgate] Run `flashgate --board {board_arg} verify --all-probes`, "
         f"fix the firmware until it exits 0, then finish.")
    if tail:
        emit(f"[flashgate] last verify output:\n{tail}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
