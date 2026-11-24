"""A git remote's address, in the one https spelling that the plugin records or shows."""

from __future__ import annotations

import re
from urllib.parse import quote, unquote, urlsplit

from .strictjson import has_lone_surrogate

# Every non-ASCII character whose NFKC form holds an "@", "?", "#" or "%".
LOOK_ALIKES = "\u2047\u2048\u2049\ufe16\ufe56\ufe5f\ufe6a\ufe6b\uff03\uff05\uff1f\uff20"

# A longer address is refused unread: the time to decode one grows with the square of its length.
_MAX_LENGTH = 2048


def _fully_unquoted(text: str) -> str:
    """`text` percent-decoded again and again, until that changes nothing."""
    while (decoded := unquote(text)) != text:
        text = decoded
    return text


def recordable(url: str) -> bool:
    """Whether `url` has the form of a recorded remote.

    The form is the https scheme, a lowercase host name, an optional port, and a path that is
    percent-encoded with uppercase hex digits. The URL has at most 2,048 characters. However
    often the path is decoded, it holds no `@`, `?`, `#`, ASCII control character, U+FFFD or
    look-alike. A look-alike is a non-ASCII character whose NFKC form holds an `@`, `?`, `#` or
    `%`. A percent-encoded byte that is not valid UTF-8 counts as U+FFFD.
    """
    if len(url) > _MAX_LENGTH:
        return False
    if not re.fullmatch(r"https://[a-z0-9.-]+(?::[0-9]+)?/(?:[A-Za-z0-9._~/-]|%[0-9A-F]{2})+", url):
        return False
    return not re.search(rf"[@?#\x00-\x1f\x7f\ufffd{LOOK_ALIKES}]", _fully_unquoted(url))


_HTTP_SCHEMES = frozenset({"http", "https"})
SCHEMES = _HTTP_SCHEMES | {"ssh", "git", "git+ssh"}


def sanitize(url: str | None) -> str | None:
    """`url` rewritten as an https URL without its userinfo, query and fragment, or None.

    The scheme becomes https and the host lowercase. A port survives only from an http or
    https URL. Scp-like `user@host:path` is read as ssh. A trailing `/` or `.git` is dropped.
    So the ssh and https spellings of one repository come out equal.

    An empty `url` is None, and so is a local path. So is a URL that:

    - has more than 2,048 characters, as given or in its recorded form;
    - has white space at either end;
    - has an ASCII control character, a `[` or a `]` in it;
    - has a raw byte in it that is not valid UTF-8 (a lone surrogate);
    - is in git's remote-helper form, `<transport>::<address>`;
    - has a scheme other than http, https, ssh, git and git+ssh;
    - has no host, or a host that is not ASCII letters, digits, dots and hyphens;
    - has a port that is neither empty nor one to five ASCII digits, at most 65535;
    - has no path left once a trailing `/` or `.git` is dropped;
    - has an `@`, `?`, `#`, ASCII control character, U+FFFD or look-alike left in its path,
      raw or percent-encoded any number of times;
    - is a `scheme://` URL whose userinfo has a non-ASCII character whose NFKC form holds a
      `/`, `?`, `#`, `@` or `:`;
    - is an http or https URL with an `@` or a look-alike in its query or fragment, raw or
      percent-encoded any number of times;
    - is an http or https URL with a `/`, percent-encoded once, in its path;
    - is an `ssh://`, `git://` or `git+ssh://` URL with a raw `?` or `#`;
    - is such a URL with a `/` or `[`, percent-encoded once, in its userinfo or host;
    - is a `git://` URL with userinfo;
    - is scp-like with a `:` or `/` ahead of its last `@`;
    - is scp-like with a host of one character.

    A look-alike is a non-ASCII character whose NFKC form holds an `@`, `?`, `#` or `%`, such
    as U+FF20. A percent-encoded byte that is not valid UTF-8 counts as U+FFFD.
    """
    text = url or ""
    if text != text.strip() or has_lone_surrogate(text) or len(text) > _MAX_LENGTH:
        return None
    if re.search(r"[\[\]\x00-\x1f\x7f]", text):
        return None
    if re.match(r"[A-Za-z0-9+.-]*::", text):
        return None
    if "://" in text:
        try:
            parts = urlsplit(text)
        except ValueError:
            return None
        scheme = parts.scheme.lower()
        if scheme not in SCHEMES:
            return None
        # Only plain ASCII digits count: urlsplit's own reading of a port differs by interpreter.
        host, _, port = parts.netloc.rpartition("@")[2].partition(":")
        if port and not (re.fullmatch(r"[0-9]{1,5}", port) and int(port) <= 65535):
            return None
        if scheme in _HTTP_SCHEMES:
            behind = _fully_unquoted(parts.query) + _fully_unquoted(parts.fragment)
            if re.search(f"[@{LOOK_ALIKES}]", behind):
                return None
            if re.search(r"%2[Ff]", parts.path):
                return None
        else:
            if re.search(r"[?#]", text):
                return None
            if re.search(r"%(?:2[Ff]|5[Bb])", parts.netloc):
                return None
            if scheme == "git" and "@" in parts.netloc:
                return None
        location = f"{host}:{int(port)}" if port and scheme in _HTTP_SCHEMES else host
        path = parts.path
    else:
        # Userinfo splits off first: an optional user@ group backtracks and leaks the secret.
        userinfo, _, rest = text.rpartition("@")
        if re.search(r"[:/]", userinfo):
            return None
        matched = re.match(r"([^@:/\\]{2,}):(.*)", rest)
        if not matched:
            return None
        location = matched[1]
        path = matched[2]
    # The host is tested ahead of lower(), which turns U+212A, the Kelvin sign, into "k".
    if not location.isascii():
        return None
    path = quote(unquote(path.strip("/"))).removesuffix(".git").rstrip("/")
    recorded = f"https://{location.lower()}/{path}"
    return recorded if recordable(recorded) else None
