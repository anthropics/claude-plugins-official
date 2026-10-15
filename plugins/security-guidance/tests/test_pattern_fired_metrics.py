import json

from conftest import (
    STUB_VULN, edit_payload, metrics_of, run_hook, stop_payload, ups_payload,
)

from patterns import RuleId

EVAL = 1 << RuleId.EVAL_INJECTION
SHELL = 1 << RuleId.PYTHON_SUBPROCESS_SHELL


def _edit(repo, env, name, content):
    (repo / name).write_text(content)
    run_hook(edit_payload(repo, repo / name, content), env)


def _turn(repo, env, edits, after=None):
    run_hook(ups_payload(repo), env)
    for name, content in edits.items():
        _edit(repo, env, name, content)
    for name, content in (after or {}).items():
        (repo / name).write_text(content)
    rc, so, se = run_hook(stop_payload(repo), env)
    return metrics_of(so)


class TestFiredRulesReachTheStopRow:
    def test_clean_review(self, env, gateway, workspace):
        _, repo = workspace
        m = _turn(repo, env, {"calc.js": "const v = eval(src)\n"})
        assert m["vulns_found"] == 0 and "review_ms" in m
        assert m["warn_fired_mask"] == EVAL
        assert m["warn_unresolved_mask"] == EVAL
        assert list(m).index("warn_fired_mask") < 20

    def test_fired_mask_is_the_last_key(self, env, gateway, workspace):
        """A row cut at the key cap loses the fired mask before the
        unresolved one."""
        _, repo = workspace
        gateway.vulns = [STUB_VULN]
        m = _turn(repo, env, {"calc.js": "const v = eval(src)\n"})
        assert list(m)[-2:] == ["warn_unresolved_mask", "warn_fired_mask"]
        assert m["warn_fixed"] == 0 and m["warn_unresolved"] == 1

    def test_review_with_findings(self, env, gateway, workspace):
        _, repo = workspace
        gateway.vulns = [STUB_VULN]
        m = _turn(repo, env, {"calc.js": "const v = eval(src)\n"})
        assert m["vulns_found"] == 1
        assert m["warn_fired_mask"] == EVAL and m["warn_unresolved_mask"] == EVAL

    def test_review_skipped(self, env, gateway, workspace):
        _, repo = workspace
        m = _turn(repo, {**env, "ENABLE_STOP_REVIEW": "0"},
                  {"calc.js": "const v = eval(src)\n"})
        assert m["skipped"] is True
        assert m["warn_fired_mask"] == EVAL and m["warn_unresolved_mask"] == EVAL

    def test_fixed_rule_is_fired_but_not_unresolved(self, env, gateway, workspace):
        _, repo = workspace
        m = _turn(
            repo, env,
            {"calc.js": "const v = eval(src)\n",
             "run.py": "import subprocess\nsubprocess.run(cmd, shell=True)\n"},
            after={"calc.js": "const v = JSON.parse(src)\n"},
        )
        assert m["warn_fired_mask"] == EVAL | SHELL
        assert m["warn_unresolved_mask"] == SHELL

    def test_no_warning_no_keys(self, env, gateway, workspace):
        _, repo = workspace
        m = _turn(repo, env, {"ok.py": "def ok():\n    return 1\n"})
        assert "warn_fired_mask" not in m and "warn_unresolved_mask" not in m

    def test_masks_are_reported_once(self, env, gateway, workspace):
        _, repo = workspace
        _turn(repo, env, {"calc.js": "const v = eval(src)\n"})
        m = _turn(repo, env, {"ok.py": "def ok():\n    return 2\n"})
        assert "warn_fired_mask" not in m and "warn_unresolved_mask" not in m

    def test_user_rule_is_not_counted_as_a_builtin_of_the_same_name(self, env, gateway, workspace):
        _, repo = workspace
        (repo / ".claude").mkdir()
        (repo / ".claude" / "security-patterns.json").write_text(json.dumps({"patterns": [
            {"rule_name": "eval_injection", "regex": "FORBIDDEN_CALL", "reminder": "no"}]}))
        m = _turn(repo, {**env, "ENABLE_STOP_REVIEW": "0"}, {"a.py": "FORBIDDEN_CALL()\n"})
        assert "warn_fired_mask" not in m
        assert m["warn_fixed"] == 0 and m["warn_unresolved"] == 1
