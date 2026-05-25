# Agent Triggering: Best Practices

Complete guide to writing trigger descriptions that cause an agent to be dispatched reliably.

## Where trigger descriptions live

An agent file has two places that talk about triggering:

1. **`description:` field in YAML frontmatter.** Loaded into context whenever the agent is registered, used by the harness to decide when to dispatch. Keep it flat prose.
2. **A "When to invoke" section in the agent body.** Loaded only when the agent is actually invoked. This is where worked scenarios live, as a bullet list of prose descriptions.

## Format

### `description:` field

```
description: Use this agent when [conditions]. Typical triggers include [scenario 1 phrased as a prose noun phrase], [scenario 2], and [scenario 3]. See "When to invoke" in the agent body for worked scenarios.
```

Rules:
- Single line of flat prose within the YAML scalar.
- Name 2-4 trigger scenarios as noun phrases.
- End with the pointer to the body's "When to invoke" section.

### "When to invoke" body section

```markdown
## When to invoke

[Two to four representative scenarios as prose bullets. Each describes the situation
in third person and what the agent should do.]

- **[Short scenario name].** [What the situation looks like — what just happened or what
  the user is asking for — and what the agent should do in response.]
- **[Short scenario name].** [Same.]
```

## Anatomy of a good scenario

### Scenario name (the bold lead)

**Purpose:** A short noun phrase identifying the situation type.

**Good names:**
- *User-requested review after a feature lands.*
- *Proactive review of newly-written code.*
- *Pre-PR sanity check.*
- *PR updated with new logic.*

**Bad names:**
- *Normal usage.* (not specific)
- *User needs help.* (vague)

### Scenario body (after the lead)

**Purpose:** Describe what happens and what the agent should do — in prose, third person, no quoted utterances.

**Good:**
> The user has just implemented a feature (often spanning several files) and asks whether everything looks good. Run a review of the recent diff and report findings.

**Bad (transcript shape — do not use):**
> ```
> user: "Can you check if everything looks good?"
> assistant: "I'll use the reviewer agent..."
> ```

The bad version mixes a turn-marker shape into the agent file. Keep scenarios as situation descriptions in prose.

## Trigger types to cover

Aim for 2-4 scenarios that span these axes:

### Explicit request
The user directly asks for what the agent does.
- *User-requested security check.* The user explicitly asks for a security review of recent code.

### Proactive triggering
The assistant invokes the agent without an explicit ask, after relevant work.
- *Proactive review after writing database code.* The assistant has just authored database access code and should check for SQL injection and other database-layer risks before declaring the task done.

### Implicit request
The user implies need without naming the agent.
- *Code-clarity complaint.* The user describes existing code as confusing or hard to follow. Treat as a request to refactor for readability.

### Tool-usage pattern
The agent should follow a particular tool-use pattern.
- *Post-test-edit verification.* The assistant has just made multiple edits to test files. Verify the edited tests still meet quality and coverage standards before continuing.

## Phrasing variation

If the same intent is commonly phrased multiple ways, mention that in prose:

> **Pre-PR sanity check.** The user signals (in any phrasing — "ready to open a PR", "I think we're done here", "let's ship this") that they're about to open a pull request.

Don't write three near-duplicate scenarios that differ only in the literal phrase — collapse them into one prose scenario that names the variation.

## How many scenarios?

- **Minimum: 2.** Usually one explicit + one proactive.
- **Recommended: 3-4.** Explicit, proactive, and one implicit or edge case.
- **Maximum: 5.** More than that bloats the body without adding routing signal.

## Worked example

### Prose triggers in `description:`

```yaml
description: Use this agent when you need to review code. Typical triggers include user-requested review after a feature lands, proactive review of freshly-written code, and a pre-PR sanity check. See "When to invoke" in the agent body for worked scenarios.
```

### Scenarios as situation descriptions in the body

```markdown
## When to invoke

- **User-requested review.** The user asks for a review of recent changes (any phrasing). Run a review of the unstaged diff.
```

### Trigger condition only — output format goes elsewhere

```markdown
- **Review.** The user asks for a review. Run the review and report findings as specified in the Output Format section.
```

## Template library

### Code review agent

```yaml
description: Use this agent when you need to review code for adherence to project guidelines and best practices. Typical triggers include the user asking for a review of a feature they just implemented, proactive review of newly-written code before declaring a task done, and a pre-PR sanity check. See "When to invoke" in the agent body.
```

```markdown
## When to invoke

- **User-requested review after a feature lands.** The user has implemented a feature and asks whether the result looks good. Review the recent diff and report findings.
- **Proactive review of newly-written code.** The assistant has just authored new code in response to a user request. Run a self-review before declaring the task done.
- **Pre-PR sanity check.** The user signals readiness to open a pull request. Review the full diff first.
```

### Test generation agent

```yaml
description: Use this agent when you need to generate tests for code that lacks them. Typical triggers include the user explicitly asking for tests for a function or module, and the assistant proactively generating tests after writing new code that has no test coverage. See "When to invoke" in the agent body.
```

```markdown
## When to invoke

- **Explicit test request.** The user asks for tests covering a specific function, module, or feature. Generate a comprehensive test suite.
- **Proactive coverage after new code.** The assistant has just written new code with no accompanying tests. Generate tests before declaring the task done.
```

### Documentation agent

```yaml
description: Use this agent when you need to write or improve documentation for code, especially APIs. Typical triggers include the user asking for docs on a specific function or endpoint, and proactive documentation generation after the assistant adds new API surface. See "When to invoke" in the agent body.
```

```markdown
## When to invoke

- **Explicit doc request.** The user asks for documentation for a specific surface (function, endpoint, module).
- **Proactive docs for new API surface.** The assistant has just added new API endpoints or public functions without docstrings.
```

### Validation agent

```yaml
description: Use this agent when you need to validate code before commit or merge. Typical triggers include the user signaling readiness to commit, and an explicit validation request. See "When to invoke" in the agent body.
```

```markdown
## When to invoke

- **Pre-commit validation.** The user signals readiness to commit. Run validation first and surface any issues.
- **Explicit validation request.** The user asks for the code to be validated.
```

## Debugging triggering issues

### Agent not triggering

Check:
1. The `description:` prose names the right trigger scenarios.
2. The scenarios in the body cover the actual phrasings the user uses.
3. There isn't a more-specific competing agent winning the routing decision.

Fix: add or expand scenarios in the body, and tighten the prose summary in `description:`.

### Agent triggers too often

Check:
1. The trigger scenarios are too generic or overlap with other agents.
2. The `description:` doesn't say when NOT to use the agent.

Fix: narrow the scenarios; add a "Do not invoke when..." line to `description:` if needed.

### Agent triggers in the wrong scenarios

Check:
1. Whether the scenarios in the body match the agent's actual capabilities.

Fix: rewrite scenarios to match what the agent actually does.

## Best practices summary

- Keep `description:` as flat prose with a short summary of trigger scenarios
- Put detailed scenarios in a "When to invoke" body section, as prose bullets
- Cover both explicit and proactive triggering
- Describe situations the agent should respond to
- Mention phrasing variation in prose ("any phrasing — 'ready to ship', 'looks done'") rather than via multiple near-duplicate scenarios
- Keep trigger scenarios separate from output format

## Conclusion

Reliable triggering comes from prose descriptions of the situations an agent should respond to.
