# Custom Security Scan Instructions

The Claude Code Security Reviewer Action supports custom security scan instructions, allowing you to add organization-specific vulnerability categories to the security audit.

## Overview

The default security scan covers common vulnerability categories like SQL injection, XSS, authentication issues, etc. However, organizations often have specific security concerns based on their:
- Technology stack (GraphQL, gRPC, specific cloud providers)
- Compliance requirements (GDPR, HIPAA, PCI DSS)
- Industry-specific vulnerabilities (financial services, healthcare)
- Custom frameworks and libraries

The `custom-security-scan-instructions` input allows you to extend the security categories that Claude checks for.

## Usage

1. Create a text file containing your custom security categories (e.g., `.github/custom-security-categories.txt`)
2. Reference it in your workflow:

```yaml
- uses: anthropics/claude-code-security-review@main
  with:
    custom-security-scan-instructions: .github/custom-security-categories.txt
```

## File Format

The file should contain additional security categories in the same format as the default categories. Each category should:
- Start with a descriptive header in bold (using `**Category Name:**`)
- List specific vulnerabilities or patterns to check for
- Use clear, actionable descriptions

### Example Structure:
```
**Category Name:**
- Specific vulnerability or pattern to check
- Another specific issue to look for
- Detailed description of what constitutes this vulnerability

**Another Category:**
- More specific checks
- Additional patterns to identify
```

## Examples

### Industry-Specific Example
See [examples/organization-specific-scan-instructions.txt](../examples/custom-security-scan-instructions.txt) for an example set of instructions that customize Claude Code to look for industry-specific security weaknesses including:
- Compliance checks (GDPR, HIPAA, PCI DSS)
- Financial services security
- E-commerce specific issues

## How It Works

Your custom instructions are appended to the security audit prompt after the default "Data Exposure" category. This means:
1. All default categories are still checked
2. Your custom categories extend (not replace) the default scan
3. The same HIGH/MEDIUM/LOW severity guidelines apply

## Best Practices

1. **Be Specific**: Provide clear descriptions of what constitutes each vulnerability
2. **Include Context**: Explain why something is a vulnerability in your environment
3. **Provide Examples**: Where possible, describe specific attack scenarios
4. **Avoid Duplicates**: Check the default categories to avoid redundancy
5. **Keep It Focused**: Only add categories relevant to your codebase

## Default Categories Reference

The default scan already includes:
- Input Validation (SQL injection, command injection, XXE, etc.)
- Authentication & Authorization
- Crypto & Secrets Management
- Injection & Code Execution
- Data Exposure

Your custom categories should complement these, not duplicate them.

## Tips for Writing Effective Categories

1. **Technology-Specific**: Add checks for your specific tech stack
   ```
   **GraphQL Security:**
   - Query depth attacks allowing unbounded recursion
   - Field-level authorization bypass
   - Introspection data leakage in production
   ```

2. **Compliance-Focused**: Add regulatory requirements
   ```
   **GDPR Compliance:**
   - Personal data processing without consent mechanisms
   - Missing data retention limits
   - Lack of data portability APIs
   ```

3. **Business Logic**: Add domain-specific vulnerabilities
   ```
   **Payment Processing:**
   - Transaction replay vulnerabilities
   - Currency conversion manipulation
   - Refund process bypass
   ```