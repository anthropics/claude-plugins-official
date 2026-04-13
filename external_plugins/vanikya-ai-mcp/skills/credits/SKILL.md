---
name: credits
description: Use this skill when the user asks about their Vanikya credit balance, available credit packages or pricing, how to buy more credits, what subscription plan they are on, ran out of credits, or why a generation failed due to insufficient credits.
version: 1.0.0
---

# Vanikya Credits

Manage the user's Vanikya credits — check balance, browse packages, and purchase.

## Available Tools

| Tool | Purpose |
|---|---|
| `credits_get_balance` | Get current credit balance and active subscription plan |
| `credits_list_packages` | List available one-time credit packages with prices |
| `credits_buy` | Generate a payment link for a credit package |

## Check Balance

```
credits_get_balance()
```

Returns:
- `credits` — current balance
- `plan.name` — active subscription plan name
- `plan.status` — subscription status (active, cancelled, etc.)
- `plan.interval` — billing interval (monthly, yearly)

## Browse Packages

```
credits_list_packages()
```

Returns a list of one-time credit packages, each with:
- `product_id` — use this to generate a purchase link
- `name` — package name
- `credits` — number of credits included

> **Note:** Pricing is not returned by this tool. Direct the user to [vanikya.com](https://vanikya.com) to see pricing details before purchasing.

## Buy Credits

This generates one-time credit top-up links only — for subscription changes, direct the user to the Vanikya dashboard.

1. Call `credits_list_packages()` to get available packages.
2. Show the user the options.
3. Once the user picks one, generate a payment link:
   ```
   credits_buy({ product_id: "<product_id>" })
   ```
4. Share the returned `url` with the user — they open it in their browser to complete payment.

## Rules

- Always show the user their current balance before presenting purchase options.
- The `credits_buy` tool generates one-time purchase links only — for subscription management, direct the user to the Vanikya dashboard.
- After payment, the user must wait a moment for credits to reflect — they can call `credits_get_balance` again to confirm.
