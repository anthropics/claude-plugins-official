#!/usr/bin/env node

/**
 * Captain CP Memory System - Core Library
 * Persistent memory management for Claude Code CLI
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const MEMORY_DIR = path.join(os.homedir(), '.claude-memory');
const MEMORY_FILE = path.join(MEMORY_DIR, 'memories.jsonl');

// Ensure memory directory exists
function ensureMemoryDir() {
  if (!fs.existsSync(MEMORY_DIR)) {
    fs.mkdirSync(MEMORY_DIR, { recursive: true });
  }
}

// Save a memory entry
function saveMemory(content, type = 'note', metadata = {}) {
  ensureMemoryDir();
  
  const entry = {
    timestamp: new Date().toISOString(),
    type,
    content,
    metadata
  };
  
  fs.appendFileSync(MEMORY_FILE, JSON.stringify(entry) + '\n', 'utf8');
  return entry;
}

// Load all memories
function loadMemories() {
  ensureMemoryDir();
  
  if (!fs.existsSync(MEMORY_FILE)) {
    return [];
  }
  
  const data = fs.readFileSync(MEMORY_FILE, 'utf8');
  return data
    .split('\n')
    .filter(line => line.trim())
    .map(line => JSON.parse(line));
}

// Search memories by keyword
function searchMemories(query, limit = 10) {
  const memories = loadMemories();
  const queryLower = query.toLowerCase();
  
  return memories
    .filter(m => m.content.toLowerCase().includes(queryLower))
    .reverse()
    .slice(0, limit);
}

// Get recent memories
function recentMemories(count = 5) {
  const memories = loadMemories();
  return memories.slice(-count).reverse();
}

// Get memory stats
function getStats() {
  const memories = loadMemories();
  const stats = {
    total: memories.length,
    byType: {},
    oldest: memories[0]?.timestamp,
    newest: memories[memories.length - 1]?.timestamp
  };
  
  memories.forEach(m => {
    stats.byType[m.type] = (stats.byType[m.type] || 0) + 1;
  });
  
  return stats;
}

module.exports = {
  saveMemory,
  loadMemories,
  searchMemories,
  recentMemories,
  getStats
};
