# The floor view — setting it up and drawing it

Loaded at step 9a. The record it reads and writes is
`../../../shared/contracts/floor-layout.md`. House style is
`../../../shared/artifact-style.md`, component *Floor schematic*.

**What it is.** The plant's own floor, redrawn as a clean schematic, with each
machine's numbers sitting where the machine is. A supervisor reads "the
bottleneck is the second machine in Cell B" faster off a map than off a table.
It is a **view of figures the report already computed**, never a new
calculation: every number on it is a row of the figures block.

**What it is not.** Not live: it shows the state at the last export, and says
so. Not to scale: positions are approximate. Not a replacement for the OEE
table, which stays below it and carries the three components for every asset.

---

## Two turns, never one

**Turn 1 shows the proposed layout and asks. Turn 2 saves it.** Same rule as
`onboarding`, *Two turns, never one*, and `../../../shared/approval-gates.md`:
a yes covers the matches that were shown, with both spellings, and nothing
else.

### Setup turn (attended, once per site)

Runs when the user attaches a floor plan, or asks for a floor view and no
layout is on file.

**1. Read the drawing.** PDF or image. A DWG or other CAD file cannot be read
directly: say so and ask for a PDF or image export.

- **Machines are labelled shapes.** Walls, dimension lines, utilities, doors,
  columns, aisle names and notes are not machines and are ignored. A box with
  no label is not assumed to be a machine: count it, and ask in step 3.
- **A legend or key comes first.** Where the drawing labels machines with codes
  (`M-04`) and carries a key, read the key before the machines. The drawing
  label stays verbatim (`M-04`); the key supplies the name used to propose the
  asset, and the proposal says it came from the key.
- **Every label gets a read mark, `clear` or `unsure`.** `unsure` is a label
  that is small, rotated, overlapped, cut off or low-contrast. **Never propose
  an asset from an `unsure` label.** Quote what was read, with a question mark,
  and ask the user to correct it.
- **One floor per drawing.** A plan that shows more than one floor or a
  mezzanine: say so, ask for one floor at a time, and set up the main floor
  first. Other floors are not supported yet.
- **Set `read_confidence`:** `clean` when every label is `clear`; `partial`
  when some are `unsure` (list them); `poor` when more than a quarter of the
  machines are `unsure`, or the text cannot be read at normal size. **On
  `poor`, stop and ask for a clearer plan or a larger export.** Never guess
  labels. The quarter is a starting cutoff, not a plant-set value.

**2. State the count before anything else.** *"I read 23 machines and 4
unlabeled shapes, in 5 areas."* The user can say at a glance whether a
machine was missed. A count that does not match what the plant expects is the
first thing to check.

**3. List what was read, by area.** One table per zone or area in the drawing's
own order, never one long list. One row per machine: the label **verbatim**,
the read mark, the position in plain words ("Cell B, upper left"), and the
proposed asset match with **both spellings verbatim**
(`Haas VF4 #2` → `HAAS-VF4-02`) and why (name, cell, or both). Candidate
assets come from the consolidated dataset's asset list, not from memory of
earlier runs. Then, for the whole drawing:

- Drawing labels with no plausible asset (*"Bandsaw: no asset by that name in
  the data"*).
- Assets in the data that no label matched (*"HAAS-UMC-01 has no machine on the
  drawing"*).
- The unlabeled shapes, asking whether any is a machine.

Neither list is empty-by-omission: if both are empty, say so.

**4. Ask for a yes per match, or per zone.** *"Yes to Cell 1 as shown"* covers
the rows shown in Cell 1 and nothing else. Where a label could match two
assets (`Puma 3` against `DOOSAN-PUMA-03` and `DOOSAN-PUMA-07`), propose none
and ask which. A blanket "looks good" confirms the rows shown, not rows the
user did not see. **On a drawing with more than about 12 machines, take it a
zone at a time**: show a zone, take its yes, save, and move on. Each save is
turn 2 for that zone; unanswered zones stay `proposed` and draw no figures.

**5. Ask for the name or role** to put on the confirmation. Never take it from
the account. **No name or role, no save**: ask again, and keep the rows
`proposed` until one is given.

### Save turn

On the yes, and with a name or role: write the layout into the plant profile
at `profile_path`, as a `### Floor layout - <site>` section in the shape of
`../../../shared/contracts/floor-layout.md`. `mapping_status` is `confirmed`
only for the rows the user confirmed, `proposed` or `unmapped` for the rest;
increment `Layout version`. Replace only that section; every other line of the
profile stays as it was.

**Then save the profile the way every write-back does**, per
`../../../shared/replies.md`, *The plant setup and the rates*: follow
`install`'s `after_any_change` when the profile came from the plant setup
page, or for a first save `render`, publish, read back and give `saved`'s line
word for word. The layout then rides the plant setup page, and any new task
finds it with `plant_setup.py find`, with no file attached.

Say "saved" only after `saved` confirms it, and name the page. Without the
artifact tools, or with the page refused, say the layout is in this task's
`profile_path` only and lasts only for this task. The yes in the setup turn
covers this save; no further approval is asked.

---

## Every run

1. **Find the layout**: the `### Floor layout - <site>` section of the
   profile at `profile_path`, after `plant_setup.py find` has brought in the
   plant setup page. A layout with no `Layout version` line is version 1: read
   it with the defaults in the contract. An unattended run never writes. None
   found: skip the section with the one-line statement in the contract, and
   carry on.
2. **Compute nothing new.** For each `confirmed` machine, read its row from the
   figures block: OEE, availability, performance, quality, downtime minutes,
   open-outage start if any. A machine with no row has no data (below). A
   machine with a row but no OEE (output with no scrap or no ideal cycle time
   recorded) is *OEE N/A* (below).
3. **Colour by the plant's thresholds**, read from the profile's
   `OEE thresholds` line. See *Thresholds*.
4. **Choose the density** from the machine count (see *Dense floors*), then
   **draw** the schematic as inline SVG built in code, numbers baked in,
   canvas proportions from `canvas_aspect`.
5. **Print the lists under it**: not on the floor plan, on the plan with no
   data, OEE not computable (with the reason), mapping not confirmed. Each with
   its count.

---

## Dense floors

The schematic has to stay readable at the page width. The density is chosen by
the count of **confirmed machines drawn**, and the chosen mode is named in the
caption.

| Machines | Mode | What each machine shows |
|---|---|---|
| Up to 24 | Full | Name, OEE, availability, state word |
| 25 to 60 | Compact | Name, OEE, state word. Availability stays in the OEE table below |
| More than 60 | By area | One schematic per zone, in the drawing's order, each with its own legend line, preceded by an overview of the plant: one block per zone coloured by its worst machine, with the counts (*"Cell 3: 2 poor, 1 watch, 9 OK"*) |

The cutoffs are starting values, to be tuned against real plants.

- **A state word is never dropped to make room.** `OK`, `WATCH`, `POOR`,
  `DOWN`, `NO DATA`, `OEE N/A`, `UNCONFIRMED` are short; the name is what gets abbreviated
  first, and the full name is in the table.
- **No text smaller than the house `--text-xs`.** If a name does not fit at
  that size, it is shortened with the full name in the table, never shrunk.
- **Zones that are not rectangles** are drawn from their outline points when
  the layout holds them, and as their bounding box when it does not.
- **Machines are drawn as boxes** whatever their real shape. Positions stay
  approximate.

---

## Thresholds

The plant sets them; the skill supplies defaults only until it does.

| State | Default | Rule |
|---|---|---|
| Good | OEE at or above 75% | Configurable |
| Watch | OEE from 60% up to the good line | Configurable |
| Poor | OEE below 60% | Configurable |
| Down | Machine currently down | **Always poor**, whatever the day's OEE |
| No data | No row in the figures block | **Always neutral grey.** Never coloured, never 0% |
| OEE N/A | A row, but OEE cannot be computed | **Neutral grey**, *OEE N/A*, availability still shown, the reason listed under the schematic |

- **Read them** from the `OEE thresholds` line of the plant profile:
  *"good at or above X%, poor below Y%"*. A line with a confirmed value is the
  plant's.
- **Missing line, or a placeholder:** use the defaults above and print, once, in
  the legend: *"Colours use default thresholds (75% / 60%), not confirmed for
  this plant."* The note disappears only when the plant has confirmed values.
- **The legend always prints the active cutoffs**, whichever source they came
  from.
- **Thresholds colour OEE only.** They never recolour a down machine, a
  no-data machine or an unconfirmed mapping.
- **Nothing here changes a threshold.** A run cannot edit the profile; that
  takes the profile's two-turn approval via `onboarding`.

---

## Rules inherited from the rest of the skill

- **Absent is not zero** (`../../../shared/absent-is-not-zero.md`). A confirmed
  machine with no output or downtime row reads *no data* in grey. It is
  excluded from every average and named in the list under the schematic. It is
  never 0% OEE.
- **An ongoing outage has a null duration.** Draw *"down since 02:20"*, never
  *"down 0 min"*, per `../../../shared/contracts/downtime-record.md`.
- **Availability above 100% is shown, not clamped** (`oee.md`). The machine's
  fill follows OEE; the cell prints the availability as it is.
- **Safety leads.** A machine with a safety-flagged diagnosis record is
  outlined in the critical colour with the words *"see safety block"*, and the
  safety block stays the first thing under the title, above the schematic. A
  record blocked for missing `safety_flagged` does not colour its machine; the
  machine carries *"blocked, safety status unknown"*.
- **Provisional matches.** A machine whose figures rest on an unapproved
  normalization is marked *provisional*, as in the tables.
- **Status never by colour alone.** Every machine prints a word or glyph with
  its state.
- **Freshness stays above it.** The schematic sits below the freshness banner
  and carries its own line: *"State as of the last export, [timestamp]. Not
  live."* A missing export is the banner's first row and the schematic's
  machines show *no data*, not yesterday's numbers.
- **Nothing is silently dropped.** An asset in the data with no machine on the
  plan is listed with its figures under *Not on the floor plan*. A drawn
  machine with no asset is listed under *On the plan, not in the data*.
- **Layout drift.** An asset that appears in the data after the layout was
  confirmed, and is on neither list, goes under *Not on the floor plan* with
  *"new since the layout was confirmed"*. The skill does not place it.
- **Approximate by design.** One line says positions are schematic, not to
  scale.

---

## What it does not do

- No click-through detail; the OEE table below carries every machine's three
  components.
- No per-machine trend.
- No live status.
- No DWG or CAD input, and one floor per layout. A drawing that shows several
  floors is set up one floor at a time, and only the main floor is supported.
- No automatic re-reading of a changed drawing. A changed floor is a new setup
  turn, `Layout version` + 1, confirmed again.

---

## Failure modes

- **A plan that cannot be read reliably** (`poor`): stop the setup turn and ask
  for a clearer one. A DWG or other CAD file: ask for a PDF or image export.
- **A drawn machine that matches no asset, or an asset with no machine on the
  drawing**: both listed under the schematic. Neither is dropped, and neither
  is given figures.
- **A label that could be two assets**: propose neither, ask which.
- **A machine currently down**: always poor, whatever its day's OEE, printed
  *down since* its start time, never a zero duration.
- **An asset added after the layout was confirmed**: listed as new since the
  layout was confirmed, not placed.
- **A busy drawing**: the count first, one table per area, a yes a zone at a
  time past about 12 machines, one floor per layout; density per *Dense
  floors*.
- **The page cannot be saved**: the layout stays in this task's
  `profile_path`; say it lasts only for this task.

## What this section exists to prevent

- A machine shown with *another* machine's OEE because a label was matched by
  guess, or because a small label was misread.
- A down machine coloured green because the day's average was fine.
- A machine with no export row drawn red at 0%, read by the meeting as a
  breakdown.
- A stale layout silently hiding a machine added last month.
- A schematic that looks live and is a day old.
- A machine missed on a busy drawing and nobody noticing, which is why the
  count comes first.
- A layout that only exists in the task where it was set up, so every new
  thread starts from nothing.
