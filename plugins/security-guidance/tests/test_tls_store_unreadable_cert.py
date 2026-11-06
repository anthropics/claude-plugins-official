"""A Windows certificate store with an entry OpenSSL cannot read must not stop reviews.

Older Python releases load each Windows store in one call, so one unreadable
certificate makes the default TLS context fail to build. The store and that
loading are stood in for here, so the cases run on every platform.
"""
import http.server
import json
import shutil
import ssl
import subprocess
import threading
import urllib.error
import urllib.request

import pytest

from conftest import _Stub

import _base
import llm

# A self-signed test CA (public certificate only).
UNRELATED_CA_PEM = """-----BEGIN CERTIFICATE-----
MIIBkjCCATmgAwIBAgIUbv89EXoDEbZBR6jKRVAU1V/0fGgwCgYIKoZIzj0EAwIw
HzEdMBsGA1UEAwwUc2cgdGVzdCB1bnJlbGF0ZWQgQ0EwHhcNMjYxMDIxMTYyMjQ1
WhcNMzYxMDE4MTYyMjQ1WjAfMR0wGwYDVQQDDBRzZyB0ZXN0IHVucmVsYXRlZCBD
QTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABPNt0cYQuFTK2120/wnrAXDuqQUE
8Cu0MpykWGDKTpymrBpKT9tB3wtr6Z951brKADRTgA7sKsIRoo9WmwnJKdyjUzBR
MB0GA1UdDgQWBBQbn4fFArXUPihIY/CG7IxtVswc1DAfBgNVHSMEGDAWgBQbn4fF
ArXUPihIY/CG7IxtVswc1DAPBgNVHRMBAf8EBTADAQH/MAoGCCqGSM49BAMCA0cA
MEQCIDuCfFRxNvoQhAXHiaA+Pgd7nuZ7hHVE16dERXHiVT6JAiACb2vks3dsL40u
UAQ7MEoy37JzJExADeVOBhztTqTkkw==
-----END CERTIFICATE-----
"""
UNRELATED_CA = ssl.PEM_cert_to_DER_cert(UNRELATED_CA_PEM)
# The same certificate with its serial number's tag overwritten.
UNREADABLE = UNRELATED_CA[:13] + b"\x04" + UNRELATED_CA[14:]

SERVER_AUTH = ssl.Purpose.SERVER_AUTH.oid
CLIENT_AUTH = ssl.Purpose.CLIENT_AUTH.oid

_real_create_default_context = ssl.create_default_context


class _Store:
    """Stand-in for the Windows certificate stores and for a Python that
    loads each of them in one call."""

    def __init__(self):
        self.stores = {"CA": [], "ROOT": []}
        self.enumerations = 0
        self.default_builds = 0

    def enum_certificates(self, name):
        self.enumerations += 1
        return list(self.stores.get(name, []))

    def create_default_context(self, purpose=ssl.Purpose.SERVER_AUTH, *,
                               cafile=None, capath=None, cadata=None):
        if cafile or capath or cadata:
            return _real_create_default_context(
                purpose, cafile=cafile, capath=capath, cadata=cadata)
        self.default_builds += 1
        # Never the machine's own trust: only what the test puts in the store.
        context = _real_create_default_context(purpose, cadata=UNRELATED_CA)
        for name in ("CA", "ROOT"):
            certs = b"".join(
                cert for cert, encoding, trust in self.stores[name]
                if encoding == "x509_asn" and (trust is True or purpose.oid in trust))
            if certs:
                context.load_verify_locations(cadata=certs)
        return context


@pytest.fixture
def store(monkeypatch):
    s = _Store()
    monkeypatch.setattr(ssl, "enum_certificates", s.enum_certificates, raising=False)
    monkeypatch.setattr(ssl, "create_default_context", s.create_default_context)
    monkeypatch.setattr(ssl, "_create_default_https_context", s.create_default_context)
    # urllib keeps one opener per process, and on newer Pythons it holds the
    # context it was built with; a hook process starts without one.
    monkeypatch.setattr(urllib.request, "_opener", None)
    # The store is checked once per process.
    monkeypatch.setattr(llm, "_store_tls_context", llm._STORE_TLS_UNSET)
    monkeypatch.setattr(llm, "_store_certs_skipped", 0)
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                "ALL_PROXY", "all_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("NO_PROXY", "*")
    monkeypatch.setenv("no_proxy", "*")
    return s


def _entry(cert, trust=True, encoding="x509_asn"):
    return (cert, encoding, trust)


def _subjects(context):
    """The test certificates in a context (it also holds the machine's default file)."""
    names = {dict(x[0] for x in c["subject"]).get("commonName", "")
             for c in context.get_ca_certs()}
    return {n for n in names if n.startswith("sg test ")}


# ── certificates and an HTTPS endpoint for the handshake cases ───────────

def _openssl(*args, cwd):
    r = subprocess.run(["openssl", *args], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.fixture(scope="module")
def pki(tmp_path_factory):
    if not shutil.which("openssl"):
        pytest.skip("needs the openssl command to make test certificates")
    d = tmp_path_factory.mktemp("pki")
    leaf = ("basicConstraints=CA:FALSE\nextendedKeyUsage=serverAuth\n"
            "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid\n")
    (d / "leaf.cnf").write_text("subjectAltName=DNS:localhost,IP:127.0.0.1\n" + leaf)
    (d / "other-host.cnf").write_text("subjectAltName=DNS:other.invalid\n" + leaf)
    # The subject goes in the config file: LibreSSL ignores -subj when the config has prompt=no.
    def req_config(common_name):
        (d / "req.cnf").write_text(
            "[req]\ndistinguished_name=dn\nx509_extensions=v3\nprompt=no\n"
            f"[dn]\nCN={common_name}\n"
            "[v3]\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,cRLSign\n"
            "subjectKeyIdentifier=hash\n")
    out = {}
    # server certificate -> (the CA that signs it, its extensions)
    servers = {"trusted": ("trusted", "leaf.cnf"), "untrusted": ("untrusted", "leaf.cnf"),
               "other-host": ("trusted", "other-host.cnf")}
    for ca in ("trusted", "untrusted"):
        req_config(f"sg test {ca} CA")
        _openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-config", "req.cnf",
                 "-keyout", f"{ca}-ca.key", "-out", f"{ca}-ca.pem", "-days", "2", cwd=d)
    req_config("sg test server")
    for name, (ca, extensions) in servers.items():
        _openssl("req", "-newkey", "rsa:2048", "-nodes", "-config", "req.cnf",
                 "-keyout", f"{name}.key", "-out", f"{name}.csr", cwd=d)
        _openssl("x509", "-req", "-in", f"{name}.csr", "-CA", f"{ca}-ca.pem",
                 "-CAkey", f"{ca}-ca.key", "-CAcreateserial", "-out", f"{name}.pem",
                 "-days", "2", "-extfile", extensions, cwd=d)
        out[name] = {
            "ca": ssl.PEM_cert_to_DER_cert((d / f"{ca}-ca.pem").read_text()),
            "cert": str(d / f"{name}.pem"), "key": str(d / f"{name}.key"),
        }
    return out


@pytest.fixture
def https_api(pki, store, tmp_path, monkeypatch):
    servers = []

    def start(signed_by):
        srv = http.server.HTTPServer(("127.0.0.1", 0), _Stub)
        srv.calls, srv.status, srv.delay, srv.vulns = [], 200, 0, []
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(pki[signed_by]["cert"], pki[signed_by]["key"])
        srv.socket = context.wrap_socket(srv.socket, server_side=True)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        monkeypatch.setenv("ANTHROPIC_BASE_URL", f"https://localhost:{srv.server_port}")
        return srv

    for var in ("SG_AGENTIC_MODEL", "SG_DUAL_OR", "CLAUDE_CODE_EXECPATH",
                "SG_AGENTIC_CLI_PATH", "CLAUDE_CODE_REMOTE", *llm._PROVIDER_ENV_VARS):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("SECURITY_REVIEW_MODEL", "claude-opus-5-5")
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", "")
    monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", True)
    monkeypatch.setattr(llm, "_auth_prefer_token", False)
    monkeypatch.setattr(llm, "_review_model_memo", None, raising=False)
    monkeypatch.setattr(llm, "_last_call_claude_http_error", None)
    monkeypatch.setattr(_base, "_USAGE", {**_base._USAGE, "models": []})
    # No waiting between the attempts of a call that keeps failing.
    monkeypatch.setattr("time.sleep", lambda s: None)
    try:
        yield start
    finally:
        for srv in servers:
            srv.shutdown()
            srv.server_close()


def _review():
    return llm.analyze_code_security([("app.py", "+print('hi')\n")], is_diff=True)


# ── the stand-in behaves like the reported machines ──────────────────────

class TestStandIn:
    def test_the_unreadable_certificate_is_unreadable(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with pytest.raises(ssl.SSLError):
            context.load_verify_locations(cadata=UNREADABLE)

    @pytest.mark.parametrize("entries", [
        [UNRELATED_CA, UNREADABLE], [UNREADABLE, UNRELATED_CA],
    ], ids=["after a readable one", "first in the store"])
    def test_one_unreadable_certificate_breaks_the_default_context(self, store, entries):
        store.stores["ROOT"] = [_entry(c) for c in entries]
        with pytest.raises(ssl.SSLError):
            ssl.create_default_context()

    def test_a_readable_store_builds(self, store):
        store.stores["ROOT"] = [_entry(UNRELATED_CA)]
        ssl.create_default_context()


# ── the context built without the unreadable entries ─────────────────────

def _context():
    return llm._context_without_unreadable_store_certs()


class TestContext:
    def test_none_when_the_default_context_builds(self, store):
        store.stores["ROOT"] = [_entry(UNRELATED_CA)]
        assert _context() == (None, 0)
        assert store.enumerations == 0

    def test_none_off_windows(self, store, monkeypatch):
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(UNRELATED_CA)]
        monkeypatch.delattr(ssl, "enum_certificates")
        assert _context() == (None, 0)
        assert store.default_builds == 0

    def test_none_when_no_certificate_is_readable(self, store):
        store.stores["ROOT"] = [_entry(UNREADABLE)]
        assert _context() == (None, 1)

    def test_still_verifies_the_chain_and_the_host_name(self, store):
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(UNRELATED_CA)]
        context, _ = _context()
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is True
        default = _real_create_default_context(cadata=UNRELATED_CA)
        assert context.verify_flags == default.verify_flags
        assert context.options == default.options
        assert context.minimum_version == default.minimum_version

    def test_readable_certificates_from_both_stores_are_kept(self, store, pki):
        store.stores["CA"] = [_entry(UNREADABLE), _entry(pki["trusted"]["ca"])]
        store.stores["ROOT"] = [_entry(UNRELATED_CA), _entry(UNREADABLE), _entry(UNREADABLE)]
        context, skipped = _context()
        assert _subjects(context) == {"sg test trusted CA", "sg test unrelated CA"}
        assert skipped == 3

    def test_only_certificates_trusted_for_servers_are_loaded(self, store, pki):
        store.stores["ROOT"] = [
            _entry(UNREADABLE),
            _entry(UNRELATED_CA, trust={SERVER_AUTH}),
            _entry(pki["trusted"]["ca"], trust={CLIENT_AUTH}),
            _entry(pki["untrusted"]["ca"], encoding="pkcs_7_asn"),
            _entry(UNREADABLE, trust={CLIENT_AUTH}),
        ]
        context, skipped = _context()
        assert _subjects(context) == {"sg test unrelated CA"}
        assert skipped == 1

    def test_a_store_that_cannot_be_listed_is_left_out(self, store, monkeypatch):
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(UNRELATED_CA)]
        listed = store.enum_certificates

        def enum_certificates(name):
            if name == "CA":
                raise PermissionError("denied")
            return listed(name)

        monkeypatch.setattr(ssl, "enum_certificates", enum_certificates)
        context, skipped = _context()
        assert _subjects(context) == {"sg test unrelated CA"}
        assert skipped == 1


# ── the plugin's HTTPS calls ─────────────────────────────────────────────

@pytest.fixture
def urlopen_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda request, **kw: calls.append(kw) or "response")
    return calls


def _head():
    return urllib.request.Request(llm._anthropic_base_url() + "/", method="HEAD")


class TestUrlopen:
    def test_default_context_is_used_when_it_builds(self, store, urlopen_calls):
        store.stores["ROOT"] = [_entry(UNRELATED_CA)]
        assert llm._urlopen("request", 7) == "response"
        assert llm._urlopen("request", 7) == "response"
        assert urlopen_calls == [{"timeout": 7}] * 2
        assert (store.default_builds, store.enumerations) == (1, 0)
        assert llm._store_certs_skipped == 0

    def test_nothing_is_checked_off_windows(self, store, urlopen_calls, monkeypatch):
        monkeypatch.delattr(ssl, "enum_certificates")
        assert llm._urlopen("request", 7) == "response"
        assert urlopen_calls == [{"timeout": 7}]
        assert store.default_builds == 0

    def test_each_request_is_sent_once(self, store, urlopen_calls):
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(UNRELATED_CA)]
        assert llm._urlopen("request", 7) == "response"
        assert len(urlopen_calls) == 1
        assert urlopen_calls[0]["timeout"] == 7
        assert isinstance(urlopen_calls[0]["context"], ssl.SSLContext)

    def test_a_store_check_that_fails_leaves_the_default_route(
            self, store, urlopen_calls, monkeypatch):
        def enum_certificates(name):
            raise OSError("store unavailable")

        store.stores["ROOT"] = [_entry(UNREADABLE)]
        monkeypatch.setattr(ssl, "enum_certificates", enum_certificates)
        assert llm._urlopen("request", 7) == "response"
        assert urlopen_calls == [{"timeout": 7}]

    def test_review_runs_with_an_unreadable_certificate_in_the_store(
            self, store, pki, https_api):
        srv = https_api("trusted")
        store.stores["CA"] = [_entry(UNRELATED_CA), _entry(UNREADABLE)]
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(pki["trusted"]["ca"])]
        _review()
        assert not llm.last_review_failed()
        assert len(srv.calls) == 1
        assert llm._store_certs_skipped == 2

    def test_the_store_is_read_once_per_process(self, store, pki, https_api):
        srv = https_api("trusted")
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(pki["trusted"]["ca"])]
        _review()
        builds, enumerations = store.default_builds, store.enumerations
        _review()
        assert len(srv.calls) == 2
        assert (store.default_builds, store.enumerations) == (builds, enumerations) == (1, 2)

    def test_a_server_the_store_does_not_trust_is_still_refused(
            self, store, pki, https_api):
        srv = https_api("untrusted")
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(pki["trusted"]["ca"])]
        with pytest.raises(urllib.error.URLError) as raised:
            llm._urlopen(_head(), 5)
        assert isinstance(raised.value.reason, ssl.SSLCertVerificationError)
        _review()
        assert llm.last_review_failed()
        assert srv.calls == []

    def test_a_host_name_the_certificate_does_not_cover_is_still_refused(
            self, store, pki, https_api):
        srv = https_api("other-host")
        store.stores["ROOT"] = [_entry(UNREADABLE), _entry(pki["trusted"]["ca"])]
        with pytest.raises(urllib.error.URLError) as raised:
            llm._urlopen(_head(), 5)
        assert isinstance(raised.value.reason, ssl.SSLCertVerificationError)
        assert "localhost" in str(raised.value.reason)
        _review()
        assert llm.last_review_failed()
        assert srv.calls == []

    def test_review_runs_on_a_readable_store(self, store, pki, https_api):
        srv = https_api("trusted")
        store.stores["ROOT"] = [_entry(pki["trusted"]["ca"])]
        _review()
        assert not llm.last_review_failed()
        assert len(srv.calls) == 1
        assert llm._store_certs_skipped == 0


def test_review_rows_count_the_skipped_store_entries(monkeypatch, capsys):
    import security_reminder_hook as hook

    def row():
        hook.emit_metrics({"vulns_found": 0, "review_ms": 10})
        return json.loads(capsys.readouterr().out)["metrics"]

    monkeypatch.setattr(llm, "_store_certs_skipped", 0)
    assert "tls_store_skipped" not in row()
    monkeypatch.setattr(llm, "_store_certs_skipped", 7)
    assert row()["tls_store_skipped"] == 7
