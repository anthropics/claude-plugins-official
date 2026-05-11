# Excel Output Spec

The Excel file is the deliverable most deal teams will actually open. Get it right.

## If Claude in Excel / Office agent is available

Build the workbook directly in Excel via the Office agent. This is the preferred path because it preserves formatting, lets the reviewer work in their native tool, and supports the cell-comment pattern natively.

## If not, use openpyxl

Check with `python3 -c "import openpyxl"`. If not installed, offer to install (`pip3 install openpyxl`) or fall back to CSV.

## Workbook structure

**Sheet 1: `Review`** (the main grid)
- Row 1: Work-product header (merged cell, the header from plugin config `## Outputs`)
- Row 2: Column labels
- Row 3+: One row per document
- Column A: Document name / path
- Columns B onward: one per schema column, in schema order
- After every data column, a hidden `_source` column with `[quote] | [location]`
- Cell comment on the data column cell = the quote and location (so it surfaces on hover even with `_source` hidden)
- Cell fill by state: no fill = `answered`, `#FFF2CC` (light yellow) = `unclear` or `needs_review`, `#EFEFEF` (light gray) = `not_present`
- A `Verified` column after each group of [data + _source]: blank by default. The reviewer fills it. Dropdown validation: `✓`, `✗`, `?`.

**Sheet 2: `Flags`**
- One row per cell flagged as `unclear` or `needs_review`
- Columns: Document, Column, State, Value (if any), Quote, Location, Note
- This is the verification work queue. Sort by column so the reviewer can batch similar judgments.

**Sheet 3: `_schema`**
- The column definitions from `.review-schema.yaml`, one row per column: id, label, type, options, prompt
- Makes the file self-documenting. A partner who opens it six months later can see exactly what was asked.

**Sheet 4: `_summary`**
- Document count, column count, run date
- Per-column counts of answered / not_present / unclear / needs_review
- List of columns the normalization pass flagged
- The verification reminder text

## What not to do

- Do not write a confidence percentage column. It's not information. The state + quote is the signal.
- Do not truncate quotes to fit a cell. Wrap the text or put the full quote in the comment.
- Do not merge cells in the data region. Lawyers will sort and filter.
- Do not write the table without the `_schema` and `_summary` sheets. The self-documentation is what makes the file trustworthy.


## Formula injection defense

Before writing any cell in Excel, Sheets, or CSV output, neutralize formula injection. Counterparty-sourced text (contract quotes, party names, registered agent data, CLM exports) is attacker-controlled. A cell starting with `=`, `+`, `-`, `@`, `	`, ``, or `
` will be interpreted as a formula or break the row structure.

- **Prefix with a single quote:** `'=SUM(A1:A10)` → `=SUM(A1:A10)` (displayed as text, not executed)
- **Applies to every cell that contains text sourced from a document, a tool result, or a user paste.** Column headers you control and computed values you produce are safe.
- **CSV: also escape embedded commas, double quotes, newlines** (RFC 4180 quoting).
- This is not optional. A spreadsheet your user opens in Excel that triggers a macro or exfiltrates data via DDE is a supply-chain attack on your user.

