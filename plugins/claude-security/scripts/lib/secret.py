"""A hard-coded credential finding's snippet and link to the change, withheld from the products.

The line such a finding quotes is the credential itself, and the JSONL and
SARIF files exist to leave the machine (a code scanning upload, a CI
artifact), so in neither file does that finding quote it: its file, line and
symbol still locate the code, and the SARIF result's message says why no line
is quoted. A change scan's link to the change (via_change) describes that same
line in the researcher's words, so it goes with the snippet: here for the
credential finding, in sarif.placed for a finding near the credential's line
or whose link opens there.

At Change Scan Effort high a site, which is a rule at a line of a file, can
have two records: one among the findings of the change, and one among those
older than it. render_report.one_per_site gives each the credential CWE ids of
the other, so that neither quotes the line. A record under another rule on
that line still quotes it.

Only the emitted copy changes: the finding is still placed on the snippet as
the researcher quoted it, and neither its id nor that of a finding placed near
it hashes the credential's line.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import cwe

if TYPE_CHECKING:
    from .finding import Finding, Record

# CWE's Simplified Mapping entry Use of Hard-coded Credentials; CWE-259, 321 and 671 roll up to it.
CREDENTIALS = 798


def is_credential_cwe(number: int) -> bool:
    """Whether CWE `number` rolls up to Use of Hard-coded Credentials."""
    return cwe.catalog.category_of.get(number) == CREDENTIALS


def is_credential_id(cwe_id: str) -> bool:
    """Whether a canonical `CWE-<number>` id rolls up to Use of Hard-coded Credentials;
    ValueError for one whose number cannot be read."""
    return is_credential_cwe(cwe.id_number(cwe_id))


def is_credential(finding: Finding) -> bool:
    """Whether any CWE the finding carries rolls up to Use of Hard-coded Credentials."""
    return any(map(is_credential_id, (finding["cwe_id"], *finding["other_cwe_ids"])))


def withheld(finding: Record) -> Record:
    """`finding` as the products carry it: a hard-coded credential's snippet and link withheld."""
    if not is_credential(finding):
        return finding
    return {**finding, "snippet": "", "via_change": None}
