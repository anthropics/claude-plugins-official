// src/claude.js
// ─────────────────────────────────────────────────────────────────
// Core Claude API client — reusable wrapper for all agent workflows
// ─────────────────────────────────────────────────────────────────

import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const MODEL   = process.env.CLAUDE_MODEL      || 'claude-sonnet-4-6';
const MAX_TOK = parseInt(process.env.CLAUDE_MAX_TOKENS) || 2048;

// ─── System prompt shared across all pricing calls ───────────────
const SYSTEM_PROMPT = `You are a senior Used Cars Pricing Appraiser for Al-Futtaim Automotive's 
COE UC Pricing team in Dubai, UAE. Your role is to evaluate vehicle enquiries and trade-in 
opportunities and return structured pricing recommendations.

When analysing a vehicle you always consider:
- UAE market segment and GCC vs non-GCC specification
- Current mileage vs expected depreciation band
- Accident history and structural damage risk
- Color desirability in the UAE market (white/silver preferred)
- Comparable retail listings (Dubizzle, YallaMotor, PriceMyCar)
- Recent auction results (Autorola, SAS Manheim)
- Age-based depreciation curves specific to the UAE
- Outstanding finance, tinting, service history completeness

You output structured JSON recommendations with: estimatedValue (AED), 
recommendedBid (AED), confidence (High/Medium/Low), decision (Acquire/Negotiate/Decline), 
and reasoning (string).`;


// ─── 1. Single message — simplest call ───────────────────────────
export async function ask(userMessage) {
  const response = await client.messages.create({
    model:      MODEL,
    max_tokens: MAX_TOK,
    system:     SYSTEM_PROMPT,
    messages: [
      { role: 'user', content: userMessage }
    ],
  });

  return response.content[0].text;
}


// ─── 2. Multi-turn conversation — maintains history ───────────────
export async function chat(messages) {
  // messages = [{ role: 'user'|'assistant', content: '...' }, ...]
  const response = await client.messages.create({
    model:      MODEL,
    max_tokens: MAX_TOK,
    system:     SYSTEM_PROMPT,
    messages,
  });

  const reply = response.content[0].text;

  // Return updated history + reply for chaining
  return {
    reply,
    history: [...messages, { role: 'assistant', content: reply }],
  };
}


// ─── 3. Structured JSON output — for programmatic use ─────────────
export async function appraise(vehicleData) {
  const prompt = `Appraise the following vehicle and return ONLY valid JSON. 
No explanation, no markdown — raw JSON only.

Vehicle details:
${JSON.stringify(vehicleData, null, 2)}

Required JSON structure:
{
  "estimatedMarketValue": <number in AED>,
  "recommendedBidPrice":  <number in AED>,
  "maximumBidPrice":      <number in AED>,
  "confidence":           "High" | "Medium" | "Low",
  "decision":             "Acquire" | "Negotiate" | "Decline",
  "depreciationNotes":    "<string>",
  "marketComparables":    "<string>",
  "riskFlags":            ["<string>"],
  "reasoning":            "<string>"
}`;

  const raw = await ask(prompt);

  // Strip any accidental markdown fences
  const clean = raw.replace(/```json|```/g, '').trim();
  return JSON.parse(clean);
}


// ─── 4. Streaming — for real-time output in the terminal ──────────
export async function stream(userMessage) {
  process.stdout.write('\n[Claude]: ');

  const response = await client.messages.stream({
    model:      MODEL,
    max_tokens: MAX_TOK,
    system:     SYSTEM_PROMPT,
    messages: [
      { role: 'user', content: userMessage }
    ],
  });

  for await (const chunk of response) {
    if (
      chunk.type === 'content_block_delta' &&
      chunk.delta.type === 'text_delta'
    ) {
      process.stdout.write(chunk.delta.text);
    }
  }

  process.stdout.write('\n\n');
  return await response.finalMessage();
}


// ─── 5. Usage info — token tracking ──────────────────────────────
export function logUsage(response) {
  const u = response.usage;
  console.log(`\n[Tokens] Input: ${u.input_tokens} | Output: ${u.output_tokens} | Total: ${u.input_tokens + u.output_tokens}`);
}

export { client, MODEL };
