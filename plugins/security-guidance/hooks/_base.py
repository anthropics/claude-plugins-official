"""
Shared low-level helpers for the security-guidance hook modules.

This module exists so that ``patterns``/``session_state``/``gitutil`` can use
``debug_log`` without importing ``security_reminder_hook`` (which would be a
circular import). It must stay free of any other intra-plugin imports.
"""
import glob
import json
import os
import re
import sys
import threading
from datetime import datetime

def state_dir():
    """Return the absolute path of the plugin's state directory.

    Resolution precedence (highest first):
      1. SECURITY_WARNINGS_STATE_DIR — plugin-specific override (existing)
      2. CLAUDE_CONFIG_DIR/security  — CC's config-dir env var (#1868)
      3. ~/.claude/security          — default fallback

    Empty-string env vars are treated as not-set so a misconfigured shell
    (`CLAUDE_CONFIG_DIR=` with no value) doesn't silently write to
    /security at the filesystem root.

    Returns a fully-expanded absolute path (no literal `~`) so subprocess
    callers can pass it through to code that doesn't re-expand tildes.

    Called per-invocation rather than cached at import time so test
    monkeypatches of the env vars take effect — the plugin's hooks each
    run as fresh subprocesses in production, so the per-call cost is
    negligible compared to subprocess spawn.
    """
    explicit = os.environ.get("SECURITY_WARNINGS_STATE_DIR")
    if explicit:
        d = explicit
    elif os.environ.get("CLAUDE_CONFIG_DIR"):
        d = os.path.join(os.environ["CLAUDE_CONFIG_DIR"], "security")
    else:
        d = "~/.claude/security"
    return os.path.abspath(os.path.expanduser(d))


def llm_reviews_switched_off():
    """True when the environment turns off every review that calls a model:
    the kill switch (SECURITY_GUIDANCE_DISABLE=1 / ENABLE_SECURITY_REMINDER=0),
    ENABLE_CODE_SECURITY_REVIEW=0, or ENABLE_STOP_REVIEW=0 together with
    ENABLE_COMMIT_REVIEW=0. Nothing loads the agent SDK then, so nothing
    should install it. Same reading of each variable as
    security_reminder_hook.py."""
    env = os.environ.get
    if env("SECURITY_GUIDANCE_DISABLE", "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    if env("ENABLE_SECURITY_REMINDER", "1") == "0":
        return True
    if env("ENABLE_CODE_SECURITY_REVIEW", "1") == "0":
        return True
    return env("ENABLE_STOP_REVIEW", "1") == "0" and env("ENABLE_COMMIT_REVIEW", "1") == "0"


def agent_sdk_site_dirs(state_dir):
    """Directories under the state dir that ensure_agent_sdk.py installs the
    agent SDK into and llm.py adds to sys.path: the venv's site-packages
    (POSIX `lib/pythonX.Y/site-packages`, Windows `Lib/site-packages`) and
    the flat `pip install --target` fallback."""
    venv_root = os.path.join(state_dir, "agent-sdk-venv")
    return (
        glob.glob(os.path.join(venv_root, "lib", "python*", "site-packages"))
        + glob.glob(os.path.join(venv_root, "Lib", "site-packages"))
        + [os.path.join(state_dir, "agent-sdk-libs")]
    )


def agent_sdk_installed(state_dir):
    """True iff one of those directories holds a finished install of the SDK:
    its package and the metadata pip writes once the package is unpacked. A
    file check only, no import."""
    return any(
        os.path.isfile(os.path.join(d, "claude_agent_sdk", "__init__.py"))
        and glob.glob(os.path.join(d, "claude_agent_sdk-*.dist-info"))
        for d in agent_sdk_site_dirs(state_dir)
    )


# Debug log file. Lives under the plugin state dir (default ~/.claude/security/)
# rather than /tmp because /tmp is world-writable on multi-user hosts (TOCTOU /
# symlink-attack surface, cross-user log leakage). Overridable per-process via
# SECURITY_GUIDANCE_DEBUG_LOG, or per-state-dir via SECURITY_WARNINGS_STATE_DIR
# (plugin-specific override) or CLAUDE_CONFIG_DIR (CC-wide config dir, #1868).
DEBUG_LOG_FILE = os.environ.get("SECURITY_GUIDANCE_DEBUG_LOG") or os.path.join(
    state_dir(), "log.txt"
)
# Cap the debug log so parallel-worker fleets don't fill disk. When the active
# file exceeds this it's atomically rotated to <file>.1 (overwriting any prior
# rotation), so total disk stays ~2× this.
DEBUG_LOG_MAX_BYTES = 1 * 1024 * 1024


def debug_log(message):
    """Append debug message to log file with timestamp."""
    try:
        # Ensure parent dir exists — first hook invocation on a fresh install
        # creates ~/.claude/security/ if it isn't already there. 0700 so other
        # local users can't read review/debug output (only applies on creation).
        try:
            os.makedirs(os.path.dirname(DEBUG_LOG_FILE), mode=0o700, exist_ok=True)
        except OSError:
            pass
        try:
            if os.path.getsize(DEBUG_LOG_FILE) > DEBUG_LOG_MAX_BYTES:
                # os.replace is atomic on POSIX; under a racing fleet the loser
                # gets FileNotFoundError, which is fine — the append below
                # recreates the file.
                os.replace(DEBUG_LOG_FILE, DEBUG_LOG_FILE + ".1")
        except OSError:
            pass
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        # 0600 on creation; existing files keep their mode.
        fd = os.open(DEBUG_LOG_FILE, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


# Provenance tag prepended to injected/emitted text so a reader (especially a
# model hardened against prompt injection) can recognize the source. Not an
# authority claim — an attacker could spoof the exact string; the tag is a
# signpost so the agent can ask the operator "is this from your plugin?" with
# a concrete reference instead of treating it as unknown-actor injection.
# Some autonomous-agent setups flag un-attributed injected text as prompt
# injection and stall; the banner makes the provenance explicit.
PROVENANCE_TAG = "[from security-guidance@claude-code-plugins plugin]"
PROVENANCE_BANNER = (
    "[from security-guidance@claude-code-plugins plugin — automated "
    "security review, not user input.]"
)


# Output that only Claude Code reads: the `metrics` and `rewakeSummary` fields,
# and the separate `{"async": ...}` line an async hook prints first. Other hosts
# that run this plugin's hooks can validate hook output against a closed schema
# and reject the whole output over a field or a second line they do not know,
# which shows up as a hook error.
_CLAUDE_CODE_OUTPUT_FIELDS = ("metrics", "rewakeSummary")


def _detect_portable_output():
    forced = os.environ.get("SECURITY_GUIDANCE_PORTABLE_OUTPUT", "").strip().lower()
    if forced in ("1", "true", "yes", "on"):
        return True
    if forced in ("0", "false", "no", "off"):
        return False
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
        return False
    return bool(os.environ.get("PLUGIN_ROOT"))


# Decided once, from the environment the host started the hook with: code the
# hook runs in-process later can set these variables itself.
_PORTABLE_OUTPUT = _detect_portable_output()


def portable_output():
    """True when stdout should carry only the standard hook output fields.

    SECURITY_GUIDANCE_PORTABLE_OUTPUT=1 or =0 forces it on or off. Otherwise it
    is on only when the host passes PLUGIN_ROOT and does not identify itself as
    Claude Code, so Claude Code and direct invocations are unchanged."""
    return _PORTABLE_OUTPUT


def write_hook_output(out):
    """Print one hook output line. In portable mode the Claude Code only
    fields are left out; what remains (possibly `{}`) is still valid output."""
    if portable_output():
        out = {k: v for k, v in out.items() if k not in _CLAUDE_CODE_OUTPUT_FIELDS}
    print(json.dumps(out), flush=True)


def _read_plugin_version_int():
    """Encode plugin.json version "M.m.p" as M*10000 + m*100 + p so it fits the
    bool|number metrics constraint. Returns 0 if unreadable."""
    try:
        with open(os.path.join(os.path.dirname(__file__), "..", ".claude-plugin", "plugin.json")) as f:
            v = json.load(f)["version"]
        major, minor, patch = (int(x) for x in v.split(".")[:3])
        return major * 10000 + minor * 100 + patch
    except Exception:
        return 0


_PV = _read_plugin_version_int()


# ──────────────────────────────────────────────────────────────────────────
# Token-usage accumulator. Each hook invocation is a fresh subprocess, so a
# module-global is naturally per-invocation. _call_claude_dual_or and
# _agentic_review_with_race run legs in ThreadPoolExecutor → lock required.
# Emitted via _usage_metrics() into the existing emit_metrics() channel so
# hook metrics rows carry per-invocation token/cost totals
# alongside the existing skip_reason / vulns_found fields.
_USAGE = {
    "in": 0, "out": 0, "cr": 0, "cw": 0, "cost": 0.0, "n": 0,
    # HTTP error visibility (#2098 visibility gap — see emit comment in
    # _usage_metrics). Without this, API failures from `_call_claude` left
    # zero fingerprint in telemetry: the call returns None, the caller's
    # emit_metrics carries no api_calls field, and the failure is
    # indistinguishable from "no review needed". The deprecation outage
    # that broke every commit-review LLM call was invisible until users
    # reported it manually.
    "http_err_last": 0,    # most recent HTTP error code this invocation
    "http_err_count": 0,   # total HTTP errors (4xx + 5xx + network)
    "net_err": 0,          # why the last call got no HTTP response, 0 if it got one
    # For the usage log line only: model ids as recorded (the requested alias
    # on the Agent SDK path), and whether any call had no price-table entry.
    "models": [],
    "default_priced": False,
}
_USAGE_LOCK = threading.Lock()

# $/Mtok (input, output). Used only for the raw-HTTP path; the SDK path
# reports total_cost_usd directly. Cache reads/writes are priced at the
# canonical 0.1×/1.25× of input. Unknown models fall back to sonnet pricing
# so cost_usd is never silently zero. Re-pricing downstream from the raw tok_*
# fields is the source of truth — cost_usd here is a convenience rollup.
_PRICE_PER_MTOK = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-5-5": (4.0, 20.0),
}
_PRICE_DEFAULT = (3.0, 15.0)


def _record_usage(usage, model, cost_usd=None):
    """Accumulate one API response's token usage. `usage` is the Anthropic
    `usage` dict (HTTP) or the SDK ResultMessage.usage dict — both use the
    same key names. `cost_usd` (SDK-provided) is preferred when present;
    otherwise computed from _PRICE_PER_MTOK keyed on the response model id
    (longest-prefix match so `claude-sonnet-4-6-20251015` → sonnet row)."""
    if not usage and cost_usd is None:
        return
    u = usage or {}
    try:
        i = int(u.get("input_tokens") or 0)
        o = int(u.get("output_tokens") or 0)
        cr = int(u.get("cache_read_input_tokens") or 0)
        cw = int(u.get("cache_creation_input_tokens") or 0)
    except (TypeError, ValueError):
        return
    default_priced = False
    if cost_usd is None:
        pin, pout = _PRICE_DEFAULT
        default_priced = True
        m = (model or "").lower()
        for k, v in sorted(_PRICE_PER_MTOK.items(), key=lambda kv: -len(kv[0])):
            if m.startswith(k):
                pin, pout = v
                default_priced = False
                break
        cost_usd = (i * pin + o * pout + cr * pin * 0.1 + cw * pin * 1.25) / 1_000_000
    with _USAGE_LOCK:
        _USAGE["in"] += i
        _USAGE["out"] += o
        _USAGE["cr"] += cr
        _USAGE["cw"] += cw
        _USAGE["cost"] += float(cost_usd or 0.0)
        _USAGE["n"] += 1
        _USAGE["default_priced"] = _USAGE["default_priced"] or default_priced
        name = re.sub(r"[^A-Za-z0-9_.:/@-]", "_", str(model or ""))[:80]
        if name and name not in _USAGE["models"]:
            _USAGE["models"].append(name)


def _record_http_error(status):
    """Record an HTTP error from an LLM API call. `status` is the HTTP
    status code (integer 400–599) or -1 for network/timeout errors. Stored
    in `_USAGE["http_err_last"]` (most recent) and counted in
    `_USAGE["http_err_count"]`. Snapshot via `_usage_metrics()` so every
    subsequent `emit_metrics` includes the failure fingerprint.

    Background: without this, the most recent example was the #2098
    deprecation 400. Every hook fire's LLM call returned HTTP 400; the
    plugin caught it and returned None; the emit_metrics carried no
    api_calls field; aggregate dashboards looked normal. The failure
    only became visible when a user manually reported errors out of
    their debug log. With this field, a category-of-failure spike (4xx,
    5xx, or -1 network) is queryable from BQ in real time.
    """
    try:
        s = int(status)
    except (TypeError, ValueError):
        return
    with _USAGE_LOCK:
        _USAGE["http_err_last"] = s
        _USAGE["http_err_count"] += 1


def _record_net_error(code):
    """Record why an LLM API call got no HTTP response: the packed code from
    llm._net_error_code. `api_error` -1 cannot tell a certificate failure
    from a refused connection or a timeout, and a failure the HTTP client
    raises outside its own error type (a default TLS context that cannot be
    built, a connection closed before the reply) has no `api_error` at all.
    Emitted as `net_err` on the row of a hook whose last call failed this
    way; a later call clears it."""
    try:
        c = int(code)
    except (TypeError, ValueError):
        return
    if c > 0:
        with _USAGE_LOCK:
            _USAGE["net_err"] = c


def _clear_net_error():
    with _USAGE_LOCK:
        _USAGE["net_err"] = 0


def _net_error_metric():
    with _USAGE_LOCK:
        return _USAGE.get("net_err", 0)


# Set by main() and the review handlers: which review this invocation runs
# and for which Claude Code session, so the usage log line can be attributed.
_USAGE_CONTEXT = {"session_id": "", "review": "stop"}


def _log_usage(usage):
    """Write this invocation's review usage to the debug log.

    `usage` is a `_usage_metrics()` snapshot, the same numbers that go out
    with the hook's metrics. The raw-HTTP review leaves no Claude Code
    transcript and no OpenTelemetry event; without this line nothing on the
    machine records what it used. `est_cost_usd` is that same rollup: list
    prices (the inner CLI's own figure on the Agent SDK path), `~` appended
    when a model had no price-table entry and the default rate was used.
    """
    if not usage.get("api_calls"):
        return
    with _USAGE_LOCK:
        models = ",".join(_USAGE["models"]) or "-"
        approx = "~" if _USAGE["default_priced"] else ""
    debug_log(
        f"Review usage: review={_USAGE_CONTEXT.get('review') or '-'} "
        f"session={_USAGE_CONTEXT.get('session_id') or '-'} "
        f"model={models} calls={usage['api_calls']} "
        f"in={usage['tok_in']} out={usage['tok_out']} "
        f"cache_read={usage['tok_cache_r']} cache_write={usage['tok_cache_w']} "
        f"est_cost_usd={usage['cost_usd']:.4f}{approx}"
    )


def launcher_probe_metrics():
    """How long sg-python.sh waited for interpreters to answer its probe.

    Only when this launch's probes took a second or more together, so ordinary
    rows carry no extra keys: `launcher_probe_ms` is all of them,
    `launcher_probe_max_ms` the slowest one. Both are capped at an hour (the
    launcher reads the wall clock, which can jump). Read once: the variables
    are removed so child processes do not report this launch as their own.
    """
    try:
        slowest = int(os.environ.pop("SG_LAUNCHER_PROBE_MAX_MS", ""))
        total = int(os.environ.pop("SG_LAUNCHER_PROBE_MS", ""))
    except ValueError:
        return {}
    if total < 1000 or slowest > total:
        return {}
    cap = 3_600_000
    return {"launcher_probe_ms": min(total, cap), "launcher_probe_max_ms": min(slowest, cap)}


# Reparse tags that redirect every open below them: symbolic links and
# junctions. App execution aliases (the entries under WindowsApps) carry
# another tag and are not counted.
_SYMLINK_TAG, _MOUNT_POINT_TAG = 0xA000000C, 0xA0000003


def _is_link(path, st, readlink):
    """True iff `path` (with lstat result `st`) is a symbolic link or a
    junction, None when that cannot be told (Python older than 3.8 has no
    reparse tag). A volume mounted at a folder has the junction tag too; its
    target is the bare volume name."""
    if not getattr(st, "st_file_attributes", 0) & 0x400:   # FILE_ATTRIBUTE_REPARSE_POINT
        return False
    tag = getattr(st, "st_reparse_tag", None)
    if tag is None:
        return None
    if tag == _MOUNT_POINT_TAG:
        try:
            target = readlink(path).lstrip("\\?").rstrip("\\").lower()
        except (OSError, ValueError, NotImplementedError):
            return True
        return not (target.startswith("volume{") and target.endswith("}"))
    return tag == _SYMLINK_TAG


def interp_reparse_metric(executable=None, base_prefix=None, environ=None, platform=None,
                          lstat=None, readlink=None):
    """`interp_reparse`, on Windows: whether the interpreter running this
    hook is reached through a symbolic link or junction. Bits:

      1  the path of the executable goes through one
      2  the path of the standard library (sys.base_prefix) goes through one
      4  such a path, as spelled, is under the user's AppData folders (a
         uv-managed Python, for one)
      8  one of the two paths could not be checked

    0 is sent too, so a Windows row without the key is a row that lost it,
    not a "no". Measurement only, on the SessionStart row. It sizes how many
    sessions start Python through such a link: inside the packaged Claude
    Desktop app, Windows leaks kernel memory on every file opened that way,
    and each hook starts an interpreter. See anthropics/claude-code#96870.

    No process is started: one lstat per folder on the two paths, up to the
    first link. Where the link points is not followed, and an 8.3 short name
    on one side reads as "not under AppData" (bit 4 missing, 1 and 2 right).
    The plugin's own folders are not looked at.

    The arguments stand in for the interpreter and the system in tests.
    """
    if (platform or sys.platform) != "win32":
        return {}
    executable = sys.executable if executable is None else executable
    base_prefix = getattr(sys, "base_prefix", "") if base_prefix is None else base_prefix
    environ = os.environ if environ is None else environ
    lstat = lstat or os.lstat
    readlink = readlink or os.readlink

    def spelled(p):
        # For comparing only: lower case, no \\?\ prefix.
        p = os.path.normcase(p)
        return p[4:] if p.startswith("\\\\?\\") and not p.startswith("\\\\?\\unc\\") else p

    value = 0
    roots = []
    for name in ("APPDATA", "LOCALAPPDATA"):
        try:
            root = environ.get(name)
            if root:
                roots.append(spelled(os.path.abspath(root)).rstrip("\\/"))
        except Exception:
            pass
    checked = {}
    for bit, start in ((1, executable), (2, base_prefix)):
        try:
            if not start:
                continue
            p = start = os.path.abspath(start)
            linked = False
            while not linked:
                parent = os.path.dirname(p)
                if parent == p:
                    break
                if p not in checked:
                    try:
                        checked[p] = _is_link(p, lstat(p), readlink)
                    except FileNotFoundError:
                        checked[p] = False
                if checked[p] is None:
                    value |= 8
                linked = bool(checked[p])
                p = parent
            if linked:
                value |= bit
                here = spelled(start)
                if any(here == r or here.startswith(r + os.sep) for r in roots):
                    value |= 4
        except Exception:
            value |= 8
    return {"interp_reparse": value}


def _usage_metrics():
    """Snapshot the accumulator as metric keys. Returns {} when no API calls
    AND no HTTP errors were made so skip-path emits don't burn key budget.
    cost_usd rounded to 1e-6 to keep the float finite/short for the zod
    schema.

    HTTP errors (`http_err_last`, `http_err_count`) emitted ONLY when
    `http_err_count > 0` so successful calls don't pad every metrics row
    with two zero fields.
    """
    with _USAGE_LOCK:
        if _USAGE["n"] == 0 and _USAGE["http_err_count"] == 0:
            return {}
        out = {}
        if _USAGE["n"] > 0:
            out.update({
                "tok_in": _USAGE["in"],
                "tok_out": _USAGE["out"],
                "tok_cache_r": _USAGE["cr"],
                "tok_cache_w": _USAGE["cw"],
                "cost_usd": round(_USAGE["cost"], 6),
                "api_calls": _USAGE["n"],
            })
        if _USAGE["http_err_count"] > 0:
            out["http_err_last"] = _USAGE["http_err_last"]
            out["http_err_count"] = _USAGE["http_err_count"]
        return out

