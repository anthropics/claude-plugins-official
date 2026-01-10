# Requirements Analysis Framework

A comprehensive framework for gathering, documenting, and validating requirements
during the PACT Prepare phase. Proper requirements analysis prevents costly
rework during implementation.

---

## Requirements Hierarchy

```
Business Requirements (Why)
    |
    +-- User Requirements (Who + What)
            |
            +-- Functional Requirements (How it works)
            |
            +-- Non-Functional Requirements (How well it works)
                    |
                    +-- Technical Requirements (Implementation details)
```

---

## User Story Template

### Standard Format

```markdown
## User Story: [ID] - [Title]

**As a** [type of user]
**I want** [to perform some action]
**So that** [I can achieve some goal/benefit]

### Acceptance Criteria
```gherkin
Given [some initial context]
When [an action is performed]
Then [a set of observable outcomes should occur]
```

### Definition of Done
- [ ] Code complete and reviewed
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Deployed to staging
- [ ] Product owner approved

### Priority
- Business Value: [High/Medium/Low]
- Effort Estimate: [Story Points or T-Shirt Size]
- Risk: [High/Medium/Low]

### Dependencies
- Depends on: [Other stories/features]
- Blocks: [Stories waiting on this]

### Notes
[Additional context, constraints, or decisions]
```

### Example User Story

```markdown
## User Story: AUTH-001 - User Password Reset

**As a** registered user who forgot my password
**I want** to reset my password via email
**So that** I can regain access to my account

### Acceptance Criteria
```gherkin
Scenario: Request password reset
  Given I am on the login page
  When I click "Forgot Password"
  And I enter my registered email address
  Then I should see "Check your email for reset instructions"
  And I should receive an email within 2 minutes

Scenario: Reset password with valid token
  Given I have received a password reset email
  When I click the reset link within 24 hours
  And I enter a new password meeting requirements
  Then my password should be updated
  And I should be redirected to login

Scenario: Reset link expiration
  Given I have received a password reset email
  When I click the reset link after 24 hours
  Then I should see "This link has expired"
  And I should be prompted to request a new reset
```

### Definition of Done
- [ ] Reset flow works end-to-end
- [ ] Email template approved by design
- [ ] Rate limiting on reset requests (5/hour)
- [ ] Old password invalidated immediately
- [ ] Audit log entry created
- [ ] Security review completed

### Priority
- Business Value: High (blocking issue for locked-out users)
- Effort Estimate: 5 points
- Risk: Medium (security-sensitive feature)

### Dependencies
- Depends on: Email service integration (INFRA-003)
- Blocks: None

### Notes
- Token should be single-use
- Consider implementing "password recently used" check
- Mobile deep linking required for app users
```

---

## Functional Requirements Template

```markdown
# Functional Requirements: [Feature Name]

## Overview
[Brief description of the feature and its purpose]

## Actors
| Actor | Description |
|-------|-------------|
| [Actor 1] | [Role description] |
| [Actor 2] | [Role description] |

## Use Cases

### UC-001: [Use Case Name]
**Actor**: [Primary actor]
**Preconditions**: [What must be true before]
**Postconditions**: [What must be true after]

**Main Flow**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Alternative Flows**:
- 2a. [Alternative at step 2]
  1. [Alternative step]
  2. [Resume at step 3]

**Exception Flows**:
- E1. [Exception condition]
  1. [System displays error]
  2. [User returns to step 1]

## Business Rules
| ID | Rule | Enforcement |
|----|------|-------------|
| BR-001 | [Rule description] | [Where/how enforced] |
| BR-002 | [Rule description] | [Where/how enforced] |

## Data Requirements
| Data Element | Type | Constraints | Source |
|--------------|------|-------------|--------|
| [Element] | [Type] | [Validation rules] | [Where from] |

## Interface Requirements
| Interface | Type | Description |
|-----------|------|-------------|
| [Interface] | API/UI/File | [Description] |
```

---

## Non-Functional Requirements (NFRs)

### NFR Categories

```markdown
# Non-Functional Requirements

## Performance
| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Page load time | < 2 seconds | 95th percentile |
| API response time | < 200ms | Average |
| Throughput | 1000 req/sec | Peak load |
| Database query time | < 50ms | 95th percentile |

## Scalability
| Requirement | Target | Notes |
|-------------|--------|-------|
| Concurrent users | 10,000 | Without degradation |
| Data volume | 10TB | 5-year projection |
| Geographic distribution | 3 regions | US, EU, APAC |

## Availability
| Requirement | Target | Notes |
|-------------|--------|-------|
| Uptime | 99.9% | Excluding planned maintenance |
| RTO | 4 hours | Recovery Time Objective |
| RPO | 1 hour | Recovery Point Objective |
| MTTR | 30 minutes | Mean Time To Repair |

## Security
| Requirement | Target | Standard |
|-------------|--------|----------|
| Data encryption | AES-256 | At rest and in transit |
| Authentication | MFA | For admin users |
| Session timeout | 30 minutes | Idle timeout |
| Password policy | NIST 800-63B | Minimum standards |
| Audit logging | All mutations | 7-year retention |

## Compatibility
| Requirement | Target | Notes |
|-------------|--------|-------|
| Browsers | Chrome, Firefox, Safari, Edge | Last 2 versions |
| Mobile | iOS 14+, Android 10+ | Native app |
| API versions | 2 versions | Backward compatibility |
| Accessibility | WCAG 2.1 AA | Minimum compliance |

## Maintainability
| Requirement | Target | Notes |
|-------------|--------|-------|
| Code coverage | 80% | Unit tests |
| Documentation | All public APIs | OpenAPI spec |
| Deployment frequency | Daily | Zero-downtime |
| Technical debt | < 5% | Per sprint |

## Compliance
| Requirement | Standard | Notes |
|-------------|----------|-------|
| Data privacy | GDPR, CCPA | User data handling |
| Payment | PCI DSS Level 1 | If handling cards |
| Healthcare | HIPAA | If handling PHI |
| Accessibility | Section 508 | Government contracts |
```

---

## Requirements Elicitation Techniques

### Stakeholder Interview Template

```markdown
## Stakeholder Interview: [Name/Role]

**Date**: [Date]
**Interviewer**: [Name]
**Duration**: [Time]

### Background
- Current role and responsibilities
- Interaction with the system
- Pain points with current solution

### Questions

**Understanding Current State**
1. Walk me through how you currently [process/workflow]?
2. What are the biggest challenges you face?
3. What workarounds have you developed?

**Desired Future State**
4. If you could change one thing, what would it be?
5. What would make your job easier?
6. How do you measure success?

**Priorities**
7. What features are must-haves vs nice-to-haves?
8. What would you be willing to give up for faster delivery?

**Constraints**
9. What constraints should we be aware of?
10. Are there any compliance or regulatory requirements?

### Key Takeaways
- [Insight 1]
- [Insight 2]
- [Insight 3]

### Action Items
- [ ] [Follow-up action]
- [ ] [Follow-up action]
```

### Requirements Workshop Agenda

```markdown
## Requirements Workshop

**Date**: [Date]
**Attendees**: [List]
**Facilitator**: [Name]
**Duration**: [2-4 hours]

### Agenda

**1. Introduction (15 min)**
- Workshop objectives
- Ground rules
- Participant introductions

**2. Problem Definition (30 min)**
- Current state review
- Pain points brainstorm
- Impact assessment

**3. Solution Brainstorming (45 min)**
- Feature ideation
- Grouping and themes
- Dot voting on priorities

**4. Deep Dive (60 min)**
- Top 3 features detailed discussion
- User story creation
- Acceptance criteria definition

**5. Prioritization (30 min)**
- MoSCoW categorization
- Dependency mapping
- Risk identification

**6. Wrap-up (15 min)**
- Summary of decisions
- Action items
- Next steps

### Outputs
- [ ] Prioritized feature list
- [ ] Initial user stories
- [ ] Risk register
- [ ] Dependency map
```

---

## Requirements Validation Checklist

```markdown
## Requirements Validation

### Completeness
- [ ] All user types/personas covered
- [ ] All workflows documented
- [ ] Edge cases identified
- [ ] Error scenarios defined
- [ ] Integration points specified

### Clarity
- [ ] No ambiguous language ("fast", "user-friendly", "easy")
- [ ] Specific, measurable criteria
- [ ] Clear acceptance conditions
- [ ] Examples provided where helpful

### Consistency
- [ ] No contradicting requirements
- [ ] Terminology used consistently
- [ ] Aligned with business goals
- [ ] Compatible with existing systems

### Feasibility
- [ ] Technically achievable
- [ ] Within budget constraints
- [ ] Achievable within timeline
- [ ] Team has required skills

### Testability
- [ ] Can be objectively verified
- [ ] Has clear pass/fail criteria
- [ ] Automation potential identified
- [ ] Test data requirements known

### Traceability
- [ ] Each requirement has unique ID
- [ ] Linked to business objective
- [ ] Dependencies documented
- [ ] Change history maintained
```

---

## Requirements Documentation Template

```markdown
# Requirements Document: [Project Name]

## Document Control
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Author] | Initial draft |

## 1. Introduction

### 1.1 Purpose
[Why this document exists]

### 1.2 Scope
[What's included and excluded]

### 1.3 Definitions
| Term | Definition |
|------|------------|
| [Term] | [Definition] |

## 2. Overall Description

### 2.1 Product Perspective
[How this fits in the larger system]

### 2.2 User Classes
| User Class | Description | Frequency |
|------------|-------------|-----------|
| [Class] | [Description] | [Usage frequency] |

### 2.3 Operating Environment
[Technical environment requirements]

### 2.4 Constraints
[Business, technical, regulatory constraints]

## 3. Functional Requirements

### 3.1 [Feature Area 1]
[User stories and acceptance criteria]

### 3.2 [Feature Area 2]
[User stories and acceptance criteria]

## 4. Non-Functional Requirements
[Performance, security, scalability, etc.]

## 5. Interface Requirements

### 5.1 User Interfaces
[UI/UX requirements]

### 5.2 API Interfaces
[API specifications]

### 5.3 External Interfaces
[Third-party integrations]

## 6. Assumptions and Dependencies
[What we're assuming to be true]

## 7. Appendices

### A. Glossary
### B. Wireframes/Mockups
### C. Data Dictionary
```

---

## INVEST Criteria for User Stories

Use INVEST to validate user story quality:

| Criterion | Description | Validation Question |
|-----------|-------------|---------------------|
| **I**ndependent | Story can be developed in any order | Can this be done without other stories? |
| **N**egotiable | Details can be discussed | Is there room for implementation flexibility? |
| **V**aluable | Delivers value to users | What benefit does this provide? |
| **E**stimable | Can be estimated | Do we understand it enough to estimate? |
| **S**mall | Fits in a sprint | Can this be completed in 1-2 weeks? |
| **T**estable | Has clear acceptance criteria | How will we know it's done? |
