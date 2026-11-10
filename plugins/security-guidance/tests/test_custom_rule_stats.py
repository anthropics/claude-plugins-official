"""Counts about custom rules on the Stop row. They change no rule's outcome."""
import json
import os

import pytest

import diffstate
import extensibility

from conftest import edit_payload, git, metrics_of, run_hook, stop_payload, ups_payload

GLOBS = ["*.ts", "**/*.ts", "**/src/**", "**/src/**/*.ts", "src/**", "src/*.ts", "src/**/*.ts", "/src/**",
         "./src/**", "src", "*.{ts,js}", "config.ts", "[!t]*.ts", "**/[!t]*.ts", "src/?.ts"]
FILES = ["config.ts", "t.ts", "src/a.ts", "src/t.ts", "src/lib/a.ts", "src/lib/deep/t.ts", "other/a.ts"]


@pytest.fixture(autouse=True)
def _home_without_user_rules(tmp_path, monkeypatch):
    """A home directory without the user's own rules and guidance."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(extensibility, "_guidance_block", "")
    monkeypatch.setattr(extensibility, "_user_patterns", [])


@pytest.mark.parametrize("glob", GLOBS)
def test_the_wider_reading_never_loses_an_include(glob, tmp_path):
    for f in FILES:
        path = str(tmp_path.joinpath(*f.split("/")))
        if extensibility._glob_match(path.lstrip("/"), (glob,), ()):
            assert extensibility._wider_glob_match(path, (f,), (glob,), ())


@pytest.mark.parametrize("glob,f,now,wider", [
    ("src/**", "src/a.ts", False, True),
    ("src/*.ts", "src/lib/a.ts", False, True),       # `*` still crosses `/`
    ("src/**/*.ts", "src/a.ts", False, True),
    ("**/src/**/*.ts", "src/a.ts", False, True),
    ("**/src/**/*.ts", "src/lib/a.ts", True, True),
    ("/src/**", "src/a.ts", False, True),
    ("*.ts", "src/lib/deep/t.ts", True, True),
    ("src/**", "other/a.ts", False, False),
    ("*.{ts,js}", "config.ts", False, False),
])
def test_readings(glob, f, now, wider, tmp_path):
    path = str(tmp_path.joinpath(*f.split("/")))
    assert extensibility._glob_match(path.lstrip("/"), (glob,), ()) is now
    assert extensibility._wider_glob_match(path, (f,), (glob,), ()) is wider


def _rules(repo, *rules, name="security-patterns.json"):
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / name).write_text(json.dumps({"patterns": [
        dict({"rule_name": f"r{i}", "substrings": ["NEEDLE("], "reminder": "x"}, **r)
        for i, r in enumerate(rules)]}))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "rules")


def _unpack(metrics):
    """The custom rule counts on a Stop row, by name; zeros left out."""
    digits = f"{metrics.get('cr_pack', 0):015d}"
    fields = (("cr_rules", digits[:2]), ("cr_shapes", digits[2:5]), ("cr_gain", digits[5:8]),
              ("cr_loss", digits[8:11]), ("cr_slow_ms", digits[11:]))
    return {k: int(v) for k, v in fields if int(v)}


def _stats(repo, env, files, cwd=None):
    env = {**env, "CLAUDE_PROJECT_DIR": str(repo)}
    run_hook(ups_payload(repo), env)
    outs = []
    for name in files:
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("NEEDLE(1)\n")
        outs.append(run_hook(edit_payload(cwd or repo, p, "NEEDLE(1)\n"), env)[1])
    m = metrics_of(run_hook(stop_payload(repo), env)[1])
    assert not [k for k in m if k.startswith("cr_") and k != "cr_pack"]
    return _unpack(m), outs


def test_rules_the_older_reading_missed(env, workspace):
    _, repo = workspace
    _rules(repo, {"paths": ["src/**"]}, {"paths": ["*.ts"]})
    stats, outs = _stats(repo, env, ["src/a.ts", "src/b.ts"])
    assert stats == {"cr_rules": 2, "cr_shapes": 1, "cr_gain": 2}
    assert all("additionalContext" in o for o in outs)


def test_excludes_the_older_reading_missed(env, workspace):
    _, repo = workspace
    _rules(repo, {"exclude_paths": ["src/**"]})
    stats, outs = _stats(repo, env, ["src/a.ts"])
    assert stats == {"cr_rules": 1, "cr_shapes": 2, "cr_loss": 1}
    assert "additionalContext" not in outs[0]


def test_no_extra_save_of_the_state(env, workspace, monkeypatch, tmp_path):
    import diffstate
    import session_state
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "st"))
    saves = []
    real = session_state.save_state
    monkeypatch.setattr(session_state, "save_state", lambda *a: saves.append(a) or real(*a))
    diffstate.record_touched_path("s9", "/a.ts", {"cr_rules": 1, "cr_gain": 1})
    assert len(saves) == 1
    assert saves[0][1]["custom_rules"] == {"cr_rules": 1, "cr_gain": 1}
    assert saves[0][1]["touched_paths"] == ["/a.ts"]


def test_worktree_outside_the_project(env, workspace, tmp_path):
    _, repo = workspace
    _rules(repo, {"paths": ["src/**"]})
    tree = tmp_path / "tree"
    git(repo, "worktree", "add", "-q", "-b", "side", str(tree))
    extensibility.load_for_session(str(tree))
    stats = extensibility.edit_stats(str(tree / "src" / "a.ts"))
    assert stats["cr_gain"] == 1


def test_they_come_after_the_review_keys(env, workspace):
    _, repo = workspace
    _rules(repo, {"paths": ["src/**"]})
    e = {**env, "CLAUDE_PROJECT_DIR": str(repo)}
    run_hook(ups_payload(repo), e)
    run_hook(edit_payload(repo, repo / "src" / "a.ts", "NEEDLE("), e)
    keys = list(metrics_of(run_hook(stop_payload(repo), e)[1]))
    assert "cr_pack" in keys
    first = min(i for i, k in enumerate(keys) if k.startswith("cr_"))
    assert not [k for k in keys[first:] if not k.startswith(("cr_", "launcher"))]


@pytest.mark.parametrize("rule,bits", [
    ({"paths": ["**/src/**/*.ts"]}, 4),
    ({"paths": ["*.{ts,js}"]}, 8),
    ({"paths": ["/src/**"]}, 16),
    ({"regex": "(a+)+$"}, 32),
    ({"regex": "(a+){2,}$"}, 64),
    ({"regex": "(a+){20}$"}, 64),
    ({"regex": "([A-Za-z0-9+/]{4}){10,}"}, 0),
])
def test_shapes(rule, bits, env, workspace):
    _, repo = workspace
    _rules(repo, rule)
    stats, _ = _stats(repo, env, ["other/a.ts"])
    assert stats.get("cr_shapes", 0) == bits


def test_a_slow_regex_is_timed(env, workspace):
    _, repo = workspace
    _rules(repo, {"substrings": [], "regex": "(a+){2,}$"})
    env = {**env, "CLAUDE_PROJECT_DIR": str(repo)}
    run_hook(ups_payload(repo), env)
    run_hook(edit_payload(repo, repo / "n.txt", "a" * 23 + "!"), env)
    m = metrics_of(run_hook(stop_payload(repo), env)[1])
    assert _unpack(m)["cr_slow_ms"] >= 100


def test_no_custom_rules_no_keys(env, workspace):
    _, repo = workspace
    assert _stats(repo, env, ["src/a.ts"])[0] == {}


def test_reported_once(env, workspace):
    _, repo = workspace
    _rules(repo, {"paths": ["src/**"]})
    assert _stats(repo, env, ["src/a.ts"])[0]
    m = metrics_of(run_hook(stop_payload(repo), env)[1])
    assert not [k for k in m if k.startswith("cr_")]


def test_a_subagent_stop_leaves_them_for_the_turn(env, workspace):
    _, repo = workspace
    _rules(repo, {"paths": ["src/**"]})
    e = {**env, "CLAUDE_PROJECT_DIR": str(repo)}
    run_hook(ups_payload(repo), e)
    run_hook(edit_payload(repo, repo / "src" / "a.ts", "NEEDLE("), e)
    run_hook(stop_payload(repo, event="SubagentStop"), e)
    m = metrics_of(run_hook(stop_payload(repo), e)[1])
    assert _unpack(m)["cr_gain"] == 1


def test_wrong_kind_in_state_does_not_break_the_hook(env, workspace):
    _, repo = workspace
    _rules(repo, {"paths": [5]}, {"paths": ["src/**"]})
    assert _stats(repo, env, ["src/a.ts"])[0]["cr_rules"] == 2


def test_pack_layout_and_caps():
    assert diffstate.custom_rule_pack(
        {"cr_rules": 2, "cr_shapes": 65, "cr_gain": 7, "cr_loss": 3, "cr_slow_ms": 450}
    ) == 2_065_007_003_0450
    biggest = diffstate.custom_rule_pack(
        {"cr_rules": 500, "cr_shapes": 5000, "cr_gain": 5000, "cr_loss": 5000, "cr_slow_ms": 99999})
    assert biggest == 10 ** 15 - 1 and biggest < 2 ** 53
    assert _unpack({"cr_pack": biggest}) == {
        "cr_rules": 99, "cr_shapes": 999, "cr_gain": 999, "cr_loss": 999, "cr_slow_ms": 9999}


@pytest.mark.parametrize("kept", [None, [], "x", {}, {"cr_rules": "2"}, {"cr_gain": -1}, {"cr_gain": True}])
def test_pack_of_nothing_usable_is_zero(kept):
    assert diffstate.custom_rule_pack(kept) == 0
