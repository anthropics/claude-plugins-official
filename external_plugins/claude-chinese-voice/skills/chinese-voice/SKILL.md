---
name: chinese-voice
description: Chinese TTS voice output — Claude's replies are read aloud. Use to set up voice, switch voices, or toggle speech on/off.
user-invocable: true
allowed-tools:
  - Bash(powershell *)
  - Write
  - Read
---

# /chinese-voice — Chinese Voice Output

Sets up Chinese TTS so Claude reads responses aloud. Uses Windows built-in
Microsoft Huihui voice (zh-CN). No cloud services, no API keys — everything
runs locally.

## Quick start

```
/chinese-voice setup
```

This installs the speak.ps1 TTS script and configures Claude to auto-read
each response.

## Commands

| Command | What it does |
|---------|-------------|
| `setup` | Full setup: install script + configure |
| `test`  | Speak a test phrase to check audio |
| `voice` | Show available Chinese voices |
| `off`   | Stop reading responses aloud |

## How it works

```
Claude responds → speak.ps1 reads text → Microsoft Huihui speaks
```

The script uses COM SAPI (built into Windows), selects the zh-CN voice,
and speaks synchronously.

## Troubleshooting

If you can't hear the voice:
1. Right-click speaker icon → Sounds → Playback
2. Find your active playback device (green checkmark)
3. Open Volume Mixer → check powershell.exe isn't muted
4. Run `/chinese-voice test` to verify

## Voice input

For voice INPUT (speaking TO Claude):
- Press `Win+H` to open Windows voice typing
- Speak your message
- Press `Enter` to send

Windows built-in voice typing supports Chinese Mandarin natively.

## Available voices

| Voice | Language | Gender |
|-------|----------|--------|
| Microsoft Huihui | zh-CN | Female |
| Microsoft Kangkang | zh-CN | Male (install via Windows Settings) |
| Microsoft Yaoyao | zh-CN | Female Child (install via Windows Settings) |

To add more voices: Windows Settings → Time & Language → Speech → Add voices.
