# Google Sheets Output Spec

For teams on Google Workspace. Same structure as the Excel output, different mechanics. If both Excel and Sheets paths are available, ask the user which they prefer — don't guess from your environment.

## How to write it

Three paths, in order of preference:

1. **Google Sheets MCP** (if a `gdrive` or `gsheets` MCP with write/create capability is connected). Create the spreadsheet, write the sheets, set formatting via the API.
2. **Google Sheets API via ADC** (if the user has `gcloud auth application-default login --enable-gdrive-access` set up and Python `google-api-python-client` available). Use `sheets.spreadsheets().create()` and `batchUpdate` for formatting.
3. **Fallback: CSV + manual import.** Write the CSVs, tell the user to import to Sheets. Also write a `format-instructions.md` so they can apply the color coding and data validation manually.

Do not assume write access you haven't verified. Check first; fall back gracefully.

## Workbook structure

Mirror the Excel spec exactly — same sheets, same semantics, Sheets-native mechanics:

**Sheet: `Review`** (the main grid)
- Row 1: Work-product header (merged cell)
- Row 2: Column labels
- Row 3+: One row per document
- Column A: Document name / link (if source docs are in Drive, hyperlink to the file — this is a Sheets advantage over Excel)
- Columns B onward: one per schema column
- **Source quotes go in cell notes** (Sheets notes, not comments — notes are persistent annotations, comments are collaboration threads). Notes surface on hover and export to `.xlsx` as comments.
- Cell fill by state: default = `answered`, light yellow = `unclear` or `needs_review`, light gray = `not_present`. Use `repeatCell` with `userEnteredFormat.backgroundColor` in `batchUpdate`.
- A `Verified` column after each group: blank by default, data validation dropdown `✓ | ✗ | ?` via `setDataValidation`.

**Sheet: `Flags`**
- Same as Excel spec. One row per flagged cell.

**Sheet: `_schema`**
- Column definitions from `.review-schema.yaml`.

**Sheet: `_summary`**
- Counts, flagged columns, verification reminder.

## Sheets-specific advantages to use

- **Hyperlinks to source documents.** If the reviewed documents are in Drive (common for VDR exports and internal repositories), each row's document name should be a hyperlink to the file. This is the click-to-source pattern, and Sheets does it natively.
- **Shared review.** Sheets handles concurrent review better than a local `.xlsx`. If the deal team wants to divide verification work, this is the format to use.
- **Named ranges for the schema.** Define a named range over each column so downstream formulas (pivot tables, conditional counts) are readable.
- **Conditional formatting by state column.** If you write a hidden `_state` column per data column, you can drive the color coding from it with conditional formatting rules — cleaner than per-cell formatting and survives sorting.

## Sheets-specific gotchas

- **Notes are per-cell and invisible in print.** If the output will be printed or PDFed for a partner meeting, also write the quotes into the `Flags` sheet so they survive.
- **Sheets has a 10 million cell limit.** You won't hit it in a legal review, but if someone tries to grid 50,000 documents with 30 columns plus source columns, warn them.
- **Sharing defaults.** Per the plugin practice profile, this is attorney work product. Create the spreadsheet with restricted sharing (owner only), and tell the user to share it deliberately. Do not default to "anyone with the link."
- **Formula escaping.** If a verbatim quote begins with `=`, `+`, `-`, or `@`, prefix it with a single quote (`'`) so Sheets doesn't try to parse it as a formula. This is a real failure mode: a contract clause that starts "- The parties agree..." will render as a formula error without the escape.

## What not to do

Same as the Excel spec: no confidence percentages, no truncated quotes, no merged cells in the data region, and always write the `_schema` and `_summary` sheets.


## Formula injection defense

Before writing any cell in Excel, Sheets, or CSV output, neutralize formula injection. Counterparty-sourced text (contract quotes, party names, registered agent data, CLM exports) is attacker-controlled. A cell starting with `=`, `+`, `-`, `@`, `	`, ``, or `
` will be interpreted as a formula or break the row structure.

- **Prefix with a single quote:** `'=SUM(A1:A10)` → `=SUM(A1:A10)` (displayed as text, not executed)
- **Applies to every cell that contains text sourced from a document, a tool result, or a user paste.** Column headers you control and computed values you produce are safe.
- **CSV: also escape embedded commas, double quotes, newlines** (RFC 4180 quoting).
- This is not optional. A spreadsheet your user opens in Excel that triggers a macro or exfiltrates data via DDE is a supply-chain attack on your user.

