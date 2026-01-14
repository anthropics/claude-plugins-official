---
description: Initialize vizvibe.mmd trajectory for this project. Creates the trajectory file and generates initial content based on codebase analysis.
---

# Initialize Viz Vibe Trajectory

Create an initial `vizvibe.mmd` file for this project.

## Steps:

1. **Check if `vizvibe.mmd` already exists**

   - If yes, inform user and show current trajectory summary
   - If no, continue with initialization

2. **Analyze the project thoroughly:**

   - Read `README.md` for project purpose and goals
   - Run `git log --oneline -n 30` for recent history
   - Examine key directories and files
   - Look for existing TODO lists, issues, or roadmaps

3. **Create `vizvibe.mmd` with this structure:**

```mermaid
flowchart TD
    %% === PROJECT GOALS ===
    %% Ultimate Goal: [The final objective of this project]
    %% Current Goal: [What we're working toward right now]
    %% @lastActive: project_start

    %% === START ===
    %% @project_start [start, closed, YYYY-MM-DD, username]
    project_start("Project Start<br/><sub>Brief project description</sub>")

    %% @ultimate_goal [end, opened, YYYY-MM-DD, username]
    ultimate_goal("Ultimate Goal<br/><sub>What success looks like</sub>")

    %% === COMPLETED WORK ===
    %% Add [closed] nodes for work already done

    %% === FUTURE WORK ===
    %% Add [opened] nodes for planned work

    %% === CONNECTIONS ===
    project_start --> ultimate_goal

    %% === STYLES ===
    %% Start node (muted gray)
    style project_start fill:#1a1a2e,stroke:#6b7280,color:#9ca3af,stroke-width:1px

    %% Ultimate Goal (muted gray)
    style ultimate_goal fill:#1a1a2e,stroke:#6b7280,color:#9ca3af,stroke-width:1px

    %% Closed tasks (soft purple)
    %% style node_id fill:#1a1a2e,stroke:#a78bfa,color:#c4b5fd,stroke-width:1px

    %% Open tasks (soft green)
    %% style node_id fill:#1a1a2e,stroke:#4ade80,color:#86efac,stroke-width:1px

    %% Last active (highlighted purple)
    %% style node_id fill:#2d1f4e,stroke:#c084fc,color:#e9d5ff,stroke-width:2px
```

4. **Populate the trajectory with:**

   - **Completed work**: Extract milestones from git history as `[closed]` nodes
   - **Future work**: Add known TODOs as `[opened]` nodes
   - **Project goals**: Ultimate goal and current focus
   - **Connections**: Link related nodes (parallel for independent, sequential for dependent)

5. **Wrap the last active node in RECENT subgraph:**

```mermaid
subgraph recent [RECENT]
    last_active_node_id
end
```

6. **Add `.vizvibe-state.json` to `.gitignore`** if not already present

7. **Ask user for feedback:**
   - "Is this trajectory accurate?"
   - "Any missing TODOs or planned features to add?"

Reference the vizvibe skill for detailed formatting instructions.
