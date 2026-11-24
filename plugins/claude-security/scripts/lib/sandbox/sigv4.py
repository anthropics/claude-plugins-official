"""AWS Signature Version 4, for a POST with no query string."""

from __future__ import annotations

import hashlib
import hmac
from typing import TYPE_CHECKING, NamedTuple
from urllib.parse import quote, urlsplit

if TYPE_CHECKING:
    from datetime import datetime


class Keys(NamedTuple):
    access: str
    secret: str
    session: str

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        return "Keys(...)"


def headers(
    keys: Keys, service: str, region: str, url: str, body: bytes, now: datetime
) -> dict[str, str]:
    """The headers that sign the request."""
    parts = urlsplit(url)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    signed = {"host": parts.netloc, "x-amz-date": stamp}
    if keys.session:
        signed["x-amz-security-token"] = keys.session
    names = ";".join(signed)
    lines = "".join(f"{name}:{value}\n" for name, value in signed.items())
    # The path is encoded once more than it is on the wire.
    request = ("POST", quote(parts.path), "", lines, names, hashlib.sha256(body).hexdigest())
    scope = (stamp[:8], region, service, "aws4_request")
    digest = hashlib.sha256("\n".join(request).encode()).hexdigest()
    key = f"AWS4{keys.secret}".encode()
    for part in (*scope, "\n".join(("AWS4-HMAC-SHA256", stamp, "/".join(scope), digest))):
        key = hmac.digest(key, part.encode(), "sha256")
    credential = "/".join((keys.access, *scope))
    proof = f"Credential={credential}, SignedHeaders={names}, Signature={key.hex()}"
    return signed | {"authorization": f"AWS4-HMAC-SHA256 {proof}"}
