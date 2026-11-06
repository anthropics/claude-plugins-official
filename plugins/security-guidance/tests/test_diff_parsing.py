import os
import subprocess

from conftest import GIT_ENV, git, make_repo

import gitutil

VULN = "import os\nos.system(input())\n"


def staged_diff(repo):
    r = subprocess.run(
        [*gitutil.GIT_CMD, "diff", "--cached", "--no-color"], cwd=repo,
        capture_output=True, env={**os.environ, **GIT_ENV},
    )
    assert r.returncode == 0, r.stderr
    return r.stdout.decode("utf-8", errors="replace")


def stage(tmp_path, files):
    repo = make_repo(tmp_path / "repo")
    for name, content in files.items():
        (repo / name).write_text(content)
    git(repo, "add", "-A")
    return staged_diff(repo)


class TestEmbeddedHeaderText:
    SOURCE = (
        'HEADER = """\n'
        "diff --git a/other.py b/other.py\n"
        '"""\n'
        "import os\n"
        "os.system(input())  # AFTER_EMBEDDED_HEADER\n"
    )

    def test_content_after_embedded_header_text_is_kept(self, tmp_path):
        files = dict(gitutil.parse_diff_into_files(stage(tmp_path, {"embed.py": self.SOURCE})))
        assert list(files) == ["embed.py"]
        assert "AFTER_EMBEDDED_HEADER" in files["embed.py"]

    def test_embedded_header_text_adds_no_path(self, tmp_path):
        diff = stage(tmp_path, {"embed.py": self.SOURCE})
        assert gitutil.extract_file_paths_from_diff(diff) == ["embed.py"]

    def test_following_file_is_still_parsed(self, tmp_path):
        diff = stage(tmp_path, {"embed.py": self.SOURCE, "z_next.py": VULN})
        assert [p for p, _ in gitutil.parse_diff_into_files(diff)] == ["embed.py", "z_next.py"]


class TestQuotedPaths:
    def test_names_git_quotes_are_reviewed(self, tmp_path):
        names = ['we"ird.py', "tab\there.py", "back\\slash.py", "café.py", "plain.py"]
        diff = stage(tmp_path, {n: VULN for n in names})
        assert '"a/we\\"ird.py"' in diff  # git did quote it
        parsed = gitutil.parse_diff_into_files(diff)
        assert sorted(p for p, _ in parsed) == sorted(names)
        assert all("os.system" in c for _, c in parsed)
        assert sorted(gitutil.extract_file_paths_from_diff(diff)) == sorted(names)

    def test_rename_to_a_quoted_name(self, tmp_path):
        repo = make_repo(tmp_path / "repo", {"plain.py": VULN * 20})
        git(repo, "mv", "plain.py", 'qu"ote.py')
        (repo / 'qu"ote.py').write_text(VULN * 20 + "eval(input())\n")
        git(repo, "add", "-A")
        diff = staged_diff(repo)
        assert 'a/plain.py "b/qu\\"ote.py"' in diff
        assert [p for p, _ in gitutil.parse_diff_into_files(diff)] == ['qu"ote.py']

    def test_octal_escapes_decode_as_utf8(self):
        header = '"a/caf\\303\\251.py" "b/caf\\303\\251.py"'
        assert gitutil._parse_diff_header(header) == ("café.py", "café.py")

    def test_unterminated_quote_is_skipped(self):
        assert gitutil._parse_diff_header('"a/x.py b/x.py') is None


class TestCommitOutput:
    def test_git_show_preamble_is_ignored(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        (repo / "app.py").write_text(VULN)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "diff --git a/fake.py b/fake.py")
        r = subprocess.run(
            [*gitutil.GIT_CMD, "show", "-p", "--no-color", "HEAD", "--"], cwd=repo,
            capture_output=True, env={**os.environ, **GIT_ENV},
        )
        parsed = gitutil.parse_diff_into_files(r.stdout.decode())
        assert [p for p, _ in parsed] == ["app.py"]


def test_unparsed_headers_are_counted_for_telemetry():
    import gitutil
    gitutil._unparsed_diff_headers.clear()
    diff = 'diff --git "a/x.py b/x.py\n@@ -0,0 +1 @@\n+x = 1\n'
    assert gitutil.parse_diff_into_files(diff) == []
    assert gitutil.extract_file_paths_from_diff(diff) == []
    assert len(gitutil._unparsed_diff_headers) == 1
    gitutil._unparsed_diff_headers.clear()
