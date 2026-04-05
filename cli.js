#!/usr/bin/env node
/**
 * COE Pricing Intelligence — CLI Runner
 * Usage:
 *   node cli.js master-scan --vin JTMAU7BJ5R4049000 --make Toyota --model "Land Cruiser" --year 2024
 *   node cli.js vin-scan --vin JTMAU7BJ5R4049000
 *   node cli.js health
 *   node cli.js list
 */

const { dispatch, healthCheck, manifest } = require('./plugins/coe-pricing/index');

// ── Argument Parser ───────────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = argv.slice(2);
  const command = args[0];
  const params = {};

  for (let i = 1; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const val = args[i + 1] && !args[i + 1].startsWith('--') ? args[++i] : true;
      // Type coerce
      if (!isNaN(val) && val !== true) {
        params[key] = Number(val);
      } else {
        params[key] = val;
      }
    }
  }
  return { command, params };
}

// ── Output Formatters ─────────────────────────────────────────────────────────
function printPrompt(result) {
  const divider = '═'.repeat(70);

  console.log(`\n${divider}`);
  console.log(`  COE PRICING INTELLIGENCE — ${result.command.toUpperCase()}`);
  if (result.vehicle) console.log(`  Vehicle : ${result.vehicle}`);
  if (result.vin)     console.log(`  VIN     : ${result.vin}`);
  console.log(`  Time    : ${result.timestamp}`);
  console.log(`  Elapsed : ${result.elapsed_ms}ms`);
  console.log(`${divider}\n`);

  const inner = result.result;

  if (inner?.prompt) {
    console.log('── GENERATED PROMPT ──────────────────────────────────────────────────');
    console.log(inner.prompt);
  }

  if (inner?.masterPrompt) {
    console.log('── MASTER PROMPT ─────────────────────────────────────────────────────');
    console.log(inner.masterPrompt);
  }

  if (inner?.handoffBlock) {
    console.log('── COPILOT HANDOFF BLOCK ─────────────────────────────────────────────');
    console.log(inner.handoffBlock);
  }

  if (inner?.instructions?.length) {
    console.log('\n── INSTRUCTIONS ──────────────────────────────────────────────────────');
    inner.instructions.forEach(i => console.log(`  ${i}`));
  }

  if (inner?.note) {
    console.log(`\n  NOTE: ${inner.note}`);
  }

  console.log(`\n${divider}\n`);
}

function printHelp() {
  console.log(`
COE Pricing Intelligence CLI
Al-Futtaim Automotive | UC Pricing COE
${'─'.repeat(50)}

USAGE
  node cli.js <command> [options]

COMMANDS
  health                    Check service health
  list                      List all available commands
`);
  manifest.commands.forEach(cmd => {
    const required = cmd.parameters.filter(p => p.required).map(p => `--${p.name}`).join(' ');
    console.log(`  ${cmd.name.padEnd(22)} ${required}`);
    console.log(`    ${cmd.description}\n`);
  });

  console.log(`
EXAMPLES
  node cli.js master-scan --vin JTMAU7BJ5R4049000 --make Toyota --model "Land Cruiser" --year 2024 --mileage 15000
  node cli.js vin-scan --vin JTMAU7BJ5R4049000
  node cli.js price-engine --vin ABC123456789XXXXX --make Audi --model Q3 --year 2024
  node cli.js gcc-verify --vin JTMAU7BJ5R4049000 --make Toyota --model "Land Cruiser" --year 2024
  node cli.js copilot-handoff --vin JTMAU7BJ5R4049000

OUTPUT
  The generated prompt is printed to stdout.
  Copy it and paste into Claude (claude.ai or Claude Code).
  For master-scan, the Copilot Handoff Block is printed at the end.
`);
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  const { command, params } = parseArgs(process.argv);

  if (!command || command === '--help' || command === '-h') {
    printHelp();
    process.exit(0);
  }

  if (command === 'health') {
    console.log('\nChecking COE service health...\n');
    const checks = await healthCheck();
    Object.entries(checks).forEach(([service, status]) => {
      const icon = status === 'OK' ? '✓' : status === 'OFFLINE' ? '✗' : '⚠';
      console.log(`  ${icon}  ${service.padEnd(25)} ${status}`);
    });
    console.log('');
    process.exit(0);
  }

  if (command === 'list') {
    console.log('\nAvailable COE Commands:\n');
    manifest.commands.forEach(cmd => {
      console.log(`  /${cmd.name.padEnd(22)} ${cmd.displayName}`);
    });
    console.log('');
    process.exit(0);
  }

  try {
    const result = await dispatch(command, params);
    printPrompt(result);
  } catch (err) {
    console.error(`\n✗ Error: ${err.message}\n`);
    console.error('Run `node cli.js --help` for usage.\n');
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Unexpected error:', err);
  process.exit(1);
});
