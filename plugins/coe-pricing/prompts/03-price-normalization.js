/**
 * PROMPT 03 — Price Normalization Engine
 * Scrapes and normalizes pricing across 5 UAE platforms.
 * Integrates with vehicle-pricing-widget Puppeteer scraper.
 */

const PRICE_PROMPT = (make, model, year, mileage) => `
You are the COE Pricing Intelligence Agent for Al-Futtaim Automotive (UAE).

## TASK: 7-PLATFORM PRICE NORMALIZATION

**Vehicle:** ${year} ${make} ${model}
**Mileage:** ${mileage ? mileage.toLocaleString() + ' km' : 'Not specified'}

Search and compile pricing from ALL available sources:

### PLATFORM SCAN

| Platform       | Listings Found | Price Range (AED) | Avg Price (AED) | Avg Mileage | Spec |
|---------------|---------------|-------------------|-----------------|-------------|------|
| Dubizzle       |               |                   |                 |             |      |
| Dubicars       |               |                   |                 |             |      |
| Cars24 UAE     |               |                   |                 |             |      |
| YallaMotor     |               |                   |                 |             |      |
| CarSwitch      |               |                   |                 |             |      |

### PRICE NORMALIZATION

1. **Raw average** (all listings): AED [AMOUNT]
2. **Outlier removal** (remove top/bottom 10%): AED [AMOUNT]
3. **Mileage adjustment** (to ${mileage || 'benchmark'} km): AED [ADJUSTMENT]
4. **GCC spec premium** (if applicable): AED [ADJUSTMENT]
5. **Normalized Market Price:** AED [FINAL]

### PRICING BAND
- **Floor (trade-in / acquire):** AED [AMOUNT]
- **Mid (fair market):** AED [AMOUNT]
- **Ceiling (retail asking):** AED [AMOUNT]

### MARKET VELOCITY
- Average days on market: [N days]
- Supply pressure: [OVERSUPPLIED / BALANCED / UNDERSUPPLIED]
- Price trend (30-day): [RISING / STABLE / DECLINING]

### COPILOT HANDOFF FLAG
[READY_FOR_COPILOT / NEEDS_CLARIFICATION / ESCALATE]
`;

async function run({ make, model, year, mileage }, scraperService) {
  // Attempt live scrape via vehicle-pricing-widget Puppeteer service
  let scraperData = null;
  if (scraperService) {
    try {
      scraperData = await scraperService.searchDubizzle({ make, model, year, mileage });
    } catch (e) {
      console.warn('[Price Engine] Scraper unavailable, using prompt-only mode:', e.message);
    }
  }

  return {
    prompt: PRICE_PROMPT(make, model, year, mileage),
    promptName: 'Price Normalization Engine',
    scraperData: scraperData || null,
    note: scraperData
      ? 'Live Dubizzle data pre-loaded from Puppeteer scraper.'
      : 'Scraper offline — Claude will perform manual research.',
  };
}

module.exports = { run, PRICE_PROMPT };
