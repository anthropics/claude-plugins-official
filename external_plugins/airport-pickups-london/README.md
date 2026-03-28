# Airport Pickups London — Claude Code Plugin

Book UK airport and cruise port transfers directly from Claude Code.

## What It Does

- **Get instant quotes** — fixed prices for any UK route
- **Validate flights** — auto-detect terminal, airline, arrival time
- **Create real bookings** — confirmed reservations with driver tracking

## Supported Locations

**Airports**: Heathrow (T2-T5), Gatwick (N&S), Stansted, Luton, London City, Edinburgh
**Cruise Ports**: Southampton, Dover, Portsmouth, Harwich, Tilbury
**Addresses**: Any UK postcode, address, hotel, or city

## Installation

```bash
/plugin install airport-pickups-london@claude-plugins-official
```

## Usage

### Slash Command

```
/apl-quote Heathrow to Oxford
/apl-quote Gatwick to Brighton 15 April 2026
```

### Natural Language

Just ask Claude:
- "How much is a taxi from Heathrow to central London?"
- "Get me a quote from Gatwick to Brighton for 4 passengers"
- "Book a transfer from Stansted to Cambridge"

## MCP Server

This plugin connects to the Airport Pickups London MCP server:
- **Endpoint**: `https://mcp.airport-pickups-london.com/mcp`
- **Auth**: OAuth 2.1 (auto-discovery)
- **Server Card**: `https://www.airport-pickups-london.com/.well-known/mcp.json`

### Available Tools

| Tool | Description |
|------|-------------|
| `london_airport_transfer_quote` | Get fixed-price quotes for any UK route |
| `book_london_airport_transfer` | Create confirmed bookings |
| `validate_flight` | Verify flight numbers, get terminal info |
| `lookup_booking` | Check booking status |
| `amend_booking` | Modify booking details |
| `cancel_booking` | Cancel a booking |
| `track_driver` | Live GPS driver tracking |

## Pricing

- All prices in GBP (£), **per vehicle** (not per person)
- Fixed prices — no surge, no hidden charges
- Includes meet & greet, flight monitoring, waiting time, parking
- Free cancellation 12+ hours before pickup

## Vehicle Types

| Vehicle | Passengers | Bags | From |
|---------|-----------|------|------|
| Saloon | Up to 3 | 3 | ~£33 |
| People Carrier | Up to 5 | 5 | ~£45 |
| 8 Seater | Up to 8 | 8 | ~£55 |
| Executive Saloon | Up to 3 | 3 | ~£65 |
| Executive MPV | Up to 7 | 7 | ~£85 |
| Executive 8 Seater | Up to 8 | 8 | ~£95 |

## Support

- 24/7 Phone: +44 208 688 7744
- WhatsApp: +44 7538 989360
- Email: info@aplcars.com
- Website: https://www.airport-pickups-london.com

## License

MIT-0 — Free to use, modify, and redistribute. No attribution required.
