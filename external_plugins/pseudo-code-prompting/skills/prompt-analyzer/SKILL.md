# Prompt Analyzer Skill

## Overview
Analyze prompts for quality, clarity, and completeness before transformation. This skill provides quantitative metrics to assess whether a prompt is ready for transformation or requires clarification.

## Core Capabilities

### 1. Ambiguity Detection
Identify vague, unclear, or ambiguous terms in user requests:
- Vague verbs: "improve", "enhance", "fix" (without specifics)
- Undefined scope: "add feature" (which feature? where?)
- Missing context: "optimize" (what metric? what constraint?)
- Implicit assumptions: unstated requirements or expectations

### 2. Complexity Scoring
Measure the complexity of a request to determine effort:
- **Simple (0-3)**: Single, well-defined action
- **Medium (4-6)**: Multiple related actions or components
- **Complex (7-10)**: Multiple systems, phases, or integrations

### 3. Completeness Assessment
Identify missing requirements or information gaps:
- Technical details not specified
- Performance requirements unstated
- Security considerations not addressed
- Integration points undefined

### 4. Optimization Suggestions
Recommend improvements to make prompts clearer and more actionable.

## Analysis Metrics

### Ambiguity Score (0-10)
- **0-3**: Clear and specific, ready for transformation
- **4-6**: Some ambiguity, clarification recommended
- **7-10**: High ambiguity, clarification required

### Complexity Score (0-10)
- **0-3**: Simple, single action
- **4-6**: Medium, multiple related actions
- **7-10**: Complex, multiple systems/phases

### Completeness Score (0-10)
- **0-3**: Many requirements missing
- **4-6**: Some requirements missing
- **7-10**: Most requirements present

## Analysis Process

### Step 1: Scan for Ambiguity
```
analyze_ambiguity(
  request="[USER_REQUEST]",
  check_for=[
    "vague_terms",
    "undefined_scope",
    "missing_context",
    "implicit_assumptions"
  ]
)
```

### Step 2: Measure Complexity
```
measure_complexity(
  actions_count="[NUMBER]",
  systems_involved=[...],
  integration_points=[...],
  phases_required=[...]
)
```

### Step 3: Assess Completeness
```
assess_completeness(
  technical_details="present|missing",
  performance_requirements="present|missing",
  security_considerations="present|missing",
  constraints="present|missing"
)
```

### Step 4: Generate Report
```
generate_analysis_report(
  ambiguity_score="[X/10]",
  complexity_score="[Y/10]",
  completeness_score="[Z/10]",
  issues=[...],
  recommendations=[...]
)
```

## Output Format

```
Prompt Analysis Report
━━━━━━━━━━━━━━━━━━━━━━
Ambiguity Score: [X/10]
Complexity Score: [Y/10]
Completeness Score: [Z/10]

Issues Detected:
- [Issue 1: Description]
- [Issue 2: Description]
- [Issue 3: Description]

Recommendations:
- [Recommendation 1]
- [Recommendation 2]
- [Recommendation 3]

Proceed to transformation: [YES/NO/WITH_CLARIFICATION]
```

## When to Use

### Use this skill when:
- Starting a new transformation request
- User request seems unclear or vague
- Complex multi-system request detected
- Quality check requested explicitly
- Before committing to implementation approach

### Integration with other skills:
- **Before prompt-structurer**: Validate request quality first
- **With prompt-optimizer**: Analyze then optimize
- **Before feature-dev-enhancement**: Ensure requirements are complete

## Examples

### Example 1: Clear Request (Low Ambiguity)
**Input**: "Add OAuth authentication using Google provider with JWT session management"

**Analysis**:
- Ambiguity: 2/10 (Clear and specific)
- Complexity: 4/10 (Single feature, well-defined)
- Completeness: 8/10 (Most details present)
- **Result**: Proceed to transformation ✓

### Example 2: Ambiguous Request (High Ambiguity)
**Input**: "Make the app faster"

**Analysis**:
- Ambiguity: 9/10 (Extremely vague)
- Complexity: 5/10 (Unclear scope)
- Completeness: 2/10 (Missing critical details)
- **Issues**: What aspect? What metric? What constraint?
- **Result**: Clarification required ✗

### Example 3: Complex Request (Medium Ambiguity)
**Input**: "Build a dashboard with real-time updates, user authentication, and data visualization"

**Analysis**:
- Ambiguity: 5/10 (Some details missing)
- Complexity: 8/10 (Multiple systems)
- Completeness: 6/10 (Partial details)
- **Recommendations**: Specify auth method, real-time protocol, chart types
- **Result**: Proceed with clarification questions ⚠

## Best Practices

1. **Always analyze before transforming** complex requests
2. **Use scoring consistently** to maintain objectivity
3. **Provide actionable recommendations** not just scores
4. **Consider context** - some ambiguity is acceptable for exploration
5. **Don't over-analyze** simple, clear requests
