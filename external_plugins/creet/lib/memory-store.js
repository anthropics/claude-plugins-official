/**
 * Creet - Memory Store Module
 * Persists session data across Claude Code sessions.
 */

const fs = require('fs');
const path = require('path');

const DEFAULT_MEMORY_FILE = '.creet-memory.json';

/**
 * Get memory file path (project-level or fallback to cwd).
 */
function getMemoryPath(configPath) {
  if (configPath) {
    const dir = path.dirname(configPath);
    if (fs.existsSync(dir)) return configPath;
  }

  // Try docs/ directory first
  const docsDir = path.join(process.cwd(), 'docs');
  if (fs.existsSync(docsDir)) {
    return path.join(docsDir, DEFAULT_MEMORY_FILE);
  }

  return path.join(process.cwd(), DEFAULT_MEMORY_FILE);
}

/**
 * Load memory from file.
 */
function loadMemory(configPath) {
  const memPath = getMemoryPath(configPath);

  try {
    if (fs.existsSync(memPath)) {
      return JSON.parse(fs.readFileSync(memPath, 'utf-8'));
    }
  } catch {
    // Corrupted file, start fresh
  }

  return createDefaultMemory();
}

/**
 * Save memory to file.
 */
function saveMemory(memory, configPath) {
  const memPath = getMemoryPath(configPath);

  try {
    const dir = path.dirname(memPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(memPath, JSON.stringify(memory, null, 2), 'utf-8');
    return true;
  } catch {
    return false;
  }
}

/**
 * Create default memory structure.
 */
function createDefaultMemory() {
  return {
    version: '1.0.0',
    sessionCount: 0,
    lastSessionAt: null,
    lastUsedSkills: [],
    recommendationHistory: [],
    skillUsageCount: {},
  };
}

/**
 * Record a new session start.
 */
function recordSessionStart(memory) {
  memory.sessionCount = (memory.sessionCount || 0) + 1;
  memory.lastSessionAt = new Date().toISOString();
  return memory;
}

/**
 * Record a skill usage.
 */
function recordSkillUsage(memory, skillName) {
  // Update last used
  memory.lastUsedSkills = memory.lastUsedSkills || [];
  memory.lastUsedSkills = [skillName, ...memory.lastUsedSkills.filter(s => s !== skillName)].slice(0, 10);

  // Update count
  memory.skillUsageCount = memory.skillUsageCount || {};
  memory.skillUsageCount[skillName] = (memory.skillUsageCount[skillName] || 0) + 1;

  return memory;
}

/**
 * Record a recommendation.
 */
function recordRecommendation(memory, request, recommendedSkills) {
  memory.recommendationHistory = memory.recommendationHistory || [];
  memory.recommendationHistory.unshift({
    request: request.substring(0, 100),
    skills: recommendedSkills,
    at: new Date().toISOString()
  });
  // Keep last 20 recommendations
  memory.recommendationHistory = memory.recommendationHistory.slice(0, 20);
  return memory;
}

/**
 * Get top used skills.
 */
function getTopSkills(memory, limit = 5) {
  const counts = memory.skillUsageCount || {};
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name, count]) => ({ name, count }));
}

/**
 * Format memory summary for session context.
 */
function formatMemorySummary(memory) {
  const lines = [];

  lines.push(`Session #${memory.sessionCount || 1}`);

  if (memory.lastSessionAt) {
    const last = new Date(memory.lastSessionAt);
    lines.push(`Last session: ${last.toLocaleDateString()}`);
  }

  if (memory.lastUsedSkills && memory.lastUsedSkills.length > 0) {
    lines.push(`Recently used: ${memory.lastUsedSkills.slice(0, 5).map(s => '/' + s).join(', ')}`);
  }

  const topSkills = getTopSkills(memory, 3);
  if (topSkills.length > 0) {
    lines.push(`Most used: ${topSkills.map(s => `/${s.name}(${s.count})`).join(', ')}`);
  }

  return lines.join('\n');
}

module.exports = {
  loadMemory,
  saveMemory,
  recordSessionStart,
  recordSkillUsage,
  recordRecommendation,
  getTopSkills,
  formatMemorySummary,
};
