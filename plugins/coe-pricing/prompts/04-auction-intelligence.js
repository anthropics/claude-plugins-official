/**
 * PROMPT 04 — Auction Intelligence Agent
 */
const AUCTION_PROMPT = (make, model, year, vin) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: AUCTION INTELLIGENCE

**Vehicle:** ${year} ${make} ${model}
**VIN:** ${vin}

Search Emirates Auction (emiratesauction.com) and Copart MEA (copart.com/mea).

### EMIRATES AUCTION
- Active listings for this make/model/year: [N]
- Price range of active lots: AED [LOW] – AED [HIGH]
- Recent sold results (last 90 days): AED [AMOUNT] avg
- Condition notes from listings: [summary]

### COPART MEA
- Active listings: [N]
- Damage types represented: [Clean / Minor Damage / Major Damage / Salvage]
- Price range: AED [LOW] – AED [HIGH]
- Salvage risk to market: [HIGH / MODERATE / LOW]

### AUCTION MARKET SIGNAL
- Distressed supply pressure on retail: [HIGH / MODERATE / LOW]
- Recommended floor adjustment from auction data: AED [ADJUSTMENT]

### COPILOT HANDOFF FLAG
[READY_FOR_COPILOT / NEEDS_CLARIFICATION / ESCALATE]
`;

async function run({ make, model, year, vin }) {
  return {
    prompt: AUCTION_PROMPT(make, model, year, vin),
    promptName: 'Auction Intelligence Agent',
    vin,
  };
}

module.exports = { run, AUCTION_PROMPT };
