/**
 * COE Pricing Workflow Configuration
 * Al-Futtaim Automotive | UC Pricing COE
 */

module.exports = {

  // ── Agent Boundary ───────────────────────────────────────────────────────
  agents: {
    claude: {
      role: 'External Research',
      scope: [
        'VIN decode & recall check',
        '7-platform UAE market pricing',
        'MOI accident history',
        'GCC/Non-GCC verification',
        'Emirates Auction + Copart MEA',
        'Reliability & residual scoring',
        'Executive summary compilation',
        'Copilot handoff packaging',
      ],
      forbidden: [
        'SAP P01 data access',
        'Trade-in decisions (ACQUIRE/NEGOTIATE/DECLINE)',
        'Autorola fleet comments',
        'AFM guideline values',
        'GM / SIV internal targets',
      ],
    },
    copilot: {
      role: 'Internal Appraisal',
      scope: [
        'SAP P01 RFC calls',
        'Autorola fleet/auction comments',
        'Trade-in decision (ACQUIRE/NEGOTIATE/DECLINE)',
        'AFM guideline cross-reference',
        'SIV / GM / Risk calculations',
        'DSR consolidation entry',
        'Final appraisal output',
      ],
    },
  },

  // ── Pricing Rules ─────────────────────────────────────────────────────────
  pricing: {
    gcc: {
      confirmedPremium:    { min: 0.05, max: 0.08 },   // +5% to +8%
      nonGccDeduction:     { min: 0.10, max: 0.18 },   // –10% to –18%
      nonGccUnverified:    { floor: 0.15 },             // –15% floor
    },

    mileagePenalties: {
      economy:  { benchmark: 15000, penaltyPer10k: 800  },
      mid:      { benchmark: 12000, penaltyPer10k: 1200 },
      premium:  { benchmark: 10000, penaltyPer10k: 1800 },
      luxury:   { benchmark: 8000,  penaltyPer10k: 2500 },
    },

    colourAdjustments: {
      white:        0,
      silver:       -500,
      grey:         -500,
      black:        1000,
      red_sports:   2000,
      uncommon:     -1500,
    },

    accidentDeductions: {
      none:       0,
      minor_1:    { min: 1500, max: 3000 },
      moderate_1: { min: 4000, max: 8000 },
      major:      { min: 10000, max: 20000 },  // Flag for review
    },
  },

  // ── Platforms ─────────────────────────────────────────────────────────────
  platforms: {
    research: [
      { name: 'Dubizzle',         url: 'https://dubizzle.com/used-cars', priority: 1 },
      { name: 'Dubicars',         url: 'https://dubicars.com',           priority: 2 },
      { name: 'Cars24 UAE',       url: 'https://cars24.com/ae',          priority: 3 },
      { name: 'YallaMotor',       url: 'https://yallamotor.com',         priority: 4 },
      { name: 'CarSwitch',        url: 'https://carswitch.com',          priority: 5 },
      { name: 'Emirates Auction', url: 'https://emiratesauction.com',    priority: 6 },
      { name: 'Copart MEA',       url: 'https://copart.com/mea',         priority: 7 },
    ],
  },

  // ── Services ──────────────────────────────────────────────────────────────
  services: {
    afPricingAgent: {
      baseUrl:          'http://localhost:3001',
      healthEndpoint:   '/api/health',
      priceEndpoint:    '/api/price',
      breakdownEndpoint:'/api/price/breakdown',
    },
    vehiclePricingWidget: {
      devServer:        'http://localhost:5173',
      scraperBackend:   'http://localhost:3002',
      scraperEndpoint:  '/api/scrape/dubizzle',
      searchEngineId:   '2079fa71b048e4d56',
    },
  },

  // ── SAP RFC Architecture ──────────────────────────────────────────────────
  sap: {
    rfcs: [
      {
        name:        'Z_GET_VEHICLE_HEADER_BY_VIN',
        description: 'VIN → vehicle header data (make, model, year, internal vehicle no.)',
        inputKey:    'VIN',
        outputKey:   'INTVEHNO',
      },
      {
        name:        'Z_GET_AFTERSALES_PROFILE_BY_INTVEHNO',
        description: 'Internal vehicle number → aftersales profile (warranty, service history)',
        inputKey:    'INTVEHNO',
      },
    ],
    system: 'P01',
    agent:  'Copilot only — Claude does not access SAP',
  },

  // ── Output Standards ──────────────────────────────────────────────────────
  output: {
    handoffStatuses: ['READY_FOR_COPILOT', 'NEEDS_CLARIFICATION', 'ESCALATE'],
    confidenceLevels: ['HIGH', 'MEDIUM', 'LOW'],
    tradeInDecisions: ['ACQUIRE', 'NEGOTIATE', 'DECLINE'],  // Copilot only
  },
};
