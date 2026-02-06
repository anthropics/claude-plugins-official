# Winning Strategy Selection Logic

## Decision Tree

```
Input: {client_id, target_industry, target_role, channel_preference, budget}
                          │
                          ▼
              ┌───────────────────────┐
              │ Query winning_strategies│
              │ for exact match        │
              └──────────┬────────────┘
                         │
                    Found match?
                   /           \
                 Yes             No
                  │               │
                  ▼               ▼
          ┌──────────┐   ┌──────────────┐
          │ Check     │   │ Query by     │
          │ confidence│   │ industry only│
          └────┬─────┘   └──────┬───────┘
               │                │
          High/Medium?     Found match?
          /        \       /          \
        Yes         No   Yes           No
         │           │    │             │
         ▼           ▼    ▼             ▼
    ┌────────┐  ┌────────┐ ┌────────┐ ┌──────────┐
    │Use with│  │Use with│ │Use with│ │Use global│
    │80/20   │  │60/40   │ │60/40   │ │benchmarks│
    │split   │  │split   │ │split   │ │100% test │
    └────────┘  └────────┘ └────────┘ └──────────┘
```

## Strategy Scoring Algorithm

For each potential strategy combination, calculate a weighted score:

```
strategy_score = (
    w_cph * normalize(1/avg_cph) +
    w_quality * normalize(avg_quality_score) +
    w_volume * normalize(avg_applications_per_week) +
    w_recency * time_decay_factor +
    w_confidence * confidence_score
)

Default weights:
  w_cph = 0.35        (cost efficiency is primary goal)
  w_quality = 0.25    (quality prevents wasted hiring time)
  w_volume = 0.15     (volume matters for speed-to-hire)
  w_recency = 0.15    (recent data is more relevant)
  w_confidence = 0.10 (prefer strategies with more data)
```

### Normalization

All metrics are normalized to a 0-1 scale using min-max normalization across the available strategy options:

```
normalize(x) = (x - min) / (max - min)
```

### Time Decay Factor

```
time_decay(weeks_ago) =
  if weeks_ago <= 4:  1.00
  if weeks_ago <= 8:  0.80
  if weeks_ago <= 12: 0.60
  if weeks_ago <= 24: 0.40
  if weeks_ago > 24:  0.20
```

### Confidence Score

```
confidence_score(sample_size) =
  if sample_size >= 15: 1.00
  if sample_size >= 10: 0.85
  if sample_size >= 5:  0.65
  if sample_size >= 3:  0.45
  if sample_size < 3:   0.20
```

## Strategy Override Rules

Certain conditions override the algorithmic recommendation:

1. **Client brand voice mismatch:** If the winning tone conflicts with the client's registered brand voice, defer to brand voice
2. **Budget constraints:** If recommended channel requires minimum spend above budget, switch to the cheaper channel
3. **Seasonal patterns:** During Q1 (Jan-Mar) and Q4 (Oct-Dec), increase weight of recency factor to 0.25 (hiring patterns shift)
4. **New client:** First 3 campaigns for a new client always run in full exploration mode regardless of industry data
5. **Creative fatigue:** If the same content type has been used for >4 consecutive weeks on the same audience, force a variant test

## Exploration Strategy Templates

When the engine runs exploration variants, use these predefined test configurations:

### Test Configuration A: Tone Test
```
Control: [Winning tone from data]
Variant 1: [Adjacent tone on the formality spectrum]
Budget split: 70% control / 30% variant
Duration: 2 weeks minimum
Success metric: CPA comparison at p<0.05
```

### Test Configuration B: Format Test
```
Control: [Winning content type]
Variant 1: [Different format, same message]
Budget split: 60% control / 40% variant
Duration: 2 weeks minimum, or 2000 impressions per variant
Success metric: CTR and CPA comparison
```

### Test Configuration C: Channel Test
```
Control: [Primary channel with winning strategy]
Variant: [Secondary channel with adapted creative]
Budget split: 60% control / 40% variant
Duration: 3 weeks minimum
Success metric: CPH comparison
```

## Anti-Patterns to Detect

The optimization engine should flag these patterns:

| Anti-Pattern | Detection | Remedy |
|-------------|-----------|--------|
| Audience fatigue | Frequency > 3.0 and declining CTR for 2+ weeks | Expand audience or refresh creative |
| Budget waste | CPA > 2x industry benchmark for 2+ weeks | Pause campaign, review targeting |
| Quality decay | Quality score declining 3+ consecutive weeks | Tighten targeting, review job description |
| Winner's curse | Scaling budget but CPH increasing proportionally | Cap budget at optimal level |
| Echo chamber | Same strategy winning by default (no competition) | Force exploration cycle |
