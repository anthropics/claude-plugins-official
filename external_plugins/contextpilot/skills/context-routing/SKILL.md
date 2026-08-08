---
name: context-routing
description: Instructions for utilizing ContextPilot adaptive project-context routing packets
---

# ContextPilot Adaptive Context Routing Skill

## Context Packet Structure
When ContextPilot is active, incoming prompts are automatically enriched with a structured `<CONTEXT_PILOT>` block. The packet provides curated, high-relevance architectural and file context bounded by your context budget:

```xml
<CONTEXT_PILOT>

Task classification:
Action: <read|debug|modify|test|explain|refactor|unknown> | Domain: <domain_tags> | Target Entities: <entities>

Relevant architecture:
<Overview of components, patterns, and module boundaries>

Relevant files:
- <filepath> (score: <relevance>, reasons: <why_selected>)
  [Structural Summary / Interface Outline / Critical Ranges]

Relevant symbols:
- <symbol_name> (<kind>) in <filepath>:<line> — <signature>

Relevant tests:
- <test_filepath> (covers <target_files>)

Project constraints:
- <CLAUDE.md rules, architectural invariants, monorepo boundaries>

Dependency relationships:
- <source_file> -> <target_file> (<edge_type>)

</CONTEXT_PILOT>
```

## Guidelines for Claude
1. **Trust Routed Context First**: The files and symbol signatures provided inside `<CONTEXT_PILOT>` represent the direct callers, callees, and dependencies relevant to the user's immediate intent.
2. **Minimize Full File Reads**: Use the symbol signatures, interface outlines, and line ranges in the packet to answer questions directly without reading massive files unless exact full implementations are required.
3. **Follow Dependency Boundaries**: Use the provided dependency relationships to ensure refactorings and modifications preserve interfaces across callers and callees.
4. **Adhere to Project Constraints**: Respect monorepo package boundaries and test file associations extracted by ContextPilot.
