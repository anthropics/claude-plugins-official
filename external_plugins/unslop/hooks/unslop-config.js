#!/usr/bin/env node
// unslop — shared configuration resolver
//
// Resolution order for default mode:
//   1. UNSLOP_DEFAULT_MODE environment variable
//   2. Config file defaultMode field:
//      - $XDG_CONFIG_HOME/unslop/config.json (any platform, if set)
//      - ~/.config/unslop/config.json (macOS / Linux fallback)
//      - %APPDATA%\unslop\config.json (Windows fallback)
//   3. 'balanced'

const fs = require('fs');
const path = require('path');
const os = require('os');

const VALID_MODES = [
  'off', 'subtle', 'balanced', 'full',
  'voice-match', 'anti-detector',
  'commit', 'review'
];

function getConfigDir() {
  if (process.env.XDG_CONFIG_HOME) {
    return path.join(process.env.XDG_CONFIG_HOME, 'unslop');
  }
  if (process.platform === 'win32') {
    return path.join(
      process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'),
      'unslop'
    );
  }
  return path.join(os.homedir(), '.config', 'unslop');
}

function getConfigPath() {
  return path.join(getConfigDir(), 'config.json');
}

function getDefaultMode() {
  const envMode = process.env.UNSLOP_DEFAULT_MODE;
  if (envMode && VALID_MODES.includes(envMode.toLowerCase())) {
    return envMode.toLowerCase();
  }

  try {
    const configPath = getConfigPath();
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (config.defaultMode && VALID_MODES.includes(config.defaultMode.toLowerCase())) {
      return config.defaultMode.toLowerCase();
    }
  } catch (e) {
    // Config file doesn't exist or is invalid
  }

  return 'balanced';
}

// Symlink-safe flag file write.
// Refuses symlinks at the target file and at the immediate parent directory,
// uses O_NOFOLLOW where available, writes atomically via temp + rename with
// 0600 permissions. Protects against local attackers replacing the predictable
// flag path with a symlink to clobber other files.
function safeWriteFlag(flagPath, content) {
  try {
    const flagDir = path.dirname(flagPath);
    fs.mkdirSync(flagDir, { recursive: true });

    try {
      if (fs.lstatSync(flagDir).isSymbolicLink()) return;
    } catch (e) {
      return;
    }

    try {
      if (fs.lstatSync(flagPath).isSymbolicLink()) return;
    } catch (e) {
      if (e.code !== 'ENOENT') return;
    }

    const tempPath = path.join(flagDir, `.unslop-active.${process.pid}.${Date.now()}`);
    const O_NOFOLLOW = typeof fs.constants.O_NOFOLLOW === 'number' ? fs.constants.O_NOFOLLOW : 0;
    const flags = fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | O_NOFOLLOW;
    let fd;
    try {
      fd = fs.openSync(tempPath, flags, 0o600);
      fs.writeSync(fd, String(content));
      try { fs.fchmodSync(fd, 0o600); } catch (e) { /* best-effort on Windows */ }
    } finally {
      if (fd !== undefined) fs.closeSync(fd);
    }
    fs.renameSync(tempPath, flagPath);
  } catch (e) {
    // Silent fail — flag is best-effort
  }
}

// Symlink-safe, size-capped, whitelist-validated flag file read.
// Returns null on any anomaly — never inject untrusted bytes into model context.
const MAX_FLAG_BYTES = 64;

function readFlag(flagPath) {
  try {
    let st;
    try {
      st = fs.lstatSync(flagPath);
    } catch (e) {
      return null;
    }
    if (st.isSymbolicLink() || !st.isFile()) return null;
    if (st.size > MAX_FLAG_BYTES) return null;

    const O_NOFOLLOW = typeof fs.constants.O_NOFOLLOW === 'number' ? fs.constants.O_NOFOLLOW : 0;
    const flags = fs.constants.O_RDONLY | O_NOFOLLOW;
    let fd;
    let out;
    try {
      fd = fs.openSync(flagPath, flags);
      const buf = Buffer.alloc(MAX_FLAG_BYTES);
      const n = fs.readSync(fd, buf, 0, MAX_FLAG_BYTES, 0);
      out = buf.slice(0, n).toString('utf8');
    } finally {
      if (fd !== undefined) fs.closeSync(fd);
    }

    const raw = out.trim().toLowerCase();
    if (!VALID_MODES.includes(raw)) return null;
    return raw;
  } catch (e) {
    return null;
  }
}

function getFlagPath() {
  const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  return path.join(claudeDir, '.unslop-active');
}

// Persona-drift reinforcement counter. Tracks how many user turns have
// passed in this session while unslop has been active. RMTBench measures
// >30% persona degradation after 8–12 turns; HorizonBench (arXiv
// 2604.17283, Apr 2026) benchmarks preference evolution over time. We use
// the counter to re-emit a shorter reinforcement banner at predetermined
// drift-risk checkpoints rather than every turn (which would get tuned out).
function getTurnCounterPath() {
  const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  return path.join(claudeDir, '.unslop-turn-count');
}

// Read the counter. Same symlink-safe / size-capped discipline as readFlag.
function readTurnCount(counterPath) {
  try {
    let st;
    try {
      st = fs.lstatSync(counterPath);
    } catch (e) {
      return 0;
    }
    if (st.isSymbolicLink() || !st.isFile()) return 0;
    if (st.size > 32) return 0;
    const O_NOFOLLOW = typeof fs.constants.O_NOFOLLOW === 'number' ? fs.constants.O_NOFOLLOW : 0;
    const flags = fs.constants.O_RDONLY | O_NOFOLLOW;
    let fd, raw;
    try {
      fd = fs.openSync(counterPath, flags);
      const buf = Buffer.alloc(32);
      const n = fs.readSync(fd, buf, 0, 32, 0);
      raw = buf.slice(0, n).toString('utf8').trim();
    } finally {
      if (fd !== undefined) fs.closeSync(fd);
    }
    const n = parseInt(raw, 10);
    if (!Number.isFinite(n) || n < 0 || n > 1_000_000) return 0;
    return n;
  } catch (e) {
    return 0;
  }
}

// Symlink-safe atomic-rename write of the counter. Uses the same pattern as
// safeWriteFlag to resist local-attacker symlink games.
function writeTurnCount(counterPath, n) {
  try {
    const dir = path.dirname(counterPath);
    fs.mkdirSync(dir, { recursive: true });
    try {
      if (fs.lstatSync(dir).isSymbolicLink()) return;
    } catch (e) { return; }
    try {
      if (fs.lstatSync(counterPath).isSymbolicLink()) return;
    } catch (e) {
      if (e.code !== 'ENOENT') return;
    }
    const tempPath = path.join(dir, `.unslop-turn-count.${process.pid}.${Date.now()}`);
    const O_NOFOLLOW = typeof fs.constants.O_NOFOLLOW === 'number' ? fs.constants.O_NOFOLLOW : 0;
    const flags = fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | O_NOFOLLOW;
    let fd;
    try {
      fd = fs.openSync(tempPath, flags, 0o600);
      fs.writeSync(fd, String(n));
      try { fs.fchmodSync(fd, 0o600); } catch (e) {}
    } finally {
      if (fd !== undefined) fs.closeSync(fd);
    }
    fs.renameSync(tempPath, counterPath);
  } catch (e) {
    // Silent fail — drift counter is best-effort
  }
}

// Reset the counter (on session start / mode change). Safe no-op if missing.
function resetTurnCount(counterPath) {
  try { fs.unlinkSync(counterPath); } catch (e) { /* noop */ }
}

module.exports = {
  getDefaultMode, getConfigDir, getConfigPath, VALID_MODES,
  safeWriteFlag, readFlag, getFlagPath,
  getTurnCounterPath, readTurnCount, writeTurnCount, resetTurnCount
};
