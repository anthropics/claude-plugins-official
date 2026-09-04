"""The snippet of a hard-coded credential finding, withheld from what the products carry.

The line such a finding quotes is the credential itself, and the JSONL and
SARIF files exist to leave the machine (a code scanning upload, a CI
artifact), so neither file quotes it: the finding's file, line and symbol
still locate the code, and the SARIF result's message says why no line is
quoted. Only the emitted copy changes: the finding is still placed on the
snippet as the researcher quoted it, and neither its id nor that of a
finding placed near it hashes the credential's line.
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


def is_credential(finding: Finding) -> bool:
    """Whether the finding's CWE rolls up to Use of Hard-coded Credentials."""
    return is_credential_cwe(cwe.id_number(finding["cwe_id"]))


def withheld(finding: Record) -> Record:
    """`finding` as the products carry it: a hard-coded credential's snippet is empty."""
    return {**finding, "snippet": ""} if is_credential(finding) else finding
