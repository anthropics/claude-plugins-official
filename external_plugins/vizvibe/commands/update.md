---
description: Manually update vizvibe.mmd with recent work. Use when you want to explicitly update the trajectory instead of waiting for automatic updates.
---

# Update Viz Vibe Trajectory

Update `vizvibe.mmd` based on recent conversation and work.

## Steps:

1. Read current `vizvibe.mmd` to understand existing trajectory

2. Analyze recent work in this session:

   - What tasks were completed?
   - What new tasks were discovered?
   - What approaches worked or failed?

3. Update the trajectory:

   - Add new nodes for significant work
   - Close completed nodes
   - Add connections between related nodes
   - Update `@lastActive` to the most recently worked node

4. Apply proper styling:

   - Green borders for open tasks
   - Purple borders for closed tasks
   - Highlighted purple for last active
   - Wrap last active in `subgraph recent [RECENT]`

5. Summarize changes made to the trajectory

Reference the vizvibe skill for detailed formatting instructions.
