# The two hard stops

Most of this skill assembles a package and reports what is missing. Two
conditions are different: they **block**, and no amount of user insistence
converts them into a warning.

---

## 1. Revision mismatch

**The revision in the document library must match the revision on the ERP item
master. When they disagree, stop.**

This is not a data-quality nicety. **Sending a supplier the wrong revision is
the classic and expensive error this skill exists to prevent**, and it is
expensive in a specific way: nothing goes wrong for months. The supplier quotes
the drawing you sent, wins the business, tools up, and ships parts that are
correct against the print in their hand and wrong against the one in yours. You
find out at first article if you are lucky, and at the customer if you are not.

### What to check

| Check | Where |
|---|---|
| Revision on the drawing file itself | The title block, not the filename. Filenames lie |
| Revision recorded in the document library | M365 metadata or the library's own record |
| Revision on the ERP item master | Where the profile's `### ERP scope` says revision lives: a named field, the item-ID suffix with its pattern, or not in the ERP. **Never inferred**: with no setting, say the ERP's revision location is not set and that the check could not use the ERP |
| Revision the current demand was ordered against | Open purchase orders and sales orders |

**Read the title block, not the filename.** `4471-B-RevC-final-v2.pdf` tells you
what somebody typed. The title block tells you what the drawing is.

### What to report

Name both revisions, both sources, and both dates. Do not resolve it — this is
a controlled-document question with an owner, and that owner is not the skill.

> *"Stopping before assembling the package. The document library holds
> 4471-B at Rev C, dated 2026-06-11. The NetSuite item master records Rev B, and
> the open demand on PO-8841 was placed against Rev B. Those cannot both be
> current. Either the item master was not updated when C released, or C was
> released and never flowed to purchasing.*
>
> *That distinction matters to the quote, because the two revisions differ. I
> need document control to confirm which revision this sourcing action is
> against before anything goes to a supplier."*

### The one thing not to do

Do not send both revisions and let the supplier work it out. It looks helpful. It
produces bids that are not comparable, and it tells the supplier that your
configuration control is unreliable, which is a bad thing for them to know while
they are pricing you.

---

## 2. Restricted data

**ITAR, EAR, export-controlled, or otherwise restricted technical data must not
be assembled into an outbound package without an explicit gate.** This is
blocking, and it blocks before assembly rather than before sending.

The reason for the ordering: once restricted geometry is collated into a package
that is one click from an email, the control has already been weakened. Stop at
the point of gathering.

### How it shows up

- An ITAR or EAR marking in the drawing title block or border
- A distribution statement, or "export controlled" in a document header
- A customer program known to be defence, space or controlled — captured in
  `## Plant context` during `onboarding`
- A supplier who is not on the plant's cleared list for that program

### What to do

Report it as blocking, name what was found and where, and state the specific
question that needs answering — usually whether the candidate supplier holds the
required registration and whether an export authorization covers the disclosure.

**Do not assess eligibility.** Whether a given supplier may receive controlled
technical data is a compliance determination with a named owner at the plant. The
skill's job is to notice, stop, and route it there.

---

## Why these two and not the rest

Everything else this skill finds goes on the missing-items list and the user
decides. These two are different because **both produce a harm that lands
somewhere other than where the mistake was made** — with a supplier who built to
the wrong print, or with a compliance exposure the plant carries.

A missing lead-time requirement produces a worse bid, and that is visible
immediately. These two are not visible until much later, which is exactly why
they are gates rather than warnings.
