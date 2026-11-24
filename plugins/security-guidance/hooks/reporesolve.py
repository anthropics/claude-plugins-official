import itertools
import os
import re
import shlex
import subprocess
import tempfile
import time

from gitutil import GIT_CMD, _folder_with_git_entry, _git_toplevel, _other_repo_with_commands, _stay_out, no_download_env
from session_state import with_locked_state


RES_NONE = 0
RES_CWD = 1
RES_COMMAND = 2
RES_SHA_SCAN = 3
RES_TOUCHED_PATHS = 4
RES_HINT = 5
RES_NAMED = 6  # a folder the command names, where the commit it printed was made

COMMIT_SUBCOMMANDS = {("git", "commit"), ("gt", "create"), ("gt", "modify")}
PUSH_SUBCOMMANDS = {("git", "push"), ("gt", "submit")}

SCAN_SKIP_DIRS = {
    "node_modules", ".venv", "venv", "__pycache__", ".tox", "dist",
    "build", "target", ".cache", ".git", "vendor", "site-packages",
}
SCAN_MAX_DEPTH = int(os.environ.get("SG_REPO_SCAN_MAX_DEPTH", "3"))
SCAN_MAX_REPOS = int(os.environ.get("SG_REPO_SCAN_MAX_REPOS", "64"))
SCAN_BUDGET_S = float(os.environ.get("SG_REPO_SCAN_BUDGET_S", "4"))

_SEPARATORS = frozenset(";&|(){}\n")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_PREFIX_WORDS = frozenset(("env", "time", "exec", "command", "nohup"))
_CHANGE_DIR_WORDS = frozenset(("cd", "pushd", "set-location", "push-location"))
_PUSH_DIR_WORDS = frozenset(("pushd", "push-location"))
_POP_DIR_WORDS = frozenset(("popd", "pop-location"))


def _abs(base, p):
    try:
        p = os.path.expanduser(p)
        if not os.path.isabs(p):
            p = os.path.join(base or os.getcwd(), p)
        return os.path.normpath(p)
    except (TypeError, ValueError, OSError):
        return None


def _is_sep(tok):
    return bool(tok) and set(tok) <= _SEPARATORS


def _tokenize(command):
    # shlex reads a line end as a space, but it ends a statement, unless a
    # backslash or a PowerShell backtick continues the line.
    command = re.sub(r"[\\`]\r?\n", " ", command)
    command = re.sub(r"\r?\n", " ; ", command)
    if os.sep == "\\":
        command = command.replace("\\", "\\\\")
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        try:
            return command.replace("&&", " && ").replace(";", " ; ").split()
        except Exception:
            return []


def dirs_from_command(command, cwd, subcommands=None):
    if not isinstance(command, str) or not command.strip():
        return []
    tokens = _tokenize(command)
    out = []
    cur = cwd or ""
    pushed = []
    i = 0
    n = len(tokens)
    at_start = True
    while i < n:
        t = tokens[i]
        if _is_sep(t):
            at_start = True
            i += 1
            continue
        if at_start and (_ENV_ASSIGN_RE.match(t) or t in _PREFIX_WORDS):
            i += 1
            continue
        if at_start and t.lower() in _POP_DIR_WORDS:
            if pushed:
                cur = pushed.pop()
            i += 1
            at_start = False
            continue
        if at_start and t.lower() in _CHANGE_DIR_WORDS:
            if t.lower() in _PUSH_DIR_WORDS:
                pushed.append(cur)
            # PowerShell names the folder with an optional -Path.
            if i + 2 < n and tokens[i + 1].lower() in ("-path", "-literalpath"):
                i += 1
            if i + 1 < n and not _is_sep(tokens[i + 1]) and tokens[i + 1] not in ("-",) \
                    and not tokens[i + 1].startswith("-"):
                nxt = _abs(cur, tokens[i + 1])
                if nxt:
                    cur = nxt
                i += 2
            else:
                i += 1
            at_start = False
            continue
        prog = os.path.basename(t) if t else t
        if prog.lower() in ("git", "git.exe", "git.cmd"):
            prog = "git"
        if at_start and prog in ("git", "gt"):
            j = i + 1
            cdir = cur
            gdir = None
            wtree = None
            if prog == "git":
                while j < n and not _is_sep(tokens[j]):
                    a = tokens[j]
                    if a == "-C" and j + 1 < n:
                        cdir = _abs(cdir, tokens[j + 1]) or cdir
                        j += 2
                        continue
                    if a == "-c" and j + 1 < n:
                        j += 2
                        continue
                    if a.startswith("--git-dir="):
                        gdir = _abs(cdir, a.split("=", 1)[1])
                        j += 1
                        continue
                    if a == "--git-dir" and j + 1 < n:
                        gdir = _abs(cdir, tokens[j + 1])
                        j += 2
                        continue
                    if a.startswith("--work-tree="):
                        wtree = _abs(cdir, a.split("=", 1)[1])
                        j += 1
                        continue
                    if a == "--work-tree" and j + 1 < n:
                        wtree = _abs(cdir, tokens[j + 1])
                        j += 2
                        continue
                    if a.startswith("-"):
                        j += 1
                        continue
                    break
            sub = tokens[j] if j < n and not _is_sep(tokens[j]) else None
            if subcommands is None or (prog, sub) in subcommands:
                cand = wtree
                if not cand and gdir:
                    cand = os.path.dirname(gdir) if os.path.basename(gdir) == ".git" else gdir
                if not cand:
                    cand = cdir
                if cand:
                    out.append(cand)
            i = j + 1 if j < n else j
            at_start = False
            continue
        at_start = False
        i += 1
    return list(dict.fromkeys(d for d in out if d))


def toplevel_from_command(command, cwd, subcommands=None, cwd_root=None):
    cwd_abs = _abs(None, cwd) if cwd else None
    for d in dirs_from_command(command, cwd, subcommands):
        if cwd_root and d == cwd_abs:
            return cwd_root
        try:
            if os.path.isdir(d):
                top = _git_toplevel(d)
                if top:
                    return top
        except OSError:
            continue
    return None


def command_in_left_out_repo(command, cwd, subcommands):
    """True when a folder the command names is in a repository the hooks stay
    out of: what it did there is not another repository's. For a command that
    toplevel_from_command finds no repository for."""
    return any(os.path.isdir(d) and _other_repo_with_commands(d)
               for d in dirs_from_command(command, cwd, subcommands))


# The folder a commit was made in cannot be read off the command in general
# (branches, loops, subshells, variables). So dirs_from_command gives the first
# choice. Only where that does not have the commit that git printed, the other
# folders the command names are looked at, and one is taken only if its own
# reflog has that commit, made while the command ran.
NAMED_MAX_WORDS = 64
NAMED_MAX_FOLDERS = 64
NAMED_MAX_REPOS = 16
NAMED_BUDGET_S = 4.0
_MAX_WORD = 1024

# A shell word: quoted and unquoted pieces, next to each other.
_WORD = r"""((?:"(?:[^"\\]|\\.)*"|'[^']*'|[^\s;&|()<>"'`\\]|\\.){1,1024})"""
_WORD_RE = re.compile(_WORD)
_NAMED_FOLDER_RE = re.compile(
    r"""(?:(?<![\w./-])(?i:cd|pushd|set-location|push-location)(?:[ \t]+(?:-[A-Za-z@]{1,12}|/[dD]))?(?:[ \t]+--)?[ \t]+"""
    r"""|(?<![\w-])-C[ \t]*|(?<![\w-])--(?:git-dir|work-tree|chdir)[= \t][ \t]*"""
    r"""|(?<!\w)GIT_(?:DIR|WORK_TREE)=)""" + _WORD)
_SET_VARIABLE_RE = re.compile(r"""(?:(?<![\w$-])([A-Za-z_]\w{0,63})=|\$([A-Za-z_]\w{0,63})[ \t]*=[ \t]*)""" + _WORD)
_FOR_RE = re.compile(r"""(?<!\w)for[ \t]+([A-Za-z_]\w{0,63})[ \t]+in[ \t]+([^;\n]{1,8192})""")
_VARIABLE_RE = re.compile(r"""\$(?:\{([A-Za-z_]\w*)\}|([A-Za-z_]\w*))""")
_PIECE_RE = re.compile(r""""(?:[^"\\]|\\.)*"|'[^']*'|(?:[^"'\\]|\\.)+|.""", re.S)


def _unquoted(word):
    """The readings of one shell word: quotes off, and backslashes as escapes
    or, on Windows, as separators too."""
    word = word[:_MAX_WORD]
    bash, plain = "", ""
    for piece in _PIECE_RE.findall(word):
        if piece[0] == "'" and len(piece) > 1:
            piece = escaped = piece[1:-1]
        elif piece[0] == '"' and len(piece) > 1:
            piece = piece[1:-1]
            escaped = re.sub(r'\\(["\\$`])', r"\1", piece)
        else:
            escaped = re.sub(r"\\(.)", r"\1", piece)
        bash += escaped
        plain += piece
    return list(dict.fromkeys([bash, plain] if os.sep == "\\" else [bash]))


def _values(word, variables, deadline, depth=6):
    """What `word` can be, with the command's own variables or else the
    environment's in place."""
    m = _VARIABLE_RE.search(word)
    if not m:
        return [word] if "$" not in word and "`" not in word else []
    if depth == 0 or time.monotonic() > deadline:
        return []
    name = m.group(1) or m.group(2)
    if name in ("PWD", "OLDPWD"):
        found = ["."]
    else:
        found = variables.get(name) or ([os.environ[name]] if os.environ.get(name) else [])
    out = []
    for value in found:
        whole = word[:m.start()] + value + word[m.end():]
        if len(whole) <= _MAX_WORD and len(out) < 16:
            out += _values(whole, variables, deadline, depth - 1)
    return out[:16]


def _each_named(command):
    """Matches of _NAMED_FOLDER_RE. The next is looked for right after the
    start of the word: what closes a quote looks like one that opens."""
    pos = 0
    while True:
        m = _NAMED_FOLDER_RE.search(command, pos)
        if not m:
            return
        yield m
        pos = m.start(1) + 1


def _last(items, n):
    """The first half of `n`, and the last: the printed commit is the last one."""
    items = list(items)
    return items if len(items) <= n else items[:n // 2] + items[-(n - n // 2):]


def _named_words(command, deadline):
    """The operands of every `cd`, `-C` or the like in `command`, wherever in
    it: in a branch, a loop, quotes or a heredoc. Text only."""
    variables = {}

    def note(name, values):
        if name in variables or len(variables) < NAMED_MAX_WORDS:
            known = variables.setdefault(name, [])
            known += [v for v in values if v not in known][:16 - len(known)]

    raw = {}
    for m in _each_named(command):
        raw.pop(m.group(1), None)
        raw[m.group(1)] = 0
        if len(raw) > NAMED_MAX_WORDS:
            # The first half, and the last: the commit is usually near the end.
            raw.pop(next(itertools.islice(raw, NAMED_MAX_WORDS // 2, None)))
        if time.monotonic() > deadline:
            break
    if any("$" in w for w in raw):
        for m in _SET_VARIABLE_RE.finditer(command):
            note(m.group(1) or m.group(2), _unquoted(m.group(3)))
            if time.monotonic() > deadline:
                break
        for m in _FOR_RE.finditer(command):
            words = _last((w.group(1) for w in _WORD_RE.finditer(m.group(2))), 16)
            # A bare variable in the list stands for the words in its value.
            note(m.group(1), [v for w in words for q in _unquoted(w)
                              for v in (_values(q, variables, deadline) if "$" in w else [q])
                              for v in ([v] if w[0] in "\"'" or "$" not in w else v.split())])
            if time.monotonic() > deadline:
                break
    out = {}
    for word in raw:
        # As it reads at the top level, and inside a double-quoted command,
        # where \" is a quote and the first bare one ends the word.
        inner = re.split(r"""(?<!\\)["']""", word[:_MAX_WORD])[0].replace('\\"', '"')
        for w in _unquoted(word) + (_unquoted(inner) if inner not in ("", word) else []):
            out.update(dict.fromkeys(_values(w, variables, deadline)))
    return _last((w for w in out if w not in ("", ".", "-")), NAMED_MAX_WORDS)


def _windows_paths(p):
    """What a path of Git Bash is to Windows: /c/x, /cygdrive/c/x, /tmp/x."""
    m = re.match(r"/(?:cygdrive/)?([A-Za-z])(?:/|$)", p)
    if m:
        return [f"{m.group(1)}:/{p[m.end():]}", p]
    if p == "/tmp" or p.startswith("/tmp/"):
        return [tempfile.gettempdir() + p[4:], p]
    return [p]


def _without_slash(p):
    """`p` without the slashes at its end, unless it is a root (`/`, `C:/`)."""
    out = p.rstrip("/\\")
    return p if not out or out.endswith(":") else out


def _named_folders(command, cwd, words, deadline):
    """Existing folders that `words` lead to, from `cwd` or one another."""
    bases = [_abs(None, cwd)]

    def add(d):
        # Never a network path: looking at one connects to that host.
        if d and d not in bases and not d.startswith(("//", "\\\\")) and os.path.isdir(d):
            bases.append(d)

    for d in dirs_from_command(command, cwd)[:NAMED_MAX_FOLDERS]:
        add(d)
    for _ in range(2):  # again, for one relative to a folder found later
        before = len(bases)
        for w in words:
            for p in _windows_paths(w) if os.name == "nt" else [w]:
                p = _without_slash(p)
                if re.split(r"[/\\]", p)[-1] == ".git":
                    p = _without_slash(p[:-4]) or "."
                whole = os.path.isabs(os.path.expanduser(p))
                for base in bases[:1] if whole else bases[:16]:
                    add(_abs(base, p))
                    if len(bases) >= NAMED_MAX_FOLDERS or time.monotonic() > deadline:
                        return bases
        if len(bases) == before:
            break
    return bases


def _same_folder(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def _joined(command):
    return re.sub(r"\\\r?\n", "", command[:100_000])


def _names_a_folder(command):
    return isinstance(command, str) and bool(_NAMED_FOLDER_RE.search(_joined(command)))


def named_repos(command, cwd, known=None):
    """Yields the repositories of folders the command names, `cwd`'s included
    and `known` not, as _git_toplevel gives them. Those the hooks stay out of
    are not among them."""
    if not isinstance(command, str) or not cwd:
        return
    deadline = time.monotonic() + NAMED_BUDGET_S
    command = _joined(command)
    words = _named_words(command, deadline)
    if not words:
        return
    seen, entries, tries = [known] if known else [], set(), {}
    try:
        if known:
            entries.add(_folder_with_git_entry(known))
        # The last first: of several commits the one printed last is looked for.
        for d in reversed(_named_folders(command, cwd, words, deadline)):
            entry = _folder_with_git_entry(d)
            if entry is None or entry in entries:
                continue
            tries[entry] = tries.get(entry, 0) + 1
            if len(tries) > NAMED_MAX_REPOS or time.monotonic() > deadline:
                return
            if tries[entry] > 3:
                continue
            top = _git_toplevel(d)
            if not top:
                continue  # inside its .git, say: another folder may do
            entries.add(entry)
            if not any(_same_folder(top, s) for s in seen):
                seen.append(top)
                yield top
    except (OSError, ValueError):
        return


def commits_made_since(repo, since, max_n=10):
    """{commit: time} for the commits `repo`'s HEAD reflog records from `since`
    (epoch seconds) on, newest first. The time is the record's: a rebase or a pull records
    commits made long before."""
    try:
        r = subprocess.run(
            [*GIT_CMD, "log", "-g", "-n", str(max_n), "--date=unix", "--format=%H|%gd|%gs", "HEAD", "--"],
            # A record can name a commit that a partial clone left out.
            cwd=repo, capture_output=True, timeout=5, env=no_download_env(),
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        return {}
    if r.returncode != 0:
        return {}
    out = {}
    for line in r.stdout.decode("utf-8", errors="replace").split("\n"):
        m = re.match(r"([0-9a-f]{40,64})\|[^|]*@\{(\d+)\}\|commit", line)
        if m and int(m.group(2)) >= since:
            out.setdefault(m.group(1), int(m.group(2)))
    return out


def named_repo_with_new_commit(command, cwd, known, sha, since):
    """The repository the command names where the printed commit `sha` was
    made since `since`, if the first choice does not have it."""
    if not _names_a_folder(command) or has_commit(known, sha):
        return None
    return next((top for top in named_repos(command, cwd, known)
                 if any(c.startswith(sha) for c in commits_made_since(top, since, 300))), None)


def has_commit(repo, sha):
    """True iff `repo` has the commit, without downloading anything."""
    if not repo or not isinstance(sha, str) or not _SHA_RE.match(sha):
        return False
    try:
        return subprocess.run(
            # Unlike cat-file, this never downloads what a partial clone left
            # out, in any git version.
            [*GIT_CMD, "rev-list", "--missing=allow-any", "--no-walk", "--max-count=1",
             f"{sha}^{{commit}}"],
            cwd=repo, capture_output=True, timeout=3, env=no_download_env(),
        ).returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def scan_roots(cwd):
    roots = []
    for r in (cwd, os.environ.get("CLAUDE_PROJECT_DIR")):
        if r and os.path.isdir(r):
            a = os.path.abspath(r)
            if a not in roots:
                roots.append(a)
    return roots


def iter_git_repos(roots, max_depth=None, max_repos=None, deadline=None):
    max_depth = SCAN_MAX_DEPTH if max_depth is None else max_depth
    max_repos = SCAN_MAX_REPOS if max_repos is None else max_repos
    seen = set()
    for root in roots or []:
        try:
            if not root or not os.path.isdir(root):
                continue
            root = os.path.abspath(root)
        except OSError:
            continue
        base_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if deadline is not None and time.monotonic() > deadline:
                return
            if ".git" in dirnames or ".git" in filenames:
                try:
                    key = os.path.realpath(dirpath)
                except OSError:
                    key = dirpath
                if key not in seen:
                    seen.add(key)
                    yield dirpath
                    if len(seen) >= max_repos:
                        return
            depth = dirpath.rstrip(os.sep).count(os.sep) - base_depth
            if depth >= max_depth:
                dirnames[:] = []
            else:
                dirnames[:] = [
                    d for d in dirnames
                    if d not in SCAN_SKIP_DIRS and not d.startswith(".")
                ]


def repo_containing_commit(sha, roots, budget_s=None):
    if not isinstance(sha, str) or not _SHA_RE.match(sha):
        return None
    budget_s = SCAN_BUDGET_S if budget_s is None else budget_s
    deadline = time.monotonic() + budget_s
    for repo in iter_git_repos(roots, deadline=deadline):
        if has_commit(repo, sha):
            top = _git_toplevel(repo)
            if top or not _stay_out(repo):
                return top or repo
    return None


def repos_from_paths(paths, cwd=None, limit=200):
    counts = {}
    order = []
    cache = {}
    for p in list(paths or [])[:limit]:
        if not isinstance(p, str) or not p:
            continue
        ap = p if os.path.isabs(p) else _abs(cwd, p)
        if not ap:
            continue
        d = os.path.dirname(ap)
        while d and not os.path.isdir(d):
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
        if not d:
            continue
        if d in cache:
            top = cache[d]
        else:
            try:
                top = _git_toplevel(d) if os.path.isdir(d) else None
            except OSError:
                top = None
            cache[d] = top
        if top:
            if top not in counts:
                order.append(top)
            counts[top] = counts.get(top, 0) + 1
    return sorted(order, key=lambda t: (-counts[t], order.index(t)))


def save_repo_hint(session_id, repo_root):
    if not session_id or not repo_root:
        return

    def _save(state):
        state["repo_root_hint"] = repo_root
    try:
        with_locked_state(session_id, _save)
    except Exception:
        pass


def load_repo_hint(session_id):
    if not session_id:
        return None
    try:
        hint = with_locked_state(session_id, lambda s: s.get("repo_root_hint"))
    except Exception:
        return None
    if isinstance(hint, str) and hint and os.path.isdir(hint):
        top = _git_toplevel(hint)
        if top:
            return top
    return None


_UNSET = object()


def resolve_repo_root(cwd, command=None, subcommands=None, sha=None,
                      touched_paths=None, session_id=None, cwd_root=_UNSET):
    if cwd_root is _UNSET:
        cwd_root = _git_toplevel(cwd) if cwd else None
    if command:
        top = toplevel_from_command(command, cwd, subcommands, cwd_root)
        if top and top != cwd_root:
            return top, RES_COMMAND
        if not top and command_in_left_out_repo(command, cwd, subcommands):
            # What it printed can still name a commit of another one.
            top = repo_containing_commit(sha, scan_roots(cwd_root or cwd)) if sha else None
            return (top, RES_SHA_SCAN) if top else (None, RES_NONE)
    if cwd_root:
        return cwd_root, RES_CWD
    if touched_paths:
        tops = repos_from_paths(touched_paths, cwd)
        if tops:
            return tops[0], RES_TOUCHED_PATHS
    if sha:
        top = repo_containing_commit(sha, scan_roots(cwd))
        if top:
            return top, RES_SHA_SCAN
    hint = load_repo_hint(session_id)
    if hint:
        return hint, RES_HINT
    return None, RES_NONE
