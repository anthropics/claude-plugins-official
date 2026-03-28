/**
 * PROMPT 01 — VIN Intelligence Scan
 * Decodes VIN, verifies GCC spec, flags recalls, identifies country of manufacture.
 */

const PROMPT_TEMPLATE = (vin) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: VIN INTELLIGENCE SCAN

**VIN:** ${vin}

Perform a full VIN decode and intelligence scan. Return ONLY structured data:

### 1. VIN DECODE
- Make / Model / Year / Trim / Grade
- Country of Manufacture (from WMI prefix)
- Engine / Transmission / Fuel Type
- GCC Spec Confirmed? [YES / NO / UNCERTAIN] + evidence

### 2. RECALL CHECK
Search NHTSA (nhtsa.gov/api/complaints/complaintsByVehicle), ADAC, and UAE RTA databases.
- Active recalls: [list or NONE]
- Severity: [CRITICAL / MODERATE / INFORMATIONAL]
- Pricing impact note

### 3. MARKET POSITION
- Segment: [Economy / Mid / Premium / Luxury / SUV / Commercial]
- UAE demand level: [HIGH / MODERATE / LOW]
- Typical retail range AED (current market snapshot)

### 4. CONFIDENCE
- Overall decode confidence: [HIGH / MEDIUM / LOW]
- GCC verification confidence: [HIGH / MEDIUM / LOW]

### COPILOT HANDOFF FLAG
[READY_FOR_COPILOT / NEEDS_CLARIFICATION / ESCALATE]

---
**Note:** This is external research only. Do NOT provide trade-in decisions or SAP values.
`;

async function run({ vin }) {
  if (!vin || vin.length !== 17) {
    throw new Error(`Invalid VIN: "${vin}". Must be 17 characters.`);
  }

  return {
    prompt: PROMPT_TEMPLATE(vin),
    promptName: 'VIN Intelligence Scan',
    vin,
    instructions: 'Submit this prompt to Claude. Results feed into /gcc-verify and /master-scan.',
  };
}

module.exports = { run, PROMPT_TEMPLATE };
