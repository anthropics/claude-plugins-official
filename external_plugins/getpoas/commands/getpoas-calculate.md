# GetPoas Calculator

Calculate Profit on Ad Spend (POAS) for campaigns, products, or time periods.

## Usage

```
/getpoas-calculate [--campaign id] [--product sku] [--period 7d|30d]
```

## What This Does

1. Fetches ad spend and revenue data
2. Calculates true profit after COGS, fees, and shipping
3. Shows POAS (Profit/Spend) instead of just ROAS (Revenue/Spend)
4. Identifies profitable vs unprofitable campaigns

## Example Output

```
POAS Analysis (Last 30 Days)

Campaign: Summer Sale - Meta Retargeting

Revenue Metrics
├── Gross Revenue: $45,230
├── Ad Spend: $8,500
└── ROAS: 5.32x ✅

Profit Metrics
├── COGS: $18,092 (40%)
├── Shipping: $2,261 (5%)
├── Payment Fees: $1,357 (3%)
├── Net Profit: $15,020
└── POAS: 1.77x ✅

Verdict: PROFITABLE
Each $1 in ad spend generates $1.77 in profit

Comparison:
─────────────────────────────────────────
Campaign              ROAS    POAS    Status
Summer Sale - Meta    5.32x   1.77x   ✅ Profitable
Brand Search          4.10x   1.45x   ✅ Profitable
Competitor KWs        2.80x   0.82x   ⚠️ Break-even
Cold Prospecting      1.90x   0.31x   ❌ Unprofitable
```
