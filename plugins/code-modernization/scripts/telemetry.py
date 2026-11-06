#!/usr/bin/env python3
"""Usage counts for the code-modernization plugin. Whole numbers only, never text.

    telemetry.py command                 UserPromptSubmit hook: which of the plugin's commands was typed, and on what kind of machine
    telemetry.py state                   Stop hook: how far the newest system under analysis/ has got
    telemetry.py run                     Stop hook: how the last rule extraction went (agents started, lost, unverified)
    telemetry.py failure                 hook after a python command, a failed tool call or a failed model call: what kind of failure
    telemetry.py show [DIR] [--prompt TEXT] [--json]
                                         print what the hooks would send for the workspace DIR (default: this folder)

The two hooks read the hook's JSON from stdin and print at most one line, {"metrics": {...}}, which Claude Code
records as usage counts when its own telemetry is on. Every key is fixed below and every value is a whole number,
capped, and rounded to two significant figures from 100 up, so a count is not a fingerprint of one system. Nothing is
read except the plugin's own artifacts under analysis/ and modernized/, and no file name, path, system name, code or
prompt text leaves this script. Nothing is sent when the plugin has not been used in the folder. It never raises,
gives up after three seconds and always exits 0.

Off switches: CODE_MODERNIZATION_TELEMETRY=0, the plugin's "Usage counts" option, or Claude Code's own
DISABLE_TELEMETRY / CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC. Anything but an explicit "on" in the first two
switches its off. To find out why nothing was sent, set CODE_MODERNIZATION_TELEMETRY_DEBUG=1: each hook run then
appends one line saying what it decided to telemetry-debug.log in the plugin's data folder.
"""
import collections
import hashlib
import itertools
import json
import os
import platform
import re
import signal
import stat
import sys
import tempfile
import threading
import time

sys.dont_write_bytecode = True  # a hook must not leave files in the plugin's own folder
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_report as br  # noqa: E402  (reads the artifacts safely and counts them the way the report does)

MAX_KEYS, CAP = 20, 10 ** 9
TRUE = {"1", "true", "on", "yes"}
# The most a key can carry: a hostile artifact cannot make a count bigger than this. Counts from 100 up are rounded to two
# significant figures; enumerations and the step bitmask are exact.
LIMITS = {"pv": 999999, "cmd": 99, "perm": 6, "has_source": 1, "fresh": 1, "systems": 99, "goal": 4, "lang": 99, "done": 65535, "phases": 99,
          "os": 9, "py": 9, "pyv": 999, "pathf": 7, "tool": 99, "kind": 99, "api": 99, "err": 99, "err_at": 99999}
COUNT_LIMIT = 10 ** 7
EXACT = {"pv", "cmd", "perm", "has_source", "fresh", "goal", "lang", "done", "os", "py", "pyv", "pathf", "tool", "kind", "api", "err", "err_at"}
NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")
LINE_WIDTH = 600  # longer lines are cut before anything is parsed, so no artifact can make a pattern slow

# One number per command: 1 is the front door, 20-22 are the pane's own commands (panel, review-pane, sign), typed without the plugin's name.
COMMANDS = {"": 1, "preflight": 2, "assess": 3, "map": 4, "extract-rules": 5, "review": 6, "brief": 7, "transform": 8,
            "uplift": 9, "reimagine": 10, "verify": 11, "harden": 12, "status": 13}
PANE = {"panel": 20, "review-pane": 21, "sign": 22}
OTHER_COMMAND = 99
PERMISSION_MODES = {"default": 1, "acceptEdits": 2, "plan": 3, "auto": 4, "bypassPermissions": 5, "dontAsk": 6}
TOOLS = {"Bash": 1, "Read": 2, "Edit": 3, "Write": 3, "MultiEdit": 3, "NotebookEdit": 3, "Glob": 4, "Grep": 4, "Agent": 5, "Task": 5, "Workflow": 6,
         "AskUserQuestion": 7, "Skill": 8, "WebFetch": 9, "WebSearch": 9}
# What went wrong, decided here from the text of a failure and never sent: first match wins. 1-5 are about the interpreter and the plugin's own scripts.
FAILURE_KINDS = [
    (2, re.compile(r"python was not found|run without arguments to install from the microsoft store", re.I)),
    (3, re.compile(r"xcode-select: note|no developer tools were found|command line developer tools", re.I)),
    (1, re.compile(r"\b(?:python3?|py)(?:\.exe)?: (?:command )?not found|command not found: (?:python3?|py)\b|'(?:python3?|py)' is not recognized|python3?: no such file|env: .?python3?.?: no such file", re.I)),
    (4, re.compile(r"syntaxerror|requires python 3|invalid syntax", re.I)),
    (6, re.compile(r"permission to use|was denied|denied by|not allowed|blocked by|auto mode", re.I)),
    (7, re.compile(r"eacces|permission denied|access is denied", re.I)),
    (8, re.compile(r"timed out|timeout|etimedout", re.I)),
    (11, re.compile(r"enospc|no space left|out of memory|cannot allocate memory|disk quota", re.I)),
    (10, re.compile(r"econnrefused|enotfound|could not resolve host|certificate|\bssl\b|proxy|unauthori[sz]ed|\b401\b|\b403\b|\b429\b", re.I)),
    (9, re.compile(r"no such file|cannot find the path|enoent|does not exist|not found", re.I)),
    (12, re.compile(r"scriptpath|unknown tool|workflow|subagent", re.I)),
]
API_ERRORS = [
    (1, re.compile(r"rate.?limit|\b429\b", re.I)),
    (2, re.compile(r"authenticat|unauthori[sz]ed|invalid.?api.?key|\b40[13]\b|oauth", re.I)),
    (3, re.compile(r"billing|credit|payment|quota", re.I)),
    (6, re.compile(r"max.?output|max_tokens|too long", re.I)),
    (7, re.compile(r"timeout|timed out|network|econn|connection", re.I)),
    (5, re.compile(r"server.?error|overloaded|\b5\d\d\b|internal", re.I)),
    (4, re.compile(r"invalid.?request|\b400\b|unrecognized_model|not_found", re.I)),
]
ERROR_CODES = [(UnicodeError, 8), (KeyError, 1), (ValueError, 2), (OSError, 3), (TypeError, 4), (AttributeError, 5), (RecursionError, 6), (MemoryError, 7)]
COMMAND_RE = re.compile(r"^/(?P<ns>code-modernization:)?modernize(?:-(?P<verb>[a-z][a-z-]*))?(?=\s|$)")

GOALS = {"understand": 1, "uplift": 2, "transform": 3, "reimagine": 4}
GOAL_LABEL = re.compile(r"(?i)^goal\b\s*[:\u2013\u2014]?\s*(.*)$")
GOAL_WORDS = re.compile(r"(?i)(understand|uplift|transform|reimagine|rewrite|rebuild)\b")
GOAL_ALIASES = {"rewrite": "transform", "rebuild": "reimagine"}
# the pop-up's own wording, when that is what was written down
GOAL_PHRASES = [(re.compile(r"(?i)newer version|same technology"), 2), (re.compile(r"(?i)different technology|one piece at a time"), 3),
                (re.compile(r"(?i)from scratch|new architecture"), 4), (re.compile(r"(?i)understand it|map it"), 1)]

# What the code is written in: the dominant language of the map, as one of these numbers (0 unknown, 99 other).
LANGS = {"cobol": 1, "jcl": 1, "java": 2, "jsp": 2, "c#": 3, "csharp": 3, "vb": 3, "vb.net": 3, "f#": 3, "python": 4, "php": 5,
         "perl": 6, "c": 7, "c++": 8, "cpp": 8, "javascript": 9, "typescript": 9, "js": 9, "ts": 9, "node": 9, "angularjs": 9,
         "ruby": 10, "go": 11, "golang": 11, "rust": 12, "kotlin": 13, "scala": 13, "groovy": 13, "sql": 14, "plsql": 14,
         "pl/sql": 14, "tsql": 14, "fortran": 15, "rpg": 16, "rpgle": 16, "pascal": 17, "delphi": 17, "shell": 18, "bash": 18,
         "assembler": 19, "assembly": 19, "hlasm": 19, "asp": 3, "vb6": 3, "nodejs": 9, "c/c++": 7}
# labels in a map that are not a language somebody modernizes
NOT_CODE = {"artifact", "make", "makefile", "cmake", "yaml", "yml", "json", "xml", "toml", "ini", "markdown", "md", "text", "txt", "html", "css",
            "pkgconfig", "config", "properties", "docker", "dockerfile", "csv", "svg", "data", "binary", "license", "gradle", "maven", "unknown", "other"}

# `done` adds up one of these for every step that has left its file: 15 = preflight, assess, map and rules.
STEPS = [("preflight", 1), ("assess", 2), ("map", 4), ("rules", 8), ("reviewed", 16), ("brief", 32), ("approved", 64),
         ("built", 128), ("verified", 256), ("signed", 512), ("hardened", 1024), ("report", 2048), ("deltas", 4096),
         ("baseline", 8192), ("playbook", 16384), ("spec", 32768)]
# Files that only this plugin writes: a folder with none of them is not something the plugin has worked on.
GATE = ("INTENT.md", "PREFLIGHT.md", "MODERNIZATION_BRIEF.md", "BUSINESS_RULES.md", "DELTA_CATALOG.md", "VERIFICATION.json", "RULE_REVIEWS.json", "AI_NATIVE_SPEC.md")
FILES = {"preflight": "PREFLIGHT.md", "assess": "ASSESSMENT.md", "map": "topology.json", "brief": "MODERNIZATION_BRIEF.md",
         "verified": "VERIFICATION.json", "hardened": "SECURITY_FINDINGS.md", "report": "REPORT.html",
         "deltas": "DELTA_CATALOG.md", "baseline": "BASELINE.md", "playbook": "PLAYBOOK.md", "spec": "AI_NATIVE_SPEC.md"}

# Every key that can be sent, and what it counts. Order is send order; the version comes first so it always survives.
MEANING = collections.OrderedDict([
    ("pv", "plugin version as major*10000 + minor*100 + patch"),
    ("cmd", "command typed: 1 front door, 2 preflight, 3 assess, 4 map, 5 extract-rules, 6 review, 7 brief, 8 transform, "
            "9 uplift, 10 reimagine, 11 verify, 12 harden, 13 status, 20-22 pane commands, 99 other"),
    ("perm", "permission mode the session ran in: 0 unknown, 1 default, 2 accept edits, 3 plan, 4 auto, 5 bypass, 6 don't ask"),
    ("has_source", "1 when the command carried --source"),
    ("fresh", "1 when the system has no artifacts yet"),
    ("systems", "systems under analysis/"),
    ("goal", "0 unknown, 1 understand, 2 uplift, 3 transform, 4 reimagine"),
    ("lang", "dominant language of the map: 1 COBOL, 2 Java, 3 C#/.NET, 4 Python, 5 PHP, 6 Perl, 7 C, 8 C++, "
             "9 JavaScript/TypeScript, 10 Ruby, 11 Go, 12 Rust, 13 Kotlin/Scala, 14 SQL, 15 Fortran, 16 RPG, 17 Pascal/Delphi, "
             "18 shell, 19 assembler, 99 other, 0 unknown"),
    ("done", "steps that have left their file, added up: " + ", ".join("%s=%d" % s for s in STEPS)),
    ("map_kloc", "thousand lines of code in the map"),
    ("rules", "business rules found"),
    ("p0", "of those, the critical (P0) ones"),
    ("rev_ok", "rules a person confirmed"),
    ("rev_wrong", "rules a person marked wrong"),
    ("phases", "phases in the plan"),
    ("built", "modules or services built (an uplift's working copy counts as one once it exists)"),
    ("eq_cases", "old-versus-new comparison cases run"),
    ("eq_diff", "of those, differences or missing outputs nobody approved"),
    ("eq_appr", "differences a person approved"),
    ("v_proven", "modules judged PROVEN"),
    ("v_partly", "modules judged PARTLY PROVEN"),
    ("v_not", "modules judged NOT PROVEN"),
    ("sec_crit", "critical security findings"),
    ("sec_high", "high security findings"),
    ("os", "system: 1 macOS, 2 Linux, 3 Windows, 4 Windows subsystem for Linux, 0 other"),
    ("py", "how python worked: 0 python3 ran, 1 none found, 2 macOS developer-tools stub, 3 python3 present but broken (the Windows Store stub), "
           "4 python3 unusable but python or py ran, 5 too old, 6 the script crashed"),
    ("pyv", "python version as major*100 + minor (311 is 3.11)"),
    ("pathf", "the folder's path: 1 has a space, 2 has non-ASCII characters, 4 is over 200 characters (added up)"),
    ("tool", "the tool that failed: 1 Bash, 2 Read, 3 Edit or Write, 4 Glob or Grep, 5 agent, 6 Workflow, 7 asking the person, 8 skill, 9 web, 10 a connector, 99 other"),
    ("kind", "what went wrong: 1 python or another interpreter missing, 2 the Windows Store python stub, 3 the macOS developer-tools stub, 4 python too old or a syntax error, "
            "5 one of the plugin's scripts raised an error, 6 blocked by a permission rule or policy, 7 a file permission was denied, 8 timed out, 9 a file or folder was not found, "
            "10 network, certificate or sign-in, 11 disk or memory, 12 workflow or agent trouble, 99 other"),
    ("api", "a model call ended a turn: 1 rate limit, 2 sign-in failed, 3 billing, 4 invalid request, 5 server error or overloaded, 6 output too long, 7 network or timeout, 99 unknown"),
    ("err", "the plugin's own script raised: 1 KeyError, 2 ValueError, 3 OSError, 4 TypeError, 5 AttributeError, 6 RecursionError, 7 MemoryError, 8 UnicodeError, 99 other"),
    ("err_at", "the line of telemetry.py where it raised"),
    ("agents", "agents the last rule extraction started"),
    ("wf_failed", "modules or agents that extraction lost"),
    ("wf_skip", "modules that extraction skipped"),
    ("wf_unver", "rules that extraction could not verify"),
])
COMMAND_KEYS = ("pv", "cmd", "perm", "has_source", "fresh", "systems", "goal", "done", "os", "py", "pyv", "pathf")
RUN_KEYS = ("pv", "agents", "wf_failed", "wf_skip", "wf_unver")
FAILURE_KEYS = ("pv", "os", "py", "pyv", "pathf", "tool", "kind", "api")
ERROR_KEYS = ("pv", "os", "py", "pyv", "err", "err_at")
STATE_KEYS = ("pv", "goal", "lang", "done", "map_kloc", "rules", "p0", "rev_ok", "rev_wrong", "phases", "built", "eq_cases",
              "eq_diff", "eq_appr", "v_proven", "v_partly", "v_not", "sec_crit", "sec_high")


def off_reason(env=None):
    """Why nothing is sent, or "" when counts may be sent. Sending needs the plugin's switches to be unset or an explicit
    "on": any other word (off, no, 0, disabled) turns it off."""
    env = os.environ if env is None else env
    val = lambda key: str(env.get(key, "")).strip().lower()  # noqa: E731
    if val("CODE_MODERNIZATION_TELEMETRY") and val("CODE_MODERNIZATION_TELEMETRY") not in TRUE:
        return "CODE_MODERNIZATION_TELEMETRY is off"
    if val("CLAUDE_PLUGIN_OPTION_TELEMETRY") and val("CLAUDE_PLUGIN_OPTION_TELEMETRY") not in TRUE:
        return "the plugin's Usage counts option is off"
    for key in ("DISABLE_TELEMETRY", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"):
        if val(key) in TRUE:
            return "%s is set" % key
    return ""


def whole(value):
    """A whole number from 0 to CAP, whatever the artifact held."""
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, min(CAP, int(value)))
    except (TypeError, ValueError, OverflowError):
        return 0


def plugin_version():
    try:
        with open(os.path.join(HERE, "..", ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
            major, minor, patch = (int(x) for x in str(json.load(fh)["version"]).split(".")[:3])
        return major * 10000 + minor * 100 + patch
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def plain(path):
    return os.path.isfile(path) and not os.path.islink(path)


def inside(cwd, path):
    """True when path really lives under cwd (links that lead elsewhere are not followed)."""
    try:
        root = os.path.realpath(cwd)
        return os.path.commonpath([root, os.path.realpath(path)]) == root
    except ValueError:
        return False


def systems_in(cwd):
    """[(newest modification time, name)] of the folders under analysis/, newest first."""
    out, folder = [], os.path.join(cwd, "analysis")
    if os.path.islink(folder) or not inside(cwd, folder):
        return out
    try:
        entries = list(itertools.islice(os.scandir(folder), 200))
    except OSError:
        return out
    for e in entries:
        if e.name.startswith(".") or e.is_symlink() or not e.is_dir():
            continue
        try:
            times = [e.stat().st_mtime]
            kids = list(itertools.islice(os.scandir(e.path), 200))
        except OSError:
            continue
        for x in kids:
            try:
                times.append(x.stat().st_mtime)
            except OSError:  # a dangling link or a file that just went away
                pass
        out.append((max(times), e.name))
    return sorted(out, reverse=True)


def language_code(topo):
    """The language with the most lines in the map, as its number."""
    weight, nodes = collections.Counter(), []

    def walk(node, depth):
        if isinstance(node, dict) and depth < 12:
            nodes.append(node)
            for child in node.get("children") or []:
                walk(child, depth + 1)

    if isinstance(topo, dict):
        walk(topo.get("root"), 0)
    for n in nodes:
        lang = n.get("language")
        if not n.get("children") and isinstance(lang, str) and isinstance(n.get("loc"), int) and n["loc"] > 0:
            low = lang.strip().lower()[:40]
            first = re.match(r"[a-z0-9#+]+", low)
            first = first.group(0) if first else ""
            if low in NOT_CODE or first in NOT_CODE:
                continue  # build files, data and the like are not what is being modernized
            weight[LANGS.get(low) or LANGS.get(first) or 99] += n["loc"]
    return min(weight, key=lambda c: (-weight[c], c)) if weight else 0


def goal_code(text, built):
    """From the answer written after "Goal" in INTENT.md (its first words, not the sentences around it), else from what was built."""
    lines = [re.sub(r"[*`_#>\-]", " ", l).strip() for l in (text or "").split("\n")[:60]]
    for i, line in enumerate(lines):
        m = GOAL_LABEL.match(line)
        if not m:
            continue
        rest = m.group(1)
        if not rest:  # a heading: the answer is on the next line that has words
            rest = next((l for l in lines[i + 1:i + 4] if l), "")
            rest = (GOAL_LABEL.match(rest) or GOAL_LABEL.match("goal " + rest)).group(1)
        word = GOAL_WORDS.match(rest)
        if word:
            word = word.group(1).lower()
            return GOALS[GOAL_ALIASES.get(word, word)]
        for pattern, code in GOAL_PHRASES:
            if pattern.search(rest[:100]):
                return code
        break
    return {"": 3, "-uplifted": 2, "-reimagined": 4}.get(built, 0)


def built_kind_and_count(cwd, system):
    """(which kind of build is newest: '' rewrite, '-uplifted' or '-reimagined'; how many modules or services)."""
    total, kinds = 0, []
    for suffix in ("", "-uplifted", "-reimagined"):
        root = os.path.join(cwd, "modernized", system + suffix)
        if os.path.islink(root) or not inside(cwd, root):
            continue
        try:
            kids = [e for e in os.scandir(root) if not e.name.startswith(".") and not e.is_symlink()]
            newest = max(e.stat().st_mtime for e in kids) if kids else 0
        except OSError:
            continue
        if not kids:
            continue
        dirs = [e for e in kids if e.is_dir()]
        total += 1 if suffix == "-uplifted" else (len(dirs) or 1)
        kinds.append((newest, suffix))
    return (max(kinds)[1] if kinds else None), total


def snapshot(cwd, system):
    """The counts for one system, or None when the plugin has left nothing there yet."""
    src = br.Source(cwd, system)
    path = lambda name: os.path.join(src.adir, name)  # noqa: E731

    def text(name):
        raw = src.read(path(name), name)
        return None if raw is None else "\n".join(line[:LINE_WIDTH] for line in raw.split("\n"))

    if not any(plain(path(name)) for name in GATE):
        return None
    done, out = 0, collections.OrderedDict((k, 0) for k in STATE_KEYS)
    present = {step: plain(path(FILES[step])) for step in FILES}

    rules_text = text("BUSINESS_RULES.md")
    reviews, _ = src.json(path("RULE_REVIEWS.json"), "RULE_REVIEWS.json")
    reviews = {k: v for k, v in reviews["reviews"].items() if isinstance(v, dict)} if isinstance(reviews, dict) and isinstance(reviews.get("reviews"), dict) else {}
    cards = [b for b in br.parse_rules(rules_text) if b["k"] == "rule"] if rules_text else []
    if cards:
        facts = br.rule_facts(rules_text, cards, reviews)
        out["rules"], out["p0"] = whole(facts["total"]), whole(facts["byPriority"].get("P0", 0))
        present["rules"] = True
    verdicts = collections.Counter(str(v.get("verdict", "")).lower() for v in reviews.values())
    out["rev_ok"], out["rev_wrong"] = whole(verdicts["confirmed"]), whole(verdicts["wrong"])
    present["reviewed"] = bool(reviews)

    topo, _ = src.json(path("topology.json"), "topology.json")
    facts = br.topology_facts(topo)
    out["map_kloc"] = whole(facts["loc"] // 1000) if facts else 0
    out["lang"] = language_code(topo)

    brief = text("MODERNIZATION_BRIEF.md") or ""
    out["phases"] = len(re.findall(r"(?m)^#{2,4}[ \t]*Phase[ \t]+\d+", brief))
    for line in brief.split("\n"):
        m = re.match(r"(?i)^\s*Approved by\s*:(.*?)(?:Date\s*:.*)?$", line)
        if m:
            present["approved"] = bool(re.search(r"[A-Za-z0-9]", m.group(1)))
            break

    # counted from the case list and the modules' own checks, the way the report does, never from the file's own totals
    eq, _ = src.json(path("EQUIVALENCE.json"), "EQUIVALENCE.json")
    view = br.equivalence_view(eq)
    if view:
        tally = view["tally"]
        out["eq_cases"] = whole(tally["executed"])
        out["eq_diff"] = whole(sum(tally.get(k, 0) for k in ("differs", "missing", "inconsistent", "unknown")))
        out["eq_appr"] = whole(tally.get("differs-approved", 0))

    ver, _ = src.json(path("VERIFICATION.json"), "VERIFICATION.json")
    proof = br.proof_view(ver)
    if proof:
        out["v_proven"], out["v_partly"], out["v_not"] = (whole(proof["counts"].get(k)) for k in ("PROVEN", "PARTLY PROVEN", "NOT PROVEN"))
        present["signed"] = bool(proof["signoff"]["name"].strip() and proof["signoff"]["decision"].strip())

    security = br.security_facts(text("SECURITY_FINDINGS.md") or "") or {}
    out["sec_crit"], out["sec_high"] = whole(security.get("Critical")), whole(security.get("High"))

    kind, out["built"] = built_kind_and_count(cwd, system)
    present["built"] = bool(out["built"])
    for step, bit in STEPS:
        done |= bit if present.get(step) else 0
    out["done"] = done
    out["goal"] = goal_code(text("INTENT.md"), kind)
    out["pv"] = plugin_version()
    return out


def os_code():
    """1 macOS, 2 Linux, 3 Windows, 4 WSL, 0 other. The shell wrapper knows best (uname); this is the fallback."""
    given = os.environ.get("CODE_MODERNIZATION_OS", "")
    if given.isdigit():
        return min(int(given), 9)
    system = platform.system().lower()
    if system == "linux":
        try:
            with open("/proc/version", encoding="utf-8", errors="replace") as fh:
                return 4 if "microsoft" in fh.read().lower() else 2
        except OSError:
            return 2
    return {"darwin": 1, "windows": 3}.get(system, 0)


def python_status():
    """0 when python3 itself ran this; the shell wrapper says 4 when it had to fall back to python or py."""
    given = os.environ.get("CODE_MODERNIZATION_PY", "")
    return min(int(given), 9) if given.isdigit() else 0


def path_flags(cwd):
    """The bits of a folder path that break scripts on Windows: 1 a space, 2 a non-ASCII character, 4 over 200 characters."""
    given = os.environ.get("CODE_MODERNIZATION_PATHF", "")
    if given.isdigit():
        return min(int(given), 7)
    return (1 if " " in cwd else 0) + (2 if any(ord(c) > 126 for c in cwd) else 0) + (4 if len(cwd) > 200 else 0)


def environment(cwd):
    return [("os", os_code()), ("py", python_status()), ("pyv", sys.version_info[0] * 100 + sys.version_info[1]), ("pathf", path_flags(cwd))]


def system_word(words):
    """The first plain word of a command's arguments, which is the system's name (a flag's value is not)."""
    skip = False
    for w in words:
        if skip:
            skip = False
        elif w.startswith("-"):
            skip = w == "--source"
        elif NAME.fullmatch(w):
            return w
    return None


def command_metrics(prompt, cwd, permission_mode=None):
    """The counts for one typed prompt, or None when it is not one of the plugin's commands."""
    m = COMMAND_RE.match(str(prompt or "").lstrip())
    if not m:
        return None
    verb = m.group("verb") or ""
    if m.group("ns"):
        cmd = COMMANDS.get(verb, OTHER_COMMAND)
    elif verb in PANE:
        cmd = PANE[verb]
    elif verb in COMMANDS:
        cmd = COMMANDS[verb]
    else:
        return None  # another tool's /modernize-something
    words = str(prompt).lstrip()[m.end():].split()
    systems = systems_in(cwd)
    named = system_word(words)
    if named in {n for _, n in systems}:
        system = named
    else:  # a name that does not exist yet is a new system; no name at all means the newest one
        system = None if named else (systems[0][1] if systems else None)
    snap = snapshot(cwd, system) if system else None
    perm = PERMISSION_MODES.get(permission_mode, 0) if isinstance(permission_mode, str) else 0
    return collections.OrderedDict([("pv", plugin_version()), ("cmd", cmd), ("perm", perm), ("has_source", int("--source" in words)),
                                    ("fresh", int(snap is None)), ("systems", min(len(systems), 99)),
                                    ("goal", snap["goal"] if snap else 0), ("done", snap["done"] if snap else 0)] + environment(cwd))


def health_metrics(cwd):
    """Once per version and machine (the shell wrapper keeps count): what the plugin is running on."""
    return collections.OrderedDict([("pv", plugin_version())] + environment(cwd))


def run_metrics(cwd):
    """How the newest system's last rule extraction went, from the statistics the workflow wrote, or None."""
    for _, system in systems_in(cwd)[:5]:
        src = br.Source(cwd, system)
        result, _ = src.json(os.path.join(src.adir, "rules_result.json"), "rules_result.json")
        stats = result.get("stats") if isinstance(result, dict) and isinstance(result.get("stats"), dict) else None
        if stats is None:
            continue
        size = lambda key: len(stats[key]) if isinstance(stats.get(key), list) else 0  # noqa: E731
        return collections.OrderedDict([("pv", plugin_version()), ("agents", whole(stats.get("agents"))), ("wf_failed", size("failedModules") + size("droppedModules")),
                                        ("wf_skip", size("skippedModules")), ("wf_unver", whole(stats.get("unverified")))])
    return None


def tool_code(name):
    name = str(name or "")
    return TOOLS.get(name) or (10 if name.startswith("mcp__") else 99)


def failure_kind(text):
    """A code for what went wrong, decided from the failure's own text (which is never sent), or None when it says nothing useful."""
    text = str(text or "")[:8000]
    if "Traceback" in text and ("code-modernization" in text or "scripts/" in text or "scripts\\" in text):
        return 5
    for code, pattern in FAILURE_KINDS:
        if pattern.search(text):
            return code
    return None


def failure_metrics(data, cwd):
    """One failure as numbers: a failed tool call, or a model call that ended a turn. None when there is nothing to say."""
    event, session = str(data.get("hook_event_name") or ""), str(data.get("session_id") or "")
    base = [("pv", plugin_version())] + environment(cwd)
    if event == "StopFailure":
        text = " ".join(str(data.get(k) or "") for k in ("error", "error_type", "error_details", "message"))[:2000]
        api = next((code for code, pattern in API_ERRORS if pattern.search(text)), 99)
        tag, extra = "api%d" % api, [("api", api)]
    else:
        if data.get("is_interrupt") is True:
            return None
        tool, error = tool_code(data.get("tool_name")), str(data.get("error") or "")
        kind = failure_kind(error)
        if kind is None:
            if tool == 1 and re.fullmatch(r"\s*Exit code \d+\s*", error):
                return None  # a command that simply exited non-zero, often on purpose
            kind = 99
        tag, extra = "t%dk%d" % (tool, kind), [("tool", tool), ("kind", kind)]
    if remember("fail|%s|%s" % (session, tag), "1") != "new":  # once per session and kind, so a loop of failures is one number
        return None
    return collections.OrderedDict(base + extra)


def state_metrics(cwd):
    """The counts for the newest system under cwd that the plugin has worked on, or None."""
    for _, system in systems_in(cwd)[:5]:
        snap = snapshot(cwd, system)
        if snap is not None:
            return snap
    return None


def rounded(value):
    """Two significant figures from 100 up (17727 becomes 18000), so a count says roughly how big, not exactly which system."""
    if value < 100:
        return value
    scale = 10 ** (len(str(value)) - 2)
    return (value + scale // 2) // scale * scale


def ok(metrics):
    """Only keys this script defines, only whole numbers within their limit, counts rounded, at most MAX_KEYS of them."""
    out = collections.OrderedDict()
    for k, v in list(metrics.items())[:MAX_KEYS]:
        if k in MEANING:
            v = min(whole(v), LIMITS.get(k, COUNT_LIMIT))
            out[k] = v if k in EXACT else rounded(v)
    return out


def data_dir():
    """The plugin's own data folder, or a private folder in the temp directory; None when neither can be used safely."""
    uid = getattr(os, "getuid", lambda: 0)()
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or ""
    base = os.path.realpath(base) if os.path.isdir(base) else os.path.join(tempfile.gettempdir(), "code-modernization-%s" % uid)
    try:
        os.makedirs(base, mode=0o700, exist_ok=True)
        st = os.lstat(base)
    except OSError:
        return None
    if os.path.islink(base) or not stat.S_ISDIR(st.st_mode) or (hasattr(st, "st_uid") and st.st_uid != uid):
        return None
    return base


def note(text):
    """With CODE_MODERNIZATION_TELEMETRY_DEBUG=1, one line saying what a hook run decided, in telemetry-debug.log in the data
    folder (a link is never followed, and the file is cut down when it grows past 200 KB). Never raises."""
    if str(os.environ.get("CODE_MODERNIZATION_TELEMETRY_DEBUG", "")).strip().lower() not in TRUE:
        return
    base = data_dir()
    if not base:
        return
    file = os.path.join(base, "telemetry-debug.log")
    try:
        if os.path.getsize(file) > 200000:
            os.remove(file)
    except OSError:
        pass
    try:
        fd = os.open(file, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0), 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write("%s %s\n" % (time.strftime("%H:%M:%S"), text))
    except OSError:
        pass


def remember(key, digest):
    """"new" when this workspace's counts changed since they were last sent and the new state is stored, "same" when
    they did not, "cannot" when the state cannot be stored: nothing is sent then, it would repeat at the end of every turn."""
    base = data_dir()
    if not base:
        return "cannot"
    try:
        file = os.path.join(base, "telemetry-state.json")
        try:
            with open(file, encoding="utf-8") as fh:
                seen = json.load(fh)
        except (OSError, ValueError):
            seen = {}
        seen = seen if isinstance(seen, dict) else {}
        if seen.get(key) == digest:
            return "same"
        seen.pop(key, None)
        seen[key] = digest
        seen = dict(list(seen.items())[-200:])
        tmp = "%s.%d" % (file, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(seen, fh)
        os.replace(tmp, file)
        return "new"
    except OSError:
        return "cannot"


def digest_of(metrics):
    return hashlib.sha1(json.dumps(metrics, sort_keys=True).encode()).hexdigest()[:12]


def hook(mode):
    """Run one hook. Whatever an artifact holds, a turn is never held up for more than a few seconds."""
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, lambda *_: os._exit(0))
        signal.alarm(3)
        try:
            run_hook(mode)
        finally:
            signal.alarm(0)
    else:  # Windows has no alarm signal: a timer thread gives up instead
        timer = threading.Timer(3, os._exit, [0])
        timer.daemon = True
        timer.start()
        try:
            run_hook(mode)
        finally:
            timer.cancel()
            timer.join(1)


def run_hook(mode):
    reason = off_reason()
    if reason:
        return note("%s: not sent, %s" % (mode, reason))
    try:
        data = json.loads(sys.stdin.read(1 << 20) or "{}")
    except ValueError:
        data = {}
    data = data if isinstance(data, dict) else {}
    cwd = data.get("cwd") if isinstance(data.get("cwd"), str) and os.path.isdir(data.get("cwd")) else os.getcwd()
    why = ""
    if mode == "command":
        metrics = command_metrics(data.get("prompt"), cwd, data.get("permission_mode"))
        why = "not one of the plugin's commands"
    elif mode == "health":
        metrics, why = health_metrics(cwd), ""
    elif mode == "failure":
        metrics = failure_metrics(data, cwd)
        why = "nothing worth counting, or the same kind was already sent this session"
    else:
        metrics = run_metrics(cwd) if mode == "run" else state_metrics(cwd)
        why = "the plugin has left no files here"
        if metrics is not None:
            key = hashlib.sha1((os.path.realpath(cwd) + mode).encode()).hexdigest()[:16]
            status = remember(key, digest_of(ok(metrics)))
            if status != "new":
                metrics, why = None, "the counts are the same as last time" if status == "same" else "the state file cannot be written"
    if metrics:
        print(json.dumps({"metrics": ok(metrics)}, separators=(",", ":")), flush=True)
        note("%s: sent %d values" % (mode, len(ok(metrics))))
    else:
        note("%s: not sent, %s" % (mode, why))


def show(args):
    """What the hooks would send for a workspace, in words."""
    cwd, prompt, as_json, i = None, None, False, 0
    while i < len(args):
        if args[i] == "--json":
            as_json = True
        elif args[i] == "--prompt":
            prompt, i = args[i + 1] if i + 1 < len(args) else "", i + 1
        elif not args[i].startswith("--") and cwd is None:
            cwd = os.path.abspath(args[i])
        i += 1
    cwd = cwd or os.getcwd()
    example = prompt is None
    prompt = "/code-modernization:modernize-status" if example else prompt
    state, command = state_metrics(cwd), command_metrics(prompt, cwd)
    if as_json:
        print(json.dumps({"off": off_reason(), "state": ok(state) if state else None, "command": ok(command) if command else None}))
        return

    def table(title, metrics, empty):
        print(title)
        if metrics is None:
            print("  " + empty + "\n")
            return
        for k, v in ok(metrics).items():
            note = MEANING[k].split(":")[0] if k in ("cmd", "lang", "done") else MEANING[k]
            if k == "done":
                note += ": " + (", ".join(n for n, bit in STEPS if v & bit) or "nothing yet")
            print("  %-10s %-8d %s" % (k, v, note))
        print()

    reason = off_reason()
    print("Usage counts for %s" % cwd)
    print("Sending is OFF: %s.\n" % reason if reason else "Sending is on. Turn it off with CODE_MODERNIZATION_TELEMETRY=0 or the plugin's Usage counts option.\n")
    table("When a turn ends and these counts have changed:", state, "nothing: the plugin has left no artifacts here yet")
    table("When you type %s%s:" % ("a command, for example " if example else "", prompt.split()[0] if prompt.split() else "nothing"), command,
          "nothing: that is not one of the plugin's commands")


def report_error(err, line):
    """The plugin's own script raised: send which kind and where, once, never the message."""
    if off_reason():
        return
    code = next((c for kind, c in ERROR_CODES if isinstance(err, kind)), 99)
    if remember("err|%s|%s|%s" % (plugin_version(), code, line), "1") == "new":
        print(json.dumps({"metrics": ok(collections.OrderedDict([("pv", plugin_version()), ("os", os_code()), ("py", python_status()),
                                                                 ("pyv", sys.version_info[0] * 100 + sys.version_info[1]), ("err", code), ("err_at", line)]))},
                         separators=(",", ":")), flush=True)


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    try:
        if mode == "show":
            show(argv[2:])
        elif mode in ("command", "state", "run", "failure", "health"):
            hook(mode)
        else:
            print(__doc__)
    except Exception as err:  # a usage count must never break the person's session
        if mode == "show":
            raise
        tb = err.__traceback__
        while tb and tb.tb_next:
            tb = tb.tb_next
        line = tb.tb_lineno if tb else 0
        note("%s: error %s at line %s" % (mode, type(err).__name__, line))
        try:
            report_error(err, line)
        except Exception:  # reporting a problem must not become one
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
