"""The Stop review counts the data files it sends whose name says they hold
secrets. Measurement only: the files are reviewed as before."""
import pytest

from conftest import (
    STUB_VULN, VULN_PY, make_repo, metrics_of, run_hook, stop_payload, ups_payload,
)

import gitutil


@pytest.mark.parametrize("path", [
    "secrets.yml",
    "config/secrets.yaml",
    "secrets.prod.json",
    ".secrets.toml",
    "Secrets.YML",
    "credentials.json",
    "client_secret.json",
    "keys/service-account.json",
    "service_account.json",
    "terraform/secrets.tfvars",
    "client-secret.json",
    "client_secret_1234-abc.apps.googleusercontent.com.json",
    "serviceAccountKey.json",
])
def test_secret_named_data_files(path):
    assert gitutil._is_secret_named(path)


@pytest.mark.parametrize("path", [
    "secrets.py",
    "src/credentials.ts",
    "secrets_manager.yaml",
    "app-secrets.json",
    "docs/secrets.md",
    "secrets",
    "config.yaml",
    "package.json",
    "secrets/config.yaml",
    "secrets.example.yml",
    "credentials.sample.json",
    "secrets.schema.json",
    "secrets.enc.yaml",
    "secrets.sops.yaml",
    ".json",
])
def test_other_files_are_not_counted(path):
    assert not gitutil._is_secret_named(path)


def _review(tmp_path, hook_env, files):
    repo = make_repo(tmp_path / "repo")
    run_hook(ups_payload(repo), hook_env)
    for name, body in files.items():
        (repo / name).write_text(body)
    return run_hook(stop_payload(repo), hook_env)


def test_stop_hook_counts_secret_named_files_and_still_reviews_them(tmp_path, hook_env, stub_api):
    _rc, stdout, _err = _review(tmp_path, hook_env, {
        "secrets.yml": "db:\n  password: example\n",
        "credentials.json": '{"token": "example"}\n',
        "app.py": "print(1)\n",
    })
    m = metrics_of(stdout)
    assert m.get("secret_named_reviewed") == 2
    assert m.get("files_reviewed") == 3
    assert "/v1/messages" in stub_api.calls


def test_count_is_on_the_findings_row_too(tmp_path, hook_env, stub_api):
    stub_api.vulns = [STUB_VULN]
    rc, stdout, _err = _review(tmp_path, hook_env, {
        "secrets.yml": "db:\n  password: example\n",
        "app.py": VULN_PY,
    })
    assert rc == 2
    assert metrics_of(stdout).get("secret_named_reviewed") == 1


def test_no_key_when_no_such_file_is_reviewed(tmp_path, hook_env, stub_api):
    _rc, stdout, _err = _review(tmp_path, hook_env, {"app.py": "print(1)\n"})
    m = metrics_of(stdout)
    assert m.get("files_reviewed") == 1
    assert "secret_named_reviewed" not in m


def test_count_is_on_the_failed_review_row(tmp_path, hook_env, stub_api):
    stub_api.status = 500
    _rc, stdout, _err = _review(tmp_path, hook_env, {"secrets.yml": "a: b\n"})
    m = metrics_of(stdout)
    assert m.get("review_failed") is True
    assert m.get("secret_named_reviewed") == 1
