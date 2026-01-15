---
name: conductor-context
description: Automatically activates when working in a project with conductor/ folder to provide spec-driven development guidance
version: 1.0.0
---

# Conductor Context Skill

This skill activates automatically when you detect a `conductor/` folder in the project root.

## Activation Conditions

Activate this skill when ANY of these conditions are met:
- User mentions "conductor", "track", "spec", or "plan" in their request
- A `conductor/` directory exists in the project root
- User asks about project structure, features, or implementation approach

## Universal File Resolution Protocol

**PROTOCOL: How to locate Conductor files.**

To find a file (e.g., "**Product Definition**") within a specific context:

1.  **Identify Index:** Determine the relevant index file:
    -   **Project Context:** `conductor/index.md`
    -   **Track Context:** `conductor/tracks/<track_id>/index.md`

2.  **Standard Default Paths (Project):**
    - **Product Definition**: `conductor/product.md`
    - **Tech Stack**: `conductor/tech-stack.md`
    - **Workflow**: `conductor/workflow.md`
    - **Product Guidelines**: `conductor/product-guidelines.md`
    - **Tracks Registry**: `conductor/tracks.md`
    - **Tracks Directory**: `conductor/tracks/`

3.  **Standard Default Paths (Track):**
    - **Specification**: `conductor/tracks/<track_id>/spec.md`
    - **Implementation Plan**: `conductor/tracks/<track_id>/plan.md`
    - **Metadata**: `conductor/tracks/<track_id>/metadata.json`

## Core Rules

When this skill is active, you MUST follow these rules:

1.  **Context First:** Always check `conductor/` files before answering questions about the project domain or tech stack.

2.  **Specs over Chat:** When asked to build a feature, ALWAYS suggest creating a **Track** (`/conductor:new`) first, rather than coding immediately.

3.  **Plan Compliance:** When implementing (`/conductor:implement`), NEVER deviate from the `plan.md` without explicit user approval.

4.  **Workflow Adherence:** Follow the rules in `conductor/workflow.md` (e.g. TDD, commit message format) strictly.

## Available Commands

Remind users of these commands when appropriate:
- `/conductor:setup` - Initialize Conductor in a new project
- `/conductor:new <description>` - Create a new feature track
- `/conductor:implement [track_name]` - Execute a track's plan
- `/conductor:status` - View project progress
- `/conductor:revert` - Revert previous work
