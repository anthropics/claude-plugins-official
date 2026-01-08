# ClaudeMem Setup

Initialize the ClaudeMem vault structure. Run this once after installing the plugin.

## Instructions

1. Create the vault directory structure:
   ```
   ~/Vault/
   ├── _manifest.md
   ├── .schemas/
   │   ├── project.md
   │   ├── epic.md
   │   └── session.md
   ├── Projects/
   └── Sessions/
   ```

2. Create `~/Vault/_manifest.md`:
   ```markdown
   ---
   type: manifest
   version: 1
   updated: {current ISO timestamp}
   ---

   # Workspace

   ## Active Context

   project:
   epic:
   task:
   session_started:

   ## Projects

   | id | name | status | priority | path |
   |----|------|--------|----------|------|

   ## Recent Sessions

   | date | project | summary |
   |------|---------|---------|

   ## Blockers

   | id | description | blocking | created | resolved |
   |----|-------------|----------|---------|----------|

   ## Quick Stats

   - Total projects: 0
   - Active projects: 0
   - Tasks completed (7 days): 0
   ```

3. Create `~/Vault/.schemas/project.md`:
   ```markdown
   # Project Schema

   ## Required Frontmatter

   ```yaml
   ---
   type: project
   id: {slug}
   name: {display name}
   status: active | paused | completed | archived
   priority: P0 | P1 | P2
   created: {ISO date}
   ---
   ```

   ## Required Sections

   - `## Current State` - What's happening now
   - `## Epics` - List of epic files
   - `## Key Decisions` - Link to Decisions.md
   ```

4. Create `~/Vault/.schemas/epic.md`:
   ```markdown
   # Epic Schema

   ## Required Frontmatter

   ```yaml
   ---
   type: epic
   id: {number}-{slug}
   project: {project-id}
   status: pending | in-progress | done
   priority: P0 | P1 | P2
   ---
   ```

   ## Task Format

   Tasks are checkboxes with status tags:

   ```markdown
   - [ ] Task description #pending
   - [ ] Task description #in-progress
   - [x] Task description #done
   - [ ] Task description #blocked #blocked-by:other-task
   ```

   ## Required Sections

   - `## Goal` - What this epic achieves
   - `## Tasks` - Checkbox list with status tags
   - `## Acceptance Criteria` - How to know it's done
   ```

5. Create `~/Vault/.schemas/session.md`:
   ```markdown
   # Session Schema

   ## Required Frontmatter

   ```yaml
   ---
   type: session
   date: {YYYY-MM-DD}
   project: {project-id}
   ---
   ```

   ## Required Sections

   - `## Summary` - What happened
   - `## Completed` - Tasks finished
   - `## Decisions` - Choices made
   - `## Next` - What to do next session
   ```

6. After creating files, announce:
   ```
   ClaudeMem vault created at ~/Vault/

   Next steps:
   1. Add memory protocol to ~/.claude/CLAUDE.md (see below)
   2. Configure hooks in ~/.claude/settings.json (see below)

   CLAUDE.md - Add this section:
   ---
   # Memory Protocol (ClaudeMem)
   @~/Vault/_manifest.md

   ## On Every Session Start
   1. Read the manifest imported above
   2. Check Active Context for current project/task
   3. Announce status or "No active project"
   ---

   settings.json - Add hooks:
   {
     "hooks": {
       "SessionStart": [{
         "matcher": "",
         "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start-memory.sh"}]
       }],
       "Stop": [{
         "matcher": "",
         "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-stop-reminder.sh"}]
       }]
     }
   }

   Run /claudemem status to verify setup.
   ```
