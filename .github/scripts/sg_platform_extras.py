#!/usr/bin/env python3
"""Behaviour checks for one checkout of the security-guidance plugin that the
unit suite does not make on its own: path handling with platform spellings,
files written by other tools, and the Stop hook's memory on large new files.

    sg_platform_extras.py <plugin dir> [--memory]

Every check prints what it saw. A check whose code is not in this checkout
prints "not in this tree". Nothing here decides pass or fail."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time

PLUGIN = os.path.abspath(sys.argv[1])
HOOKS = os.path.join(PLUGIN, "hooks")
TESTS = os.path.join(PLUGIN, "tests")
WINDOWS = os.name == "nt"


def snippet(title, code, env=None, cwd=None):
    """Run `code` in a fresh interpreter with the hooks folder importable."""
    print("\n### %s\n" % title, flush=True)
    full_env = dict(os.environ, PYTHONPATH=os.pathsep.join([HOOKS, TESTS]),
                    PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    full_env.update(env or {})
    r = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], env=full_env,
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900)
    print(r.stdout.rstrip())
    if r.returncode or r.stderr.strip():
        print("exit=%d stderr:\n%s" % (r.returncode, r.stderr.rstrip()))
    sys.stdout.flush()


def inflight_markers():
    snippet("In-flight review markers without fcntl", """
        import importlib.util, os, subprocess, tempfile
        import diffstate
        if not hasattr(diffstate, "_mark_inflight"):
            raise SystemExit("not in this tree")
        d = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", d], check=True)
        r = diffstate._mark_inflight(d, ["a" * 40])
        print("fcntl", importlib.util.find_spec("fcntl") is not None)
        print("returned", r)
        print("held", len(diffstate._inflight_held))
        print("markers", [n for n in os.listdir(os.path.join(d, ".git")) if n.startswith("sg-inflight-")])
    """)


def secret_paths():
    snippet("Secret-shaped and secret-named paths", r"""
        import gitutil
        shaped = [".credentials.json", ".claude.json", r"C:\Users\x\.claude\.credentials.json",
                  ".CREDENTIALS.JSON", "config/credentials.json", r"src\claude.json"]
        for p in shaped:
            print("shaped", repr(p), gitutil._is_secret_shaped(p))
        if not hasattr(gitutil, "_is_secret_named"):
            raise SystemExit("_is_secret_named: not in this tree")
        named = ["secrets.yml", r"config\secrets.yml", "Credentials.JSON", "client_secret_123.apps.json",
                 "service-account.json", "secrets.example.yml", "secrets.enc.yaml", "secretsmanager.py",
                 "secret.txt"]
        for p in named:
            print("named", repr(p), gitutil._is_secret_named(p))
        print("count", gitutil.count_secret_named([("a\\secrets.yml", ""), ("b.py", "")]))
    """)


def patterns_files():
    home = tempfile.mkdtemp(prefix="sg-home-")
    valid = json.dumps({"patterns": [{"rule_name": "demo_rule", "regex": "AKIA[0-9A-Z]{16}",
                                      "reminder": "DEMO_RULE_REMINDER"}]})
    load = """
        import sys
        import extensibility
        extensibility.load_for_session(sys.argv[1] if len(sys.argv) > 1 else %r)
        print("loaded", [r["ruleName"] for r in extensibility.user_patterns()])
    """
    cases = [("local file is [1,2], written as UTF-8", "[1,2]", None)]
    if WINDOWS and shutil.which("powershell.exe"):
        cases.append(("local file is [1,2], written by Windows PowerShell Set-Content -Encoding Unicode",
                      "[1,2]", "Unicode"))
        cases.append(("local file is a valid rule file, written by Windows PowerShell Set-Content -Encoding Unicode",
                      valid.replace("demo_rule", "local_rule"), "Unicode"))
    for title, body, encoding in cases:
        proj = tempfile.mkdtemp(prefix="sg-proj-")
        subprocess.run(["git", "init", "-q", proj], check=True)
        os.makedirs(os.path.join(proj, ".claude"))
        with open(os.path.join(proj, ".claude", "security-patterns.json"), "w") as handle:
            handle.write(valid)
        local = os.path.join(proj, ".claude", "security-patterns.local.json")
        if encoding:
            subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                            "Set-Content -Encoding %s -Path $env:SG_LOCAL -Value $env:SG_BODY" % encoding],
                           env=dict(os.environ, SG_LOCAL=local, SG_BODY=body), check=True)
        else:
            with open(local, "w") as handle:
                handle.write(body)
        with open(local, "rb") as handle:
            print("\nfirst bytes of the local file:", handle.read(8))
        env = {"HOME": home, "USERPROFILE": home, "CLAUDE_CONFIG_DIR": ""}
        snippet("Pattern files: " + title, load % proj, env=env, cwd=proj)


def review_scope():
    root = os.path.realpath(tempfile.mkdtemp(prefix="sg-Scope-"))
    repo = os.path.join(root, "Root")
    out = os.path.join(root, "Out")
    os.makedirs(os.path.join(repo, "src"))
    os.makedirs(out)
    subprocess.run(["git", "init", "-q", repo], check=True)
    with open(os.path.join(repo, "src", "app.py"), "w") as handle:
        handle.write("x = 1\n")
    snippet("Review scope: path spellings", r"""
        import os, sys
        import diffstate
        if not hasattr(diffstate, "touched_scope"):
            raise SystemExit("not in this tree")
        from diffstate import touched_scope, review_scope_code
        ROOT, OUT = sys.argv[1] if len(sys.argv) > 1 else %r, %r
        app = os.path.join(ROOT, "src", "app.py")
        def show(label, *args):
            try:
                print(label, touched_scope(*args))
            except Exception as e:
                print(label, "EXCEPTION", type(e).__name__, e)
        show("a absolute", ROOT, ROOT, [app])
        show("b case changed", ROOT.swapcase(), ROOT.swapcase(), [os.path.join(ROOT.swapcase(), "SRC", "APP.PY")])
        show("b root as given, path case changed", ROOT, ROOT, [os.path.join(ROOT, "SRC", "APP.PY")])
        show("c relative", ROOT, ROOT, ["src/app.py"])
        show("d outside", ROOT, ROOT, [os.path.join(OUT, "x.py")])
        show("d mixed", ROOT, ROOT, [app, os.path.join(OUT, "x.py")])
        show("d none", ROOT, ROOT, [])
        if os.name == "nt":
            show("e forward slashes", ROOT.replace("\\", "/"), ROOT.replace("\\", "/"), [app.replace("\\", "/")])
            show("e backslashes", ROOT.replace("/", "\\"), ROOT.replace("/", "\\"), [app.replace("/", "\\")])
            show("e other drive", ROOT, ROOT, ["Q:\\x.py"])
            import ctypes
            buf = ctypes.create_unicode_buffer(1024)
            n = ctypes.windll.kernel32.GetShortPathNameW(ROOT, buf, 1024)
            short = buf.value if n else ""
            print("e short form:", short if short and short != ROOT else "none different from the long form")
            if short and short != ROOT:
                show("e short root", short, short, [app])
        s, inside = touched_scope(ROOT, ROOT, [app])
        print("g one file", review_scope_code(ROOT, s, inside, ["src/app.py"], 0))
        print("g with untouched", review_scope_code(ROOT, s, inside, ["src/app.py", "other.py"], 0))
        print("g case changed", review_scope_code(ROOT, s, inside, ["SRC/App.py"], 0))
        print("g base_fail 1", review_scope_code(ROOT, s, inside, ["src/app.py"], 1))
    """ % (repo, out))


def peak_memory_mb(proc):
    if WINDOWS:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        call = ctypes.windll.kernel32.K32GetProcessMemoryInfo
        call.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not call(int(proc._handle), ctypes.byref(counters), counters.cb):
            return -1
        return counters.PeakWorkingSetSize / 1e6
    import resource
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return peak / (1e6 if sys.platform == "darwin" else 1e3)


def stop_memory():
    """Peak memory of the Stop hook's own process on a turn that adds four
    50 MB data files next to one changed source file."""
    sys.path[:0] = [HOOKS, TESTS]
    import http.server
    import threading
    from pathlib import Path
    import conftest

    for kind in ("txt", "json"):
        print("\n### Stop hook memory: four 50 MB .%s files\n" % kind, flush=True)
        work = Path(tempfile.mkdtemp(prefix="sg-mem-"))
        repo = conftest.make_repo(work / "repo", {"app.py": "print('hi')\n"})
        state = work / "state"
        state.mkdir()
        server = http.server.HTTPServer(("127.0.0.1", 0), conftest._Stub)
        server.calls, server.status, server.delay, server.vulns = [], 200, 0, []
        threading.Thread(target=server.serve_forever, daemon=True).start()
        env = {k: v for k, v in os.environ.items()
               if k not in ("ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_REMOTE", "CLAUDE_PROJECT_DIR",
                            "CLAUDE_CODE_REMOTE_SESSION_ID", "HTTP_PROXY", "HTTPS_PROXY",
                            "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy")}
        env.update(conftest.GIT_ENV)
        env.update({
            "SECURITY_WARNINGS_STATE_DIR": str(state), "ANTHROPIC_API_KEY": "test-key",
            "ANTHROPIC_BASE_URL": "http://127.0.0.1:%d" % server.server_port,
            "NO_PROXY": "*", "no_proxy": "*", "SG_AGENTIC_COMMIT_REVIEW": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        })

        def hook(payload):
            started = time.perf_counter()
            proc = subprocess.Popen([sys.executable, str(conftest.HOOK_SCRIPT)], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            try:
                out, err = proc.communicate(json.dumps(payload).encode(), timeout=900)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, err = proc.communicate()
                print("TIMED OUT after 900 s")
            return proc, time.perf_counter() - started, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")

        proc, seconds, out, err = hook(conftest.ups_payload(repo))
        print("UserPromptSubmit: exit %d in %.1f s" % (proc.returncode, seconds))
        (repo / "app.py").write_text(conftest.VULN_PY)
        for index in range(4):
            mark = " \U0001F600" if index == 2 else ""
            if kind == "txt":
                line = "line %%09d of ordinary generated text for file %d%s\n" % (index, mark)
            else:
                line = '{"id": %%09d, "file": %d, "note": "ordinary generated record%s"}\n' % (index, mark)
            count = 50 * 1024 * 1024 // len((line % 0).encode("utf-8")) + 1
            with open(repo / ("data%d.%s" % (index, kind)), "w", encoding="utf-8", newline="\n") as handle:
                for start in range(0, count, 100000):
                    handle.write("".join(line % n for n in range(start, min(start + 100000, count))))
        proc, seconds, out, err = hook(conftest.stop_payload(repo))
        print("Stop: exit %d in %.1f s, peak memory of the hook process %.0f MB"
              % (proc.returncode, seconds, peak_memory_mb(proc)))
        print("review requests at the stub API:", len(server.calls))
        print("metrics:", json.dumps(conftest.metrics_of(out), sort_keys=True))
        if err.strip():
            print("stderr (last 15 lines):\n" + "\n".join(err.strip().splitlines()[-15:]))
        server.shutdown()
        shutil.rmtree(work, ignore_errors=True)


def main():
    for check in (inflight_markers, secret_paths, patterns_files, review_scope):
        try:
            check()
        except Exception as error:
            print("CHECK FAILED TO RUN: %s: %s: %s" % (check.__name__, type(error).__name__, error), flush=True)
    if "--memory" in sys.argv:
        try:
            stop_memory()
        except Exception as error:
            print("CHECK FAILED TO RUN: stop_memory: %s: %s" % (type(error).__name__, error), flush=True)


if __name__ == "__main__":
    main()
