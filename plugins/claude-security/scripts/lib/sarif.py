"""SARIF 2.1.0 for one scan: the log encoder."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, NamedTuple
from urllib.parse import quote

from . import cwe, secret, source

if TYPE_CHECKING:
    import uuid
    from collections.abc import Collection, Mapping, Sequence

    from .finding import Finding, Panel, Record

SCHEMA_ID = (
    "https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/schemas/sarif-schema-2.1.0.json"
)
# The driver name GitHub keys alert identity on; renaming it orphans every open alert.
TOOL_NAME = "Claude Security Plugin for Claude Code"
TOOL_URI = "https://claude.com/product/claude-security"
PROPERTY_BAG = "claudeSecurityPlugin"
ID_PREFIX = "claude-security-plugin"
FINDING_ID: Final = "claudeSecurityPluginFindingId"
ID_VERSION = "v3"
CONTEXT_LINES = 3
SRCROOT = "%SRCROOT%"
# error is SARIF's highest level, so CRITICAL and HIGH both map to it.
LEVEL = {"CRITICAL": "error", "HIGH": "error", "MEDIUM": "warning", "LOW": "note"}


@dataclass(frozen=True)
class Scan:
    """The one scan a log describes: its identity, where it ran, and the repository it names."""

    id: uuid.UUID
    mode: str
    # The scan root below the repository top level, slash-terminated; "" when there is none.
    prefix: str
    # The credential-free https form of the repository's remote; None when there is not one.
    remote: str | None
    # The directories the scan was limited to, relative to the scan root; empty for all of it.
    scope: tuple[str, ...]
    # The commit the scanned tree was exactly at; None when it was dirty, unversioned or unknown.
    revision: str | None


def log(
    findings: Sequence[Record],
    scan: Scan,
    tool_version: str | None,
    run_properties: Mapping[str, object],
    panels: Mapping[str, Panel],
    notifications: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """The SARIF 2.1.0 log for one scan: one run, one rule per category, one result per finding.

    `findings` are the records render_report built with placed(): each on the
    line its file places it on, carrying its id.
    """
    filed = [(item, category_of(item)) for item in findings]
    categories = list(dict.fromkeys(category for _, category in filed))
    index = {category: position for position, category in enumerate(categories)}
    driver: dict[str, object] = {
        "name": TOOL_NAME,
        "organization": "Anthropic",
        "informationUri": TOOL_URI,
        **({"version": tool_version} if tool_version else {}),
        "rules": [rule(category) for category in categories],
    }
    invocation: dict[str, object] = {"executionSuccessful": True}
    if notifications:
        invocation["toolExecutionNotifications"] = list(notifications)
    base_description = (
        "The top level of the scanned repository, or the scanned directory when the scan did "
        "not run inside a git checkout."
    )
    run: dict[str, object] = {
        "tool": {"driver": driver},
        "automationDetails": {"id": automation_id(scan), "guid": str(scan.id)},
        "invocations": [invocation],
        "originalUriBaseIds": {SRCROOT: {"description": {"text": base_description}}},
        "results": [
            result(item, category, index[category], scan, panels.get(item["id"]))
            for item, category in filed
        ],
        "properties": {
            PROPERTY_BAG: {
                **run_properties,
                "target_kind": "git-remote" if scan.remote else "local-path",
            }
        },
    }
    if scan.remote:
        provenance: dict[str, object] = {"repositoryUri": scan.remote}
        if scan.revision:
            provenance["revisionId"] = scan.revision
        run["versionControlProvenance"] = [provenance]
    return {"$schema": SCHEMA_ID, "version": "2.1.0", "runs": [run]}


def automation_id(scan: Scan) -> str:
    """The run's automation id: the plugin prefix, the mode, the scan's extent if any, its id."""
    category = f"{ID_PREFIX}/{scan.mode}"
    if scan.scope:
        extent = ",".join(scan.prefix + entry.strip("/") for entry in sorted(scan.scope))
    else:
        extent = scan.prefix.rstrip("/")
    if extent:
        category += "/" + quote(uri_bytes(extent))
    return f"{category}/{scan.id}"


def category_of(finding: Finding) -> cwe.Category | None:
    """The Simplified Mapping entry the finding's CWE rolls up to; None for Uncategorized."""
    return cwe.catalog.category(cwe.id_number(finding["cwe_id"]))


def rule_id(category: cwe.Category | None) -> str:
    """A rule's id: its entry's CWE id (`CWE-89`), or `uncategorized`."""
    return category.id if category is not None else cwe.UNCATEGORIZED.lower()


def rule(category: cwe.Category | None) -> dict[str, object]:
    """The reporting descriptor for one entry: the catalog's names, its page, its fixed tags."""
    help_text = (
        "Each alert's message names the finding's own CWE and states the impact, exploit "
        "scenario, preconditions and recommended fix; the finding appears under its F<n> id "
        "in CLAUDE-SECURITY-RESULTS.md."
    )
    if category is None:
        return {
            "id": rule_id(None),
            "name": cwe.UNCATEGORIZED,
            "shortDescription": {"text": cwe.UNCATEGORIZED},
            "fullDescription": {
                "text": "Findings whose CWE is not an entry of the CWE Simplified Mapping view "
                f"and rolls up to none, reported by {TOOL_NAME} from static review of the "
                "source."
            },
            "help": {"text": help_text},
            "properties": {"tags": ["security"]},
        }
    return {
        "id": category.id,
        "name": rule_name(category.name),
        "shortDescription": {"text": category.name},
        "fullDescription": {
            "text": f"{category.title} ({category.id}, CWE {cwe.catalog.version}): findings whose "
            f"CWE is this entry of the Simplified Mapping view or rolls up to it, reported by "
            f"{TOOL_NAME} from static review of the source."
        },
        "help": {"text": help_text},
        "helpUri": f"https://cwe.mitre.org/data/definitions/{category.number}.html",
        "properties": {"tags": ["security", f"external/cwe/cwe-{category.number}"]},
    }


def placed(
    findings: Sequence[Finding],
    scan: Scan,
    sources: Mapping[str, str],
    *,
    refused_secrets: Collection[str],
) -> list[Record]:
    """Each finding as the products carry it: `line` moved to where its file places it, id added.

    `sources` is the text of each scanned file by the finding's `file`; a
    finding whose file is absent from it keeps its line and hashes the number.
    """
    texts = {repository_file(scan, file): text for file, text in sources.items()}
    secrets = {
        (path, line)
        for f in findings
        if secret.is_credential(f)
        for path, line in secret_lines(repository_path(scan, f), f, texts)
    } | {
        (path, line)
        for quote in refused_secrets
        for path, text in texts.items()
        for line in source.quoted_lines(text, quote, whole=False)
    }
    return [placed_one(f, scan, sources.get(f["file"]), secrets) for f in findings]


def placed_one(
    finding: Finding, scan: Scan, text: str | None, secrets: Collection[tuple[str, int]]
) -> Record:
    """One finding placed in `text`, its file's content (None when unread), and given its id."""
    moved: Finding = finding
    code = None
    if text is not None:
        lines = source.normalized_lines(text)
        row = source.placing_row(lines, finding["line"], finding["snippet"])
        if row is not None:
            moved = {**finding, "line": row + 1}
            path = repository_path(scan, finding)
            near_secret = any(p == path and abs(row + 1 - n) <= CONTEXT_LINES for p, n in secrets)
            code = None if near_secret else code_at(lines, row)
    return {**moved, FINDING_ID: fingerprint(moved, scan, code)}


def secret_lines(home: str, credential: Finding, texts: Mapping[str, str]) -> set[tuple[str, int]]:
    """Every (repository path, line) of `texts` on which the `credential` finding's quote occurs.

    `home` is the credential's own repository path and `texts` the scanned
    files by repository path. The quote is marked wherever it occurs in any
    file, with one restraint: a quote its own file shows only as part of a
    longer line is marked in the other files just where it is a whole line of
    theirs. The credential's own line is always marked, for one whose quote
    matched nothing or whose file was not read.
    """
    snippet = credential["snippet"]
    own = texts.get(home, "")
    found = bool(source.quoted_lines(own, snippet, whole=False))
    fragment = found and not source.quoted_lines(own, snippet, whole=True)
    return {
        (path, line)
        for path, text in texts.items()
        for line in source.quoted_lines(text, snippet, whole=fragment and path != home)
    } | {(home, credential["line"])}


def fingerprint(finding: Finding, scan: Scan, code: str | None) -> str:
    """ID_VERSION, a colon, and a sha256 hex over the rule id, the repository path and `code`.

    `code` is the file's normalized lines around the placed one (code_at);
    None hashes the finding's line number in its place.
    """
    where: str | int = finding["line"] if code is None else code
    basis = [rule_id(category_of(finding)), repository_path(scan, finding), where]
    canonical = json.dumps(basis, separators=(",", ":"), ensure_ascii=True)
    return f"{ID_VERSION}:{hashlib.sha256(canonical.encode()).hexdigest()}"


def code_at(lines: Sequence[str], row: int) -> str:
    """The normalized `lines` CONTEXT_LINES either side of `row`, joined; fewer at a file's ends."""
    return "\n".join(lines[max(row - CONTEXT_LINES, 0) : row + CONTEXT_LINES + 1])


class Site(NamedTuple):
    """What one result stands for: a rule at a line of a file; the log holds one result per site."""

    rule: str
    path: str
    line: int


def site(finding: Record, scan: Scan) -> Site | None:
    """The finding's site: its rule id, repository path and placed line; None for a line below 1."""
    if finding["line"] < 1:
        return None
    return Site(rule_id(category_of(finding)), repository_path(scan, finding), finding["line"])


def result(
    finding: Record,
    category: cwe.Category | None,
    rule_index: int,
    scan: Scan,
    panel: Panel | None,
) -> dict[str, object]:
    """One result: the finding under its rule, its location, and its JSONL record, id included."""
    shown = secret.withheld(finding)
    record: dict[str, object] = {**shown}
    if panel is not None:
        record["verification"] = {"panel": panel}
    return {
        "ruleId": rule_id(category),
        "ruleIndex": rule_index,
        "level": LEVEL[finding["severity"]],
        "message": {"text": message(finding)},
        "locations": [location(shown, scan)],
        "properties": {PROPERTY_BAG: record},
    }


def location(finding: Finding, scan: Scan) -> dict[str, object]:
    """A result's one location: the file relative to SRCROOT, the line, the snippet, the symbol.

    The line is the finding's placed line (placed()): where its quoted code
    sits in the file, or the line it declared when nothing places it.
    """
    line = finding["line"]
    region: dict[str, object] = {"startLine": max(line, 1)}
    if line >= 1 and finding["snippet"].strip():
        region["snippet"] = {"text": finding["snippet"]}
    place: dict[str, object] = {
        "physicalLocation": {
            "artifactLocation": {
                "uri": quote(uri_bytes(repository_path(scan, finding))),
                "uriBaseId": SRCROOT,
            },
            "region": region,
        }
    }
    if symbol := finding["symbol"].strip():
        place["logicalLocations"] = [{"name": symbol, "fullyQualifiedName": symbol}]
    return place


def repository_path(scan: Scan, finding: Finding) -> str:
    """The finding's file relative to the repository top level, with any leading climb folded."""
    return repository_file(scan, finding["file"])


def repository_file(scan: Scan, file: str) -> str:
    """A scan-root-relative `file`, as file_field carries it, made repository-relative."""
    return posixpath.normpath(scan.prefix + file)


def uri_bytes(text: str) -> bytes:
    """`text` as the bytes its uri must name; byte-faithful for a filesystem name."""
    try:
        return text.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        return text.encode("utf-8", "surrogatepass")


def notification(descriptor_id: str, level: str, text: str) -> dict[str, object]:
    """One invocation notification: its namespaced descriptor id, its level, and its message."""
    return {"descriptor": {"id": descriptor_id}, "level": level, "message": {"text": text}}


def message(finding: Finding) -> str:
    """A result's message: the finding's prose, its stated parts labeled, then its ratings."""
    parts = [sentence(finding["title"]), sentence(finding["description"])]
    labeled = (
        ("Impact", finding["impact"]),
        ("Exploit scenario", finding["exploit_scenario"]),
        ("Preconditions", "; ".join(finding["preconditions"])),
        ("Recommendation", finding["recommendation"]),
    )
    parts += [f"{label}: {text}" for label, value in labeled if (text := sentence(value))]
    if finding["line"] < 1:
        parts.append("The exact line was not determined; see the description.")
    if secret.is_credential(finding):
        parts.append("The source line is not quoted because it holds the credential.")
    parts.append(
        f"{finding['cwe_id']}. Severity {finding['severity']}, confidence {finding['confidence']}."
    )
    return "\n\n".join(parts)


def rule_name(category: str) -> str:
    """A category's common name in PascalCase, for a rule name: `SQLInjection`."""
    return "".join(word[:1].upper() + word[1:] for word in re.split(r"[^A-Za-z0-9]+", category))


def sentence(text: str) -> str:
    """`text` stripped and closed with a period unless it already ends in punctuation."""
    text = text.strip()
    return text if not text or text[-1] in ".!?" else text + "."
