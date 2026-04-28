# Diff Review Template

Use this template when the playground is about reviewing code diffs: git commits, pull requests, code changes with interactive line-by-line commenting for feedback.

## Layout

```
+-------------------+----------------------------------+
|                   |                                  |
|  Commit Header:   |  Diff Content                    |
|  • Hash           |  (files with hunks)              |
|  • Message        |  with line numbers               |
|  • Author/Date    |  and +/- indicators              |
|                   |                                  |
+-------------------+----------------------------------+
|  Prompt Output Panel (fixed bottom-right)            |
|  [ Copy All ]                                        |
|  Shows all comments formatted for prompt             |
+------------------------------------------------------+
```

Diff review playgrounds display git diffs with syntax highlighting. Users click lines to add comments, which become part of the generated prompt for code review feedback.

## Control types for diff review

| Feature | Control | Behavior |
|---|---|---|
| Line commenting | Click any diff line | Opens textarea below the line |
| Comment indicator | Badge on commented lines | Shows which lines have feedback |
| Save/Cancel | Buttons in comment box | Persist or discard comment |
| Copy prompt | Button in prompt panel | Copies all comments to clipboard |

## Diff rendering

Parse diff data into structured format for rendering:

```javascript
const diffData = [
  {
    file: "path/to/file.py",
    hunks: [
      {
        header: "@@ -41,13 +41,13 @@ function context",
        lines: [
          { type: "context", oldNum: 41, newNum: 41, content: "unchanged line" },
          { type: "deletion", oldNum: 42, newNum: null, content: "removed line" },
          { type: "addition", oldNum: null, newNum: 42, content: "added line" },
        ]
      }
    ]
  }
];
```

## Line type styling

| Type | Background | Text Color | Prefix |
|---|---|---|---|
| `context` | transparent | default | ` ` (space) |
| `addition` | green tint (#dafbe1 light / rgba(46,160,67,0.15) dark) | green (#1a7f37 light / #7ee787 dark) | `+` |
| `deletion` | red tint (#ffebe9 light / rgba(248,81,73,0.15) dark) | red (#cf222e light / #f85149 dark) | `-` |
| `hunk-header` | blue tint (#ddf4ff light) | blue (#0969da light) | `@@` |

## Comment system

Each diff line gets a unique identifier for comment tracking:

```javascript
const comments = {}; // { lineId: commentText }

function selectLine(lineId, lineEl) {
  // Deselect previous
  document.querySelectorAll('.diff-line.selected').forEach(el =>
    el.classList.remove('selected'));
  document.querySelectorAll('.comment-box.active').forEach(el =>
    el.classList.remove('active'));

  // Select new
  lineEl.classList.add('selected');
  document.getElementById(`comment-box-${lineId}`).classList.add('active');
}

function saveComment(lineId) {
  const textarea = document.getElementById(`textarea-${lineId}`);
  const comment = textarea.value.trim();

  if (comment) {
    comments[lineId] = comment;
  } else {
    delete comments[lineId];
  }

  renderDiff(); // Re-render to show comment indicator
  updatePromptOutput();
}
```

## Prompt output format

Generate a structured code review format:

```javascript
function updatePromptOutput() {
  const commentKeys = Object.keys(comments);

  if (commentKeys.length === 0) {
    promptContent.innerHTML = '<span class="no-comments">Click on any line to add a comment...</span>';
    return;
  }

  let output = 'Code Review Comments:\n\n';

  commentKeys.forEach(lineId => {
    const lineEl = document.querySelector(`[data-line-id="${lineId}"]`);
    const file = lineEl.dataset.file;
    const lineNum = lineEl.dataset.lineNum;
    const content = lineEl.dataset.content;

    output += `📍 ${file}:${lineNum}\n`;
    output += `   Code: ${content.trim()}\n`;
    output += `   Comment: ${comments[lineId]}\n\n`;
  });

  promptContent.textContent = output;
}
```

## Data attributes for line elements

Store metadata on each line element for prompt generation:

```html
<div class="diff-line addition"
     data-line-id="0-1-5"
     data-file="src/utils/handler.py"
     data-line-num="45"
     data-content="subagent_id = tracker.register()">
```

## Pre-populating with real data

To create a diff viewer for a specific commit:

1. Run `git show <commit> --format="%H%n%s%n%an%n%ad" -p`
2. Parse the output into the `diffData` structure
3. Include commit metadata in the header section

## Theme support

Support both light and dark modes:

```css
/* Light mode */
body { background: #f6f8fa; color: #1f2328; }
.file-card { background: #ffffff; border: 1px solid #d0d7de; }
.diff-line.addition { background: #dafbe1; }
.diff-line.deletion { background: #ffebe9; }

/* Dark mode */
body { background: #0d1117; color: #c9d1d9; }
.file-card { background: #161b22; border: 1px solid #30363d; }
.diff-line.addition { background: rgba(46, 160, 67, 0.15); }
.diff-line.deletion { background: rgba(248, 81, 73, 0.15); }
```

## Interactive features

- **Hover hint:** Show "Click to comment" tooltip on line hover
- **Comment indicator:** Badge (💬) on lines with saved comments
- **Toast notification:** "Copied to clipboard!" feedback on copy
- **Edit existing:** Allow editing previously saved comments

## Example topics

- Git commit review (single commit diff with line comments)
- Pull request review (multiple commits, file-level and line-level comments)
- Code diff comparison (before/after refactoring)
- Merge conflict resolution (showing both versions with annotations)
- Code audit (security review with findings per line)
