# MEOK Compliance Pack

EU AI Act, DORA, NIS2, EU CRA, GDPR compliance pack for Claude Code.

## What's included

8 MCP servers covering the major EU regulatory frameworks:

| MCP | Coverage |
|---|---|
| `meok-eu-ai-act-governance` | EU AI Act Articles 4 → 72 with crosswalk to ISO/IEC 42001 + NIST AI RMF |
| `meok-watermark-attest` | EU AI Act Article 50 watermarking (C2PA + invisible WM + fingerprint) |
| `meok-dpia-edpb` | EDPB harmonised DPIA template (14 April 2026) auto-fill, doubles as Article 26(9) FRIA |
| `meok-nis2-de-register` | Germany NIS2-UmsuCG BSI register (Section 30/32 entity classifier + payload) |
| `meok-cra-annex-iv` | EU CRA (Reg 2024/2847) Annex III + Annex IV technical documentation classifier |
| `meok-omnibus-tracker` | Authoritative dated tracker for every EU AI Act / DORA / NIS2 / CRA deadline |
| `meok-mcp-injection-scan` | Scans MCP servers for prompt-injection + tool-poisoning vectors |
| `meok-attestation-verify` | Verifier for HMAC-signed MEOK compliance certificates |

All packages are MIT-licensed and listed in the official MCP Registry under `io.github.CSOAI-ORG/*`.

## Why use this pack

- **Compliance buyers + procurement reviewers** ask whether your AI product covers EU AI Act + DORA + NIS2 + CRA. This pack lets you generate signed evidence on demand from inside Claude Code.
- **Article 50 watermarking deadline 2 August 2026** is the only EU AI Act cliff still in 2026 (high-risk Annex III delayed to 2 Dec 2027 by the Digital Omnibus). The watermark MCP covers the full Code-of-Practice 2-layer approach.
- **NIS2-DE BSI register** — ~17,500 German Mittelstand entities missed the 6 March 2026 deadline. The register MCP generates the late-filing rationale + payload.
- **EU CRA reporting (24h to ENISA)** starts 11 September 2026 — the CRA classifier MCP scopes your obligation.

## Install

```
/plugin install meok-compliance@claude-plugins-official
```

## Web

- Catalogue: https://meok-attestation-api.vercel.app/catalogue
- Verify any MEOK signed cert: https://meok-attestation-api.vercel.app/verify
- Source: https://github.com/CSOAI-ORG
- Docs: https://meok.ai/docs

## License

Plugin manifest: MIT (this directory).
Underlying MCP servers: MIT (per-package).

## Maintainer

MEOK AI Labs (a trading name of CSOAI LTD, UK Companies House 16939677). Founder: Nicholas Templeman. Contact: nicholas@csoai.org.
