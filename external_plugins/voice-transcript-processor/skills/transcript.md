---
name: transcript
description: Process a voice recording transcript into structured project documents. Extracts instructions, answers to previous questions, research tasks, feedback, and decisions — presents the structured document for review before executing.
user_invocable: true
---

# Voice Transcript Processor

You are processing a voice recording transcript into structured project context documents that will keep you aligned with the user's instructions across sessions.

## Step 1: Receive the Transcript

Check if a file path or text was provided as the argument to this skill.

- If a **file path** was provided: read that file
- If **raw text** was provided: use it directly
- If **nothing** was provided: ask the user to either paste the transcript or provide the file path

## Step 2: Parse and Categorize

Read the full transcript carefully. Extract every piece of content into one of these categories:

### Instructions
Things the user wants Claude to do — in this session or upcoming work.
**Signals:** "I want", "can you", "make it", "change the", "add a", "remove", "fix", "update", "build", "create", imperative phrases, feature requests, bug reports

### Answers to Previous Questions
The user responding to questions Claude asked in a prior session.
**Signals:** Direct answers, "yes to your question", "the answer is", "to answer what you asked", "about that thing you mentioned", anything that sounds like a response rather than a new request

### Research Tasks
Things to investigate, look up, verify, or analyze.
**Signals:** "can you look up", "research", "find out", "check if", "what is the", "how does", "compare", "what are the options for"

### Feedback
User's reaction to previous work Claude did.
**Signals:** "that looks good", "I don't like", "that was wrong", "perfect", "the problem with", "it should have been", "next time", positive or negative reactions to deliverables

### Decisions Made
Architectural, business, content, or design decisions the user has committed to.
**Signals:** "we're going to", "I've decided", "the plan is", "going with", "sticking with", "I've chosen", "from now on"

### Todo / Task Updates
Completion status updates on existing project tasks.
**Signals:** "that's done", "mark complete", "cross off", "still need to", "defer", "cancel", "don't bother with", "skip"

### Context / Notes
Anything that doesn't fit above but is useful background — constraints, stakeholder info, deadlines, dependencies, things to be aware of.

---

## Step 3: Write the Session Document

Create the `.claude/voice/` directory if it doesn't exist.

Write **`.claude/voice/LATEST_CONTEXT.md`** (always overwrite this file — it's the "current context" for the session):

```markdown
# Voice Session Context
**Processed:** [date and time]
**Source:** [file path or "pasted transcript"]

---

## Instructions for This Session
[Numbered list of every instruction extracted. Be specific — preserve the user's intent exactly.]

## Answers to Your Previous Questions
[Q: [what Claude asked] → A: [what the user answered]]
[If none found, write: "No answers to previous questions found in this transcript."]

## Research Tasks
- [ ] [task]
[If none, omit this section]

## Feedback on Previous Work
[Bullet list of feedback items, labeled POSITIVE or NEEDS CHANGE]
[If none, omit this section]

## Decisions Made
[Bullet list of decisions]
[If none, omit this section]

## Todo Updates
[What to mark complete, add, defer, or cancel]
[If none, omit this section]

## Context / Notes
[Background info, constraints, anything else]
[If none, omit this section]
```

Also write an **archive copy** at `.claude/voice/session_[YYYYMMDD_HHMMSS].md` with identical content so the user has a history of all processed sessions.

---

## Step 4: Update Pending Tasks

Read `.claude/voice/PENDING_TASKS.md` if it exists. If it doesn't exist, create it fresh.

- Add all new **Instructions** and **Research Tasks** from this session as unchecked items `- [ ]`
- Mark any **Todo Updates** that indicate completion as `- [x]`
- Remove any items explicitly cancelled
- Keep existing incomplete tasks

Write the updated file with this structure:

```markdown
# Pending Tasks

> Auto-maintained by /transcript — do not edit manually.
> Last updated: [date]

## Instructions / To-Do
- [ ] [task] *(added [date])*
- [x] [completed task] *(completed [date])*

## Research Tasks
- [ ] [task] *(added [date])*
```

---

## Step 5: Present the Structured Document

Output the full contents of `LATEST_CONTEXT.md` directly in the conversation so the user can review exactly what was extracted before anything is acted on.

Present it as a fenced markdown block with a header:

```
Here's what I extracted from your transcript:

---
[full LATEST_CONTEXT.md content]
---

Files saved:
- .claude/voice/LATEST_CONTEXT.md
- .claude/voice/session_[timestamp].md
- .claude/voice/PENDING_TASKS.md

Ready to start. Should I begin with [first instruction]?
```

Wait for the user to confirm before executing. If the user says "yes", "go", "start", or gives any approval signal, begin working through the instructions in order. If they correct something, update `LATEST_CONTEXT.md` with the correction and proceed.

---

## Important Behaviors

- **Preserve intent:** When extracting instructions, keep the user's meaning intact. Do not paraphrase in ways that lose nuance.
- **Don't skip ambiguous items:** If you're not sure what category something belongs to, include it under Context / Notes rather than discarding it.
- **Voice transcripts ramble:** The same idea may appear multiple times or be half-finished. Consolidate duplicates into a single clean instruction.
- **Filler words are noise:** Ignore "um", "uh", "like", "you know", etc. Focus on meaning.
- **Assume accountability:** The user recorded this to direct your work. Treat every extracted instruction as a committed directive unless it's clearly tentative ("maybe", "I'm thinking about", "not sure yet").
