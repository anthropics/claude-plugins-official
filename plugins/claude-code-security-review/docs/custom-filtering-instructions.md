# Custom False Positive Filtering Instructions

The Claude Code Security Reviewer Action supports custom false positive filtering instructions, allowing you to tailor the security analysis to your specific environment and requirements.

## Overview

By default, the SAST action includes a comprehensive set of exclusions and criteria for filtering out false positives. However, every organization has unique security requirements, technology stacks, and threat models. The `false-positive-filtering-instructions` input allows you to provide your own custom criteria.

## Usage

1. Create a text file containing your custom filtering instructions (e.g., `.github/false-positive-filtering.txt`)
2. Reference it in your workflow:

```yaml
- uses: anthropics/claude-code-security-review@main
  with:
    false-positive-filtering-instructions: .github/false-positive-filtering.txt
```

## File Format

The file should contain plain text with three main sections:

### 1. HARD EXCLUSIONS
List patterns that should be automatically excluded from findings.

### 2. SIGNAL QUALITY CRITERIA
Questions to assess whether a finding represents a real vulnerability.

### 3. PRECEDENTS
Specific guidance for common security patterns in your environment.

## Example

See [examples/custom-false-positive-filtering.txt](../examples/custom-false-positive-filtering.txt) for a complete example tailored to a modern cloud-native application.

## Default Instructions

If no custom file is provided, the action uses default instructions tuned to work well for most applications.

## Best Practices

1. **Start with defaults**: Begin with the default instructions and modify based on false positives you encounter
2. **Be specific**: Include details about your security architecture (e.g., "We use AWS Cognito for all authentication")
3. **Document assumptions**: Explain why certain patterns are excluded (e.g., "k8s resource limits prevent DOS")
4. **Version control**: Track changes to your filtering instructions alongside your code
5. **Team review**: Have your security team review and approve the filtering instructions

## Common Customizations

- **Technology-specific exclusions**: Exclude findings that don't apply to your tech stack
- **Infrastructure assumptions**: Document security controls at the infrastructure level
- **Compliance requirements**: Adjust criteria based on your compliance needs
- **Development practices**: Reflect your team's security practices and tooling