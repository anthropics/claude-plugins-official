#!/usr/bin/env python3
"""Call an external vision-capable LLM to describe an image.

Supports:
- Anthropic (Claude) API
- OpenAI API and OpenAI-compatible endpoints (Ollama, vLLM, etc.)

Config via environment variables or ~/.claude/vision.env file.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib import request
from urllib.error import URLError


def load_env():
    """Load config from environment, falling back to ~/.claude/vision.env."""
    env_file = Path.home() / ".claude" / "vision.env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")


def get_image_mime_type(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return mime_map.get(ext, "image/png")


def encode_image(filepath: str) -> str:
    """Read image file and return base64-encoded string."""
    with open(filepath, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def describe_anthropic(image_path: str, prompt: str, api_key: str, model: str, max_tokens: int) -> str:
    """Call Anthropic Messages API with vision."""
    image_data = encode_image(image_path)
    media_type = get_image_mime_type(image_path)

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    base_url = os.environ.get("VISION_API_BASE_URL", "https://api.anthropic.com")
    url = f"{base_url.rstrip('/')}/v1/messages"

    req = request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    resp = request.urlopen(req, timeout=120)
    data = json.loads(resp.read().decode("utf-8"))

    # Extract text from response
    for block in data.get("content", []):
        if block.get("type") == "text":
            return block["text"]

    return "[No text in response]"


def describe_openai(image_path: str, prompt: str, api_key: str, model: str, max_tokens: int) -> str:
    """Call OpenAI-compatible chat completions API with vision."""
    image_data = encode_image(image_path)
    media_type = get_image_mime_type(image_path)
    data_url = f"data:{media_type};base64,{image_data}"

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    base_url = os.environ.get("VISION_API_BASE_URL", "https://api.openai.com/v1")
    url = f"{base_url.rstrip('/')}/chat/completions"

    req = request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    resp = request.urlopen(req, timeout=120)
    data = json.loads(resp.read().decode("utf-8"))

    return data["choices"][0]["message"]["content"]


def main():
    load_env()

    parser = argparse.ArgumentParser(description="Describe an image using a vision LLM")
    parser.add_argument("image", help="Path to the image file")
    parser.add_argument(
        "--prompt", "-p",
        default="Please describe this image in detail. Include all visible text, objects, colors, layout, and any notable details.",
        help="Prompt to send with the image",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"Error: image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    provider = os.environ.get("VISION_API_PROVIDER", "").lower()
    api_key = os.environ.get("VISION_API_KEY", "")
    model = os.environ.get("VISION_MODEL", "")
    max_tokens = int(os.environ.get("VISION_MAX_TOKENS", "4096"))

    if not api_key:
        print(
            "Error: No vision API configured.\n\n"
            "Set up one of these environment variables (or ~/.claude/vision.env):\n\n"
            "  Option A — Anthropic API:\n"
            "    export VISION_API_PROVIDER=anthropic\n"
            "    export VISION_API_KEY=sk-ant-...\n\n"
            "  Option B — OpenAI API:\n"
            "    export VISION_API_PROVIDER=openai\n"
            "    export VISION_API_KEY=sk-...\n\n"
            "  Option C — Local model (Ollama etc.):\n"
            "    export VISION_API_PROVIDER=openai\n"
            "    export VISION_API_KEY=ollama\n"
            "    export VISION_API_BASE_URL=http://localhost:11434/v1\n"
            "    export VISION_MODEL=llava",
            file=sys.stderr,
        )
        sys.exit(1)

    # Default model per provider
    if not model:
        model = "claude-opus-4-7" if provider == "anthropic" else "gpt-4o"

    try:
        if provider == "anthropic":
            result = describe_anthropic(args.image, args.prompt, api_key, model, max_tokens)
        elif provider in ("openai", "openai-compatible"):
            result = describe_openai(args.image, args.prompt, api_key, model, max_tokens)
        else:
            print(f"Error: unknown VISION_API_PROVIDER '{provider}'. Use 'anthropic' or 'openai'.", file=sys.stderr)
            sys.exit(1)

        print(result)

    except URLError as e:
        print(f"Error calling vision API: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
