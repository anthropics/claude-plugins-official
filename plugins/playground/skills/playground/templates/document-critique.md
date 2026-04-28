# Document Critique Template

Use this template when the playground helps review and critique documents: SKILL.md files, READMEs, specs, proposals, or any text that needs structured feedback with approve/reject/comment workflow.

## Layout

```
+---------------------------+--------------------+
|                           |                    |
|  Document content         |  Suggestions panel |
|  with line numbers        |  (filterable list) |
|  and suggestion           |  • Approve         |
|  highlighting             |  • Reject          |
|                           |  • Comment         |
|                           |                    |
+---------------------------+--------------------+
|  Prompt output (approved + commented items)    |
|  [ Copy Prompt ]                               |
+------------------------------------------------+
```

## Key components

### Document panel (left)
- Display full document with line numbers
- Highlight lines with suggestions using a colored left border
- Color-code by status: pending (amber), approved (green), rejected (red with opacity)
- Click a suggestion card to scroll to the relevant line

### Suggestions panel (right)
- Filter tabs: All / Pending / Approved / Rejected
- Stats in header showing counts for each status
- Each suggestion card shows:
  - Line reference (e.g., "Line 3" or "Lines 17-24")
  - The suggestion text
  - Action buttons: Approve / Reject / Comment (or Reset if already decided)
  - Optional textarea for user comments

### Prompt output (bottom)
- Generates a prompt only from approved suggestions and user comments
- Groups by: Approved Improvements, Additional Feedback, Rejected (for context)
- Copy button with "Copied!" feedback

## State structure

```javascript
const suggestions = [
  {
    id: 1,
    lineRef: "Line 3",
    targetText: "description: Creates interactive...",
    suggestion: "The description is too long. Consider shortening.",
    category: "clarity",  // clarity, completeness, performance, accessibility, ux
    status: "pending",    // pending, approved, rejected
    userComment: ""
  },
  // ... more suggestions
];

let state = {
  suggestions: [...],
  activeFilter: "all",
  activeSuggestionId: null
};
```

## Suggestion matching to lines

Match suggestions to document lines by parsing the lineRef:

```javascript
const suggestion = state.suggestions.find(s => {
  const match = s.lineRef.match(/Line[s]?\s*(\d+)/);
  if (match) {
    const targetLine = parseInt(match[1]);
    return Math.abs(targetLine - lineNum) <= 2; // fuzzy match nearby lines
  }
  return false;
});
```

## Document rendering

Handle markdown-style formatting inline:

```javascript
// Skip ``` lines, wrap content in code-block-wrapper
if (line.startsWith('```')) {
  inCodeBlock = !inCodeBlock;
  // Open or close wrapper div
}

// Headers
if (line.startsWith('# ')) renderedLine = `<h1>...</h1>`;
if (line.startsWith('## ')) renderedLine = `<h2>...</h2>`;

// Inline formatting (outside code blocks)
renderedLine = renderedLine.replace(/`([^`]+)`/g, '<code>$1</code>');
renderedLine = renderedLine.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
```

## Prompt output generation

Only include actionable items:

```javascript
function updatePrompt() {
  const approved = state.suggestions.filter(s => s.status === 'approved');
  const withComments = state.suggestions.filter(s => s.userComment?.trim());

  if (approved.length === 0 && withComments.length === 0) {
    // Show placeholder
    return;
  }

  let prompt = 'Please update [DOCUMENT] with the following changes:\n\n';

  if (approved.length > 0) {
    prompt += '## Approved Improvements\n\n';
    for (const s of approved) {
      prompt += `**${s.lineRef}:** ${s.suggestion}`;
      if (s.userComment?.trim()) {
        prompt += `\n  → User note: ${s.userComment.trim()}`;
      }
      prompt += '\n\n';
    }
  }

  // Additional feedback from non-approved items with comments
  // Rejected items listed for context only
}
```

## Styling highlights

```css
.doc-line.has-suggestion {
  border-left: 3px solid #bf8700;  /* amber for pending */
  background: rgba(191, 135, 0, 0.08);
}

.doc-line.approved {
  border-left-color: #1a7f37;  /* green */
  background: rgba(26, 127, 55, 0.08);
}

.doc-line.rejected {
  border-left-color: #cf222e;  /* red */
  background: rgba(207, 34, 46, 0.08);
  opacity: 0.6;
}
```

## Pre-populating suggestions

When building a critique playground for a specific document:

1. Read the document content
2. Analyze and generate suggestions with:
   - Specific line references
   - Clear, actionable suggestion text
   - Category tags (clarity, completeness, performance, accessibility, ux)
3. Embed both the document content and suggestions array in the HTML

## Example use cases

- SKILL.md review (skill definition quality, completeness, clarity)
- README critique (documentation quality, missing sections, unclear explanations)
- Spec review (requirements clarity, missing edge cases, ambiguity)
- Proposal feedback (structure, argumentation, missing context)
- Code comment review (docstring quality, inline comment usefulness)
