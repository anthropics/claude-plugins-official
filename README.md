# COE Pricing Intelligence — claude-plugins-official
**Al-Futtaim Automotive | Used Cars Expansion | UC Pricing COE**

> Full end-to-end integration of 9 COE pricing prompts, af-pricing-agent,
> vehicle-pricing-widget, and the Claude ↔ Copilot dual-agent pipeline —
> all wired into a single VS Code Claude plugin.

---

## Architecture

```
claude-plugins-official/
├── .claude-plugin/
│   └── manifest.json              ← All 9 commands registered
├── plugins/
│   └── coe-pricing/
│       ├── index.js               ← Dispatcher + orchestrator
│       ├── prompts/
│       │   ├── 01-vin-intelligence.js
│       │   ├── 02-moi-accident.js
│       │   ├── 03-price-normalization.js
│       │   ├── 04-auction-intelligence.js
│       │   ├── 05-gcc-nongcc-verification.js
│       │   ├── 06-executive-summary.js
│       │   ├── 07-master-full-scan.js       ← Runs all 7 in sequence
│       │   ├── 08-reliability-residual.js
│       │   └── 09-copilot-handoff.js        ← Packages for Copilot
│       ├── services/
│       │   ├── af-pricing-agent.js          ← Express backend client
│       │   ├── dubizzle-scraper.js          ← Puppeteer scraper bridge
│       │   └── copilot-handoff.js           ← Handoff formatter
│       └── config/
│           └── workflow.config.js           ← All pricing rules + boundaries
└── CLAUDE.md                                ← Claude Code CLI instructions
```

---

## Dual-Agent Boundary

| Agent       | Role                    | Handles                                         |
|------------|-------------------------|-------------------------------------------------|
| **Claude** | External Research       | VIN decode, 7-platform pricing, MOI, GCC verify |
| **Copilot**| Internal Appraisal      | SAP P01, Autorola, trade-in decision, AFM GM    |

---

## Slash Commands

| Command              | Description                                      |
|---------------------|--------------------------------------------------|
| `/vin-scan`          | VIN decode + GCC flag + recall check             |
| `/moi-accident`      | MOI accident history + deduction calc            |
| `/price-engine`      | 7-platform normalization + pricing bands         |
| `/auction-intel`     | Emirates Auction + Copart MEA scan               |
| `/gcc-verify`        | GCC/Non-GCC status + adjustment                  |
| `/exec-summary`      | Executive appraisal summary                      |
| `/master-scan`       | **Full pipeline — all 7 prompts in sequence**    |
| `/reliability-score` | Reliability + residual value scoring             |
| `/copilot-handoff`   | Generate Copilot handoff block                   |

---

## Linked Services

| Service                   | Port  | Purpose                                  |
|--------------------------|-------|------------------------------------------|
| `af-pricing-agent`        | 3001  | GCC/mileage/colour pricing calculations  |
| `vehicle-pricing-widget`  | 5173  | Vite frontend + Trade-In tab             |
| Dubizzle scraper backend  | 3002  | Puppeteer scraper (Express)              |

---

## Quick Start

```bash
# 1. Clone into your existing repo
git clone https://github.com/qasimsethi-code/claude-plugins-official

# 2. Install dependencies
cd claude-plugins-official
npm install

# 3. Start linked services (personal laptop)
cd ../af-pricing-agent && npm start          # port 3001
cd ../vehicle-pricing-widget && npm run dev  # port 5173

# 4. Run master scan (Claude Code CLI)
claude /master-scan --vin JTMAU7BJ5R4049000 --make Toyota --model "Land Cruiser" --year 2024
```

---

## Standard Workflow

```
1. Customer enquiry received
2. Claude Code: /master-scan VIN + vehicle details
3. Claude researches all 7 modules externally
4. Claude generates Copilot Handoff Block
5. Paste handoff block into Microsoft Copilot
6. Copilot: SAP P01 lookup + Autorola + trade-in decision
7. Final appraisal output → DSR consolidation
```

---

## Pricing Rules (Quick Reference)

- **GCC confirmed:** +5% to +8%
- **Non-GCC confirmed:** –10% to –18%
- **Non-GCC unverified:** –15% floor
- **Accident deductions:** Minor –AED 1,500–3,000 | Moderate –AED 4,000–8,000 | Major –AED 10,000+
- **Mileage penalties:** Economy –800/10k km | Mid –1,200 | Premium –1,800 | Luxury –2,500

---

*Maintained by: Qasim Sethi — UC Pricing COE, Al-Futtaim Automotive*
*Last updated: 2026-03-28*
