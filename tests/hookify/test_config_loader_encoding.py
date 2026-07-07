#!/usr/bin/env python3
"""Regression tests for hookify UTF-8 rule/transcript reading.

Reproduces https://github.com/anthropics/claude-plugins-official/issues/3711:
on Windows systems whose default locale is not UTF-8 (e.g. cp950 / cp1252),
hookify read rule and transcript files with a bare ``open(path, 'r')`` and no
explicit ``encoding``. A rule file containing non-ASCII characters (e.g. the
emoji in ``action: block`` messages) then raised ``UnicodeDecodeError``; the
exception was swallowed and the rule silently dropped, so a ``block`` rule
failed *open* — the dangerous command it was meant to stop ran normally.

To reproduce that platform behaviour deterministically on any OS, we patch
``builtins.open`` so that a text-mode read with no explicit ``encoding`` falls
back to a codec that cannot decode multi-byte UTF-8 (``ascii``). With the fix
in place the module passes ``encoding='utf-8'`` explicitly and is unaffected.
"""

import builtins
import sys
from pathlib import Path

import pytest

# Make ``core`` importable the same way the hookify hooks do (they run with the
# plugin root on sys.path and import ``from core.config_loader import ...``).
HOOKIFY_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "hookify"
if str(HOOKIFY_ROOT) not in sys.path:
    sys.path.insert(0, str(HOOKIFY_ROOT))

from core.config_loader import load_rule_file  # noqa: E402
from core.rule_engine import RuleEngine  # noqa: E402

_real_open = builtins.open


def _ascii_default_open(file, mode="r", *args, **kwargs):
    """Stand-in for ``open`` that mimics a non-UTF-8 default locale.

    When a caller opens a text-mode file without specifying an encoding, real
    ``open`` uses ``locale.getpreferredencoding()`` — cp950/cp1252 on many
    Windows installs. We force ``ascii`` in that case so any non-ASCII byte
    raises ``UnicodeDecodeError``, exactly as the bug does in the field. Callers
    that pass an explicit ``encoding`` (the fix) are left untouched.
    """
    # open(file, mode, buffering, encoding, ...): encoding is the 2nd optional
    # positional after mode, i.e. args[1]. Only inject when it is truly absent.
    if "b" not in mode and "encoding" not in kwargs and len(args) < 2:
        kwargs["encoding"] = "ascii"
    return _real_open(file, mode, *args, **kwargs)


RULE_WITH_EMOJI = """---
name: block-rm-rf
enabled: true
event: bash
action: block
pattern: "rm -rf"
---

\U0001f6d1 Dangerous command blocked! Do not run rm -rf.
"""


def test_load_rule_file_reads_utf8_under_non_utf8_locale(tmp_path, monkeypatch):
    rule_file = tmp_path / "hookify.block.local.md"
    rule_file.write_text(RULE_WITH_EMOJI, encoding="utf-8")

    monkeypatch.setattr(builtins, "open", _ascii_default_open)

    rule = load_rule_file(str(rule_file))

    # Before the fix this is None (UnicodeDecodeError -> rule dropped -> fail-open).
    assert rule is not None, "block rule was silently dropped under a non-UTF-8 locale"
    assert rule.action == "block"
    assert "\U0001f6d1" in rule.message


def test_extract_transcript_reads_utf8_under_non_utf8_locale(tmp_path, monkeypatch):
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        '{"role":"user","content":"\U0001f6d1 please stop"}\n', encoding="utf-8"
    )

    monkeypatch.setattr(builtins, "open", _ascii_default_open)

    engine = RuleEngine()
    result = engine._extract_field(
        "transcript", "", {}, {"transcript_path": str(transcript)}
    )

    # Before the fix this is '' (UnicodeDecodeError swallowed), so Stop-event
    # rules matching transcript content would never fire.
    assert result, "transcript read returned empty under a non-UTF-8 locale"
    assert "\U0001f6d1" in result


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
