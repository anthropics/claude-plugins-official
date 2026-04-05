/**
 * Service: Copilot Handoff Formatter
 * Formats Claude research output into the standard M365 Copilot handoff block
 */

class CopilotHandoffService {
  /**
   * Generate the complete structured handoff block
   * @param {Object} data
   * @param {string} data.vin
   * @param {string} data.vehicle
   * @param {Object} data.vinScan
   * @param {Object} data.moiData
   * @param {Object} data.priceData
   * @param {Object} data.auctionData
   * @param {Object} data.gccData
   * @param {Object} data.reliabilityData
   * @param {Object} data.execSummary
   */
  format(data) {
    const {
      vin, vehicle,
      vinScan, moiData, priceData, auctionData,
      gccData, reliabilityData, execSummary,
    } = data;

    const ts = new Date().toISOString();
    const date = ts.split('T')[0];

    return `
╔══════════════════════════════════════════════════════════════════╗
║  CLAUDE → COPILOT HANDOFF BLOCK                                 ║
║  Al-Futtaim UC Pricing COE                   Date: ${date}      ║
╚══════════════════════════════════════════════════════════════════╝

VEHICLE : ${vehicle || 'N/A'}
VIN     : ${vin}
TIME    : ${ts}
SOURCE  : Claude COE Pricing Intelligence (External Research)
TARGET  : Microsoft Copilot (Internal Appraisal)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — VIN INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${this._section(vinScan)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2 — MOI ACCIDENT HISTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${this._section(moiData)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — MARKET PRICING (7 PLATFORMS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${this._section(priceData)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4 — AUCTION INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${this._section(auctionData)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — GCC / NON-GCC STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${this._section(gccData)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — RELIABILITY & RESIDUAL VALUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${this._section(reliabilityData)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 7 — EXECUTIVE SUMMARY & PRICING BANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
${this._section(execSummary)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COPILOT ACTION CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 1. SAP P01: Z_GET_VEHICLE_HEADER_BY_VIN (VIN: ${vin})
[ ] 2. SAP P01: Z_GET_AFTERSALES_PROFILE_BY_INTVEHNO
[ ] 3. Autorola: Retrieve fleet/auction comments
[ ] 4. AFM Guideline: Cross-reference vs Claude normalized price
[ ] 5. Trade-In Decision: ACQUIRE / NEGOTIATE / DECLINE
[ ] 6. Final Autorola appraisal comment
[ ] 7. DSR consolidation entry

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOUNDARY CONFIRMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Claude:  External research, UAE market pricing, GCC verify, MOI
✗ Copilot: SAP data, trade-in decision, Autorola, AFM, GM targets

══════════════════════════════════════════════════════════════════
    `;
  }

  _section(data) {
    if (!data) return '[Not yet collected — run individual prompt first]';
    if (typeof data === 'string') return data;
    return JSON.stringify(data, null, 2);
  }
}

module.exports = CopilotHandoffService;
