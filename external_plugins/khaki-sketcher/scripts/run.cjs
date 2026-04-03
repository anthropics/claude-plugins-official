#!/usr/bin/env node
// Hook runner: loads and executes ESM hook scripts from CJS context
const { pathToFileURL } = require('node:url');
const path = require('node:path');

const scriptPath = process.argv[2];
if (!scriptPath) {
  process.exit(0);
}

const absPath = path.resolve(scriptPath);

import(pathToFileURL(absPath).href)
  .then((mod) => {
    if (typeof mod.default === 'function') {
      return mod.default();
    }
  })
  .catch((err) => {
    console.error(`[KSK Hook Error] ${err.message}`);
    process.exit(0); // Don't block Claude Code on hook failure
  });
