---
description: "Launch The Fabric — autonomous SDLC agent team that builds a full application from a business objective"
argument-hint: "[business objective]"
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Agent, TeamCreate, TeamDelete, TaskCreate, TaskUpdate, TaskGet, TaskList, SendMessage]
---

You have been asked to launch The Fabric — an autonomous SDLC agent team.

**Business objective provided:** `$ARGUMENTS`

## Instructions

1. If `$ARGUMENTS` is empty or not provided, ask the user: "What would you like me to build? Describe your business objective and I'll take it from here."  Wait for their response before proceeding.

2. Once you have the business objective, invoke the `fabric-sdlc` skill to execute the full SDLC protocol.
