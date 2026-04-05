/**
 * Service: Dubizzle Scraper Bridge
 * Connects to the Puppeteer scraper in vehicle-pricing-widget backend
 * Repo: qasimsethi-code/vehicle-pricing-widget
 * Endpoint: POST /api/scrape/dubizzle (Express backend, port 5174 or 3002)
 */

class DubizzleScraperService {
  constructor({ devServer, scraperEndpoint }) {
    // vehicle-pricing-widget Express backend (separate from Vite dev server)
    this.baseUrl        = process.env.SCRAPER_BASE_URL || 'http://localhost:3002';
    this.scraperPath    = scraperEndpoint || '/api/scrape/dubizzle';
    this.widgetFrontend = devServer || 'http://localhost:5173';
    this.timeout        = 30000; // Puppeteer needs more time
  }

  async _fetch(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const res = await fetch(`${this.baseUrl}${path}`, {
        ...options,
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      });
      clearTimeout(timer);
      if (!res.ok) throw new Error(`Scraper HTTP ${res.status}`);
      return res.json();
    } catch (e) {
      clearTimeout(timer);
      if (e.name === 'AbortError') throw new Error('Scraper timed out (30s). Dubizzle may be slow.');
      throw e;
    }
  }

  async ping() {
    try {
      await this._fetch('/api/health');
      return 'OK';
    } catch {
      return 'OFFLINE';
    }
  }

  /**
   * Search Dubizzle for vehicle listings
   * @param {Object} params
   * @param {string} params.make
   * @param {string} params.model
   * @param {number} params.year
   * @param {number} [params.mileage]
   * @param {string} [params.trim]
   * @returns {Object} { listings: [], avgPrice, priceRange, avgMileage }
   */
  async searchDubizzle({ make, model, year, mileage, trim } = {}) {
    return this._fetch(this.scraperPath, {
      method: 'POST',
      body: JSON.stringify({ make, model, year, mileage, trim }),
    });
  }

  /**
   * Get Google Custom Search results for price estimator
   * Uses Search Engine ID: 2079fa71b048e4d56
   */
  async googlePriceSearch({ query }) {
    return this._fetch('/api/search/price', {
      method: 'POST',
      body: JSON.stringify({ query, searchEngineId: '2079fa71b048e4d56' }),
    });
  }

  /**
   * Build a normalized pricing dataset from scraper results
   */
  normalizeListings(listings = []) {
    if (!listings.length) return null;

    const prices = listings.map(l => l.price).filter(Boolean).sort((a, b) => a - b);
    const trimPct = Math.floor(prices.length * 0.1);
    const trimmed = prices.slice(trimPct, prices.length - trimPct);
    const avg = Math.round(trimmed.reduce((a, b) => a + b, 0) / trimmed.length);

    return {
      count: listings.length,
      rawMin: prices[0],
      rawMax: prices[prices.length - 1],
      trimmedAvg: avg,
      floor: Math.round(avg * 0.93),   // –7% for trade-in floor
      ceiling: Math.round(avg * 1.05), // +5% retail ceiling
    };
  }
}

module.exports = DubizzleScraperService;
