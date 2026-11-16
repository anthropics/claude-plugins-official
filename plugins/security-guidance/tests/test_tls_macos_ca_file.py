"""A macOS Python without any CA certificate uses the CA file macOS ships.

A python.org Python has none until its "Install Certificates" command is run.
The machine and that Python are stood in for here, so the cases run on every
platform.
"""
import http.client
import ssl
import types
import urllib.error

import pytest

# The certificates, the HTTPS endpoint and the review call of the store tests.
from test_tls_store_unreadable_cert import (  # noqa: F401
    UNRELATED_CA_PEM, _head, _review, https_api, pki, store, urlopen_calls)

import llm

_real_create_default_context = ssl.create_default_context


def _no_certificates(*args, **kwargs):
    """What create_default_context gives on a Python with no CA file."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    default = _real_create_default_context(cadata=UNRELATED_CA_PEM)
    context.verify_flags, context.options = default.verify_flags, default.options
    return context


@pytest.fixture
def mac(store, monkeypatch, tmp_path):
    """A Mac whose Python has no certificates and whose OS CA file holds one."""
    os_file = tmp_path / "cert.pem"
    os_file.write_text(UNRELATED_CA_PEM)
    paths = types.SimpleNamespace(cafile=None, capath=None)
    monkeypatch.delattr(ssl, "enum_certificates", raising=False)  # Windows only
    monkeypatch.setattr(llm, "_ON_MACOS", True)
    monkeypatch.setattr(llm, "_MACOS_CA_FILE", str(os_file))
    monkeypatch.setattr(ssl, "get_default_verify_paths", lambda: paths)
    monkeypatch.setattr(ssl, "_create_default_https_context", _no_certificates)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    return types.SimpleNamespace(paths=paths, os_file=os_file, tmp=tmp_path)


def _names(context):
    return {dict(x[0] for x in c["subject"])["commonName"] for c in context.get_ca_certs()}


def _context():
    return llm._context_with_os_ca_file()


class TestContext:
    def test_holds_the_os_file_and_nothing_else(self, mac):
        assert _names(_context()) == {"sg test unrelated CA"}

    def test_verifies_as_any_default_context(self, mac):
        context = _context()
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is True
        default = _real_create_default_context(cadata=UNRELATED_CA_PEM)
        assert context.verify_flags == default.verify_flags
        assert context.options == default.options
        assert context.minimum_version == default.minimum_version

    def test_is_set_up_as_http_client_does(self, mac, monkeypatch):
        offered = []
        monkeypatch.setattr(ssl.SSLContext, "set_alpn_protocols",
                            lambda self, protocols: offered.append(protocols))
        ours = _context()
        theirs = http.client.HTTPSConnection("localhost")._context
        assert offered == [["http/1.1"], ["http/1.1"]]
        assert ours.post_handshake_auth == theirs.post_handshake_auth

    def test_a_python_with_a_ca_file_is_left_alone(self, mac):
        mac.paths.cafile = str(mac.tmp / "own.pem")
        assert _context() is None

    def test_a_python_with_a_ca_directory_is_left_alone(self, mac):
        certs = mac.tmp / "certs"
        certs.mkdir()
        (certs / "1a2b3c4d.0").write_text(UNRELATED_CA_PEM)
        mac.paths.capath = str(certs)
        assert _context() is None

    @pytest.mark.parametrize("contents", [[], [".keepme"], ["notes.txt"]])
    def test_a_directory_without_certificates_counts_as_none(self, mac, contents):
        certs = mac.tmp / "certs"
        certs.mkdir()
        for name in contents:  # Homebrew keeps a .keepme there
            (certs / name).write_text("")
        mac.paths.capath = str(certs)
        assert _context() is not None

    def test_a_directory_that_cannot_be_listed_counts_as_none(self, mac, monkeypatch):
        def listdir(path):
            raise PermissionError(path)
        mac.paths.capath = str(mac.tmp)
        monkeypatch.setattr(llm.os, "listdir", listdir)
        assert _context() is not None

    def test_certificates_found_another_way_are_left_alone(self, mac, monkeypatch):
        """A default context can hold some though the paths name no file."""
        monkeypatch.setattr(ssl, "_create_default_https_context",
                            lambda: _real_create_default_context(cadata=UNRELATED_CA_PEM))
        assert _context() is None

    def test_a_site_that_replaced_the_default_is_left_alone(self, mac, monkeypatch):
        monkeypatch.setattr(ssl, "_create_default_https_context",
                            ssl._create_unverified_context)
        assert _context() is None

    @pytest.mark.parametrize("value", ["/nonexistent", ""])
    @pytest.mark.parametrize("var", ["SSL_CERT_FILE", "SSL_CERT_DIR"])
    def test_the_users_own_choice_wins(self, mac, monkeypatch, var, value):
        monkeypatch.setenv(var, value)
        assert _context() is None

    def test_a_plain_http_endpoint_needs_none(self, mac, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://127.0.0.1:4000")
        assert _context() is None

    def test_other_platforms_are_untouched(self, mac, monkeypatch):
        monkeypatch.setattr(llm, "_ON_MACOS", False)
        assert _context() is None

    def test_no_os_file_means_no_change(self, mac):
        mac.os_file.unlink()
        assert _context() is None


class TestCalls:
    def test_the_context_is_built_once(self, mac, urlopen_calls, monkeypatch):
        real, builds = llm._context_with_os_ca_file, []
        monkeypatch.setattr(llm, "_context_with_os_ca_file",
                            lambda: builds.append(1) or real())
        llm._urlopen(_head(), 5)
        llm._urlopen(_head(), 5)
        assert len(builds) == 1
        first, second = [c["context"] for c in urlopen_calls]
        assert first is second
        assert _names(first) == {"sg test unrelated CA"}

    @pytest.mark.parametrize("problem", ["not a certificate", PermissionError])
    def test_an_os_file_that_cannot_be_used_changes_nothing(
            self, mac, urlopen_calls, monkeypatch, problem):
        if isinstance(problem, str):
            mac.os_file.write_text(problem)
        else:
            def refuse(self, **kwargs):
                raise problem("denied")
            monkeypatch.setattr(ssl.SSLContext, "load_verify_locations", refuse)
            monkeypatch.setattr(ssl, "_create_default_https_context",
                                lambda: ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
        llm._urlopen(_head(), 5)
        assert urlopen_calls == [{"timeout": 5}]


class TestHandshake:
    """Real TLS against a local endpoint that only the OS file can vouch for."""

    @staticmethod
    def _os_file_trusts(mac, pki):
        mac.os_file.write_text(ssl.DER_cert_to_PEM_cert(pki["trusted"]["ca"]))

    @staticmethod
    def _refused(srv):
        with pytest.raises(urllib.error.URLError) as raised:
            llm._urlopen(_head(), 5)
        assert isinstance(raised.value.reason, ssl.SSLCertVerificationError)
        _review()
        assert llm.last_review_failed()
        assert srv.calls == []

    def test_a_review_runs(self, mac, pki, https_api):
        srv = https_api("trusted")
        self._os_file_trusts(mac, pki)
        _review()
        assert not llm.last_review_failed()
        assert len(srv.calls) == 1

    def test_without_the_os_file_the_review_fails(self, mac, https_api):
        srv = https_api("trusted")
        mac.os_file.unlink()
        self._refused(srv)

    @pytest.mark.parametrize("server", ["untrusted", "other-host"])
    def test_a_certificate_it_does_not_cover_is_still_refused(
            self, mac, pki, https_api, server):
        srv = https_api(server)
        self._os_file_trusts(mac, pki)
        self._refused(srv)
