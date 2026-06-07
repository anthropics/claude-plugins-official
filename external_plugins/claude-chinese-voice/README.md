# Claude Code Chinese Voice

Chinese TTS voice output plugin for Claude Code. Uses Windows built-in speech
synthesis — no cloud API, no keys, zero cost.

## Features

- **Auto-read responses**: Claude's replies spoken aloud in Chinese (Microsoft Huihui)
- **Voice switching**: Support for Huihui, Kangkang (male), Yaoyao (child)
- **Voice input guide**: Win+H voice typing setup for speaking TO Claude
- **Offline**: Everything runs locally on Windows

## Requirements

- Windows 10 or 11
- Chinese speech recognition installed (Settings → Time & Language → Speech)
- Claude Code

## Install

```bash
# Clone the plugin
git clone https://github.com/<your-username>/claude-chinese-voice.git

# Or install via Claude Code plugins
```

Then in Claude Code:

```
/chinese-voice setup
```

## Usage

- `/chinese-voice setup` — one-time setup
- `/chinese-voice test` — test audio output
- `/chinese-voice voice` — list Chinese voices
- `/chinese-voice off` — disable auto-read

## How it works

The plugin installs a PowerShell script (`speak.ps1`) that:
1. Reads text piped from Claude's output
2. Selects Microsoft Huihui voice (zh-CN)
3. Speaks using COM SAPI

## License

MIT
