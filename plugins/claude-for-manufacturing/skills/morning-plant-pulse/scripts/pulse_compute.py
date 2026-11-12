"""Morning plant pulse: every figure the Operations pages print, computed in one place.

    python3 -I pulse_compute.py --exports exports/ --out pulse-output/ \
        [--day YYYY-MM-DD] [--profile FILE] [--rates FILE] [--diagnoses DIR] \
        [--manifest manifest.json] [--run-time ISO-8601] [--tz Area/City]

Standard library only, so it runs wherever Python 3.9+ does. It reads the
export folder (CSV, or XLSX with one table per sheet), recognises each file by
its header signature, and writes three files to --out:

    figures.csv        the figures tab: one row per printed number, with its
                       filter, period and source. A number the pages print
                       and this file does not hold is a defect.
    pulse_model.json   everything the pages are built from, already computed.
                       The page code selects and formats; it does no arithmetic.
    day_records.json   one pulse day record per production day the exports
                       cover, per shared/contracts/pulse-day-record.md.

It then checks itself (subtotals reconcile, no absent value stored as 0) and
exits 2 with the failures listed if any check fails. Nothing is written to any
system of record. Rules it applies, by file:

    skills/data-consolidate/reference/join-keys.md         the ladder, integrity flags
    skills/data-consolidate/reference/mismatch-classes.md  classes 1-8
    skills/daily-production-report/reference/oee.md        OEE and its traps
    shared/absent-is-not-zero.md                           absent is never 0
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile
from collections import Counter, OrderedDict, defaultdict
from datetime import date, datetime, timedelta, timezone
from xml.etree import ElementTree

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9
    ZoneInfo = None

ENGINE_VERSION = "1"
DEFAULT_TZ = "America/New_York"
LOOKBACK_DAYS = 180
TERSE_NOTES = {"fixed", "fixed.", "done", "done.", "ok", "ok.", "repaired", "repaired.", "n/a", ""}
SEIZURE_WORDS = ("seiz", "seized", "seizure", "locked up", "crash")


# --------------------------------------------------------------------------
# Reading files
# --------------------------------------------------------------------------

def fold(name):
    """Header comparison form: case-folded, punctuation collapsed to _."""
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def read_csv(path):
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            text = f.read()
    except UnicodeDecodeError:  # a spreadsheet's "CSV" is often Windows-1252, not UTF-8
        with open(path, newline="", encoding="cp1252", errors="replace") as f:
            text = f.read()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    rows = list(csv.reader(io.StringIO(text)))
    return rows


def read_xlsx(path):
    """Every sheet of an XLSX, as {sheet_name: rows}, with the standard library."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    out = OrderedDict()
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ElementTree.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
        wb = ElementTree.fromstring(z.read("xl/workbook.xml"))
        rels = ElementTree.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels}
        for sh in wb.find("m:sheets", ns):
            rid = sh.get("{%s}id" % ns["r"])
            t = target[rid].lstrip("/")
            t = t if t.startswith("xl/") else "xl/" + t
            root = ElementTree.fromstring(z.read(t))
            rows = []
            for row in root.iter("{%s}row" % ns["m"]):
                cells = {}
                for c in row.findall("m:c", ns):
                    ref = re.match(r"([A-Z]+)", c.get("r", "A")).group(1)
                    col = 0
                    for ch in ref:
                        col = col * 26 + ord(ch) - 64
                    v = c.find("m:v", ns)
                    if c.get("t") == "s" and v is not None:
                        val = shared[int(v.text)]
                    elif c.get("t") == "inlineStr":
                        val = "".join(x.text or "" for x in c.iter("{%s}t" % ns["m"]))
                    else:
                        val = v.text if v is not None else ""
                    cells[col - 1] = val
                if cells:
                    rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
            out[sh.get("name")] = rows
    return out


def read_flat_yaml(path):
    """One contract record per file: flat `key: value` lines, as breakdown-diagnosis emits."""
    rec = OrderedDict()
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.lstrip().startswith("#") or line.startswith((" ", "\t", "-")):
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith(("'", '"')) and v.endswith(v[0]) and len(v) >= 2:
            v = v[1:-1]
        elif v in ("null", "~", ""):
            v = None
        elif v in ("true", "false"):
            v = v == "true"
        elif v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        rec[k.strip()] = v
    return rec


# --------------------------------------------------------------------------
# Recognising each export by its header signature
# --------------------------------------------------------------------------

# Canonical column name -> accepted folded spellings. A plant whose headers
# differ passes a manifest; this list only spares the common cases.
ALIASES = {
    "part_number": ["part_number", "part", "part_no", "item", "item_number", "item_id", "pn"],
    "work_order": ["work_order", "production_work_order", "wo", "wo_number", "job", "job_number"],
    "qty_good": ["qty_good", "good", "good_qty", "quantity_good", "qty_complete_good"],
    "qty_scrap": ["qty_scrap", "scrap", "scrap_qty", "quantity_scrap"],
    "qty_rework": ["qty_rework", "rework", "rework_qty"],
    "qty_ordered": ["qty_ordered", "order_qty", "quantity_ordered", "qty"],
    "uom": ["uom", "unit", "unit_of_measure", "units"],
    "shift": ["shift", "shift_start"],
    "production_day": ["production_day", "prod_day", "production_date"],
    "lot_number": ["lot_number", "lot", "batch", "lot_no", "heat"],
    "asset_id": ["asset_id", "asset", "machine", "machine_id", "equipment_id"],
    "cell": ["cell", "line"],
    "due_date": ["due_date", "due"],
    "status": ["status"],
    "site": ["site", "location_site", "subsidiary_site"],
    "planned_qty": ["planned_qty", "plan_qty", "qty_planned", "planned_quantity"],
    "plan_date": ["plan_date", "date", "scheduled_date"],
    "planned_hours": ["planned_hours", "scheduled_hours"],
    "work_center": ["work_center", "workcenter", "resource"],
    "started_at": ["started_at", "start", "start_time", "down_start"],
    "ended_at": ["ended_at", "end", "end_time", "down_end"],
    "duration_minutes": ["duration_minutes", "minutes", "duration_min", "duration"],
    "reason_code": ["reason_code", "reason", "code"],
    "reason_text": ["reason_text", "reason_description", "comment", "description"],
    "maintenance_wo": ["maintenance_wo", "maintenance_work_order", "mwo", "ticket"],
    "opened_date": ["opened_date", "opened", "open_date", "created"],
    "closed_date": ["closed_date", "closed", "close_date"],
    "type": ["type", "wo_type", "maintenance_type"],
    "close_out_note": ["close_out_note", "closeout_note", "notes", "note", "resolution"],
    "ncr_id": ["ncr_id", "ncr", "ncr_number"],
    "found_at": ["found_at", "found", "date_found", "created_at"],
    "customer": ["customer", "customer_name"],
    "description": ["description", "desc"],
    "std_cost": ["std_cost", "standard_cost", "unit_cost"],
    "measured": ["measured", "measurement", "value"],
    "nominal": ["nominal", "spec", "target"],
    "characteristic": ["characteristic", "feature"],
    "sales_order": ["sales_order", "so", "so_number"],
    "promised_date": ["promised_date", "promise_date", "ship_date"],
    "customer_id": ["customer_id"],
    "op_seq": ["op_seq", "operation", "oper_no", "op"],
    "run_min_per_unit": ["run_min_per_unit"],
    "run_hours_per_unit": ["run_hours_per_unit", "run_hrs_per_unit"],
    "setup_hours": ["setup_hours", "setup_hrs"],
    "recorded_at": ["recorded_at", "timestamp", "ts"],
    "asset_name": ["asset_name", "name"],
    "location": ["location"],
    "found_by": ["found_by"],
    "source_file": ["source_file", "file"],
    "generated_at": ["generated_at", "generated", "exported_at"],
    "covers_from": ["covers_from"],
    "covers_to": ["covers_to"],
}

# role -> (columns that must all resolve, columns that must not be present)
ROLES = OrderedDict([
    ("drop_manifest", (["source_file", "generated_at"], [])),
    ("ncrs", (["ncr_id"], [])),
    ("downtime", (["asset_id", "started_at"], ["recorded_at", "opened_date", "closed_date"])),
    ("maintenance", (["maintenance_wo", "asset_id"], [])),
    ("historian", (["asset_id", "recorded_at"], [])),
    ("output", (["work_order", "qty_good"], [])),
    ("inspection", (["measured", "nominal"], [])),
    ("routings", (["part_number", "op_seq"], [])),
    ("plan", (["part_number", "planned_qty"], [])),
    ("work_orders", (["work_order", "part_number", "qty_ordered", "status"], ["qty_good", "closed_date", "promised_date"])),
    ("sales_orders", (["sales_order", "part_number"], [])),
    ("customers", (["customer_id", "customer"], ["part_number", "ncr_id", "sales_order"])),
    ("items", (["part_number", "std_cost"], ["work_order", "op_seq"])),
    ("assets", (["asset_id", "location"], ["started_at", "maintenance_wo"])),
])

# Files the pulse recognises but does not read.
UNUSED_SIGNATURES = [
    ("purchase_orders", ["po_number"]), ("suppliers", ["supplier_name"]),
    ("bom", ["qty_per_piece"]), ("closed_job_costs", ["actual_material_cost"]), ("capacity", ["available_hours"]),
]


def resolve_columns(header, overrides=None):
    folded = {fold(h): h for h in header}
    cols = {}
    for canon, spellings in ALIASES.items():
        for s in spellings:
            if s in folded:
                cols[canon] = folded[s]
                break
    for canon, actual in (overrides or {}).items():
        if actual in header:
            cols[canon] = actual
    return cols


def recognise(header, overrides=None):
    cols = resolve_columns(header, overrides)
    folded = {fold(h) for h in header}
    for role, (must, must_not) in ROLES.items():
        if all(c in cols for c in must) and not any(c in cols and fold(cols[c]) in folded for c in must_not):
            # "description" doubles as reason text; only downtime keeps it.
            return role, cols
    for role, marks in UNUSED_SIGNATURES:
        if all(m in folded for m in marks):
            return "unused:" + role, cols
    return None, cols


class Table:
    def __init__(self, name, role, header, rows, cols):
        self.name, self.role, self.header, self.cols = name, role, header, cols
        self.rows = []
        for r in rows:
            if not any(str(v).strip() for v in r):
                continue
            rec = {h: (r[i] if i < len(r) else "") for i, h in enumerate(header)}
            self.rows.append(rec)

    def get(self, row, canon, default=""):
        c = self.cols.get(canon)
        return row.get(c, default) if c else default

    def has(self, canon):
        return canon in self.cols


def load_exports(folder, manifest):
    tables, skipped = {}, []
    role_override = (manifest or {}).get("roles", {})
    col_override = (manifest or {}).get("columns", {})
    for fn in sorted(os.listdir(folder)):
        path = os.path.join(folder, fn)
        if not os.path.isfile(path) or fn.startswith("."):
            continue
        low = fn.lower()
        if low.endswith(".csv"):
            sheets = {fn: read_csv(path)}
        elif low.endswith(".xlsx"):
            try:
                sheets = {"%s[%s]" % (fn, k): v for k, v in read_xlsx(path).items()}
            except Exception as e:  # noqa: BLE001 - report, never crash on one file
                skipped.append({"file": fn, "why": "could not read XLSX: %s" % e})
                continue
        else:
            skipped.append({"file": fn, "why": "not CSV or XLSX"})
            continue
        for name, rows in sheets.items():
            if not rows:
                skipped.append({"file": name, "why": "empty"})
                continue
            header = [h.strip() for h in rows[0]]
            forced = role_override.get(name) or role_override.get(fn)
            role, cols = recognise(header, col_override.get(forced) if forced else None)
            if forced:
                role = forced
                cols = resolve_columns(header, col_override.get(forced))
            else:   # a columns entry needs no roles entry: it applies to the file it makes recognisable as that role
                for want, over in col_override.items():
                    r2, c2 = recognise(header, over)
                    if r2 == want and any(v in header for v in over.values()):
                        role, cols = r2, c2
                        break
            if role is None:
                skipped.append({"file": name, "why": "header not recognised: " + ", ".join(header)})
                continue
            if role.startswith("unused:"):
                skipped.append({"file": name, "why": "recognised as %s; the pulse does not read it" % role[7:]})
                continue
            if role in tables:
                skipped.append({"file": name, "why": "second %s file; %s used" % (role, tables[role].name)})
                continue
            tables[role] = Table(name, role, header, rows[1:], cols)
    return tables, skipped


# --------------------------------------------------------------------------
# The plant profile (## Plant context)
# --------------------------------------------------------------------------

def parse_rates(path):
    """The downtime rate from the plant's rates file (## Plant rates, at
    plant_setup.py's rates_path). {downtime_rate, downtime_rate_kind} or {}."""
    if not path or not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    if not re.search(r"^##\s*Plant rates\s*$", text, re.M):
        return {}
    dc = re.search(r"[Dd]owntime cost per hour[:*| \t]*(?:[A-Za-z]+[ \t]+)?[$~]?[ \t]*(\d[\d,]*(?:\.\d+)?)", text)
    if not dc or "not set" in dc.group(0):
        return {}
    return {"downtime_rate": float(dc.group(1).replace(",", "")),
            "downtime_rate_kind": "profile_placeholder" if "placeholder" in dc.group(0).lower() else "profile_confirmed"}


def parse_profile(path):
    if not path or not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^##\s*Plant context\s*$(.*?)(?=^##\s(?!#)|\Z)", text, re.M | re.S)
    if not m:
        return None
    body = m.group(1)
    p = {"source": path}

    def field(label):
        mm = re.search(r"\*\*%s:\*\*\s*(.+)" % re.escape(label), body)
        return mm.group(1).strip() if mm else None

    p["company"] = field("Company")
    sites = field("Sites")
    if sites:
        names = [x for x in re.split(r"\s+-\s+|,", sites) if x.strip()] or [sites]
        p["site"] = re.sub(r"\s*\(default\)", "", next((x for x in names if "(default)" in x), names[0])).strip()
    tz = field("Time zone") or field("Timezone")
    if tz:
        p["tz"] = tz.split()[0]
    ds = field("Production day")
    if ds and re.match(r"^\d{4}-\d{2}-\d{2}$", ds):
        p["production_day"] = ds
        ds = None
    if ds:
        mm = re.search(r"starts\s+(\d{1,2}:\d{2})", ds)
        if mm:
            p["day_start"] = mm.group(1)
        p["day_boundary_text"] = ds
    mm = re.match(r"\d{1,2}:\d{2}", field("Production day starts") or "")
    if mm:
        p.setdefault("day_start", mm.group(0))
    ppt = field("Planned production time")
    if ppt:
        mm = re.search(r"([\d.]+)\s*hours?\s*per\s*shift", ppt)
        if mm:
            p["planned_hours_per_shift"] = float(mm.group(1))
        p["planned_production_time_text"] = ppt
    shifts = field("Shifts")
    if shifts:
        p["shifts"] = re.findall(r"(\d{1,2}:\d{2})\s*-\s*\d{1,2}:\d{2}", shifts)
    elif field("Shift pattern"):
        p["shifts"] = re.findall(r"\d{1,2}:\d{2}", field("Shift pattern"))
    rates = field("Rates") or ""
    dc = re.search(r"[Dd]owntime cost per hour[:*| \t]*(?:[A-Za-z]+[ \t]+)?[$~]?[ \t]*(\d[\d,]*(?:\.\d+)?)", body)
    if dc and "not set" not in dc.group(0):
        p["downtime_rate"] = float(dc.group(1).replace(",", ""))
        p["downtime_rate_kind"] = "profile_placeholder" if "placeholder" in dc.group(0).lower() else "profile_confirmed"
    p["rates_text"] = rates
    # Approved normalizations: lines like - `4471B` -> `PN-4471-B`
    ap = re.search(r"^###\s*Approved normalizations\s*$(.*?)(?=^###|\Z)", body, re.M | re.S)
    p["approved"] = {}
    if ap:
        for a, b in re.findall(r"`([^`]+)`\s*(?:->|→|=>)\s*`([^`]+)`", ap.group(1)):
            p["approved"][a] = b
        for line in ap.group(1).splitlines():
            ticks = re.findall(r"`([^`]*)`", line)
            if line.strip().startswith("|") and len(ticks) >= 2:
                p["approved"][ticks[0]] = ticks[1]
    # Reason codes table
    rc = re.search(r"^###\s*Reason codes\s*$(.*?)(?=^###|\Z)", body, re.M | re.S)
    p["reason_codes"] = {}
    if rc:
        for code, meaning in re.findall(r"^\|\s*([^|\s][^|]*?)\s*\|\s*([^|]+?)\s*\|\s*$", rc.group(1), re.M):
            if code.lower() not in ("code", "---", "-") and not set(code) <= set("-: "):
                p["reason_codes"][code] = meaning
    # Machine classes: work centers -> cell
    p["cells"] = {}
    mc = re.search(r"Machine classes:(.*?)(?=^###|\Z)", body, re.M | re.S)
    if mc:
        for line in mc.group(1).splitlines():
            parts = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(parts) >= 3 and parts[0] and not set(parts[0]) <= set("-: ") and parts[0] != "Machine class":
                for wc in parts[1].split(","):
                    p["cells"][wc.strip()] = parts[2].split(",")[0].strip()
    return p


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------

class Figures:
    def __init__(self):
        self.rows = []
        self.ids = set()

    def add(self, fid, label, value, source, filt, period="window", unit=""):
        if fid in self.ids:
            raise ValueError("duplicate figure id " + fid)
        self.ids.add(fid)
        self.rows.append({"id": fid, "figure": label, "value": value, "unit": unit,
                          "period": period, "source": source, "filter": filt})
        return value

    SHORT_PREFIXES = ("sp-", "decision.", "remaining.", "per.sp-", "dt.sp-")

    def write(self, path, short_path=None):
        """figures.csv holds the full page's rows; the short page's view roll-ups go to short_path."""
        full = [r for r in self.rows if not r["id"].startswith(self.SHORT_PREFIXES)]
        short = [r for r in self.rows if r["id"].startswith(self.SHORT_PREFIXES)]
        self._write(path, full)
        if short_path and short:
            self._write(short_path, short)

    @staticmethod
    def _write(path, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["id", "figure", "value", "unit", "period", "source", "filter"])
            w.writeheader()
            for r in rows:
                v = r["value"]
                if v is None:
                    v = "not computable"
                elif isinstance(v, float):
                    v = ("%.4f" % v).rstrip("0").rstrip(".")
                w.writerow(dict(r, value=v))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def num(s):
    s = str(s).strip().replace(",", "")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def intish(x):
    return int(x) if x is not None and float(x).is_integer() else x


def excel_serial(s):
    """A date cell read from XLSX arrives as its serial number (days since 1899-12-30)."""
    if re.match(r"^\d{5}(\.\d+)?$", s):
        return datetime(1899, 12, 30) + timedelta(seconds=round(float(s) * 86400))
    return None


def parse_ts(s, tz):
    s = str(s).strip()
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        d = excel_serial(s)
        if d is None:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=tz)
    return d.astimezone(tz)


def parse_day(s):
    s = str(s).strip()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        d = excel_serial(s)
        return d.date() if d else None


def hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def local_str(d):
    return d.strftime("%Y-%m-%d %H:%M") + " (plant local)" if d else None


def comp_rank(items, key):
    """Competition ranking: 1, 2, 2, 4. items sorted by key descending."""
    ranks, prev, r = [], object(), 0
    for i, it in enumerate(items):
        k = key(it)
        if k != prev:
            r = i + 1
            prev = k
        ranks.append(r)
    return ranks


def week_of(d):
    start = d - timedelta(days=d.weekday())
    return start, start + timedelta(days=6)


# --------------------------------------------------------------------------
# The normalization ladder, toward the item master
# --------------------------------------------------------------------------

REV_RE = re.compile(r"\s*(?:rev\.?|revision|r)\s*[-.]?\s*([A-Za-z0-9]+)\s*$", re.I)


def punct(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


class Ladder:
    """Rungs 1-5 of join-keys.md. Returns (canonical, class, rule, revision)."""

    def __init__(self, master, approved):
        self.master = list(master)
        self.set = set(self.master)
        self.approved = approved or {}
        self.cache = {}

    def match(self, raw):
        if raw in self.cache:
            return self.cache[raw]
        res = self._match(raw)
        self.cache[raw] = res
        return res

    def _match(self, raw):
        if raw in self.set:
            return raw, None, None, None
        if raw in self.approved and self.approved[raw] in self.set:
            return self.approved[raw], "approved", "approved normalization", None
        t = raw.strip()
        if t in self.set:
            return t, 5, "trim whitespace", None
        for m in self.master:
            if t.lower() == m.lower():
                return m, 5, "trim whitespace and fold case" if t != raw else "fold case", None
        key = punct(t)
        hits = [m for m in self.master if punct(m) == key]
        if len(hits) == 1:
            return hits[0], 2, "normalize punctuation", None
        prefixed = [m for m in self.master if re.match(r"^[A-Za-z]+[-_ ]", m)
                    and punct(re.sub(r"^[A-Za-z]+[-_ ]", "", m)) == key]
        if len(prefixed) == 1:
            pre = re.match(r"^([A-Za-z]+)[-_ ]", prefixed[0]).group(1)
            return prefixed[0], 2, "normalize punctuation; prefix %s- restored" % pre, None
        if len(prefixed) > 1:
            return None, 1, "ambiguous: " + ", ".join(prefixed), None
        if t.isdigit():
            pad = [m for m in self.master if m.isdigit() and len(m) > len(t) and m.lstrip("0") == t.lstrip("0")]
            if len(pad) == 1:
                return pad[0], 3, "restore leading zeros to width %d" % len(pad[0]), None
        rv = REV_RE.search(t)
        if rv:
            base = t[:rv.start()].strip()
            sub = self._match(base) if base != t else (None, None, None, None)
            if sub[0]:
                return sub[0], 4, "strip revision suffix (Rev %s kept in its own column)" % rv.group(1), rv.group(1)
        return None, 1, "no rung matches the item master", None


# --------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------

class Pulse:
    def __init__(self, args):
        self.args = args
        self.F = Figures()
        self.manifest = json.load(open(args.manifest)) if args.manifest else {}
        self.profile = parse_profile(args.profile)
        rates = parse_rates(getattr(args, "rates", None))
        if rates:   # the rates file wins over a value left in an older profile
            self.profile = dict(self.profile or {}, **rates)
        p = self.profile or {}
        self.assumptions = []
        tzname = args.tz or p.get("tz")
        if not tzname:
            tzname = DEFAULT_TZ
            self.assumptions.append("Times are plant local, assumed %s; %s." % (
                tzname, "the plant profile sets no time zone" if self.profile else "no plant profile"))
        self.tzname = tzname
        self.tz = ZoneInfo(tzname) if ZoneInfo else timezone(timedelta(hours=-4))
        self.run_time = parse_ts(args.run_time, self.tz) if args.run_time else datetime.now(self.tz)
        self.T, self.skipped = load_exports(args.exports, self.manifest)
        self.model = OrderedDict()
        self.checks = []

    # -- small accessors -------------------------------------------------
    def t(self, role):
        return self.T.get(role)

    def check(self, ok, what):
        self.checks.append({"check": what, "ok": bool(ok)})

    # -- context -----------------------------------------------------------
    def context(self):
        p = self.profile or {}
        out = self.t("output")
        site = p.get("site")
        if not site:
            for role in ("output", "work_orders", "plan", "items"):
                tb = self.t(role)
                if tb and tb.has("site"):
                    vals = {tb.get(r, "site") for r in tb.rows if tb.get(r, "site")}
                    if len(vals) == 1:
                        site = vals.pop()
                        break
        self.site = site or "Plant"
        # One run reports one site: other sites' rows in a shared export are left out, and the run says so.
        seen = sorted({tb.get(r, "site").strip() for tb in self.T.values() if tb.has("site") for r in tb.rows} - {""})
        if len(seen) > 1 and self.site.lower() in [s.lower() for s in seen]:
            for tb in self.T.values():
                if tb.has("site"):
                    tb.rows = [r for r in tb.rows if tb.get(r, "site").strip().lower() in ("", self.site.lower())]
            self.assumptions.append("The exports carry more than one site (%s); only %s rows are used." % (", ".join(seen), self.site))
        elif len(seen) > 1:
            self.assumptions.append("The exports carry more than one site (%s) and none is %s; their rows are pooled." % (
                ", ".join(seen), self.site))
        elif seen and seen[0].lower() != self.site.lower():
            self.assumptions.append("The exports are marked site %s, not %s, the site this run reports under; check which "
                                    "site the export is for." % (seen[0], self.site))
        # Day start: the profile's, else the earliest shift label in the MES.
        if p.get("day_start"):
            self.day_start = p["day_start"]
            self.day_rule = p.get("day_boundary_text") or "day starts %s" % self.day_start
        else:
            why = "the plant profile sets no day start" if self.profile else "no plant profile"
            shifts = sorted({out.get(r, "shift") for r in out.rows if re.match(r"^\d{1,2}:\d{2}$", out.get(r, "shift"))},
                            key=hm) if out and out.has("shift") else []
            self.day_start = shifts[0] if shifts else "00:00"
            self.day_rule = ("day starts %s, the earliest MES shift; a shift belongs to the production day it "
                             "starts on (assumed; %s)" % (self.day_start, why)) if shifts else \
                ("calendar day, plant local (assumed; %s and no MES shift labels)" % why)
            self.assumptions.append("Production-day rule: " + self.day_rule + ".")
        self.model["context"] = OrderedDict([
            ("engine_version", ENGINE_VERSION), ("site", self.site),
            ("company", p.get("company")), ("profile", bool(self.profile)),
            ("profile_source", p.get("source")), ("time_zone", self.tzname),
            ("time_zone_assumed", not (self.args.tz or p.get("tz"))),
            ("day_start", self.day_start), ("day_boundary", self.day_rule),
            ("run_time", self.run_time.isoformat()), ("run_time_local", local_str(self.run_time)),
            ("assumptions", self.assumptions),
            ("files_used", {r: tb.name for r, tb in self.T.items()}),
            ("files_not_used", self.skipped),
        ])

    def prod_day_of(self, ts):
        """Production day for a plant-local timestamp under the day-start rule."""
        return (ts - timedelta(minutes=hm(self.day_start))).date()

    # -- normalization -------------------------------------------------------
    def normalize(self):
        items = self.t("items")
        self.master = OrderedDict()
        self.master_source = None
        if items:
            for r in items.rows:
                self.master[items.get(r, "part_number").strip()] = r
            self.master_source = items.name + " (item master)"
        else:
            # No item master: the ERP work orders, then the plan, stand in, and the page says so.
            for role in ("work_orders", "plan"):
                tb = self.t(role)
                if tb and tb.has("part_number"):
                    for r in tb.rows:
                        self.master.setdefault(tb.get(r, "part_number").strip(), {})
                    self.master_source = "%s part numbers (no item master in the drop)" % tb.name
                    break
        approved = (self.profile or {}).get("approved", {})
        approved.update(self.manifest.get("approved_normalizations", {}))
        self.ladder = Ladder(self.master.keys(), approved)
        self.norm_log = OrderedDict()
        self.unmatched_parts = OrderedDict()
        for role in ("plan", "output", "work_orders", "inspection", "ncrs", "sales_orders", "routings"):
            tb = self.t(role)
            if not tb or not tb.has("part_number"):
                continue
            for r in tb.rows:
                raw = tb.get(r, "part_number")
                canon, cls, rule, rev = self.ladder.match(raw) if self.master else (raw, None, None, None)
                r["_part"] = canon
                r["_part_class"] = cls
                r["_part_verbatim"] = raw
                r["_provisional"] = cls in (2, 3, 4, 5)
                if rev:
                    r["_revision_stripped"] = rev
                if cls in (2, 3, 4, 5, "approved"):
                    k = (tb.name, raw)
                    e = self.norm_log.setdefault(k, OrderedDict([
                        ("source", tb.name), ("role", role), ("verbatim", raw), ("canonical", canon),
                        ("class", cls), ("rule", rule), ("status", "approved" if cls == "approved" else
                                                          "proposed, awaiting approval"), ("rows", 0)]))
                    e["rows"] += 1
                elif cls == 1 and role in ("plan", "output", "inspection", "ncrs", "sales_orders"):
                    k = (tb.name, raw)
                    e = self.unmatched_parts.setdefault(k, {"source": tb.name, "verbatim": raw, "why": rule, "rows": 0})
                    e["rows"] += 1
        for n, e in enumerate(self.norm_log.values()):
            self.F.add("norm.%d.rows" % n, "Rows resting on %s normalization %r -> %s (%s)" % (
                e["status"].split(",")[0], e["verbatim"], e["canonical"], e["rule"]), e["rows"], e["source"],
                "part_number == %r" % e["verbatim"])
        self.model["normalizations"] = list(self.norm_log.values())
        self.model["context"]["part_reference"] = self.master_source

    # -- freshness and coverage -------------------------------------------------
    def freshness(self):
        req = self.args.day or (self.profile or {}).get("production_day")
        cov = OrderedDict()
        spec = [("plan", "plan_date", "date"), ("output", "production_day", "date"),
                ("downtime", "started_at", "ts"), ("inspection", "production_day", "date"),
                ("ncrs", "found_at", "ts"), ("maintenance", "opened_date", "date"),
                ("work_orders", "due_date", "date"), ("sales_orders", "promised_date", "date"),
                ("historian", "recorded_at", "ts")]
        newest_ts = None
        landed_dt = {}
        future = []
        unread = {}
        for role, col, kind in spec:
            tb = self.t(role)
            if not tb or not tb.has(col):
                continue
            days = []
            for r in tb.rows:
                v = tb.get(r, col)
                if str(v).strip() and (parse_ts(v, self.tz) if kind == "ts" else parse_day(v)) is None:
                    unread.setdefault(role, []).append(str(v).strip())
                if kind == "ts":
                    d = parse_ts(v, self.tz)
                    if d is None:
                        continue
                    if role in ("downtime", "historian", "ncrs"):
                        newest_ts = d if newest_ts is None or d > newest_ts else newest_ts
                        if d > self.run_time:
                            future.append({"source": tb.name, "value": v})
                    days.append(self.prod_day_of(d) if role == "downtime" else d.date())
                else:
                    d = parse_day(v)
                    if d:
                        days.append(d)
            if days:
                path = os.path.join(self.args.exports, tb.name.split("[")[0])
                mtime = datetime.fromtimestamp(os.path.getmtime(path), self.tz) if os.path.exists(path) else None
                landed_dt[role] = mtime
                cov[role] = OrderedDict([("file", tb.name), ("first", str(min(days))), ("last", str(max(days))),
                                         ("rows", len(tb.rows)), ("landed", local_str(mtime)),
                                         ("activity", role in ("plan", "output", "downtime", "inspection"))])
        man = self.t("drop_manifest")
        if man:
            for r in man.rows:
                fn = man.get(r, "source_file").strip()
                for c in cov.values():
                    if c["file"] == fn:
                        g = parse_ts(man.get(r, "generated_at"), self.tz)
                        c["landed"] = local_str(g)
                        c["landed_source"] = "drop manifest generated_at"
                        for role_, c_ in cov.items():
                            if c_ is c and g:
                                landed_dt[role_] = g
                        if g:
                            c["landed_days_before_run"] = (self.run_time.date() - g.date()).days
        for role, c in cov.items():
            self.F.add("cov.%s" % role, "Coverage, %s" % c["file"], "%s to %s" % (c["first"], c["last"]), c["file"],
                       "min/max of the date column")
        act = [c for c in cov.values() if c["activity"]]
        # A plan looks forward, so output and downtime date the data; the plan only when neither landed, never past the run date.
        run_day = self.run_time.date()
        newest_day = max((min(date.fromisoformat(cov[r]["last"]), run_day) for r in ("output", "downtime") if r in cov),
                         default=min(date.fromisoformat(cov["plan"]["last"]), run_day) if "plan" in cov else None)
        day = date.fromisoformat(req) if req else None
        need = ("plan", "output", "downtime")
        if day is None:
            # Latest production day every needed export covers; else the newest any covers.
            ends = [date.fromisoformat(cov[r]["last"]) for r in need if r in cov]
            day = min(ends) if len(ends) == len(need) else newest_day
            self.day_source = "latest complete production day in the exports (no day requested)"
        else:
            self.day_source = "requested" if self.args.day else "set in the plant context"
        self.day = day
        missing = [r for r in need if r not in self.T]
        not_cover = [r for r in need if r in cov and not (cov[r]["first"] <= str(day) <= cov[r]["last"])]
        gaps = []
        names = {"plan": "planning export", "output": "production (MES output) export", "downtime": "downtime export"}
        for r in missing:
            gaps.append("%s did not land" % names[r])
        for r in not_cover:
            gaps.append("%s has no rows for %s (covers %s to %s)" % (names[r], day, cov[r]["first"], cov[r]["last"]))
        for r in need:
            if unread.get(r):   # rows whose date cannot be read are in no day: a gap, never silence
                gaps.append("%s has %d rows whose date could not be read (first: %r); dates must be YYYY-MM-DD" % (
                    names[r], len(unread[r]), unread[r][0]))
        for r in need:   # recognised, has rows, but no date column resolved (or it is blank): its rows are in no day
            if self.t(r) and self.t(r).rows and r not in cov and not unread.get(r):
                gaps.append("%s has no readable date column, so none of its rows can be placed in a production day" % names[r])
        self.data_complete = not gaps
        # Activity window intersection (class 7 reference)
        inter = None
        if act:
            lo = max(c["first"] for c in act)
            hi = min(c["last"] for c in act)
            inter = (lo, hi) if lo <= hi else None
        age = (self.run_time.date() - newest_day).days if newest_day else None
        # The newest refresh the figures rest on: when the activity exports landed (manifest, else file time).
        landed = [landed_dt[r] for r in ("plan", "output", "downtime") if landed_dt.get(r)]
        as_of = max(landed) if landed else newest_ts
        as_of_basis = "when the plan, output and downtime exports landed (drop manifest, else file time)" if landed \
            else ("newest event timestamp in the exports" if newest_ts else "no source could be dated")
        self.model["freshness"] = OrderedDict([
            ("production_day", str(day) if day else None), ("day_source", self.day_source),
            ("newest_production_day", str(newest_day) if newest_day else None),
            ("days_old", age), ("data_as_of", as_of.isoformat() if as_of else None),
            ("data_as_of_local", local_str(as_of)), ("data_as_of_basis", as_of_basis),
            ("newest_event", local_str(newest_ts)), ("data_complete", self.data_complete), ("gaps", gaps),
            ("coverage", cov), ("activity_window", list(inter) if inter else None),
            ("future_timestamps", future),
            ("sources_disagree", len({(c["first"], c["last"]) for c in act}) > 1),
        ])
        self.F.add("fresh.days_old", "Days between the newest production day and the run date", age,
                   "run clock vs exports", "run date - newest production day")
        self.F.add("fresh.future", "Records timestamped after the run time (future_timestamp)", len(future),
                   "downtime, historian, NCR exports", "timestamp > run time; due and promised dates excluded")
        if day:
            self.F.add("fresh.day", "Production day reported", str(day), "exports", self.day_source)
        self.window = (date.fromisoformat(inter[0]), date.fromisoformat(inter[1])) if inter else None

    # -- production output and the work order join --------------------------
    def output(self):
        out, wos = self.t("output"), self.t("work_orders")
        self.WO = OrderedDict()
        if wos:
            for r in wos.rows:
                self.WO[wos.get(r, "work_order").strip()] = r
        self.out_rows = []
        self.dup_list = []
        self.unit_conflicts = OrderedDict()
        self.shared_lots = {}
        self.unit_ref, self.unit_ref_short = None, "item master"
        problems, integrity = [], defaultdict(list)
        if not out:
            self.model["output_rows"] = None
            self.problems, self.integrity = problems, integrity
            return
        items = self.t("items")
        self.unit_ref = "item master" if items and items.has("uom") else None
        dominant = None
        if not self.unit_ref and out.has("uom"):
            c = Counter(out.get(r, "uom").strip() for r in out.rows if out.get(r, "uom").strip())
            if c:
                dominant = c.most_common(1)[0][0]
                self.unit_ref = "the unit most MES rows carry (%s); no item master in the drop, so unconfirmed" % dominant
        self.model["context"]["unit_reference"] = self.unit_ref
        self.unit_ref_short = "item master" if self.unit_ref == "item master" else "rest of the MES (no item master)"
        grain = defaultdict(list)
        for i, r in enumerate(out.rows):
            wo = out.get(r, "work_order").strip()
            day = parse_day(out.get(r, "production_day"))
            good = num(out.get(r, "qty_good"))
            scrap_raw = out.get(r, "qty_scrap") if out.has("qty_scrap") else None
            scrap = num(scrap_raw) if scrap_raw is not None else None
            unit = out.get(r, "uom").strip() if out.has("uom") else None
            part = r.get("_part")
            item_unit = (self.master.get(part, {}).get(items_col(items, "uom"), None) if part and items else dominant)
            rec = OrderedDict([
                ("i", i), ("work_order", wo), ("part", part_key(r)), ("part_verbatim", r.get("_part_verbatim")),
                ("part_class", r.get("_part_class")), ("provisional", r.get("_provisional", False)),
                ("good", good), ("scrap", scrap), ("scrap_recorded", scrap is not None),
                ("scrap_column", out.has("qty_scrap")), ("rework", num(out.get(r, "qty_rework")) if out.has("qty_rework") else None),
                ("unit", unit), ("item_unit", item_unit),
                ("unit_conflict", bool(unit and item_unit and unit.strip().lower() != str(item_unit).strip().lower())),
                ("shift", out.get(r, "shift")), ("day", str(day) if day else None),
                ("lot", out.get(r, "lot_number").strip() if out.has("lot_number") else None),
                ("asset", out.get(r, "asset_id").strip() if out.has("asset_id") else None),
                ("cell", out.get(r, "cell").strip() if out.has("cell") else None),
                ("in_erp", wo in self.WO), ("held_out", None if good is not None else "no readable good quantity")])
            self.out_rows.append(rec)
            grain[(wo, rec["shift"], rec["day"])].append(rec)
        # Class 8 at the tab's grain: work order, shift, production day.
        dups = []
        for (wo, sh, d), rs in grain.items():
            if len(rs) > 1:
                for x in rs:
                    x["held_out"] = "duplicate key"
                allrows = [x for x in self.out_rows if x["work_order"] == wo]
                dups.append(OrderedDict([
                    ("work_order", wo), ("shift", sh), ("day", d), ("rows_for_key", len(allrows)),
                    ("rows_colliding", len(rs)), ("good_values", [intish(x["good"]) for x in rs]),
                    ("other_rows", [OrderedDict([("shift", x["shift"]), ("day", x["day"]), ("good", intish(x["good"]))])
                                    for x in allrows if x not in rs])]))
        for n, d in enumerate(dups):
            allvals = [intish(x["good"]) for x in self.out_rows if x["work_order"] == d["work_order"]]
            d["all_good_values"] = allvals
            self.F.add("dup.%d.values" % n, "Good on every row of %s" % d["work_order"], " / ".join(str(v) for v in allvals),
                       out.name, "work_order == %r; none picked or summed" % d["work_order"])
            self.F.add("dup.%d.rows" % n, "Class 8: rows for %s (all shifts)" % d["work_order"], d["rows_for_key"],
                       out.name, "work_order == %r" % d["work_order"])
            self.F.add("dup.%d.colliding" % n, "Class 8: rows colliding at %s %s %s" % (d["work_order"], d["day"], d["shift"]),
                       d["rows_colliding"], out.name, "work_order, shift and production_day equal; good " +
                       " / ".join(str(g) for g in d["good_values"]))
            problems.append(OrderedDict([
                ("class", 8), ("name", "Duplicate key"), ("key", d["work_order"]),
                ("what", "%s has %d MES rows; %d collide on %s at %s (good %s, none picked or summed)%s" % (
                    d["work_order"], d["rows_for_key"], d["rows_colliding"], d["day"], d["shift"],
                    " / ".join(str(g) for g in d["good_values"]),
                    "; " + "; ".join("the %s on the %s shift is its own shift" % (o["good"], o["shift"]) for o in d["other_rows"])
                    if d["other_rows"] else "")),
                ("rows", d["rows_colliding"]), ("fix", "None automatic. Both rows held out of every total until someone says which is real.")]))
        self.dup_list = dups
        # Lot on two different parts: class 8. Same lot across work orders of one part is traceability, not a duplicate.
        lot_parts = defaultdict(set)
        lot_wos = defaultdict(set)
        for x in self.out_rows:
            if x["lot"]:
                lot_parts[x["lot"]].add(x["part"])
                lot_wos[x["lot"]].add(x["work_order"])
        for lot, parts in lot_parts.items():
            if len(parts) > 1:
                problems.append(OrderedDict([("class", 8), ("name", "Duplicate key"), ("key", lot),
                                             ("what", "Lot %s is on %d different parts: %s" % (lot, len(parts), ", ".join(sorted(map(str, parts))))),
                                             ("rows", sum(1 for x in self.out_rows if x["lot"] == lot)),
                                             ("fix", "None automatic. The plant says which part the lot belongs to.")]))
        self.shared_lots = {l: sorted(w) for l, w in lot_wos.items() if len(w) > 1 and len(lot_parts[l]) == 1}
        # Class 1: output against a work order the ERP does not hold.
        if wos:
            orphans = [x for x in self.out_rows if not x["in_erp"]]
            self.F.add("orphan.count", "Class 1: MES rows whose production work order is not in the ERP", len(orphans),
                       out.name + " vs " + wos.name, "work_order not in ERP")
            for x in orphans:
                x["held_out"] = x["held_out"] or "orphan"
                problems.append(OrderedDict([
                    ("class", 1), ("name", "Orphan record"), ("key", x["work_order"]),
                    ("what", "%s in the MES (%s, %s good, %s, %s shift) is not in the ERP" % (
                        x["work_order"], x["part_verbatim"], fmtq(x["good"]), x["day"], x["shift"])),
                    ("rows", 1), ("fix", "None automatic: an unauthorized job, a deleted order, or a typo. A question for whoever ran that shift.")]))
            # Part on the MES row disagrees with the ERP work order's part.
            for x in self.out_rows:
                if x["in_erp"] and x["part_verbatim"] and x["part_class"] != 1:
                    erp_part = self.WO[x["work_order"]].get("_part")
                    if erp_part and erp_part != x["part"]:
                        integrity["mes_part_differs"].append(x)
        # Unit conflicts and absent scrap.
        units = defaultdict(set)
        for x in self.out_rows:
            if x["unit_conflict"]:
                units[x["part"]].add(x["unit"])
        self.unit_conflicts = OrderedDict()
        for part, us in units.items():
            n = sum(1 for x in self.out_rows if x["part"] == part and x["unit_conflict"])
            item_unit = next(x["item_unit"] for x in self.out_rows if x["part"] == part)
            self.unit_conflicts[part] = OrderedDict([("export_units", sorted(us)), ("item_unit", item_unit), ("rows", n)])
            self.F.add("unit.%s" % part, "units_conflict rows: %s, MES %s vs %s %s" % (part, "/".join(sorted(us)), self.unit_ref_short, item_unit),
                       n, out.name + " vs " + self.unit_ref_short, "part == %r and uom != %r" % (part, item_unit))
            problems.append(OrderedDict([
                ("class", "units"), ("name", "Unit conflict"), ("key", part),
                ("what", "%s is counted in %s in the MES and %s in the %s; no conversion factor on file" % (
                    part, "/".join(sorted(us)), item_unit, self.unit_ref_short)),
                ("rows", n), ("fix", "Waiting on a decision: how many %s per %s. Until then no variance, no price." % (item_unit, "/".join(sorted(us))))]))
        blank_scrap = [x for x in self.out_rows if not x["scrap_recorded"]]
        self.F.add("scrap.absent_rows", "MES rows with no scrap recorded (absent, not zero)", len(blank_scrap), out.name,
                   "qty_scrap blank or column missing")
        missing_lot = [x for x in self.out_rows if out.has("lot_number") and not x["lot"]]
        for x in missing_lot:
            integrity["blank_lot"].append(x)
        self.problems, self.integrity = problems, integrity

    # -- downtime ----------------------------------------------------------
    def downtime(self):
        dt = self.t("downtime")
        self.events = []
        if not dt:
            self.load_diagnoses()
            return
        for i, r in enumerate(dt.rows):
            s = parse_ts(dt.get(r, "started_at"), self.tz)
            e = parse_ts(dt.get(r, "ended_at"), self.tz) if dt.has("ended_at") else None
            stated = num(dt.get(r, "duration_minutes")) if dt.has("duration_minutes") else None
            code_raw = dt.get(r, "reason_code").strip() if dt.has("reason_code") else ""
            flags = []
            minutes = None
            if s is None:
                flags.append("no_start")
            elif e is None and not stated:
                flags.append("ongoing")
            elif e is None:
                minutes = stated   # a start and a stated length: finished, with no end time written
            else:
                span = (e.astimezone(timezone.utc) - s.astimezone(timezone.utc)).total_seconds() / 60.0
                if span < 0:
                    flags.append("end_before_start")
                elif stated is not None and abs(stated - span) > 1:
                    flags.append("duration_mismatch")
                else:
                    minutes = stated if stated is not None else span
            uncoded = code_raw == "" or code_raw.lower() == "other"
            self.events.append(OrderedDict([
                ("i", i), ("asset", dt.get(r, "asset_id").strip()), ("start", s), ("end", e),
                ("start_local", local_str(s)), ("end_local", local_str(e)),
                ("day", str(self.prod_day_of(s)) if s else None), ("stated_minutes", stated),
                ("minutes", minutes), ("flags", flags), ("code", code_raw or "(blank)"),
                ("uncoded", uncoded), ("text", dt.get(r, "reason_text") if dt.has("reason_text") else ""),
                ("blocked", None)]))
        # breakdown-diagnosis contract records, when handed in
        self.load_diagnoses()

    def load_diagnoses(self):
        self.diagnoses = []
        folder = self.args.diagnoses or os.path.join(self.args.exports, "diagnoses")
        if not os.path.isdir(folder):
            return
        for fn in sorted(os.listdir(folder)):
            path = os.path.join(folder, fn)
            try:
                if fn.endswith(".json"):
                    d = json.load(open(path))
                    recs = d if isinstance(d, list) else [d]
                elif fn.endswith((".yaml", ".yml")):
                    recs = [read_flat_yaml(path)]
                else:
                    continue
            except ValueError:
                self.skipped.append({"file": fn, "why": "diagnosis record could not be read"})
                continue
            for rec in recs:
                rec["_file"] = fn
                self.diagnoses.append(rec)

    def rank_events(self, evs, label, period):
        """Both rankings, by asset and by named reason code, for a set of events."""
        trusted = [e for e in evs if e["minutes"] is not None and not e["blocked"]]
        ranked = [e for e in evs if not e["blocked"]]
        def agg(key, pool):
            g = OrderedDict()
            for e in pool:
                k = key(e)
                a = g.setdefault(k, OrderedDict([("key", k), ("events", 0), ("minutes", 0.0), ("ongoing", 0),
                                                 ("held_out", 0)]))
                a["events"] += 1
                if "ongoing" in e["flags"]:
                    a["ongoing"] += 1
                elif e["minutes"] is None:
                    a["held_out"] += 1
                else:
                    a["minutes"] += e["minutes"]
            rows = list(g.values())
            for a in rows:
                a["minutes"] = intish(a["minutes"])
            by_min = sorted(rows, key=lambda a: (-a["minutes"], -a["events"], str(a["key"])))
            rm = comp_rank(by_min, lambda a: a["minutes"])
            by_ev = sorted(rows, key=lambda a: (-a["events"], -a["minutes"], str(a["key"])))
            re_ = comp_rank(by_ev, lambda a: a["events"])
            rank_m = {a["key"]: r for a, r in zip(by_min, rm)}
            rank_e = {a["key"]: r for a, r in zip(by_ev, re_)}
            for a in rows:
                a["rank_minutes"] = rank_m[a["key"]]
                a["rank_events"] = rank_e[a["key"]]
            return by_min
        assets = agg(lambda e: e["asset"], ranked)
        codes = agg(lambda e: e["code"], [e for e in ranked if not e["uncoded"]])
        other = [e for e in ranked if e["uncoded"]]
        out = OrderedDict([
            ("label", label), ("events", len(ranked)),
            ("minutes", intish(sum(e["minutes"] for e in trusted))),
            ("ongoing", sum(1 for e in ranked if "ongoing" in e["flags"])),
            ("held_out", [OrderedDict([("asset", e["asset"]), ("start", e["start_local"]), ("end", e["end_local"]),
                                       ("stated_minutes", intish(e["stated_minutes"])), ("flags", e["flags"])])
                          for e in ranked if e["minutes"] is None and "ongoing" not in e["flags"]]),
            ("uncoded_events", len(other)),
            ("uncoded_minutes", intish(sum(e["minutes"] for e in other if e["minutes"] is not None))),
            ("by_asset", assets), ("by_code", codes),
        ])
        f = self.F
        p = "dt.%s" % label
        f.add(p + ".events", "Downtime events [%s]" % label, out["events"], "downtime export", period, period=label)
        f.add(p + ".minutes", "Downtime minutes, trusted rows only [%s]" % label, out["minutes"], "downtime export",
              period + "; minutes held out for end_before_start, duration_mismatch and ongoing", period=label)
        f.add(p + ".ongoing", "Ongoing events, length unknown [%s]" % label, out["ongoing"], "downtime export",
              period + "; no end time", period=label)
        f.add(p + ".held", "Events with untrusted minutes [%s]" % label, len(out["held_out"]), "downtime export",
              period + "; end_before_start or duration_mismatch", period=label)
        f.add(p + ".uncoded_events", "Events coded Other or blank [%s]" % label, out["uncoded_events"], "downtime export",
              period + "; reason_code in ('Other', '')", period=label)
        f.add(p + ".uncoded_minutes", "Minutes coded Other or blank [%s]" % label, out["uncoded_minutes"], "downtime export",
              period + "; reason_code in ('Other', ''); trusted rows", period=label)
        if out["events"]:
            f.add(p + ".uncoded_pct", "Share of events coded Other or blank [%s]" % label,
                  round(100.0 * out["uncoded_events"] / out["events"]), "downtime export", "uncoded / events", period=label, unit="%")
        f.add(p + ".uncoded_min_pct", "Share of minutes coded Other or blank [%s]" % label,
              round(100.0 * out["uncoded_minutes"] / out["minutes"]) if out["minutes"] else None, "downtime export",
              "uncoded minutes / minutes; not computable with no recorded minutes", period=label, unit="%")
        if label.startswith("sp-"):
            for kind, rows in (("asset", assets), ("code", codes)):
                for a in rows:
                    for fld in ("events", "minutes", "ongoing", "held_out", "rank_minutes", "rank_events"):
                        f.add("%s.%s.%s.%s" % (p, kind, a["key"], fld), "%s %s, %s [%s]" % (kind, a["key"], fld, label), a[fld],
                              "downtime export", period + "; %s == %r" % (kind, a["key"]), period=label)
            assets_c, codes_c = [], []
        else:
            assets_c, codes_c = assets, codes
        for a in assets_c:
            f.add("%s.asset.%s" % (p, a["key"]), "Downtime on %s [%s]" % (a["key"], label),
                  "%s events, %s min%s%s; rank %s by minutes, %s by events" % (
                      a["events"], a["minutes"], ", %d ongoing" % a["ongoing"] if a["ongoing"] else "",
                      ", %d held out" % a["held_out"] if a["held_out"] else "", a["rank_minutes"], a["rank_events"]),
                  "downtime export", period + "; asset_id == %r" % a["key"], period=label)
        for a in codes_c:
            f.add("%s.code.%s" % (p, a["key"]), "Reason code %s [%s]" % (a["key"], label),
                  "%s events, %s min%s; rank %s by minutes, %s by events" % (
                      a["events"], a["minutes"], ", %d held out" % a["held_out"] if a["held_out"] else "",
                      a["rank_minutes"], a["rank_events"]),
                  "downtime export", period + "; reason_code == %r" % a["key"], period=label)
        # Reconcile: per-asset events and minutes sum to the totals.
        self.check(sum(a["events"] for a in assets) == out["events"], "%s: asset events sum to the total" % label)
        self.check(abs(sum(a["minutes"] for a in assets) - out["minutes"]) < 1e-6, "%s: asset minutes sum to the total" % label)
        self.check(sum(a["events"] for a in codes) + out["uncoded_events"] == out["events"],
                   "%s: coded + uncoded events equal the total" % label)
        return out

    # -- per-day computation ---------------------------------------------------
    def days(self):
        plan, rout = self.t("plan"), self.t("routings")
        self.plan_rows = []
        if plan:
            for r in plan.rows:
                d = parse_day(plan.get(r, "plan_date"))
                self.plan_rows.append(OrderedDict([
                    ("part", part_key(r)), ("part_verbatim", r.get("_part_verbatim")), ("provisional", r.get("_provisional")),
                    ("qty", num(plan.get(r, "planned_qty"))), ("day", str(d) if d else None),
                    ("asset", plan.get(r, "asset_id").strip() if plan.has("asset_id") else None),
                    ("cell", plan.get(r, "cell").strip() if plan.has("cell") else None),
                    ("work_center", plan.get(r, "work_center").strip() if plan.has("work_center") else None),
                    ("planned_hours", num(plan.get(r, "planned_hours")) if plan.has("planned_hours") else None)]))
        # Ideal cycle minutes per unit, per part and work center, from the routing.
        self.ideal = {}
        if rout:
            unit_col = None
            if rout.has("run_min_per_unit"):
                unit_col, factor = "run_min_per_unit", 1.0
            elif rout.has("run_hours_per_unit"):
                unit_col, factor = "run_hours_per_unit", 60.0
            if unit_col:
                for r in rout.rows:
                    v = num(rout.get(r, unit_col))
                    if v is not None and r.get("_part"):
                        key = (r["_part"], rout.get(r, "work_center").strip() if rout.has("work_center") else None)
                        self.ideal[key] = self.ideal.get(key, 0.0) + v * factor
        rate, rate_source = self.downtime_rate()
        all_days = sorted({x["day"] for x in self.out_rows if x["day"]} | {x["day"] for x in self.plan_rows if x["day"]} |
                          {e["day"] for e in self.events if e["day"]})
        self.perday = OrderedDict()
        for d in all_days:
            self.perday[d] = self.one_day(d, rate, rate_source)

    def downtime_rate(self):
        env = os.environ.get("MFG_DOWNTIME_COST_PER_HOUR")
        if env and num(env) is not None:
            return num(env), "env_variable"
        p = self.profile or {}
        if p.get("downtime_rate") is not None:
            return p["downtime_rate"], p.get("downtime_rate_kind", "profile_confirmed")
        return None, "unset"

    def one_day(self, d, rate, rate_source):
        p = self.profile or {}
        outs = [x for x in self.out_rows if x["day"] == d]
        plans = [x for x in self.plan_rows if x["day"] == d]
        evs = [e for e in self.events if e["day"] == d]
        units_by_part = {x["part"]: x["item_unit"] for x in self.out_rows}
        items_unit = lambda part: (self.master.get(part, {}).get(items_col(self.t("items"), "uom")) if self.t("items")
                                   else units_by_part.get(part)) if part else None
        # Output against plan, by part.
        parts = OrderedDict()
        for x in plans:
            a = parts.setdefault(x["part"], new_part(x["part"]))
            a["planned"] = (a["planned"] or 0) + (x["qty"] or 0)
            a["plan_spellings"].add(x["part_verbatim"])
            a["provisional"] = a["provisional"] or bool(x["provisional"])
        for part in {x["part"] for x in plans if x["qty"] is None}:   # a plan quantity that cannot be read is not 0
            parts[part]["planned"] = None
        for x in outs:
            a = parts.setdefault(x["part"], new_part(x["part"]))
            a["mes_spellings"].add(x["part_verbatim"])
            a["provisional"] = a["provisional"] or bool(x["provisional"])
            a["units"].add(x["unit"])
            if x["held_out"]:
                a["held_out_rows"].append(OrderedDict([("work_order", x["work_order"]), ("good", intish(x["good"])),
                                                       ("shift", x["shift"]), ("why", x["held_out"])]))
                continue
            a["good"] = (a["good"] or 0) + (x["good"] or 0)
            a["rows_counted"] += 1
        for part, a in parts.items():
            iu = items_unit(part)
            a["item_unit"] = iu
            a["unit_conflict"] = any(u and iu and u.strip().lower() != str(iu).strip().lower() for u in a["units"])
            dup_day = any(h["why"] == "duplicate key" for h in a["held_out_rows"])
            if a["planned"] is not None and a["held_out_rows"] and (a["rows_counted"] == 0 or dup_day):
                # Unresolved output for the day: plan "not counted", good "held out", day out of period totals.
                a["status"] = "held out"
            elif a["unit_conflict"]:
                a["status"] = "not comparable, unit conflict"
            elif a["planned"] is None:
                a["status"] = "no plan"
            elif a["rows_counted"] == 0:
                a["status"] = "no output recorded"
            else:
                a["status"] = "comparable"
                a["variance"] = intish(a["good"] - a["planned"])
                a["variance_pct"] = round(100.0 * (a["good"] - a["planned"]) / a["planned"], 1) if a["planned"] else None
                a["under_plan"] = a["good"] < a["planned"]
            a["plan_spellings"] = sorted(s for s in a["plan_spellings"] if s)
            a["mes_spellings"] = sorted(s for s in a["mes_spellings"] if s)
            a["units"] = sorted(u for u in a["units"] if u)
            a["planned"] = intish(a["planned"]) if a["planned"] is not None else None
            a["good"] = intish(a["good"]) if a["good"] is not None else None
        planned_qty = defaultdict(float)
        actual_qty = defaultdict(float)
        for part, a in parts.items():
            if a["planned"] is not None and a["status"] != "held out":
                planned_qty[a["item_unit"] or "unit"] += a["planned"]
            for x in outs:
                if x["part"] == part and not x["held_out"]:
                    actual_qty[(x["unit"] if a["unit_conflict"] else a["item_unit"]) or x["unit"] or "unit"] += x["good"] or 0
        # OEE per asset.
        assets = OrderedDict()
        for x in plans:
            if not x["asset"]:
                continue
            a = assets.setdefault(x["asset"], OrderedDict([
                ("asset", x["asset"]), ("cell", x["cell"]), ("work_center", x["work_center"]),
                ("planned_minutes", 0.0), ("parts", set())]))
            if x["planned_hours"] is not None:
                if a["planned_minutes"] is not None:
                    a["planned_minutes"] += x["planned_hours"] * 60
            elif p.get("planned_hours_per_shift"):
                a["planned_minutes"] = None
            a["parts"].add(x["part"])
        oee_rows = []
        for asset, a in assets.items():
            ev = [e for e in evs if e["asset"] == asset and not e["blocked"]]
            mine = [x for x in outs if x["asset"] == asset]
            held = [e for e in ev if e["minutes"] is None]
            down = sum(e["minutes"] for e in ev if e["minutes"] is not None)
            pm = a["planned_minutes"] or None
            row = OrderedDict([("asset", asset), ("cell", a["cell"]), ("planned_minutes", intish(pm) if pm else None),
                               ("downtime_minutes", intish(down) if self.t("downtime") else None), ("availability", None), ("performance", None),
                               ("quality", None), ("oee", None), ("why_not", [])])
            if not mine:
                row["why_not"].append("no output recorded for this asset")
            if self.t("downtime") is None:
                row["why_not"].append("no downtime export, so availability is not computed")
            elif pm is None:
                row["why_not"].append("no planned production time")
            elif held:
                row["why_not"].append("downtime minutes untrusted or open (%s)" % ", ".join(
                    "%s %s" % (e["start_local"], "/".join(e["flags"])) for e in held))
            elif down > pm:
                row["why_not"].append("stops charged to this day (%s min) exceed its planned production time (%s min): "
                                      "an outage runs past the day, so availability is not computed" % (intish(down), intish(pm)))
            else:
                row["availability"] = round((pm - down) / pm, 4)
            counted = [x for x in mine if not x["held_out"]]
            if mine and len(counted) < len(mine):
                row["why_not"].append("duplicate, orphan or unreadable-quantity rows held out")
            if counted and all(x["scrap_recorded"] for x in counted) and not any(x["held_out"] for x in mine):
                g = sum(x["good"] or 0 for x in counted)
                s = sum(x["scrap"] or 0 for x in counted)
                rw = sum(x["rework"] or 0 for x in counted) if any(x["rework"] is not None for x in counted) else 0
                if g + s + rw:
                    row["quality"] = round(g / (g + s + rw), 4)
            elif counted and not all(x["scrap_recorded"] for x in counted):
                row["why_not"].append("scrap not recorded (absent, not zero)")
            if row["availability"] is not None and counted and not any(x["held_out"] for x in mine):
                ideal = 0.0
                ok = True
                for x in counted:
                    k = (x["part"], a["work_center"])
                    if k not in self.ideal or x["unit_conflict"]:
                        ok = False
                        break
                    ideal += self.ideal[k] * ((x["good"] or 0) + (x["scrap"] or 0))
                run = pm - down
                if ok and run > 0:
                    row["performance"] = round(ideal / run, 4)
                elif not ok:
                    row["why_not"].append("performance not computable: " + (
                        "no routing file in the drop, so no ideal cycle time" if not self.ideal else
                        "no routing run standard for this part and work center, or a unit conflict"))
            if None not in (row["availability"], row["performance"], row["quality"]):
                row["oee"] = round(row["availability"] * row["performance"] * row["quality"], 4)
            oee_rows.append(row)
        # Site roll-up: time-weighted availability, ideal/run performance, pooled quality, over assets with each.
        reported = {x["asset"] for x in outs}   # oee.md: an asset with no output is unreported, and out of the average
        av = [r for r in oee_rows if r["availability"] is not None and r["asset"] in reported]
        site_av = round(sum(r["planned_minutes"] - r["downtime_minutes"] for r in av) / sum(r["planned_minutes"] for r in av), 4) if av else None
        pf = [r for r in oee_rows if r["performance"] is not None]
        site_pf = round(sum(r["performance"] * (r["planned_minutes"] - r["downtime_minutes"]) for r in pf) /
                        sum(r["planned_minutes"] - r["downtime_minutes"] for r in pf), 4) if pf else None
        q = [r for r in oee_rows if r["quality"] is not None]
        site_q = None
        if q:
            gs = ts = 0.0
            for r in q:
                mine = [x for x in outs if x["asset"] == r["asset"] and not x["held_out"]]
                gs += sum(x["good"] or 0 for x in mine)
                ts += sum((x["good"] or 0) + (x["scrap"] or 0) + (x["rework"] or 0) for x in mine)
            site_q = round(gs / ts, 4) if ts else None
        same = [r["asset"] for r in av] == [r["asset"] for r in pf] == [r["asset"] for r in q]
        site_oee = round(site_av * site_pf * site_q, 4) if same and None not in (site_av, site_pf, site_q) else None
        excluded = ["%s (%s)" % (r["asset"], "; ".join(r["why_not"])) for r in oee_rows if r["why_not"]]
        if not same and None not in (site_av, site_pf, site_q):
            excluded.append("site composite (the three components rest on different assets)")
        # Scrap and cost.
        scrap_parts = OrderedDict()
        unpriced = []
        for x in outs:
            if x["held_out"]:
                continue
            s = scrap_parts.setdefault(x["part"], OrderedDict([("part", x["part"]), ("scrap", 0.0), ("unit", x["unit"]),
                                                               ("recorded", True), ("unit_conflict", False), ("scrap_usd", None)]))
            if not x["scrap_recorded"]:
                s["recorded"] = False
                continue
            s["scrap"] += x["scrap"] or 0
            s["unit_conflict"] = s["unit_conflict"] or x["unit_conflict"]
        priced_total = 0.0
        cost_col = items_col(self.t("items"), "std_cost")
        for part, s in scrap_parts.items():
            cost = num(self.master.get(part, {}).get(cost_col, "")) if cost_col and part else None
            s["scrap"] = intish(s["scrap"]) if s["recorded"] else None
            if not s["recorded"]:
                unpriced.append("%s scrap: not recorded in the MES export (absent, not zero)" % part)
            elif s["unit_conflict"]:
                unpriced.append("%s scrap: unit conflict, MES %s / %s %s" % (part, s["unit"], self.unit_ref_short, items_unit(part)))
            elif cost is None:
                unpriced.append("%s scrap: no standard cost on file" % part)
            else:
                s["scrap_usd"] = round(s["scrap"] * cost, 2)
                priced_total += s["scrap_usd"]
        any_priced = any(s["scrap_usd"] is not None for s in scrap_parts.values())
        for s in scrap_parts.values():
            s["share_of_priced"] = round(100.0 * s["scrap_usd"] / priced_total, 1) if s["scrap_usd"] is not None and priced_total else None
        held_out_scrap = [x for x in outs if x["held_out"]]
        if held_out_scrap:
            unpriced.append("held-out rows (%s): duplicate, orphan or no readable quantity, none counted" % ", ".join(
                sorted({x["work_order"] for x in held_out_scrap})))
        trusted = [e for e in evs if e["minutes"] is not None and not e["blocked"]]
        down_total = sum(e["minutes"] for e in trusted)
        down_usd = round(down_total / 60.0 * rate, 2) if rate is not None else None
        if rate is None:
            unpriced.insert(0, "all downtime: no downtime cost rate (MFG_DOWNTIME_COST_PER_HOUR not set, none in the plant's rates)")
        rework_col = self.t("output") is not None and self.t("output").has("qty_rework")
        return OrderedDict([
            ("day", d), ("parts", parts), ("planned_qty", {k: intish(v) for k, v in planned_qty.items()}),
            ("actual_qty", {k: intish(v) for k, v in actual_qty.items()}),
            ("output_provisional", any(a["provisional"] for a in parts.values())),
            ("oee_by_asset", oee_rows), ("availability", site_av), ("performance", site_pf), ("quality", site_q),
            ("oee", site_oee), ("oee_excluded", excluded),
            ("quality_convention", "good ÷ (good + scrap + rework), first-pass yield" if rework_col else
             "good ÷ (good + scrap); no rework column, so first-pass yield could not be applied"),
            ("scrap", list(scrap_parts.values())), ("scrap_priced_usd", round(priced_total, 2) if any_priced else None),
            ("downtime_usd", down_usd), ("rate_source", rate_source), ("unpriced", unpriced),
            ("downtime_minutes", intish(down_total) if self.t("downtime") else None),
            ("events", len([e for e in evs if not e["blocked"]]) if self.t("downtime") else None),
            ("open_outages", sum(1 for e in evs if "ongoing" in e["flags"])),
            ("stops", [OrderedDict([("asset", e["asset"]), ("cell", self.cell_of(e["asset"])), ("start", e["start_local"]),
                                    ("minutes", intish(e["minutes"])), ("stated_minutes", intish(e["stated_minutes"])),
                                    ("code", e["code"]), ("text", e["text"]), ("flags", e["flags"])]) for e in
                       sorted(evs, key=lambda e: e["start"] or self.run_time)]),
        ])

    def cell_of(self, asset):
        assets = self.t("assets")
        if assets and assets.has("location"):
            for r in assets.rows:
                if assets.get(r, "asset_id").strip() == asset:
                    return assets.get(r, "location").strip()
        for x in self.plan_rows:
            if x["asset"] == asset and x["cell"]:
                return x["cell"]
        return None

    # -- class 6, class 7 and the remaining integrity flags ------------------------
    def classes(self):
        out, wos = self.t("output"), self.t("work_orders")
        problems = self.problems
        checked = []
        produced = {x["part"] for x in self.out_rows}
        planned = {x["part"] for x in self.plan_rows}
        for part in self.master:
            if part not in produced and part not in planned:
                checked.append(OrderedDict([("record", part), ("type", "part"),
                                            ("line", "in the item master, not planned and not produced in the window")]))
        assets = self.t("assets")
        active_assets = {x["asset"] for x in self.out_rows if x["asset"]} | {x["asset"] for x in self.plan_rows if x["asset"]}
        if assets:
            for r in assets.rows:
                a = assets.get(r, "asset_id").strip()
                if a not in active_assets:
                    checked.append(OrderedDict([("record", a), ("type", "asset"),
                                                ("line", "in the asset list, in no plan and no production record")]))
        # Closed work orders with no output: one-sided, unless another source contradicts it.
        self.contradicted = []
        if wos and out:
            produced_wos = {x["work_order"] for x in self.out_rows}
            evidence = defaultdict(list)
            for role in ("ncrs", "inspection"):
                tb = self.t(role)
                if tb and tb.has("work_order"):
                    for r in tb.rows:
                        ref = tb.get(r, "ncr_id") if role == "ncrs" else "inspection rows"
                        evidence[tb.get(r, "work_order").strip()].append("%s %s" % (tb.name, ref))
            for wo, r in self.WO.items():
                st = wos.get(r, "status").strip().lower()
                if wo in produced_wos or st not in ("closed", "complete", "completed"):
                    continue
                ev = sorted(set(evidence.get(wo, [])))
                if ev:
                    c = OrderedDict([("record", wo), ("type", "production work order"), ("contradicted_by", ev),
                                     ("line", "closed with no MES output, contradicted by %s" % ", ".join(ev))])
                    self.contradicted.append(c)
                    problems.append(OrderedDict([("class", 6), ("name", "One-sided, contradicted"), ("key", wo),
                                                 ("what", "%s is closed with no MES output, but %s" % (wo, ", ".join(ev))),
                                                 ("rows", 1), ("contradicted_by", ev),
                                                 ("fix", "None automatic: the work order was run. Find its output.")]))
                else:
                    checked.append(OrderedDict([("record", wo), ("type", "production work order"),
                                                ("line", "closed in the ERP with no MES output in the window")]))
        # Class 2-5 rows for the numbered table, one block per verbatim spelling.
        names = {2: "Format drift", 3: "Leading-zero loss", 4: "Revision suffix", 5: "Case and whitespace"}
        for e in self.norm_log.values():
            if e["class"] in names:
                problems.append(OrderedDict([("class", e["class"]), ("name", names[e["class"]]), ("key", e["verbatim"]),
                                             ("what", "%s spells %r; the item master has %s (%s)" % (e["source"], e["verbatim"], e["canonical"], e["rule"])),
                                             ("rows", e["rows"]), ("fix", "Proposed, awaiting approval: read %r as %s. %d rows stay provisional until then." % (
                                                 e["verbatim"], e["canonical"], e["rows"]))]))
        for e in self.unmatched_parts.values():
            problems.append(OrderedDict([("class", 1), ("name", "Orphan record"), ("key", e["verbatim"]),
                                         ("what", "%s carries part %r, which matches nothing in the item master (%s)" % (e["source"], e["verbatim"], e["why"])),
                                         ("rows", e["rows"]), ("fix", "None automatic.")]))
        # Class 7: activity rows outside the overlapping window.
        c7 = []
        if self.window:
            lo, hi = self.window
            for role, col in (("output", "day"), ("plan", "day")):
                rows = self.out_rows if role == "output" else self.plan_rows
                n = sum(1 for x in rows if x[col] and not (str(lo) <= x[col] <= str(hi)))
                if n:
                    c7.append("%s: %d rows outside %s to %s" % (role, n, lo, hi))
            n = sum(1 for e in self.events if e["day"] and not (str(lo) <= e["day"] <= str(hi)))
            if n:
                c7.append("downtime: %d events outside %s to %s" % (n, lo, hi))
        # NCR integrity.
        ncrs = self.t("ncrs")
        first_out = {}
        for x in self.out_rows:
            if x["day"]:
                first_out[x["work_order"]] = min(first_out.get(x["work_order"], x["day"]), x["day"])
        self.ncr_flags = []
        if ncrs:
            for r in ncrs.rows:
                wo = ncrs.get(r, "work_order").strip()
                erp = self.WO.get(wo)
                flags = []
                if erp and r.get("_part") and erp.get("_part") and r["_part"] != erp["_part"]:
                    flags.append("ncr_part_differs: NCR says %s, the ERP holds %s for %s" % (r["_part_verbatim"], erp["_part"], wo))
                fd = parse_ts(ncrs.get(r, "found_at"), self.tz)
                if fd and wo in first_out and str(fd.date()) < first_out[wo]:
                    flags.append("ncr_dated_before_wo: found %s, before %s's first output on %s" % (fd.date(), wo, first_out[wo]))
                if flags:
                    self.ncr_flags.append(OrderedDict([("ncr", ncrs.get(r, "ncr_id")), ("work_order", wo), ("flags", flags)]))
        # Terse maintenance close-out notes.
        maint = self.t("maintenance")
        terse = []
        if maint and maint.has("close_out_note"):
            for r in maint.rows:
                if maint.get(r, "close_out_note").strip().lower() in TERSE_NOTES:
                    terse.append(OrderedDict([("maintenance_wo", maint.get(r, "maintenance_wo")), ("asset", maint.get(r, "asset_id")),
                                              ("note", maint.get(r, "close_out_note"))]))
        dt_flags = [OrderedDict([("asset", e["asset"]), ("start", e["start_local"]), ("end", e["end_local"]),
                                 ("stated_minutes", intish(e["stated_minutes"])), ("flags", e["flags"])])
                    for e in self.events if set(e["flags"]) & {"end_before_start", "duration_mismatch"}]
        # Number the table: classes 1-5 and 8, contradicted one-sided records, and unit conflicts, which the
        # Operations page has always listed among its problems.
        order = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 8: 8, 6: 6, "units": 9}
        numbered = [x for x in problems if x["class"] in order]
        numbered.sort(key=lambda x: (order[x["class"]], str(x["key"])))
        for n, x in enumerate(numbered, 1):
            x["n"] = n
            self.F.add("problem.%d.what" % n, "Data problem %d, as described" % n, x["what"], "this run", "class %s %s" % (x["class"], x["key"]))
        self.F.add("problems.count", "Data problems (classes 1-5, 8, contradicted one-sided and unit conflicts), numbered table count",
                   len(numbered), "this run", "; ".join("class %s %s" % (x["class"], x["key"]) for x in numbered))
        self.F.add("checked.count", "Checked, nothing wrong (class 6), outside the count", len(checked), "this run",
                   "; ".join(c["record"] for c in checked))
        mismatched = [x for x in numbered if x["class"] in (1, 2, 3, 4, 5, 8)]
        self.F.add("mismatched.count", "Mismatched records: classes 1-5 and 8", len(mismatched), "this run",
                   "; ".join("class %s %s" % (x["class"], x["key"]) for x in mismatched))
        by_class = Counter(x["class"] for x in numbered)
        for c, n in sorted(by_class.items(), key=lambda kv: str(kv[0])):
            self.F.add("problems.class%s" % c, "Data problems, class %s" % c, n, "this run", "class == %s" % c)
        self.check(sum(by_class.values()) == len(numbered), "data problems by class sum to the table count")
        self.F.add("integrity.dt_flags", "Downtime rows held out for end_before_start or duration_mismatch", len(dt_flags),
                   "downtime export", "; ".join("%s %s" % (x["asset"], x["start"]) for x in dt_flags))
        self.F.add("integrity.ncr", "NCRs whose part or date disagrees with their work order", len(self.ncr_flags),
                   "NCR export vs ERP and MES", "; ".join(x["ncr"] for x in self.ncr_flags))
        self.F.add("integrity.terse", "Maintenance close-out notes that say nothing", len(terse), "maintenance export",
                   "close_out_note in ('Fixed.', 'Done', ...)")
        self.F.add("integrity.blank_lot", "MES rows with a blank lot number", len(self.integrity["blank_lot"]), "MES export",
                   "lot_number == ''")
        self.model["data_problems"] = OrderedDict([
            ("numbered", numbered), ("count", len(numbered)),
            ("mismatched", [x for x in numbered if x["class"] in (1, 2, 3, 4, 5, 8)]), ("duplicates", self.dup_list),
            ("waiting_on_decision", OrderedDict([
                ("unit_conflicts", self.unit_conflicts),
                ("normalizations", [e for e in self.norm_log.values() if e["status"] != "approved"]),
                ("provisional_rows", sum(e["rows"] for e in self.norm_log.values() if e["status"] != "approved")),
                ("ncr_keys", self.ncr_flags)])),
            ("class7", c7), ("checked_nothing_wrong", checked), ("contradicted", self.contradicted),
            ("integrity", OrderedDict([
                ("downtime_duration_conflicts", dt_flags),
                ("blank_lots", [OrderedDict([("work_order", x["work_order"]), ("day", x["day"])]) for x in self.integrity["blank_lot"]]),
                ("mes_part_differs", [OrderedDict([("work_order", x["work_order"]), ("mes_part", x["part_verbatim"])]) for x in self.integrity["mes_part_differs"]]),
                ("terse_close_out_notes", terse), ("shared_lots", self.shared_lots)])),
        ])

    # -- exceptions -------------------------------------------------------------
    def exceptions(self):
        wos, ncrs, maint = self.t("work_orders"), self.t("ncrs"), self.t("maintenance")
        d = str(self.day) if self.day else None
        exc = []
        so_link = wos is not None and wos.has("sales_order")
        good_by_wo = defaultdict(float)
        unclear = set()
        for x in self.out_rows:
            if x["held_out"]:
                unclear.add(x["work_order"])
                continue
            if x["unit_conflict"]:
                unclear.add(x["work_order"])
            good_by_wo[x["work_order"]] += x["good"] or 0
        late, cannot = [], []
        if wos and d:
            for wo, r in self.WO.items():
                if wos.get(r, "status").strip().lower() in ("closed", "complete", "completed", "cancelled", "canceled"):
                    continue
                due = parse_day(wos.get(r, "due_date"))
                if not due or str(due) > d:
                    continue
                if wo in unclear:
                    cannot.append(wo)
                    continue
                g = good_by_wo.get(wo, 0.0)
                q = num(wos.get(r, "qty_ordered")) or 0
                if g < q:
                    late.append(OrderedDict([("work_order", wo), ("part", r.get("_part")), ("ordered", intish(q)),
                                             ("good", intish(g)), ("due", str(due))]))
        for x in late:
            self.F.add("exc.late.%s" % x["work_order"], "Good / ordered, %s" % x["work_order"], "%s / %s" % (x["good"], x["ordered"]),
                       "ERP vs MES", "due %s" % x["due"])
            exc.append(OrderedDict([("kind", "late_job"), ("ref", x["work_order"]), ("detail", x),
                                    ("commitment_impact", None if so_link else "not traceable: no work order to sales order link in the ERP")]))
        self.F.add("exc.late", "Open work orders due on or before %s with good output short of ordered" % d, len(late),
                   "ERP vs MES", "; ".join("%s %s/%s due %s" % (x["work_order"], x["good"], x["ordered"], x["due"]) for x in late))
        self.F.add("exc.late_undeterminable", "Open work orders due on or before %s whose completion cannot be judged" % d,
                   len(cannot), "ERP vs MES", "unit conflict or held-out rows: " + ", ".join(cannot))
        # Machines down: ongoing at the window close.
        for e in self.events:
            if "ongoing" in e["flags"]:
                exc.append(OrderedDict([("kind", "machine_down"), ("ref", e["asset"]),
                                        ("detail", OrderedDict([("down_since", e["start_local"]), ("code", e["code"]), ("text", e["text"])])),
                                        ("commitment_impact", None if so_link else "not traceable: no work order to sales order link in the ERP")]))
        # Quality holds: open NCRs tied to a customer.
        if ncrs:
            for r in ncrs.rows:
                st = ncrs.get(r, "status").strip().lower() if ncrs.has("status") else "open"
                cust = ncrs.get(r, "customer").strip() if ncrs.has("customer") else ""
                if st == "open" and cust:
                    exc.append(OrderedDict([("kind", "quality_hold"), ("ref", ncrs.get(r, "ncr_id")),
                                            ("detail", OrderedDict([("customer", cust), ("work_order", ncrs.get(r, "work_order")),
                                                                    ("part", r.get("_part")), ("lot", ncrs.get(r, "lot_number"))])),
                                            ("commitment_impact", None)]))
        for c in self.contradicted:
            exc.append(OrderedDict([("kind", "one_sided_contradicted"), ("ref", c["record"]), ("detail", c),
                                    ("commitment_impact", None)]))
        self.F.add("exc.count", "Exceptions (late jobs, machines down, quality holds, contradicted one-sided)", len(exc),
                   "this run", ", ".join("%s %s" % (x["kind"], x["ref"]) for x in exc))
        # Maintenance history per asset, for the machine decision.
        hist = OrderedDict()
        if maint:
            lo = (self.day - timedelta(days=LOOKBACK_DAYS)) if self.day else None
            for r in maint.rows:
                a = maint.get(r, "asset_id").strip()
                od = parse_day(maint.get(r, "opened_date"))
                if lo and od and od < lo:
                    continue
                h = hist.setdefault(a, OrderedDict([("records", 0), ("corrective", 0), ("seizure", []), ("notes", [])]))
                h["records"] += 1
                typ = maint.get(r, "type").strip().lower() if maint.has("type") else ""
                note = maint.get(r, "close_out_note") if maint.has("close_out_note") else ""
                if typ == "corrective":
                    h["corrective"] += 1
                if any(w in note.lower() for w in SEIZURE_WORDS):
                    h["seizure"].append(OrderedDict([("maintenance_wo", maint.get(r, "maintenance_wo")), ("date", str(od)), ("note", note)]))
                h["notes"].append(OrderedDict([("maintenance_wo", maint.get(r, "maintenance_wo")), ("date", str(od)),
                                               ("type", typ), ("note", note)]))
            for a, h in hist.items():
                h["repeat_failure"] = h["corrective"] >= 2
        self.model["exceptions"] = OrderedDict([("items", exc), ("late_jobs", late), ("late_undeterminable", cannot),
                                                ("so_link", so_link), ("maintenance_history", hist)])

    # -- breakdown-diagnosis records -------------------------------------------
    def fold_diagnoses(self):
        blocked, flagged, matched, assessed = [], [], [], set()
        for rec in getattr(self, "diagnoses", []):
            if rec.get("source_system") not in (None, "breakdown_diagnosis"):
                continue
            s = parse_ts(rec.get("started_at") or "", self.tz)
            e = parse_ts(rec.get("ended_at") or "", self.tz)
            sf = rec.get("safety_flagged")
            if sf is not None and not isinstance(sf, bool):   # True, yes, 1, or a trailing comment; anything else is unknown
                sf = {"true": True, "yes": True, "y": True, "1": True, "false": False, "no": False, "n": False, "0": False}.get(
                    str(sf).split("#")[0].strip().strip("'\"").lower())
            item = OrderedDict([("file", rec.get("_file")), ("asset", rec.get("asset_id")), ("start", local_str(s)),
                                ("end", local_str(e)), ("duration_minutes", rec.get("duration_minutes")),
                                ("reason_code", rec.get("reason_code")), ("reason_text", rec.get("reason_text")),
                                ("leading_cause", rec.get("leading_cause")), ("diagnosis_state", rec.get("diagnosis_state")),
                                ("technician_step", rec.get("technician_step")),
                                ("safety_flagged", sf), ("safety_reason", rec.get("safety_reason"))])
            if sf is None:
                item["why"] = "safety status missing on a diagnosis record - not ranked until confirmed"
                blocked.append(item)
                continue
            assessed.add(str(rec.get("asset_id")))
            if sf is True:
                flagged.append(item)
            # A flagged record (true or false) joins the log as a row, untransformed.
            stated = num(rec.get("duration_minutes") or "")
            mins = stated if (s and e and stated is not None and
                              abs(stated - (e.astimezone(timezone.utc) - s.astimezone(timezone.utc)).total_seconds() / 60) <= 1) else None
            code = rec.get("reason_code") or ""
            # The same stoppage as an MES row (same asset, start within the same shift) is counted once.
            same = [m for m in self.events if s and m["start"] and "source" not in m and "diagnosis" not in m
                    and m["asset"] == rec.get("asset_id") and abs((m["start"] - s).total_seconds()) <= 8 * 3600]
            if same:
                m = min(same, key=lambda m: abs((m["start"] - s).total_seconds()))
                m["diagnosis"] = rec.get("_file")
                item["matched_mes_row"] = m["start_local"]
                matched.append(item)
                continue
            self.events.append(OrderedDict([
                ("i", "diag:%s" % rec.get("_file")), ("asset", rec.get("asset_id")), ("start", s), ("end", e),
                ("start_local", local_str(s)), ("end_local", local_str(e)), ("day", str(self.prod_day_of(s)) if s else None),
                ("stated_minutes", stated), ("minutes", mins),
                ("flags", ["ongoing"] if s and not e else ([] if mins is not None else ["duration_mismatch"])),
                ("code", code or "(blank)"), ("uncoded", code == "" or code.lower() == "other"),
                ("text", rec.get("reason_text") or ""), ("blocked", None), ("source", "breakdown_diagnosis")]))
        self.model["diagnoses"] = OrderedDict([("blocked_safety_unknown", blocked), ("safety_flagged", flagged),
                                               ("matched_to_mes_row", matched),
                                               ("assets_with_diagnosis", sorted(assessed))])
        self.F.add("diag.blocked", "Diagnosis records blocked, safety status unknown", len(blocked), "breakdown-diagnosis records",
                   "safety_flagged absent")

    # -- week over week -------------------------------------------------------
    def week_over_week(self):
        if not self.day:
            self.model["week_over_week"] = None
            return
        def window(a, b):
            ds = [str(self.day - timedelta(days=i)) for i in range(a, b)]
            recs = [self.perday[x] for x in ds if x in self.perday]
            cmp_plan = sum(p["planned"] for r in recs for p in r["parts"].values() if p["status"] == "comparable")
            cmp_good = sum(p["good"] for r in recs for p in r["parts"].values() if p["status"] == "comparable")
            av = [r["availability"] for r in recs if r["availability"] is not None]
            q = [r["quality"] for r in recs if r["quality"] is not None]
            return OrderedDict([("from", ds[-1]), ("to", ds[0]), ("days", len(recs)),
                                ("output_vs_plan_pct", round(100.0 * cmp_good / cmp_plan, 1) if cmp_plan else None),
                                ("availability", round(sum(av) / len(av), 4) if av else None), ("availability_days", len(av)),
                                ("quality", round(sum(q) / len(q), 4) if q else None), ("quality_days", len(q)),
                                ("downtime_minutes", intish(sum(r["downtime_minutes"] for r in recs))
                                 if recs and self.t("downtime") else None),
                                ("scrap_usd", round(sum(r["scrap_priced_usd"] for r in recs if r["scrap_priced_usd"] is not None), 2)
                                 if any(r["scrap_priced_usd"] is not None for r in recs) else None)])
        this, prev = window(0, 7), window(7, 14)
        self.model["week_over_week"] = OrderedDict([("basis", "per-day figures computed this run from the exports"),
                                                    ("this_week", this), ("last_week", prev),
                                                    ("skip", prev["days"] == 0)])
        for lab, w in (("this", this), ("prev", prev)):
            for k in ("days", "output_vs_plan_pct", "availability", "quality", "downtime_minutes", "scrap_usd"):
                self.F.add("wow.%s.%s" % (lab, k), "Week over week, %s week %s..%s: %s" % (lab, w["from"], w["to"], k), w[k],
                           "per-day figures, this run", "%s to %s" % (w["from"], w["to"]))

    # -- period roll-ups: every Day, Week and Month-to-date figure ---------------
    def rollup(self, days, label, period):
        """Sum per-day figures over a period. Every value lands in the figures tab."""
        recs = [self.perday[d] for d in days if d in self.perday]
        parts = OrderedDict()
        for r in recs:
            for part, a in r["parts"].items():
                t = parts.setdefault(part, OrderedDict([
                    ("part", part), ("planned", 0), ("good", 0), ("days_compared", 0), ("days_under_plan", 0),
                    ("days_held_out", []), ("unit_conflict", False), ("provisional", False), ("q_good", 0), ("q_total", 0),
                    ("plan_spellings", set()), ("mes_spellings", set()), ("units", set()), ("item_unit", a["item_unit"])]))
                t["provisional"] = t["provisional"] or a["provisional"]
                t["plan_spellings"].update(a["plan_spellings"])
                t["mes_spellings"].update(a["mes_spellings"])
                t["units"].update(a["units"])
                if a["status"] == "held out":
                    t["days_held_out"].append(r["day"])
                elif a["status"] == "not comparable, unit conflict":
                    t["unit_conflict"] = True
                    t["planned"] += a["planned"] or 0
                    t["good"] += a["good"] or 0
                elif a["status"] == "comparable":
                    t["planned"] += a["planned"]
                    t["good"] += a["good"]
                    t["days_compared"] += 1
                    t["days_under_plan"] += 1 if a["under_plan"] else 0
        # Quality by part, over days whose scrap was recorded and whose output was not held out.
        for r in recs:
            for x in r["scrap"]:
                a = r["parts"].get(x["part"])
                if x["part"] in parts and x["scrap"] is not None and a and a["status"] != "held out" and a["good"] is not None:
                    parts[x["part"]]["q_good"] += a["good"]
                    parts[x["part"]]["q_total"] += a["good"] + x["scrap"] + sum(
                        o["rework"] or 0 for o in self.out_rows if o["day"] == r["day"] and o["part"] == x["part"] and not o["held_out"])
        for part, t in parts.items():
            for k in ("plan_spellings", "mes_spellings", "units"):
                t[k] = sorted(t[k])
            t["quality"] = round(t["q_good"] / t["q_total"], 4) if t["q_total"] else None
            del t["q_good"], t["q_total"]
            if t["unit_conflict"]:
                t["status"] = "not comparable, unit conflict"
                t["planned"], t["good"] = intish(t["planned"]), intish(t["good"])
                t["variance"] = t["variance_pct"] = None
            elif not t["days_compared"]:
                t["status"] = "no comparable day"
                t["planned"] = t["good"] = t["variance"] = t["variance_pct"] = None
            else:
                t["status"] = "comparable"
                t["variance"] = intish(t["good"] - t["planned"])
                t["variance_pct"] = round(100.0 * (t["good"] - t["planned"]) / t["planned"], 1) if t["planned"] else None
                t["planned"], t["good"] = intish(t["planned"]), intish(t["good"])
        scrap = OrderedDict()
        for r in recs:
            for x in r["scrap"]:
                s_ = scrap.setdefault(x["part"], OrderedDict([("part", x["part"]), ("scrap", 0), ("scrap_usd", 0.0), ("unit", x["unit"]),
                                                              ("days_not_recorded", 0), ("unit_conflict", False), ("priced", True)]))
                if x["scrap"] is None:
                    s_["days_not_recorded"] += 1
                else:
                    s_["scrap"] += x["scrap"]
                s_["unit_conflict"] = s_["unit_conflict"] or x["unit_conflict"]
                if x["scrap_usd"] is None:
                    s_["priced"] = False
                else:
                    s_["scrap_usd"] += x["scrap_usd"]
        for s_ in scrap.values():
            if s_["days_not_recorded"] and not s_["scrap"]:
                s_["scrap"] = None
            s_["scrap"] = intish(s_["scrap"]) if s_["scrap"] is not None else None
            s_["scrap_usd"] = round(s_["scrap_usd"], 2) if s_["priced"] and s_["scrap"] is not None else None
        priced = round(sum(s_["scrap_usd"] for s_ in scrap.values() if s_["scrap_usd"] is not None), 2) \
            if any(s_["scrap_usd"] is not None for s_ in scrap.values()) else None
        for s_ in scrap.values():
            s_["share_of_priced"] = round(100.0 * s_["scrap_usd"] / priced, 1) if s_["scrap_usd"] is not None and priced else None
        held = [h for r in recs for a in r["parts"].values() for h in a["held_out_rows"]]
        comp = [t for t in parts.values() if t["status"] == "comparable"]
        summ = OrderedDict([
            ("comparable_parts", len(comp)),
            ("max_abs_variance_pct", max((abs(t["variance_pct"]) for t in comp if t["variance_pct"] is not None), default=None)),
            ("all_under", bool(comp) and all(t["variance"] < 0 for t in comp)),
            ("all_over", bool(comp) and all(t["variance"] > 0 for t in comp)),
            ("days_under", [OrderedDict([("part", t["part"]), ("under", t["days_under_plan"]), ("of", t["days_compared"])]) for t in comp]),
            ("provisional", [OrderedDict([("part", t["part"]), ("held_out_days", t["days_held_out"])]) for t in parts.values() if t["provisional"]]),
            ("held_out_parts", [OrderedDict([("part", t["part"]), ("days", t["days_held_out"])]) for t in parts.values() if t["days_held_out"]]),
            ("not_comparable", [OrderedDict([("part", t["part"]), ("why", "unit conflict" if t["unit_conflict"] else "no comparable day")])
                                for t in parts.values() if t["status"] != "comparable"])])
        out = OrderedDict([("label", label), ("period", period), ("days", [r["day"] for r in recs]), ("summary", summ),
                           ("parts", parts), ("scrap", scrap), ("scrap_priced_usd", priced),
                           ("held_out_rows", len(held)), ("held_out_good", intish(sum(h["good"] or 0 for h in held)))])
        f, k = self.F, "per.%s" % label
        for part, t in parts.items():
            for fld in ("planned", "good", "variance", "variance_pct", "days_under_plan", "days_compared", "quality"):
                f.add("%s.out.%s.%s" % (k, part, fld), "%s, %s [%s]" % (fld.replace("_", " ").capitalize(), part, label), t[fld],
                      "plan and MES", period + "; comparable days only; held-out days excluded", period=label)
        for part, s_ in scrap.items():
            f.add("%s.scrap.%s" % (k, part), "Scrap qty, %s [%s]" % (part, label), s_["scrap"], "MES export",
                  period + "; held-out rows excluded; absent when not recorded", period=label, unit=s_["unit"] or "")
            f.add("%s.scrapusd.%s" % (k, part), "Scrap $, %s [%s]" % (part, label), s_["scrap_usd"], "MES x item master std_cost",
                  period + "; unpriced on a unit conflict or no record", period=label, unit="USD")
        f.add("%s.scrapusd" % k, "Priced scrap $ [%s]" % label, priced, "MES x item master std_cost", period, period=label, unit="USD")
        for part, s_ in scrap.items():
            f.add("%s.scrapshare.%s" % (k, part), "Share of priced scrap $, %s [%s]" % (part, label), s_["share_of_priced"],
                  "MES x item master std_cost", period + "; part's scrap $ / priced total", period=label, unit="%")
        f.add("%s.maxvar" % k, "Largest absolute variance among comparable parts [%s]" % label, summ["max_abs_variance_pct"],
              "plan and MES", period + "; comparable parts only", period=label, unit="%")
        f.add("%s.comparable" % k, "Comparable parts [%s]" % label, summ["comparable_parts"], "plan and MES", period, period=label)
        f.add("%s.heldgood" % k, "Good on held-out rows, not in totals [%s]" % label, out["held_out_good"], "MES export",
              period + "; duplicate, orphan or no readable quantity", period=label)
        f.add("%s.held" % k, "Held-out output rows [%s]" % label, out["held_out_rows"], "MES export", period + "; duplicate, orphan or no readable quantity", period=label)
        # Reconcile: each comparable part's period total equals the sum of its days.
        for part, t in parts.items():
            if t["status"] == "comparable":
                dsum = sum(r["parts"][part]["good"] for r in recs if part in r["parts"] and r["parts"][part]["status"] == "comparable")
                self.check(dsum == t["good"], "%s %s: daily good sums to the period" % (label, part))
        self.check(abs(sum(s_["scrap_usd"] or 0 for s_ in scrap.values()) - (priced or 0)) <= 0.005, "%s: priced scrap sums" % label)
        return out

    def periods(self):
        self.model["periods"] = OrderedDict()
        if not self.day:
            return
        d = self.day
        ws, _ = week_of(d)
        ms = d.replace(day=1)
        spans = [("day", [d], "production day == %s" % d),
                 ("week", [ws + timedelta(days=i) for i in range((d - ws).days + 1)], "%s to %s (Mon-Sun week to date)" % (ws, d)),
                 ("month", [ms + timedelta(days=i) for i in range((d - ms).days + 1)], "%s to %s (month to date)" % (ms, d))]
        for name, ds, period in spans:
            self.model["periods"][name] = self.rollup([str(x) for x in ds], "%s:%s..%s" % (name, ds[0], ds[-1]), period)

    # -- the short Operations page: every view, precomputed ---------------------
    def short_periods(self):
        """Day, Week (Mon-Sun containing the day) and Month (1st to the day) for every production day.

        Written to periods.json so the full page's model stays small. Every value is a figures row."""
        lo, hi = (str(self.window[0]), str(self.window[1])) if self.window else (None, None)
        if lo and self.day:   # the reported day has a view even when one export stops short of it
            lo, hi = min(lo, str(self.day)), max(hi, str(self.day))
        days = sorted(d for d in self.perday if not lo or lo <= d <= hi)
        if not days:
            self.short = None
            return
        first, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
        latest = str(self.day) if self.day and str(self.day) in self.perday else days[-1]
        rollups, views = OrderedDict(), OrderedDict()

        def build(key, kind, span, label, period):
            if key in rollups:
                return
            ds = [str(x) for x in span]
            have = [x for x in ds if x in days]
            r = self.rollup(have, "sp-" + key, period)
            evs = [e for e in self.events if e["day"] in have]
            r["downtime"] = self.rank_events(evs, "sp-" + key, period) if self.t("downtime") else None
            r["kind"] = kind
            r["span"] = [ds[0], ds[-1]]
            r["label"] = label
            r["covered"] = have
            r["missing"] = [x for x in ds if x not in self.perday or not (str(first) <= x <= str(last))]
            r["partial"] = bool(r["missing"]) if kind == "week" else (kind == "month" and span[-1].month == (span[-1] + timedelta(days=1)).month)
            if r["downtime"]:
                tie_assets(r["downtime"])
                for i, row in enumerate(r["downtime"]["asset_rows"]):
                    if row.get("tied"):
                        row["tie_id"] = "sp-%s.tie.%d" % (key, i)
                        self.F.add(row["tie_id"], "Assets tied on minutes and events [%s]" % key, len(row["assets"]),
                                   "downtime export", "same minutes and events: " + ", ".join(row["assets"]), period=key)
            if kind == "day" and have:
                r["stops"] = self.perday[have[0]]["stops"]
                for i, st in enumerate(r["stops"]):
                    self.F.add("sp-%s.stop.%d" % (key, i), "Stop %s at %s [%s]" % (st["asset"], st["start"], key),
                               st["minutes"], "downtime export", "minutes held out when the duration disagrees with the "
                               "times, or the stop is ongoing; stated %s" % st["stated_minutes"], period=key)
                    if st["minutes"] is None and "ongoing" not in st["flags"]:
                        self.F.add("sp-%s.stop.%d.stated" % (key, i), "Stated minutes, held out, %s at %s" % (st["asset"], st["start"]),
                                   st["stated_minutes"], "downtime export", "duration_minutes as written", period=key)
            self.F.add("sp-%s.covered" % key, "Days with data [%s]" % key, len(have), "exports", period, period=key)
            rollups[key] = r

        for d in days:
            dd = date.fromisoformat(d)
            ws, we = week_of(dd)
            ms = dd.replace(day=1)
            dk, wk, mk = "day:%s" % d, "week:%s..%s" % (ws, we), "month:%s..%s" % (ms, d)
            build(dk, "day", [dd], dd.strftime("%A, %Y-%m-%d"), "production day == %s" % d)
            build(wk, "week", [ws + timedelta(days=i) for i in range(7)], "Week of %s to %s" % (ws, we),
                  "%s to %s (Monday to Sunday)" % (ws, we))
            build(mk, "month", [ms + timedelta(days=i) for i in range((dd - ms).days + 1)],
                  "%s to date: 1-%d" % (dd.strftime("%B"), dd.day), "%s to %s (month to date)" % (ms, d))
            views[d] = OrderedDict([("day", dk), ("week", wk), ("month", mk)])
        self.short = OrderedDict([("latest", latest), ("days", days), ("views", views), ("rollups", rollups),
                                  ("data_window", [str(first), str(last)])])

    def decisions(self):
        """Today's decisions, in the rev 2 priority order, from computed facts only."""
        fr, ex, dp = self.model["freshness"], self.model["exceptions"], self.model["data_problems"]
        out, f = [], self.F
        # 1. Export failure: an export missing, or last night's drop holds nothing newer than days ago.
        missing = [g for g in fr["gaps"] if "did not land" in g]
        stale = fr["days_old"] is not None and fr["days_old"] > 1
        if missing or stale:
            out.append(OrderedDict([("kind", "export"), ("missing", missing), ("stale", stale),
                                    ("newest_day", fr["newest_production_day"]), ("days_old", fr["days_old"])]))
        # 2. The machine decision, for the worst asset by downtime minutes, month to date.
        mk = self.short["views"][self.short["latest"]]["month"] if self.short else None
        rk = self.short["rollups"][mk]["downtime"] if mk else None
        if rk and rk["by_asset"]:
            worst = rk["by_asset"][0]
            a = worst["key"]
            evs = sorted([e for e in self.events if e["asset"] == a and e["day"] and e["day"] <= self.short["latest"]],
                         key=lambda e: e["start"])
            open_ev = next((e for e in reversed(evs) if "ongoing" in e["flags"]), None)
            texts = Counter(e["text"] for e in evs if e["text"])
            text = texts.most_common(1)[0][0] if texts else None
            hist = ex["maintenance_history"].get(a, {})
            diagnosed = a in self.model["diagnoses"]["assets_with_diagnosis"]
            repeat = bool(hist.get("repeat_failure"))
            seized = hist.get("seizure", [])
            lockout = (not diagnosed) and (repeat or bool(seized))
            share = round(100.0 * worst["minutes"] / rk["minutes"]) if rk["minutes"] else None
            f.add("decision.machine.share", "Share of downtime minutes on %s [%s]" % (a, mk), share, "downtime export",
                  "asset minutes / total minutes, month to date; trusted rows", period=mk, unit="%")
            out.append(OrderedDict([
                ("kind", "machine"), ("asset", a), ("cell", self.cell_of(a)), ("period", mk), ("minutes", worst["minutes"]),
                ("total_minutes", rk["minutes"]), ("share_pct", share), ("approximate", worst["held_out"] > 0),
                ("reason_text", text), ("down_since", open_ev["start_local"] if open_ev else None),
                ("as_of", fr["newest_production_day"]), ("stale", stale), ("diagnosed", diagnosed),
                ("safety", next((("flagged", d["safety_reason"]) for d in self.model["diagnoses"]["safety_flagged"] if d["asset"] == a), None)),
                ("lockout", lockout), ("repeat_failure", repeat), ("seizure", seized[-1] if seized else None)]))
        # 3. Customer quality hold, for any open NCR tied to a customer.
        holds = [x for x in ex["items"] if x["kind"] == "quality_hold"]
        ncrs = self.t("ncrs")
        if holds:
            n_ncr = len(ncrs.rows) if ncrs else 0
            n_diff = len([x for x in dp["waiting_on_decision"]["ncr_keys"] if any(fl.startswith("ncr_part_differs") for fl in x["flags"])])
            f.add("decision.hold.ncrs", "NCRs in the log", n_ncr, "NCR export", "all rows")
            f.add("decision.hold.ncr_part_differs", "NCRs naming a different part than the ERP for their work order", n_diff,
                  "NCR export vs ERP", "ncr_part_differs")
            for h in holds:
                d = h["detail"]
                lot_wos = sorted({x["work_order"] for x in self.out_rows if d.get("lot") and x["lot"] == d["lot"]})
                out.append(OrderedDict([("kind", "quality_hold"), ("ncr", h["ref"]), ("customer", d["customer"]),
                                        ("work_order", d["work_order"]), ("part", d["part"]), ("lot", d["lot"]),
                                        ("orders_on_lot", lot_wos), ("open_lines", self.open_lines(d["customer"])),
                                        ("ncrs", n_ncr), ("ncrs_part_differs", n_diff)]))
        # 4. Any other decision, by what is at stake: the late jobs, priced at standard cost.
        late = ex["late_jobs"]
        if late:
            cost_col = items_col(self.t("items"), "std_cost")
            short_units = sum(x["ordered"] - x["good"] for x in late)
            usd = None
            if cost_col:
                vals = [(x["ordered"] - x["good"]) * num(self.master.get(x["part"], {}).get(cost_col, "")) for x in late
                        if num(self.master.get(x["part"], {}).get(cost_col, "")) is not None]
                usd = round(sum(vals), 2) if len(vals) == len(late) else None
            f.add("decision.late.count", "Late open work orders", len(late), "ERP vs MES", "due on or before the day; good < ordered")
            f.add("decision.late.units", "Units short on late work orders", intish(short_units), "ERP vs MES", "sum(ordered - good)")
            f.add("decision.late.usd", "Units short on late work orders, at standard cost", usd, "ERP, MES, item master",
                  "sum((ordered - good) x std_cost)", unit="USD")
            out.append(OrderedDict([("kind", "late_jobs"), ("count", len(late)), ("units_short", intish(short_units)),
                                    ("usd_at_stake", usd), ("work_orders", [x["work_order"] for x in late])]))
        shown, rest = out[:3], out[3:]
        wd = dp["waiting_on_decision"]
        remaining = OrderedDict([
            ("unit_conflicts", list(wd["unit_conflicts"].keys())),
            ("normalizations", len(wd["normalizations"])), ("provisional_rows", wd["provisional_rows"]),
            ("ncr_keys", len(wd["ncr_keys"])), ("overflow", [x["kind"] for x in rest])])
        f.add("remaining.normalizations", "Normalizations awaiting approval", remaining["normalizations"], "this run", "status != approved")
        f.add("remaining.provisional_rows", "Rows provisional until approved", remaining["provisional_rows"], "this run", "rows on unapproved normalizations")
        f.add("remaining.unit_conflicts", "Unit conflicts waiting on a factor", len(remaining["unit_conflicts"]), "this run", "units_conflict")
        self.model["short_page"] = OrderedDict([("decisions", shown), ("remaining", remaining)])

    def open_lines(self, customer):
        so = self.t("sales_orders")
        if not so:
            return None
        cust_ids = {customer}
        cu = self.t("customers")
        if cu:
            cust_ids |= {cu.get(r, "customer_id") for r in cu.rows if cu.get(r, "customer").strip() == customer}
        lines = [OrderedDict([("sales_order", so.get(r, "sales_order")), ("part", r.get("_part")), ("qty", so.get(r, "qty_ordered"))])
                 for r in so.rows if so.get(r, "status").strip().lower() in ("open", "") and
                 (so.get(r, "customer").strip() in cust_ids or so.get(r, "customer_id").strip() in cust_ids)]
        return lines

    # -- the day, the records, the figures ----------------------------------------
    def emit(self):
        out_dir = self.args.out
        os.makedirs(out_dir, exist_ok=True)
        d = str(self.day) if self.day else None
        dt_tb = self.t("downtime")
        rk = OrderedDict()
        if dt_tb and d:
            day_evs = [e for e in self.events if e["day"] == d]
            rk["day"] = self.rank_events(day_evs, d, "production day == %s" % d)
            ws, _ = week_of(self.day)
            rk["week"] = self.rank_events([e for e in self.events if e["day"] and str(ws) <= e["day"] <= d],
                                          "%s..%s" % (ws, d), "production day %s to %s (week to date, Mon-Sun)" % (ws, d))
            ms = self.day.replace(day=1)
            rk["month"] = rk["week"] if ms == ws else self.rank_events(
                [e for e in self.events if e["day"] and str(ms) <= e["day"] <= d],
                "%s..%s" % (ms, d), "production day %s to %s (month to date)" % (ms, d))
            rk["window"] = self.rank_events([e for e in self.events if e["day"]], "window", "every event in the export")
        self.model["downtime"] = rk
        if d and d in self.perday:
            today = self.perday[d]
            f = self.F
            for part, a in today["parts"].items():
                k = "out.%s.%s" % (d, part)
                f.add(k + ".planned", "Planned, %s, %s" % (part, d), a["planned"], "plan export", "plan_date == %s; part == %s" % (d, part), period=d, unit=a["item_unit"] or "")
                f.add(k + ".good", "Good, %s, %s" % (part, d), a["good"], "MES export", "production_day == %s; part == %s; held-out rows excluded" % (d, part), period=d, unit=", ".join(a["units"]))
                if a["status"] == "comparable":
                    f.add(k + ".variance", "Variance, %s, %s" % (part, d), a["variance"], "plan and MES", "good - planned", period=d)
                    f.add(k + ".variance_pct", "Variance %%, %s, %s" % (part, d), a["variance_pct"], "plan and MES", "(good - planned) / planned", period=d, unit="%")
                for n, h in enumerate(a["held_out_rows"]):
                    f.add("%s.held.%d" % (k, n), "Held-out row, %s %s" % (h["work_order"], h["shift"]), h["good"], "MES export", h["why"], period=d)
            for comp in ("availability", "performance", "quality", "oee"):
                f.add("oee.%s.%s" % (d, comp), "Site %s, %s" % (comp, d), today[comp], "plan, MES, downtime, routings",
                      "time-weighted availability; ideal ÷ run performance; pooled quality", period=d)
            for r in today["oee_by_asset"]:
                for comp in ("availability", "performance", "quality", "oee"):
                    f.add("oee.%s.%s.%s" % (d, r["asset"], comp), "%s %s, %s" % (r["asset"], comp, d), r[comp],
                          "plan, MES, downtime, routings", "; ".join(r["why_not"]) or "asset == %s" % r["asset"], period=d)
            for s in today["scrap"]:
                f.add("scrap.%s.%s" % (d, s["part"]), "Scrap qty, %s, %s" % (s["part"], d), s["scrap"], "MES export",
                      "production_day == %s; held-out rows excluded" % d, period=d, unit=s["unit"] or "")
                f.add("scrapusd.%s.%s" % (d, s["part"]), "Scrap $, %s, %s" % (s["part"], d), s["scrap_usd"], "MES x item master std_cost",
                      "unpriced when not recorded or a unit conflict", period=d, unit="USD")
            f.add("scrapusd.%s.total" % d, "Priced scrap $, %s" % d, today["scrap_priced_usd"], "MES x item master std_cost", "sum of priced parts", period=d, unit="USD")
            f.add("dtusd.%s" % d, "Downtime $, %s" % d, today["downtime_usd"], "downtime minutes x rate", today["rate_source"], period=d, unit="USD")
            self.check(abs(sum(s["scrap_usd"] or 0 for s in today["scrap"]) - (today["scrap_priced_usd"] or 0)) <= 0.005,
                       "priced scrap per part sums to the total")
            self.model["today"] = today
        else:
            self.model["today"] = None
        # Day records, one per production day the exports cover.
        records = []
        for day, r in self.perday.items():
            complete = all(self.covers(role, day) for role in ("plan", "output", "downtime"))
            gaps = [] if complete else [
                ("%s export did not land" % role) if role not in self.T else ("%s export has no rows for %s" % (role, day))
                for role in ("plan", "output", "downtime") if not self.covers(role, day)]
            if day in self.partial_shifts:
                complete = False
                gaps.append(self.partial_shifts[day])
            rk_day = self.day_reasons(day)
            records.append(OrderedDict([
                ("contract_version", 1), ("record_key", "%s_%s" % (self.site, day)), ("site", self.site),
                ("production_day", day), ("day_boundary", self.day_rule), ("run_timestamp", self.run_time.isoformat()),
                ("data_as_of", self.model["freshness"]["data_as_of"]), ("data_complete", complete), ("gaps", gaps),
                ("backfilled", day != d),
                ("planned_qty", r["planned_qty"] if self.t("plan") else None),
                ("actual_qty", r["actual_qty"] if self.t("output") else None),
                ("output_provisional", r["output_provisional"]),
                ("oee", r["oee"]), ("availability", r["availability"]), ("performance", r["performance"]),
                ("quality", r["quality"]), ("quality_convention", r["quality_convention"]),
                ("oee_basis", "per asset, time-weighted to site; excluded: " + ("; ".join(r["oee_excluded"]) or "none")),
                ("downtime_by_reason", rk_day if self.t("downtime") else None),
                ("downtime_minutes_total", r["downtime_minutes"] if self.t("downtime") else None),
                ("open_outages", r["open_outages"]),
                ("uncoded_share", self.uncoded(day) if self.t("downtime") else None),
                ("blocked_safety_unknown", len(self.model.get("diagnoses", {}).get("blocked_safety_unknown", []))),
                ("loss_usd", OrderedDict([("scrap", r["scrap_priced_usd"]), ("downtime", r["downtime_usd"]), ("currency", "USD")])),
                ("rate_source", r["rate_source"]), ("unpriced", r["unpriced"]),
                ("exceptions", [OrderedDict([("ref", x["ref"]), ("kind", x["kind"]), ("commitment_impact", x["commitment_impact"])])
                                for x in self.model["exceptions"]["items"]] if day == d else []),
                ("data_problems_count", self.model["data_problems"]["count"]),
            ]))
        # Self-checks.
        for day, r in self.perday.items():
            for part, a in r["parts"].items():
                if a["status"] == "comparable":
                    self.check(a["variance"] == intish(a["good"] - a["planned"]), "%s %s: variance = good - planned" % (day, part))
        for rec in records:
            for k in ("availability", "performance", "quality", "oee"):
                v = rec[k]
                self.check(v is None or v >= 0, "%s %s is not negative" % (rec["record_key"], k))
            if rec["oee"] is not None:
                self.check(None not in (rec["availability"], rec["performance"], rec["quality"]),
                           "%s: OEE only with all three components" % rec["record_key"])
        self.model["checks"] = OrderedDict([("run", len(self.checks)), ("failed", [c["check"] for c in self.checks if not c["ok"]])])
        n_short = sum(1 for r in self.F.rows if r["id"].startswith(Figures.SHORT_PREFIXES))
        if n_short:
            self.F.add("sp-figures.rows", "Rows in figures-short-page.csv", n_short + 1, "this file", "row count, this row included")
        self.F.add("figures.rows", "Rows in figures.csv", len(self.F.rows) - n_short - (1 if n_short else 0) + 1, "this file",
                   "row count, this row included")
        self.F.write(os.path.join(out_dir, "figures.csv"), os.path.join(out_dir, "figures-short-page.csv"))
        with open(os.path.join(out_dir, "pulse_model.json"), "w", encoding="utf-8") as f:
            json.dump(self.model, f, indent=1, default=jsonable)
        if getattr(self, "short", None):
            with open(os.path.join(out_dir, "periods.json"), "w", encoding="utf-8") as f:
                json.dump(self.short, f, indent=1, default=jsonable)
        with open(os.path.join(out_dir, "day_records.json"), "w", encoding="utf-8") as f:
            json.dump(records, f, indent=1, default=jsonable)
        return records

    def shift_coverage(self):
        """A day whose MES output carries fewer shifts than most days is not a complete plant day."""
        by_day = defaultdict(set)
        for x in self.out_rows:
            s = (x["shift"] or "").strip()
            if x["day"] and re.match(r"^\d{1,2}:\d{2}$", s):
                by_day[x["day"]].add(s)
        self.partial_shifts = {}
        if len(by_day) >= 3:
            counts = Counter(s for v in by_day.values() for s in v)
            usual = sorted((s for s, c in counts.items() if c * 2 > len(by_day)), key=hm)
            for d, have in by_day.items():
                if have and any(s not in have for s in usual):
                    self.partial_shifts[d] = "production (MES output) export has only the %s shift%s for %s; most days carry %s" % (
                        ", ".join(sorted(have, key=hm)), "" if len(have) == 1 else "s", d, ", ".join(usual))
        fr = self.model["freshness"]
        g = self.partial_shifts.get(str(self.day))
        if g:
            fr["gaps"].append(g)
            fr["day_source"] += "; only part of that day is in"
            fr["data_complete"] = self.data_complete = False

    def covers(self, role, day):
        c = self.model["freshness"]["coverage"].get(role)
        return bool(c and c["first"] <= day <= c["last"]) and role in self.T

    def day_reasons(self, day):
        g = OrderedDict()
        for e in self.events:
            if e["day"] != day or e["uncoded"] or e["blocked"]:
                continue
            a = g.setdefault(e["code"], OrderedDict([("reason_code", e["code"]), ("minutes", 0), ("events", 0), ("_held", 0)]))
            a["events"] += 1
            if e["minutes"] is None:
                a["_held"] += 1
            else:
                a["minutes"] += e["minutes"]
        rows = []
        for a in sorted(g.values(), key=lambda a: -a["minutes"]):
            rows.append(OrderedDict([("reason_code", a["reason_code"]), ("minutes", intish(a["minutes"]) if not a["_held"] else None),
                                     ("events", a["events"])]))
        return rows

    def uncoded(self, day):
        evs = [e for e in self.events if e["day"] == day and not e["blocked"]]
        un = [e for e in evs if e["uncoded"]]
        return OrderedDict([("events", len(un)), ("minutes", intish(sum(e["minutes"] for e in un if e["minutes"] is not None))),
                            ("of_events", len(evs)), ("of_minutes", intish(sum(e["minutes"] for e in evs if e["minutes"] is not None)))])

    def run(self):
        self.context()
        self.normalize()
        self.freshness()
        self.output()
        self.shift_coverage()
        self.downtime()
        self.fold_diagnoses()
        self.days()
        self.classes()
        self.exceptions()
        self.week_over_week()
        self.periods()
        self.short_periods()
        if self.short:
            self.decisions()
        records = self.emit()
        return records


def tie_assets(rk):
    """Assets tied on both minutes and events collapse into one row; single assets stay their own rows."""
    groups = OrderedDict()
    for a in rk["by_asset"]:
        groups.setdefault((a["minutes"], a["events"], a["ongoing"]), []).append(a)
    rows = []
    for (mins, evs, ong), g in groups.items():
        if len(g) == 1:
            rows.append(OrderedDict([("assets", [g[0]["key"]])] + [(k, v) for k, v in g[0].items() if k != "key"]))
        else:
            rows.append(OrderedDict([("assets", [a["key"] for a in g]), ("events", evs), ("minutes", mins), ("ongoing", ong),
                                     ("held_out", sum(a["held_out"] for a in g)), ("rank_minutes", g[0]["rank_minutes"]),
                                     ("rank_events", g[0]["rank_events"]), ("tied", True)]))
    rk["asset_rows"] = rows


def items_col(items, canon):
    return items.cols.get(canon) if items else None


def part_key(r):
    """What a plan or MES row is grouped under: its item-master part, else its own spelling. Never None."""
    return r["_part"] if r.get("_part") is not None else (r.get("_part_verbatim") or "(no part number)")


def new_part(part):
    return OrderedDict([("part", part), ("planned", None), ("good", None), ("rows_counted", 0),
                        ("plan_spellings", set()), ("mes_spellings", set()), ("units", set()),
                        ("provisional", False), ("held_out_rows", []), ("status", None),
                        ("variance", None), ("variance_pct", None), ("under_plan", None)])


def fmtq(v):
    return "absent" if v is None else str(intish(v))


def jsonable(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, set):
        return sorted(map(str, o))
    raise TypeError(type(o))


def summary(p, records):
    m = p.model
    fr = m["freshness"]
    lines = ["site: %s | production day: %s (%s) | data complete: %s" % (
        m["context"]["site"], fr["production_day"], fr["day_source"], fr["data_complete"])]
    if fr["gaps"]:
        lines.append("gaps: " + "; ".join(fr["gaps"]))
    for a in m["context"]["assumptions"]:
        lines.append("assumption: " + a)
    lines.append("data problems (numbered): %d | checked, nothing wrong: %d | exceptions: %d" % (
        m["data_problems"]["count"], len(m["data_problems"]["checked_nothing_wrong"]), len(m["exceptions"]["items"])))
    t = m.get("today")
    if t:
        lines.append("OEE %s: availability %s, performance %s, quality %s, composite %s" % (
            fr["production_day"], t["availability"], t["performance"], t["quality"], t["oee"]))
        lines.append("downtime %s: %s min trusted, %s events, %s open | scrap priced $%s | downtime $ %s (%s)" % (
            fr["production_day"], t["downtime_minutes"], t["events"], t["open_outages"], t["scrap_priced_usd"],
            t["downtime_usd"] if t["downtime_usd"] is not None else "unpriced", t["rate_source"]))
    lines.append("figures: %d rows | day records: %d | self-checks: %d run, %d failed" % (
        len(p.F.rows), len(records), m["checks"]["run"], len(m["checks"]["failed"])))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exports", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--day")
    ap.add_argument("--profile")
    ap.add_argument("--rates", help="the plant's rates file (## Plant rates), plant_setup.py's rates_path")
    ap.add_argument("--diagnoses")
    ap.add_argument("--manifest")
    ap.add_argument("--run-time")
    ap.add_argument("--tz")
    args = ap.parse_args(argv)
    p = Pulse(args)
    records = p.run()
    print(summary(p, records))
    failed = p.model["checks"]["failed"]
    if failed:
        print("SELF-CHECK FAILED:\n  " + "\n  ".join(failed), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
