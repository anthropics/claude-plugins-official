// src/index.js
// ─────────────────────────────────────────────────────────────────
// Entry point — demonstrates all Claude integration modes
// Run: npm start
// ─────────────────────────────────────────────────────────────────

import 'dotenv/config';
import { ask, chat, appraise, stream } from './claude.js';

// ─── Example 1: Simple ask ────────────────────────────────────────
async function exampleAsk() {
  console.log('═'.repeat(60));
  console.log('EXAMPLE 1 — Simple Ask');
  console.log('═'.repeat(60));

  const reply = await ask(
    'What is a fair trade-in value range for a 2020 Toyota Camry 2.5L ' +
    'GCC spec, white, 85,000 km, no accidents, full service history in Dubai?'
  );

  console.log(reply);
}


// ─── Example 2: Structured appraisal (JSON output) ───────────────
async function exampleAppraise() {
  console.log('═'.repeat(60));
  console.log('EXAMPLE 2 — Structured Appraisal');
  console.log('═'.repeat(60));

  const vehicle = {
    make:           'Toyota',
    model:          'Camry',
    variant:        '2.5L SE',
    year:           2020,
    mileage_km:     85000,
    spec:           'GCC',
    color:          'White',
    accident_history: false,
    service_history:  'Full dealer',
    outstanding_finance: false,
    condition:       'Good',
    tinting:         true,
    location:        'Dubai, UAE',
  };

  const result = await appraise(vehicle);

  console.log('\nAppraisal Result:');
  console.log(JSON.stringify(result, null, 2));
}


// ─── Example 3: Multi-turn chat ───────────────────────────────────
async function exampleChat() {
  console.log('═'.repeat(60));
  console.log('EXAMPLE 3 — Multi-turn Chat');
  console.log('═'.repeat(60));

  let { reply, history } = await chat([
    { role: 'user', content: 'I have a 2019 Nissan Patrol Platinum, 120,000 km, GCC, silver. What should I bid?' }
  ]);
  console.log('Turn 1:', reply);

  // Follow-up with more context
  const turn2 = await chat([
    ...history,
    { role: 'user', content: 'It has one minor accident on record — front bumper replacement only. Does that change your recommendation?' }
  ]);
  console.log('\nTurn 2:', turn2.reply);
}


// ─── Example 4: Streaming output ─────────────────────────────────
async function exampleStream() {
  console.log('═'.repeat(60));
  console.log('EXAMPLE 4 — Streaming Output');
  console.log('═'.repeat(60));

  await stream(
    'Give me a quick depreciation overview for the Toyota Land Cruiser 300 ' +
    'series in the UAE market for 2023-2024 model years.'
  );
}


// ─── Run selected example ─────────────────────────────────────────
async function main() {
  const mode = process.argv[2] || 'appraise';

  try {
    switch (mode) {
      case 'ask':      await exampleAsk();      break;
      case 'appraise': await exampleAppraise();  break;
      case 'chat':     await exampleChat();      break;
      case 'stream':   await exampleStream();    break;
      default:
        console.log('Usage: node src/index.js [ask|appraise|chat|stream]');
    }
  } catch (err) {
    if (err.status === 401) {
      console.error('❌ Invalid API key — check your .env file');
    } else if (err.status === 429) {
      console.error('❌ Rate limited — wait a moment and retry');
    } else {
      console.error('❌ Error:', err.message);
    }
    process.exit(1);
  }
}

main();
