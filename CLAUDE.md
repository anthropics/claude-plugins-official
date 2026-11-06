# Instructions for Claude

## MEMORY MANAGEMENT

Caleb uses ONE shared memory across every Claude app (Code, Cowork, Chat, Artifacts).
There are two layers — each fact lives in exactly one of them:

1. **Notion Memory (shared brain)** — who Caleb is, his preferences, and all projects
   across apps. Reach it through the Notion connector.
2. **This repo's memory folders** — notes that only matter for this repo
   (code decisions, status, style).

At the START of each session:
- Notion: fetch id `"memory"` (About page + Memories database); use memory search for specifics
- Read `memory/memory.md`, then the relevant files in `workspace/`

At the END of each session (or when meaningful work is finished):
- Personal or cross-project facts (preferences, goals, new projects, decisions that
  affect other work) → update Notion Memory (search first; update the existing entry)
- Repo-specific facts → update `memory/memory.md` and the relevant `workspace/` files,
  and commit them with the work
- Keep everything concise — remove outdated info

NEVER duplicate information across files or between the repo and Notion.
ALWAYS prefer updating existing entries over adding new ones.
If the Notion connector is unavailable, say so and continue with the repo files.

## Layout

```
memory/memory.md                            core repo memory (summary + pointers)
workspace/projects/goals.md                 what's being built & why
workspace/projects/decisions.md             choices already made (dated, with reasoning)
workspace/projects/current-status.md        where things stand now
workspace/preferences/coding-style.md       formatting, naming, conventions
workspace/preferences/communication.md      repo-specific response notes (general ones live in Notion)
workspace/knowledge-base/research-notes.md  gathered information
workspace/knowledge-base/reference-data.md  key reference material
```
