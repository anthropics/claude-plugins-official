---
description: Execute an agentic browser workflow with multi-step navigation and actions
argument-hint: <workflow-json>
allowed-tools: []
---

# Run Workflow Command

Execute a multi-step agentic browser workflow composed of navigation, actions, extractions, loops, and conditionals.

## Usage

```
/run-workflow <workflow-json>
```

## Arguments

- **workflow-json** (required): JSON workflow definition

## Workflow Structure

```json
{
  "name": "Workflow Name",
  "description": "Workflow description",
  "start_url": "https://example.com",
  "use_session": true,
  "steps": [
    {"type": "navigate", "url": "https://example.com/login"},
    {"type": "action", "action": "Click login button"},
    {"type": "extract", "instruction": "Extract user profile", "save_to": "profile"}
  ],
  "initial_context": {},
  "output_variables": ["profile"]
}
```

## Step Types

- **navigate**: Navigate to a URL
- **action**: Perform an action (click, fill, etc.)
- **extract**: Extract data with AI
- **extract_markdown**: Extract markdown content
- **loop**: Iterate over an array
- **conditional**: Execute steps conditionally
- **subworkflow**: Execute nested workflow
- **wait**: Wait for condition or duration

## Examples

```
/run-workflow '{"name":"Product Scraper","start_url":"https://shop.com","steps":[{"type":"navigate","url":"https://shop.com/products"},{"type":"extract","instruction":"Extract all products","save_to":"products"}]}'
```

## Features

- Multi-step browser automation
- Variable management
- Loops and conditionals
- Nested workflows
- Session persistence
- Error handling

## Notes

- Requires `SCRAPEGRAPHAI_API_KEY` environment variable
- Returns workflow execution result with step-by-step results
- Use for complex multi-page scraping scenarios
- Supports variable interpolation in URLs and actions


