---
description: Get an airport transfer quote from Airport Pickups London
argument-hint: <origin> to <destination> [date]
allowed-tools: [Read, Bash]
---

# Airport Transfer Quote

Get a fixed-price quote for a UK airport or cruise port transfer.

## Arguments

The user provided: $ARGUMENTS

## Instructions

1. Parse the origin, destination, and optional date from the arguments
2. Call the `london_airport_transfer_quote` MCP tool with the parsed values
3. Present all vehicle options with prices
4. Ask if the user would like to book

## Examples

```
/apl-quote Heathrow to Oxford
/apl-quote Gatwick to Brighton 15 April 2026
/apl-quote Southampton cruise port to London
```
