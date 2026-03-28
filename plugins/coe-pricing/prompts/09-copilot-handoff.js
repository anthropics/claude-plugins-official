/**
 * PROMPT 09 — Copilot Handoff Trigger
 * Packages all Claude research into a structured block for Microsoft Copilot.
 */

function buildHandoffBlock(vin, scanData) {
  const ts = new Date().toISOString();
  return `
╔══════════════════════════════════════════════════════════════════╗
║         CLAUDE → COPILOT HANDOFF BLOCK                          ║
║         Al-Futtaim UC Pricing COE | ${ts.split('T')[0]}         ║
╚══════════════════════════════════════════════════════════════════╝

## HANDOFF METADATA
- Source Agent:    Claude COE Pricing Intelligence (External Research)
- Target Agent:    Microsoft Copilot (Internal Appraisal)
- VIN:             ${vin}
- Timestamp:       ${ts}
- Pipeline Status: RESEARCH COMPLETE — READY FOR INTERNAL APPRAISAL

## CLAUDE RESEARCH SUMMARY
${scanData ? JSON.stringify(scanData, null, 2) : '[Paste Claude research output here]'}

## COPILOT ACTION ITEMS
Copilot: Please complete the following using internal systems:

1. **SAP P01 Lookup**
   - Call Z_GET_VEHICLE_HEADER_BY_VIN with VIN: ${vin}
   - Call Z_GET_AFTERSALES_PROFILE_BY_INTVEHNO with retrieved INTVEHNO
   - Extract: SIV, stock age, GM target, warranty status

2. **Autorola Comments**
   - Retrieve fleet/auction history comments for this VIN
   - Flag any condition notes relevant to appraisal

3. **Trade-In Decision**
   - Apply Claude's recommended pricing band (above) to internal GM targets
   - Decision: ACQUIRE / NEGOTIATE / DECLINE
   - If NEGOTIATE: counter-offer at AED [___]

4. **AFM Guideline Check**
   - Cross-reference Claude's normalized price vs AFM guideline value
   - Variance: AED [___] ([+/-]%)

5. **Final Appraisal Output**
   - Complete Autorola appraisal comment
   - Submit to DSR consolidation pipeline

## BOUNDARY CONFIRMATION
✓ Claude handled:  External research, 7-platform pricing, GCC verification, MOI query
✗ Copilot handles: SAP data, trade-in decision, Autorola, AFM guidelines, GM targets

══════════════════════════════════════════════════════════════════
`;
}

const COPILOT_PROMPT = (vin, scanData) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: COPILOT HANDOFF TRIGGER

Generate the structured Copilot Handoff Block for VIN: ${vin}

Compile ALL research from this session and format as the standard
Al-Futtaim COE handoff block. Include:

1. Handoff metadata (VIN, timestamp, agent identifiers)
2. Research summary (all 7 modules condensed)
3. Pricing bands (floor / target / ceiling in AED)
4. GCC status and confidence
5. Accident history summary
6. Risk flags
7. Copilot action checklist (SAP lookup, Autorola, trade-in decision)
8. Boundary confirmation line

${scanData ? `Pre-loaded scan data:\n${JSON.stringify(scanData, null, 2)}` : ''}

Format the output as a clean, copy-paste-ready block that can be
pasted directly into Microsoft Copilot chat.
`;

async function run({ vin, scanData }, copilotHandoffService) {
  const handoffBlock = buildHandoffBlock(vin, scanData);

  return {
    prompt: COPILOT_PROMPT(vin, scanData),
    promptName: 'Copilot Handoff Trigger',
    vin,
    handoffBlock,        // Pre-built structural template
    instructions: [
      '1. Claude generates the complete handoff block.',
      '2. Copy the entire block.',
      '3. Open Microsoft Copilot (corporate M365).',
      '4. Paste and send — Copilot handles internal appraisal from here.',
    ],
  };
}

module.exports = { run, buildHandoffBlock, COPILOT_PROMPT };
