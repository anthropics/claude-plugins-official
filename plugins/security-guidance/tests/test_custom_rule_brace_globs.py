"""`{a,b}` in a custom rule's glob means either."""
import fnmatch
import itertools
import time

import pytest

import extensibility

from test_custom_rule_path_globs import _hits, _module_state, _rule  # noqa: F401

CASES = [
    # glob, file inside the project, applies
    ("*.{ts,tsx}", "src/a.ts", True),
    ("*.{ts,tsx}", "src/lib/a.tsx", True),
    ("*.{ts,tsx}", "src/a.js", False),
    ("*.{ts,tsx}", "src/a.ts.bak", False),
    ("**/*.{ts,tsx}", "config.ts", True),
    ("**/*.{ts,tsx}", "src/lib/a.tsx", True),
    ("**/*.{ts,tsx}", "src/a.py", False),
    ("{src,lib}/**", "src/x/a.py", True),
    ("{src,lib}/**", "lib/a.py", True),
    ("{src,lib}/**", "other/a.py", False),
    ("src/{a,b}/**/*.{ts,js}", "src/b/a.js", True),
    ("src/{a,b}/**/*.{ts,js}", "src/c/a.js", False),
    ("./{src,lib}/*.ts", "lib/a.ts", True),
    ("*.{ts,{m,c}ts}", "a.mts", True),
    ("*.{ts,{m,c}ts}", "a.xts", False),
    ("*.{test,spec}.ts", "src/a.spec.ts", True),
    ("*.{ts, tsx}", "a.tsx", True),
    # An empty option before `/` does not turn the glob into "every file".
    ("{src,}/**", "src/a.ts", True),
    ("{src,}/**", "lib/a.ts", False),
    ("{,src}/*.ts", "lib/a.ts", False),
    ("{{,x},src}{,y}/**", "lib/a.ts", False),
    # More combinations than anyone counts.
    ("{src,lib,app,packages}/**/*.{js,jsx,ts,tsx,mjs,cjs,mts,cts,vue}", "app/x/a.vue", True),
    ("config{,.local}.ts", "config.ts", True),
    ("config{,.local}.ts", "config.local.ts", True),
    # A set keeps its braces, and one option is not a choice.
    ("[{,}].ts", "{.ts", True),
    ("[{,}].ts", "ts", False),
    ("a{b}.ts", "a{b}.ts", True),
    ("a{b}.ts", "ab.ts", False),
    ("*.{ts,tsx", "a.ts", False),
    # An option with no folder in it is about the file name.
    ("{test*,src/**}", "tests/x/a.py", False),
    ("{test*,src/**}", "x/test_a.py", True),
    ("{test*,src/**}", "src/a.py", True),
]


@pytest.fixture(autouse=True)
def _fresh_forms(monkeypatch):
    monkeypatch.setattr(extensibility, "_forms_cache", {})
    monkeypatch.setattr(extensibility, "_brace_forms_left", extensibility._BRACE_BUDGET)


@pytest.mark.parametrize("glob,rel,applies", CASES)
def test_braces_in_paths(glob, rel, applies, tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=[glob])
    assert bool(_hits(project, rel)) is applies


@pytest.mark.parametrize("glob,rel,applies", CASES)
def test_braces_in_exclude_paths(glob, rel, applies, tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, exclude=[glob])
    assert bool(_hits(project, rel)) is not applies


def test_an_exclude_silences_only_its_own_rule(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, exclude=["*.{js,ts}"])
    extensibility.load_for_session(str(project))
    import security_reminder_hook as hook
    hits = [r for r, _ in hook.check_patterns(str(project / "a.js"), "NEEDLE(eval(x))\n")]
    assert "eval_injection" in hits and "user:r" not in hits


@pytest.mark.parametrize("glob", ["{a,b}.ts", "*.{ts,tsx}", "x{,y}", "{a,{b,c}}"])
def test_a_name_with_the_braces_in_it_still_matches(glob):
    name = glob.replace("*", "z")
    assert extensibility._wider_glob_match("/p/" + name, (), (glob,), ())


@pytest.mark.parametrize("glob,forms", [
    ("*.ts", {"*.ts"}),
    ("{a,b}", {"{a,b}", "a", "b"}),
    ("{{a,b}}", {"{{a,b}}", "{a}", "{b}"}),
    ("{a,b}{c,d}", {"{a,b}{c,d}", "ac", "ad", "bc", "bd"}),
    ("{a,}", {"{a,}", "a"}),
    ("{a,}/b", {"{a,}/b", "a/b"}),
    ("{/a,/b}/c", {"{/a,/b}/c", "/a/c", "/b/c"}),
    ("x/{a,}/b", {"x/{a,}/b", "x/a/b", "x//b"}),
    ("{,}", {"{,}"}),
    ("a}{b,c}", {"a}{b,c}", "a}b", "a}c"}),
    ("{x{a,b}", {"{x{a,b}", "{xa", "{xb"}),
    ("[{a,b]{c,d}", {"[{a,b]{c,d}", "[{a,b]c", "[{a,b]d"}),
    ("[!]{]{c,d}", {"[!]{]{c,d}", "[!]{]c", "[!]{]d"}),
    ("[{a,b}", {"[{a,b}", "[a", "[b"}),
    ("", {""}),
])
def test_forms(glob, forms):
    assert set(extensibility._brace_forms(glob)) == forms


def test_up_to_the_cap_is_expanded_and_over_it_is_not():
    cap = extensibility._MAX_BRACE_FORMS
    at = "{" + ",".join(map(str, range(cap))) + "}"
    assert len(extensibility._brace_forms(at)) == cap + 1
    assert extensibility._brace_forms(at[:-1] + ",x}") is None


def _over_cap():
    return "src/*.{" + ",".join(f"e{i}" for i in range(extensibility._MAX_BRACE_FORMS)) + ",ts}"


def test_an_over_cap_glob_is_read_as_written_and_the_log_names_the_rule(tmp_path, monkeypatch):
    log = []
    monkeypatch.setattr(extensibility, "debug_log", log.append)
    project = _rule(tmp_path, monkeypatch, include=[_over_cap(), "lib/*.{ts,js}"])
    assert not _hits(project, "src/a.ts")
    assert _hits(project, "lib/a.ts")
    assert [m for m in log if "too many combinations" in m and " r:" in m]


def test_the_budget_is_shared_by_all_rules_and_starts_again_each_load(tmp_path, monkeypatch):
    monkeypatch.setattr(extensibility, "_BRACE_BUDGET", 5)
    project = _rule(tmp_path, monkeypatch, include=["a.{ts,js}", "b.{ts,js}"])
    for _ in range(2):
        assert _hits(project, "a.ts")
        assert not _hits(project, "b.ts")


def test_plain_globs_need_no_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(extensibility, "_BRACE_BUDGET", 0)
    project = _rule(tmp_path, monkeypatch, include=["src/**/*.ts", "a{b}.py"])
    assert _hits(project, "src/a.ts") and _hits(project, "a{b}.py")


@pytest.mark.parametrize("glob", [
    "{a,b}" * 200,
    "{" * 20000 + "a,b" + "}" * 20000,
    "{a," * 20000,
    "[" * 20000 + "{a,b}",
    "[{" * 10000 + "]" + "{a,b}" * 20,
    "{" + "a," * 50000 + "}",
])
def test_a_hostile_glob_is_quick(glob):
    started = time.perf_counter()
    extensibility._brace_forms(glob)
    assert time.perf_counter() - started < 5


@pytest.mark.parametrize("glob", [
    "**/r/**/x/**/y/**/z{a,b}{c,d}{e,f}{g,h}{i,j}/**",
    "*{*a,*b}*{*c,*d}*{*e,*f}*{*g,*h}*",
])
def test_a_project_full_of_hostile_rules_is_bounded(glob):
    """Whole matching cost, no literal end to help, 500 different globs."""
    globs = tuple(f"{i}{glob}" for i in range(500))
    plain = tuple(g.replace("{", "(").replace("}", ")") for g in globs)
    started = time.perf_counter()
    sizes = [len(extensibility._glob_forms(g)) - len(extensibility._glob_forms(p))
             for g, p in zip(globs, plain)]
    assert 0 < sum(sizes) <= extensibility._BRACE_BUDGET
    assert not extensibility._wider_glob_match("/p/src/lib/a.ts", ("src/lib/a.ts",), globs, ())
    assert time.perf_counter() - started < 20


def test_many_globs_that_do_not_fit_are_given_up_on_quickly():
    started = time.perf_counter()
    for i in range(5000):
        extensibility._glob_forms(f"{i}" + "{a,b}" * 190)
    assert time.perf_counter() - started < 10


def _matches(name, glob):
    """One glob against one file name, through the plugin's matcher."""
    return any(name.endswith(tail) and fnmatch.fnmatchcase(name, form)
               for form, tail, _ in extensibility._glob_forms(glob) if form == glob)


def test_the_quick_check_agrees_with_fnmatch():
    globs = ["".join(g) for n in range(5) for g in itertools.product("a*?[]!", repeat=n)]
    for glob in globs:
        for name in ("", "a", "aa", "ab", "a-b", "a]", "]", "[a", "!", "a!"):
            assert _matches(name, glob) == fnmatch.fnmatchcase(name, glob), (name, glob)
