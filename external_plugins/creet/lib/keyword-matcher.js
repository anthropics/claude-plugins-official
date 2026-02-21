/**
 * Creet - Keyword Matcher Module
 * Dynamically builds keyword map from scanner results.
 * No hardcoded skill names — works with any installed plugin combination.
 */

const path = require('path');
const fs = require('fs');

const PLUGIN_ROOT = path.resolve(__dirname, '..');
const CACHE_PATH = path.join(PLUGIN_ROOT, '.creet-cache.json');

/**
 * Build keyword map dynamically from scanner results.
 * Uses each skill's triggers as keywords.
 * @param {Array} scanResults - Output from scanInstalledSkills()
 * @returns {Array<{skill: string, domain: string, keywords: string[]}>}
 */
function buildKeywordMap(scanResults) {
  return scanResults
    .filter(s => s.triggers && s.triggers.length > 0)
    .map(s => ({
      skill: s.name,
      domain: s.domain || 'General',
      keywords: s.triggers,
    }));
}

/**
 * Save scan results to cache for use by UserPromptSubmit hook.
 */
function saveScanCache(scanResults) {
  try {
    fs.writeFileSync(CACHE_PATH, JSON.stringify(scanResults), 'utf-8');
  } catch {
    // Non-critical — prompt handler will just skip matching
  }
}

/**
 * Load cached scan results.
 */
function loadCachedScanResults() {
  try {
    if (fs.existsSync(CACHE_PATH)) {
      return JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8'));
    }
  } catch {}
  return [];
}

/**
 * Match user message against dynamically built keyword map.
 * @param {string} message - User's message
 * @param {Array|null} scanResults - Scanner output (null = use cache)
 * @param {Array} customMap - Optional custom keyword entries from config
 * @returns {Array<{skill: string, domain: string, score: number}>}
 */
function matchKeywords(message, scanResults, customMap) {
  const results = scanResults || loadCachedScanResults();
  const keywordMap = buildKeywordMap(results);

  // Merge custom keywords if provided
  if (customMap && Array.isArray(customMap)) {
    keywordMap.push(...customMap);
  }

  const lowerMsg = message.toLowerCase();
  const matches = [];

  for (const entry of keywordMap) {
    let score = 0;
    for (const keyword of entry.keywords) {
      if (lowerMsg.includes(keyword.toLowerCase())) {
        score += keyword.length;
      }
    }
    if (score > 0) {
      matches.push({
        skill: entry.skill,
        domain: entry.domain,
        score,
      });
    }
  }

  return matches.sort((a, b) => b.score - a.score);
}

/**
 * Format keyword table from scan results for session context.
 * @param {Array|null} scanResults - Scanner output (null = use cache)
 */
function formatKeywordTable(scanResults) {
  const results = scanResults || loadCachedScanResults();
  const keywordMap = buildKeywordMap(results);

  if (keywordMap.length === 0) {
    return 'No keyword mappings detected (no skills with triggers found).';
  }

  let table = '| Domain | Skill | Sample Keywords |\n';
  table += '|--------|-------|-----------------|\n';

  for (const entry of keywordMap) {
    const samples = entry.keywords.slice(0, 5).join(', ');
    const prefix = entry.domain === 'LSP' ? '' : '/';
    table += `| ${entry.domain} | ${prefix}${entry.skill} | ${samples} |\n`;
  }

  return table;
}

module.exports = { matchKeywords, formatKeywordTable, buildKeywordMap, saveScanCache, loadCachedScanResults };
