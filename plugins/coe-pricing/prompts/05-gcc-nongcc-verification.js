/**
 * PROMPT 05 — GCC / Non-GCC Verification Agent
 */

const GCC_ADJUSTMENTS = {
  confirmed_gcc:        { pct: '+5% to +8%',  label: 'GCC Premium' },
  non_gcc_confirmed:    { pct: '-10% to -18%', label: 'Non-GCC Deduction' },
  non_gcc_unverified:   { pct: '-15% floor',   label: 'Non-GCC Conservative Floor' },
};

const GCC_PROMPT = (make, model, year, vin) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: GCC / NON-GCC VERIFICATION

**Vehicle:** ${year} ${make} ${model}
**VIN:** ${vin}

### VERIFICATION EVIDENCE

**1. VIN Decode Signal**
- Country of manufacture from WMI: [COUNTRY]
- Factory destination code (if decodable): [UAE / GCC / EXPORT / UNKNOWN]

**2. Platform Listing Evidence**
Search Dubizzle, YallaMotor, CarSwitch for this exact VIN or matching trim:
- Seller-declared spec: [GCC / Non-GCC / Not stated]
- Consistency across platforms: [CONSISTENT / CONFLICTING]

**3. Spec Indicators**
- Climate control tuning (GCC A/C package): [PRESENT / ABSENT / UNKNOWN]
- Arabic language cluster option: [PRESENT / ABSENT / UNKNOWN]
- Warranty type declared: [UAE dealer / International / Expired / None]

### VERDICT
**GCC Status:** [CONFIRMED GCC / CONFIRMED NON-GCC / UNVERIFIED]
**Confidence:** [HIGH / MEDIUM / LOW]
**Evidence strength:** [STRONG / MODERATE / WEAK]

### PRICING ADJUSTMENT
- GCC status: [status]
- Applicable adjustment: ${Object.entries(GCC_ADJUSTMENTS).map(([k,v]) => `${v.label}: ${v.pct}`).join(' | ')}
- **Recommended adjustment for this vehicle:** AED [AMOUNT] ([+/-]%)

### COPILOT HANDOFF FLAG
[READY_FOR_COPILOT / NEEDS_CLARIFICATION / ESCALATE]
`;

async function run({ make, model, year, vin }) {
  return {
    prompt: GCC_PROMPT(make, model, year, vin),
    promptName: 'GCC/Non-GCC Verification Agent',
    vin,
    adjustmentReference: GCC_ADJUSTMENTS,
  };
}

module.exports = { run, GCC_PROMPT, GCC_ADJUSTMENTS };
