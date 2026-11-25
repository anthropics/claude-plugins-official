# Contract: the floor layout

**Emitted by** `daily-production-report`, step 9a, in an attended setup turn only
**Consumed by** `daily-production-report`, step 9a, on every later run, to draw the floor view
**Chains** 3 (the morning report inside the pulse reads the same profile)
**Contract version** 2

Rules that govern every contract are in [README.md](README.md). Where the
profile is stored and how it is saved is `../replies.md`, *The plant setup and
the rates: two private pages*.

---

## Why it exists

A plant manager gives Claude their floor plan once. Every later report, in any
new task, draws each machine's figures where it sits, with no re-upload. So
the layout is stored **inside the plant profile**, as one section per site,
and travels with it on the plant setup page that every skill brings in with
`plant_setup.py find`. The drawing itself is never stored, only what was read
from it.

**Only the setup turn writes it**, after the person confirmed the matches and
typed a name or role. Every other run only reads it.

---

## Where it lives

A `### Floor layout - <site>` section of the `## Plant context` block, one per
site, after the profile's other sections. It holds no rate value and no email
address, so the plant setup page accepts it.

## Header lines

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `Layout version` | integer | Required | Starts at 1, plus 1 on every save. A section with no version line is version 1 |
| `Contract version` | integer | Required | 2. Absent: read as 1, with the defaults under *Missing behavior* |
| `Drawing` | string | Required | File name, sha256 (first 12 characters), date received, machines read, unlabeled shapes, legend used yes or no. Provenance only |
| `Aspect` | number | Required | The drawing's width divided by its height. The schematic keeps it at any width |
| `Read` | `clean`, `partial` or `poor` | Required | A `poor` read is never saved |
| `Zones` | list | Required | `Name (x,y,w,h)` per area, separated by `;`. Optional outline points after the box for an irregular zone: `Name (x,y,w,h) [x1,y1 x2,y2 ...]` |
| `Confirmed by` | string | Required | The name or role the person typed, and the date. Never taken from the account. No value, no save |

## Machine rows

One pipe table, one row per labelled shape on the drawing. Positions are
normalized 0 to 1 on the drawing, origin top left.

| Column | Type | Behavior | Notes |
|---|---|---|---|
| `Label` | string | Required | Verbatim from the drawing, `?` appended when the read mark is `unsure` |
| `Asset` | string or `-` | Required | The asset key, verbatim from the data. `-` when unmapped |
| `Asset name` | string or `-` | Required | The asset's own spelling in the data, so both spellings stay visible |
| `Box` | `x,y,w,h` | Required | Normalized 0 to 1 |
| `Zone` | string | Required | A zone named in `Zones` |
| `Read` | `clear` or `unsure` | Required | An `unsure` label is never `confirmed` |
| `Status` | `confirmed`, `proposed` or `unmapped` | Required | Only `confirmed` draws figures |
| `Confirmed at` | date or `-` | Required | The day of the yes, for `confirmed` rows |

Unlabeled shapes the person said are not machines are not rows.

---

## Worked example

```
### Floor layout - Fairview

- **Layout version:** 1
- **Contract version:** 2
- **Drawing:** fairview-floor-plan.png, sha256 18c963f688f7, received 2026-11-10, 7 machines read, 1 unlabeled shape, legend used no
- **Aspect:** 1.60
- **Read:** clean
- **Zones:** Cell A (0.03,0.06,0.44,0.40); Cell B (0.53,0.06,0.44,0.40); Cell C (0.03,0.54,0.44,0.40); Cell D (0.53,0.54,0.44,0.40)
- **Confirmed by:** plant manager, 2026-11-10

| Label | Asset | Asset name | Box | Zone | Read | Status | Confirmed at |
|---|---|---|---|---|---|---|---|
| Mazak QT250 | MAZAK-QT-01 | Mazak QT250 | 0.07,0.16,0.16,0.22 | Cell A | clear | confirmed | 2026-11-10 |
| Mazak QT250 #4 | MAZAK-QT-04 | Mazak QT250 #4 | 0.27,0.16,0.16,0.22 | Cell A | clear | confirmed | 2026-11-10 |
| Haas VF4 #2 | HAAS-VF4-02 | Haas VF4 #2 | 0.57,0.16,0.16,0.22 | Cell B | clear | confirmed | 2026-11-10 |
| Haas VF4 #5 | HAAS-VF4-05 | Haas VF4 #5 | 0.77,0.16,0.16,0.22 | Cell B | clear | confirmed | 2026-11-10 |
| Puma 3 | DOOSAN-PUMA-03 | Doosan Puma 3 | 0.07,0.64,0.16,0.22 | Cell C | clear | confirmed | 2026-11-10 |
| Puma 7 | DOOSAN-PUMA-07 | Doosan Puma 7 | 0.27,0.64,0.16,0.22 | Cell C | clear | confirmed | 2026-11-10 |
| Okuma Genos M560 | OKUMA-GENOS-02 | Okuma Genos M560 | 0.57,0.64,0.16,0.22 | Cell D | clear | confirmed | 2026-11-10 |
| Bar saw | - | - | 0.77,0.64,0.16,0.22 | Cell D | clear | unmapped | - |
```

`HAAS-UMC-01` is in the data and on no row, so every report lists it under
*Not on the floor plan* with its figures. `Bar saw` is on the drawing and in
no data, so it is drawn as a neutral outline and listed under *On the plan,
not in the data*.

---

## Missing behavior

| Absent | What the consumer does |
|---|---|
| The whole section | Skip the floor view with one line: *"No floor layout is on file. Attach a floor plan (PDF or image) to set one up."* Nothing else in the report changes |
| `Layout version` or `Contract version` | Read as version 1. Rows with no `Read` column are `clear`; rows with no `Status` column are `proposed`, so they draw no figures until confirmed again |
| `Confirmed by` | Every row is treated as `proposed`. The view draws outlines only and says the layout needs confirming |
| `Aspect` | Use the bounding box of all zones |
| A zone's outline points | Draw its box |
| A machine's figures-block row | *No data*, grey, out of every average. Never 0% |
| A machine's OEE, with the row present | *OEE N/A*, grey, availability shown, the reason listed |
