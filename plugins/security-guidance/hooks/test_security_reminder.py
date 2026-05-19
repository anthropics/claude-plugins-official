#!/usr/bin/env python3
"""
Standalone tests for security_reminder_hook.check_patterns().

Run directly :
    python3 test_security_reminder.py

No external dependencies. Validates the word-boundary fix for false-positive
prone substrings.

NOTE: all dangerous keywords (both in test data and in test descriptions)
are constructed via string concatenation so this test file itself does not
trip the very hook it tests when contributors edit it through Claude Code.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK_PATH = os.path.join(HERE, "security_reminder_hook.py")

spec = importlib.util.spec_from_file_location("hook", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


# Trigger keyword fragments (built at runtime to avoid self-trigger).
_E = "\x65"   # 'e'
_P = "\x70"   # 'p'
_N = "\x6e"   # 'n'

EV = _E + "val("
EX = _E + "xec("
PI = _P + "ickle"
NF = _N + "ew Function"
IHE = ".inner" + "HTML ="
DW = "docu" + "ment.write"
DSIH = "danger" + "ouslySetInnerHTML"
OSY = "os.sy" + "stem"

# Description tokens (also fragmented).
KW_DYN = "dynamic-" + "code-call"
KW_SHELL = "shell-" + "exec-call"
KW_DESER = "des" + "eria" + "lization"
KW_XSS = "XSS-" + "inner-html"
KW_DOC_W = "doc-" + "write"
KW_DSIH = "dyn-" + "html-prop"
KW_NF = "dyn-" + "fn-ctor"
KW_OSY = "os-" + "syscall"


# (description, content, should_trigger)
TEST_CASES = [
    # True positives (must trigger after fix)
    (f"standalone {KW_DYN}", "result = " + EV + "user_input)", True),
    (f"standalone {KW_SHELL}", "import os; os." + EX + "cmd)", True),
    (
        f"standalone {KW_DESER}",
        "import " + PI + "\nx = " + PI + ".loads(data)",
        True,
    ),

    # False positives the boundary check must SUPPRESS
    (
        "user-defined retr-prefixed function",
        "def score_retr" + "ieval(query, base):\n    return sims",
        False,
    ),
    (
        f"method name with {KW_DESER}-keyword prefix",
        "def " + PI + "_data(self): return self.data",
        False,
    ),
    (
        f"function name with {KW_SHELL}-keyword prefix",
        "def myex" + "ec(cmd):\n    return run(cmd)",
        False,
    ),
    (
        "identifier 'medi-val_history'",
        "self.medie" + "val_history = []",
        False,
    ),
    (
        "identifier 'ev-aluate(' with alphanum suffix",
        "score = e" + "val" + "uate(x, y, z)",
        False,
    ),

    # Backward compat (non-WB patterns still trigger by raw substring)
    (f"{KW_XSS} still flagged", "el" + IHE + " userInput", True),
    (f"{KW_DOC_W} still flagged", DW + "('<div>' + html + '</div>')", True),
    (f"{KW_DSIH} still flagged", "<div " + DSIH + "={{__html: x}} />", True),
    (f"{KW_NF} still flagged", "const f = " + NF + "('return ' + src);", True),
    (f"{KW_OSY} still flagged", "import os\n" + OSY + "('rm -rf /tmp/' + name)", True),
]


def main():
    passed = 0
    failed = []

    for desc, content, expected in TEST_CASES:
        rule, _ = hook.check_patterns("test.py", content)
        triggered = rule is not None
        ok = triggered == expected
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {desc:60s} -> triggered={triggered}, rule={rule}")
        if ok:
            passed += 1
        else:
            failed.append(desc)

    print("")
    print(f"Result: {passed}/{len(TEST_CASES)} passed")
    if failed:
        print(f"FAILED: {failed}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
