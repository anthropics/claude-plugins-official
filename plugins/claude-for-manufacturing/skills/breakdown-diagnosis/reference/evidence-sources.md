# The five evidence sources, and how to read each

A technician standing at a stopped machine has all five of these available and
time to assemble none of them. That gap is the skill.

**MTTR's largest component is usually not the repair.** It is the diagnosis —
working out what is actually wrong. Every minute spent there is a minute the
plant is not producing.

Listed in order of value, which is not the order anyone expects.

---

## 1. Free-text close-out notes — the highest-value input in the plugin

When a technician closes a maintenance work order, they write what they found in
prose:

> *"Bearing was hot, replaced, coupling was misaligned again."*

That sentence contains a diagnosis, a repair, and a recurring root cause that
nobody has acted on. It is written by the person with their hands on the machine,
it is the most honest record in the plant, and **nobody has ever aggregated it.**
It sits in a text field on a work order and is read once, by the person who wrote
it, never again.

### How to mine it

**Search this asset first, then siblings of the same model.** A machine that is
new or has thin history is not a dead end — the same model in the next bay has
been failing in the same ways for years.

**Weight by symptom similarity, then by recency.** A note describing this exact
symptom from two years ago beats a generic note from last month.

**Read what the words actually say, including the throwaway ones.** "Again" is
the single highest-signal word in a close-out note. So are "still," "same as
last time," "temporary fix," and "needs proper repair when we have time." Each
one is a technician telling you this is unresolved.

### Check for templates before citing anything

A CMMS lets a technician pick a stock close-out phrase, and many do. "Spindle
noise reported. Could not reproduce. Monitored." on five machines of three
different makes on the same day is a default, not five observations. Group the
notes by exact text and count the makes and models each group spans (model from
the asset name if the record has no model column; say so). Text shared across
makes is shown, labelled "same text on N assets — not specific to this
machine", and never cited as this asset's evidence. The same failure on
same-model siblings is cited, as a fleet pattern. Do the grouping in code and
print it, so the cited set is the same on every run over the same data.

### Report coverage honestly

Many notes are useless. "Fixed." "Repaired." "OK now." A field that exists is
not a field that says anything.

**State what fraction of the relevant history carried usable notes.** Do not
over-read a terse note into a pattern — per
`../../../shared/absent-is-not-zero.md`, an empty note is not evidence of a
simple repair.

> *"Nine prior work orders on this asset. Four have substantive close-out notes;
> five say only 'repaired' or similar. The pattern below rests on those four."*

---

## 2. The sensor window — read shapes, not thresholds

The historian logs temperature, vibration, pressure and spindle load at high
frequency. Pull a configurable period **before** the failure.

**Look for excursions, trends and step changes — not just threshold breaches.**
This is the whole point. A vibration reading that climbed steadily for six hours
and never once crossed its alarm limit is a bearing failing in plain sight, and a
threshold check reports nothing at all. Three shapes worth naming:

| Shape | Typically means |
|---|---|
| A steady climb | Progressive wear — bearing, tool, belt |
| A step change | Something discrete happened — a part let go, a setting changed, a fixture moved |
| An excursion that recovered | An intermittent fault, which is the hardest kind to catch and the most valuable to have caught |

**Verify the window actually covers the event.** If the export stops an hour
before the failure, say so and **do not reason from adjacent data as if it were
the event.** That is the highest-risk error available here.

**No sensor data at all is very common** — most assets in most plants are not
instrumented. Proceed on the other four sources and say plainly that sensor
evidence was unavailable. This is not a degraded run; it is the normal one.

---

## 3. Maintenance history

What has broken before, what fixed it, what has been replaced recently.

Weight **recency and symptom similarity** together. A part replaced last week is
relevant to a failure this week in a way a five-year-old record is not — both
because it may be the cause and because it may have been installed wrong.

**A new asset with no history falls back to the manual and to sibling assets of
the same model.** State which you used.

---

## 4. Photos — a genuine multimodal advantage

Technicians photograph what they see, and always have. Read them for:

- Visible damage, leaks, scoring, discolouration, wear patterns
- Part numbers on the failed component, which shortens the repair
- Display readings and fault codes on the machine's own panel

**Describe what is visible. Never assert a diagnosis from an unclear image.** A
blurry photo of a dark housing supports nothing, and saying so costs nothing.

> *"The photo shows fluid pooled below the left side of the housing and
> discolouration around the upper bearing cap. I can't tell from this image
> whether the fluid is coolant or hydraulic oil, and that distinction changes
> the diagnosis — worth a look."*

---

## 5. The manufacturer's manual

A PDF sitting in a document library, containing exactly what is needed and never
opened during a breakdown: troubleshooting trees keyed to fault codes,
tolerances, and specified procedures.

Match the fault code the machine is displaying to the manufacturer's own tree,
and **cite the page**. A manufacturer's stated tolerance beats an inference every
time.

---

## The citation rule

Every candidate cause carries the specific evidence behind it — including the
**specific prior work order numbers**, so the technician can read what was
actually done last time rather than taking a ranked list on trust.

**A candidate with no citation is a guess, and is labelled as one.** Not omitted:
an experienced hunch is worth stating. But it is marked as reasoning rather than
evidence, so the technician knows which of the five sources it came from — and
that it came from none of them.
