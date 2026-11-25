"""Render the short Operations page from the compute engine's output.

    python3 -I render_short.py --out pulse-output [--full-page-url URL] [--day YYYY-MM-DD]

Reads pulse_model.json, periods.json, figures.csv and figures-short-page.csv
from --out, written by pulse_compute.py in the same run, and writes
operations-short-<site>-<day>.html there. It selects and formats values; it
does no arithmetic. Every number it prints is a figures row, and the page
carries that row's id, so the checks at the end can prove it.

The checks at the end run on every render. Any failure exits 2 and no page is
written.
"""
import argparse
import csv
import html
import json
import os
import re
import sys
from collections import OrderedDict

DRAFT_WORDS = ("hand-edited", "mockup")
LEVELS = ("day", "week", "month")


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def idn(s):
    """An identifier (part, work order, lot): mono, and never read as a quantity."""
    return '<code class="id">%s</code>' % esc(s)


def load_figures(*paths):
    figs = OrderedDict()
    for p in paths:
        if os.path.exists(p):
            with open(p, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    figs[r["id"]] = r
    return figs


class Page:
    def __init__(self, out, full_page_url=None, day=None):
        self.out = out
        self.model = json.load(open(os.path.join(out, "pulse_model.json"), encoding="utf-8"))
        self.per = json.load(open(os.path.join(out, "periods.json"), encoding="utf-8"))
        self.figs = load_figures(os.path.join(out, "figures.csv"), os.path.join(out, "figures-short-page.csv"))
        self.url = full_page_url
        ctx, fr = self.model["context"], self.model["freshness"]
        self.site = ctx["site"]
        self.requested = day or fr["production_day"]
        self.latest = self.per["latest"]
        self.errors = []

    # -- numbers: every one is a figures row -----------------------------------
    def n(self, fid, kind="count", none=None, scale=1, unit=""):
        """A figure, formatted. `none` is what an absent value says (a label, never 0, blank or a dash)."""
        row = self.figs.get(fid)
        if row is None:
            self.errors.append("no figures row %s" % fid)
            return '<span class="na">not computable</span>'
        v = row["value"]
        if v in ("not computable", ""):
            return none or '<a class="na" href="#dp-gaps">not computable &#8595;</a>'
        try:
            x = float(v) * scale
        except ValueError:
            return '<span class="n" data-fig="%s">%s</span>' % (esc(fid), esc(v))
        if kind == "usd":
            txt = "${:,.2f}".format(x)
        elif kind == "pct":
            txt = ("{:,.1f}".format(x).rstrip("0").rstrip(".") if abs(x) % 1 else "{:,.0f}".format(x)) + "%"
        elif kind == "signed":
            txt = ("+" if x > 0 else "") + ("{:,.0f}".format(x) if x == int(x) else "{:,.1f}".format(x))
        elif kind == "signedpct":
            txt = ("+" if x > 0 else "") + "{:,.1f}".format(x) + "%"
        else:
            txt = "{:,.0f}".format(x) if x == int(x) else "{:,}".format(x)
        sc = "" if scale == 1 else ' data-scale="%s"' % scale
        return '<span class="n" data-fig="%s"%s>%s</span>%s' % (esc(fid), sc, txt, esc(unit))

    def text_fig(self, fid):
        """A sentence the engine wrote, printed verbatim from its figures row and checked as such."""
        row = self.figs.get(fid)
        if row is None:
            self.errors.append("no figures row %s" % fid)
            return ""
        return '<span class="ft" data-figtext="%s">%s</span>' % (esc(fid), esc(row["value"]))

    def has(self, fid):
        return fid in self.figs and self.figs[fid]["value"] not in ("not computable", "")

    # -- the page ---------------------------------------------------------------
    def render(self):
        m = self.model
        parts = [self.header(), self.safety(), self.freshness(), self.decisions(), self.exceptions(),
                 self.toggle(), self.views(), self.cant_show(), self.data_problems(), self.footer()]
        body = "\n".join(p for p in parts if p)
        title = "%s: short Operations page, %s" % (self.site, self.requested)
        return TEMPLATE.replace("{{TITLE}}", esc(title)).replace("{{CSS}}", CSS).replace("{{BODY}}", body) \
            .replace("{{VIEWS}}", json.dumps(self.per["views"])).replace("{{LATEST}}", json.dumps(self.latest)) \
            .replace("{{START}}", json.dumps(self.latest if self.requested not in self.per["views"] else self.requested)) \
            .replace("{{LABELS}}", json.dumps({k: self.view_label(k) for k in self.per["rollups"]}))

    def header(self):
        run = self.model["context"]["run_time"][:10]
        return ('<header class="page-header avoid"><h1>%s: short Operations page</h1>'
                '<p class="meta">%s &middot; production day %s &middot; generated %s</p>'
                '<p class="sub">Generated from the morning-plant-pulse run of %s. Read-only, nothing written to any system.</p>'
                '</header>') % (esc(self.site), esc(self.site), esc(self.requested), esc(self.model["context"]["run_time_local"]), esc(run))

    def safety(self):
        dg = self.model["diagnoses"]
        out = []
        for d in dg["safety_flagged"]:
            out.append('<div class="card critical avoid"><span class="status status--critical">Safety</span> '
                       '<strong>%s</strong>, %s to %s: %s. %s</div>' % (
                           esc(d["asset"]), esc(d["start"]), esc(d["end"]), esc(d["reason_text"]),
                           esc(d["safety_reason"] or "Flagged by breakdown-diagnosis.")))
        for d in dg["blocked_safety_unknown"]:
            out.append('<div class="card warn avoid"><span class="status status--warn">Blocked, safety status unknown</span> '
                       '<strong>%s</strong> from %s: %s. Held out of every figure on this page.</div>' % (
                           esc(d["asset"]), esc(d["start"]), esc(d["why"])))
        return '<section class="safety">%s</section>' % "".join(out) if out else ""

    def freshness(self):
        fr, ctx = self.model["freshness"], self.model["context"]
        missing = [g for g in fr["gaps"] if "did not land" in g]
        partial = [g for g in fr["gaps"] if "has only the" in g]
        other = [g for g in fr["gaps"] if g not in missing and g not in partial]   # coverage, unreadable dates, any other
        if missing:
            landed = "Last night's export did not land in full: %s." % "; ".join(esc(g) for g in missing)
        elif fr["days_old"] is not None and fr["days_old"] > 1:
            landed = "Last night's export landed, but holds nothing after %s." % esc(fr["newest_production_day"])
        elif other or (fr.get("data_complete") is False and not partial):
            landed = "Last night's export is not complete for this day."
        else:
            landed = "Last night's export landed."
        line = ['<p class="fresh avoid" id="freshness">', landed]
        if partial:
            line.append(" Not a complete plant day: %s." % "; ".join(esc(g) for g in partial))
        if other:
            line.append(" Gaps: %s." % "; ".join(esc(g) for g in other))
        if fr.get("data_as_of_local"):
            line.append(" Sources last landed %s." % esc(fr["data_as_of_local"]))
        if fr["newest_production_day"]:
            line.append(" Newest production day %s, %s day%s old." % (esc(fr["newest_production_day"]), self.n("fresh.days_old"),
                                                                      "" if fr["days_old"] == 1 else "s"))
        w = self.per["data_window"]
        line.append(" This page covers %s to %s." % (esc(w[0]), esc(w[1])))
        if ctx["time_zone_assumed"]:
            why = "no plant profile" if not ctx["profile"] else "the plant profile sets no time zone"
            line.append(" Times are plant local, assumed %s; %s." % (esc(ctx["time_zone"]), esc(why)))
        line.append("</p>")
        table = ""
        cov = fr["coverage"]
        if fr["sources_disagree"]:
            rows = "".join("<tr><td>%s</td><td>%s</td><td>%s to %s</td></tr>" % (esc(c["file"]), esc(c.get("landed") or "not dated"),
                                                                                esc(c["first"]), esc(c["last"])) for c in cov.values())
            table = ('<div class="table-scroll"><table class="avoid"><thead><tr><th>Source</th><th>Landed</th><th>Covers</th></tr>'
                     '</thead><tbody>%s</tbody></table></div>' % rows)
        return "".join(line) + table

    # -- today's decisions ------------------------------------------------------
    def decisions(self):
        sp = self.model["short_page"]
        items = []
        for d in sp["decisions"]:
            items.append("<li class=\"avoid\">%s</li>" % getattr(self, "decision_" + d["kind"])(d))
        rem = sp["remaining"]
        bits = []
        if rem["unit_conflicts"]:
            bits.append("the unit conflict%s on %s" % ("s" if len(rem["unit_conflicts"]) > 1 else "", ", ".join(idn(x) for x in rem["unit_conflicts"])))
        if rem["normalizations"]:
            bits.append("%s part-number fixes awaiting approval, %s rows provisional until then" % (
                self.n("remaining.normalizations"), self.n("remaining.provisional_rows")))
        if rem["ncr_keys"]:
            bits.append("NCR keys that disagree with the ERP")
        for k in rem["overflow"]:
            bits.append({"late_jobs": "the late work orders", "quality_hold": "a customer quality hold",
                         "machine": "a machine decision", "export": "the export"}.get(k, k))
        link = ('<a href="%s">the full Operations page</a>' % esc(self.url)) if self.url else \
            "the full Operations page (in this run's reply)"
        rest = ('<p class="remaining avoid">Also waiting on a decision: %s. Details on %s.</p>' % ("; ".join(bits), link)) if bits else \
            '<p class="remaining avoid">Nothing else is waiting on a decision. Details on %s.</p>' % link
        return '<section class="panel" id="decisions"><h2>Today&#8217;s decisions</h2><ol>%s</ol>%s</section>' % ("".join(items), rest)

    def decision_export(self, d):
        if d["missing"]:
            what = "%s." % "; ".join(esc(x[0].upper() + x[1:]) for x in d["missing"])
        else:
            what = "Last night&#8217;s drop holds nothing after %s (%s day%s old)." % (esc(d["newest_day"]), self.n("fresh.days_old"),
                                                                                     "" if d["days_old"] == 1 else "s")
        return ("<strong>Export.</strong> %s Restart the export, then re-run the pulse; a re-run rewrites this page "
                "rather than adding a second one." % what)

    def decision_machine(self, d):
        a, mk = d["asset"], "dt.sp-" + d["period"]
        s = []
        if not d["diagnosed"]:
            s.append("Safety status: not assessed.")
        elif d["safety"]:
            s.append("Safety status: flagged by breakdown-diagnosis (%s)." % esc(d["safety"][1] or "see the diagnosis record"))
        else:
            s.append("Safety status: no safety trigger in the diagnosis record; this is not a safety assessment.")
        acts = "confirm whether %s is still down, then run a breakdown diagnosis." % esc(a)
        s.append(("Lock out %s, " % esc(a) + acts) if d["lockout"] else acts[0].upper() + acts[1:])
        ev = "%s%s carries %s of downtime minutes month to date (%s of %s min)%s" % (
            esc(a), " (%s)" % esc(d["cell"]) if d["cell"] else "", self.n("decision.machine.share", "pct"),
            self.n("%s.asset.%s.minutes" % (mk, a)), self.n("%s.minutes" % mk),
            ", approximate because some of its stops have durations that disagree with their timestamps" if d["approximate"] else "")
        if d["reason_text"]:
            ev += "; MES reason text &#8220;%s&#8221;" % esc(d["reason_text"])
        if d["down_since"]:
            since = d["down_since"].replace(" (plant local)", "")
            if d["stale"]:
                ev += "; down since %s (plant local; as of %s, current state unknown)" % (esc(since), esc(d["as_of"]))
            else:
                ev += "; down since %s" % esc(d["down_since"])
        s.append(ev + ".")
        if d["lockout"]:
            if d["seizure"]:
                first = re.split(r"(?<=[.!?])\s", d["seizure"]["note"].strip())[0].rstrip(".")
                why = "%s on %s records &#8220;%s&#8221;" % (esc(d["seizure"]["maintenance_wo"]), esc(d["seizure"]["date"]), esc(first))
            else:
                why = "its maintenance history shows a repeat failure"
            s.append("Precaution, not a finding: safety hasn&#8217;t been assessed and %s." % why)
        return "<strong>Machine: %s.</strong> %s" % (esc(a), " ".join(s))

    def decision_quality_hold(self, d):
        wos = ", ".join(esc(x) for x in (d["orders_on_lot"] or [d["work_order"]]))
        s = "<strong>Quality hold: %s.</strong> %s is open against %s from lot %s, work orders %s." % (
            esc(d["customer"]), esc(d["ncr"]), idn(d["part"]), idn(d["lot"]), wos)
        if d["open_lines"] is None:
            s += " The customer&#8217;s open lines are not in this drop (no sales order export)."
        elif d["open_lines"]:
            s += " Open lines: %s." % ", ".join(esc(x["sales_order"]) for x in d["open_lines"])
        if d["ncrs_part_differs"]:
            s += " Hold scope unreliable: %s of %s NCRs name a different part than the ERP for the same work order." % (
                self.n("decision.hold.ncr_part_differs"), self.n("decision.hold.ncrs"))
        return s

    def decision_late_jobs(self, d):
        usd = (" (%s at standard cost)" % self.n("decision.late.usd", "usd")) if self.has("decision.late.usd") else ""
        s = "<strong>Late work orders.</strong> %s open work orders are past due and short by %s units%s: close them short or schedule the make-up." % (
            self.n("decision.late.count"), self.n("decision.late.units"), usd)
        if not self.model["exceptions"]["so_link"]:
            s += " Commitment impact not traceable: no work order to sales order link in the ERP."
        return s

    # -- exceptions, the whole data window ---------------------------------------
    def exceptions(self):
        cards = []
        for x in self.model["exceptions"]["items"]:
            k, d = x["kind"], x["detail"]
            if k == "late_job":
                body = "<strong>%s</strong> &middot; %s &middot; good / ordered %s &middot; due %s" % (
                    esc(x["ref"]), idn(d["part"]), self.n("exc.late." + x["ref"]), esc(d["due"]))
            elif k == "machine_down":
                body = "<strong>%s</strong> down since %s, ongoing, length unknown &middot; %s &#8220;%s&#8221;" % (
                    esc(x["ref"]), esc(d["down_since"]), esc(d["code"]), esc(d["text"]))
            elif k == "quality_hold":
                body = "<strong>%s</strong> open for %s &middot; %s &middot; %s &middot; lot %s" % (
                    esc(x["ref"]), esc(d["customer"]), esc(d["work_order"]), idn(d["part"]), idn(d["lot"]))
            else:
                body = "<strong>%s</strong> %s" % (esc(x["ref"]), esc(d.get("line", "")))
            label = {"late_job": "Late", "machine_down": "Machine down", "quality_hold": "Quality hold",
                     "one_sided_contradicted": "One-sided, contradicted"}.get(k, k)
            cards.append('<div class="card avoid"><span class="status status--warn">%s</span> %s</div>' % (label, body))
        if not cards:
            cards.append('<p>No exceptions in the data window.</p>')
        return '<section class="panel" id="exceptions"><h2>Exceptions</h2><p class="note">Covers the whole data window.</p>%s</section>' % "".join(cards)

    # -- the period toggle and its three sections ---------------------------------
    def view_label(self, key):
        r = self.per["rollups"][key]
        if r["kind"] == "day":
            return r["label"]
        if r["kind"] == "week":
            if r["partial"]:
                return "%s. Partial: data for %d of 7 days (%s); the export has nothing for %s" % (
                    r["label"], len(r["covered"]), ", ".join(r["covered"]), ", ".join(r["missing"]))
            return r["label"]
        return r["label"]

    def toggle(self):
        req_note = ""
        if self.requested not in self.per["views"]:
            req_note = "Latest day with data: %s (no data for %s)" % (self.latest, self.requested)
        return ('<div class="toggle" id="toggle"><div class="buttons" role="group" aria-label="Period">'
                '<button type="button" data-level="day">Day</button><button type="button" data-level="week">Week</button>'
                '<button type="button" data-level="month">Month</button></div>'
                '<p class="period-label" id="period-label" data-note="%s"></p><span class="pill" id="partial-pill" hidden>Partial month</span>'
                '<a href="#" id="back" hidden></a></div>' % esc(req_note))

    def views(self):
        blocks = []
        for key, r in self.per["rollups"].items():
            blocks.append('<div class="view" data-view="%s" hidden>%s%s%s</div>' % (
                esc(key), self.output_section(key, r), self.downtime_section(key, r), self.scrap_section(key, r)))
        return '<div id="views">%s</div>' % "".join(blocks)

    def heading(self, name, r):
        return "<h2>%s &middot; %s</h2>" % (name, r["kind"])

    def out_fig(self, key, part, fld, kind="count"):
        return self.n("per.sp-%s.out.%s.%s" % (key, part, fld), kind)

    def output_section(self, key, r):
        sm, k = r["summary"], r["kind"]
        sent = []
        if sm["comparable_parts"]:
            mood = "all under" if sm["all_under"] else ("all over" if sm["all_over"] else "some over, some under")
            s = "Comparable parts within %s of plan (%s)" % (self.n("per.sp-%s.maxvar" % key, "pct"), mood)
            if k != "day":
                s += ", under plan on %s days" % ", ".join("%s of %s" % (self.out_fig(key, x["part"], "days_under_plan"),
                                                                        self.out_fig(key, x["part"], "days_compared")) for x in sm["days_under"])
            sent.append(s + ".")
        else:
            sent.append("No part is comparable with plan in this view.")
        prov = [x for x in sm["provisional"]]
        if prov:
            sent.append("%s rest%s on unapproved part-number fixes." % (" and ".join(idn(x["part"]) for x in prov), "" if len(prov) > 1 else "s"))
        for h in sm["held_out_parts"]:
            sent.append("%s excludes %s (duplicate-key output, unresolved)." % (idn(h["part"]), ", ".join(esc(x) for x in h["days"])))
        for x in sm["not_comparable"]:
            sent.append("%s: not comparable, %s." % (idn(x["part"]), esc(x["why"])))
        rows = []
        for part, t in r["parts"].items():
            label = '<span class="status status--warn">Provisional</span>' if t["provisional"] else '<span class="status status--good">Exact match</span>'
            spell = "plan: %s &middot; MES: %s" % (", ".join("<code>%s</code>" % esc(x) for x in t["plan_spellings"]) or "none",
                                                  ", ".join("<code>%s</code>" % esc(x) for x in t["mes_spellings"]) or "none")
            if t["status"] == "comparable":
                plan, good = self.out_fig(key, part, "planned"), self.out_fig(key, part, "good")
                var = "%s (%s)" % (self.out_fig(key, part, "variance", "signed"), self.out_fig(key, part, "variance_pct", "signedpct"))
                last = ("yes" if t["days_under_plan"] else "no") if k == "day" else "%s of %s" % (
                    self.out_fig(key, part, "days_under_plan"), self.out_fig(key, part, "days_compared"))
            elif t["status"] == "not comparable, unit conflict":
                plan = "%s %s" % (self.out_fig(key, part, "planned"), esc(t["item_unit"] or ""))
                good = "%s %s" % (self.out_fig(key, part, "good"), esc(", ".join(t["units"])))
                var, last = '<span class="status status--warn">Unit conflict</span>', "not comparable"
            elif t["days_held_out"] and k == "day":
                plan, good, var, last = "not counted", "held out", "held out", "held out"
            else:
                plan = good = var = last = "no comparable day"
            rows.append("<tr><td><strong>%s</strong> %s<br><small>%s</small></td><td class=\"num\">%s</td><td class=\"num\">%s</td>"
                        "<td class=\"num\">%s</td><td class=\"num\">%s</td></tr>" % (idn(part), label, spell, plan, good, var, last))
        held = ""
        if r["held_out_rows"]:
            dups = self.model["data_problems"]["duplicates"]
            vals = "; ".join("%s: %s good, none picked or summed" % (esc(d["work_order"]), self.n("dup.%d.values" % i))
                             for i, d in enumerate(dups) if d["day"] in r["covered"])
            held = '<p class="note">%s held-out rows (%s good) are not in these totals%s.</p>' % (
                self.n("per.sp-%s.held" % key), self.n("per.sp-%s.heldgood" % key), ("; " + vals) if vals else "")
        table = ('<details class="tbl" open><summary>Output by part (table)</summary><div class="table-scroll"><table>'
                 '<thead><tr><th>Part</th><th class="num">Plan</th><th class="num">Good</th><th class="num">Variance</th>'
                 '<th class="num">%s</th></tr></thead><tbody>%s</tbody></table></div></details>' % (
                     "Under plan" if k == "day" else "Days under plan", "".join(rows)))
        bd = self.breakdown(r, "output") if k != "day" else ""
        return '<section class="panel">%s<p class="summary">%s</p>%s%s%s</section>' % (
            self.heading("Output against plan", r), " ".join(sent), table, held, bd)

    def breakdown(self, r, what):
        parts = list(r["parts"].keys()) if what == "output" else list(r["scrap"].keys())
        head = "".join("<th class=\"num\">%s</th>" % idn(p) for p in parts)
        if what == "scrap":
            head += '<th class="num">Priced $</th>'
        if what == "downtime":
            head = '<th class="num">Events</th><th class="num">Recorded min</th><th class="num">Ongoing</th><th class="num">Other or blank</th>'
        rows = []
        for d in r["covered"]:
            dk = "day:%s" % d
            dr = self.per["rollups"][dk]
            cells = []
            if what == "output":
                for p in parts:
                    t = dr["parts"].get(p)
                    if not t:
                        cells.append("no plan")
                    elif t["status"] == "comparable":
                        cells.append("%s / %s (%s)" % (self.out_fig(dk, p, "good"), self.out_fig(dk, p, "planned"),
                                                       self.out_fig(dk, p, "variance", "signed")))
                    elif t["status"] == "not comparable, unit conflict":
                        cells.append("unit conflict")
                    elif t["days_held_out"]:
                        cells.append("held out")
                    else:
                        cells.append("no comparable day")
            elif what == "scrap":
                for p in parts:
                    cells.append(self.scrap_qty(dk, p, dr["scrap"].get(p)) if p in dr["scrap"] else "no output")
                cells.append(self.n("per.sp-%s.scrapusd" % dk, "usd", none="none priced"))
            else:
                p = "dt.sp-" + dk
                cells = [self.n(p + ".events"), self.n(p + ".minutes"), self.n(p + ".ongoing"),
                         "%s min, %s events" % (self.n(p + ".uncoded_minutes"), self.n(p + ".uncoded_events"))]
            rows.append('<tr><td><a href="#" class="go-day" data-day="%s">%s</a></td>%s</tr>' % (
                esc(d), esc(d), "".join("<td class=\"num\">%s</td>" % c for c in cells)))
        return ('<details class="breakdown"><summary>Day by day</summary><div class="table-scroll"><table><thead><tr><th>Day</th>%s</tr>'
                '</thead><tbody>%s</tbody></table></div></details>' % (head, "".join(rows)))

    def downtime_section(self, key, r):
        dt = r.get("downtime")
        if dt is None:
            return '<section class="panel">%s<p>The downtime export did not land, so downtime is not computable for this view. ' \
                   '<a href="#dp-gaps">&#8595;</a></p></section>' % self.heading("Downtime", r)
        p = "dt.sp-" + key
        if dt["events"]:
            lead = '<p class="summary">%s events (incl. %s ongoing), %s min recorded. %s of %s events (%s) and %s of %s min (%s) carry no usable reason code (Other or blank).</p>' % (
                self.n(p + ".events"), self.n(p + ".ongoing"), self.n(p + ".minutes"), self.n(p + ".uncoded_events"),
                self.n(p + ".events"), self.n(p + ".uncoded_pct", "pct"), self.n(p + ".uncoded_minutes"), self.n(p + ".minutes"),
                self.n(p + ".uncoded_min_pct", "pct", none="share not computable"))
        else:
            lead = '<p class="summary">No stops recorded in this view.</p>'
        if r["kind"] == "day":
            rows = []
            for i, st in enumerate(r.get("stops", [])):
                if "ongoing" in st["flags"]:
                    mins = "ongoing, length unknown"
                elif st["minutes"] is None:
                    mins = 'held out: %s, %s <a href="#dp-integrity">&#8595;</a>' % (
                        (self.n("sp-%s.stop.%d.stated" % (key, i)) + " stated") if st.get("stated_minutes") is not None
                        else "no duration stated",
                        esc("/".join(st["flags"]).replace("_", " ")))
                else:
                    mins = self.n("sp-%s.stop.%d" % (key, i))
                rows.append("<tr><td>%s%s</td><td>%s</td><td class=\"num\">%s</td><td>%s</td><td>%s</td></tr>" % (
                    esc(st["asset"]), (" (%s)" % esc(st["cell"])) if st["cell"] else "", esc(st["start"]), mins, esc(st["code"]), esc(st["text"])))
            table = ('<div class="table-scroll"><table><thead><tr><th>Machine (cell)</th><th>Start</th><th class="num">Minutes</th>'
                     '<th>Code</th><th>Reason text</th></tr></thead><tbody>%s</tbody></table></div>' % "".join(rows)) if rows else ""
            return '<section class="panel">%s%s%s</section>' % (self.heading("Downtime", r), lead, table)
        rows = ['<tr class="grp"><th colspan="5">Assets</th></tr>']
        for a in dt["asset_rows"]:
            k0 = a["assets"][0]
            base = "%s.asset.%s" % (p, k0)
            if len(a["assets"]) > 1:
                name = "%s assets tied at %s min, %s events each: %s" % (self.n(a["tie_id"]), self.n(base + ".minutes"), self.n(base + ".events"),
                                                                      ", ".join(esc(x) for x in a["assets"]))
            else:
                name = esc(k0)
            rows.append(self.rank_row(name, base, a))
        rows.append('<tr class="grp"><th colspan="5">Named reason codes</th></tr>')
        for c in dt["by_code"]:
            rows.append(self.rank_row(idn(c["key"]), "%s.code.%s" % (p, c["key"]), c))
        held = ""
        if dt["held_out"]:
            held = '<p class="note">Duration conflicts, minutes held out of these totals: %s.</p>' % "; ".join(
                "%s %s to %s" % (esc(h["asset"]), esc(h["start"]), esc(h["end"])) for h in dt["held_out"])
        table = ('<div class="table-scroll"><table><thead><tr><th>Asset or code</th><th class="num">Minutes</th><th class="num">Events</th>'
                 '<th class="num">Rank by minutes</th><th class="num">Rank by events</th></tr></thead><tbody>%s</tbody></table></div>' % "".join(rows))
        return '<section class="panel">%s%s%s%s%s</section>' % (self.heading("Downtime", r), lead, table, held, self.breakdown(r, "downtime"))

    def rank_row(self, name, base, a):
        if a["ongoing"] and a["ongoing"] == a["events"]:
            mins = "ongoing, length unknown"
        else:
            mins = self.n(base + ".minutes")
        evs = self.n(base + ".events") + ((" (incl. %s ongoing)" % self.n(base + ".ongoing")) if a["ongoing"] else "")
        return '<tr><td>%s</td><td class="num">%s</td><td class="num">%s</td><td class="num">%s</td><td class="num">%s</td></tr>' % (
            name, mins, evs, self.n(base + ".rank_minutes"), self.n(base + ".rank_events"))

    def scrap_qty(self, key, part, s):
        if s is None or s["scrap"] is None:
            return '<a class="na" href="#dp-gaps">absent &#8595;</a>'
        return "%s %s" % (self.n("per.sp-%s.scrap.%s" % (key, part)), esc(s["unit"] or ""))

    def scrap_section(self, key, r):
        rows = []
        for part, s in r["scrap"].items():
            if s["scrap"] is None:
                usd = '<a class="na" href="#dp-gaps">absent &#8595;</a>'
            elif s["unit_conflict"]:
                usd = 'unpriced (set how many %s per %s)' % (esc(r["parts"].get(part, {}).get("item_unit") or "units"), esc(s["unit"]))
            else:
                usd = self.n("per.sp-%s.scrapusd.%s" % (key, part), "usd", none="unpriced (no standard cost on file)")
            share = self.n("per.sp-%s.scrapshare.%s" % (key, part), "pct", none="not priced")
            qual = self.out_fig(key, part, "quality", "pct") if part in r["parts"] else "not computable"
            if part in r["parts"] and self.has("per.sp-%s.out.%s.quality" % (key, part)):
                qual = self.n("per.sp-%s.out.%s.quality" % (key, part), "pct", scale=100)
            rows.append("<tr><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td></tr>" % (
                idn(part), self.scrap_qty(key, part, s), usd, share, qual))
        priced = self.n("per.sp-%s.scrapusd" % key, "usd", none="nothing priced")
        top = max((s for s in r["scrap"].values() if s["share_of_priced"] is not None), key=lambda s: s["share_of_priced"], default=None)
        tail = (" Top part %s is %s of it." % (idn(top["part"]), self.n("per.sp-%s.scrapshare.%s" % (key, top["part"]), "pct"))) if top else ""
        t = self.model["today"] or {}
        conv = esc(t.get("quality_convention") or "quality = good ÷ (good + scrap)")
        if not conv.startswith("quality"):
            conv = "quality = " + conv
        oee = []
        for comp, name in (("availability", "Availability"), ("performance", "performance"), ("oee", "composite OEE")):
            fid = "oee.%s.%s" % (self.model["freshness"]["production_day"], comp)
            oee.append("%s %s" % (name, self.n(fid, "pct", scale=100) if self.has(fid) else '<a class="na" href="#dp-gaps">not computable &#8595;</a>'))
        left = [r["asset"] for r in t.get("oee_by_asset") or [] if r["availability"] is None and
                any("untrusted or open" in w or "no planned production time" in w for w in r["why_not"])]
        if left and self.has("oee.%s.availability" % self.model["freshness"]["production_day"]):
            oee[0] += " (leaves out %s: a stop still open, untrusted minutes or no planned time)" % ", ".join(idn(a) for a in left)
        note = '<p class="note">%s.</p><p class="note oee">OEE, %s: %s.</p>' % (conv, esc(self.model["freshness"]["production_day"]), ", ".join(oee))
        table = ('<div class="table-scroll"><table><thead><tr><th>Part</th><th class="num">Scrap</th><th class="num">Scrap $</th>'
                 '<th class="num">Share of priced $</th><th class="num">Quality</th></tr></thead><tbody>%s</tbody></table></div>' % "".join(rows))
        bd = self.breakdown(r, "scrap") if r["kind"] != "day" else ""
        return '<section class="panel">%s<p class="summary">Scrap at standard cost, an estimate: %s.%s Downtime is unpriced: set MFG_DOWNTIME_COST_PER_HOUR or a plant profile rate.</p>%s%s%s</section>' % (
            self.heading("Scrap, cost and quality", r), priced, tail, table, note, bd) if self.model["today"] and self.model["today"]["downtime_usd"] is None else \
            '<section class="panel">%s<p class="summary">Scrap at standard cost, an estimate: %s.%s</p>%s%s%s</section>' % (self.heading("Scrap, cost and quality", r), priced, tail, table, note, bd)

    # -- what the page cannot show, the data problems, the footer -----------------
    def cant_show(self):
        dec = {d["kind"]: d for d in self.model["short_page"]["decisions"]}
        m = dec.get("machine")
        q = dec.get("quality_hold")
        worst = esc(m["asset"]) if m else "the worst machine"
        cell = esc(m["cell"]) if m and m["cell"] else "its cell"
        last = esc(self.model["freshness"]["newest_production_day"])
        items = [
            "Whether %s is down now: the data stops at %s." % (worst, last),
            "Which orders depend on %s: %s" % (cell, "the ERP holds no work order to sales order link." if not self.model["exceptions"]["so_link"]
                                               else "no routing or schedule in this drop ties orders to the cell."),
            "Whether %s received parts from lot %s: no shipment records in this drop." % (esc(q["customer"]), esc(q["lot"])) if q else
            "Whether any customer received parts from a suspect lot: no shipment records in this drop.",
        ]
        return '<section class="panel" id="cant-show"><h2>What this report can&#8217;t show yet</h2><ul>%s</ul></section>' % "".join(
            "<li>%s</li>" % x for x in items)

    def data_problems(self):
        dp, ctx, fr, t = self.model["data_problems"], self.model["context"], self.model["freshness"], self.model["today"] or {}
        wd = dp["waiting_on_decision"]
        b1 = []
        for x in wd["ncr_keys"]:
            b1.append("<li>%s on %s: %s</li>" % (esc(x["ncr"]), esc(x["work_order"]), esc("; ".join(x["flags"]))))
        for part, u in wd["unit_conflicts"].items():
            b1.append("<li>Unit conflict: %s is %s in the MES and %s in the %s; no conversion factor on file.</li>" % (
                idn(part), esc("/".join(u["export_units"])), esc(u["item_unit"]), esc("item master")))
        if wd["normalizations"]:
            b1.append("<li>%s part-number fixes awaiting approval; %s rows stay provisional until then.</li>" % (
                self.n("remaining.normalizations"), self.n("remaining.provisional_rows")))
        gaps = ["OEE components: %s." % esc("; ".join(t.get("oee_excluded") or ["see the full Operations page"]))]
        gaps += ["%s." % esc(u[0].upper() + u[1:]) for u in t.get("unpriced", [])]
        if "first-pass yield could not be applied" in (t.get("quality_convention") or ""):
            gaps.append("First-pass yield: the export has no rework column.")
        gaps.append("Output by cell, week-over-week movers and reschedule proposals: on the full Operations page.")
        if "bom" not in " ".join(x["why"] for x in ctx["files_not_used"]):
            gaps.append("Material shortages: no BOM or inventory in this drop.")
        b3 = ["%s" % esc(a) for a in ctx["assumptions"]]
        if not any(a.startswith("Production-day rule") for a in ctx["assumptions"]):
            b3.append("Production-day rule: %s." % esc(ctx["day_boundary"]))
        b3 += ["Not used: %s (%s)." % (esc(x["file"]), esc(x["why"])) for x in ctx["files_not_used"]]
        b3.append("Every source is an export file; no system was queried live.")
        b3 += ["Date window: %s." % esc(x) for x in dp["class7"]] or []
        b4 = ["<li><code>%s</code> &#8594; <code>%s</code>, %s, %s rows. Proposed, awaiting approval.</li>" % (
            esc(e["verbatim"]), esc(e["canonical"]), esc(e["rule"]), self.n("norm.%d.rows" % i))
            for i, e in enumerate(self.model["normalizations"]) if e["status"] != "approved"]
        mm = "".join("<tr><td class=\"num\">%s</td><td>%s</td><td><code>%s</code></td><td>%s</td></tr>" % (
            '<span class="ord">%d</span>' % (i + 1), esc(x["name"]), esc(x["key"]), self.text_fig("problem.%d.what" % x["n"]))
            for i, x in enumerate(dp["mismatched"]))
        integ = dp["integrity"]
        b6 = ["<li>Duration conflict: %s, %s to %s, %s.</li>" % (esc(x["asset"]), esc(x["start"]), esc(x["end"]), esc("/".join(x["flags"]).replace("_", " ")))
              for x in integ["downtime_duration_conflicts"]]
        b6 += ["<li>Blank lot: %s on %s.</li>" % (esc(x["work_order"]), esc(x["day"])) for x in integ["blank_lots"]]
        b6 += ["<li>Cross-source conflict: %s on %s: %s.</li>" % (esc(x["ncr"]), esc(x["work_order"]), esc("; ".join(x["flags"]))) for x in wd["ncr_keys"]]
        b6 += ["<li>Uninformative close-out note: %s on %s, &#8220;%s&#8221;</li>" % (esc(x["maintenance_wo"]), esc(x["asset"]), esc(x["note"]))
               for x in integ["terse_close_out_notes"]]
        b7 = ["<li>%s: %s.</li>" % (esc(c["record"]), esc(c["line"])) for c in dp["checked_nothing_wrong"]]

        def ul(items, empty):
            return "<ul>%s</ul>" % ("".join(x if x.startswith("<li>") else "<li>%s</li>" % x for x in items) if items else "<li>%s</li>" % empty)
        return ('<details class="panel dp" id="data-problems"><summary><h2>Data problems</h2></summary>'
                '<h3 id="dp-waiting">Waiting on a decision</h3>%s'
                '<h3 id="dp-gaps">Other gaps in this run</h3>%s'
                '<h3 id="dp-assumptions">Run assumptions</h3>%s'
                '<h3 id="dp-normalizations">Part-number normalizations</h3>%s'
                '<h3 id="dp-mismatched">Mismatched records &middot; %s</h3><div class="table-scroll"><table><thead><tr><th class="num">#</th>'
                '<th>Class</th><th>Key</th><th>What</th></tr></thead><tbody>%s</tbody></table></div>'
                '<h3 id="dp-integrity">Integrity flags</h3><p class="note">Not in the count above.</p>%s'
                '<h3 id="dp-checked">Checked, nothing wrong</h3><p class="note">Not problems, and in no count.</p>%s'
                '</details>') % (ul(b1, "Nothing waiting."), ul(gaps, "None."), ul(b3, "None."), ul(b4, "None awaiting approval."),
                                 self.n("mismatched.count"), mm, ul(b6, "None."), ul(b7, "None."))

    def footer(self):
        run = self.model["context"]["run_time"][:10]
        files = "figures.csv (%s rows) and figures-short-page.csv (%s rows), in the run's output folder" % (
            self.n("figures.rows"), self.n("sp-figures.rows"))
        return ('<footer class="page-footer"><p>Generated from the morning-plant-pulse run of %s. Read-only, nothing written to any system.</p>'
                '<p>Every number on this page is in the figures tab: %s, each with its filter.</p>'
                '<p>This is the short Operations page for production day %s. The full Operations page is separate; keep both.</p></footer>') % (
                    esc(run), files, esc(self.requested))

    # -- the acceptance checks that need no browser ---------------------------------
    def check(self, page):
        errs = list(self.errors)
        text = re.sub(r"<script\b.*?</script[^>]*>|<style\b.*?</style[^>]*>", "", page, flags=re.S | re.I)
        low = text.lower()
        for w in DRAFT_WORDS:
            if w in low:
                errs.append("draft wording on the page: %r" % w)
        if re.search(r"save (it|this|the page|this page)? ?over", low):
            errs.append("the footer must never say to save over the full Operations page")
        # No new numbers: every data-fig span equals its row; no other digit outside dates, times and identifiers.
        for fid, scale, shown in re.findall(r'data-fig="([^"]+)"(?: data-scale="([^"]+)")?>([^<]*)<', text):
            scale = scale or "1"
            row = self.figs.get(html.unescape(fid))
            vals = [float(x) * float(scale) for x in re.findall(r"-?\d+(?:\.\d+)?", row["value"].replace(",", ""))] if row else []
            got = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", shown.replace(",", "").replace("+", ""))]
            if not got or not all(any(abs(g - v) < 0.051 for v in vals) for g in got):
                errs.append("number %r does not match figures row %s (%s)" % (shown, fid, row and row["value"]))
        for fid, shown in re.findall(r'data-figtext="([^"]+)">([^<]*)<', text):
            row = self.figs.get(html.unescape(fid))
            if not row or html.unescape(shown) != row["value"]:
                errs.append("text %s differs from its figures row" % fid)
        bare = re.sub(r'<span class="(?:n|ft|ord)"[^>]*>[^<]*</span>|<code[^>]*>[^<]*</code>', "", text)
        bare = re.sub(r"<[^>]+>", " ", bare)
        bare = html.unescape(bare)
        idents = set()
        for r in self.per["rollups"].values():
            for t in r["parts"].values():
                idents.update([t["part"]] + t["plan_spellings"] + t["mes_spellings"])
        for e in self.model["normalizations"]:
            idents.update([e["verbatim"], e["canonical"]])

        def strings(o):
            # Every string the engine put in its output (asset, work order, lot, reason code, a
            # date-window line) is text printed verbatim, never a quantity this page computed.
            if isinstance(o, str):
                idents.add(o)
            elif isinstance(o, dict):
                idents.update(o)
                for v in o.values():
                    strings(v)
            elif isinstance(o, list):
                for v in o:
                    strings(v)
        ctx = self.model["context"]   # of the run's context, only what the page prints; never the self-check tally
        strings({k: v for k, v in self.model.items() if k not in ("context", "checks")})
        strings([ctx.get(k) for k in ("site", "time_zone", "day_boundary", "run_time_local", "assumptions", "files_not_used")])
        strings(self.per)
        for ident in sorted((i for i in idents if i and re.search(r"\d", i) and i.strip() in bare), key=len, reverse=True):
            bare = re.sub(r"(?<![\w-])%s(?![\w])" % re.escape(ident.strip()), " ", bare)
        bare = re.sub(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?|\b\d{1,2}:\d{2}\b", " ", bare)
        bare = re.sub(r"[A-Za-z][A-Za-z0-9_]*[-_ ]?[A-Za-z0-9-]*\d[A-Za-z0-9-]*", " ", bare)
        bare = re.sub(r"\b(?:of 7 days|1-\d{1,2}|Rev \d+)\b", " ", bare)
        stray = re.findall(r"(?<![\w-])\d[\d,.]*", bare)
        stray = [x for x in stray if x.rstrip(".,") != "7"]
        if stray:
            errs.append("numbers printed with no figures row: %s" % ", ".join(sorted(set(stray))[:20]))
        # Assumed time zone shown when no plant profile exists.
        ctx = self.model["context"]
        if ctx["time_zone_assumed"]:
            fresh = re.search(r'<p class="fresh[^>]*>(.*?)</p>', text, re.S)
            if not fresh or ctx["time_zone"] not in fresh.group(1) or ("no plant profile" not in fresh.group(1) and not ctx["profile"]):
                errs.append("the freshness line must name the assumed time zone and 'no plant profile'")
        # Safety label, lockout trigger, four sentences.
        decs = self.model["short_page"]["decisions"]
        mach = next((d for d in decs if d["kind"] == "machine"), None)
        if mach:
            li = re.search(r"<strong>Machine: [^<]*</strong>(.*?)</li>", text, re.S)
            body = html.unescape(re.sub(r"<[^>]+>", "", li.group(1))) if li else ""
            if not mach["diagnosed"] and "Safety status: not assessed" not in body:
                errs.append("machine decision lacks 'Safety status: not assessed'")
            if ("Lock out" in body) != bool(mach["lockout"]):
                errs.append("lockout text does not follow the lockout trigger")
            if "Lock out" in body and "Precaution, not a finding" not in body:
                errs.append("lockout without its 'Precaution, not a finding' basis")
            # Quoted source text and bracketed asides are counted with their sentence, not as sentences of their own.
            prose = re.sub(r"\u201c.*?\u201d|\([^()]*\)", "", body, flags=re.S)
            n_sent = len([x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z])", prose.strip()) if x.strip()])
            if n_sent > 4:
                errs.append("machine decision has %d sentences, more than four" % n_sent)
        order = {"export": 1, "machine": 2, "quality_hold": 3}
        ranks = [order.get(d["kind"], 4) for d in decs]
        if ranks != sorted(ranks) or len(decs) > 3:
            errs.append("decisions out of priority order: %s" % [d["kind"] for d in decs])
        # Month on the last day equals the full page's month figures.
        mk = self.per["views"][self.latest]["month"]
        full = self.model.get("periods", {}).get("month")
        if full and full["days"] and full["days"][-1] == self.latest:
            short = self.per["rollups"][mk]
            for part, t in full["parts"].items():
                s = short["parts"].get(part, {})
                if (t.get("good"), t.get("variance")) != (s.get("good"), s.get("variance")):
                    errs.append("Month view differs from the full page for %s" % part)
            if full["scrap_priced_usd"] != short["scrap_priced_usd"]:
                errs.append("Month view priced scrap differs from the full page")
        # Provisional labels survive in every view where a normalization was used.
        for key, r in self.per["rollups"].items():
            block = re.search(r'data-view="%s" hidden>(.*?)</div><div class="view"|data-view="%s" hidden>(.*)' % (re.escape(key), re.escape(key)), text, re.S)
            chunk = (block.group(1) or block.group(2)) if block else ""
            for part, t in r["parts"].items():
                if t["provisional"] and "Provisional" not in chunk:
                    errs.append("view %s drops the Provisional label" % key)
                    break
        return errs


CSS = r"""
:root{--ink:#1A1D21;--paper:#F2F3F5;--paper-raised:#FFFFFF;--line:#D6D9DD;--accent:#1F5C8B;--accent-soft:#E4EDF4;
--good:#2E7248;--good-soft:#E3EFE7;--warn:#A8641A;--warn-soft:#F7EBDA;--critical:#A93226;--critical-soft:#F9E9E7;
--font-display:'IBM Plex Sans Condensed','Arial Narrow',sans-serif;--font-body:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,sans-serif;
--font-mono:'IBM Plex Mono','SF Mono',Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ink:#E8EAEC;--paper:#15181B;--paper-raised:#1D2126;--line:#2E343A;
--accent:#6BA8D4;--accent-soft:#1B2C39;--good:#6FBF88;--good-soft:#1B2E22;--warn:#D9A15C;--warn-soft:#33271A;--critical:#DE8378;--critical-soft:#35201E}}
:root[data-theme="dark"]{--ink:#E8EAEC;--paper:#15181B;--paper-raised:#1D2126;--line:#2E343A;--accent:#6BA8D4;--accent-soft:#1B2C39;
--good:#6FBF88;--good-soft:#1B2E22;--warn:#D9A15C;--warn-soft:#33271A;--critical:#DE8378;--critical-soft:#35201E}
*{box-sizing:border-box}[hidden]{display:none!important}html,body{margin:0;background:var(--paper);color:var(--ink);font:400 15px/1.5 var(--font-body)}
.page{display:flex;flex-direction:column;gap:1.1rem;max-width:900px;margin:0 auto;padding:1.5rem 16px}
h1,h2,h3{font-family:var(--font-display);font-weight:600;margin:0 0 .5rem}h1{font-size:1.75rem}h2{font-size:1.25rem}h3{font-size:1rem;margin-top:1rem}
.meta,.sub,.note{color:var(--ink);opacity:.8;font-size:.875rem;margin:.25rem 0}
.panel{background:var(--paper-raised);border:1px solid var(--line);border-radius:4px;padding:1rem 1.25rem}
.card{background:var(--paper-raised);border:1px solid var(--line);border-radius:4px;padding:.6rem .8rem;margin:.4rem 0}
.card.critical{border-color:var(--critical)}.card.warn{border-color:var(--warn)}
.fresh{background:var(--accent-soft);border:1px solid var(--line);border-radius:4px;padding:.6rem .8rem;margin:0}
.status{display:inline-block;padding:.1rem .5rem;border-radius:2px;font:600 .72rem var(--font-body);text-transform:uppercase;letter-spacing:.04em}
.status--good{background:var(--good-soft);color:var(--good)}.status--warn{background:var(--warn-soft);color:var(--warn)}
.status--critical{background:var(--critical-soft);color:var(--critical)}
.pill{display:inline-block;padding:.1rem .5rem;border-radius:999px;background:var(--warn-soft);color:var(--warn);font-size:.75rem;font-weight:600}
.table-scroll{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;font-size:.875rem}
th,td{text-align:left;padding:.35rem .5rem;border-bottom:1px solid var(--line);vertical-align:top}
.num{text-align:right;font-family:var(--font-mono);font-variant-numeric:tabular-nums;white-space:nowrap}
td.num .na,td .na{font-family:var(--font-body)}a{color:var(--accent)}code{font-family:var(--font-mono);font-size:.85em;white-space:nowrap}
tr.grp th{background:var(--paper);font-family:var(--font-display)}
.toggle{position:sticky;top:0;z-index:5;background:var(--paper);padding:.5rem 0;border-bottom:1px solid var(--line)}
.toggle button{font:600 .875rem var(--font-body);padding:.35rem .9rem;border:1px solid var(--line);background:var(--paper-raised);color:var(--ink);cursor:pointer}
.toggle button[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.period-label{margin:.35rem 0 0;font-size:.875rem}#back{font-size:.875rem;margin-left:.5rem}
details summary{cursor:pointer;font-weight:600}details.dp>summary h2{display:inline}
.page-footer{font-size:.75rem;opacity:.85}
@media (max-width:480px){.panel{padding:.75rem}h1{font-size:1.4rem}}
@media print{
:root{--ink:#1A1D21;--paper:#FFFFFF;--paper-raised:#FFFFFF;--line:#C9CDD2;--accent:#1F5C8B;--accent-soft:#EEF3F7}
html,body,.page,section,.panel,.card,details,.table-scroll,#views,.view{height:auto!important;overflow:visible!important;max-height:none!important}
.card,li,tr,p,.fresh,.page-header,.page-footer,.avoid{break-inside:avoid}
.page-footer{display:inline-block;width:100%}
h1,h2,h3,summary{break-after:avoid}
details::details-content{content-visibility:visible;display:contents}
.toggle .buttons,#back{display:none!important}.toggle{position:static;border:0}
thead{display:table-header-group}td.num,th.num{word-break:normal;overflow-wrap:normal}
}
"""

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>{{CSS}}</style></head>
<body><main class="page">
{{BODY}}
</main>
<script>
(function(){
  var VIEWS={{VIEWS}}, LATEST={{LATEST}}, LABELS={{LABELS}}, state={day:{{START}}, level:"day"};
  function show(){
    var key=VIEWS[state.day][state.level];
    document.querySelectorAll(".view").forEach(function(v){v.hidden=(v.getAttribute("data-view")!==key);});
    document.querySelectorAll(".toggle button").forEach(function(b){b.setAttribute("aria-pressed", String(b.getAttribute("data-level")===state.level));});
    var lab=document.getElementById("period-label"); var note=lab.getAttribute("data-note");
    lab.textContent=LABELS[key]+(note&&state.day===LATEST&&state.level==="day"?". "+note:"");
    document.getElementById("partial-pill").hidden=!(state.level==="month"&&/ to date: 1-/.test(LABELS[key])&&!isMonthEnd(state.day));
    var back=document.getElementById("back"); back.hidden=(state.day===LATEST); back.textContent="Back to "+LATEST;
  }
  function isMonthEnd(d){var x=new Date(d+"T12:00:00");var y=new Date(x.getTime()+864e5);return y.getMonth()!==x.getMonth();}
  document.querySelectorAll(".toggle button").forEach(function(b){b.addEventListener("click",function(){state.level=b.getAttribute("data-level");show();});});
  document.getElementById("back").addEventListener("click",function(e){e.preventDefault();state.day=LATEST;state.level="day";show();});
  document.addEventListener("click",function(e){var a=e.target.closest(".go-day");if(!a)return;e.preventDefault();state.day=a.getAttribute("data-day");state.level="day";show();window.scrollTo(0,document.getElementById("toggle").offsetTop);});
  window.addEventListener("beforeprint",function(){document.querySelectorAll("details").forEach(function(d){d.setAttribute("data-was-open",d.open?"1":"0");d.open=true;});});
  window.addEventListener("afterprint",function(){document.querySelectorAll("details").forEach(function(d){d.open=d.getAttribute("data-was-open")==="1";});});
  show();
})();
</script>
</body></html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help="the folder pulse_compute.py wrote")
    ap.add_argument("--full-page-url", help="the Operations Command Center URL, when this run published it")
    ap.add_argument("--day", help="the production day asked for, when it differs from the engine's")
    args = ap.parse_args(argv)
    if not os.path.exists(os.path.join(args.out, "periods.json")):
        print("no periods.json in %s: run pulse_compute.py first; no short page written" % args.out, file=sys.stderr)
        return 2
    pg = Page(args.out, args.full_page_url, args.day)
    page = pg.render()
    errs = pg.check(page)
    if errs:
        print("SHORT PAGE CHECKS FAILED, no page written:\n  " + "\n  ".join(errs[:40]), file=sys.stderr)
        return 2
    name = "operations-short-%s-%s.html" % (re.sub(r"[^A-Za-z0-9]+", "-", pg.site), pg.requested)
    path = os.path.join(args.out, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    n_views = len(pg.per["rollups"])
    print("short page: %s | %d views (%d days) | checks passed" % (path, n_views, len(pg.per["days"])))
    sec = re.search(r'id="decisions">(.*?)</section>', page, re.S).group(1)
    for i, li in enumerate(re.findall(r"<li[^>]*>(.*?)</li>", sec, re.S), 1):
        print("decision %d: %s" % (i, html.unescape(re.sub(r"<[^>]+>", "", li)).strip()))
    rem = re.search(r'<p class="remaining[^>]*>(.*?)</p>', sec, re.S)
    if rem:
        print("then: " + html.unescape(re.sub(r"<[^>]+>", "", rem.group(1))).strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
