# GetFeeder Sync

Sync product feeds to Google Shopping, Meta Catalog, TikTok Shop, and more.

## Usage

```
/getfeeder-sync [--feed id] [--platform google|meta|tiktok] [--force]
```

## What This Does

1. Triggers a feed sync to specified platforms
2. Validates products before sync
3. Reports sync status and any errors
4. Shows product approval status

## Example Output

```
Feed Sync: Main Product Catalog

Syncing to: Google Merchant Center, Meta Catalog, TikTok Shop

Progress:
├── Google: ✅ Complete (1,234 products)
├── Meta: ✅ Complete (1,234 products)
└── TikTok: 🔄 In Progress (856/1,234)

Product Status:
├── Approved: 1,198 (97%)
├── Pending: 24 (2%)
├── Disapproved: 12 (1%)
└── Warnings: 45

Issues to Fix:
1. Missing GTIN: 8 products
2. Image too small: 4 products
3. Price mismatch: 3 products

Run /getfeeder-validate for detailed error report
```
