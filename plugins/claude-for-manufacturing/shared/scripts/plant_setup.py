#!/usr/bin/env python3
"""The plant setup page: the plant profile (## Plant context) kept as a private
page in the user's Claude account, titled "Plant setup: <company>", so a new
Cowork task finds it with no folder and no project.

Three pages, all private. Onboarding writes the first two once; any skill
creates the third on its first write:

  "Plant setup: <company>"  setup/plant-context.txt, the ## Plant context block.
                            No rate values: it can be shared with teammates.
  "Plant rates: <company>"  setup/plant-rates.txt, the ## Plant rates block with
                            the confirmed and placeholder rate values. Its
                            readable view shows each rate's state, never the
                            number. It stays private.
  "Open work: <company>"    setup/open-work.txt (## Dashboards, ## Open
                            inquiries, ## Sourcing events, ## Closed) plus the
                            paused intake forms (inquiries/*.intake.txt) and the
                            bid records (sourcing/<event-id>/*.txt). Holds
                            customer quantities and supplier prices, so its
                            readable view shows references and states only. It
                            stays private.

Each page carries its file byte for byte plus a readable view. Claude publishes
and reads the pages with its artifact tools (Artifact, or mcp__claude-artifacts__*
in Cowork); this script only builds and checks
files, so every skill still reads a real file. `--kind rates` or `--kind work`
selects the other pages; the default is the setup page.

  find    [--company NAME] [--titles <setup page titles from the list call>...]
      Prints {setup_page_first, profile_path, exists, rates_path,
      rates_exists, work_path, work_exists, companies, company, persistent}.
      Every skill runs it before reading the profile, and does the
      setup_page_first step before anything else.
  render  --profile <file> --out <dir>
      Writes <dir>/index.html and <dir>/setup/plant-context.txt. Prints the
      publish arguments: {title, file_path, files, sha256}.
  install --from <file read from the page> [--company NAME]
      Checks the file is a plant profile with no rate values, then copies it
      to profile_path, keeping the old copy in history/ when it differs.
      Prints {profile_path, company, sha256, changed, persistent,
      after_any_change}.
  saved   --from <file read back after publishing> --sha256 <x> --title <t>
      Prints {ok, line}: the saved line only when the read-back matches.
  stamp   --profile <file>
      Sets the Configured date to today after a value is written back.
  put     --block <name> [--entry KEY] (--text-file F | --text T | --remove)
          [--company NAME] [--by SKILL]
      Open work only: replaces one block, or one entry in it (a "### KEY"
      section or a "- KEY" line), in the working copy at work_path, creating
      it for --company when there is none. Every other byte stays as it was.
  prune   [--days 90]
      Open work only: drops ## Closed lines older than N days and their files.
  migrate --from <file holding older blocks> --company NAME
      Lifts ## Dashboards, ## Open inquiries and ## Sourcing events verbatim
      into the Open work working copy and copies any rfq/...intake.yaml they
      name into inquiries/. Never edits or deletes the source.

For --kind work, render takes --profile <work_path>, install takes --from <the
folder the page's files were saved to>, and saved takes --from <the folder
read back> --rendered <render's --out folder>.

`--selftest` runs the checks at the bottom.
"""

import argparse
import datetime
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile

TOOLS = "the artifact tools (Artifact, or mcp__claude-artifacts__* in Cowork)"
LOCAL_DIR = "plant-setup"
KINDS = {
    "setup": {"prefix": "Plant setup: ", "heading": "Plant context",
              "data": "setup/plant-context.txt", "old": "setup/plant-context.md",
              "name": "plant-context.md",
              "noun": "plant setup page"},
    "rates": {"prefix": "Plant rates: ", "heading": "Plant rates",
              "data": "setup/plant-rates.txt", "old": "setup/plant-rates.md",
              "name": "plant-rates.md",
              "noun": "plant rates page"},
    "work": {"prefix": "Open work: ", "heading": "Open work",
             "data": "setup/open-work.txt", "old": None,
             "name": "open-work.md",
             "noun": "Open work page", "dirs": ["inquiries", "sourcing"]},
}
WORK_DIR = "open-work"
WORK_BLOCKS = ("Dashboards", "Open inquiries", "Sourcing events", "Closed")
SIZE_WARN = 1024 * 1024
TITLE_PREFIX = KINDS["setup"]["prefix"]
DATA_PATH = KINDS["setup"]["data"]
PROFILE_NAME = KINDS["setup"]["name"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
RESULT_LAST = ("If this run also publishes its own result (a dashboard, register or report "
               "page), save this page first and publish the result last; if the result had to "
               "come first, finish by opening the result (action open with its url) and end the "
               "reply with its link, so the person sees the result, not this page.")
NOT_SAVED_LINE = ("Not saved to your %s: the copy read back did not match. "
                  "The page is unchanged; ask me to save it again.")


def _block_re(kind):
    return re.compile(r"^##\s*%s\s*$(.*?)(?=^##\s(?!#)|\Z)" % KINDS[kind]["heading"], re.M | re.S)


BLOCK_RE = _block_re("setup")
RATES_RE = re.compile(r"^###\s*Commercial rates\s*$(.*?)(?=^#{2,3}\s|\Z)", re.M | re.S)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


class SetupError(Exception):
    pass


def _sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _field(block, label):
    m = re.search(r"\*\*%s:\*\*[ \t]*(.+)" % re.escape(label), block)
    return m.group(1).strip() if m else None


def title_for(company, kind="setup"):
    return KINDS[kind]["prefix"] + (company or "unnamed plant")


def problems(text, kind="setup"):
    """Why this text cannot be saved as that page: a list of plain sentences,
    empty when it can. Names fields, never values. The setup page holds no
    rate value (those go on the rates page); neither holds an email address."""
    out = []
    if kind == "setup":
        # every line under Commercial rates, and under a Plant rates block kept in the same file
        secs = [m.group(1) for m in (RATES_RE.search(text), _block_re("rates").search(text)) if m]
        for line in "\n".join(secs).splitlines():
            m = re.match(r"^\s*-\s*\*\*(.+?):\*\*\s*(.*)$", line)
            if not m:
                why = ("a rate value sits outside a rate line (a sub-bullet, a table or a paragraph); "
                       "rate values go on the rates page")
                if not line.lstrip().startswith("#") and _no_values(line) != line and why not in out:
                    out.append(why)
                continue
            rest = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", m.group(2))   # dates
            rest = re.sub(r"\bMFG_\w+", "", rest)                      # variable names
            why = ("the %s line holds a rate value; rate values go on the "
                   "rates page, and the setup records the state only" % m.group(1))
            if re.search(r"\d", rest) and why not in out:
                out.append(why)
    if EMAIL_RE.search(text):
        out.append("it holds an email address; record a role or the name the person gave")
    return out


def read_profile(path, kind="setup"):
    """{company, version, text} for that page's file, or SetupError."""
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise SetupError("the file could not be read (%s)" % e)
    m = _block_re(kind).search(text)
    if not m:
        raise SetupError("the file has no ## %s block" % KINDS[kind]["heading"])
    company = _field(m.group(1), "Company")
    if not company:
        raise SetupError("the file names no company")
    version = _field(m.group(1), "Profile version")
    if kind == "setup" and not version:
        raise SetupError("the profile has no Profile version line")
    if kind == "work":
        version = _field(m.group(1), "Format version")
        if not version:
            raise SetupError("the Open work file has no Format version line")
    return {"company": company, "version": version, "text": text}


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def profile_path(cwd=None, kind="setup"):
    """Where this task's working copy lives: {path, persistent}. Never inside
    the plugin's own folder: run from there, the copy would land in the
    installed plugin (or a git checkout of it), so that is refused."""
    name = KINDS[kind]["name"]
    if kind == "work":
        name = "%s/%s" % (WORK_DIR, name)
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if data and os.path.isdir(data) and os.access(data, os.W_OK):
        return {"path": str(pathlib.Path(data) / name), "persistent": True}
    base = pathlib.Path(cwd or os.getcwd()).resolve()
    if base == PLUGIN_ROOT or PLUGIN_ROOT in base.parents:
        raise SetupError("run this from the task's own folder, not from inside the plugin's "
                         "folder (%s): cd back to the folder the task started in" % PLUGIN_ROOT)
    return {"path": str(base / LOCAL_DIR / name), "persistent": False}


# --- find: the step every skill runs first -----------------------------------

def setup_page_step(company=None):
    script = pathlib.Path(__file__).resolve()
    name = company or "<company>"
    return ("Required before reading the plant profile or any rate, once per conversation, even "
            "when profile_path does not exist yet: if you have %s, list the user's artifacts "
            "(scope all) and look for '%s' and '%s'. If more than one 'Plant setup:' page exists "
            "and the user has not named the company, ask which plant before reading any page "
            "(run find again with --titles and the titles listed; companies names them). For each "
            "page found, read its file with those tools (action read, path %s or %s; an older page "
            "has %s or %s instead; never retype it), then run: python3 \"%s\" install "
            "--from <the saved file> --company \"<company>\" (add --kind rates for the rates "
            "file), and read profile_path and rates_path. If this skill reads or writes "
            "## Dashboards, ## Open inquiries or ## Sourcing events, also look for '%s': read %s "
            "and then every file it names and every file the page lists (action read with paths, or "
            "one read per file) into one folder, keeping the page's paths, and run install --kind "
            "work --from <that folder> --company \"<company>\"; the blocks are then at work_path. "
            "Not found, no artifact tools, or a call refused: read the paths as printed and say "
            "nothing about a page. Never show a rate value from rates_path outside an internal "
            "artifact."
            % (TOOLS, title_for(name), title_for(name, "rates"), KINDS["setup"]["data"],
               KINDS["rates"]["data"], KINDS["setup"]["old"], KINDS["rates"]["old"], script,
               title_for(name, "work"), KINDS["work"]["data"]))


def companies_from(titles):
    """The companies named by 'Plant setup: <company>' titles, in order, once each."""
    out = []
    for t in titles or []:
        t = (t or "").strip()
        if t.startswith(TITLE_PREFIX):
            c = t[len(TITLE_PREFIX):].strip()
            if c and c not in out:
                out.append(c)
    return out


def find(company=None, cwd=None, titles=None):
    loc = profile_path(cwd)   # SetupError when run from inside the plugin's folder
    rates = profile_path(cwd, "rates")["path"]
    work = profile_path(cwd, "work")["path"]
    out = {"setup_page_first": setup_page_step(company), "profile_path": loc["path"],
           "exists": os.path.isfile(loc["path"]), "rates_path": rates,
           "rates_exists": os.path.isfile(rates), "work_path": work,
           "work_exists": os.path.isfile(work), "companies": companies_from(titles),
           "company": None, "persistent": loc["persistent"]}
    if len(out["companies"]) > 1 and not company:
        out["ask_which_plant"] = ("More than one plant has a setup page (%s). Ask which plant "
                                  "before reading any page." % ", ".join(out["companies"]))
    if out["exists"]:
        try:
            out["company"] = read_profile(loc["path"])["company"]
        except SetupError as e:
            out["error"] = str(e)
    return out


# --- render: the page and its file -------------------------------------------

def _inline(text):
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", out)


def state_only(item):
    """A rate line as its state and who gave it, without the number:
    'Labor rate: confirmed 71.00/hr - given by Pat Doyle' -> 'Labor rate: confirmed - given by Pat Doyle'."""
    m = re.match(r"^(\*\*.+?:\*\*)\s*(.*)$", item)
    if not m:
        return _no_values(item)
    head, sep, tail = m.group(2).partition(" - ")
    tail = _no_values(tail)
    if not re.search(r"\d", re.sub(r"\bMFG_\w+", "", head)):
        return "%s %s%s%s" % (m.group(1), head, sep, tail)
    state = next((w for w in head.split() if not re.search(r"\d", w)), "set")
    return "%s %s%s" % (m.group(1), state, (" - " + tail) if tail else "")


def _no_values(text):
    """Text on the rates view with its numbers hidden. Dates, MFG_ names and
    numbers inside a reference (FY25, PN-4471) stay. A word or reference is
    matched whole first, so both ends of a range (30-45%) and a bare decimal
    (.28) are hidden while PN-4471 is not."""
    return re.sub(r"\d{4}-\d{2}-\d{2}|[A-Za-z]\w*(?:-\w+)*"
                  r"|(?<![\w.])[$€£]?\d+(?:,\d{3})*(?:\.\d+)?%?(?:/\w+)?|(?<!\w)[$€£]?\.\d+%?(?:/\w+)?",
                  lambda m: m.group(0) if m.group(0)[0].isalpha() or m.group(0)[4:5] == "-" else "[on file]", text)


def details_html(block, hide_values=False):
    """A block as panels: a ### heading starts a panel, bullets become a
    list, pipe tables become tables. hide_values shows rate lines as their
    state only."""
    out, in_list, in_table, open_panel = [], False, False, False

    def close():
        nonlocal in_list, in_table
        if in_list:
            out.append("</ul>")
            in_list = False
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    for line in block.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("### "):
            close()
            if open_panel:
                out.append("</section>")
            out.append('<section class="panel"><h2>%s</h2>' % html.escape(s[4:]))
            open_panel = True
            continue
        if not open_panel:
            out.append('<section class="panel"><h2>Plant</h2>')
            open_panel = True
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            if not in_table:
                close()
                out.append("<table><tbody>")
                in_table = True
            out.append("<tr>%s</tr>" % "".join(
                "<td>%s</td>" % _inline(_no_values(c) if hide_values else c) for c in cells))
            continue
        if s.startswith("- "):
            if not in_list:
                close()
                out.append("<ul>")
                in_list = True
            out.append("<li>%s</li>" % _inline(state_only(s[2:]) if hide_values else s[2:]))
            continue
        if out and out[-1].startswith("<p>") and not in_list and not in_table:
            out[-1] = out[-1][:-4] + " " + _inline(_no_values(s) if hide_values else s) + "</p>"   # a wrapped paragraph stays one
            continue
        close()
        out.append("<p>%s</p>" % _inline(_no_values(s) if hide_values else s))
    close()
    if open_panel:
        out.append("</section>")
    return "\n".join(out)


PAGE = """<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* One column of panels, a record the plant reads, not a dashboard. */
:root {{ --bg:#f7f8f6; --panel:#ffffff; --fg:#1c211e; --muted:#5f6862; --line:#dde2dd; --accent:#2f6b4f; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#161a18; --panel:#1e2421; --fg:#e6ebe7; --muted:#9aa59e; --line:#323a35; --accent:#7cc3a0;
  color-scheme:dark; }} }}
:root[data-theme="dark"] {{ --bg:#161a18; --panel:#1e2421; --fg:#e6ebe7; --muted:#9aa59e; --line:#323a35;
  --accent:#7cc3a0; color-scheme:dark; }}
body {{ background:var(--bg); color:var(--fg); margin:0; padding-block:32px;
  padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px));
  font:15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width:860px; margin:0 auto; display:flex; flex-direction:column; gap:16px; }}
h1 {{ font-size:24px; margin:0; text-wrap:balance; }}
.sub {{ color:var(--muted); margin:0 0 8px; max-width:65ch; }}
.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:6px;
  padding:16px 20px; overflow-wrap:anywhere; min-width:0; }}
h2 {{ font-size:13px; letter-spacing:.06em; text-transform:uppercase; color:var(--accent); margin:0 0 8px; }}
ul {{ margin:4px 0; padding-left:20px; }}
li, p {{ margin:2px 0; }}
table {{ border-collapse:collapse; width:100%; display:block; overflow-x:auto;
  font-variant-numeric:tabular-nums; }}
td, th {{ border-top:1px solid var(--line); padding:4px 8px; vertical-align:top; text-align:left; }}
th {{ font-size:12px; color:var(--muted); font-weight:600; }}
.stale {{ color:var(--accent); }}
code {{ font-size:13px; }}
</style>
<main>
<h1>{company}</h1>
<p class="sub">{lede} {when} To change it, ask Claude;
edits made on this page are not read.</p>
{body}
</main>
"""


LEDES = {
    "setup": "The plant setup Claude reads at the start of every manufacturing task. "
             "Rate values are not kept here.",
    "rates": "The plant's commercial rates, read by Claude for internal costing only. Each "
             "rate shows its state here; the numbers are never shown on this page. Keep this "
             "page private.",
}


def render(profile, out, kind="setup"):
    if kind == "work":
        return render_work(profile, out)
    p = read_profile(profile, kind)
    bad = problems(p["text"], kind)
    if bad:
        raise SetupError("not saved: " + "; ".join(bad))
    block = _block_re(kind).search(p["text"]).group(1)
    data = KINDS[kind]["data"]
    out = pathlib.Path(out)
    (out / "setup").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(profile, out / data)
    title = title_for(p["company"], kind)
    page = PAGE.format(title=html.escape(title), company=html.escape(title),
                       lede=LEDES[kind],
                       when="Configured %s." % html.escape(_field(block, "Configured") or "date not recorded"),
                       body=details_html(block, hide_values=(kind == "rates")))
    (out / "index.html").write_text(page, encoding="utf-8")
    return {"title": title, "file_path": str(out / "index.html"),
            "files": {data: str(out / data)},
            "sha256": _sha(out / data)}


# --- install: the page's copy into this task ----------------------------------

def _keep_history(dest):
    hist = dest.parent / "history"
    hist.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    kept = hist / ("%s-%s.md" % (dest.stem, stamp))
    shutil.copyfile(dest, kept)
    return kept


def install(src, company=None, cwd=None, kind="setup"):
    if kind == "work":
        return install_work(src, company, cwd)
    p = read_profile(src, kind)
    bad = problems(p["text"], kind)
    if bad:
        raise SetupError("not installed: " + "; ".join(bad))
    if company and _slug(company) != _slug(p["company"]):
        raise SetupError("the page holds %s's setup, not %s's" % (p["company"], company))
    loc = profile_path(cwd, kind)
    dest = pathlib.Path(loc["path"])
    changed = not dest.is_file() or _sha(dest) != _sha(src)
    if changed:
        if dest.is_file():
            _keep_history(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(dest.parent))
        os.close(fd)
        shutil.copyfile(src, tmp)
        os.replace(tmp, dest)
    if _sha(dest) != _sha(src):
        raise SetupError("the copy in this task does not match the page")
    return {"profile_path": str(dest), "company": p["company"], "sha256": _sha(dest),
            "changed": changed, "persistent": loc["persistent"]}


def after_any_change(kind="setup"):
    script = pathlib.Path(__file__).resolve()
    if kind == "work":
        return ("This tree came from the Open work page. Whenever a block changes later in this "
                "conversation, change it only with python3 \"{script}\" put (one block, or one "
                "entry, at a time; never edit another block), then save the page in the same turn, "
                "without asking: run prune, then render --kind work --profile <work_path> --out <a "
                "new empty folder>; read the page itself with {tools}, action read and url only, "
                "immediately before the publish; publish to this page's url with the file_path and "
                "files render printed (a refusal saying the content leaves out the live page's text "
                "is answered by publishing the same files once more). If the publish is refused "
                "because a newer version exists: read that version's files into a new folder, run "
                "install --kind work --from it, run this run's same put commands again, render and "
                "publish again. Never force. After two such refusals, stop and print the block, "
                "marked not saved, with the reason. Then read every file back from the page (action "
                "read with paths, or one read per file) into a new folder and run saved --kind work "
                "--from <that folder> --rendered <render's out folder> --title <render's title>, and "
                "show its line word for word. {last}").format(script=script, tools=TOOLS, last=RESULT_LAST)
    path_word = "profile_path" if kind == "setup" else "rates_path"
    kind_flag = " --kind rates" if kind == "rates" else ""
    return ("This file came from the {noun}. Whenever {path_word} is changed later in this "
            "conversation (a value the user confirmed, a reconfigure), update the page as part of "
            "the same save, without asking again: run python3 \"{script}\" stamp --profile "
            "<that path>, then render --profile <that path> --out <a working folder>{kind_flag}; "
            "read the page itself with {tools}, action read and url only (reading the "
            "file does not count), in a step before the publish; publish to this page's url with the "
            "file_path and files render printed (the page is rebuilt from the file on purpose, so "
            "a refusal saying the content leaves out the live page's text is answered by "
            "publishing the same files once more); then read {data} back from the page and run "
            "saved --from <that file> --sha256 <render's sha256> --title <render's title>, and "
            "show its line word for word. {last}").format(last=RESULT_LAST, noun=KINDS[kind]["noun"], path_word=path_word,
                                                   script=script, kind_flag=kind_flag,
                                                   data=KINDS[kind]["data"], tools=TOOLS)


# --- saved and stamp ----------------------------------------------------------

def saved(src, sha256, title, when=None, rendered=None):
    if rendered or (title or "").startswith(KINDS["work"]["prefix"]):
        return saved_work(src, rendered or "", title, when)
    noun = KINDS["rates" if (title or "").startswith(KINDS["rates"]["prefix"]) else "setup"]["noun"]
    if not pathlib.Path(src).is_file() or _sha(src) != sha256:
        return {"ok": False, "line": NOT_SAVED_LINE % noun}
    when = when or datetime.datetime.now().astimezone()
    stamp = "%d %s %d %02d:%02d" % (when.day, MONTHS[when.month - 1], when.year,
                                    when.hour, when.minute)
    return {"ok": True, "line": "Saved to your %s in Claude (%s), %s." % (noun, title, stamp)}


def stamp(profile, when=None):
    """Set the Configured line to today. Only that line changes."""
    path = pathlib.Path(profile)
    text = path.read_text(encoding="utf-8")
    day = (when or datetime.date.today()).isoformat()
    new, n = re.subn(r"^([ \t]*-[ \t]*\*\*Configured:\*\*[ \t]*).*$",   # one line: an empty value stays on its own line
                     lambda m: m.group(1) + ("" if m.group(1)[-1] in " \t" else " ") + day, text, count=1, flags=re.M)
    if n == 0:
        raise SetupError("the profile has no Configured line")
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(new)
    os.replace(tmp, str(path))
    return {"configured": day}


# --- the Open work page: three working blocks plus the files they name --------

FILE_REF_RE = re.compile(r"\b((?:inquiries|sourcing)/[^\s|,;()`]+)")
WORK_RATE_RE = re.compile(r"(?im)^[\s\-*]*(?:\*\*)?\s*(labou?r[ _-]?rate|burden(?:[ _-]?rate)?|"
                          r"margin(?:[ _-]?(?:rate|rules|pct|percent))?)\s*:\s*(?:\*\*)?([^\n]*)$")
CONTACT_LINE_RE = re.compile(r"(?im)^\s*(?:contact\s*:|email\s*:).*$")
MONEY_RE = re.compile(r"(?:[$€£]\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|EUR|GBP|CAD|MXN)\b"
                      r"|\b(?:USD|EUR|GBP|CAD|MXN)\s?\d[\d,]*(?:\.\d+)?)")
ISO_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
LEGACY_INTAKE_RE = re.compile(r"(?<![\w/])(?:file:\s*)?((?:[\w.-]+/)*rfq/[^\s|,;()`]+\.intake\.ya?ml)")


def _work_root(src):
    """(root, index) for an Open work tree: the folder the page's files were
    saved to (index at setup/open-work.txt), or the working copy (open-work.md)."""
    src = pathlib.Path(src)
    if src.is_dir():
        for cand in (src / KINDS["work"]["data"], src / KINDS["work"]["name"]):
            if cand.is_file():
                return src, cand
        raise SetupError("no %s or %s in %s" % (KINDS["work"]["data"], KINDS["work"]["name"], src))
    if src.name == pathlib.Path(KINDS["work"]["data"]).name and src.parent.name == "setup":
        return src.parent.parent, src
    return src.parent, src


def _attached(root):
    """Every file under inquiries/ and sourcing/, as page paths."""
    out = []
    for d in KINDS["work"]["dirs"]:
        base = pathlib.Path(root) / d
        if base.is_dir():
            out += sorted(q.relative_to(root).as_posix() for q in base.rglob("*")
                          if q.is_file() and not q.name.startswith("."))
    return out


def _block(text, name):
    m = re.search(r"^##[ \t]*%s[ \t]*$\n?(.*?)(?=^##\s(?!#)|\Z)" % re.escape(name), text, re.M | re.S)
    return m.group(1) if m else ""


def work_problems(root, index):
    """Why this tree cannot be saved as the Open work page. Names files and
    fields, never values. No labour, burden or margin rate anywhere; no email
    address except an intake form's contact; every file a line names exists;
    every attached file is .txt (Cowork refuses other uploads)."""
    root, out = pathlib.Path(root), []
    files = [(KINDS["work"]["data"], pathlib.Path(index))] + [(r, root / r) for r in _attached(root)]
    for rel, path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            out.append("%s could not be read (%s)" % (rel, e))
            continue
        for m in WORK_RATE_RE.finditer(text):
            rest = re.sub(r"\bMFG_\w+", "", ISO_RE.sub("", m.group(2)))
            if re.search(r"\d", rest):
                out.append("%s holds a %s value; rates belong on the rates page" % (rel, m.group(1)))
        body = CONTACT_LINE_RE.sub("", text) if ".intake." in rel else text
        if EMAIL_RE.search(body):
            out.append("%s holds an email address outside an intake form's contact" % rel)
        if rel != KINDS["work"]["data"] and not rel.endswith(".txt"):
            out.append("%s is not a .txt file; save page files as .txt" % rel)
    index_text = pathlib.Path(index).read_text(encoding="utf-8", errors="replace")
    for rel in sorted(set(FILE_REF_RE.findall(index_text))):
        rel = rel.rstrip(".")
        if not (root / rel).is_file():
            out.append("%s is named in the blocks but is not in the folder" % rel)
    return out


def read_work(src):
    root, index = _work_root(src)
    p = read_profile(index, "work")
    bad = work_problems(root, index)
    if bad:
        raise SetupError("; ".join(bad))
    p.update({"root": root, "index": index, "files": _attached(root)})
    return p


def _tree_shas(root, index):
    out = {KINDS["work"]["data"]: _sha(index)}
    for rel in _attached(root):
        out[rel] = _sha(pathlib.Path(root) / rel)
    return out


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _no_money(s):
    return MONEY_RE.sub("[on file]", s)


def _kv(fields):
    out = {}
    for f in fields:
        k, sep, v = f.partition(":")
        if sep and re.fullmatch(r"[\w ]+", k.strip()):
            out[k.strip().lower().replace(" ", "_")] = v.strip()
    return out


def _days_past(due, today):
    try:
        d = datetime.date.fromisoformat(due)
    except ValueError:
        return None
    return (today - d).days if today > d else None


def _table(head, rows, empty):
    if not rows:
        return "<p>%s</p>" % empty
    th = "".join("<th>%s</th>" % html.escape(h) for h in head)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, body)


def work_view(text, today=None):
    """The readable view: references and states, never a price or a total."""
    today = today or datetime.date.today()
    esc = lambda s: html.escape(_no_money(s or ""), quote=False)
    inq = []
    for line in _block(text, "Open inquiries").splitlines():
        if not line.strip().startswith("- "):
            continue
        f = _cells(line.strip()[2:])
        kv = _kv(f[2:])
        stale_after = kv.get("stale_after", "")
        stale = (stale_after and kv.get("bid_decision_state") != "declined"
                 and _days_past(stale_after, today) is not None)
        inq.append([esc(f[0]), esc(f[1] if len(f) > 1 else ""), esc(kv.get("paused_at_step", "")),
                    esc(kv.get("waiting_on", "")),
                    esc(stale_after) + (' <strong class="stale">stale</strong>' if stale else "")])
    src, event, desc, status, head = [], None, "", "", []
    for line in _block(text, "Sourcing events").splitlines():
        s = line.strip()
        if s.startswith("### "):
            event, _, desc = s[4:].partition(" — ")
            if not desc:
                event, _, desc = s[4:].partition(" - ")
            status, head = "", []
            continue
        if event and not s.startswith("|") and "Status:" in s:
            status = _kv(_cells(s)).get("status", "")
            continue
        if event and s.startswith("|"):
            cells = _cells(s)
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            if not head:
                head = [c.lower() for c in cells]
                continue
            row = dict(zip(head, cells))
            resp = row.get("response", "").strip()
            state = ("no response" if resp.lower() in ("", "-", "none") or resp.lower().startswith("no response")
                     else resp.split()[0].rstrip(","))
            due = row.get("due", "")
            late = _days_past(due, today) if state == "no response" else None
            src.append([esc(event.strip()), esc(desc.strip()), esc(row.get("supplier", "")),
                        esc(status), esc(due), esc(state), str(late) if late else "-"])
    dash = []
    for line in _block(text, "Dashboards").splitlines():
        m = re.match(r"^\s*-\s*(.*?)\s*[—:-]*\s*(https?://\S+)", line)
        if m:
            dash.append([esc(m.group(1).rstrip(" —-:")),
                         '<a href="%s">%s</a>' % (html.escape(m.group(2)), html.escape(m.group(2)))])
    closed = sum(1 for l in _block(text, "Closed").splitlines() if l.strip().startswith("- "))
    return "\n".join([
        '<section class="panel"><h2>Open inquiries</h2>%s</section>' % _table(
            ["Reference", "Customer", "Paused at step", "Waiting on", "Stale after"], inq, "None open."),
        '<section class="panel"><h2>Sourcing events</h2>%s</section>' % _table(
            ["Event", "Part", "Supplier", "Status", "Due", "Response", "Days past due"], src, "None open."),
        '<section class="panel"><h2>Dashboards</h2>%s</section>' % _table(["Title", "Link"], dash, "None saved."),
        '<section class="panel"><h2>Closed</h2><p>%d closed item%s kept for 90 days.</p></section>'
        % (closed, "" if closed == 1 else "s")])


def render_work(profile, out, today=None):
    w = read_work(profile)
    out = pathlib.Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for rel, path in [(KINDS["work"]["data"], w["index"])] + [(r, w["root"] / r) for r in w["files"]]:
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        files[rel] = str(dest)
    title = title_for(w["company"], "work")
    block = _block_re("work").search(w["text"]).group(1)
    page = PAGE.format(title=html.escape(title), company=html.escape(title),
                       lede="Private working record for %s. Holds customer and supplier pricing. "
                            "Don't share. The prices stay in the files; this view shows references "
                            "and states only." % html.escape(w["company"]),
                       when="Last written %s." % html.escape(_field(block, "Last written") or "date not recorded"),
                       body=work_view(w["text"], today))
    (out / "index.html").write_text(page, encoding="utf-8")
    shas = {rel: _sha(p) for rel, p in files.items()}
    (out / ".manifest.json").write_text(json.dumps(shas, indent=1), encoding="utf-8")
    res = {"title": title, "file_path": str(out / "index.html"), "files": files,
           "sha256": shas[KINDS["work"]["data"]], "rendered": str(out)}
    if pathlib.Path(w["index"]).stat().st_size > SIZE_WARN:
        res["warning"] = ("The Open work index is over 1 MB. Suggest closing old sourcing events "
                          "and inquiries.")
    return res


def install_work(src, company=None, cwd=None):
    w = read_work(src)
    if company and _slug(company) != _slug(w["company"]):
        raise SetupError("the page holds %s's open work, not %s's" % (w["company"], company))
    loc = profile_path(cwd, "work")
    dest_index = pathlib.Path(loc["path"])
    dest = dest_index.parent
    new = _tree_shas(w["root"], w["index"])
    old = _tree_shas(dest, dest_index) if dest_index.is_file() else None
    changed = new != old
    if changed:
        dest.mkdir(parents=True, exist_ok=True)
        if old is not None:
            hist = dest / "history" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            hist.mkdir(parents=True)
            for name in [KINDS["work"]["name"]] + KINDS["work"]["dirs"]:
                if (dest / name).exists():
                    shutil.move(str(dest / name), str(hist / name))
        tmp = pathlib.Path(tempfile.mkdtemp(prefix=".tmp-", dir=str(dest)))
        shutil.copyfile(w["index"], tmp / KINDS["work"]["name"])
        for rel in w["files"]:
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(w["root"] / rel, tmp / rel)
        for name in [KINDS["work"]["name"]] + KINDS["work"]["dirs"]:
            if (tmp / name).exists():
                os.replace(str(tmp / name), str(dest / name))
        shutil.rmtree(tmp, ignore_errors=True)
    if _tree_shas(dest, dest_index) != new:
        raise SetupError("the copy in this task does not match the page")
    return {"work_path": str(dest_index), "company": w["company"], "sha256": new[KINDS["work"]["data"]],
            "files": w["files"], "changed": changed, "persistent": loc["persistent"]}


def saved_work(src, rendered, title, when=None):
    """ok only when the index and every attached file read back match render."""
    try:
        want = json.loads((pathlib.Path(rendered) / ".manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"ok": False, "line": "Not saved to your Open work page: render's record of the "
                                     "files was not found, so the read-back could not be checked."}
    bad = [rel for rel, sha in sorted(want.items())
           if not (pathlib.Path(src) / rel).is_file() or _sha(pathlib.Path(src) / rel) != sha]
    if bad:
        return {"ok": False, "line": "Not saved to your Open work page: %s did not read back the "
                                     "same. Ask me to save it again." % ", ".join(bad), "differs": bad}
    when = when or datetime.datetime.now().astimezone()
    stamp_ = "%d %s %d %02d:%02d" % (when.day, MONTHS[when.month - 1], when.year, when.hour, when.minute)
    return {"ok": True, "line": "Saved to your Open work page in Claude (%s), %s." % (title, stamp_)}


def _new_work(company, when):
    return ("## Open work\n\n- **Company:** %s\n- **Format version:** 1\n- **Last written:** %s\n\n"
            "## Dashboards\n\n## Open inquiries\n\n## Sourcing events\n\n## Closed\n"
            % (company, when))


def _write(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, str(path))


def put_block(doc, block, text=None, entry=None, remove=False):
    """doc with one block, or one entry in it, replaced. Nothing else changes."""
    if block not in WORK_BLOCKS:
        raise SetupError("no block named %s; the blocks are %s" % (block, ", ".join(WORK_BLOCKS)))
    m = re.search(r"^##[ \t]*%s[ \t]*$\n?(.*?)(?=^##\s(?!#)|\Z)" % re.escape(block), doc, re.M | re.S)
    if not m:
        doc = doc.rstrip("\n") + "\n\n## %s\n\n" % block
        m = re.search(r"^##[ \t]*%s[ \t]*$\n?(.*?)(?=^##\s(?!#)|\Z)" % re.escape(block), doc, re.M | re.S)
    body = m.group(1)
    new = (text or "").strip("\n")
    if entry is None:
        nb = "" if remove else "\n" + new + "\n"
    else:
        sec = re.search(r"^###\s*%s(?=\s|$).*?(?=^###\s|\Z)" % re.escape(entry), body, re.M | re.S)
        line = re.search(r"^\s*-\s*%s(?=\s|\||$).*\n?" % re.escape(entry), body, re.M)
        hit = sec or line
        if hit:
            rep = "" if remove else new + ("\n\n" if sec else "\n")
            nb = body[:hit.start()] + rep + body[hit.end():]
        elif remove:
            nb = body
        else:
            nb = body.rstrip("\n") + ("\n" if body.strip() else "\n") + new + "\n"
    if nb.strip():
        nb = "\n" + nb.strip("\n") + "\n\n"
    else:
        nb = "\n"
    if m.end() == len(doc):
        nb = nb.rstrip("\n") + "\n"
    return doc[:m.start(1)] + nb + doc[m.end():]


def put(block, text=None, entry=None, remove=False, company=None, by=None, cwd=None, when=None):
    loc = profile_path(cwd, "work")
    idx = pathlib.Path(loc["path"])
    when = (when or datetime.datetime.now().astimezone()).strftime("%Y-%m-%dT%H:%M%z")
    created = not idx.is_file()
    if created:
        if not company:
            raise SetupError("there is no Open work page yet: name the company it is for "
                             "(--company), never 'unnamed plant'")
        doc = _new_work(company, when)
    else:
        doc = idx.read_text(encoding="utf-8")
        have = read_profile(idx, "work")["company"]
        if company and _slug(company) != _slug(have):
            raise SetupError("the Open work copy here is %s's, not %s's" % (have, company))
    new = put_block(doc, block, text, entry, remove)
    new = re.sub(r"^(\s*-\s*\*\*Last written:\*\*\s*).*$",
                 lambda m: m.group(1) + when + (" by %s" % by if by else ""), new, count=1, flags=re.M)
    changed = new != doc or created
    if changed:
        _write(idx, new)
    return {"work_path": str(idx), "block": block, "entry": entry, "created": created,
            "changed": changed, "persistent": loc["persistent"]}


def _plain_name(ref):
    """True for one file or folder name; a path could reach outside its folder."""
    return ref not in ("", ".", "..") and not re.search(r"[/\\:\x00]", ref)


def prune(days=90, cwd=None, today=None):
    """Drop ## Closed lines whose close date is more than `days` ago, and
    their files. Moves nothing else."""
    idx = pathlib.Path(profile_path(cwd, "work")["path"])
    if not idx.is_file():
        return {"dropped": [], "files_removed": []}
    today = today or datetime.date.today()
    doc, root = idx.read_text(encoding="utf-8"), idx.parent
    dropped, removed = [], []
    in_use = set(r.rstrip(".") for b in WORK_BLOCKS[:3] for r in FILE_REF_RE.findall(_block(doc, b)))
    for line in _block(doc, "Closed").splitlines():
        s = line.strip()
        dates = ISO_RE.findall(s[2:].partition("|")[2])   # after the reference, which may hold a date itself
        if not s.startswith("- ") or not dates:
            continue
        try:
            age = (today - datetime.date.fromisoformat(dates[0])).days
        except ValueError:
            continue
        if age > days:
            key = _cells(s[2:])[0]
            if not _plain_name(key):
                continue
            dropped.append(key)
            for q in sorted((root / "inquiries").iterdir()) if (root / "inquiries").is_dir() else []:
                rel = q.relative_to(root).as_posix()
                if not re.fullmatch(r"(?:.*-)?%s\.intake\.\w+" % re.escape(key), q.name) or rel in in_use:
                    continue
                q.unlink()
                removed.append(rel)
            ev = root / "sourcing" / key
            if ev.is_dir() and not any(r.startswith("sourcing/%s/" % key) for r in in_use):
                removed += sorted(q.relative_to(root).as_posix() for q in ev.rglob("*") if q.is_file())
                shutil.rmtree(ev)
    for key in dropped:
        doc = put_block(doc, "Closed", entry=key, remove=True)
    if dropped:
        _write(idx, doc)
    return {"dropped": dropped, "files_removed": removed}


def migrate(src, company, cwd=None):
    """Lift older blocks into the Open work working copy. The source
    is only read. Blocks the working copy already holds are kept as they are."""
    if not company:
        raise SetupError("name the company the open work belongs to (--company)")
    src = pathlib.Path(src)
    text = src.read_text(encoding="utf-8")
    loc = profile_path(cwd, "work")
    idx = pathlib.Path(loc["path"])
    root = idx.parent
    when = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M%z")
    doc = idx.read_text(encoding="utf-8") if idx.is_file() else _new_work(company, when)
    moved, kept, missing = [], [], []
    for name in ("Dashboards", "Open inquiries", "Sourcing events"):
        m = re.search(r"^##[ \t]*%s[ \t]*$\n?(.*?)(?=^##\s(?!#)|\Z)" % re.escape(name), text, re.M | re.S)
        if not m or not m.group(1).strip():
            continue
        if _block(doc, name).strip():
            kept.append(name)
            continue
        body = m.group(1)
        if name == "Open inquiries":
            def lift(mm):
                old = mm.group(1)
                for base in (src.parent, pathlib.Path(cwd or os.getcwd())):
                    if (base / old).is_file():
                        stem = pathlib.Path(old).name.rsplit(".intake.", 1)[0]
                        rel = "inquiries/%s.intake.txt" % stem
                        (root / "inquiries").mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(base / old, root / rel)
                        return "file: " + rel
                missing.append(old)
                return "file: missing"
            body = LEGACY_INTAKE_RE.sub(lift, body)

        def gone(mm):   # a page path the old block named that is not here
            if (root / mm.group(1).rstrip(".")).is_file():
                return mm.group(0)
            missing.append(mm.group(1))
            return "missing"
        body = FILE_REF_RE.sub(gone, body)
        doc = put_block(doc, name, body)
        moved.append(name)
    if moved:
        _write(idx, doc)
    return {"work_path": str(idx), "moved": moved, "kept_on_page": kept, "missing_files": missing,
            "source_untouched": str(src)}


# --- selftest -------------------------------------------------------------------

SAMPLE = """## Plant context

- **Profile version:** 2
- **Configured:** 2026-09-08
- **Company:** Example Manufacturing
- **Sites:** Fairview (default) - Brantford
- **Rates:** see Commercial rates - state and source per rate

### Systems

| System | Status |
|---|---|
| Oracle NetSuite | live |

### Commercial rates

- **Labor rate:** set in environment (MFG_LABOR_RATE)
- **Burden rate:** from the ERP - confirmed by the plant controller, 2026-10-02
- **Downtime cost per hour:** not set - see gaps
"""


RATES_SAMPLE = """## Plant rates

- **Company:** Example Manufacturing
- **Configured:** 2026-10-02

### Commercial rates

- **Labor rate:** confirmed 71.00/hr - given by Pat Doyle, 2026-10-02
- **Burden rate:** set in environment (MFG_BURDEN_RATE)
- **Margin rules:** confirmed `{"default":0.32}` - given by Pat Doyle, 2026-10-02
- **Downtime cost per hour:** placeholder 62.00/hr - assumed from the FY25 budget, not confirmed
- **Scrap costing basis:** standard cost from NetSuite
"""


WORK_SOURCING = """### SRC-2026-10-14-PN-4471-B-BO — black oxide, PN-4471-B Rev 2 (Fairview)

Trigger: quote EH-RFQ-0912 line 1 | Breaks: 50, 200 each | Due: 2026-10-28 | Status: open

| Supplier | Approval | Drafted | Sent (per buyer) | Due | Response | Chased |
|---|---|---|---|---|---|---|
| VEND-5120 Example Finishing | approved, single source | 2026-10-14 | 2026-10-14 | 2026-10-28 | bid 2026-10-22, sourcing/SRC-2026-10-14-PN-4471-B-BO/example-finishing.bid.txt | - |
| VEND-5141 Example Coatings | approved | 2026-10-14 | 2026-10-14 | 2026-10-28 | - | - |"""

INTAKE_SAMPLE = """rfq_reference: EH-RFQ-0912
customer: Example Hydraulics
contact: { name: "Ana Ruiz", email: "aruiz@example-hydraulics.example" }
paused_at_step: 5
lines:
  - part: PN-4471-B
    quantities: [50, 200]
"""

BID_SAMPLE = """bid_ref: SRC-2026-10-14-PN-4471-B-BO/example-finishing
supplier_id: VEND-5120
breaks:
  - quantity: 50
    unit_price: 3.10
    currency: USD
  - quantity: 200
    unit_price: 2.20
    currency: USD
tooling_price: 0
"""

LEGACY = """# Workspace notes

## Dashboards

- Fairview: Operations Command Center — https://claude.ai/artifact/abc123

## Open inquiries

- EV-RFQ-0410 | Example Valve | rfq/example-valve-EV-RFQ-0410.intake.yaml | paused_at_step: 5
- EH-RFQ-0001 | Example Hydraulics | rfq/example-hydraulics-EH-RFQ-0001.intake.yaml | paused_at_step: 3

## Sourcing events

""" + WORK_SOURCING + "\n"


def _work_selftest(t):
    """The Open work page: put, render, install, saved, prune, migrate."""
    when = datetime.datetime(2026, 11, 10, 10, 15)
    day = datetime.date(2026, 11, 10)
    wd = t / "work"
    wd.mkdir()
    os.environ.pop("CLAUDE_PLUGIN_DATA", None)
    try:
        put("Open inquiries", "- EH-RFQ-0912 | Example Hydraulics | file: inquiries/example-hydraulics-EH-RFQ-0912.intake.txt "
            "| paused_at_step: 5 | waiting_on: customer answers to Q1-Q3 | stale_after: 2026-11-05 | "
            "bid_decision_state: draft", entry="EH-RFQ-0912", cwd=wd, when=when, company="Example Manufacturing")
    except SetupError:
        raise AssertionError("put refused a first write that named the company")
    try:
        put("Dashboards", "- x", cwd=t / "nowhere-yet", when=when)
        raise AssertionError("put created a page with no company")
    except SetupError as e:
        assert "unnamed plant" in str(e), e
    root = wd / LOCAL_DIR / WORK_DIR
    (root / "inquiries").mkdir()
    (root / "inquiries" / "example-hydraulics-EH-RFQ-0912.intake.txt").write_text(INTAKE_SAMPLE, encoding="utf-8")
    ev = root / "sourcing" / "SRC-2026-10-14-PN-4471-B-BO"
    ev.mkdir(parents=True)
    (ev / "example-finishing.bid.txt").write_text(BID_SAMPLE, encoding="utf-8")
    put("Sourcing events", WORK_SOURCING, entry="SRC-2026-10-14-PN-4471-B-BO", cwd=wd, when=when, by="supplier-quote-request")
    put("Dashboards", "- Fairview: Operations Command Center — https://claude.ai/artifact/abc123", entry="Fairview: Operations Command Center", cwd=wd, when=when)
    put("Closed", "- EH-RFQ-0877 | quoted 2026-07-30 | file kept until 2026-10-28", entry="EH-RFQ-0877", cwd=wd, when=when)
    idx = root / KINDS["work"]["name"]
    f = find(cwd=wd, titles=["Plant setup: Example Manufacturing", "Plant setup: Example Tool", "Plant rates: Example Manufacturing"])
    assert f["work_exists"] and f["work_path"] == str(idx), f
    assert f["companies"] == ["Example Manufacturing", "Example Tool"] and "ask_which_plant" in f, f
    assert "Open work: <company>" in f["setup_page_first"] and "ask which plant" in f["setup_page_first"]
    assert RESULT_LAST in after_any_change("work")

    # only the block being written changes
    doc = idx.read_text(encoding="utf-8")
    keep = {b: _block(doc, b) for b in ("Dashboards", "Open inquiries", "Closed")}
    put("Sourcing events", WORK_SOURCING.replace("Status: open", "Status: decided"),
        entry="SRC-2026-10-14-PN-4471-B-BO", cwd=wd, when=when)
    doc2 = idx.read_text(encoding="utf-8")
    assert "Status: decided" in doc2 and doc2.count("### SRC-") == 1, doc2
    for b, body in keep.items():
        assert _block(doc2, b) == body, b
    put("Sourcing events", WORK_SOURCING, entry="SRC-2026-10-14-PN-4471-B-BO", cwd=wd, when=when)

    # render: every file byte for byte; the view hides every price
    r = render(idx, t / "wpage", "work")
    assert r["title"] == "Open work: Example Manufacturing", r
    assert set(r["files"]) == {"setup/open-work.txt", "inquiries/example-hydraulics-EH-RFQ-0912.intake.txt",
                               "sourcing/SRC-2026-10-14-PN-4471-B-BO/example-finishing.bid.txt"}, r
    view = (t / "wpage" / "index.html").read_text(encoding="utf-8")
    assert not MONEY_RE.search(view) and "3.10" not in view and "2.20" not in view, view
    assert "unit_price: 3.10" in (t / "wpage" / "sourcing/SRC-2026-10-14-PN-4471-B-BO/example-finishing.bid.txt").read_text()
    assert "Don't share" in view and "EH-RFQ-0912" in view and "Example Coatings" in view and "<script" not in view
    assert "aruiz@" not in view
    v2 = work_view(idx.read_text(encoding="utf-8"), day)
    assert 'class="stale">stale' in v2 and ">13<" in v2, v2   # stale after 5 Nov; Example Coatings 13 days past due

    # problems: an email outside the contact, a rate in the index, a missing file, a .yaml file
    bad_idx = t / "bad" / "setup"
    shutil.copytree(t / "wpage", t / "bad")
    (t / "bad" / "inquiries" / "example-hydraulics-EH-RFQ-0912.intake.txt").write_text(
        INTAKE_SAMPLE + "notes: forwarded by ops@example-hydraulics.example\n", encoding="utf-8")
    assert any("email" in x and ".intake." in x for x in work_problems(t / "bad", bad_idx / "open-work.txt"))
    (t / "bad" / "inquiries" / "example-hydraulics-EH-RFQ-0912.intake.txt").write_text(INTAKE_SAMPLE, encoding="utf-8")
    assert work_problems(t / "bad", bad_idx / "open-work.txt") == []
    (bad_idx / "open-work.txt").write_text(doc + "- **Labor rate:** 71.00/hr\n", encoding="utf-8")
    pr = work_problems(t / "bad", bad_idx / "open-work.txt")
    assert pr and "Labor rate" in pr[0] and "71" not in pr[0], pr
    (bad_idx / "open-work.txt").write_text(doc.replace(".intake.txt", ".intake.yaml"), encoding="utf-8")
    assert any("not in the folder" in x for x in work_problems(t / "bad", bad_idx / "open-work.txt"))

    # install from the folder the page was read into, then saved
    i1 = install(t / "wpage", "Example Manufacturing", cwd=t / "other", kind="work")
    assert i1["changed"] and len(i1["files"]) == 2 and i1["work_path"].endswith("plant-setup/open-work/open-work.md"), i1
    assert not install(t / "wpage", cwd=t / "other", kind="work")["changed"]
    try:
        install(t / "wpage", "Example Tool", cwd=t / "other", kind="work")
        raise AssertionError("installed another company's open work")
    except SetupError:
        pass
    ok = saved(t / "wpage", None, r["title"], when, rendered=t / "wpage")
    assert ok["ok"] and ok["line"].startswith("Saved to your Open work page"), ok
    shutil.copytree(t / "wpage", t / "readback")
    (t / "readback" / "sourcing/SRC-2026-10-14-PN-4471-B-BO/example-finishing.bid.txt").write_text(BID_SAMPLE + "#\n")
    nok = saved(t / "readback", None, r["title"], when, rendered=t / "wpage")
    assert not nok["ok"] and "example-finishing.bid.txt" in nok["line"], nok

    # prune: closed lines past 90 days go, with their files; open lines stay
    (root / "inquiries" / "acme-EH-RFQ-0877.intake.txt").write_text(INTAKE_SAMPLE, encoding="utf-8")
    pr = prune(90, cwd=wd, today=day)
    assert pr == {"dropped": ["EH-RFQ-0877"], "files_removed": ["inquiries/acme-EH-RFQ-0877.intake.txt"]}, pr
    after = idx.read_text(encoding="utf-8")
    assert "EH-RFQ-0877" not in after and "EH-RFQ-0912" in after and "SRC-2026-10-14" in after

    # prune takes the reference whole (RFQ-12 is not RFQ-123), leaves a file an open line
    # names, and ages by the close date, not a date inside the reference
    for ref in ("RFQ-12", "RFQ-123"):
        (root / "inquiries" / ("acme-%s.intake.txt" % ref)).write_text(INTAKE_SAMPLE, encoding="utf-8")
    put("Open inquiries", "- RFQ-123 | acme | file: inquiries/acme-RFQ-123.intake.txt | paused_at_step: 2",
        entry="RFQ-123", cwd=wd, when=when)
    put("Closed", "- RFQ-12 | quoted 2026-07-30", entry="RFQ-12", cwd=wd, when=when)
    put("Closed", "- RFQ-123 | withdrawn 2026-07-01, re-opened", entry="RFQ-123", cwd=wd, when=when)
    put("Closed", "- SRC-2026-07-01-PN-1-A | decided and closed 2026-11-01", entry="SRC-2026-07-01-PN-1-A",
        cwd=wd, when=when)
    kept = root / "sourcing" / "SRC-2026-07-01-PN-1-A" / "decision.txt"
    kept.parent.mkdir()
    kept.write_text("decision\n", encoding="utf-8")
    pr = prune(90, cwd=wd, today=day)
    assert pr == {"dropped": ["RFQ-12", "RFQ-123"], "files_removed": ["inquiries/acme-RFQ-12.intake.txt"]}, pr
    assert (root / "inquiries" / "acme-RFQ-123.intake.txt").is_file() and kept.is_file()
    assert "SRC-2026-07-01-PN-1-A" in _block(idx.read_text(encoding="utf-8"), "Closed")
    assert read_work(idx)["files"].count("inquiries/acme-RFQ-123.intake.txt") == 1

    # put: an entry whose reference starts another's is its own section
    d = put_block(_new_work("x", "t"), "Sourcing events", "### SRC-1-B-BO — a\n\nStatus: open", entry="SRC-1-B-BO")
    d = put_block(d, "Sourcing events", "### SRC-1-B — b\n\nStatus: open", entry="SRC-1-B")
    assert "### SRC-1-B-BO — a" in d and "### SRC-1-B — b" in d, d
    d = put_block(d, "Sourcing events", entry="SRC-1-B", remove=True)
    assert "### SRC-1-B-BO — a" in d and "### SRC-1-B —" not in d, d

    # view: "no response" written out is that state, with its days past due
    d = put_block(_new_work("x", "t"), "Sourcing events", "### SRC-1-B — b\n\nStatus: open\n\n| Supplier | Due | Response |\n"
                  "|---|---|---|\n| VEND-1 | 2026-10-28 | No response, chased |", entry="SRC-1-B")
    assert "<td>no response</td><td>13</td>" in work_view(d, day), work_view(d, day)

    # migrate: blocks lifted verbatim, the intake file copied, the source untouched
    mig = t / "mig"
    (mig / "rfq").mkdir(parents=True)
    (mig / "rfq" / "example-valve-EV-RFQ-0410.intake.yaml").write_text(INTAKE_SAMPLE, encoding="utf-8")
    legacy = mig / "CLAUDE.local.md"
    legacy.write_text(LEGACY, encoding="utf-8")
    m = migrate(legacy, "Example Manufacturing", cwd=mig)
    assert m["moved"] == ["Dashboards", "Open inquiries", "Sourcing events"], m
    assert m["missing_files"][0] == "rfq/example-hydraulics-EH-RFQ-0001.intake.yaml", m
    assert legacy.read_text(encoding="utf-8") == LEGACY
    moved = pathlib.Path(m["work_path"]).read_text(encoding="utf-8")
    assert "file: inquiries/example-valve-EV-RFQ-0410.intake.txt" in moved and "| file: missing |" in moved, moved
    assert m["missing_files"][-1].endswith("example-finishing.bid.txt") and "bid 2026-10-22, missing" in moved, m
    assert render(m["work_path"], t / "migpage", "work")["title"] == "Open work: Example Manufacturing"
    assert _block(moved, "Sourcing events").strip() == _block(LEGACY, "Sourcing events").strip().replace(
        "sourcing/SRC-2026-10-14-PN-4471-B-BO/example-finishing.bid.txt", "missing")
    assert (pathlib.Path(m["work_path"]).parent / "inquiries" / "example-valve-EV-RFQ-0410.intake.txt").is_file()


def _selftest():
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t).resolve()   # macOS: /var is /private/var
        prof = t / "in.md"
        prof.write_text(SAMPLE, encoding="utf-8")

        # 1. render: the file is the profile byte for byte; the page reads in plain words
        r = render(prof, t / "page")
        assert r["title"] == "Plant setup: Example Manufacturing", r
        assert r["sha256"] == _sha(prof) and r["files"] == {DATA_PATH: str(t / "page" / DATA_PATH)}, r
        page = (t / "page" / "index.html").read_text(encoding="utf-8")
        assert "<title>Plant setup: Example Manufacturing</title>" in page
        assert "<h2>Commercial rates</h2>" in page and "<td>Oracle NetSuite</td>" in page
        assert "<script" not in page

        # 2. no rate value and no email address is ever saved or installed
        for bad_line, why in (("- **Labor rate:** confirmed 71.00/hr - given by Pat Doyle, 2026-10-02", "Labor rate"),
                              ("- **Burden rate:** placeholder 140% - assumed, not confirmed", "Burden rate"),
                              ("- **Margin rules:** confirmed `{\"default\":0.32}`", "Margin rules")):
            dirty = t / "dirty.md"
            dirty.write_text(SAMPLE.replace("- **Downtime cost per hour:** not set - see gaps", bad_line),
                             encoding="utf-8")
            for fn in (lambda: render(dirty, t / "x"), lambda: install(dirty, cwd=t)):
                try:
                    fn()
                    raise AssertionError("accepted a rate value: " + bad_line)
                except SetupError as e:
                    assert why in str(e) and "71" not in str(e) and "140" not in str(e), e
        mail = t / "mail.md"
        mail.write_text(SAMPLE + "- **Confirmed by:** pat@example-manufacturing.example.com\n", encoding="utf-8")
        assert problems(mail.read_text()) and "email" in problems(mail.read_text())[0]
        # a value outside a rate line (sub-bullet, table row), or in a Plant rates block kept in the same file
        for extra in ("  - prototype: 0.45\n", "\n| prototype | 30-45% |\n", "\n" + RATES_SAMPLE):
            pr = problems(SAMPLE + extra)
            assert pr and "rate value" in pr[0] and not re.search(r"\d", "".join(pr)), (extra, pr)
        assert problems(SAMPLE) == [] and problems(SAMPLE + "\nAssumed from the FY25 budget, 2026-10-02.\n") == []

        # 3. install into the task folder: a new copy, then the same copy again
        old = os.environ.pop("CLAUDE_PLUGIN_DATA", None)
        try:
            f0 = find(cwd=t)
            assert not f0["exists"] and f0["setup_page_first"].startswith("Required before"), f0
            i1 = install(t / "page" / DATA_PATH, cwd=t)
            assert i1["changed"] and i1["company"] == "Example Manufacturing" and not i1["persistent"], i1
            assert i1["profile_path"] == str(t / LOCAL_DIR / PROFILE_NAME)
            i2 = install(t / "page" / DATA_PATH, cwd=t)
            assert not i2["changed"] and not (t / LOCAL_DIR / "history").exists(), i2
            assert find(cwd=t)["company"] == "Example Manufacturing"

            # 4. a page that differs: the page wins, the old copy goes to history
            newer = t / "newer.md"
            newer.write_text(SAMPLE.replace("2026-09-08", "2026-11-05"), encoding="utf-8")
            i3 = install(newer, cwd=t)
            assert i3["changed"] and len(list((t / LOCAL_DIR / "history").iterdir())) == 1, i3

            # 5. refusals: another company's page, a file that is not a profile
            for bad, kw in ((newer, {"company": "Other Co"}), (t / "page" / "index.html", {})):
                try:
                    install(bad, cwd=t, **kw)
                    raise AssertionError("install accepted %s" % bad)
                except SetupError:
                    pass

            # 6. the plugin data folder wins when it is set and writable
            data = t / "data"
            data.mkdir()
            os.environ["CLAUDE_PLUGIN_DATA"] = str(data)
            i4 = install(newer, cwd=t)
            assert i4["persistent"] and i4["profile_path"] == str(data / PROFILE_NAME), i4
        finally:
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            if old is not None:
                os.environ["CLAUDE_PLUGIN_DATA"] = old

        # 6b. never a working copy inside the plugin's own folder
        os.environ.pop("CLAUDE_PLUGIN_DATA", None)
        for inside in (PLUGIN_ROOT, PLUGIN_ROOT / "shared" / "scripts"):
            try:
                find(cwd=inside)
                raise AssertionError("find accepted the plugin folder %s" % inside)
            except SetupError as e:
                assert "task's own folder" in str(e), e
        if old is not None:
            os.environ["CLAUDE_PLUGIN_DATA"] = old

        # 6c. the after-change steps name the right page, path and file for each kind
        for kind, words in (("setup", ("plant setup page", "profile_path", "setup/plant-context.txt", "mcp__claude-artifacts__")),
                            ("rates", ("plant rates page", "rates_path", "--kind rates", "setup/plant-rates.txt"))):
            text = after_any_change(kind)
            assert all(w in text for w in words) and str(pathlib.Path(__file__).resolve()) in text, (kind, text)
            assert RESULT_LAST in text, kind
        here = os.getcwd()
        os.chdir(t)
        try:
            assert "CLAUDE_PLUGIN_DATA" not in os.environ   # main() set it aside: nothing here writes outside t
            assert main(["install", "--from", str(t / "page" / DATA_PATH), "--company", "Example Manufacturing"]) == 0
        finally:
            os.chdir(here)

        # 7. stamp changes the Configured line and nothing else
        s = t / "stamp.md"
        s.write_text(SAMPLE, encoding="utf-8")
        assert stamp(s, datetime.date(2026, 11, 5)) == {"configured": "2026-11-05"}
        assert s.read_text(encoding="utf-8") == SAMPLE.replace("Configured:** 2026-09-08", "Configured:** 2026-11-05")
        # an empty value stays on its own line: the next line is neither read as it nor overwritten
        s.write_text(SAMPLE.replace("Configured:** 2026-09-08", "Configured:**"), encoding="utf-8")
        assert _field(s.read_text(encoding="utf-8"), "Configured") is None
        stamp(s, datetime.date(2026, 11, 5))
        assert s.read_text(encoding="utf-8") == SAMPLE.replace("Configured:** 2026-09-08", "Configured:** 2026-11-05")

        # 8. the saved line only for a read-back that matches
        when = datetime.datetime(2026, 11, 5, 14, 5)
        ok = saved(t / "page" / DATA_PATH, r["sha256"], r["title"], when)
        assert ok == {"ok": True, "line": "Saved to your plant setup page in Claude "
                      "(Plant setup: Example Manufacturing), 5 Nov 2026 14:05."}, ok
        assert saved(newer, r["sha256"], r["title"], when) == {"ok": False, "line": NOT_SAVED_LINE % "plant setup page"}

        # 9. the rates page: values in the file, states only on the page, private wording
        rates = t / "rates.md"
        rates.write_text(RATES_SAMPLE, encoding="utf-8")
        rr = render(rates, t / "rpage", "rates")
        assert rr["title"] == "Plant rates: Example Manufacturing", rr
        assert list(rr["files"]) == ["setup/plant-rates.txt"] and rr["sha256"] == _sha(rates), rr
        rpage = (t / "rpage" / "index.html").read_text(encoding="utf-8")
        for value in ("71.00", "140", "0.32", "62.00"):
            assert value not in rpage, value
        assert "Labor rate:</strong> confirmed - given by Pat Doyle, 2026-10-02" in rpage, rpage
        assert "set in environment (MFG_BURDEN_RATE)" in rpage and "Keep this page private" in rpage
        # the value is hidden wherever it sits: first word, after the dash, a sub-bullet, a table
        assert state_only("**Labor rate:** 71.00/hr confirmed - given by x") == "**Labor rate:** confirmed - given by x"
        assert state_only("**Labor rate:** confirmed - 71.00/hr, given by x, 2026-10-02") == \
            "**Labor rate:** confirmed - [on file], given by x, 2026-10-02"
        assert state_only("**Burden rate:** set in environment (MFG_BURDEN_RATE)") == \
            "**Burden rate:** set in environment (MFG_BURDEN_RATE)"
        hidden = details_html("### Commercial rates\n\n- **Margin rules:** see the table\n  - prototype: 0.45\n\n"
                              "| Job type | Margin |\n|---|---|\n| prototype | 45% |\n\nFY25 budget, 2026-10-02.\n",
                              hide_values=True)
        assert "45" not in hidden and "FY25 budget, 2026-10-02." in hidden, hidden
        # both ends of a range and a bare decimal are hidden; references, dates and MFG_ names are not
        assert _no_values("30-45% by job type, 0.30-0.45 or .28") == "[on file]-[on file] by job type, [on file]-[on file] or [on file]"
        refs = "PN-4471 FY25 RFQ-12 SRC-2026-10-14-PN-4471-B-BO VEND-5120 MFG_LABOR_RATE 2026-10-02"
        assert _no_values(refs) == refs, _no_values(refs)
        try:
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            ri = install(t / "rpage" / "setup" / "plant-rates.txt", company="Example Manufacturing", cwd=t, kind="rates")
            assert ri["profile_path"] == str(t / LOCAL_DIR / "plant-rates.md"), ri
            f = find(cwd=t)
            assert f["rates_exists"] and f["rates_path"] == ri["profile_path"], f
            assert "Plant rates: <company>" in f["setup_page_first"], f
            for w in ("mcp__claude-artifacts__", "setup/plant-context.txt", "setup/plant-rates.txt",
                      "setup/plant-context.md", "setup/plant-rates.md"):   # .md: older pages
                assert w in f["setup_page_first"], w
            assert "Artifact tool" not in f["setup_page_first"], f
        finally:
            if old is not None:
                os.environ["CLAUDE_PLUGIN_DATA"] = old
        assert saved(rates, rr["sha256"], rr["title"], when)["line"].startswith("Saved to your plant rates page")
        try:
            install(t / "page" / DATA_PATH, cwd=t, kind="rates")
            raise AssertionError("rates install accepted a setup file")
        except SetupError:
            pass

        # 10. the Open work page
        try:
            _work_selftest(t)
        finally:
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            if old is not None:
                os.environ["CLAUDE_PLUGIN_DATA"] = old
    print("plant_setup selftest: ok")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        old = os.environ.pop("CLAUDE_PLUGIN_DATA", None)   # the selftest writes only to its own temp folder
        try:
            return _selftest()
        finally:
            if old is not None:
                os.environ["CLAUDE_PLUGIN_DATA"] = old
    ap = argparse.ArgumentParser(prog="plant_setup.py")
    ap.add_argument("command", choices=["find", "render", "install", "saved", "stamp", "put",
                                        "prune", "migrate"])
    ap.add_argument("--profile")
    ap.add_argument("--out")
    ap.add_argument("--from", dest="src")
    ap.add_argument("--company")
    ap.add_argument("--sha256")
    ap.add_argument("--title")
    ap.add_argument("--kind", choices=sorted(KINDS), default="setup")
    ap.add_argument("--titles", nargs="*")
    ap.add_argument("--rendered")
    ap.add_argument("--block")
    ap.add_argument("--entry")
    ap.add_argument("--text")
    ap.add_argument("--text-file", dest="text_file")
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--by")
    ap.add_argument("--days", type=int, default=90)
    a = ap.parse_args(argv)
    try:
        if a.command == "find":
            res = find(a.company, titles=a.titles)
        elif a.command == "put":
            text = a.text
            if a.text_file:
                text = pathlib.Path(a.text_file).read_text(encoding="utf-8")
            if text is None and not a.remove:
                raise SetupError("put needs --text-file, --text or --remove")
            res = put(a.block, text, a.entry, a.remove, a.company, a.by)
            res["after_any_change"] = after_any_change("work")
        elif a.command == "prune":
            res = prune(a.days)
        elif a.command == "migrate":
            res = migrate(a.src, a.company)
        elif a.command == "render":
            res = render(a.profile, a.out, a.kind)
        elif a.command == "install":
            res = install(a.src, a.company, kind=a.kind)
            res["after_any_change"] = after_any_change(a.kind)
        elif a.command == "saved":
            res = saved(a.src, a.sha256, a.title, rendered=a.rendered)
        else:
            res = stamp(a.profile)
    except (SetupError, OSError, TypeError) as e:
        sys.stdout.write(json.dumps({"error": str(e)}) + "\n")
        return 2
    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
