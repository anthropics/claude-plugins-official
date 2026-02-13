---
name: poc-trigger
description: "Harmless file to trigger the validate-frontmatter workflow. This file exists solely to satisfy the paths filter."
---

# PoC Trigger

This file triggers the `validate-frontmatter` workflow via the `paths` filter:

```yaml
paths:
  - '**/agents/*.md'
```

It demonstrates that a PR can include changes to BOTH trigger files
AND `.github/scripts/`, and the workflow will execute the attacker's
modified scripts.
