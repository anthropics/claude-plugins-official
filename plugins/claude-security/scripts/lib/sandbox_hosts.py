"""The `host:port` that model requests go to, for the firewall to allow.

It is the host that a base URL names or, with no URL, the provider's own. No host for signing in
is given. With a URL no variable is read. With no URL, the only ones read are AWS_REGION,
CLOUD_ML_REGION and ANTHROPIC_FOUNDRY_RESOURCE, each only on its own provider's job.
"""

from __future__ import annotations

import enum
import re
from typing import TYPE_CHECKING, final

from .exhaustiveness import unreachable

if TYPE_CHECKING:
    from collections.abc import Mapping


CLAUDE_API_HOST = "api.anthropic.com"


class Provider(enum.Enum):
    """A provider, as scripts/scan_user.py's command line spells it."""

    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    FOUNDRY = "foundry"


class HostError(Exception):
    """A refusal to give any host; the message names what to set."""


@final
class _Hosts:
    """The port and the highest port, the pattern for each cloud's region or resource, and the
    patterns for a host's label and a base URL."""

    PORT = 443
    # 53 letters keep the longest region at 63 characters, the most that a DNS label can have.
    BEDROCK_REGION = "(?:us|eu|ap|sa|ca|me|af|il|mx|us-gov)-[a-z]{1,53}-[0-9]{1,2}"
    # A single region. The bounds keep the host's first label to 63 characters.
    VERTEX_REGION = "[a-z]{2,20}-[a-z]{1,20}[0-9]{1,2}"
    FOUNDRY_RESOURCE = "[a-z0-9][a-z0-9-]{0,61}[a-z0-9]"
    LABEL = "[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    URL = (
        f"https://(?P<host>(?:{LABEL}[.])+(?![0-9]){LABEL})(?::(?P<port>[1-9][0-9]{{0,4}}))?"
        "(?:/[A-Za-z0-9._~/-]*)?"
    )
    LAST_PORT = 65535
    NOT_ACCEPTED = "is not accepted (this message does not show it)"


def allowed(provider: Provider, environ: Mapping[str, str], url: str) -> str:
    """The `host:port` that model requests go to: the one that `url` names or, if `url` is empty,
    `provider`'s own, with a cloud's region or resource read from `environ`. Raises HostError when
    the URL is not accepted or, with no URL, that region or resource is unset or not accepted."""
    if url:
        return _named_by(url)
    if provider is Provider.ANTHROPIC:
        host = CLAUDE_API_HOST
    elif provider is Provider.BEDROCK:
        host = f"bedrock-runtime.{_region(environ)}.amazonaws.com"
    elif provider is Provider.VERTEX:
        host = _vertex_host(environ)
    elif provider is Provider.FOUNDRY:
        host = _foundry_host(environ)
    else:
        unreachable(provider)
    return f"{host}:{_Hosts.PORT}"


def _named_by(url: str) -> str:
    """The `host:port` that `url` names, with port 443 if it names no port. Raises HostError when
    the URL's form is not accepted."""
    found = re.fullmatch(_Hosts.URL, url)
    if found and (port := int(found["port"] or _Hosts.PORT)) <= _Hosts.LAST_PORT:
        return f"{found['host']}:{port}"
    msg = (
        f"the model_base_url input {_Hosts.NOT_ACCEPTED}. Set it to https://HOST[:PORT][/PATH] and "
        "nothing more, not even a space or a line break, such as "
        "https://{your-gateway}:8443/bedrock. HOST holds only a to z, 0 to 9, - and dots, with at "
        "least one dot, and is not an IP address. PATH holds only a to z, A to Z, 0 to 9 and "
        "- . _ ~ /."
    )
    raise HostError(msg)


def _region(environ: Mapping[str, str]) -> str:
    """AWS_REGION's value in `environ`. Raises HostError when it is unset or not accepted."""
    region = environ.get("AWS_REGION", "")
    if re.fullmatch(_Hosts.BEDROCK_REGION, region):
        return region
    fault = f"holds a value that {_Hosts.NOT_ACCEPTED}" if region else "is not set"
    msg = (
        f"AWS_REGION {fault}: set the aws_region input, or that variable, to an AWS region in "
        "lower case and nothing else, such as us-east-1; regions whose hosts do not end in "
        "amazonaws.com, such as cn-north-1, are not supported"
    )
    raise HostError(msg)


def _vertex_host(environ: Mapping[str, str]) -> str:
    """Google Cloud's host for CLOUD_ML_REGION's value in `environ`. Raises HostError when it is
    unset or not accepted."""
    region = environ.get("CLOUD_ML_REGION", "")
    if region == "global":
        return "aiplatform.googleapis.com"
    if region in {"eu", "us"}:
        return f"aiplatform.{region}.rep.googleapis.com"
    if re.fullmatch(_Hosts.VERTEX_REGION, region):
        return f"{region}-aiplatform.googleapis.com"
    fault = _Hosts.NOT_ACCEPTED if region else "is not set"
    msg = (
        f"the vertex_region input {fault}. Set it to global, us, eu or a single region such as "
        "us-east5, in lower case."
    )
    raise HostError(msg)


def _foundry_host(environ: Mapping[str, str]) -> str:
    """Foundry's host for ANTHROPIC_FOUNDRY_RESOURCE's value in `environ`. Raises HostError when it
    is unset or not accepted."""
    resource = environ.get("ANTHROPIC_FOUNDRY_RESOURCE", "")
    if re.fullmatch(_Hosts.FOUNDRY_RESOURCE, resource):
        return f"{resource}.services.ai.azure.com"
    fault = _Hosts.NOT_ACCEPTED if resource else "is not set"
    msg = (
        f"the foundry_resource input {fault}. Set it to the resource's name in lower case, such as "
        "my-resource: the part of its address between https:// and the first dot. For a gateway, "
        "give model_base_url instead."
    )
    raise HostError(msg)
