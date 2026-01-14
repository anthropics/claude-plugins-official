#!/usr/bin/env node

/**
 * Viz Vibe - SessionStart Hook
 * 
 * This hook runs when a Claude Code session starts.
 * It reads vizvibe.mmd and provides context to Claude.
 */

const fs = require('fs');
const path = require('path');

// Get project directory from environment
const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.dirname(path.dirname(__filename));

const trajectoryPath = path.join(projectDir, 'vizvibe.mmd');
const skillPath = path.join(pluginRoot, 'skills', 'vizvibe', 'SKILL.md');
const stateFile = path.join(projectDir, '.vizvibe-state.json');

function extractLastActiveNode(content) {
  const match = content.match(/%% @lastActive:\s*(\w+)/);
  return match ? match[1] : null;
}

function updateStateWithLastActive(lastActiveNode) {
  try {
    let state = { mode: 'idle', updatedAt: new Date().toISOString() };
    if (fs.existsSync(stateFile)) {
      state = JSON.parse(fs.readFileSync(stateFile, 'utf-8'));
    }
    state.lastActiveNode = lastActiveNode;
    fs.writeFileSync(stateFile, JSON.stringify(state));
  } catch (e) {}
}

// Check if vizvibe.mmd exists in project
if (!fs.existsSync(trajectoryPath)) {
  // No trajectory file - exit silently
  process.exit(0);
}

const trajectory = fs.readFileSync(trajectoryPath, 'utf-8');

// Extract lastActiveNode and update state
const lastActiveNode = extractLastActiveNode(trajectory);
if (lastActiveNode) {
  updateStateWithLastActive(lastActiveNode);
}

// Extract node descriptions from comments (both old and new format)
const nodeDescriptions = [];
const nodeIds = [];
const lines = trajectory.split('\n');
for (const line of lines) {
  // Try new format first: %% @node_id [type, state, date, author]
  let match = line.match(/%% @([\w-]+) \[([\w-]+)(?:,\s*\w+)?(?:,\s*[\d-]+)?(?:,\s*\w+)?\]/);
  if (match) {
    const [, nodeId, nodeType] = match;
    nodeIds.push(nodeId);
    const isActive = nodeId === lastActiveNode ? ' ⬅️ RECENT' : '';
    nodeDescriptions.push(`- [${nodeType}] ${nodeId}${isActive}`);
    continue;
  }
  
  // Try old format: %% @node_id [type, state]: description
  match = line.match(/%% @([\w-]+) \[([\w-]+)(?:,\s*\w+)?\]: (.+)/);
  if (match) {
    const [, nodeId, nodeType, description] = match;
    nodeIds.push(nodeId);
    const isActive = nodeId === lastActiveNode ? ' ⬅️ RECENT' : '';
    nodeDescriptions.push(`- [${nodeType}] ${description}${isActive}`);
  }
}

// Check if trajectory is in template state (only has project_start node)
const isTemplateState = nodeIds.length <= 1 && (nodeIds.length === 0 || nodeIds[0] === 'project_start');

// Read SKILL.md if exists (contains VIZVIBE.md content)
let skillContent = '';
if (fs.existsSync(skillPath)) {
  skillContent = fs.readFileSync(skillPath, 'utf-8');
}

// Build context message
let context;

if (isTemplateState) {
  // Template state - request initial trajectory creation
  context = `=== Viz Vibe: Initial Setup Required ===

⚠️ **ACTION REQUIRED**: This project has Viz Vibe installed but the trajectory is empty (template state).

Please create an initial trajectory based on:
1. Our conversation history (if any)
2. The codebase structure and recent git commits
3. README.md and other documentation

After analyzing the project, update vizvibe.mmd with:
- Project goals (ultimate and current)
- Completed work as [closed] nodes
- Planned work as [opened] nodes
- Proper connections between related nodes

---
${skillContent}
`;
} else {
  // Normal state - show current trajectory
  const lastActiveInfo = lastActiveNode ? `\nLast active node: ${lastActiveNode}` : '';
  context = `=== Viz Vibe: Project Trajectory ===

This project uses Viz Vibe to track work history. When you complete tasks, update vizvibe.mmd.
${lastActiveInfo}

Current trajectory has ${nodeDescriptions.length} nodes:
${nodeDescriptions.slice(-5).join('\n')}
${nodeDescriptions.length > 5 ? `\n... and ${nodeDescriptions.length - 5} more nodes` : ''}

**Important**: When updating vizvibe.mmd, also update the \`%% @lastActive: node_id\` line with the node you just worked on.

---
${skillContent}
`;
}

// Output as JSON with additionalContext
const output = {
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: context
  }
};

console.log(JSON.stringify(output));
