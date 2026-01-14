# Transformation Template

## Input Analysis Template
```
Original Request: [USER_REQUEST]

Step 1: Intent Analysis
- Action (verb): [VERB]
- Subject (noun): [NOUN]
- Core intent: [INTENT_SUMMARY]

Step 2: Extract Details
- Technologies mentioned: [TECH_LIST]
- Scope indicators: [SCOPE]
- Modifiers/constraints: [MODIFIERS]

Step 3: Infer Constraints
- Performance needs: [PERF_CONSTRAINTS]
- Security implications: [SECURITY]
- Compatibility: [COMPAT]

Step 4: Generate Function
function_name: [ACTION]_[SUBJECT]
parameters:
  - param1: "[VALUE1]"
  - param2: "[VALUE2]"
  ...

Step 5: Output
Transformed: function_name(param1="value1", param2="value2", ...)
