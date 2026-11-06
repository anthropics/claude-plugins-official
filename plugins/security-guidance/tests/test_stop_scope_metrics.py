"""Stop rows carry one count-only number, `review_scope`, saying how the
reviewed files relate to what the session's edit tools wrote and whether the
turn-start snapshot was a real one."""
import os
import shutil

import pytest

from conftest import (
    STUB_VULN, VULN_PY, edit_payload, metrics_of, run_hook, stop_payload,
    ups_payload,
)

import diffstate

needs_sh = pytest.mark.skipif(os.name == "nt", reason="uses a /bin/sh git shim")


def _stop(repo, env):
    return metrics_of(run_hook(stop_payload(repo), env)[1])


def _turn(repo, env, edits=(), during=None):
    run_hook(ups_payload(repo), env)
    for path in edits:
        run_hook(edit_payload(repo, path), env)
    if during:
        during()
    return _stop(repo, env)


def _no_write_tree_env(tmp_path, hook_env):
    """An env whose `git write-tree` fails, like a snapshot that could not be taken."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    shim = bindir / "git"
    shim.write_text(
        '#!/bin/sh\nfor a in "$@"; do [ "$a" = write-tree ] && exit 1; done\n'
        f'exec "{shutil.which("git")}" "$@"\n')
    shim.chmod(0o755)
    return {**hook_env, "PATH": f"{bindir}{os.pathsep}{hook_env['PATH']}"}


class TestScope:
    def test_edits_outside_repo_review_of_a_file_they_did_not_write(self, hook_env, workspace):
        ws, repo = workspace
        m = _turn(repo, hook_env, edits=[ws / "notes.md"],
                  during=lambda: (repo / "other.py").write_text(VULN_PY))
        assert m["files_reviewed"] == 1 and m["review_scope"] == 30001

    def test_edit_inside_repo(self, hook_env, workspace):
        _, repo = workspace
        m = _turn(repo, hook_env, edits=[repo / "app.py"],
                  during=lambda: (repo / "app.py").write_text(VULN_PY))
        assert m["files_reviewed"] == 1 and m["review_scope"] == 10000

    def test_relative_edit_path_is_read_against_the_session_cwd(self, hook_env, workspace):
        _, repo = workspace
        m = _turn(repo, hook_env, edits=["app.py"],
                  during=lambda: (repo / "app.py").write_text(VULN_PY))
        assert m["files_reviewed"] == 1 and m["review_scope"] == 10000

    def test_mixed_edits_and_a_file_changed_by_other_means(self, hook_env, workspace):
        ws, repo = workspace

        def during():
            (repo / "app.py").write_text(VULN_PY)
            (repo / "gen.py").write_text(VULN_PY)
        m = _turn(repo, hook_env, edits=[ws / "notes.md", repo / "app.py"], during=during)
        assert m["files_reviewed"] == 2 and m["review_scope"] == 20001

    def test_no_edit_tool_paths(self, hook_env, workspace):
        _, repo = workspace
        m = _turn(repo, hook_env, during=lambda: (repo / "app.py").write_text(VULN_PY))
        assert m["files_reviewed"] == 1 and m["review_scope"] == 1

    def test_outside_only_turn_with_nothing_to_review(self, hook_env, workspace):
        ws, repo = workspace
        m = _turn(repo, hook_env, edits=[ws / "notes.md"])
        assert m["skipped"] is True and m["review_scope"] == 30000

    def test_skipped_review_counts_over_the_review_set(self, hook_env, workspace):
        _, repo = workspace
        m = _turn(repo, hook_env, during=lambda: (repo / "notes.txt").write_text("x\n"))
        assert m["skipped"] is True and m["review_scope"] == 1

    def test_second_review_of_the_same_turn_still_knows_the_edits(self, hook_env, workspace):
        _, repo = workspace
        m = _turn(repo, hook_env, edits=[repo / "app.py"],
                  during=lambda: (repo / "app.py").write_text(VULN_PY))
        assert m["review_scope"] == 10000
        m = _stop(repo, hook_env)  # a rewake: no new prompt, same baseline
        assert m["files_reviewed"] == 1 and m["review_scope"] == 10000
        # The next prompt starts a new count.
        m = _turn(repo, hook_env, during=lambda: (repo / "gen.py").write_text(VULN_PY))
        assert m["files_reviewed"] == 1 and m["review_scope"] == 1

    def test_no_key_outside_a_repo(self, hook_env, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        m = _turn(plain, hook_env, edits=[plain / "a.py"],
                  during=lambda: (plain / "a.py").write_text(VULN_PY))
        assert m["skipped"] is True and "review_scope" not in m

    def test_unreadable_path_does_not_stop_the_review(self, hook_env, workspace):
        _, repo = workspace
        m = _turn(repo, hook_env, edits=[str(repo / "a\ud800b.py"), repo / "app.py"],
                  during=lambda: (repo / "app.py").write_text(VULN_PY))
        assert m["files_reviewed"] == 1
        if os.name == "nt":
            # Windows paths can hold a lone surrogate: it is one more file
            # in the repo.
            assert m["review_scope"] == 10000
        else:
            assert "review_scope" not in m


class TestSnapshot:
    def test_no_prompt_hook_means_no_snapshot(self, hook_env, workspace):
        _, repo = workspace
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py"), hook_env)
        m = _stop(repo, hook_env)
        assert m["files_reviewed"] == 1 and m["review_scope"] == 310000

    @needs_sh
    def test_failed_snapshot_is_counted(self, hook_env, workspace, tmp_path):
        ws, repo = workspace
        (repo / "app.py").write_text(VULN_PY)  # uncommitted work from before the turn
        m = _turn(repo, _no_write_tree_env(tmp_path, hook_env), edits=[ws / "notes.md"])
        assert m["files_reviewed"] == 1 and m["review_scope"] == 130001
        # The next prompt takes a real snapshot and the flag is gone.
        m = _turn(repo, hook_env, edits=[repo / "app.py"],
                  during=lambda: (repo / "app.py").write_text(VULN_PY + "# more\n"))
        assert m["files_reviewed"] == 1 and m["review_scope"] == 10000

    @needs_sh
    def test_flag_follows_the_snapshot_taken_after_a_finding(self, hook_env, stub_api,
                                                             workspace, tmp_path):
        _, repo = workspace
        broken = _no_write_tree_env(tmp_path, hook_env)
        stub_api.vulns = [STUB_VULN]
        # Good snapshot at the prompt; the one taken after the finding fails.
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py"), hook_env)
        m = _stop(repo, broken)
        assert m["vulns_found"] == 1 and m["review_scope"] == 10000
        (repo / "app.py").write_text(VULN_PY + "# fix\n")
        run_hook(edit_payload(repo, repo / "app.py"), hook_env)
        m = _stop(repo, hook_env)
        assert m["review_scope"] == 110000
        # That Stop took a real one again.
        (repo / "app.py").write_text(VULN_PY + "# fix 2\n")
        run_hook(edit_payload(repo, repo / "app.py"), hook_env)
        m = _stop(repo, hook_env)
        assert m["review_scope"] == 10000


class TestCode:
    def _code(self, root, cwd, touched, files, fail=0):
        scope, inside = diffstate.touched_scope(root, cwd, touched)
        return diffstate.review_scope_code(root, scope, inside, files, fail)

    def test_repo_at_the_filesystem_root(self):
        root = os.path.abspath(os.sep)
        assert self._code(root, root, [os.path.join(root, "x.py")], ["x.py", "y.py"]) == 10001

    def test_names_that_only_start_like_a_parent_dir(self, tmp_path):
        root = str(tmp_path)
        assert self._code(root, root, [str(tmp_path / "..hidden.py")], ["..hidden.py"], 2) == 210000

    def test_untouched_count_is_capped(self, tmp_path):
        files = [f"f{i}.py" for i in range(12000)]
        assert self._code(str(tmp_path), "", [], files) == 9999

    def test_absolute_and_relative_file_names_count_the_same(self, tmp_path):
        root = str(tmp_path)
        touched = [str(tmp_path / "a.py")]
        assert self._code(root, root, touched, ["a.py", "b.py"]) == 10001
        assert self._code(root, root, touched, [str(tmp_path / "a.py"), str(tmp_path / "b.py")]) == 10001
