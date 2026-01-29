# Artifact Plugin

Creates interactive HTML artifacts — self-contained single-file explorers that let users configure something visually through controls, see a live preview, and copy out a prompt.

## What is an Artifact?

An artifact is a self-contained HTML file with:
- Interactive controls on one side
- A live preview on the other
- A prompt output at the bottom with a copy button

The user adjusts controls, explores visually, then copies the generated prompt back into Claude.

## When to Use

Use this plugin when the user asks for an interactive artifact, playground, explorer, or visual tool for a topic — especially when the input space is large, visual, or structural and hard to express as plain text.

## Templates

The skill includes templates for common artifact types:
- **design-playground** — Visual design decisions (components, layouts, spacing, color, typography)
- **data-explorer** — Data and query building (SQL, APIs, pipelines, regex)
- **concept-map** — Learning and exploration (concept maps, knowledge gaps, scope mapping)
- **writing-tool** — Writing and content (tone, document structure, audience)

## Installation

Add this plugin to your Claude Code configuration to enable the artifact skill.
