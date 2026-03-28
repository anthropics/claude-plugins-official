/**
 * PROMPT 07 — Master Full Scan
 * Runs all research prompts in sequence and packages for Copilot handoff.
 */

const vinIntelligence     = require('./01-vin-intelligence');
const moiAccident         = require('./02-moi-accident');
const priceNormalization  = require('./03-price-normalization');
const auctionIntelligence = require('./04-auction-intelligence');
const gccVerification     = require('./05-gcc-nongcc-verification');
const executiveSummary    = require('./06-executive-summary');
const reliabilityResidual = require('./08-reliability-residual');
const copilotHandoff      = require('./09-copilot-handoff');

const MASTER_SYSTEM_PROMPT = (params) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: MASTER FULL SCAN — COMPLETE PIPELINE

**Vehicle:** ${params.year} ${params.make} ${params.model}
**VIN:** ${params.vin}
**Mileage:** ${params.mileage ? params.mileage.toLocaleString() + ' km' : 'Not specified'}
**Colour:** ${params.colour || 'Not specified'}
**Plate:** ${params.plateNumber || 'Not provided'}

Execute ALL 7 research modules in sequence. Do not skip any module.
Label each section clearly. Conclude with a Copilot Handoff Block.

---
## MODULE 1: VIN INTELLIGENCE SCAN
[Run full VIN decode per prompt 01 specification]

---
## MODULE 2: MOI ACCIDENT HISTORY
[Run full MOI query per prompt 02 specification]

---
## MODULE 3: PRICE NORMALIZATION ENGINE
[Run 7-platform price scan per prompt 03 specification]

---
## MODULE 4: AUCTION INTELLIGENCE
[Run Emirates Auction + Copart MEA scan per prompt 04 specification]

---
## MODULE 5: GCC / NON-GCC VERIFICATION
[Run full GCC verification per prompt 05 specification]

---
## MODULE 6: RELIABILITY & RESIDUAL VALUE
[Run reliability scoring per prompt 08 specification]

---
## MODULE 7: EXECUTIVE SUMMARY
[Compile all modules into executive summary per prompt 06 specification]

---
## COPILOT HANDOFF BLOCK
[Generate complete handoff block per prompt 09 specification]

---
**BOUNDARY REMINDER:** All findings above are external research only.
Trade-in decisions, SAP data, and Autorola comments are Copilot's boundary.
`;

async function run(params, { afPricingAgent, dubizzleScraper, copilotHandoffSvc }) {
  const { vin, make, model, year, mileage, colour, plateNumber } = params;

  // Build all sub-prompts
  const [
    p01, p02, p03, p04, p05, p06, p08
  ] = await Promise.all([
    vinIntelligence.run({ vin }),
    moiAccident.run({ vin, plateNumber }),
    priceNormalization.run({ make, model, year, mileage }, dubizzleScraper),
    auctionIntelligence.run({ make, model, year, vin }),
    gccVerification.run({ make, model, year, vin }),
    executiveSummary.run({ vin, scanData: null }, afPricingAgent),
    reliabilityResidual.run({ make, model, year, mileage }),
  ]);

  return {
    promptName: 'Master Full Scan',
    masterPrompt: MASTER_SYSTEM_PROMPT(params),
    subPrompts: { p01, p02, p03, p04, p05, p06, p08 },
    vin,
    vehicle: `${year} ${make} ${model}`,
    instructions: [
      '1. Submit masterPrompt to Claude for full pipeline execution.',
      '2. Claude will return 7 modules + Copilot Handoff Block.',
      '3. Copy the Copilot Handoff Block into Microsoft Copilot for internal appraisal.',
      '4. Copilot handles: trade-in decision, SAP data, Autorola comments, final pricing.',
    ],
  };
}

module.exports = { run, MASTER_SYSTEM_PROMPT };
