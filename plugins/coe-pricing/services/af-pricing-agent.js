/**
 * Service: af-pricing-agent Client
 * Connects to the Express backend at http://localhost:3001
 * Repo: qasimsethi-code/af-pricing-agent
 */

class AfPricingAgentService {
  constructor({ baseUrl, healthEndpoint, priceEndpoint }) {
    this.baseUrl       = baseUrl       || 'http://localhost:3001';
    this.healthPath    = healthEndpoint || '/api/health';
    this.pricePath     = priceEndpoint  || '/api/price';
    this.timeout       = 8000;
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

      if (!res.ok) {
        throw new Error(`af-pricing-agent HTTP ${res.status}: ${res.statusText}`);
      }
      return res.json();
    } catch (e) {
      clearTimeout(timer);
      if (e.name === 'AbortError') {
        throw new Error('af-pricing-agent request timed out after 8s');
      }
      throw e;
    }
  }

  async ping() {
    try {
      const data = await this._fetch(this.healthPath);
      return data.status === 'ok' ? 'OK' : 'DEGRADED';
    } catch {
      return 'OFFLINE';
    }
  }

  /**
   * Calculate price using af-pricing-agent rules:
   *   - GCC spec premiums
   *   - Mileage penalties
   *   - Non-GCC deductions
   *   - Colour premiums
   *
   * @param {Object} params
   * @param {string} params.make
   * @param {string} params.model
   * @param {number} params.year
   * @param {string} params.grade
   * @param {number} params.mileage
   * @param {string} params.colour
   * @param {boolean} params.isGCC
   * @param {boolean} params.hasAccident
   * @param {number}  params.baseMarketPrice
   */
  async calculatePrice(params) {
    return this._fetch(this.pricePath, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  /**
   * Get full pricing breakdown with adjustment stack
   */
  async getPricingBreakdown(params) {
    return this._fetch('/api/price/breakdown', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  /**
   * Get DSR data (if af-pricing-agent has consolidation endpoint)
   */
  async getDSRData({ date, dealer } = {}) {
    const query = new URLSearchParams({ date, dealer }).toString();
    return this._fetch(`/api/dsr?${query}`);
  }
}

module.exports = AfPricingAgentService;
