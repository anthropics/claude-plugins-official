# Pseudo-Code Prompting Plugin Installation

## Quick Start

### Requirements

- Claude Code v2.1.0 or higher

### From Marketplace

```bash
# Step 1: Add the marketplace
/plugin marketplace add EladAriel/pseudo-code-prompting-plugin

# Step 2: Install the plugin
/plugin install pseudo-code-prompting
```

All features (6 skills, 5 agents, 4 commands, 3 hooks) are automatically available after installation.

### From GitHub (Manual)

```bash
git clone https://github.com/EladAriel/pseudo-code-prompting-plugin ~/.claude/plugins/pseudo-code-prompting
```

### Local Development

```bash
# Clone and symlink for development
git clone https://github.com/EladAriel/pseudo-code-prompting-plugin
cd ~/.claude/plugins
ln -s /path/to/pseudo-code-prompting-plugin pseudo-code-prompting
```

## Features

- **Progressive Loading**: Skills use `capabilities.json` for token-efficient discovery (4-tier architecture)
- **5 Specialized Agents**: Analyzer, transformer, validator, optimizer, compressor
- **4 Commands**: `/transform-query`, `/validate-requirements`, `/optimize-prompt`, `/compress-context`
- **3 Hooks**: Auto-transformation, validation, compression suggestions
- **60-95% Compression**: Reduce verbose requirements while preserving 100% semantics
- **Comprehensive Validation**: Security (95% OWASP), completeness (90%), edge cases (85%)

## Workflows

### Full Transformation (900 tokens)
```
Analyze → Transform → Validate
```
Complete workflow from natural language to validated pseudo-code

### Quick Transform (200 tokens)
```
Transform
```
Fast transformation without deep analysis

### Optimize and Validate (700 tokens)
```
Optimize → Validate
```
Enhance existing pseudo-code with missing parameters and validation

### Compress, Transform, Validate (1000 tokens)
```
Compress → Transform → Validate
```
Full workflow from verbose requirements to validated pseudo-code

## Use Cases

- ✅ Transform verbose requirements into concise pseudo-code (60-95% compression)
- ✅ Validate pseudo-code for completeness, security, and edge cases
- ✅ Optimize requirements for implementation readiness
- ✅ Eliminate ambiguity from natural language specifications
- ✅ Structure feature requests before development
- ✅ Ensure security requirements are not missed

## PROMPTCONVERTER Methodology

The plugin uses the PROMPTCONVERTER methodology with 5 transformation rules:

1. **Analyze Intent**: Identify core action (verb) and subject (noun)
2. **Create Function Name**: Combine into `snake_case` (e.g., `implement_authentication`)
3. **Extract Parameters**: Convert details to named parameters (e.g., `providers=["google"]`)
4. **Infer Constraints**: Detect implicit requirements (security, performance, validation)
5. **Output Format**: Single-line pseudo-code: `function_name(param="value", ...)`

## Example Transformation

**Input (158 words):**
```
We need to create a REST API endpoint that handles user registration. The endpoint should accept POST requests at the /api/register path. Users need to provide their email address, which must be validated to ensure it's a proper email format and not already in use. They also need to provide a password that meets our security requirements: at least 12 characters, including uppercase, lowercase, numbers, and special characters. The system should hash the password using bcrypt before storing it. If registration is successful, return a 201 status with the new user ID. If the email is already taken, return a 409 error. If validation fails, return a 400 error with details about what went wrong. We should also rate limit this endpoint to prevent abuse, allowing maximum 10 registration attempts per hour from the same IP address.
```

**Output (1 function call, 95% reduction):**
```javascript
create_endpoint(
  path="/api/register",
  method="POST",
  request_schema={
    "email": "email:required:unique",
    "password": "string:required:min(12):requires(upper,lower,number,special)"
  },
  password_hash="bcrypt",
  response_codes={
    "201": {"user_id": "string", "created_at": "timestamp"},
    "400": "validation_error",
    "409": "duplicate_email"
  },
  rate_limit={"max": 10, "window": "1h", "key": "ip"},
  audit_log=true
)
```

## Plugin Structure

This plugin follows Claude Code's official auto-discovery pattern:

- **Skills**: `skills/*/SKILL.md` with progressive loading (capabilities.json → SKILL.md → references → templates)
- **Agents**: `agents/*.md` with YAML frontmatter
- **Commands**: `commands/*.md` slash commands
- **Hooks**: `hooks/hooks.json` + bash scripts for event automation

No manual configuration needed - everything is auto-discovered!

## More Information

See the main [README.md](../README.md) for full documentation, examples, and advanced usage.

## Version

**Current Version:** 1.1.0
**Last Updated:** 2026-01-14
