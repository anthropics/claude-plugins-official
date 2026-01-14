#!/usr/bin/env node

/**
 * Viz Vibe - Stop Hook
 * 
 * This hook triggers after Claude completes a response.
 * It instructs Claude to update vizvibe.mmd with the work done.
 *
 * State management:
 * - "idle": Normal conversation, should trigger update
 * - "updating": Currently updating trajectory, should skip and reset to idle
 */

const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const STATE_FILE = path.join(projectDir, '.vizvibe-state.json');

function getState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const data = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
      return data.mode || 'idle';
    }
  } catch (e) {}
  return 'idle';
}

function setState(mode, lastActiveNode = null) {
  const state = { mode, updatedAt: new Date().toISOString() };
  if (lastActiveNode !== null) {
    state.lastActiveNode = lastActiveNode;
  } else {
    // Preserve existing lastActiveNode
    try {
      const existing = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
      if (existing.lastActiveNode) {
        state.lastActiveNode = existing.lastActiveNode;
      }
    } catch (e) {}
  }
  fs.writeFileSync(STATE_FILE, JSON.stringify(state));
}

function extractLastActiveNode(projectDir) {
  const trajectoryPath = path.join(projectDir, 'vizvibe.mmd');
  try {
    const content = fs.readFileSync(trajectoryPath, 'utf-8');
    const match = content.match(/%% @lastActive:\s*(\w+)/);
    return match ? match[1] : null;
  } catch (e) {
    return null;
  }
}

// Read stdin
let inputData = '';
process.stdin.setEncoding('utf8');

process.stdin.on('readable', () => {
  let chunk;
  while ((chunk = process.stdin.read()) !== null) {
    inputData += chunk;
  }
});

process.stdin.on('end', () => {
  try {
    const input = JSON.parse(inputData);

    // Prevent infinite loop: if already in hook continuation, let Claude stop
    if (input.stop_hook_active) {
      const lastActive = extractLastActiveNode(projectDir);
      setState('idle', lastActive);  // Reset state and update lastActiveNode
      process.exit(0);
    }

    const trajectoryPath = path.join(projectDir, 'vizvibe.mmd');

    // Check if vizvibe.mmd exists
    if (!fs.existsSync(trajectoryPath)) {
      process.exit(0);
    }

    // Analyze transcript to determine if update is needed
    const transcriptPath = input.transcript_path;
    if (transcriptPath && fs.existsSync(transcriptPath)) {
      const transcript = fs.readFileSync(transcriptPath, 'utf-8');
      const lines = transcript.trim().split('\n').filter(Boolean);

      // Skip if conversation is too short (likely just a question)
      if (lines.length < 4) {
        process.exit(0);
      }
    }

    // State-based duplicate prevention
    const currentState = getState();

    if (currentState === 'updating') {
      // Just finished updating trajectory, reset to idle and skip
      const lastActive = extractLastActiveNode(projectDir);
      setState('idle', lastActive);
      process.exit(0);
    }

    // Set state to updating before requesting trajectory update
    setState('updating');

    // Output instruction for Claude to continue and update trajectory
    const response = {
      decision: "block",
      reason: `Update vizvibe.mmd based on the work done in this session. Follow the format in the vizvibe skill.`
    };

    process.stdout.write(JSON.stringify(response));
    process.exit(0);

  } catch (error) {
    // On error, allow Claude to stop normally
    process.exit(0);
  }
});
