/**
 * PROMPT 02 — MOI Accident Intelligence Agent
 */
const MOI_PROMPT = (vin, plateNumber) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: MOI ACCIDENT INTELLIGENCE

**VIN:** ${vin}
**Plate Number:** ${plateNumber || 'Not provided'}

Query UAE Ministry of Interior accident records.

### 1. ACCIDENT HISTORY
- Total accidents on record: [N or NONE]
- Most recent accident date: [DATE or N/A]
- Severity breakdown: [Minor / Moderate / Major / Total Loss]
- Airbag deployment recorded? [YES / NO / UNKNOWN]

### 2. REPAIR HISTORY INDICATORS
- Structural repair flags: [YES / NO / UNKNOWN]
- Estimated repair cost impact on valuation: AED [AMOUNT] or N/A
- Recommended: Pre-purchase inspection? [YES / NO]

### 3. PRICING IMPACT
Apply standard COE deduction stack:
- 0 accidents: No deduction
- 1 minor: –AED 1,500 to –AED 3,000
- 1 moderate: –AED 4,000 to –AED 8,000
- 1+ major / structural: –AED 10,000 to –AED 20,000+ (flag for review)

**Recommended accident deduction:** AED [AMOUNT]

### COPILOT HANDOFF FLAG
[READY_FOR_COPILOT / NEEDS_CLARIFICATION / ESCALATE]
`;

async function run({ vin, plateNumber }) {
  return {
    prompt: MOI_PROMPT(vin, plateNumber),
    promptName: 'MOI Accident Intelligence Agent',
    vin,
  };
}

module.exports = { run, MOI_PROMPT };
