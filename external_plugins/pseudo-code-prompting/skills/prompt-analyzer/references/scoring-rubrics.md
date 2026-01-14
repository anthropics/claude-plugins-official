# Scoring Rubrics

## Ambiguity Score Rubric

### Score: 0-1 (Exceptional Clarity)
- All terms precisely defined
- No vague language
- Explicit scope and boundaries
- Clear success criteria
- All assumptions stated

### Score: 2-3 (Clear)
- Most terms well-defined
- Minor ambiguities that don't affect understanding
- Scope mostly explicit
- Success criteria inferable
- Few unstated assumptions

### Score: 4-5 (Acceptable with Minor Issues)
- Some vague terms present
- Scope partially defined
- Some context missing
- Success criteria partially clear
- Some implicit assumptions

### Score: 6-7 (Moderate Ambiguity)
- Multiple vague terms
- Scope unclear in places
- Significant context gaps
- Success criteria vague
- Many implicit assumptions

### Score: 8-9 (High Ambiguity)
- Pervasive vague language
- Scope poorly defined
- Major context missing
- Success criteria unclear
- Extensive implicit assumptions

### Score: 10 (Extremely Ambiguous)
- Almost entirely vague
- No clear scope
- Minimal context
- No success criteria
- Everything implicit

## Complexity Score Rubric

### Score: 0-1 (Trivial)
- Single, atomic action
- No dependencies
- No integrations
- One system involved
- Straightforward implementation

### Score: 2-3 (Simple)
- Single feature or component
- Minimal dependencies
- Single system
- Clear implementation path
- Low coordination needs

### Score: 4-5 (Moderate)
- Multiple related actions
- Some dependencies
- Few integrations
- 2-3 systems involved
- Moderate coordination

### Score: 6-7 (Complex)
- Multiple features/components
- Many dependencies
- Multiple integrations
- 3-5 systems involved
- High coordination needs

### Score: 8-9 (Very Complex)
- Extensive feature set
- Complex dependencies
- Numerous integrations
- 5+ systems involved
- Critical coordination requirements

### Score: 10 (Extremely Complex)
- Large-scale system changes
- Intricate dependencies
- Enterprise-level integrations
- Many systems affected
- Organizational coordination needed

## Completeness Score Rubric

### Score: 0-2 (Severely Incomplete)
- No technical details
- No performance requirements
- No security considerations
- No constraints specified
- Missing critical information

### Score: 3-4 (Incomplete)
- Minimal technical details
- Vague performance needs
- Security not addressed
- Few constraints mentioned
- Major information gaps

### Score: 5-6 (Partially Complete)
- Some technical details
- Basic performance hints
- Some security mentions
- Some constraints present
- Moderate information gaps

### Score: 7-8 (Mostly Complete)
- Good technical details
- Performance requirements stated
- Security considered
- Most constraints present
- Minor information gaps

### Score: 9-10 (Complete)
- Comprehensive technical details
- Clear performance requirements
- Security well-addressed
- All constraints specified
- Minimal to no information gaps

## Composite Decision Matrix

| Ambiguity | Complexity | Completeness | Recommendation |
|-----------|------------|--------------|----------------|
| 0-3 | 0-3 | 7-10 | ✓ Proceed immediately |
| 0-3 | 4-6 | 7-10 | ✓ Proceed with care |
| 0-3 | 7-10 | 7-10 | ⚠ Proceed with planning |
| 4-6 | 0-6 | 5-10 | ⚠ Proceed with clarification |
| 7-10 | Any | Any | ✗ Clarification required |
| Any | Any | 0-4 | ✗ More details needed |

## Red Flags Checklist

Automatic high scores should be assigned when:
- [ ] Request uses only generic verbs ("improve", "enhance", "optimize")
- [ ] No specific technologies, frameworks, or systems mentioned
- [ ] Scale/scope completely undefined ("make it work", "add feature")
- [ ] Success criteria absent or circular ("make it better")
- [ ] Multiple critical details missing (>3 major gaps)
- [ ] Contradictory requirements detected
- [ ] Unrealistic expectations without context
