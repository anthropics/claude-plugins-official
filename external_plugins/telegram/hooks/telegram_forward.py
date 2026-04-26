#!/usr/bin/env python3
"""
Forward Claude assistant text back to the originating Telegram chat — both
during a turn (after each tool call) and at the end of a turn. Wired into
two Claude Code hook events:

  - PostToolUse: ships any new assistant text since the last fire. Lets the
    user see "Let me check..." narration as it lands, instead of waiting
    for the whole turn to finish.
  - Stop: trailing flush after the model emits its final text block.

Watermarking by assistant-message UUID prevents duplicate sends across the
two events and across multiple PostToolUse fires within a single turn.

State lives at:
  ~/.claude/hooks/state/telegram_forward_<session_id>.json
Log:
  ~/.claude/hooks/state/telegram_forward.log

Wire in ~/.claude/settings.json:

    {
      "hooks": {
        "PostToolUse": [
          { "hooks": [{ "type": "command",
                        "command": "python3 ~/.claude/hooks/telegram_forward.py" }] }
        ],
        "Stop": [
          { "hooks": [{ "type": "command",
                        "command": "python3 ~/.claude/hooks/telegram_forward.py" }] }
        ]
      }
    }

The `/telegram:stream` skill installs both the hook file and the settings.json
wiring; you can also use either piece independently.

Optional environment overrides:

  TELEGRAM_FORWARD_PREFIX   — string prepended to each chunk (default: empty).
                              Useful for distinguishing model output from
                              other senders in shared chats; e.g. "[claude]".
  TELEGRAM_FORWARD_CHUNK    — soft byte cap per Telegram message
                              (default: 4000; Telegram hard cap is 4096).

Apache-2.0 — same license as the rest of this plugin.
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

HOME = Path.home()
ENV_FILE = HOME / ".claude/channels/telegram/.env"
ACCESS_FILE = HOME / ".claude/channels/telegram/access.json"
STATE_DIR = HOME / ".claude/hooks/state"
LOG_FILE = STATE_DIR / "telegram_forward.log"

PREFIX = os.environ.get("TELEGRAM_FORWARD_PREFIX", "").strip()
CHUNK_LIMIT = int(os.environ.get("TELEGRAM_FORWARD_CHUNK", "4000"))

CHANNEL_RE = re.compile(
    r'<channel\s+source="plugin:telegram:telegram"'
    r'[^>]*?chat_id="(?P<chat_id>\d+)"'
    r'(?:[^>]*?message_id="(?P<message_id>\d+)")?',
    re.DOTALL,
)


def log(msg: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def load_token() -> str | None:
    """Read TELEGRAM_BOT_TOKEN from the channel's .env file. The env file is
    written by /telegram:configure; the same file is read by the MCP server."""
    try:
        for line in ENV_FILE.read_text().splitlines():
            m = re.match(r"^TELEGRAM_BOT_TOKEN=(.*)$", line.strip())
            if m:
                return m.group(1)
    except Exception:
        return None
    return None


def load_allowed_chats() -> set[str]:
    """Parse the access.json allowlist so we never forward to a chat the user
    hasn't explicitly trusted. Empty set = no allowlist defined; in that case
    we let the channel server's own gating decide and forward unconditionally
    to whatever chat sent the inbound message."""
    try:
        data = json.loads(ACCESS_FILE.read_text())
        allowed = set(data.get("allowFrom") or [])
        allowed.update((data.get("groups") or {}).keys())
        return allowed
    except Exception:
        return set()


def chunk(text: str, limit: int = CHUNK_LIMIT) -> list[str]:
    """Split text on paragraph/line/space boundaries to fit Telegram's 4096
    char-per-message hard cap. Soft default 4000 leaves room for prefixes."""
    out: list[str] = []
    rest = text
    while len(rest) > limit:
        cut = rest.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        out.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        out.append(rest)
    return out


def send(token: str, chat_id: str, text: str) -> dict:
    payload = {"chat_id": chat_id, "text": text, "disable_notification": False}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def extract_text(content) -> str:
    """User messages have content as either a string or a list of blocks; we
    only care about the textual portion when scanning for the channel tag."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return "".join(parts)
    return ""


def read_rows(transcript_path: str) -> list[dict]:
    out: list[dict] = []
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def find_user_idx(rows: list[dict]) -> tuple[int | None, str | None, str | None]:
    """Return the index of the most recent user row whose content carries the
    plugin:telegram:telegram channel tag, plus the chat_id and message_id."""
    for i in range(len(rows) - 1, -1, -1):
        r = rows[i]
        if r.get("type") != "user":
            continue
        text = extract_text(r.get("message", {}).get("content", ""))
        m = CHANNEL_RE.search(text)
        if m:
            return i, m.group("chat_id"), m.group("message_id")
    return None, None, None


def find_uuid_row(rows: list[dict], target_uuid: str | None) -> int:
    if not target_uuid:
        return -1
    for i, r in enumerate(rows):
        if r.get("uuid") == target_uuid:
            return i
    return -1


def collect_new_texts(rows: list[dict], start_after_idx: int) -> tuple[list[str], str | None]:
    """Walk rows[start_after_idx+1:], gather text blocks from assistant rows.
    Returns ([texts], uuid-of-last-assistant-row-with-text)."""
    texts: list[str] = []
    last_uuid: str | None = None
    for r in rows[start_after_idx + 1:]:
        if r.get("type") != "assistant":
            continue
        had_text = False
        for c in r.get("message", {}).get("content", []) or []:
            if isinstance(c, dict) and c.get("type") == "text":
                t = (c.get("text") or "").strip()
                if t:
                    texts.append(t)
                    had_text = True
        if had_text:
            last_uuid = r.get("uuid", last_uuid)
    return texts, last_uuid


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        log(f"bad payload: {e}: {raw[:200]!r}")
        return

    session_id = payload.get("session_id", "unknown")
    event = payload.get("hook_event_name") or payload.get("event") or "unknown"
    log(f"FIRED event={event} session={session_id[:8]} stop_hook_active={payload.get('stop_hook_active')}")

    # Don't recursively re-fire if a Stop hook caused work.
    if event == "Stop" and payload.get("stop_hook_active"):
        return

    transcript_path = payload.get("transcript_path")
    if not transcript_path or not Path(transcript_path).is_file():
        log(f"  no transcript: {transcript_path!r}")
        return

    token = load_token()
    if not token:
        log("  no TELEGRAM_BOT_TOKEN in env file; nothing to do")
        return

    rows = read_rows(transcript_path)
    last_user_idx, chat_id, message_id = find_user_idx(rows)
    if last_user_idx is None or not chat_id:
        log("  no telegram channel tag in any prior user msg")
        return

    allowed = load_allowed_chats()
    if allowed and chat_id not in allowed:
        log(f"  chat {chat_id} not in allowFrom — skipping")
        return

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"telegram_forward_{session_id}.json"
    try:
        prev_state = json.loads(state_file.read_text())
    except Exception:
        prev_state = {}
    # Backward-compat: prior versions stored the watermark under "last_uuid".
    prev_shipped_uuid = prev_state.get("last_shipped_uuid") or prev_state.get("last_uuid")

    start_after = find_uuid_row(rows, prev_shipped_uuid)
    if start_after < last_user_idx:
        start_after = last_user_idx

    texts, last_uuid = collect_new_texts(rows, start_after)

    # Wait briefly for transcript stability — the JSONL writer is async, so a
    # Stop firing immediately after the model's final text block can race the
    # flush, and PostToolUse can fire while the post-tool text is mid-write.
    waited = 0.0
    prev_sig = (len(rows), len(texts))
    stable_ticks = 0
    max_wait = 5.0 if event == "Stop" else 1.0
    while waited < max_wait:
        time.sleep(0.25)
        waited += 0.25
        rows = read_rows(transcript_path)
        new_idx, new_chat, new_msg = find_user_idx(rows)
        if new_idx is not None:
            last_user_idx, chat_id, message_id = new_idx, new_chat, new_msg
        start_after = find_uuid_row(rows, prev_shipped_uuid)
        if start_after < last_user_idx:
            start_after = last_user_idx
        texts, last_uuid = collect_new_texts(rows, start_after)
        sig = (len(rows), len(texts))
        if sig == prev_sig and texts:
            stable_ticks += 1
            if stable_ticks >= 2:
                break
        else:
            stable_ticks = 0
            prev_sig = sig
    if waited:
        log(f"  waited {waited:.2f}s; got {len(texts)} new text block(s)")

    if not texts:
        # PostToolUse will frequently fire with nothing new (the model wrote no
        # text before calling the next tool). Stop with nothing means we
        # already shipped everything earlier in the turn. Both are normal.
        log(f"  no new assistant text after start_after={start_after}")
        return

    body = "\n\n".join(texts)
    if PREFIX:
        body = f"{PREFIX}\n\n{body}"
    parts = chunk(body, CHUNK_LIMIT)
    sent_ids: list[int] = []
    try:
        for part in parts:
            resp = send(token, chat_id, part)
            sent_ids.append(resp.get("result", {}).get("message_id"))
    except Exception as e:
        log(f"  send failed after {len(sent_ids)}/{len(parts)}: {e}")
        return

    new_state = {
        "last_shipped_uuid": last_uuid,
        "chat_id": chat_id,
        "last_event": event,
        "ts": int(time.time()),
    }
    tmp = state_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(new_state))
    os.replace(tmp, state_file)
    log(f"  forwarded {len(parts)} chunk(s) on {event} to chat {chat_id} (ids: {sent_ids}, hwm={str(last_uuid)[:8]})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"unhandled: {e}")
