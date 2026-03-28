---
name: apl-validate-flight
description: "This skill should be used when the user provides a flight number during a transfer booking, or asks to check/verify a flight. Triggers on phrases like 'my flight is BA2534', 'check flight EK007', 'what terminal does my flight arrive at'."
version: 1.0.0
---

# Flight Validation

Verify flight numbers and get terminal, airline, and arrival details.

## When to Use

Use the `validate_flight` MCP tool when:
- User provides a flight number during the booking flow
- User asks to check or verify a flight
- You need to determine which terminal a flight arrives at

## How to Use

Call `validate_flight` with:
- **flight_number**: e.g. "BA2534", "EK007", "FR1234"
- **date**: Flight date in YYYY-MM-DD format

## What It Returns

- Airline name
- Arrival airport
- Arrival terminal
- Scheduled arrival time

## After Validation

- If times match user's stated time: "I've verified your flight — [number] ([airline]) arrives at [terminal] at [time]. All looks good!"
- If times differ: Tell the user and ask which time to use
- If validation fails: "I wasn't able to verify that flight, but no problem — I'll use the details you've given me."
- NEVER ask the user for the terminal — this tool provides it
