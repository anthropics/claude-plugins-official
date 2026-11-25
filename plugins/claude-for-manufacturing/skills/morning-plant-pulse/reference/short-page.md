# The short Operations page

Loaded at step 3.4. The page is rendered by `../scripts/render_short.py`
from the engine's output in the same run; you run it and report it, you do not
write it.

**It is a second page, not a replacement.** The Operations Command Center
dashboard (`operations-dashboard.md`) stays exactly as it is: one per site,
updated in place, trend panel and all. The short page is one HTML file per
production day, `operations-short-<site>-<day>.html`, written beside the
figures. Its footer says so: *"The full Operations page is separate; keep
both."* It never tells anyone to save over the full page.

---

## What is on it, in order

1. **Header**: site, production day, generated time, *"Generated from the
   morning-plant-pulse run of <date>. Read-only, nothing written to any
   system."*
2. **Safety**, when a diagnosis record is safety-flagged or blocked for a
   missing flag. Above the freshness line, as on the full page: the safety
   rule in `../../daily-production-report/SKILL.md`, step 7, outranks every
   other ordering rule.
3. **Freshness line**: one line, not a table, unless sources disagree. With
   no plant profile it ends *"Times are plant local, assumed <zone>; no plant
   profile."*
   When the day holds fewer shifts than most days it says *"Not a complete
   plant day: …"* with the shifts that are in.
4. **Today's decisions**: three at most, in this order: export failure, the
   machine decision for the worst asset by downtime month to date, a customer
   quality hold, then anything else by what is at stake. One line after them
   names the fixes still waiting and links to the full page.
   - **The machine decision** is four sentences at most: *"Safety status: not
     assessed"* whenever no diagnosis record exists; the actions; one evidence
     line; and, only with lockout advice, *"Precaution, not a finding: …"*.
   - **Lockout** appears only when the asset has no diagnosis record AND its
     maintenance history shows a repeat failure or a seizure.
5. **Exceptions**, the whole data window, one card each.
6. **Day / Week / Month**, controlling Output, Downtime, and Scrap, cost and
   quality only. Week is Monday to Sunday around the selected day; Month is
   the 1st through the selected day, marked *Partial month* until the last
   day. Clicking a day in any breakdown opens that day.
7. **What this report can't show yet**: exactly three items.
8. **Data problems**, collapsed, last: waiting on a decision, other gaps, run
   assumptions, part-number normalizations, *Mismatched records · N*
   (classes 1–5 and 8 only), integrity flags, checked, nothing wrong.
9. **Footer**: where the figures live, with row counts, and the placement line.

## The checks it runs before writing anything

No new numbers (each printed number is a figures row, and the page carries
the row id); no draft wording; the assumed zone named when there is no
profile; the safety label, the lockout trigger and the four-sentence cap; the
decision order; the Month view on the last day equal to the full page's month;
the Provisional label in every view a normalization touched. Any failure: no
page, and the reply says the short page was not written and why.

## A stop whose duration disagrees with its timestamps

This page holds those minutes out, as the full page does
(`../../daily-production-report/SKILL.md`, step 4), so the Month view always
equals the full page. The conflict is listed on the stop's row and under each
table.
