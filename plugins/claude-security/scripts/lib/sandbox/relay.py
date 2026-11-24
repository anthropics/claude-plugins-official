"""The one way out: it takes model requests from the sandbox and makes them with the credential."""

from __future__ import annotations

import os
import re
import ssl
import threading
import time
from collections import defaultdict
from contextlib import suppress
from http import HTTPStatus
from http.client import HTTPException, HTTPMessage, HTTPResponse, parse_headers
from socket import SHUT_RDWR
from typing import TYPE_CHECKING, cast
from urllib.error import URLError
from urllib.request import (
    HTTPHandler,
    HTTPSHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
    getproxies_environment,
)

from .. import strictjson
from . import request, streams
from .plan import MOST_CALLS, SHORTEST_PRIVATE, SandboxError
from .request import RefusedError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from socket import socket

    from .provider import Provider


_TLS_VARIABLES = (
    "NODE_EXTRA_CA_CERTS",
    "CLAUDE_CODE_CLIENT_CERT",
    "CLAUDE_CODE_CLIENT_KEY",
    "CLAUDE_CODE_CLIENT_KEY_PASSPHRASE",
)
_STORES = "CLAUDE_CODE_CERT_STORE"
_REVOKED = b"OAuth token has been revoked"
_MOST_TOLD = 32
_LONGEST_TOLD = 1000
_LONGEST_LINE = 8192
_LARGEST_BODY = 32 << 20
_LARGEST_ERROR = 1 << 20
_READ_SECONDS = 60
_ANSWER_SECONDS = 900
_ACCEPT_TRIES = 60
_ACCEPT_PAUSE_SECONDS = 1
# Not the headers that choose whose account a request counts for; the betas are checked apart.
_ASKED = re.compile(
    r"accept|user-agent|x-app|x-client-(app|request-id)|x-anthropic-additional-protection"
    r"|(x-(cc|claude-code|stainless)-|anthropic-(?!beta))"
    r"(?!.*(org|workspace|profile|account|user|key|auth|token))[a-z-]+"
)
# Not the headers that name the account.
_ANSWERED = re.compile(
    r"content-type|request-id|retry-after(-ms)?|x-should-retry|anthropic-(?!org|workspace)[a-z0-9-]+"
    r"|x-amzn-(requestid|errortype|bedrock-[a-z-]+)"
)
_LONGEST_HEADER = 4000
_PLAIN = re.compile(rf"[\x20-\x7e]{{0,{_LONGEST_HEADER}}}")
# stderr can be a public log. This masks long words that could be part of a credential: a guess.
_OPAQUE = re.compile(rb"(?=[\w+/=\\.-]*\d)[\w+/=\\.-]{16,}")
_REQUEST_LINE = re.compile(rb"POST ([\x21-\x7e]+) HTTP/1\.1\r\n")


def _only(names: re.Pattern[str], headers: HTTPMessage) -> dict[str, str]:
    given = ((name.lower(), value) for name, value in headers.items())
    return {name: value for name, value in given if names.fullmatch(name)}


def _head(status: int, headers: Mapping[str, str]) -> bytes:
    lines = (f"{name}: {value}\r\n" for name, value in {**headers, "connection": "close"}.items())
    return f"HTTP/1.1 {status} -\r\n{''.join(lines)}\r\n".encode()


def _whole(status: int, headers: Mapping[str, str], body: bytes) -> bytes:
    return _head(status, {**headers, "content-length": str(len(body))}) + body


def _failure(status: int, why: str, headers: Mapping[str, str] | None = None) -> bytes:
    kind = "api_error" if status >= HTTPStatus.INTERNAL_SERVER_ERROR else "invalid_request_error"
    error = {"type": kind, "message": f"sandbox: {why}"}
    body = strictjson.text({"type": "error", "error": error}).encode()
    return _whole(status, {**(headers or {}), "content-type": "application/json"}, body)


def _proxy() -> str:
    """The proxy that the environment names for https requests, else the one for http, if any."""
    named = getproxies_environment()
    return named.get("https") or named.get("http", "")


def tls_context(variables: Mapping[str, str]) -> ssl.SSLContext:
    """What the relay's requests trust, and the client certificate that they show. It reads the
    files that `variables` name, so the caller calls it while it can open them. SandboxError for a
    file, a proxy or a choice of stores that it cannot use, or half of a certificate's pair."""
    proxy = _proxy()
    # urllib speaks plain http to any proxy, so a proxy's password would cross in the clear.
    if ":/" in proxy and not proxy.lower().startswith("http://"):
        msg = "the proxy must have an http:// address"
        raise SandboxError(msg)
    stores = {word.strip().lower() for word in variables.get(_STORES, "").split(",")}
    if "bundled" in stores and "system" not in stores:
        msg = f"{_STORES} leaves out the system's certificates, which the relay trusts: add system"
        raise SandboxError(msg)
    context = ssl.create_default_context()
    # As before Python 3.13, which rejects many company CAs and accepts a chain with no root.
    context.verify_flags = ssl.VERIFY_X509_TRUSTED_FIRST
    cert = variables.get("CLAUDE_CODE_CLIENT_CERT")
    key = variables.get("CLAUDE_CODE_CLIENT_KEY")
    if bool(cert) != bool(key):
        msg = "CLAUDE_CODE_CLIENT_CERT and CLAUDE_CODE_CLIENT_KEY work only together"
        raise SandboxError(msg)
    names = " or ".join(name for name in _TLS_VARIABLES if variables.get(name))
    try:
        if extra := variables.get("NODE_EXTRA_CA_CERTS"):
            context.load_verify_locations(extra)
        if cert and key:
            phrase = variables.get("CLAUDE_CODE_CLIENT_KEY_PASSPHRASE", "")
            context.load_cert_chain(cert, key, phrase)
    except OSError as error:
        msg = f"{names} cannot be used: {error}"
        raise SandboxError(msg) from error
    except ValueError as error:
        msg = f"{names} cannot be used"
        raise SandboxError(msg) from error
    return context


class Relay:
    """Serves `listener` until close(), or the end of a Door. `added` are headers of the user's own
    for each request, `tls` comes from tls_context(), and `fail` hears of a fault that ends it.
    `refused` counts the calls that it refused, and so answered with a 400."""

    def __init__(
        self,
        listener: socket,
        provider: Provider,
        added: Mapping[str, str],
        tls: ssl.SSLContext,
        fail: Callable[[str], None],
    ) -> None:
        self._listener: socket = listener
        self._fail: Callable[[str], None] = fail
        self._closed: bool = False
        self._provider: Provider = provider
        self._added: Mapping[str, str] = added
        # Where the provider yields, the user's header of a credential's name goes in its place.
        self._yielded: Mapping[str, str] = added if provider.yields else {}
        # The caller's own headers can hold a gateway's key.
        words = (word for value in added.values() for word in (value, *value.split()))
        self._private: frozenset[str] = frozenset(w for w in words if len(w) >= SHORTEST_PRIVATE)
        self._checking: threading.Lock = threading.Lock()
        self._counting: threading.Lock = threading.Lock()
        self.refused: int = 0
        self._told: defaultdict[str, set[str]] = defaultdict(set)
        # No handler for redirects: one would carry the credential to another host.
        self._opener: OpenerDirector = OpenerDirector()
        # Plain http goes to loopback alone, and must not carry the credential to a proxy.
        proxy = ProxyHandler({"https": address} if (address := _proxy()) else {})
        for handler in (proxy, HTTPHandler(), HTTPSHandler(context=tls)):
            self._opener.add_handler(handler)
        threading.Thread(target=self._accept, daemon=True).start()

    def close(self) -> None:
        """Take no more connections."""
        self._closed = True
        with suppress(OSError):
            self._listener.shutdown(SHUT_RDWR)

    def _tell(self, what: str, why: str) -> None:
        """Say `what: why` on stderr, the first time, up to a limit for each `what`."""
        told = self._told[what]
        if why not in told and len(told) < _MOST_TOLD:
            told.add(why)
            streams.say(f"{what}: {why}")

    def _accept(self) -> None:
        room = threading.BoundedSemaphore(MOST_CALLS)

        def serve(caller: socket) -> None:
            try:
                with suppress(OSError, HTTPException, MemoryError):
                    caller.settimeout(_READ_SECONDS)
                    self._serve(caller)
            except Exception as error:
                self._tell("a call failed", type(error).__name__)
            finally:
                room.release()
                caller.close()

        tries = _ACCEPT_TRIES
        while room.acquire():
            try:
                self._start(serve)
                tries = _ACCEPT_TRIES
            except EOFError:  # noqa: PERF203
                return
            except (OSError, RuntimeError, MemoryError) as error:
                room.release()
                tries -= 1
                if self._closed or not tries:
                    if not self._closed:
                        self._fail(f"the relay cannot take calls: {error}")
                    return
                time.sleep(_ACCEPT_PAUSE_SECONDS)

    def _start(self, serve: Callable[[socket], None]) -> None:
        caller = self._listener.accept()[0]
        if self._closed:
            caller.close()
            raise EOFError
        try:
            threading.Thread(target=serve, args=(caller,), daemon=True).start()
        except (RuntimeError, MemoryError):
            caller.close()
            raise

    def _serve(self, caller: socket) -> None:
        try:
            asked = self._read(caller)
        except (RefusedError, HTTPException) as error:
            why = str(error) if isinstance(error, RefusedError) else "the head is too long"
            with self._counting:
                self.refused += 1
            self._tell("refused a request", why)
            return caller.sendall(_failure(HTTPStatus.BAD_REQUEST, why))
        except SandboxError as error:
            missing = "the credential is not at hand"
            self._tell(missing, str(error))
            return caller.sendall(_failure(HTTPStatus.BAD_GATEWAY, missing))
        try:
            answer = cast("HTTPResponse", self._opener.open(asked, timeout=_ANSWER_SECONDS))
        except (OSError, HTTPException, ValueError) as error:
            cause = error.reason if isinstance(error, URLError) else error
            self._tell("the model's host did not answer", type(cause).__name__)
            return caller.sendall(_failure(HTTPStatus.BAD_GATEWAY, "the model did not answer"))
        with answer:
            if answer.status != HTTPStatus.OK:
                return caller.sendall(self._error(answer, asked))
            return self._stream(answer, caller)

    def _read(self, caller: socket) -> Request:
        """The request to make in place of the one that `caller` sends."""
        with caller.makefile("rb") as sent:
            first = sent.readline(_LONGEST_LINE)
            if not (line := _REQUEST_LINE.fullmatch(first)):
                msg = f"only model requests pass, and not {first[:60].decode('latin-1')!a}"
                raise RefusedError(msg)
            url = self._provider.route(line[1].decode())
            try:
                headers = parse_headers(sent)
            except (OSError, HTTPException, MemoryError):
                raise
            except Exception as error:
                msg = "the head cannot be parsed"
                raise RefusedError(msg) from error
            lengths = headers.get_all("content-length", [""])
            packed = "transfer-encoding" in headers or "content-encoding" in headers
            if packed or len(lengths) > 1 or not re.fullmatch(r"[0-9]{1,9}", lengths[0]):
                msg = "the body must be plain, with one Content-Length"
                raise RefusedError(msg)
            size = int(lengths[0])
            if size > _LARGEST_BODY:
                msg = "the body is too large"
                raise RefusedError(msg)
            if len(raw := sent.read(size)) < size:
                msg = "the body is cut short"
                raise RefusedError(msg)
        # One at a time: a parsed body can take many times its size in memory.
        with self._checking:
            body = request.checked(raw, version_in_body=self._provider.version_in_body)
        betas = request.betas(",".join(headers.get_all("anthropic-beta", [])).split(","))
        kept = _only(_ASKED, headers)
        if odd := [name for name, value in kept.items() if not _PLAIN.fullmatch(value)]:
            msg = (
                f"the header {odd[0][:40]!a} is not plain text "
                f"of {_LONGEST_HEADER} characters or fewer"
            )
            raise RefusedError(msg)
        made = {
            **kept,
            **({"anthropic-beta": ",".join(betas)} if betas else {}),
            "content-type": "application/json",
            **({} if self._provider.version_in_body else {"anthropic-version": request.VERSION}),
            **self._added,
            **self._provider.sign(url, body),
            **self._yielded,
        }
        return Request(url, body, made)  # noqa: S310

    def _secrets(self) -> set[str]:
        return self._provider.credential.seen | self._private

    def _headers(self, answer: HTTPResponse) -> dict[str, str]:
        named, secrets = _only(_ANSWERED, answer.headers), self._secrets()
        hidden = {"content-type": self._provider.credential.seen.copy()}
        plain = ((k, v) for k, v in named.items() if _PLAIN.fullmatch(v))
        return {k: v for k, v in plain if not any(s in v for s in hidden.get(k, secrets))}

    def _stream(self, answer: HTTPResponse, caller: socket) -> None:
        # In chunks, so that an answer that breaks off lacks its last chunk and shows as broken.
        headers = self._headers(answer) | {"transfer-encoding": "chunked"}
        caller.sendall(_head(answer.status, headers))
        while chunk := answer.read1(1 << 16):
            caller.sendall(b"%x\r\n%b\r\n" % (len(chunk), chunk))
        if not answer.length:
            caller.sendall(b"0\r\n\r\n")

    def _error(self, answer: HTTPResponse, asked: Request) -> bytes:
        turned_down = answer.status in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}
        if turned_down:
            self._provider.credential.forget()
        try:
            body = answer.read(_LARGEST_ERROR + 1)
        except (OSError, HTTPException):
            body = None
        if body is None or answer.length or len(body) > _LARGEST_ERROR:
            cut = "the model's error answer was cut or too long"
            self._tell(cut, f"status {answer.status}")
            return _failure(HTTPStatus.BAD_GATEWAY, cut)
        headers = self._headers(answer)
        for secret in sorted(self._secrets(), key=len, reverse=True):
            body = body.replace(os.fsencode(secret), b"***")
        if turned_down:
            ended = answer.status == HTTPStatus.UNAUTHORIZED or _REVOKED in body
            sent = asked.get_header("Authorization", "")
            own = "authorization" in self._yielded
            if ended and not own and self._provider.credential.wait_for_renewal(sent):
                headers["x-should-retry"] = "true"
                return _failure(HTTPStatus.UNAUTHORIZED, "the token was renewed", headers)
            # A host can quote a credential in part when it turns one down.
            said = _OPAQUE.sub(b"***", body[: 2 * _LONGEST_TOLD])[:_LONGEST_TOLD].decode("latin-1")
            self._tell(f"the model's host answered {answer.status}", said)
            return _failure(answer.status, "the answer's words are on stderr, outside", headers)
        return _whole(answer.status, headers, body)
