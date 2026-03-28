---
name: apl-book
description: "This skill should be used when the user wants to book an airport transfer, reserve a taxi, make a transfer booking, or confirms they want to proceed with a quote from Airport Pickups London. Triggers on phrases like 'yes book it', 'I want to book', 'reserve a transfer', 'confirm the booking'."
version: 1.0.0
---

# Airport Transfer Booking

Create confirmed transfer bookings with Airport Pickups London.

## When to Use

Use the `book_london_airport_transfer` MCP tool when the user confirms they want to book a transfer. **Always get a quote first** using `london_airport_transfer_quote`.

## Required Information

Collect ALL of these before calling the booking tool:

1. **Origin & destination** (from the quote)
2. **Transfer date** (YYYY-MM-DD)
3. **Transfer time** (HH:MM — for airport pickups: landing time + clearance)
4. **Passenger name** (full name)
5. **Phone number** (with country code, e.g. +447123456789)
6. **Passenger email** (for confirmation)
7. **Car type** (let the user choose from the quote options)
8. **Passengers & suitcases count**
9. **Flight number** (for airport pickups only — use `validate_flight` to verify)
10. **Special requests** (child seat, wheelchair, extra luggage — always ask)

## Booking Flow

1. Get a quote first — never guess prices
2. User confirms they want to book
3. Ask which car type they want — never choose for them
4. For airport pickups: get flight number, call `validate_flight`
5. For airport pickups: recommend clearance time (domestic 15min, European 45min, international 60min after landing)
6. Collect name, phone, email
7. Ask about special requests
8. Inform about payment: cash to driver or online via manage booking link
9. Read back ALL details and get confirmation
10. Call `book_london_airport_transfer`
11. Share booking reference and manage booking URL

## After Booking

Present:
- **Booking reference** (e.g. APL-CJ5KDJ)
- **Manage booking URL** — customer can view, pay online, track driver, amend, cancel
- **Meeting point instructions** with terminal name
- **24/7 support**: 0208 688 7744

## Important Rules

- NEVER book without user confirmation
- NEVER choose a car type for the user
- NEVER use landing time as pickup time — add clearance time
- NEVER call book again to amend — direct to manage booking link or phone 0208 688 7744
