# Claude Interactive - Human-in-the-Loop Result Filtering

Filter search results BEFORE they enter your context window.

## Trigger Phrases

When the user includes these phrases, use interactive mode:
- "interactively" (e.g., "search for X interactively")
- "let me pick" (e.g., "find files and let me pick which to use")
- "filter results" (e.g., "grep for errors, filter results first")
- "select results" (e.g., "glob for configs, let me select results")

## Interactive Search Protocol

When triggered, follow this exact workflow:

### Step 1: Run the search
Execute the requested search tool (Grep, Glob, or WebSearch) with appropriate parameters.

### Step 2: Present numbered results
Format results like this:
```
Found N results for "[query]":

1. path/to/file.ts:42 - matching line preview...
2. path/to/other.ts:18 - another match preview...
3. ...
```

### Step 3: Ask user to select
Use AskUserQuestion with these exact parameters:
```
question: "[query] - Select which results to keep:"
header: "Results"
multiSelect: true
options:
  - label: "1", description: "[first result preview]"
  - label: "2", description: "[second result preview]"
  - label: "All", description: "Keep all results"
  - label: "None", description: "Discard all results"
```

### Step 4: Use only selected results
- If user selects specific numbers: Use ONLY those results
- If user selects "All": Use all results
- If user selects "None": Acknowledge and proceed without using results

## Example Interaction

**User:** "Find all files with useState interactively"

**Claude:**
1. Runs: `Grep pattern="useState" type="ts"`
2. Shows:
   ```
   Found 5 results for "useState":
   1. src/App.tsx:12 - const [count, setCount] = useState(0)
   2. src/Form.tsx:8 - const [value, setValue] = useState('')
   3. src/Modal.tsx:15 - const [open, setOpen] = useState(false)
   4. src/List.tsx:22 - const [items, setItems] = useState([])
   5. src/tests/App.test.tsx:5 - import { useState } from 'react'
   ```
3. Asks via AskUserQuestion: "useState - Select which results to keep:"
4. User picks: "1, 2, 3"
5. Claude continues using ONLY App.tsx, Form.tsx, and Modal.tsx

## Auto-Mode (Optional)

If `.claude-interactive-automode` file exists in project root:
- ALL search operations trigger interactive mode automatically
- No trigger phrase needed
- Toggle with: `/interactive auto on|off`

Check status: `/interactive auto status`

## Why This Matters

Search results consume context tokens. Every result returned by Grep, Glob, or WebSearch takes space in your context window.

By filtering results BEFORE they enter context:
- You control what Claude "sees"
- Irrelevant matches don't waste tokens
- Responses stay focused on what matters

This is especially valuable for:
- Large codebases with many matches
- Broad searches that return noise
- When you know which files are relevant
