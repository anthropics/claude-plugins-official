"""What a model request may ask for: the model's answer, and nothing that reaches further."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from .. import strictjson
from ..strictjson import is_list, is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..strictjson import JsonMap

_FIELDS = frozenset({
    "anthropic_beta",
    "anthropic_version",
    "cache_control",
    "compaction",
    "context_management",
    "diagnostics",
    "fallbacks",
    "inference_geo",
    "max_tokens",
    "messages",
    "metadata",
    "model",
    "output_config",
    "output_format",
    "safeguards",
    "service_tier",
    "speed",
    "stop_sequences",
    "stream",
    "system",
    "temperature",
    "thinking",
    "tool_choice",
    "tools",
    "top_k",
    "top_p",
})
_REQUEST_FIELDS = {
    "": _FIELDS,
    ".fallbacks": frozenset({"max_tokens", "model", "output_config", "speed", "thinking"}),
}
_NEVER = frozenset({"container", "file_id", "mcp_servers", "uri", "url"})
_TEXT = frozenset({
    "cited_text",
    "content",
    "context",
    "data",
    "description",
    "document_title",
    "signature",
    "stop_sequences",
    "system",
    "text",
    "thinking",
    "title",
})
_OWN_JSON = frozenset({
    (".messages.content", "tool_use", "input"),
    (".messages.content.tool.definition", "custom", "input_schema"),
    (".messages.content.tool_changes.tool.definition", "custom", "input_schema"),
    (".fallbacks.output_config.format", "json_schema", "schema"),
    (".output_config.format", "json_schema", "schema"),
    (".output_format", "json_schema", "schema"),
    (".safeguards", "dangerous_tool_use", "classifier_context"),
    (".tools", "custom", "input_schema"),
})
_NAME = re.compile(r"[a-z0-9_]{1,80}")
_REACHING = re.compile(
    r"url|file|mcp.*|.*container.*|server_tool.*"
    r"|(?!(clear_tool_uses|clear_thinking|compact)_\d{8}\Z).*_\d{8}"
)
_TYPES = {
    "definition": frozenset({"custom"}),
    "source": frozenset({"base64", "content", "text"}),
    "tool": frozenset({"tool_definition", "tool_reference"}),
    "tools": frozenset({"custom"}),
}
_TOOLS = frozenset(_TYPES.keys() - {"source"})
# The version of the API whose requests this module checks.
VERSION = "2023-06-01"
_REACHING_BETA = re.compile(
    r"mcp|files|skills|code-exec|web-|url|container|managed-|message-batch|prompt-caching-scope"
)
_BETA = re.compile(r"[a-z0-9.-]+")


class RefusedError(Exception):
    """The request does not pass; the message says why."""


def betas(names: Iterable[object]) -> list[str]:
    """The beta names that may pass."""
    plain = (name.strip() for name in names if is_str(name))
    return [name for name in plain if _BETA.fullmatch(name) and not _REACHING_BETA.match(name)]


def _check(value: object, place: str) -> None:
    """`place` names the fields from the request down to `value`."""
    if is_str(value):
        field = place.rpartition(".")[2]
        address = "://" in value or value.startswith("//")
        if field in _TOOLS or (address and field not in _TEXT):
            msg = f"the field {field!a} may not hold this text"
            raise RefusedError(msg)
    elif is_list(value):
        for item in value:
            _check(item, place)
    elif is_map(value):
        _check_part(value, place)


def _check_part(part: JsonMap, place: str) -> None:
    field = place.rpartition(".")[2]
    kind = part.get("type", "custom" if field in _TOOLS else "none")
    plain = is_str(kind) and _NAME.fullmatch(kind) and not _REACHING.fullmatch(kind)
    types = _TYPES.get(field)
    if not plain or (types is not None and kind not in types):
        msg = f"the type {str(kind)[:40]!a} does not pass in {field!a}"
        raise RefusedError(msg)
    # For another caller the API adds a tool of its own that runs code.
    if part.get("allowed_callers", ["direct"]) != ["direct"]:
        msg = "the field 'allowed_callers' may name the model alone"
        raise RefusedError(msg)
    if field == "cache_control" and isinstance(part, dict):
        part.pop("scope", None)
    fields = _REQUEST_FIELDS.get(place)
    for name, inner in part.items():
        allowed = name not in _NEVER if fields is None else name in fields
        if not (allowed and _NAME.fullmatch(name)):
            msg = f"the field {name[:40]!a} does not pass"
            raise RefusedError(msg)
        if name == "tools" and not is_list(inner):
            msg = "the field 'tools' must be a list"
            raise RefusedError(msg)
        if name == "anthropic_beta" and not (is_list(inner) and betas(inner) == inner):
            msg = f"a beta in {str(inner)[:60]!a} does not pass"
            raise RefusedError(msg)
        if (place, kind, name) not in _OWN_JSON:
            _check(inner, f"{place}.{name}")


def checked(body: bytes, *, version_in_body: bool = False) -> bytes:
    """The body to send on: written anew, less the betas that may not pass and the scope of each
    cache_control. `version_in_body` says that it may name the API's version. RefusedError if the
    request may not go."""
    try:
        asked = strictjson.loads(body.decode())
    except ValueError as error:
        msg = "the body is not strict JSON in UTF-8, or passes a limit on numbers or nesting"
        raise RefusedError(msg) from error
    if not is_map(asked):
        msg = "the body is not a JSON object"
        raise RefusedError(msg)
    if "anthropic_version" in asked and not version_in_body:
        msg = "the field 'anthropic_version' does not pass here"
        raise RefusedError(msg)
    if is_list(named := asked.get("anthropic_beta")):
        asked = {**asked, "anthropic_beta": betas(named)}
    try:
        _check(asked, "")
        text = json.dumps(asked, ensure_ascii=False, separators=(",", ":"))
        return text.encode(errors="backslashreplace")
    except RecursionError as error:
        msg = "the body is nested too deep"
        raise RefusedError(msg) from error
