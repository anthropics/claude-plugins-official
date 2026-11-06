"""A call that got no HTTP response reports why, as `net_err`."""
import asyncio
import errno
import http.client
import socket
import ssl
import sys
import types
import urllib.error

import pytest

from conftest import VULN_PY, metrics_of, run_hook, stop_payload, ups_payload

import _base
import llm
import security_reminder_hook as hook


def _cert_error(code):
    e = ssl.SSLCertVerificationError(1, "certificate verify failed")
    e.verify_code = code
    return e


class TestClass:
    @pytest.mark.parametrize("exc, expected", [
        (urllib.error.URLError(_cert_error(20)), (llm.NET_ERR_CERT_VERIFY, 20)),
        (urllib.error.URLError(_cert_error(19)), (llm.NET_ERR_CERT_VERIFY, 19)),
        (urllib.error.URLError(_cert_error(0)), (llm.NET_ERR_CERT_VERIFY, 0)),
        (urllib.error.URLError(ssl.SSLError(1, "wrong version number")), (llm.NET_ERR_TLS, 0)),
        # A default context that cannot be built is raised bare, before any connection.
        (ssl.SSLError(1, "[ASN1] nested asn1 error"), (llm.NET_ERR_TLS, 0)),
        (urllib.error.URLError(socket.gaierror(-2, "Name or service not known")), (llm.NET_ERR_DNS, 0)),
        (urllib.error.URLError(ConnectionRefusedError(errno.ECONNREFUSED, "refused")), (llm.NET_ERR_CONNECT, 0)),
        (urllib.error.URLError(OSError(errno.ENETUNREACH, "unreachable")), (llm.NET_ERR_CONNECT, 0)),
        (http.client.RemoteDisconnected("closed without response"), (llm.NET_ERR_CONNECT, 0)),
        (TimeoutError("The read operation timed out"), (llm.NET_ERR_TIMEOUT, 0)),
        (urllib.error.URLError(socket.timeout("timed out")), (llm.NET_ERR_TIMEOUT, 0)),
        (urllib.error.URLError(OSError("Tunnel connection failed: 403 Forbidden")), (llm.NET_ERR_PROXY, 0)),
        (urllib.error.URLError(OSError("Tunnel connection failed: 504 Gateway Timed Out")),
         (llm.NET_ERR_PROXY, 0)),
        (urllib.error.URLError("unknown url type"), (llm.NET_ERR_OTHER, 0)),
        (http.client.IncompleteRead(b"x"), (llm.NET_ERR_OTHER, 0)),
        (http.client.BadStatusLine("x"), (llm.NET_ERR_OTHER, 0)),
        (ValueError("step timed out"), (0, 0)),
        (UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"), (0, 0)),
    ])
    def test_class_and_verify_code(self, exc, expected):
        assert llm._net_error_class(exc) == expected

    def test_code_packs_class_verify_code_and_flags(self, monkeypatch):
        monkeypatch.setattr(llm, "_net_error_flags", lambda tls: 5 if tls else 2)
        assert llm._net_error_code(urllib.error.URLError(_cert_error(20))) == 1 + 2000 + 50000
        assert llm._net_error_code(urllib.error.URLError(socket.gaierror(-2, "x"))) == 3 + 20000

    def test_no_code_and_no_setup_checks_for_an_exception_that_is_not_a_network_failure(
            self, monkeypatch):
        monkeypatch.setattr(llm, "_net_error_flags", lambda tls: pytest.fail("checked"))
        assert llm._net_error_code(ValueError("x")) == 0

    def test_a_setup_check_that_raises_keeps_the_class(self, monkeypatch):
        def boom(tls):
            raise RuntimeError("x")
        monkeypatch.setattr(llm, "_net_error_flags", boom)
        assert llm._net_error_code(urllib.error.URLError(_cert_error(20))) == 2001


class TestFlags:
    @pytest.fixture(autouse=True)
    def _clean(self, monkeypatch, tmp_path):
        for name in ("NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "SSL_CERT_DIR"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.example.com")
        monkeypatch.setattr(llm.urllib.request, "getproxies", lambda: {})
        monkeypatch.setattr(llm.sys, "platform", "darwin")
        self.cafile = tmp_path / "cert.pem"
        self.cafile.write_text("-----BEGIN CERTIFICATE-----\n")
        self.capath = tmp_path / "certs"
        self.capath.mkdir()

    def _paths(self, monkeypatch, cafile, capath):
        monkeypatch.setattr(ssl, "get_default_verify_paths", lambda: ssl.DefaultVerifyPaths(
            cafile, capath, "SSL_CERT_FILE", str(self.cafile), "SSL_CERT_DIR", str(self.capath)))

    def test_no_ca_file_and_an_empty_directory(self, monkeypatch):
        self._paths(monkeypatch, None, str(self.capath))
        assert llm._net_error_flags(True) == 1
        self._paths(monkeypatch, None, None)
        assert llm._net_error_flags(True) == 1

    def test_an_empty_ca_file_counts_as_none(self, monkeypatch):
        self.cafile.write_text("")
        self._paths(monkeypatch, str(self.cafile), None)
        assert llm._net_error_flags(True) == 1

    def test_a_ca_file_or_a_filled_directory_is_not_flagged(self, monkeypatch):
        self._paths(monkeypatch, str(self.cafile), str(self.capath))
        assert llm._net_error_flags(True) == 0
        (self.capath / "0a1b2c3d.0").write_text("x")
        self._paths(monkeypatch, None, str(self.capath))
        assert llm._net_error_flags(True) == 0

    def test_windows_is_not_flagged_for_its_files(self, monkeypatch):
        monkeypatch.setattr(llm.sys, "platform", "win32")
        self._paths(monkeypatch, None, None)
        assert llm._net_error_flags(True) == 0

    def test_tls_variables(self, monkeypatch):
        self._paths(monkeypatch, str(self.cafile), None)
        monkeypatch.setenv("NODE_EXTRA_CA_CERTS", "/x/ca.pem")
        assert llm._net_error_flags(True) == 4
        monkeypatch.setenv("SSL_CERT_DIR", "/x")
        assert llm._net_error_flags(True) == 12
        # Not read for a failure that is not about TLS.
        assert llm._net_error_flags(False) == 0

    def test_proxy_for_the_url_scheme(self, monkeypatch):
        monkeypatch.setattr(llm.urllib.request, "proxy_bypass", lambda host: False)
        monkeypatch.setattr(llm.urllib.request, "getproxies", lambda: {"https": "http://proxy:8080"})
        assert llm._net_error_flags(False) == 2
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://gateway.internal:4000")
        assert llm._net_error_flags(False) == 0
        monkeypatch.setattr(llm.urllib.request, "getproxies", lambda: {"http": "http://proxy:8080"})
        assert llm._net_error_flags(False) == 2

    def test_proxy_bypass_is_asked_with_the_port(self, monkeypatch):
        asked = []
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://gw.internal:8443/base")
        monkeypatch.setattr(llm.urllib.request, "getproxies", lambda: {"https": "http://proxy:8080"})
        monkeypatch.setattr(llm.urllib.request, "proxy_bypass", lambda host: asked.append(host) or True)
        assert llm._net_error_flags(False) == 0
        assert asked == ["gw.internal:8443"]


@pytest.fixture
def direct(monkeypatch, tmp_path):
    """In-process calls with a credential, no real state dir, no model
    lookup, no waiting between retries and a plain machine setup."""
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    for var in llm._PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", True)
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(llm, "default_review_model", lambda: "claude-opus-5-5")
    monkeypatch.setattr(llm, "debug_log", lambda *a, **k: None)
    monkeypatch.setattr(llm, "_net_error_flags", lambda tls: 0)
    monkeypatch.setattr("time.sleep", lambda s: None)
    monkeypatch.setitem(_base._USAGE, "http_err_count", 0)
    monkeypatch.setitem(_base._USAGE, "http_err_last", 0)


class _Reply:
    def __init__(self, text):
        self._body = ('{"content": [{"type": "text", "text": %s}], "usage": {}}'
                      % __import__("json").dumps(text)).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body


class TestRecorded:
    def _urlopen(self, monkeypatch, *outcomes):
        """Each call takes the next outcome (the last one repeats): an
        exception is raised, anything else is the reply text."""
        calls = []

        def urlopen(*a, **k):
            outcome = outcomes[min(len(calls), len(outcomes) - 1)]
            calls.append(outcome)
            if isinstance(outcome, BaseException):
                raise outcome
            return _Reply(outcome)
        monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
        return calls

    def test_call_that_never_connects(self, direct, monkeypatch):
        self._urlopen(monkeypatch, urllib.error.URLError(_cert_error(20)))
        assert llm._call_claude("p", {"type": "object"}, model="m") is None
        assert llm._last_call_claude_http_error == -1
        assert _base._net_error_metric() == 2001

    def test_http_error_records_nothing(self, direct, monkeypatch):
        self._urlopen(monkeypatch, urllib.error.HTTPError("u", 400, "bad", {}, None))
        assert llm._call_claude("p", {"type": "object"}, model="m") is None
        assert llm._last_call_claude_http_error == 400
        assert _base._net_error_metric() == 0

    def test_a_later_call_that_gets_a_response_clears_it(self, direct, monkeypatch):
        refused = urllib.error.URLError(ConnectionRefusedError(errno.ECONNREFUSED, "refused"))
        self._urlopen(monkeypatch, refused, refused, refused, '{"ok": true}')
        assert llm._call_claude("p", {"type": "object"}, model="m") is None
        assert _base._net_error_metric() == llm.NET_ERR_CONNECT
        assert llm._call_claude("p", {"type": "object"}, model="fallback") == {"ok": True}
        assert _base._net_error_metric() == 0

    def test_a_later_call_refused_with_a_status_clears_it(self, direct, monkeypatch):
        refused = urllib.error.URLError(ConnectionRefusedError(errno.ECONNREFUSED, "refused"))
        self._urlopen(monkeypatch, refused, refused, refused,
                      urllib.error.HTTPError("u", 400, "bad", {}, None))
        llm._call_claude("p", {"type": "object"}, model="m")
        llm._call_claude("p", {"type": "object"}, model="fallback")
        assert llm._last_call_claude_http_error == 400
        assert _base._net_error_metric() == 0

    def test_tls_context_that_cannot_be_built(self, direct, monkeypatch):
        """Raised bare by the HTTP client, so the review sees an exception
        and no api_error."""
        self._urlopen(monkeypatch, ssl.SSLError(1, "[ASN1] nested asn1 error"))
        assert llm.analyze_code_security([("a.py", "+x = 1\n")]) == (None, [])
        assert llm.last_review_failed() and llm.last_review_status() is None
        assert _base._net_error_metric() == llm.NET_ERR_TLS

    def test_failure_on_the_windows_store_context_is_recorded(self, direct, monkeypatch):
        """The context built for a Windows store with an unreadable entry is
        the one the call uses, and a failure on it is still classified."""
        context = ssl.create_default_context()
        monkeypatch.setattr(llm, "_store_tls_context", context)
        used = []

        def urlopen(*a, **k):
            used.append(k.get("context"))
            raise urllib.error.URLError(_cert_error(20))
        monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
        assert llm._call_claude("p", {"type": "object"}, model="m") is None
        assert used and all(c is context for c in used)
        assert _base._net_error_metric() == 2001

    def test_store_check_that_fails_is_recorded_as_tls(self, direct, monkeypatch):
        """The store check raises and Python's own default context cannot be
        built either: the call raises past the retry loop."""
        def check():
            raise ssl.SSLError(1, "[ASN1] nested asn1 error")
        monkeypatch.setattr(llm, "_store_tls_context", llm._STORE_TLS_UNSET)
        monkeypatch.setattr(llm, "_context_without_unreadable_store_certs", check)
        self._urlopen(monkeypatch, ssl.SSLError(1, "[ASN1] nested asn1 error"))
        assert llm.analyze_code_security([("a.py", "+x = 1\n")]) == (None, [])
        assert llm.last_review_failed()
        assert _base._net_error_metric() == llm.NET_ERR_TLS

    def test_reply_that_is_not_json_records_nothing(self, direct, monkeypatch):
        self._urlopen(monkeypatch, "<html>sign in</html>")
        assert llm.analyze_code_security([("a.py", "+x = 1\n")]) == (None, [])
        assert llm.last_review_failed()
        assert _base._net_error_metric() == 0

    def test_only_a_positive_code_is_kept(self):
        _base._record_net_error(None)
        _base._record_net_error(0)
        assert _base._net_error_metric() == 0
        _base._record_net_error(4)
        _base._record_net_error(20003)
        assert _base._net_error_metric() == 20003

    def test_probe_that_cannot_connect(self, direct, monkeypatch):
        self._urlopen(monkeypatch, urllib.error.URLError(socket.gaierror(-2, "x")))
        assert llm._probe_anthropic() is False
        assert _base._net_error_metric() == llm.NET_ERR_DNS


class TestInnerCli:
    @pytest.fixture
    def sdk(self, direct, monkeypatch):
        mod = types.ModuleType("claude_agent_sdk")
        for name in ("AssistantMessage", "ClaudeAgentOptions", "ResultMessage"):
            setattr(mod, name, type(name, (), {"__init__": lambda self, **k: None}))
        mod.query = None
        monkeypatch.setitem(sys.modules, "claude_agent_sdk", mod)
        monkeypatch.setattr(llm, "_send_sdk_logs_to_debug_log", lambda: None)
        return mod

    def _run(self, monkeypatch, exc):
        def run(start, stderr_lines):
            raise exc
        monkeypatch.setattr(llm, "_run_inner_cli", run)
        assert llm._call_claude_via_sdk("p", {"type": "object"}) is None
        assert llm._last_call_claude_http_error == -1
        return _base._net_error_metric()

    def test_cli_failed(self, sdk, monkeypatch):
        assert self._run(monkeypatch, RuntimeError("exit code 1")) == llm.NET_ERR_INNER_CLI

    def test_cli_timed_out(self, sdk, monkeypatch):
        assert self._run(monkeypatch, asyncio.TimeoutError()) == llm.NET_ERR_INNER_CLI_TIMEOUT

    def test_no_sdk(self, direct, monkeypatch):
        monkeypatch.setitem(sys.modules, "claude_agent_sdk", None)
        monkeypatch.setattr(llm, "_inject_agent_sdk_venv_into_syspath", lambda d: None)
        assert llm._call_claude_via_sdk("p", {"type": "object"}) is None
        assert _base._net_error_metric() == llm.NET_ERR_NO_SDK


class TestEmittedRow:
    @pytest.fixture(autouse=True)
    def _clean(self, monkeypatch):
        monkeypatch.setattr(hook, "_TAIL_METRICS", {})
        monkeypatch.setattr(hook, "_log_usage", lambda usage: None)
        monkeypatch.setattr(hook.llm, "gateway_cfg", lambda: 0)

    def _row(self, capsys):
        return __import__("json").loads(capsys.readouterr().out)["metrics"]

    def test_ahead_of_the_rows_own_keys(self, capsys, monkeypatch):
        monkeypatch.setitem(_base._USAGE, "http_err_count", 2)
        monkeypatch.setitem(_base._USAGE, "http_err_last", -1)
        _base._record_net_error(2001)
        hook.emit_metrics({"review_failed": True, "vulns_found": 0, "review_ms": 18000,
                           "api_error": -1})
        keys = list(self._row(capsys))
        at = keys.index("net_err")
        assert keys[at - 1] == "http_err_count" and keys[at + 1] == "review_failed"

    def test_kept_on_a_row_over_the_key_cap(self, capsys):
        _base._record_net_error(2001)
        hook.emit_metrics({f"k{i}": i for i in range(25)})
        assert "net_err" in list(self._row(capsys))[:20]

    def test_absent_without_a_failure(self, capsys):
        hook.emit_metrics({"vulns_found": 0, "review_ms": 10})
        assert "net_err" not in self._row(capsys)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_stop_review_that_cannot_connect(workspace, hook_env):
    """Through the real hook: nothing listens at the endpoint."""
    _, repo = workspace
    env = dict(hook_env)
    env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{_free_port()}"
    env["SECURITY_REVIEW_MODEL"] = "claude-sonnet-4-6"  # one model: one round of retries
    run_hook(ups_payload(repo), env)
    (repo / "app.py").write_text(VULN_PY)
    _, out, _ = run_hook(stop_payload(repo), env)
    m = metrics_of(out)
    assert m["api_error"] == -1 and m["review_failed"] is True
    assert m["net_err"] % 100 == llm.NET_ERR_CONNECT
    assert "net_err" in list(m)[:20]


def test_stop_review_that_ran_has_no_class(workspace, hook_env):
    _, repo = workspace
    run_hook(ups_payload(repo), hook_env)
    (repo / "app.py").write_text(VULN_PY)
    _, out, _ = run_hook(stop_payload(repo), hook_env)
    m = metrics_of(out)
    assert "review_ms" in m and "net_err" not in m
