---
name: terraform-patterns
description: >
  This skill should be used when the user asks to "analyze Terraform modules",
  "scan IaC for security issues", "review Terraform configurations",
  "check infrastructure code for misconfigurations", or "audit cloud resources".
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: engineering
  domain: infrastructure-as-code
  updated: 2026-04-02
  tags: [terraform, iac, security, cloud, infrastructure]
---
# Terraform Patterns

> **Category:** Engineering
> **Domain:** Infrastructure as Code

## Overview

The **Terraform Patterns** skill provides automated analysis of Terraform configurations for module complexity, security misconfigurations, and infrastructure best practices. It catches open ports, public buckets, missing encryption, and overly permissive IAM policies before they reach production.

## Quick Start

```bash
# Analyze Terraform module structure and complexity
python scripts/tf_module_analyzer.py --path ./modules/vpc

# Scan for security misconfigurations
python scripts/tf_security_scanner.py --path ./environments/production

# JSON output for CI pipelines
python scripts/tf_security_scanner.py --path . --format json

# Recursive analysis of all modules
python scripts/tf_module_analyzer.py --path . --recursive
```

## Tools Overview

### tf_module_analyzer.py

Analyzes Terraform modules for complexity, structure, dependencies, and documentation quality.

| Feature | Description |
|---------|-------------|
| Complexity scoring | Scores modules by resource count, variable count, nesting |
| Dependency mapping | Maps module dependencies and data source usage |
| Variable analysis | Checks for missing types, defaults, descriptions |
| Output completeness | Validates output documentation and coverage |
| Naming conventions | Checks resource and variable naming patterns |

### tf_security_scanner.py

Scans Terraform configurations for security misconfigurations and compliance violations.

| Feature | Description |
|---------|-------------|
| Open ports | Detects 0.0.0.0/0 CIDR in security groups |
| Public access | Flags public S3 buckets, databases, instances |
| Encryption gaps | Checks for missing encryption at rest and in transit |
| IAM overreach | Identifies wildcard actions and overly broad policies |
| Logging gaps | Verifies CloudTrail, flow logs, access logging |

## Workflows

### Security Review Workflow

1. **Scan** - Run tf_security_scanner.py across all environments
2. **Triage** - Prioritize critical findings (public data, open access)
3. **Remediate** - Apply recommended fixes per finding
4. **Verify** - Re-scan to confirm fixes resolved issues
5. **Gate** - Add scanner to PR checks for continuous enforcement

### Module Quality Workflow

1. **Analyze** - Run tf_module_analyzer.py on each module
2. **Score** - Review complexity scores, identify modules over threshold
3. **Refactor** - Break down modules scoring above 70/100 complexity
4. **Document** - Fill in missing variable and output descriptions
5. **Standardize** - Apply consistent naming and file organization

### CI Integration

```bash
# Security gate
python scripts/tf_security_scanner.py --path . --format json --min-severity high
if [ $? -ne 0 ]; then
  echo "Security scan failed - blocking merge"
  exit 1
fi

# Module quality check
python scripts/tf_module_analyzer.py --path . --recursive --format json
```

## Reference Documentation

- [Terraform Patterns](references/terraform-patterns.md) - Module design, state management, naming conventions

## Common Patterns Quick Reference

### Module Structure
```
modules/vpc/
  main.tf           # Primary resources
  variables.tf      # Input variables with descriptions
  outputs.tf        # Module outputs
  versions.tf       # Required providers and versions
  locals.tf         # Local values and computed expressions
```

### Security Checklist
| Resource | Check | Rule |
|----------|-------|------|
| Security Groups | No 0.0.0.0/0 ingress | Restrict to known CIDRs |
| S3 Buckets | No public ACLs | Use bucket policies instead |
| RDS | No public access | Set publicly_accessible = false |
| EBS/S3/RDS | Encryption enabled | Add encryption configuration |
| IAM | No wildcard actions | Use least-privilege policies |
| CloudTrail | Enabled in all regions | is_multi_region_trail = true |
| VPC | Flow logs enabled | Create flow log resources |

### Complexity Scoring
| Score | Rating | Action |
|-------|--------|--------|
| 0-30 | Low | No action needed |
| 31-60 | Medium | Consider splitting |
| 61-80 | High | Should refactor |
| 81-100 | Critical | Must refactor |
