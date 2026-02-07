# CallTracker Calls

View recent calls and call logs with attribution data.

## Usage

```
/calltracker-calls [--period 24h|7d|30d] [--status answered|missed|voicemail]
```

## What This Does

1. Lists recent calls with caller info
2. Shows attribution (source, campaign, keyword)
3. Displays call duration and outcome
4. Links to recordings if available

## Example Output

```
Recent Calls (Last 24 Hours)

Total: 47 calls | Answered: 38 | Missed: 6 | Voicemail: 3

Time        Number          Duration  Source            Status
────────────────────────────────────────────────────────────────
2:34 PM     +1 (555) 123    4:23      Google Ads        ✅ Answered
2:15 PM     +1 (555) 456    -         Organic           ❌ Missed
1:48 PM     +1 (555) 789    2:45      Meta Ads          ✅ Answered
1:22 PM     +1 (555) 012    1:12      Direct            📞 Voicemail
12:55 PM    +1 (555) 345    8:32      Google Ads        ✅ Answered

Top Sources:
├── Google Ads: 22 calls (47%)
├── Meta Ads: 12 calls (26%)
├── Organic: 8 calls (17%)
└── Direct: 5 calls (10%)

Call Quality:
├── Answer Rate: 81%
├── Avg Duration: 4:12
└── Conversion Rate: 23%
```
