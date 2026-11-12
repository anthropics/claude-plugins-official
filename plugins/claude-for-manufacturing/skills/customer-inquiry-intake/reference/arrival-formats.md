# How an RFQ actually arrives

**There is no standard format, and that is exactly the problem this skill
exists to solve.** In one week an estimator might get all five of these.

The extraction is mechanical, high-volume work, and it is currently done by the
most expensive person in the department.

---

## The five formats

### 1. A PDF drawing package with "can you do this?" in the email body

The commercial terms are often in the email, the technical content in the
attachments. The email body is an input, not a covering note.

### 2. A spreadsheet with 40 line items and no drawings

The column headers are the customer's. Extract what is there. Do not invent
drawings that did not arrive.

### 3. A customer portal export with fields in an unfamiliar order

The field names are the portal's, not yours. Extract into the intake form
anyway.

Portal exports carry a generation timestamp. **Note it** — a portal export
pulled a week ago may no longer match what the portal says today, and the
response deadline is usually counted from the portal's date rather than the
day the file reached you.

### 4. A phone photo of a marked-up print

Extract what is visible and **mark the line for human review**.

**Never infer a tolerance from a drawing**, and never from a photograph of one.
A `specs` entry with no source reference is not permitted.

### 5. A forwarded thread where the requirement is in the fourth message down

Read the thread. Cite the message each field came from. Do not treat the latest
message as the requirement just because it is latest.

---

## One inquiry, several line items

**A multi-attachment RFQ is one inquiry with several line items, never several
inquiries.**

Different parts in one package can carry different delivery dates, different
quantities and different certifications. That is normal — the contract holds
dates per line for exactly this reason. Splitting the package into separate
inquiries loses the fact that the customer is asking for them together, which is
often the whole commercial point.

---

## Revisions of an earlier RFQ

Detect and **link** rather than creating a duplicate. Set `supersedes_rfq`.

A revised RFQ that quietly becomes a second inquiry is how a plant ends up
quoting the same job twice against different requirements, then sending both.

Signals worth checking: the customer's own reference reappearing, the same part
and customer within a short window, "revised," "updated," or "rev 2" in a
filename or subject line.

---

## Provenance on every field

Every extracted field carries **which file and which page it came from**, so the
estimator can verify without re-reading the package.

This is what separates a useful extraction from one that has to be checked from
scratch, and it is why `field_sources` is a required field the consumer blocks
on. An estimator who cannot trace a number will re-derive all of them, and the
skill has then saved nobody anything.
