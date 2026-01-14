---
description: Transform natural language query to code-style pseudo-code format
argument-hint: [query]
---

# Transform Query to Pseudo-Code

Transform the provided natural language query into concise, function-like pseudo-code format following PROMPTCONVERTER methodology.

## Task

User query: `$ARGUMENTS`

Apply the PROMPTCONVERTER transformation rules:

1. **Analyze Intent** - Identify the core action (verb) and main subject (noun) of the query
2. **Create Function Name** - Combine into descriptive snake_case function name
3. **Extract Parameters** - Convert specific details and constraints into function arguments
4. **Infer Constraints** - Detect implicit requirements (brevity, style, performance, etc.)
5. **Output Format** - Return ONLY single-line pseudo-code, no markdown or explanations

## Output Format

Return the transformed pseudo-code in this format:

```
Transformed: function_name(param1="value1", param2="value2", ...)
```

## Examples to Reference

**Example 1: Feature Request**
- Input: "Add user authentication with OAuth"
- Output: `implement_authentication(type="oauth", providers=["google", "github"])`

**Example 2: Debugging Task**
- Input: "Debug the async function that's not waiting properly"
- Output: `debug_async_function(framework="javascript", issue="premature_return")`

**Example 3: Optimization**
- Input: "Optimize SQL query for large datasets"
- Output: `optimize_sql_query(scale="large_datasets", metrics=["latency", "throughput"])`

## Key Rules

- Preserve all semantic information from the original query
- Use meaningful parameter names aligned with the task
- Include all constraints as explicit parameters
- Function name should clearly indicate the action being requested
- Output exactly one line (no markdown formatting, no extra text)
