/**
 * Creet - Plugin Registry Module
 * Curated list of known Claude Code plugins for discovery when no installed skill matches.
 */

const KNOWN_PLUGINS = [
  // Branding & Design
  {
    name: 'brand-guardian',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Branding',
    description: 'Brand guidelines, visual consistency, brand asset management',
    keywords: ['brand', 'branding', 'guideline', 'visual identity', 'logo', 'color palette',
      '브랜딩', '브랜드', '가이드라인', '비주얼', 'ブランド', 'ガイドライン', '品牌', '指南'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill brand-guardian',
  },
  {
    name: 'content-creator',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Marketing',
    description: 'Marketing content, copywriting, messaging',
    keywords: ['content', 'copy', 'copywriting', 'marketing', 'messaging', 'landing page copy',
      '카피', '마케팅', '콘텐츠', 'コピー', 'マーケティング', '文案', '营销'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill content-creator',
  },
  {
    name: 'growth-hacker',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Marketing',
    description: 'Growth optimization, scaling, market expansion strategies',
    keywords: ['growth', 'scale', 'market', 'acquisition', 'retention', 'funnel',
      '성장', '마켓', '퍼널', 'グロース', '増殖', '增长', '漏斗'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill growth-hacker',
  },
  {
    name: 'product-sales-specialist',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Product',
    description: 'B2B sales, product design, user research, project management',
    keywords: ['product', 'sales', 'b2b', 'user research', 'project management',
      '제품', '세일즈', '유저 리서치', '製品', 'セールス', '产品', '销售'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill product-sales-specialist',
  },
  {
    name: 'pricing-packaging-specialist',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Product',
    description: 'B2B pricing strategies, revenue models, packaging optimization',
    keywords: ['pricing', 'package', 'revenue', 'monetize', 'subscription',
      '가격', '패키지', '수익', '価格', 'パッケージ', '定价', '收入'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill pricing-packaging-specialist',
  },
  {
    name: 'app-store-optimizer',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Marketing',
    description: 'App store listing optimization, metadata, discoverability',
    keywords: ['app store', 'aso', 'listing', 'metadata', 'discoverability',
      '앱스토어', '최적화', 'ストア', '应用商店', '优化'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill app-store-optimizer',
  },

  // DevOps & Infrastructure
  {
    name: 'docker-compose',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'DevOps',
    description: 'Docker Compose configuration and container orchestration',
    keywords: ['docker', 'container', 'compose', 'orchestration',
      '도커', '컨테이너', 'コンテナ', '容器'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill docker-compose',
  },

  // Testing & QA
  {
    name: 'playwright-test',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Testing',
    description: 'E2E testing with Playwright, browser automation',
    keywords: ['test', 'e2e', 'playwright', 'browser test', 'automation',
      '테스트', 'E2E', 'テスト', '测试', '自动化'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill playwright-test',
  },

  // Documentation
  {
    name: 'superpowers',
    source: 'travisvn/claude-code-superpowers',
    domain: 'Productivity',
    description: 'Brainstorm, write-plan, execute-plan, structured workflows',
    keywords: ['brainstorm', 'plan', 'execute', 'workflow', 'ideation',
      '브레인스토밍', '기획', '아이디어', 'ブレスト', '企画', '头脑风暴', '策划'],
    installCmd: 'claude plugin install travisvn/claude-code-superpowers',
  },

  // Data & Analytics
  {
    name: 'data-analyst',
    source: 'ccplugins/awesome-claude-code-plugins',
    domain: 'Data',
    description: 'Data analysis, visualization, statistical insights',
    keywords: ['data', 'analytics', 'chart', 'visualization', 'statistics',
      '데이터', '분석', '차트', 'データ', '分析', '数据', '图表'],
    installCmd: 'claude plugin install ccplugins/awesome-claude-code-plugins --skill data-analyst',
  },
];

/**
 * Search registry for plugins matching a query.
 * @param {string} query - User's request
 * @returns {Array<{name, source, domain, description, installCmd, score}>}
 */
function searchRegistry(query) {
  const lowerQuery = query.toLowerCase();
  const results = [];

  for (const plugin of KNOWN_PLUGINS) {
    let score = 0;
    for (const keyword of plugin.keywords) {
      if (lowerQuery.includes(keyword.toLowerCase())) {
        score += keyword.length;
      }
    }
    // Also check domain and description
    if (lowerQuery.includes(plugin.domain.toLowerCase())) {
      score += 5;
    }
    if (score > 0) {
      results.push({ ...plugin, score });
    }
  }

  return results.sort((a, b) => b.score - a.score).slice(0, 3);
}

/**
 * Format search results for display.
 */
function formatRegistryResults(results) {
  if (results.length === 0) return null;

  let output = '## Creet — Plugin Discovery\n\n';
  output += 'No installed skill matches, but these plugins might help:\n\n';
  output += '| Plugin | Domain | Description | Install |\n';
  output += '|--------|--------|-------------|--------|\n';

  for (const r of results) {
    output += `| ${r.name} | ${r.domain} | ${r.description} | \`${r.installCmd}\` |\n`;
  }

  return output;
}

module.exports = { searchRegistry, formatRegistryResults, KNOWN_PLUGINS };
