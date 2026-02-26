#!/usr/bin/env node

// Ralph Loop Stop Hook (Node.js)
// Prevents session exit when a ralph-loop is active.
// Feeds Claude's output back as input to continue the loop.
//
// This is a cross-platform Node.js port of stop-hook.sh.
// It eliminates external dependencies (jq, perl, awk, sed, grep)
// and fixes Windows MSYS2/Cygwin bash race conditions that cause
// "add_item" fatal errors when multiple bash-based hooks run in parallel.

'use strict';

const fs = require('fs');
const path = require('path');

const RALPH_STATE_FILE = path.join(process.cwd(), '.claude', 'ralph-loop.local.md');

// ─────────────────────────────────────────────
// Stdin Reader
// ─────────────────────────────────────────────

function readStdin() {
  return new Promise((resolve) => {
    let input = '';
    const timeout = setTimeout(() => resolve('{}'), 5000);

    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { input += chunk; });
    process.stdin.on('end', () => {
      clearTimeout(timeout);
      resolve(input || '{}');
    });
  });
}

// ─────────────────────────────────────────────
// Frontmatter Parser
// ─────────────────────────────────────────────

/**
 * Parse YAML frontmatter between --- delimiters.
 * Returns an object with key-value pairs.
 */
function parseFrontmatter(content) {
  const lines = content.split('\n');
  let inFrontmatter = false;
  const frontmatterLines = [];
  let delimiterCount = 0;

  for (const line of lines) {
    if (line.trim() === '---') {
      delimiterCount++;
      if (delimiterCount === 1) { inFrontmatter = true; continue; }
      if (delimiterCount === 2) { break; }
    }
    if (inFrontmatter) {
      frontmatterLines.push(line);
    }
  }

  const result = {};
  for (const line of frontmatterLines) {
    const match = line.match(/^(\w+):\s*(.*)/);
    if (match) {
      let value = match[2].trim();
      // Strip surrounding quotes
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      result[match[1]] = value;
    }
  }

  return result;
}

// ─────────────────────────────────────────────
// Prompt Extractor
// ─────────────────────────────────────────────

/**
 * Extract everything after the second --- delimiter.
 * Handles --- appearing within prompt content (delimiterCount > 2).
 */
function extractPrompt(content) {
  const lines = content.split('\n');
  let delimiterCount = 0;
  const promptLines = [];
  let collecting = false;

  for (const line of lines) {
    if (line.trim() === '---') {
      delimiterCount++;
      if (delimiterCount === 2) { collecting = true; continue; }
    }
    if (collecting) {
      promptLines.push(line);
    }
  }

  return promptLines.join('\n').trim();
}

// ─────────────────────────────────────────────
// Promise Detection
// ─────────────────────────────────────────────

/**
 * Extract text from the first <promise>...</promise> tag.
 * Normalizes whitespace for comparison.
 */
function extractPromiseText(text) {
  const match = text.match(/<promise>([\s\S]*?)<\/promise>/);
  if (!match) return '';
  return match[1].trim().replace(/\s+/g, ' ');
}

// ─────────────────────────────────────────────
// Transcript Reader
// ─────────────────────────────────────────────

/**
 * Read the last assistant message from a JSONL transcript file.
 * Searches from end of file for efficiency with large transcripts.
 */
function getLastAssistantOutput(transcriptPath) {
  if (!fs.existsSync(transcriptPath)) return null;

  const content = fs.readFileSync(transcriptPath, 'utf8');
  const lines = content.split('\n').filter(Boolean);

  // Search from end for last assistant message
  let lastAssistantLine = null;
  for (let i = lines.length - 1; i >= 0; i--) {
    if (lines[i].includes('"role":"assistant"')) {
      lastAssistantLine = lines[i];
      break;
    }
  }

  if (!lastAssistantLine) return null;

  try {
    const parsed = JSON.parse(lastAssistantLine);
    const contentArr = parsed.message && parsed.message.content;
    if (!Array.isArray(contentArr)) return null;

    return contentArr
      .filter(function(item) { return item.type === 'text'; })
      .map(function(item) { return item.text; })
      .join('\n');
  } catch (_) {
    return null;
  }
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function removeStateFile() {
  try { fs.unlinkSync(RALPH_STATE_FILE); } catch (_) { /* ignore */ }
}

function failAndCleanup(message) {
  process.stderr.write(message + '\n');
  removeStateFile();
  process.exit(0);
}

// ─────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────

async function main() {
  const rawInput = await readStdin();

  // Check if ralph-loop is active
  if (!fs.existsSync(RALPH_STATE_FILE)) {
    // No active loop - allow exit
    process.exit(0);
  }

  let hookInput;
  try { hookInput = JSON.parse(rawInput); } catch (_) { hookInput = {}; }

  const stateContent = fs.readFileSync(RALPH_STATE_FILE, 'utf8');
  const fm = parseFrontmatter(stateContent);

  const iteration = fm.iteration;
  const maxIterations = fm.max_iterations;
  const completionPromise = fm.completion_promise || '';

  // Validate numeric fields before arithmetic operations
  if (!/^\d+$/.test(iteration)) {
    failAndCleanup(
      '\u26a0\ufe0f  Ralph loop: State file corrupted\n' +
      '   File: ' + RALPH_STATE_FILE + '\n' +
      "   Problem: 'iteration' field is not a valid number (got: '" + iteration + "')\n\n" +
      '   This usually means the state file was manually edited or corrupted.\n' +
      '   Ralph loop is stopping. Run /ralph-loop again to start fresh.'
    );
    return;
  }

  if (!/^\d+$/.test(maxIterations)) {
    failAndCleanup(
      '\u26a0\ufe0f  Ralph loop: State file corrupted\n' +
      '   File: ' + RALPH_STATE_FILE + '\n' +
      "   Problem: 'max_iterations' field is not a valid number (got: '" + maxIterations + "')\n\n" +
      '   This usually means the state file was manually edited or corrupted.\n' +
      '   Ralph loop is stopping. Run /ralph-loop again to start fresh.'
    );
    return;
  }

  const iterNum = parseInt(iteration, 10);
  const maxIterNum = parseInt(maxIterations, 10);

  // Check if max iterations reached
  if (maxIterNum > 0 && iterNum >= maxIterNum) {
    process.stdout.write('\ud83d\uded1 Ralph loop: Max iterations (' + maxIterNum + ') reached.\n');
    removeStateFile();
    process.exit(0);
  }

  // Get transcript path from hook input
  const transcriptPath = hookInput.transcript_path;
  if (!transcriptPath || !fs.existsSync(transcriptPath)) {
    failAndCleanup(
      '\u26a0\ufe0f  Ralph loop: Transcript file not found\n' +
      '   Expected: ' + transcriptPath + '\n' +
      '   This is unusual and may indicate a Claude Code internal issue.\n' +
      '   Ralph loop is stopping.'
    );
    return;
  }

  // Read last assistant message from transcript
  const lastOutput = getLastAssistantOutput(transcriptPath);

  if (lastOutput === null) {
    failAndCleanup(
      '\u26a0\ufe0f  Ralph loop: No assistant messages found or failed to parse\n' +
      '   Transcript: ' + transcriptPath + '\n' +
      '   This is unusual and may indicate a transcript format issue\n' +
      '   Ralph loop is stopping.'
    );
    return;
  }

  if (!lastOutput) {
    failAndCleanup(
      '\u26a0\ufe0f  Ralph loop: Assistant message contained no text content\n' +
      '   Ralph loop is stopping.'
    );
    return;
  }

  // Check for completion promise (only if set)
  if (completionPromise && completionPromise !== 'null') {
    const promiseText = extractPromiseText(lastOutput);
    if (promiseText && promiseText === completionPromise) {
      process.stdout.write('\u2705 Ralph loop: Detected <promise>' + completionPromise + '</promise>\n');
      removeStateFile();
      process.exit(0);
    }
  }

  // Not complete - continue loop with SAME PROMPT
  const nextIteration = iterNum + 1;

  // Extract prompt (everything after the closing ---)
  const promptText = extractPrompt(stateContent);

  if (!promptText) {
    failAndCleanup(
      '\u26a0\ufe0f  Ralph loop: State file corrupted or incomplete\n' +
      '   File: ' + RALPH_STATE_FILE + '\n' +
      '   Problem: No prompt text found\n\n' +
      '   This usually means:\n' +
      '     \u2022 State file was manually edited\n' +
      '     \u2022 File was corrupted during writing\n\n' +
      '   Ralph loop is stopping. Run /ralph-loop again to start fresh.'
    );
    return;
  }

  // Update iteration in frontmatter (atomic write via temp file)
  const updatedContent = stateContent.replace(
    /^iteration:\s*.*/m,
    'iteration: ' + nextIteration
  );
  const tempFile = RALPH_STATE_FILE + '.tmp.' + process.pid;
  fs.writeFileSync(tempFile, updatedContent, 'utf8');
  fs.renameSync(tempFile, RALPH_STATE_FILE);

  // Build system message with iteration count and completion promise info
  let systemMsg;
  if (completionPromise && completionPromise !== 'null') {
    systemMsg = '\ud83d\udd04 Ralph iteration ' + nextIteration +
      ' | To stop: output <promise>' + completionPromise +
      '</promise> (ONLY when statement is TRUE - do not lie to exit!)';
  } else {
    systemMsg = '\ud83d\udd04 Ralph iteration ' + nextIteration +
      ' | No completion promise set - loop runs infinitely';
  }

  // Output JSON to block the stop and feed prompt back
  const output = JSON.stringify({
    decision: 'block',
    reason: promptText,
    systemMessage: systemMsg
  });

  process.stdout.write(output);
  process.exit(0);
}

main().catch(function() {
  // On any unhandled error, allow exit (don't trap user)
  process.exit(0);
});
