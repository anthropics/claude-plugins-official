---
name: pact-prepare-research
description: |
  Research methodologies and documentation gathering workflows for PACT Prepare phase.
  Use when: conducting technology research, evaluating API documentation,
  comparing framework options, analyzing library choices, gathering requirements,
  or creating technology comparison matrices.
  Triggers on: research, requirements gathering, API exploration, documentation
  review, technology evaluation, library comparison, prepare phase.
---

# PACT Prepare Research Methodology

Structured approaches for the Prepare phase of PACT. This skill provides
frameworks for systematic research, documentation gathering, and technology
evaluation to build a solid foundation before architecture and implementation.

## Research Workflow

### Phase 1: Define Research Scope

Before starting research, clearly define:

```markdown
## Research Scope Definition

### Primary Question
What specific problem are we trying to solve?

### Success Criteria
What would make a solution acceptable?
- [ ] Performance requirements
- [ ] Integration requirements
- [ ] Security requirements
- [ ] Budget constraints

### Constraints
What limitations must we work within?
- Technology stack restrictions
- Team expertise
- Timeline
- Licensing requirements
```

### Phase 2: Source Prioritization

Prioritize sources by authority and reliability:

| Priority | Source Type | Examples | Trust Level |
|----------|-------------|----------|-------------|
| 1 | Official documentation | Docs, API references | Highest |
| 2 | Official repositories | GitHub READMEs, wikis | Very High |
| 3 | Maintainer content | Blog posts by core team | High |
| 4 | Community verified | Stack Overflow accepted answers | Medium |
| 5 | Third-party tutorials | Blog posts, videos | Low-Medium |
| 6 | AI-generated content | ChatGPT, Copilot | Verify Required |

**Source Verification Checklist:**
- [ ] Publication date within 12 months (for version-specific info)
- [ ] Author has verifiable credentials
- [ ] Information matches official docs
- [ ] Code examples actually work

### Phase 3: Documentation Types to Gather

Collect these documentation types for complete understanding:

**1. API References**
```markdown
## API Documentation Checklist
- [ ] Authentication methods
- [ ] Rate limits and quotas
- [ ] Available endpoints
- [ ] Request/response formats
- [ ] Error codes and handling
- [ ] SDK availability
- [ ] Webhook support
```

**2. Configuration Guides**
```markdown
## Configuration Documentation
- [ ] Environment variables
- [ ] Configuration file formats
- [ ] Default values
- [ ] Required vs optional settings
- [ ] Security-sensitive configs
```

**3. Migration Documentation**
```markdown
## Migration Considerations
- [ ] Breaking changes between versions
- [ ] Deprecation timelines
- [ ] Migration guides
- [ ] Data migration requirements
```

**4. Security Advisories**
```markdown
## Security Documentation
- [ ] Known vulnerabilities (CVEs)
- [ ] Security best practices
- [ ] Authentication requirements
- [ ] Data handling guidelines
```

### Phase 4: Evaluation Criteria

Use this framework to evaluate research findings:

| Criterion | Questions | Weight |
|-----------|-----------|--------|
| **Currency** | Updated within 12 months? Active development? | High |
| **Authority** | Official source? Maintainer authored? | High |
| **Completeness** | Covers required use cases? | Medium |
| **Practicality** | Actionable? Working examples? | Medium |
| **Compatibility** | Works with existing stack? | High |
| **Community** | Active community? Good support? | Medium |
| **Security** | Security track record? Quick patches? | High |

## Quick Reference Templates

### Technology Comparison

For structured side-by-side comparisons:
See [technology-comparison-matrix.md](references/technology-comparison-matrix.md)

**Quick Comparison Template:**
```markdown
| Criterion | Option A | Option B | Winner |
|-----------|----------|----------|--------|
| Learning curve | Steep | Gentle | B |
| Performance | Fast | Very Fast | B |
| Documentation | Good | Excellent | B |
| Community size | Large | Medium | A |
| **Total** | 1 | 3 | **B** |
```

### API Documentation Summary

For capturing API details systematically:
See [api-exploration-template.md](references/api-exploration-template.md)

**Quick API Summary:**
```markdown
## API: [Name]

**Base URL**: `https://api.example.com/v1`
**Auth**: Bearer token in header
**Rate Limit**: 100 req/min

### Key Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /users | GET | List users |
| /users/:id | GET | Get user |
| /users | POST | Create user |

### Authentication
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.example.com/v1/users
```
```

### Requirements Analysis

For comprehensive requirements documentation:
See [requirements-analysis.md](references/requirements-analysis.md)

**Quick Requirements Template:**
```markdown
## Feature: [Name]

### User Story
As a [user type], I want [action] so that [benefit].

### Acceptance Criteria
- [ ] Given [context], when [action], then [result]
- [ ] Given [context], when [action], then [result]

### Technical Requirements
- Performance: [target]
- Security: [requirements]
- Integration: [dependencies]

### Dependencies
- Depends on: [other features/services]
- Blocked by: [blockers]
```

## Research Output Format

### Standard Research Document Structure

```markdown
# Research: [Topic]

## Executive Summary
[2-3 sentence summary of findings and recommendation]

## Background
[Why this research was needed]

## Methodology
[How research was conducted]

## Findings

### Option 1: [Name]
**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Evidence:**
- [Link to source]
- [Link to source]

### Option 2: [Name]
[Same structure]

## Comparison Matrix
[Side-by-side comparison table]

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk] | High/Med/Low | High/Med/Low | [Strategy] |

## Recommendation
[Clear recommendation with rationale]

## Next Steps
1. [Action item]
2. [Action item]

## References
- [Source 1]
- [Source 2]
```

## Quality Checklist

Before completing Prepare phase research:

### Source Quality
- [ ] All critical information from official sources
- [ ] Version numbers explicitly stated
- [ ] Publication dates verified (within 12 months for technical details)
- [ ] No single point of information failure (multiple sources for key facts)

### Completeness
- [ ] All evaluation criteria addressed
- [ ] Alternatives presented with pros/cons
- [ ] Security implications documented
- [ ] Performance characteristics noted
- [ ] Integration requirements identified

### Actionability
- [ ] Recommendations backed by evidence
- [ ] Next steps clearly defined
- [ ] Risks identified with mitigations
- [ ] Dependencies mapped

### Documentation
- [ ] Research document follows standard structure
- [ ] All sources linked and accessible
- [ ] Key decisions documented with rationale
- [ ] Output saved to `docs/{feature}/preparation/`

## Common Research Patterns

### Library/Framework Selection
1. Define requirements and constraints
2. Identify 3-5 candidates
3. Evaluate against criteria matrix
4. Prototype with top 2 candidates
5. Document decision rationale

### API Integration Research
1. Gather official API documentation
2. Test authentication flow
3. Document all required endpoints
4. Identify rate limits and quotas
5. Plan error handling strategy

### Technology Migration
1. Document current state
2. Research target technology
3. Identify breaking changes
4. Plan migration path
5. Define rollback strategy

## Detailed References

For comprehensive templates and frameworks:

- **API Exploration Template**: [references/api-exploration-template.md](references/api-exploration-template.md)
  - Full API documentation template
  - Authentication testing guide
  - Error handling documentation

- **Requirements Analysis Framework**: [references/requirements-analysis.md](references/requirements-analysis.md)
  - User story templates
  - Acceptance criteria patterns
  - Non-functional requirements

- **Technology Comparison Matrix**: [references/technology-comparison-matrix.md](references/technology-comparison-matrix.md)
  - Weighted scoring templates
  - Multi-criteria decision analysis
  - Risk assessment frameworks
