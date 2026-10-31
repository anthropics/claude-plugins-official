---
description: Check one or more npm packages against PkgDiet supply-chain security and dependency health policies
argument: <package-name>
---

Check the specified npm package(s) using the PkgDiet MCP tool `check_dependency` or the CLI `pkgdiet check --json $ARGUMENT`.
Evaluate the verdict (ALLOW, WARN, or BLOCK) and report:
- Verdict & risk score
- Supply chain health (maintenance, popularity, license, security)
- If WARN or BLOCK, provide recommended alternatives.
