"""ANTHROPIC_CUSTOM_HEADERS reach every call the plugin makes."""
from conftest import (
    STUB_VULN, VULN_PY, edit_payload, run_hook, stop_payload, ups_payload,
)

import llm

GATEWAY_KEY = ("x-litellm-api-key", "Bearer sk-gateway")


class TestCustomHeaders:
    def test_parsed_like_claude_code(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS",
                           "x-litellm-api-key: Bearer sk-1\r\n"
                           "X-Tenant:  acme:eu \n"
                           "no colon here\n"
                           ": no name\n"
                           "\n"
                           "X-Empty:")
        assert llm._custom_headers() == [
            ("x-litellm-api-key", "Bearer sk-1"), ("X-Tenant", "acme:eu"), ("X-Empty", ""),
        ]

    def test_unsendable_lines_are_skipped(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS",
                           "bad name: x\nX-Ok: 1\nX-Uni: caf\u00e9\u2603\nX-Cr: a\rb")
        assert llm._custom_headers() == [("X-Ok", "1")]

    def test_sent_with_the_plugin_credentials(self, monkeypatch):
        monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", "oauth")
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", "x-litellm-api-key: k")
        h = llm._build_auth_headers(use_token=True)
        assert h["x-litellm-api-key"] == "k"
        assert h["Authorization"] == "Bearer oauth"

    def test_custom_line_wins_over_the_same_header(self, monkeypatch):
        monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", "oauth")
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", "authorization: Bearer gw")
        h = llm._build_auth_headers(use_token=True)
        assert [v for k, v in h.items() if k.lower() == "authorization"] == ["Bearer gw"]

    def test_custom_beta_lines_are_not_sent(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", "anthropic-beta: extra-1\nX-Ok: 1")
        h = llm._build_auth_headers(use_token=False)
        assert h["anthropic-beta"] == "structured-outputs-2025-11-13"
        assert h["X-Ok"] == "1"

    def test_without_custom_headers_only_the_plugin_headers_are_sent(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_CUSTOM_HEADERS", raising=False)
        assert set(llm._build_auth_headers(use_token=False)) == {
            "Content-Type", "anthropic-version", "x-api-key", "anthropic-beta"}

    def test_stop_review_reaches_a_header_keyed_gateway(self, env, gateway, workspace):
        """Every plugin call (model lookup and review) carries the gateway
        key, and the review finds the vuln."""
        _, repo = workspace
        gateway.required = GATEWAY_KEY
        gateway.vulns = [STUB_VULN]
        e = {**env, "ANTHROPIC_CUSTOM_HEADERS": f"{GATEWAY_KEY[0]}: {GATEWAY_KEY[1]}"}
        run_hook(ups_payload(repo), e)
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py", VULN_PY), e)
        rc, so, se = run_hook(stop_payload(repo), e)
        assert rc == 2, (so, se)
        assert "command_injection" in se
        calls = [(m, p.split("?")[0]) for m, p, _ in gateway.requests]
        assert ("GET", "/v1/models") in calls and ("POST", "/v1/messages") in calls
        for method, path, headers in gateway.requests:
            if path.startswith("/v1/"):
                assert headers.get(GATEWAY_KEY[0]) == GATEWAY_KEY[1], (method, path)
