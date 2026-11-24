"""Where model requests go, which ones may go, and the credential that the relay adds to them."""

from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlsplit

from .. import strictjson
from ..strictjson import JsonMap, as_map, clean, is_map, is_str
from . import sigv4
from .plan import RELAY, SHORTEST_PRIVATE, SandboxError
from .request import RefusedError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

STAND_IN = "the-real-credential-stays-outside"
# Variables that name models, regions or the Vertex project. The command sees them as they are.
SETTINGS = re.compile(
    r"ANTHROPIC_(MODEL|SMALL_FAST_MODEL|DEFAULT_\w+_MODEL|VERTEX_PROJECT_ID)"
    r"|CLAUDE_CODE_SUBAGENT_MODEL|CLOUD_ML_REGION|VERTEX_REGION_\w+|AWS_REGION"
)
# The families of variables that can choose the host, the account, the way there or the sign-in.
ROUTE = re.compile(
    r"(?i:(https?|no)_proxy)|NODE_EXTRA_CA_CERTS|CLOUD_ML_REGION|CLAUDE_CODE_(USE|CLIENT|OAUTH)_\w+"
    r"|CLAUDE_CODE_SKIP_(BEDROCK|VERTEX)_AUTH|CLAUDE_CODE_CERT_STORE"
    r"|(ANTHROPIC|AWS|AZURE|CLOUDSDK|GOOGLE|SSL_CERT|VERTEX_REGION)_\w+"
)
# Credentials, and the headers that can hold one. What the provider does not use stays outside too.
SECRETS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_AWS_API_KEY",
    "ANTHROPIC_CUSTOM_HEADERS",
    "ANTHROPIC_FOUNDRY_API_KEY",
    "ANTHROPIC_FOUNDRY_AUTH_TOKEN",
    "ANTHROPIC_IDENTITY_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "AWS_CONTAINER_AUTHORIZATION_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AZURE_CLIENT_SECRET",
    "CLAUDE_CODE_CLIENT_KEY_PASSPHRASE",
    "CLAUDE_CODE_OAUTH_REFRESH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
)
CREDENTIAL_FILES = (
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_GHA_CREDS_PATH",
    "AWS_SHARED_CREDENTIALS_FILE",
    "CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "AZURE_FEDERATED_TOKEN_FILE",
    "ANTHROPIC_IDENTITY_TOKEN_FILE",
    "CLAUDE_CODE_CLIENT_KEY",
    "CLOUDSDK_AUTH_ACCESS_TOKEN_FILE",
    "AWS_CONFIG_FILE",
    "AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE",
    "AZURE_CLIENT_CERTIFICATE_PATH",
)
_SWITCH = re.compile(r"CLAUDE_CODE_USE_(?!POWERSHELL_TOOL\Z)\w+")
_SKIP = re.compile(r"CLAUDE_CODE_SKIP_\w+_AUTH")
_BASE_URL = re.compile(r"ANTHROPIC_\w*BASE_URL")
_PROXY = re.compile(r"https?_proxy|HTTPS?_PROXY")
# Each cloud's variables, by the switch that turns it on.
_OF_A_CLOUD = {
    "CLAUDE_CODE_USE_BEDROCK": re.compile(r"AWS_\w+|ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION"),
    "CLAUDE_CODE_USE_FOUNDRY": re.compile(r"(ANTHROPIC_FOUNDRY|AZURE)_\w+"),
    "CLAUDE_CODE_USE_VERTEX": re.compile(
        r"CLOUD_ML_REGION|(ANTHROPIC_VERTEX|CLOUDSDK|GOOGLE|VERTEX_REGION)_\w+"
    ),
}
_YES = frozenset({"1", "true", "yes", "on"})
_INSIDE = "http://{}:{}".format(*RELAY)
_MESSAGES = re.compile(r"/v1/messages(/count_tokens)?(\?beta=true)?")
_BEDROCK = re.compile(r"/model/([\w.:%-]+)/invoke(-with-response-stream)?")
_BEDROCK_MODEL = re.compile(r"([a-z-]+\.)?anthropic\.claude-[\w.:-]+")
_VERTEX = re.compile(
    r"/v1/projects/([\w.:-]+)/locations/([a-z0-9-]+)/publishers/anthropic/models/"
    r"(claude-[\w.@-]+|count-tokens):(streamRawPredict|rawPredict)"
)
_VERTEX_HOSTS = {
    "global": "aiplatform.googleapis.com",
    "us": "aiplatform.us.rep.googleapis.com",
    "eu": "aiplatform.eu.rep.googleapis.com",
}
# The addresses that get gcloud's token unasked: Vertex's global, regional, private and mTLS hosts.
_AT_VERTEX = re.compile(
    r"https://([a-z0-9-]+-)?aiplatform(-[a-z0-9-]+\.p|\.[a-z0-9-]+\.rep|\.mtls)?\.googleapis\.com"
    r"(:[0-9]+)?(/.*)?",
    re.ASCII | re.IGNORECASE,
)
_PLAIN = re.compile(r"[a-z0-9-]+")
_PROJECT = re.compile(r"[a-z0-9.:-]+")
_TOKEN = re.compile(r"[\x21-\x7e]+")
_FRESH_SECONDS = 300
_SOONEST_SECONDS = 10
_HOLD_SECONDS = 10
_LONGEST_TOKEN = 1 << 16


class Credential:
    """A secret from the environment, from a command that is asked again as its answer ages, or
    from a file that is read each time. It is empty where a provider sends none."""

    def __init__(self, fixed: str, command: str, file: str = "") -> None:
        self._value: str = fixed.strip()
        self._command: str = command
        self._file: str = file
        self._asked: float = 0
        self._fresh: float = 0
        self._lock: threading.Lock = threading.Lock()
        self.seen: set[str] = set()

    def text(self) -> str:
        if self._file:
            return self._read()
        with self._lock:
            if self._command and time.monotonic() - self._asked >= self._fresh:
                self._value, self._fresh = "", _SOONEST_SECONDS
                try:
                    self._value = self._ask()
                    self._fresh = _FRESH_SECONDS
                finally:
                    self._asked = time.monotonic()
            return self._value

    def forget(self, soonest: float = _SOONEST_SECONDS) -> None:
        """Ask the command again at the next request from `soonest` seconds after the last ask."""
        self._fresh = soonest

    def wait_for_renewal(self, header: str) -> bool:
        """Wait a few seconds for the file, if there is one, to hold another token than the
        authorization `header` did. Whether it does."""
        end = time.monotonic() + _HOLD_SECONDS
        with suppress(SandboxError):
            while self._file and time.monotonic() < end:
                if _as_bearer(self._read()) != header:
                    return True
                time.sleep(0.2)
        return False

    def _read(self) -> str:
        try:
            opened = os.open(self._file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(opened, "rb", 0) as file:
                status, text = os.fstat(opened), (file.read(_LONGEST_TOKEN) or b"").decode().strip()
        except (OSError, ValueError) as error:
            why = error.strerror if isinstance(error, OSError) else "it is not UTF-8"
            msg = f"the token file cannot be read: {why}"
            raise SandboxError(msg) from error
        if status.st_nlink > 1 or status.st_mode & 0o077 or os.geteuid() not in {0, status.st_uid}:
            msg = "the token file must be this user's alone, and have no hard link"
            raise SandboxError(msg)
        return text

    def _ask(self) -> str:
        try:
            answer = subprocess.check_output(  # noqa: S602
                self._command, shell=True, cwd="/", stdin=subprocess.DEVNULL, timeout=60
            )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            msg = "the credential command failed"
            raise SandboxError(msg) from error
        return answer.decode(errors="replace").strip()

    def token(self) -> str:
        if not _TOKEN.fullmatch(value := self.text()):
            self.forget()
            msg = "the credential is empty, or is not one word"
            raise SandboxError(msg)
        self.seen.add(value)
        return value

    def keys(self) -> sigv4.Keys:
        """AWS keys, in the form that `aws configure export-credentials` prints."""
        try:
            fields = strictjson.loads(self.text())
        except ValueError:
            fields = None
        names = ("AccessKeyId", "SecretAccessKey", "SessionToken")
        keys = sigv4.Keys(*(clean(fields.get(name)) if is_map(fields) else "" for name in names))
        if not (keys.access and keys.secret and all(map(_TOKEN.fullmatch, filter(None, keys)))):
            self.forget()
            msg = "the AWS keys are missing or incomplete"
            raise SandboxError(msg)
        self.seen.update(filter(None, keys))
        return keys


@dataclass(frozen=True)
class Provider:
    """`route` gives the address for a path that may pass, `sign` the headers that carry the
    credential, if one goes, and `inside` the variables that send Claude Code to the relay. With
    `version_in_body`, a request may name the API's version in its body, and the relay sets no
    version of its own. With `yields`, a header of ANTHROPIC_CUSTOM_HEADERS goes in place of the
    credential's header of that name."""

    route: Callable[[str], str]
    sign: Callable[[str, bytes], Mapping[str, str]]
    inside: Mapping[str, str]
    credential: Credential
    version_in_body: bool = False
    yields: bool = False


def _match(pattern: re.Pattern[str], path: str) -> re.Match[str]:
    if not (found := pattern.fullmatch(path)):
        msg = f"only model requests pass, and not {path[:60]!a}"
        raise RefusedError(msg)
    return found


def _base(variables: Mapping[str, str], name: str, default: str) -> str:
    msg = f"{name} must be an https address"
    url = (variables.get(name) or default).rstrip("/")
    try:
        parts = urlsplit(url)
    except ValueError as error:
        raise SandboxError(msg) from error
    local = parts.scheme == "http" and parts.hostname in {"127.0.0.1", "localhost", "::1"}
    if not ((parts.scheme == "https" and parts.hostname) or local) or {*"@?#"} & {*url}:
        raise SandboxError(msg)
    return url


def _needed(variables: Mapping[str, str], name: str, form: re.Pattern[str] = _PLAIN) -> str:
    if not form.fullmatch(value := variables.get(name, "")):
        msg = f"{name} is not set, or is no plain name"
        raise SandboxError(msg)
    return value


def _as_bearer(token: str) -> str:
    return f"Bearer {token}"


def _bearer(credential: Credential) -> Callable[[str, bytes], Mapping[str, str]]:
    return lambda _url, _body: {"authorization": _as_bearer(credential.token())}


def _key(credential: Credential) -> Callable[[str, bytes], Mapping[str, str]]:
    return lambda _url, _body: {"x-api-key": credential.token()}


def _unsigned(_url: str, _body: bytes) -> Mapping[str, str]:
    return {}


def _is_yes(value: str) -> bool:
    return value.strip().lower() in _YES


def _is_on(variables: Mapping[str, str], name: str) -> bool:
    return _is_yes(variables.get(name, ""))


def has_plain_host(variables: Mapping[str, str]) -> bool:
    """Whether the base URL of the provider that `variables` switch on is plain http."""
    clouds = ("BEDROCK", "VERTEX", "FOUNDRY")
    on = (f"{cloud}_" for cloud in clouds if _is_on(variables, f"CLAUDE_CODE_USE_{cloud}"))
    return variables.get(f"ANTHROPIC_{next(on, '')}BASE_URL", "").lower().startswith("http:")


def _for_a_gateway(provider: Provider, variables: Mapping[str, str]) -> Provider:
    """`provider` with no credential of the cloud's: ANTHROPIC_AUTH_TOKEN goes in its place, or
    nothing."""
    token = Credential(variables.get("ANTHROPIC_AUTH_TOKEN", ""), "")
    return replace(provider, sign=_bearer(token) if token.text() else _unsigned, credential=token)


def _anthropic(variables: Mapping[str, str], command: str, file: str) -> Provider:
    base = _base(variables, "ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    names = ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")
    name = next((name for name in names if variables.get(name)), names[0])
    credential = Credential(variables.get(name, ""), command, file)
    return Provider(
        lambda path: base + _match(_MESSAGES, path)[0],
        (_key if name == "ANTHROPIC_API_KEY" else _bearer)(credential),
        {"ANTHROPIC_BASE_URL": _INSIDE, name: STAND_IN},
        credential,
        yields=name != "ANTHROPIC_AUTH_TOKEN",
    )


def _foundry(variables: Mapping[str, str], command: str) -> Provider:
    name = "ANTHROPIC_FOUNDRY_BASE_URL"
    resource = "" if variables.get(name) else _needed(variables, "ANTHROPIC_FOUNDRY_RESOURCE")
    base = _base(variables, name, f"https://{resource}.services.ai.azure.com/anthropic")
    token = variables.get("ANTHROPIC_FOUNDRY_AUTH_TOKEN", "")
    credential = Credential(token or variables.get("ANTHROPIC_FOUNDRY_API_KEY", ""), command)
    keyed = not (command or token)
    return Provider(
        lambda path: base + _match(_MESSAGES, path)[0],
        (_key if keyed else _bearer)(credential),
        {name: _INSIDE, "CLAUDE_CODE_USE_FOUNDRY": "1", "CLAUDE_CODE_SKIP_FOUNDRY_AUTH": "1"},
        credential,
        yields=keyed,
    )


def _bedrock(variables: Mapping[str, str], command: str) -> Provider:
    name, region = "ANTHROPIC_BEDROCK_BASE_URL", _needed(variables, "AWS_REGION")
    base = _base(variables, name, f"https://bedrock-runtime.{region}.amazonaws.com")
    chosen = {v for k, v in variables.items() if SETTINGS.fullmatch(k) and k.endswith("MODEL")}
    bearer = "" if command else variables.get("AWS_BEARER_TOKEN_BEDROCK", "")
    keys = {
        "AccessKeyId": variables.get("AWS_ACCESS_KEY_ID"),
        "SecretAccessKey": variables.get("AWS_SECRET_ACCESS_KEY"),
        "SessionToken": variables.get("AWS_SESSION_TOKEN"),
    }
    credential = Credential(bearer or strictjson.text(keys), command)

    def route(path: str) -> str:
        model = unquote(_match(_BEDROCK, path)[1])
        if model not in chosen and not _BEDROCK_MODEL.fullmatch(model):
            msg = f"{model[:60]!a} is no Claude model, and the settings do not name it"
            raise RefusedError(msg)
        return base + path

    def sign(url: str, body: bytes) -> Mapping[str, str]:
        now = datetime.now(timezone.utc)
        return sigv4.headers(credential.keys(), "bedrock", region, url, body, now)

    skip = "CLAUDE_CODE_SKIP_BEDROCK_AUTH"
    skipped = _is_on(variables, skip)
    if skipped and command:
        msg = (
            f"{skip} keeps AWS keys from the gateway, and --credential-command gives them: leave"
            " the option out, and give the gateway's token, if any, in ANTHROPIC_AUTH_TOKEN"
        )
        raise SandboxError(msg)
    provider = Provider(
        route,
        _bearer(credential) if bearer else sign,
        {name: _INSIDE, "CLAUDE_CODE_USE_BEDROCK": "1", skip: "1"},
        credential,
        version_in_body=True,
    )
    return _for_a_gateway(provider, variables) if skipped and not bearer else provider


def _vertex(variables: Mapping[str, str], command: str) -> Provider:
    name = "ANTHROPIC_VERTEX_BASE_URL"
    project = _needed(variables, "ANTHROPIC_VERTEX_PROJECT_ID", _PROJECT)
    regions = {_needed(variables, "CLOUD_ML_REGION")}
    regions |= {value for key, value in variables.items() if key.startswith("VERTEX_REGION_")}
    gateway = _base(variables, name, "") if variables.get(name) else ""
    skip = "CLAUDE_CODE_SKIP_VERTEX_AUTH"
    skipped = _is_on(variables, skip)
    gcloud = "gcloud auth print-access-token"
    if gateway and not (_AT_VERTEX.fullmatch(gateway) or command or skipped):
        msg = (
            f"{name} names no host of Vertex's, and gcloud's token does not go there unasked: set"
            f" {skip}=1 for a gateway that holds the Google sign-in, or give"
            f" --credential-command='{gcloud}' to send that token"
        )
        raise SandboxError(msg)
    credential = Credential("", command or gcloud)

    def route(path: str) -> str:
        found = _match(_VERTEX, path)
        # Another project could keep a log of the requests for someone else.
        if found[1] != project or found[2] not in regions:
            msg = f"the settings do not name the project and region {found.groups()!a}"
            raise RefusedError(msg)
        host = _VERTEX_HOSTS.get(found[2], f"{found[2]}-aiplatform.googleapis.com")
        return (gateway or f"https://{host}/v1") + path.removeprefix("/v1")

    inside = {"CLAUDE_CODE_USE_VERTEX": "1", skip: "1"}
    provider = Provider(
        route,
        _bearer(credential),
        inside | {name: f"{_INSIDE}/v1"},
        credential,
        version_in_body=True,
    )
    return _for_a_gateway(provider, variables) if skipped and not command else provider


def setting_text(value: object) -> str:
    """A value of Claude Code's settings as text: its JSON text, if it is no string."""
    return value if is_str(value) else strictjson.text(value)


def settings_env(settings: JsonMap) -> dict[str, str]:
    """The variables that the `env` of Claude Code's `settings` sets, less lists, maps and null."""
    given = as_map(settings.get("env")).items()
    return {k: setting_text(v) for k, v in given if isinstance(v, (str, int, float))}


def clouds_on(variables: Mapping[str, str]) -> list[str]:
    """The CLAUDE_CODE_USE_ switches that `variables` turn on, but PowerShell's."""
    return [k for k, v in variables.items() if _SWITCH.fullmatch(k) and _is_yes(v)]


def routes_lacking(
    given: Mapping[str, str], variables: Mapping[str, str], also: tuple[str, ...] = ()
) -> list[str]:
    """The names in `given` that choose a host or a way to it, and that `variables` lack: a switch
    that clouds_on() counts or the skip of a cloud's sign-in, turned on, and, with a value, an
    ANTHROPIC_ base URL, a proxy, ANTHROPIC_CUSTOM_HEADERS, a variable of a cloud that `variables`
    turn on, or a name in `also`. A proxy's name counts in small and in capital letters."""
    held = {*variables, *(name.swapcase() for name in filter(_PROXY.fullmatch, variables))}
    exact = {"ANTHROPIC_CUSTOM_HEADERS", *also}
    clouds = (pattern for switch, pattern in _OF_A_CLOUD.items() if _is_on(variables, switch))
    patterns = [_BASE_URL, _PROXY, *clouds]

    def counts(name: str, value: str) -> bool:
        if _SWITCH.fullmatch(name) or _SKIP.fullmatch(name):
            return _is_yes(value)
        return bool(value) and (name in exact or any(each.fullmatch(name) for each in patterns))

    return [name for name, value in given.items() if name not in held and counts(name, value)]


def select(variables: Mapping[str, str], command: str, file: str = "") -> Provider:
    """The provider that `variables` select. `command`, if given, prints the credential, or `file`
    holds it. SandboxError if they select none that may start, such as two at once, or if `file`
    comes with a cloud, ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN or a `command`."""
    clouds = {
        "CLAUDE_CODE_USE_BEDROCK": _bedrock,
        "CLAUDE_CODE_USE_VERTEX": _vertex,
        "CLAUDE_CODE_USE_FOUNDRY": _foundry,
    }
    chosen = clouds_on(variables)
    if chosen[1:] or not clouds.keys() >= {*chosen}:
        served = "the relay serves one provider: the Claude API, Bedrock, Vertex or Foundry"
        msg = f"{served}, and these are set: {', '.join(chosen)}"
        raise SandboxError(msg)
    keyed = variables.get("ANTHROPIC_API_KEY") or variables.get("ANTHROPIC_AUTH_TOKEN")
    if file and (chosen or command or keyed):
        msg = (
            "--token-file works only with the Claude API, and not beside ANTHROPIC_API_KEY, "
            "ANTHROPIC_AUTH_TOKEN or --credential-command"
        )
        raise SandboxError(msg)
    provider = (
        clouds[chosen[0]](variables, command) if chosen else _anthropic(variables, command, file)
    )
    # This stops a start that lacks its credential, and fills credential.seen for the leak check.
    provider.sign("", b"")
    secrets = (variables.get(name, "") for name in SECRETS)
    provider.credential.seen.update(word for word in secrets if len(word) >= SHORTEST_PRIVATE)
    return provider
