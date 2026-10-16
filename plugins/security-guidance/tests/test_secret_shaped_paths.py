import os
import subprocess

import pytest

from conftest import (
    GIT_ENV, git, make_repo, metrics_of, run_hook, stop_payload, ups_payload,
)

import gitutil


@pytest.mark.parametrize("path", [
    "dot_config/private_example/encrypted_private_token",
    "encrypted_private_dot_netrc",
    "home/encrypted_config.yaml",
    "id_ed25519",
    ".ssh/id_rsa",
    "private_dot_ssh/private_id_ecdsa",
    "deploy_rsa",
    "keys/github_ed25519",
    ".env.production.json",
    ".env.local.yaml",
    "config/dot_env.toml",
    "private_dot_netrc",
    "dot_aws/credentials",
    "Deploy_RSA",
    ".credentials.json",
    ".claude/.credentials.json",
    "private_dot_claude/private_dot_credentials.json",
    ".claude.json",
    "dot_claude.json",
])
def test_secret_shaped_names_are_not_reviewable(path):
    assert gitutil._is_secret_shaped(path)
    assert not gitutil._is_reviewable_source(path)


@pytest.mark.parametrize("path", [
    "src/private_api.py",
    "src/id_generator.py",
    "lib/encrypted_store.py",
    "crypto/rsa.py",
    "auth/sign_rsa.go",
    "app/credentials.py",
    "scripts/run_migrations.sh",
    "dot_product.py",
    "config/environment.json",
    "bin/deploy",
    "Dockerfile.dev",
    "executable_backup.sh",
    "config/credentials.json",
    "src/claude.json",
])
def test_ordinary_source_stays_reviewable(path):
    assert not gitutil._is_secret_shaped(path)
    assert gitutil._is_reviewable_source(path)


def _staged_diff(repo):
    r = subprocess.run(
        [*gitutil.GIT_CMD, "diff", "--cached", "--no-color", "-M"], cwd=repo,
        capture_output=True, env={**os.environ, **GIT_ENV},
    )
    assert r.returncode == 0, r.stderr
    return r.stdout.decode("utf-8", errors="replace")


def test_secret_content_is_left_out_of_the_parsed_diff(tmp_path):
    repo = make_repo(tmp_path / "repo")
    (repo / "encrypted_private_token").write_text("CIPHERTEXT_BODY\n")
    (repo / "id_ed25519").write_text("PRIVATE_KEY_BODY\n")
    (repo / ".env.production.json").write_text('{"API_KEY": "ENV_SECRET_BODY"}\n')
    (repo / "app.py").write_text("import os\nos.system(input())\n")
    git(repo, "add", "-A")
    diff = _staged_diff(repo)
    parsed = gitutil.parse_diff_into_files(diff)
    assert [p for p, _ in parsed] == ["app.py"]
    assert "_BODY" not in "".join(c for _, c in parsed)
    assert gitutil.extract_file_paths_from_diff(diff) == ["app.py"]


def test_rename_away_from_a_secret_name_is_left_out(tmp_path):
    body = "".join(f"KEY_{i}=SECRET_VALUE_{i}\n" for i in range(30))
    repo = make_repo(tmp_path / "repo", {"deploy_rsa": body})
    git(repo, "mv", "deploy_rsa", "notes.sh")
    (repo / "notes.sh").write_text(body + "KEY_NEW=SECRET_VALUE_NEW\n")
    git(repo, "add", "-A")
    diff = _staged_diff(repo)
    assert "rename from deploy_rsa" in diff
    assert gitutil.parse_diff_into_files(diff) == []
    assert gitutil.extract_file_paths_from_diff(diff) == []


def test_stop_hook_reports_how_many_files_it_left_out(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo")
    run_hook(ups_payload(repo), hook_env)
    (repo / "id_ed25519").write_text("-----BEGIN OPENSSH PRIVATE KEY-----\n")
    (repo / ".env.local").write_text("TOKEN=abc\n")
    _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
    assert metrics_of(stdout).get("secret_shaped_skipped") == 2
    assert stub_api.calls == []


@pytest.mark.parametrize("name", [".credentials.json", ".claude.json"])
def test_claude_code_files_rewritten_during_the_turn_are_not_sent(tmp_path, hook_env, stub_api, name):
    repo = make_repo(tmp_path / "repo")
    (repo / name).write_text('{"accessToken": "old"}\n')
    run_hook(ups_payload(repo), hook_env)
    (repo / name).write_text('{"accessToken": "new-and-longer"}\n')
    later = (repo / name).stat().st_mtime + 5
    os.utime(repo / name, (later, later))
    _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
    assert metrics_of(stdout).get("secret_shaped_skipped") == 1
    assert stub_api.calls == []
