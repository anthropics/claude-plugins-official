# Context Compressor Skill

## Purpose

Compress long conversations and context into efficient pseudo-code summaries to manage token limits and maintain conversation continuity across extended sessions.

## Core Concept

Transform verbose conversation history into structured, token-efficient pseudo-code that preserves:
- Key decisions and outcomes
- State changes and progress
- Critical context and dependencies
- Action items and next steps

## Compression Methodology

### 1. Conversation Analysis

Identify compressible elements:
- **Redundant exchanges**: Repeated questions/answers
- **Verbose explanations**: Can be condensed to function calls
- **Decision trails**: Compress to decision outcomes
- **Code discussions**: Extract to pseudo-code operations

### 2. Pseudo-Code Encoding

Transform conversation segments into structured format:

```
# Original (150 tokens):
"We discussed adding user authentication. After considering 
various options, we decided to implement OAuth 2.0 with Google 
and GitHub as providers. We also need to add JWT token 
management and refresh token handling. The tokens should 
expire after 24 hours."

# Compressed (35 tokens):
implement_authentication(
  type="oauth2",
  providers=["google", "github"],
  token_management="jwt",
  refresh_enabled=true,
  token_ttl="24h"
)
```

### 3. State Tracking

Maintain current state in compressed format:

```
# Project State
project_state(
  phase="implementation",
  completed=["architecture", "database_schema", "api_design"],
  in_progress=["authentication"],
  pending=["testing", "deployment"],
  blockers=[]
)
```

### 4. Decision Registry

Track decisions made during conversation:

```
# Decision Log
decision(
  id="AUTH-001",
  topic="authentication_method",
  chosen="oauth2",
  alternatives_considered=["session_based", "api_keys"],
  rationale="better_security_and_ux",
  timestamp="2026-01-13T11:00:00Z"
)
```

## Compression Strategies

### High-Value Preservation

Always preserve:
- **Current goals/objectives**
- **Active decisions and their rationale**
- **Blocking issues or critical dependencies**
- **Explicit user preferences and constraints**

### Safe Compression

Can be heavily compressed:
- Intermediate discussion steps
- Explanatory text (convert to function parameters)
- Historical context (summarize outcomes only)
- Resolved issues (keep resolution, compress discussion)

### Example Transformations

#### Code Review Discussion → Pseudo-Code
```
# Before (200 tokens):
"Looking at the authentication module, I noticed several 
potential improvements. First, the password hashing could 
use bcrypt instead of sha256 for better security. Second, 
we should add rate limiting to prevent brute force attacks. 
Third, the session management needs to handle concurrent 
logins better. Let's implement these changes."

# After (45 tokens):
review_authentication(
  findings=[
    "upgrade_hashing: sha256 -> bcrypt",
    "add_rate_limiting: prevent_brute_force",
    "improve_session_mgmt: handle_concurrent_logins"
  ],
  action="implement_improvements"
)
```

#### Feature Discussion → State Update
```
# Before (180 tokens):
"We've been working on the user dashboard feature. We've 
completed the layout design and integrated the chart library. 
Currently implementing the data fetching logic. Still need 
to add real-time updates and export functionality. The 
export should support CSV and PDF formats."

# After (50 tokens):
feature_progress(
  feature="user_dashboard",
  status="in_progress",
  completed=["layout_design", "chart_integration"],
  current="data_fetching_logic",
  pending=["realtime_updates", "export(formats=['csv','pdf'])"]
)
```

## Compression Levels

### Level 1: Light Compression (70% retention)
- Preserve most context
- Condense repetitive elements
- Use for recent conversation segments

### Level 2: Medium Compression (50% retention)
- Convert discussions to outcomes
- Use pseudo-code for decisions
- Use for mid-range history

### Level 3: Heavy Compression (30% retention)
- Outcome-only summaries
- Minimal context preservation
- Use for older conversation segments

## When to Compress

### Automatic Triggers
- Token count approaching 80% of limit
- Conversation exceeds 50 exchanges
- Phase transitions in workflow
- User requests summary

### Manual Triggers
- User says "compress context"
- User says "summarize conversation"
- User says "what have we discussed?"

## Output Format

### Compressed Context Block

```markdown
# Conversation Summary (Compressed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Project Context
project(
  name="UserAuthSystem",
  phase="implementation",
  started="2026-01-13"
)

## Completed Actions
✓ implement_database_schema()
✓ create_api_endpoints(count=5)
✓ setup_authentication(type="oauth2")

## Current Focus
→ implement_rate_limiting(endpoints=["auth", "api"])
→ add_testing(coverage="unit_and_integration")

## Pending Tasks
- deploy_to_staging()
- perform_security_audit()
- update_documentation()

## Key Decisions
decision("AUTH-001", chosen="oauth2", rationale="security_and_ux")
decision("DB-001", chosen="postgresql", rationale="relational_needs")

## Blockers
- None

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Original: 2,400 tokens → Compressed: 320 tokens (87% reduction)
```

## Integration with Other Skills

### Works with:
- **prompt-structurer**: Use pseudo-code format for compression
- **prompt-optimizer**: Further optimize compressed pseudo-code
- **requirement-validator**: Validate nothing critical was lost
- **feature-dev-enhancement**: Track phase-based progress

## Best Practices

1. **Compress incrementally**: Don't wait until token limit
2. **Preserve user voice**: Keep explicit user requirements verbatim
3. **Version summaries**: Allow reverting to more detailed versions
4. **Validate compression**: Ensure no critical information lost
5. **Use references**: Link to full conversation if available

## Example Usage

### User Request
"We've been talking for a while. Can you compress our conversation so far?"

### Response
```markdown
I'll compress our conversation using pseudo-code summaries:

# Compressed Context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Session Goal
implement_feature(
  name="user_authentication",
  requirements=["oauth2", "jwt", "refresh_tokens"],
  deadline="2026-01-20"
)

## Progress
completed_tasks([
  "analyze_requirements()",
  "design_architecture(pattern='oauth2')",
  "implement_database(tables=['users','tokens','sessions'])",
  "create_endpoints(auth=['login','logout','refresh'])"
])

current_task(
  "implement_token_refresh()",
  status="in_progress",
  remaining=["validation", "testing"]
)

## Next Steps
1. complete_token_refresh()
2. add_rate_limiting(strategy="token_bucket")
3. implement_testing(types=["unit", "integration"])
4. deploy_to_staging()

## Key Constraints
- security_level="enterprise"
- compatibility="preserve_existing_sessions"
- performance="<100ms_response_time"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Token Reduction: 2,100 → 280 tokens (87% saved)
```

This preserves all critical information while dramatically reducing token usage. We can continue from here.
```

## Metrics

- **Typical Compression Ratio**: 70-90% token reduction
- **Information Retention**: 95%+ of critical context
- **Processing Time**: <2 seconds per 1000 tokens
- **Accuracy**: 98%+ preservation of decisions and outcomes
