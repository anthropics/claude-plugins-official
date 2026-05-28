---
name: vision
description: Recognize and describe images using an external vision-capable model. Use this skill whenever the user provides an image path and asks what's in it, asks to analyze a screenshot, diagram, photo, or any image file. Also use when the user mentions looking at, reading, or describing an image/picture/screenshot/photo/diagram/chart.
---

# Vision — External image recognition

This skill enables image recognition by calling an external vision-capable LLM API (Claude, OpenAI, etc.) since the current model cannot process images directly.

## How it works

1. The user provides an image file path
2. Run `scripts/describe_image.py` with the image path and an optional prompt
3. The script calls the configured vision API and prints the description
4. Use the description to respond to the user's request

## Usage

```
python3 <skill-dir>/scripts/describe_image.py <image-path> [--prompt "custom prompt"]
```

The script returns the vision model's text description of the image. Use this output directly to answer the user's question — don't summarize or paraphrase it unless asked.

## Supported image formats

PNG, JPEG, GIF, WebP, BMP (anything the underlying vision model supports).

## Setup (one-time)

The script needs a vision API key. Set one of these environment variables:

**Option A — Anthropic (Claude) API:**
```bash
export VISION_API_PROVIDER=anthropic
export VISION_API_KEY=sk-ant-...
```

**Option B — OpenAI API:**
```bash
export VISION_API_PROVIDER=openai
export VISION_API_KEY=sk-...
export VISION_API_BASE_URL=https://api.openai.com/v1  # optional, default
```

**Option C — OpenAI-compatible endpoint (Ollama, vLLM, etc.):**
```bash
export VISION_API_PROVIDER=openai
export VISION_API_KEY=ollama
export VISION_API_BASE_URL=http://localhost:11434/v1
export VISION_MODEL=llava  # or minicpm-v, etc.
```

You can also configure via `~/.claude/vision.env`:
```
VISION_API_PROVIDER=anthropic
VISION_API_KEY=sk-ant-...
```

Optional overrides:
- `VISION_MODEL` — defaults to `claude-opus-4-7` (Anthropic) or `gpt-4o` (OpenAI)
- `VISION_MAX_TOKENS` — defaults to 4096

## Behavior

- If the image file doesn't exist, report the error to the user
- If no API key is configured, tell the user how to set it up (see Setup section)
- After getting the description, use it naturally in your response — the user shouldn't need to know a separate model was called unless they ask
