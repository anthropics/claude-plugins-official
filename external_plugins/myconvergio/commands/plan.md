---
name: plan
description: Create a strategic execution plan using the strategic-planner agent
allowed-tools: ["Task"]
argument-hint: "<objective>"
---

# MyConvergio Plan

Create a comprehensive execution plan for complex tasks.

## Instructions

When the user runs `/myconvergio:plan <objective>`:

1. Invoke the strategic-planner agent using the Task tool:
   ```
   Use the Task tool with subagent_type="strategic-planner" and prompt:
   "Create a comprehensive execution plan for: <user's objective>"
   ```

2. The strategic-planner will create a wave-based plan with:
   - STATUS DASHBOARD with phases
   - Parallel lanes for independent tasks
   - Atomic tasks with verification commands
   - Checkpoint commits every 3-5 tasks

3. Save the plan to `docs/plans/[ProjectName]Plan[Date].md`

4. Ask if user wants to execute in parallel (if running in Kitty)

## Example

User: `/myconvergio:plan Migrate the monolith to microservices`

Result: Creates detailed plan with phases, task assignments, and verification steps.
