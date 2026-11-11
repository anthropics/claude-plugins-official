#!/usr/bin/env python3
"""Real agent-SDK installs with the plugin's bootstrap script, on two
checkouts of the plugin, printing the outcome code of each run.

    sg_platform_sdk_bootstrap.py <main plugin dir> <pull request plugin dir>

Prints what each step returned next to what is expected; decides nothing."""
import json
import os
import subprocess
import sys
import tempfile
import time

MAIN, PR = (os.path.abspath(p) for p in sys.argv[1:3])
WORK = tempfile.mkdtemp(prefix="sg-sdk-")


def bootstrap_env(state, extra=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("SECURITY_GUIDANCE_DISABLE", "ENABLE_CODE_SECURITY_REVIEW")}
    env.update({"SECURITY_WARNINGS_STATE_DIR": state, "PYTHONDONTWRITEBYTECODE": "1"})
    env.update(extra or {})
    return env


def run(label, plugin, state, expect, extra=None):
    started = time.perf_counter()
    r = subprocess.run([sys.executable, os.path.join(plugin, "hooks", "ensure_agent_sdk.py")],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       env=bootstrap_env(state, extra), timeout=1500)
    metrics = {}
    for line in r.stdout.splitlines():
        try:
            metrics = json.loads(line).get("metrics") or metrics
        except (json.JSONDecodeError, AttributeError):
            pass
    shown = {k: v for k, v in metrics.items() if k.startswith("sdk_")}
    print("%s: sdk_bootstrap=%s (expected %s), exit %d, %.0f s, %s"
          % (label, metrics.get("sdk_bootstrap"), expect, r.returncode,
             time.perf_counter() - started, json.dumps(shown, sort_keys=True)), flush=True)
    if r.stderr.strip():
        print("  stderr (last 8 lines):\n  " + "\n  ".join(r.stderr.strip().splitlines()[-8:]))
    return metrics.get("sdk_bootstrap")


def sdk_package_dirs(state):
    return [os.path.join(root, "claude_agent_sdk") for root, dirs, _ in os.walk(state)
            if "claude_agent_sdk" in dirs]


def reviewer_import(label, plugin, state):
    """Import the SDK the way the plugin's reviewer does (its own path setup,
    which also handles pywin32's .pth files on Windows)."""
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import llm, _base; "
            "llm._inject_agent_sdk_venv_into_syspath(_base.state_dir()); "
            "from claude_agent_sdk import query; print('import ok')")
    r = subprocess.run([sys.executable, "-c", code, os.path.join(plugin, "hooks")],
                       capture_output=True, text=True, env=bootstrap_env(state))
    print("%s: %s" % (label, (r.stdout + r.stderr).strip().splitlines()[-1:]))


print("## a. whole plugin switched off")
off = os.path.join(WORK, "off")
run("pull request, SECURITY_GUIDANCE_DISABLE=1", PR, off, 10, {"SECURITY_GUIDANCE_DISABLE": "1"})
print("state folder created:", os.path.exists(off), "(expected False)")

print("\n## b. first install, then a second run")
state = os.path.join(WORK, "state")
run("pull request, first run", PR, state, 2)
run("pull request, second run", PR, state, 1)

print("\n## c. installed package emptied of its files")
packages = sdk_package_dirs(state)
print("SDK package folders:", packages)
removed = 0
for package in packages:
    for root, _, files in os.walk(package):
        for name in files:
            os.remove(os.path.join(root, name))
            removed += 1
print("files removed:", removed)
run("main on the emptied install", MAIN, state, "1 (the bug)")
run("pull request on the emptied install", PR, state, "2 with sdk_venv_emptied 1")
run("pull request again", PR, state, 1)
reviewer_import("reviewer import after the rebuild", PR, state)

print("\n## d. review switched off: is the bootstrap still started from a tool hook")
payload = json.dumps({"session_id": "s", "hook_event_name": "PostToolUse", "tool_name": "Write",
                      "tool_input": {"file_path": "x.txt", "content": "hi"}, "cwd": "."})
for label, plugin, expect in (("main", MAIN, True), ("pull request", PR, False)):
    folder = os.path.join(WORK, "w-" + label.replace(" ", "-"))
    r = subprocess.run([sys.executable, os.path.join(plugin, "hooks", "security_reminder_hook.py")],
                       input=payload, capture_output=True, text=True, cwd=WORK,
                       env=bootstrap_env(folder, {"ENABLE_CODE_SECURITY_REVIEW": "0"}), timeout=300)
    time.sleep(3)
    marker = os.path.join(folder, ".sdk_bootstrap_spawned")
    print("%s: hook exit %d, marker file exists: %s (expected %s)"
          % (label, r.returncode, os.path.exists(marker), expect))

print("\n## e. install killed part way, then run again")
killed = os.path.join(WORK, "k")
proc = subprocess.Popen([sys.executable, os.path.join(PR, "hooks", "ensure_agent_sdk.py")],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env=bootstrap_env(killed))
time.sleep(5)
proc.kill()
proc.wait()
print("after the kill the state folder holds:", sorted(os.listdir(killed)) if os.path.isdir(killed) else "nothing")
time.sleep(10)
outcome = run("pull request, 10 s after the kill", PR, killed, "2, or 5 while a cooldown holds")
if outcome == 5:
    print("waiting 6 minutes for the cooldown")
    time.sleep(365)
    # The kill ends the bootstrap script only. Killed while it creates the venv,
    # the next run rebuilds (2). Killed while pip runs, pip finishes the install
    # by itself and the next run finds it complete (1).
    outcome = run("pull request, 6 minutes later", PR, killed, "2, or 1 when pip was already running")
run("pull request, once more", PR, killed, 1)
reviewer_import("reviewer import after the killed install", PR, killed)
