/**
 * PROMPT 06 — Executive Appraisal Summary
 */

const EXEC_PROMPT = (vin, scanData) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: EXECUTIVE APPRAISAL SUMMARY

**VIN:** ${vin}
${scanData ? `**Pre-loaded scan data:** ${JSON.stringify(scanData, null, 2)}` : '**Note:** Compile from available research in this session.'}

Produce a concise, COE-standard executive summary:

---

## EXECUTIVE APPRAISAL SUMMARY
**Vehicle:** [Year Make Model Grade]
**VIN:** ${vin}
**Date:** [ISO DATE]
**Appraiser Agent:** Claude COE Pricing Intelligence

---

### KEY FINDINGS

| Factor              | Status              | AED Impact     |
|--------------------|---------------------|----------------|
| GCC Spec           | [Confirmed/Non-GCC] | [+/- AED]      |
| Accident History   | [Clean/N accidents] | [–AED or None] |
| Mileage Position   | [Above/Below avg]   | [–AED or None] |
| Recall Status      | [Clear/Active]      | [Flag/None]    |
| Market Supply      | [Over/Under/Bal]    | [–AED or None] |
| Colour Premium     | [Colour]            | [+/– AED]      |

---

### PRICE RECOMMENDATION

| Band          | AED Amount | Use Case                    |
|--------------|------------|-----------------------------|
| **Floor**    | AED [AMT]  | Aggressive trade-in / buy   |
| **Target**   | AED [AMT]  | Fair market acquisition      |
| **Ceiling**  | AED [AMT]  | Max retail / counter-offer   |

**Recommended Trade-In Offer:** → AED [AMOUNT] *(Decision: Copilot)*

---

### RISK FLAGS
- [Flag 1 or NONE]
- [Flag 2 or NONE]

### RESEARCH COMPLETENESS
- VIN Scan: [✓ / ✗]
- MOI History: [✓ / ✗]
- Platform Pricing: [✓ / ✗]
- Auction Data: [✓ / ✗]
- GCC Verification: [✓ / ✗]
- Reliability Score: [✓ / ✗]

---
**HANDOFF STATUS:** [READY_FOR_COPILOT / NEEDS_CLARIFICATION / ESCALATE]
`;

async function run({ vin, scanData }, afPricingService) {
  // Optionally call af-pricing-agent to enrich with calculated pricing
  let pricingCalc = null;
  if (afPricingService && scanData) {
    try {
      pricingCalc = await afPricingService.calculatePrice(scanData);
    } catch (e) {
      console.warn('[Exec Summary] af-pricing-agent unavailable:', e.message);
    }
  }

  return {
    prompt: EXEC_PROMPT(vin, scanData),
    promptName: 'Executive Appraisal Summary',
    vin,
    pricingCalc: pricingCalc || null,
  };
}

module.exports = { run, EXEC_PROMPT };
