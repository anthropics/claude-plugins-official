# Skill Creator

A Claude Code skill for creating, improving, and benchmarking skills.

## Architecture

- `SKILL.md` — The skill definition loaded by Claude Code
- `scripts/` — Python CLI scripts for the skill creation lifecycle
- `agents/` — Sub-agent definitions (analyzer, comparator, grader)
- `eval-viewer/` — Web-based eval review tool with feedback + benchmark views
- `references/schemas.md` — JSON schema documentation for run artifacts

## Key Scripts

| Script | Purpose |
|--------|---------|
| `run_eval.py` | Run trigger evaluation for a skill description |
| `run_loop.py` | Iterative skill improvement loop |
| `generate_review.py` | Serve the eval review web page on port 3117 |
| `evaluate_description.py` | Improve skill description triggering accuracy |
| `aggregate_benchmark.py` | Aggregate benchmark results |
| `generate_report.py` | Generate eval reports |
| `package_skill.py` | Package a skill for distribution |
| `quick_validate.py` | Quick validation of skill structure |

## Eval Viewer

- **Entry point**: `python eval-viewer/generate_review.py <workspace-path>`
- Serves a self-contained HTML page on port 3117
- Reads runs from workspace (directories containing `outputs/`)
- Embeds all run data, prompts, and outputs into the page
- Auto-saves feedback via POST to `/api/feedback` → `feedback.json`
- Supports `--previous-workspace` for comparing outputs against prior iteration
- Supports `--benchmark` for quantitative stats tab
- Supports `--static <path>` to write standalone HTML instead of starting server

## Tech Stack

- Python 3 (stdlib only, no third-party dependencies required)
- Vanilla HTML/CSS/JS (SheetJS xlsx loaded from CDN for benchmark exports)

## Local Development

```bash
# Validate skill structure
python scripts/quick_validate.py .

# Run evals
python scripts/run_eval.py --skill-desc-file SKILL.md ...

# Start eval viewer
python eval-viewer/generate_review.py <workspace-path>

# Package skill
python scripts/package_skill.py .
```