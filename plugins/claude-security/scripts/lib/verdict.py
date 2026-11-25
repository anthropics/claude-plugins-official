"""The merge verdict: the policies CLAUDE_SECURITY_FAIL_ON names, what each makes of a report's
findings, and the lines the job's later steps read."""

from __future__ import annotations

import enum
from collections import Counter
from typing import TYPE_CHECKING, NamedTuple

from . import plugin
from .exhaustiveness import unreachable
from .finding import Confidence, Severity

if TYPE_CHECKING:
    from collections.abc import Sequence


class Graded(NamedTuple):
    """What the verdict reads of one finding."""

    severity: Severity
    confidence: Confidence


class Status(enum.Enum):
    """A report's verification status as its stamp gives it: one of the renderer's two words, or
    UNKNOWN for any other value or for none."""

    VERIFIED = plugin.VERIFIED
    UNVERIFIED = plugin.UNVERIFIED
    UNKNOWN = "unknown"


class FailOn(enum.Enum):
    """The policies CLAUDE_SECURITY_FAIL_ON can name, permissive to strict. fails() says which
    findings fail the run, and Verdict.of() what else does."""

    NEVER = "never"
    CONFIDENT_HIGH = "confident-high"
    HIGH = "high"
    MEDIUM = "medium"
    ANY = "any"

    def fails(self, finding: Graded) -> bool:
        """Whether one finding fails the run under this policy."""
        if self is FailOn.NEVER:
            return False
        if self is FailOn.ANY:
            return True
        if self is FailOn.MEDIUM:
            return finding.severity >= Severity.MEDIUM
        high = finding.severity >= Severity.HIGH
        if self is FailOn.HIGH:
            return high
        if self is FailOn.CONFIDENT_HIGH:
            return high and finding.confidence is Confidence.high
        return unreachable(self)


DEFAULT_POLICY = FailOn.HIGH
PASS, FAIL = "pass", "fail"
KEYS = ("verdict", "findings", *(level.name.lower() for level in Severity))
IN_THIS_CHANGE = " in this change"


def reading_missing(lost: int) -> str:
    """What the verdict, the review and the job's log say of Stamp.lost. It is true of an agent
    that did not return and of one that returned without the diff: the stamp does not tell them
    apart."""
    return f"the reading of {lost} of the scan's research agents is missing"


class Verdict(NamedTuple):
    """Whether the run passes, the reason, and the grades it was reached over."""

    passed: bool
    reason: str
    graded: Sequence[Graded]
    # Whether the findings, not another rule, fail the run.
    by_findings: bool = False

    @property
    def word(self) -> str:
        """pass or fail, as the verdict file and the printed line spell it."""
        return PASS if self.passed else FAIL

    @property
    def sentence(self) -> str:
        """The verdict and its reason, as the job summary says them."""
        return f"Verdict: {self.word} ({self.reason})."

    @classmethod
    def nothing_scanned(cls) -> Verdict:
        """The verdict for a pull request that changes no files: it passes, nothing audited."""
        nothing = "the pull request changes no files, so there was nothing to scan"
        return cls(passed=True, reason=nothing, graded=[])

    @classmethod
    def of(
        cls,
        graded: Sequence[Graded],
        *,
        status: Status,
        lost: int,
        policy: FailOn,
        older: bool = False,
    ) -> Verdict:
        """The verdict over the findings' grades under `policy`; a report whose checks did not all
        pass fails every policy but `never`, and so does one whose scan lacks an agent's reading.
        `older` says that the report also lists findings older than the change, which `graded`
        leaves out. A pass at a bar then gives a reason on the change alone."""
        if policy is FailOn.NEVER:
            return cls(passed=True, reason="the policy is never", graded=graded)
        if status is not Status.VERIFIED:
            unverified = (
                f"the report's verification status is {status.value}, so it cannot clear the run"
            )
            return cls(passed=False, reason=unverified, graded=graded)
        failing = sum(policy.fails(finding) for finding in graded)
        if failing:
            findings = f"{failing} finding{'' if failing == 1 else 's'}"
            reason = f"{findings} at the {policy.value} bar"
            return cls(passed=False, reason=reason, graded=graded, by_findings=True)
        if lost:
            missing = f"{reading_missing(lost)}, so part of the scan is missing"
            return cls(passed=False, reason=missing, graded=graded)
        where = IN_THIS_CHANGE if older else ""
        return cls(
            passed=True, reason=f"no finding at the {policy.value} bar{where}", graded=graded
        )

    def lines(self) -> list[str]:
        """The key=value lines later workflow steps read: the verdict, the finding count, and
        the tally by severity."""
        counts = Counter(finding.severity for finding in self.graded)
        values = (self.word, len(self.graded), *(counts[level] for level in Severity))
        return [f"{key}={value}" for key, value in zip(KEYS, values)]
