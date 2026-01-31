# GetChannel Campaign Manager

List and manage ad campaigns across Google, Meta, TikTok, and LinkedIn.

## Usage

```
/getchannel-campaigns [action] [--platform google|meta|tiktok|linkedin]
```

## Actions

- `list` - List all campaigns (default)
- `status [id]` - Get campaign status
- `pause [id]` - Pause a campaign
- `resume [id]` - Resume a paused campaign
- `create` - Create a new campaign (interactive)

## Example Output

```
Active Campaigns (12)

Platform    Campaign                   Status    Spend     ROAS
──────────────────────────────────────────────────────────────
Google      Brand - Search             Active    $1,234    4.2x
Google      Competitor Keywords        Active    $567      2.8x
Meta        Retargeting - Cart         Active    $890      5.1x
Meta        Lookalike - Purchasers     Paused    $0        -
TikTok      Product Launch - Gen Z     Active    $445      3.2x
LinkedIn    B2B Decision Makers        Active    $1,100    2.1x

Total Daily Spend: $4,236
Average ROAS: 3.5x
```

---

When the user runs this command:

1. Fetch campaigns from all connected platforms via GetChannel API
2. Display unified view with status, spend, and performance
3. Allow filtering by platform or status
4. Support pause/resume actions with confirmation
