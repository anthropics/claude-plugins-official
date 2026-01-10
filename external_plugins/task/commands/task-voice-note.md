# Add a voice note to decisions

## Instructions

When the user runs `/task-voice-note`, help them add a voice transcription to the task:

## Method 1: Manual Transcription (Quickest)

1. **User dictates** using their OS voice typing:
   - **Windows**: Win + H
   - **macOS**: Fn Fn (or Control + Command + Space)
   - **Linux**: Various tools (speech-to-text)

2. **User pastes** the transcribed text

3. **Add to decisions.log** with `[VOICE]` tag:
   ```
   [2026-01-10T15:30:00.000Z] [VOICE] <transcribed text>
   ```

## Method 2: Whisper Local (Recommended)

### Setup (one-time)

1. **Install Whisper**:
   ```bash
   pip install openai-whisper
   ```

2. **Install ffmpeg** (required):
   - Windows: `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `apt install ffmpeg`

### Usage

1. **Record audio** (any format: mp3, wav, m4a):
   - Use Voice Recorder, Audacity, or phone
   - Save as `note.mp3` or similar

2. **Transcribe with Whisper**:
   ```bash
   whisper note.mp3 --model tiny --output_format txt
   ```

3. **View transcription**:
   ```bash
   cat note.txt
   ```

4. **I will add it to decisions.log** with `[VOICE]` tag

### Whisper Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 39M | Fastest | Basic |
| base | 74M | Fast | Good |
| small | 244M | Medium | Better |
| medium | 769M | Slow | Great |
| large | 1550M | Slowest | Best |

Recommendation: Start with `tiny` or `base` for quick notes.

## Method 3: Whisper Python Script

Create a helper script for quick voice notes:

```python
#!/usr/bin/env python3
# save as voice-note.py

import whisper
import sys
from datetime import datetime

model = whisper.load_model("tiny")
result = model.transcribe(sys.argv[1])

timestamp = datetime.now().isoformat()
print(f"[{timestamp}] [VOICE] {result['text']}")
```

Usage:
```bash
python voice-note.py note.mp3 >> .claude/task/<task_id>/decisions.log
```

## Quick Workflow

1. **Record**: Use phone or computer to record a quick audio note
2. **Transcribe**: Run `whisper audio.mp3 --model tiny`
3. **Tell me**: "Add this voice note: [paste transcription]"
4. **Done**: I'll add it to decisions.log with [VOICE] tag

## Example Entry

```
[2026-01-10T15:30:00.000Z] [VOICE] Decided to use Redis for caching
because PostgreSQL was too slow. Benchmark showed 10x improvement.
Need to set up Redis cluster before next sprint.
```

## Benefits

- **Hands-free logging** while coding
- **Capture thoughts quickly** without stopping work
- **Natural language** decision documentation
- **Searchable** transcriptions in decisions.log
- **Offline** with Whisper local

## Tips

- Keep notes short (30 seconds - 2 minutes)
- Speak clearly but naturally
- State the decision/observation first
- Include reasoning if possible
- Mention any follow-up needed
