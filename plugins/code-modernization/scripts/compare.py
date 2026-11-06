#!/usr/bin/env python3
"""Deterministic judge of "does the new system give the same output as the legacy one".

    python3 compare.py <cases.json> [--out EQUIVALENCE.json] [--quiet] [--allow-outside]

The verdict comes from comparing bytes, never from a model's opinion. Input:

    {"system": "carddemo",
     "legacy": {"label": "COBOL, GnuCOBOL 3.2", "command": "optional free text"},
     "new":    {"label": "Java 17",             "command": "optional free text"},
     "cases": [{"id": "C01", "title": "Interest posting, normal account",
                "legacy": "out/legacy/C01.out", "new": "out/new/C01.out",
                "mask": [{"bytes": "278-330", "why": "run timestamp"},
                         {"regex": "\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}:\\d{2}"}],
                "approvedDifference": "optional: why a person accepted a difference",
                "note": "optional"}]}

Paths are relative to the cases file's folder and may not leave it unless --allow-outside is
given. `bytes` ranges are 0-based and inclusive; `regex` runs on the bytes decoded as latin-1.
Every masked span, on both sides, is replaced by one fixed marker, so masks never hide the
position of a difference and a variable-length match still compares equal. A case is:
  same      identical after masking
  differs   different; the first difference is recorded (a person may approve it: differs-approved)
  missing   a file is absent, unreadable or outside the cases folder. Never a pass.

A person who accepts a difference records it on the case (`"approvedDifference": "why"`), or once for every
case that shares an `input` label with a top-level `"approvedInputs": {"F23": "why"}`. A reason is required either way, and an approved difference is still listed as a
difference in the result.

Numbers that a run legitimately prints a little differently (floating-point results from another
compiler or math library) can be compared within a declared tolerance, per case or for all cases:

    "tolerance": {"rel": 1e-9, "abs": 0, "why": "last-digit rounding of the exp() in the interest formula"}

The reason is required and is recorded. Only numbers written with a decimal point or an exponent
may differ, and only within the tolerance (compared as exact decimals); every other byte, every integer and every
dotted run like 1.2.3 must match exactly. The case is `same`, with the largest relative difference
recorded; anything outside the tolerance is `differs`. A relative tolerance above 1% or an absolute one
above 1e-6 is refused: that is a different result, not rounding.

Writes EQUIVALENCE.json (default: next to the cases file). Exit 0 only when at least one case
executed, none is missing or differs (approved differences are allowed), the self-check did not
fail and some compared output was not empty; 1 otherwise; 2 for unusable input.
"""
import argparse
import bisect
import datetime
import hashlib
import decimal
import json
import math
import os
import re
import sys
import tempfile

MARK = b"\x00<MASK>\x00"
MAX_BYTES = 256 * 1024 * 1024
MAX_TOLERANT_BYTES = 32 * 1024 * 1024
# A dotted run such as 1.2.3 or 10.0.0.1 is an identifier, not a number: it is left inside the text around it.
NUMBER = re.compile(rb"(?P<dotted>\d+(?:\.\d+){2,})|(?P<num>[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?)")
MAX_ABS_TOLERANCE = 1e-6
MAX_NUMBER_CHARS = 64


class InputError(Exception):
    pass


def clip(value, limit):
    return value[:limit] if isinstance(value, str) else ""


def parse_masks(specs, cid):
    """[{"bytes": "0-3,10"} | {"regex": "..."}] -> [(kind, ranges-or-pattern, label)]."""
    masks = []
    for spec in specs if isinstance(specs, list) else []:
        if not isinstance(spec, dict) or ("bytes" in spec) == ("regex" in spec):
            raise InputError("case %s: each mask needs exactly one of 'bytes' or 'regex'" % cid)
        why = " (%s)" % clip(spec.get("why"), 120) if spec.get("why") else ""
        if "bytes" in spec:
            ranges = []
            for part in str(spec["bytes"]).split(","):
                m = re.fullmatch(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*", part)
                if not m or (m.group(2) and int(m.group(2)) < int(m.group(1))):
                    raise InputError("case %s: bad byte range %r" % (cid, part))
                ranges.append((int(m.group(1)), int(m.group(2) or m.group(1))))
            masks.append(("bytes", ranges, "bytes %s%s" % (spec["bytes"], why)))
        else:
            try:
                masks.append(("regex", re.compile(str(spec["regex"])), "regex %s%s" % (clip(str(spec["regex"]), 120), why)))
            except re.error as err:
                raise InputError("case %s: bad regex %r: %s" % (cid, spec["regex"], err))
    return masks


def parse_tolerance(spec, cid):
    """{"rel": 1e-9, "abs": 0, "why": "..."} -> a validated dict, or None when there is none."""
    if spec is None:
        return None
    if not isinstance(spec, dict):
        raise InputError("case %s: 'tolerance' must be an object with rel, abs and why" % cid)
    try:
        rel, ab = float(spec.get("rel", 0)), float(spec.get("abs", 0))
    except (TypeError, ValueError):
        raise InputError("case %s: the tolerance's rel and abs must be numbers" % cid)
    if not (math.isfinite(rel) and math.isfinite(ab)) or rel < 0 or ab < 0 or (rel == 0 and ab == 0):
        raise InputError("case %s: give a positive rel or abs tolerance" % cid)
    if rel > 0.01:
        raise InputError("case %s: a relative tolerance above 1%% is a different result, not rounding" % cid)
    if ab > MAX_ABS_TOLERANCE:
        raise InputError("case %s: an absolute tolerance above %g is a different result, not rounding" % (cid, MAX_ABS_TOLERANCE))
    why = clip(spec.get("why"), 300).strip()
    if not why:
        raise InputError("case %s: a tolerance needs a 'why' saying what legitimately differs" % cid)
    return {"rel": rel, "abs": ab, "why": why}


def split_numbers(data):
    """-> [(is_number, bytes, offset)] covering `data` end to end."""
    parts, pos = [], 0
    for m in NUMBER.finditer(data):
        if m.group("dotted") is not None:
            continue
        if m.start() > pos:
            parts.append((False, data[pos:m.start()], pos))
        parts.append((True, m.group(), m.start()))
        pos = m.end()
    if pos < len(data):
        parts.append((False, data[pos:], pos))
    return parts


def is_float(token):
    return any(c in token for c in b".eE")


def within_tolerance(a, b, tol):
    """Compare two masked outputs number by number. -> (True, stats) or (False, offset of the first real difference)."""
    if len(a) > MAX_TOLERANT_BYTES or len(b) > MAX_TOLERANT_BYTES:
        return False, first_diff(a, b) or 0
    ta, tb = split_numbers(a), split_numbers(b)
    if len(ta) != len(tb):
        return False, first_diff(a, b) or 0
    allow_abs, allow_rel = decimal.Decimal(repr(tol["abs"])), decimal.Decimal(repr(tol["rel"]))
    differing, worst = 0, 0.0
    for (na, xa, sa), (nb, xb, _) in zip(ta, tb):
        if xa == xb:
            continue
        if na != nb:
            return False, sa
        if not na:
            return False, sa + (first_diff(xa, xb) or 0)
        if not (is_float(xa) and is_float(xb)) or max(len(xa), len(xb)) > MAX_NUMBER_CHARS:
            return False, sa                      # an integer, or a very long number, must match exactly
        try:                                      # exact decimal arithmetic: no double-precision blind spot
            x, y = decimal.Decimal(xa.decode("ascii")), decimal.Decimal(xb.decode("ascii"))
            if not (x.is_finite() and y.is_finite()):
                return False, sa
            scale, diff = max(abs(x), abs(y)), abs(x - y)
            if diff > max(allow_abs, allow_rel * scale):
                return False, sa
            if scale:
                worst = max(worst, float(diff / scale))
        except (ArithmeticError, ValueError):
            return False, sa
        differing += 1
    return True, {"differing": differing, "maxRelativeDifference": worst}


def mask_spans(data, masks):
    """Merged (start, end) spans of `data` that the masks hide."""
    spans, text = [], None
    for kind, spec, _ in masks:
        if kind == "bytes":
            spans += [(s, min(e + 1, len(data))) for s, e in spec if s < len(data)]
        else:
            text = data.decode("latin-1") if text is None else text
            spans += [m.span() for m in spec.finditer(text) if m.end() > m.start()]
    merged = []
    for s, e in sorted(spans):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else:
            merged.append((s, e))
    return merged


def apply_masks(data, masks):
    """-> (masked bytes, cuts, hidden byte count); cuts map masked offsets back to file offsets."""
    out, pos, cuts, hidden, at = [], 0, [], 0, 0
    for s, e in mask_spans(data, masks):
        out.append(data[pos:s])
        at += s - pos
        cuts.append((at, s, e))
        out.append(MARK)
        at += len(MARK)
        hidden += e - s
        pos = e
    out.append(data[pos:])
    return b"".join(out), cuts, hidden


def original_offset(cuts, masked_offset):
    shift = 0
    for at, s, e in cuts:
        if masked_offset < at:
            break
        if masked_offset < at + len(MARK):
            return s
        shift += (e - s) - len(MARK)
    return masked_offset + shift


def first_diff(a, b):
    n, step, i = min(len(a), len(b)), 1 << 16, 0
    while i < n:
        j = min(i + step, n)
        if a[i:j] != b[i:j]:
            return next(k for k in range(i, j) if a[k] != b[k])
        i = j
    return n if len(a) != len(b) else None


def escape(chunk):
    out = []
    for byte in chunk:
        if byte == 0x5C:
            out.append("\\\\")
        elif 0x20 <= byte < 0x7F:
            out.append(chr(byte))
        else:
            out.append({10: "\\n", 13: "\\r", 9: "\\t"}.get(byte, "\\x%02x" % byte))
    return "".join(out).replace("\\x00<MASK>\\x00", "[masked]")


def context(masked, off):
    before = escape(masked[max(0, off - 12):off])[-12:]
    after = escape(masked[off:off + 28])[:28] if off < len(masked) else "<end of output>"
    return before + after, len(before)


def read_file(rel, base, allow_outside):
    """-> (bytes, None) or (None, plain-English problem)."""
    if not isinstance(rel, str) or not rel:
        return None, "no path was given"
    path = os.path.join(base, rel)
    try:
        real, root = os.path.realpath(path), os.path.realpath(base)
        if not allow_outside and os.path.commonpath([root, real]) != root:
            return None, "the path leaves the cases folder (pass --allow-outside if that is intended)"
        if not os.path.exists(path):
            return None, "the file does not exist"
        if os.path.getsize(path) > MAX_BYTES:
            return None, "the file is larger than %d MB" % (MAX_BYTES >> 20)
        with open(path, "rb") as fh:
            return fh.read(), None
    except (OSError, ValueError) as err:
        return None, "the file could not be read (%s)" % err.__class__.__name__


def rel_to(path, folder):
    try:
        return os.path.relpath(path, folder).replace(os.sep, "/")
    except ValueError:
        return path


def judge(case, index, base, out_dir, allow_outside, default_tolerance=None, approved_inputs=None):
    """-> (case record, legacy bytes or None, masks)."""
    cid = clip(str(case.get("id") or "C%02d" % (index + 1)), 80)
    masks = parse_masks(case.get("mask"), cid)
    tol = parse_tolerance(case["tolerance"] if "tolerance" in case else default_tolerance, cid)
    rec = {"id": cid, "title": clip(case.get("title"), 300), "verdict": "missing", "reason": "",
           "legacyPath": "", "newPath": "", "legacySha256": "", "newSha256": "",
           "masked": [m[2] for m in masks],
           "approvedDifference": clip(case.get("approvedDifference") or (approved_inputs or {}).get(str(case.get("input", "")), ""), 500),
           "note": clip(case.get("note"), 500)}
    data, problems = {}, []
    for side in ("legacy", "new"):
        given = case.get(side)
        rec[side + "Path"] = rel_to(os.path.join(base, given), out_dir) if isinstance(given, str) and given else ""
        data[side], why = read_file(given, base, allow_outside)
        if why:
            problems.append("The %s output was not compared: %s (%s)." % (side, why, clip(str(given), 200)))
    if problems:
        rec["reason"] = " ".join(problems)
        return rec, None, masks, tol
    legacy, new = data["legacy"], data["new"]
    rec["legacySha256"], rec["newSha256"] = hashlib.sha256(legacy).hexdigest(), hashlib.sha256(new).hexdigest()
    a, cuts, hid_a = apply_masks(legacy, masks)
    b, _, hid_b = apply_masks(new, masks)
    rec["bytes"], rec["maskedBytes"] = {"legacy": len(legacy), "new": len(new)}, {"legacy": hid_a, "new": hid_b}
    rec["empty"] = not legacy and not new
    at = first_diff(a, b)
    if at is None:
        rec["verdict"] = "same"
        rec["reason"] = ("Both outputs are empty, so nothing was compared." if rec["empty"] else
                         "Identical after masking: %d of %d bytes were hidden by %d mask(s)." % (hid_a, len(legacy), len(masks)) if masks else
                         "Identical, %d bytes." % len(legacy))
        return rec, legacy, masks, tol
    seen, seen_at = context(a, at)
    got, _ = context(b, at)
    line = a.count(b"\n", 0, at) + 1
    rec["firstDiff"] = {"offset": original_offset(cuts, at), "line": line, "legacy": seen, "new": got, "at": seen_at}
    where = "line %d, byte %d" % (line, rec["firstDiff"]["offset"])
    if at >= len(a) or at >= len(b):
        rec["reason"] = "The %s output ends at %s while the %s output continues." % (
            "legacy" if at >= len(a) else "new", where, "new" if at >= len(a) else "legacy")
    else:
        rec["reason"] = "The outputs first differ at %s." % where
    if tol:
        rec["tolerance"] = dict(tol)
        ok, info = within_tolerance(a, b, tol)
        if ok:
            rec["verdict"] = "same"
            rec["withinTolerance"] = info
            rec["reason"] = ("Identical apart from %d number(s) that differ within the declared tolerance "
                             "(relative %g, absolute %g; largest relative difference %.3g). Declared reason: %s"
                             % (info["differing"], tol["rel"], tol["abs"], info["maxRelativeDifference"], clip(tol["why"], 200)))
            return rec, legacy, masks, tol
        line = a.count(b"\n", 0, info) + 1
        rec["reason"] = "A number or text differs beyond the declared tolerance at line %d, byte %d." % (line, original_offset(cuts, info))
    if rec["approvedDifference"].strip():
        rec["verdict"] = "differs-approved"
        rec["reason"] += " A person approved this difference: %s" % clip(rec["approvedDifference"], 200)
    else:
        rec["verdict"] = "differs"
    return rec, legacy, masks, tol


def differs_under(changed, data, masks, tol):
    """Would the comparator report `changed` as different from `data`?"""
    a, b = apply_masks(data, masks)[0], apply_masks(changed, masks)[0]
    return a != b and not (tol and within_tolerance(a, b, tol)[0])


def self_check(items):
    """Prove the comparator can fail: change one unmasked byte of each legacy output; it must differ."""
    tested = 0
    for cid, data, masks, tol in items:
        if not data:
            continue
        tested += 1
        free, pos = [], 0
        for s, e in mask_spans(data, masks) + [(len(data), len(data))]:
            if s > pos:
                free.append((pos, s))
            pos = e
        if not free:
            return False, "case %s: the masks hide every byte, so no difference could ever be seen" % cid
        biggest = max(free, key=lambda f: f[1] - f[0])
        flip = lambda p: data[:p] + bytes([data[p] ^ 1]) + data[p + 1:]
        spots = [free[0][0], free[-1][1] - 1, (biggest[0] + biggest[1]) // 2]
        caught = any(differs_under(flip(p), data, masks, tol) for p in spots)
        if tol and caught:
            # A tolerance must never hide a change to the numbers it covers: changing the leading digit of every
            # sampled float that is not masked has to be reported, or the tolerance is too loose to prove anything.
            for m in list(NUMBER.finditer(data[:1 << 20]))[:200]:
                token = m.group("num")
                if token is None or not is_float(token) or not any(a <= m.start() < b for a, b in free):
                    continue
                at = m.start() + next(i for i, c in enumerate(token) if 48 <= c <= 57)
                if not differs_under(flip(at), data, masks, tol):
                    caught = False
                    break
        if not caught:
            return False, "case %s: a one-byte change to the legacy output was not reported as different%s" % (
                cid, " (the tolerance may be too loose)" if tol else "")
    if not tested:
        return None, "not applicable: no executed case had bytes to test"
    return True, "each legacy output was compared with a copy changed by one byte and reported as different"


def totals(records, executed, count):
    t = {"cases": len(records), "executed": executed, "same": count("same"), "differs": count("differs"),
         "differsApproved": count("differs-approved"), "missing": count("missing")}
    tolerant = sum(1 for r in records if r.get("withinTolerance"))
    if tolerant:  # additive: absent unless a declared tolerance was used
        t["sameWithinTolerance"] = tolerant
    return t


def run(cases_path, out_path=None, allow_outside=False):
    """-> the EQUIVALENCE record. Raises InputError for a cases file that cannot be used."""
    try:
        with open(cases_path, "rb") as fh:
            spec = json.loads(fh.read().decode("utf-8-sig"))
    except (OSError, ValueError) as err:
        raise InputError("cannot read %s: %s" % (cases_path, err))
    if not isinstance(spec, dict) or not isinstance(spec.get("cases"), list):
        raise InputError("%s must be a JSON object with a 'cases' list" % cases_path)
    base = os.path.dirname(os.path.abspath(cases_path))
    out_dir = os.path.dirname(os.path.abspath(out_path)) if out_path else base
    records, items, ids = [], [], set()
    approved = {str(k): v for k, v in spec["approvedInputs"].items() if isinstance(v, str) and v.strip()} if isinstance(spec.get("approvedInputs"), dict) else {}
    for i, case in enumerate(spec["cases"]):
        if not isinstance(case, dict):
            raise InputError("case %d is not an object" % (i + 1))
        rec, data, masks, tol = judge(case, i, base, out_dir, allow_outside, spec.get("tolerance"), approved)
        if rec["id"] in ids:
            raise InputError("duplicate case id %r" % rec["id"])
        ids.add(rec["id"])
        records.append(rec)
        if data is not None:
            items.append((rec["id"], data, masks, tol))
    passed, detail = self_check(items)
    count = lambda v: sum(1 for r in records if r["verdict"] == v)
    ends = lambda key: {k: clip(spec.get(key, {}).get(k), 300) for k in ("label", "command")} if isinstance(spec.get(key), dict) else {"label": "", "command": ""}
    return {"system": clip(spec.get("system"), 200), "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "legacy": ends("legacy"), "new": ends("new"), "selfCheck": {"passed": passed, "detail": detail},
            "totals": totals(records, len(items), count), "cases": records}


def verdict_of(result):
    """-> None when proven, else the reason it is not."""
    t = result["totals"]
    if t["executed"] == 0:
        return "no case executed"
    if t["missing"] or t["differs"]:
        return " and ".join(filter(None, ["%d case(s) differ" % t["differs"] if t["differs"] else "",
                                         "%d case(s) are missing" % t["missing"] if t["missing"] else ""]))
    if result["selfCheck"]["passed"] is False:
        return "the self-check failed: " + result["selfCheck"]["detail"]
    if all(r.get("empty") for r in result["cases"] if r["verdict"] != "missing"):
        return "every compared output was empty"
    return None


def write_atomic(path, text):
    path = os.path.abspath(path)
    folder = os.path.dirname(path)
    for p in (path, folder):
        if os.path.islink(p):
            raise InputError("refusing to write through a symbolic link: %s" % p)
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".equivalence-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(text.encode("utf-8"))
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)
        os.replace(tmp, path)
    except BaseException:
        if os.path.lexists(tmp):
            os.unlink(tmp)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compare legacy and new outputs byte for byte.")
    ap.add_argument("cases", help="cases.json (see the module docstring for the schema)")
    ap.add_argument("--out", help="where to write EQUIVALENCE.json (default: next to the cases file)")
    ap.add_argument("--quiet", action="store_true", help="write the file, print nothing")
    ap.add_argument("--allow-outside", action="store_true", help="allow case paths that leave the cases folder")
    args = ap.parse_args(argv)
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.cases)), "EQUIVALENCE.json")
    try:
        result = run(args.cases, out, args.allow_outside)
    except InputError as err:
        print("compare.py: %s" % err, file=sys.stderr)
        return 2
    try:
        write_atomic(out, json.dumps(result, indent=2, ensure_ascii=True) + "\n")
    except InputError as err:
        print("compare.py: %s" % err, file=sys.stderr)
        return 2
    problem = verdict_of(result)
    if not args.quiet:
        t, plain = result["totals"], lambda s: re.sub(r"[\x00-\x1f\x7f-\x9f]", "?", s)
        print("equivalence cases executed: %d" % t["executed"])
        print("same %d%s | differs %d | differs but approved %d | missing %d | of %d cases" %
              (t["same"], " (%d within a declared tolerance)" % t["sameWithinTolerance"] if t.get("sameWithinTolerance") else "",
               t["differs"], t["differsApproved"], t["missing"], t["cases"]))
        sc = result["selfCheck"]
        print("self-check: %s - %s" % ({True: "passed", False: "FAILED", None: "not applicable"}[sc["passed"]], plain(sc["detail"])))
        for r in result["cases"]:
            if r["verdict"] != "same" or r.get("withinTolerance"):
                print("  %s  %s: %s" % (plain(r["id"]), r["verdict"], plain(r["reason"])[:200]))
        print(("NOT PROVEN: %s" % problem) if problem else "PROVEN: %d case(s) executed, none differ" % t["executed"])
        print("wrote %s" % out)
    return 1 if problem else 0


if __name__ == "__main__":
    sys.exit(main())
