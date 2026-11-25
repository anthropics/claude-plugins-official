"""The plugin's fixed names, and its own manifest."""

from __future__ import annotations

import enum
import os
import re
from contextlib import suppress
from pathlib import Path
from typing import Final

from . import strictjson
from .strictjson import JsonMap, is_list, is_map, is_str

NAME = "claude-security"
MANIFEST_DIR = ".claude-plugin"
ROOT = Path(__file__).resolve().parents[2]
RUN_DIR_NAME = ".claude-security-run"
TARGET_FILES_NAME = "target-files.json"
COVERAGE_MD_NAME = "coverage.md"
LAST_REPORT_NAME = "last-report.json"
BEHIND_NAME = "reports-behind.json"
BEHIND_FILED = "alsoFiledAt"
BEHIND_PLACES = "places"
CHANGE_SCAN_EFFORT_KEY = "changeScanEffort"
CHANGE_SCAN_EFFORT_HIGH = "high"
RUN_NOT_RECORDED_KEY = "runNotRecorded"
# Set only by workflows/scan.js (its PROVENANCE) on each vote record it computes.
VOTES_PROVENANCE = "workflows/scan.js"
STAMP_MODES = {"scan": "scan.full", "changes": "scan.changes", "commit": "scan.commit"}
MODES = tuple(STAMP_MODES)
ANALYSIS_STAMP_MODE = "scan.attack-surface"
TRIAGE_STAMP_MODE = "triage"
ANALYSIS_META_NAME = "analysis.json"
REPORT_DIR_PREFIX = "CLAUDE-SECURITY-"
# \Z, not $: `$` also matches before a trailing newline, and this is a fence.
REPORT_DIR_RE = re.compile(rf"^{re.escape(REPORT_DIR_PREFIX)}[0-9][0-9-]*\Z")
RESULTS_MD_NAME = "CLAUDE-SECURITY-RESULTS.md"
JSONL_NAME = "CLAUDE-SECURITY-RESULTS.jsonl"
TRIAGE_MD_NAME = "FINDINGS-TRIAGE.md"
SARIF_NAME = "CLAUDE-SECURITY-RESULTS.sarif"
REVISION_PREFIX = "CLAUDE-SECURITY-REVISION-"
PATCHES_DIR_NAME = "patches"
ANALYSIS_PATCHES_DIR_NAME = "attack-surface-patches"
PATCHES_INDEX_NAME = "PATCHES.md"
PATCHES_JSONL_NAME = "patches.jsonl"
EXPLANATIONS_DIR_NAME = "explanations"
# The mark that patch_artifacts.py sets on each patches.jsonl record.
PATCHES_PROVENANCE = "scripts/patch_artifacts.py"
# The apply_check value patch_artifacts.py records for a patch that applied cleanly when written.
APPLY_CLEAN = "clean"
APPLY_CONFLICTS = "conflicts"
APPLY_NOT_RUN = "not_run"
PROBE_NAME = "claude-security-probe.json"
PREVIOUS_NAME = "CLAUDE-SECURITY-PREVIOUS.json"
# Marks a finished report: it comes out last, not after a fault, refused file or named removal.
COMPLETE_NAME = "CLAUDE-SECURITY-COMPLETE"
MESSAGE_TOLD: Final = ".message-told-"


class Claim(enum.Enum):
    """The claims a patch's panel makes about it, in the order a patches.jsonl record states
    them: each carries its key in that record, and its wording as the review labels it and
    as a patch's header and notes print it."""

    TARGETED = (
        "targeted",
        "targeted to this finding",
        "the change is highly targeted to this finding",
    )
    NO_NEW_VULNERABILITY = (
        "no_new_vulnerability",
        "introduces no new vulnerability",
        "the change introduces no new security vulnerability",
    )
    BEHAVIOUR_UNCHANGED = (
        "behaviour_unchanged",
        "leaves behaviour otherwise unchanged",
        (
            "apart from the fix itself, the change does not alter the code's behaviour or the "
            "inputs it accepts"
        ),
    )

    key: str
    label: str
    sentence: str

    def __init__(self, key: str, label: str, sentence: str) -> None:
        self.key = key
        self.label = label
        self.sentence = sentence


AI_CAUTION = "Claude is an AI and can make mistakes"
AI_CAUTION_LINK = (
    f"[{AI_CAUTION}](https://support.claude.com/en/articles/"
    "8525154-claude-is-providing-incorrect-or-misleading-responses-what-s-going-on)"
)
SET_ASIDE = "set_aside"
# A claim's state when the panel vouches for it, and every state a panel may leave one in.
CONFIDENT = "CONFIDENT"
CLAIM_STATES = (CONFIDENT, "NOT_CONFIDENT", "UNSURE")
# The id of a finding a patch is written for, F and its number: it names F<n>.patch and F<n>.md.
PATCH_UNIT_ID_PATTERN = "F[0-9]{1,9}"
# The verification status that render_report.py and attack_surface_report.py stamp.
VERIFIED: Final = "verified"
UNVERIFIED: Final = "unverified"
# \Z, not $: `$` also matches before a trailing newline, and this id names product files.
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,64}\Z")
SHORT_ID_CHARS = 12
_RETIRED_MAX_NOTE = (
    "The `max` effort tier has been retired, so I'm running this scan at `high`. "
    "A future version will stop accepting `max` and return an error."
)
RETIRED_MAX_RELAY = (
    "relay: say this to the user exactly as printed, to open your kickoff message and "
    f"again to close your results message: {_RETIRED_MAX_NOTE}"
)
NO_CHANGED_FILE = "no file changed here;"
OLD_SCAN_KEEP_REASON = "what that scan found might not be found again"
OLD_SCAN_META_REASON = (
    "A report of what that scan saved, made with such a file in any directory, would vouch for "
    "scan-meta.json content which that scan did not write, and nothing in the report would show it."
)


def lost_findings_text(run_dir: Path) -> str:
    """What the save and the render print for a run directory with votes.json and no findings.json:
    a sentence, then a relay line, or only a sentence if the scan's report is already delivered."""
    report_dir = Path(os.path.realpath(run_dir)).parent
    with suppress(OSError):
        if any(map(is_revision_stamp, report_dir.iterdir())):
            return (
                f"{report_dir.name} holds this scan's report, so there is nothing left to render."
            )
    return (
        "A list written by hand would not be the list that the panel voted on, so the panel's "
        "votes would not cover a report made from it.\n"
        "relay: say this to the user exactly as printed, as your whole message: This scan has no "
        f"report, because its findings.json file is missing. {report_dir.name} holds what is left "
        f"of the scan. Keep that directory, since {OLD_SCAN_KEEP_REASON}. Do you want a new scan?"
    )


def at_change_scan_effort_high(coverage: JsonMap) -> bool:
    """Whether the run whose coverage account this is ran at Change Scan Effort high."""
    return coverage.get(CHANGE_SCAN_EFFORT_KEY) == CHANGE_SCAN_EFFORT_HIGH


def context_of(coverage: JsonMap) -> JsonMap | None:
    """coverage.json's `context` map: what the scan was given. None where it names nothing."""
    context = coverage.get("context")
    if not is_map(context):
        return None
    given = context.get("given")
    return context if is_list(given) and any(is_str(name) and name for name in given) else None


def revision_stamp_name(tag: str) -> str:
    """A revision stamp's name, `CLAUDE-SECURITY-REVISION-<tag>.json`."""
    return f"{REVISION_PREFIX}{tag}.json"


def is_revision_stamp(path: Path) -> bool:
    """Whether `path` has a revision stamp's name, `CLAUDE-SECURITY-REVISION-<tag>.json`."""
    return path.name.startswith(REVISION_PREFIX) and path.suffix == ".json"


def holds_analysis(report_dir: Path) -> bool:
    """Whether the directory is an attack surface analysis's: its name has the form
    CLAUDE-SECURITY-<timestamp>, as a scan's has too, and analysis.json lies at its top. False where
    that file cannot be examined."""
    try:
        named = REPORT_DIR_RE.match(report_dir.absolute().name)
        return bool(named) and (report_dir / ANALYSIS_META_NAME).is_file()
    except OSError:
        return False


def version() -> str | None:
    """The non-blank version string in the plugin's manifest, or None when there is not one."""
    try:
        manifest = strictjson.load(ROOT / MANIFEST_DIR / "plugin.json")
    except (OSError, ValueError):
        return None
    if not is_map(manifest):
        return None
    declared = manifest.get("version")
    if not is_str(declared):
        return None
    return declared.strip() or None


def worktree_warning(folder: Path) -> str:
    """What the user must know of a report folder below `.claude/worktrees/`, where Claude Code puts
    its worktrees by default. Empty for any other folder."""
    if "/.claude/worktrees/" not in Path(os.path.realpath(folder)).as_posix():
        return ""
    return (
        "The report is in this session's worktree, where git ignores it. It can be deleted with "
        "the worktree, so copy its folder out to keep it."
    )


def folder_target_relay(folder: str, *, done: bool) -> str:
    """The relay line on a codebase scan whose target is `folder`, a folder below its repository's
    top: for the results message where the scan is `done`, else for the kickoff message."""
    message, verb = ("results", "was") if done else ("kickoff", "is")
    return (
        f"relay: say this to the user exactly as printed, in your {message} message, and do not "
        f"call the target the repository: This scan's target {verb} the folder {folder!r}, which "
        f"lies inside a git repository. The rest of that repository {verb} outside the target. To "
        "scan all of it, start Claude Code in the repository's top folder."
    )


def scan_call(args: JsonMap) -> str:
    """The call of the scan workflow with `args`, as a script prints it for the session to make."""
    return f'Workflow({{ name: "{NAME}:scan", args: {strictjson.text(args)} }})'
