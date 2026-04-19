#!/usr/bin/env python3
"""
Financial Scenario Modeler - Three-scenario financial projection engine.

Models base, upside, and downside scenarios with probability weighting.
Produces board-ready projections with sensitivity analysis and decision triggers.
"""

import argparse
import json
import math
import sys
from datetime import datetime


def project_scenario(base: dict, scenario: dict, quarters: int = 8) -> list:
    """Project financials for a scenario over N quarters."""
    projections = []
    arr = base.get("arr", 0)
    expenses = base.get("quarterly_expenses", 0)
    cash = base.get("cash_balance", 0)

    growth_rate = scenario.get("quarterly_arr_growth_pct", 10) / 100
    expense_growth = scenario.get("quarterly_expense_growth_pct", 5) / 100
    gross_margin = scenario.get("gross_margin_pct", 75) / 100
    churn_rate = scenario.get("quarterly_churn_pct", 2) / 100

    for q in range(1, quarters + 1):
        # Revenue dynamics
        new_arr = arr * growth_rate
        churned_arr = arr * churn_rate
        net_new_arr = new_arr - churned_arr
        arr += net_new_arr
        quarterly_revenue = arr / 4

        # Cost dynamics
        expenses *= (1 + expense_growth)
        gross_profit = quarterly_revenue * gross_margin
        operating_income = gross_profit - expenses
        free_cash_flow = operating_income * 0.85  # simplified for WC and capex

        cash += free_cash_flow

        # Derived metrics
        burn_multiple = (-operating_income / net_new_arr) if net_new_arr > 0 and operating_income < 0 else 0
        rule_of_40 = (growth_rate * 4 * 100) + (operating_income / quarterly_revenue * 100) if quarterly_revenue > 0 else 0
        runway = (cash / (-operating_income)) if operating_income < 0 else 999

        projections.append({
            "quarter": q,
            "arr": round(arr),
            "quarterly_revenue": round(quarterly_revenue),
            "net_new_arr": round(net_new_arr),
            "gross_profit": round(gross_profit),
            "gross_margin_pct": round(gross_margin * 100, 1),
            "quarterly_expenses": round(expenses),
            "operating_income": round(operating_income),
            "operating_margin_pct": round(operating_income / quarterly_revenue * 100, 1) if quarterly_revenue > 0 else 0,
            "free_cash_flow": round(free_cash_flow),
            "cash_balance": round(cash),
            "burn_multiple": round(burn_multiple, 2),
            "rule_of_40": round(rule_of_40, 1),
            "runway_months": round(runway * 3, 1) if runway < 999 else 999,
            "arr_growth_yoy_pct": round((1 + growth_rate) ** 4 * 100 - 100, 1),
        })

    return projections


def model_scenarios(data: dict) -> dict:
    """Run full scenario analysis."""
    base_financials = {
        "arr": data.get("arr", 0),
        "quarterly_expenses": data.get("quarterly_expenses", 0),
        "cash_balance": data.get("cash_balance", 0),
    }

    scenarios_config = data.get("scenarios", {
        "base": {
            "name": "Base Case",
            "probability": 0.50,
            "quarterly_arr_growth_pct": 10,
            "quarterly_expense_growth_pct": 5,
            "gross_margin_pct": 75,
            "quarterly_churn_pct": 2,
        },
        "upside": {
            "name": "Upside",
            "probability": 0.25,
            "quarterly_arr_growth_pct": 15,
            "quarterly_expense_growth_pct": 7,
            "gross_margin_pct": 78,
            "quarterly_churn_pct": 1.5,
        },
        "downside": {
            "name": "Downside",
            "probability": 0.25,
            "quarterly_arr_growth_pct": 5,
            "quarterly_expense_growth_pct": 3,
            "gross_margin_pct": 72,
            "quarterly_churn_pct": 3,
        },
    })

    quarters = data.get("projection_quarters", 8)

    results = {
        "timestamp": datetime.now().isoformat(),
        "company": data.get("company", "Company"),
        "starting_arr": base_financials["arr"],
        "starting_cash": base_financials["cash_balance"],
        "projection_quarters": quarters,
        "scenarios": {},
        "probability_weighted": {},
        "sensitivity": {},
        "decision_triggers": [],
        "board_summary": {},
    }

    # Project each scenario
    for key, config in scenarios_config.items():
        projections = project_scenario(base_financials, config, quarters)
        final = projections[-1] if projections else {}
        results["scenarios"][key] = {
            "name": config["name"],
            "probability": config["probability"],
            "assumptions": {
                "quarterly_arr_growth": f"{config['quarterly_arr_growth_pct']}%",
                "quarterly_expense_growth": f"{config['quarterly_expense_growth_pct']}%",
                "gross_margin": f"{config['gross_margin_pct']}%",
                "quarterly_churn": f"{config['quarterly_churn_pct']}%",
            },
            "projections": projections,
            "year_2_arr": final.get("arr", 0),
            "year_2_operating_margin": final.get("operating_margin_pct", 0),
            "year_2_cash": final.get("cash_balance", 0),
            "year_2_rule_of_40": final.get("rule_of_40", 0),
            "profitability_quarter": next(
                (p["quarter"] for p in projections if p["operating_income"] > 0), None
            ),
        }

    # Probability-weighted outcomes
    pw_arr = sum(
        s["year_2_arr"] * s["probability"]
        for s in results["scenarios"].values()
    )
    pw_cash = sum(
        s["year_2_cash"] * s["probability"]
        for s in results["scenarios"].values()
    )
    pw_margin = sum(
        s["year_2_operating_margin"] * s["probability"]
        for s in results["scenarios"].values()
    )
    results["probability_weighted"] = {
        "expected_arr": round(pw_arr),
        "expected_cash": round(pw_cash),
        "expected_operating_margin": round(pw_margin, 1),
        "arr_range": f"${min(s['year_2_arr'] for s in results['scenarios'].values()):,.0f} - ${max(s['year_2_arr'] for s in results['scenarios'].values()):,.0f}",
    }

    # Sensitivity analysis
    base_arr = results["scenarios"].get("base", {}).get("year_2_arr", 0)
    for var_name, var_range in [("growth", [-5, -2, 0, 2, 5]), ("churn", [-1, -0.5, 0, 0.5, 1]), ("margin", [-5, -2, 0, 2, 5])]:
        sensitivity = []
        for delta in var_range:
            adj_config = dict(scenarios_config.get("base", {}))
            if var_name == "growth":
                adj_config["quarterly_arr_growth_pct"] += delta
            elif var_name == "churn":
                adj_config["quarterly_churn_pct"] += delta
            elif var_name == "margin":
                adj_config["gross_margin_pct"] += delta
            proj = project_scenario(base_financials, adj_config, quarters)
            final_arr = proj[-1]["arr"] if proj else 0
            sensitivity.append({
                "delta": f"{delta:+.1f}%",
                "year_2_arr": round(final_arr),
                "impact_pct": round((final_arr - base_arr) / base_arr * 100, 1) if base_arr > 0 else 0,
            })
        results["sensitivity"][var_name] = sensitivity

    # Decision triggers
    downside = results["scenarios"].get("downside", {})
    downside_projs = downside.get("projections", [])
    for p in downside_projs:
        if p.get("runway_months", 999) < 9 and p["quarter"] <= 4:
            results["decision_triggers"].append({
                "quarter": p["quarter"],
                "trigger": f"Downside runway drops to {p['runway_months']:.0f} months",
                "action": "Initiate fundraising or cost reduction",
                "severity": "critical",
            })
            break

    if downside.get("profitability_quarter") is None:
        results["decision_triggers"].append({
            "quarter": "N/A",
            "trigger": "Downside never reaches profitability in projection window",
            "action": "Ensure fundraising plan covers downside scenario",
            "severity": "high",
        })

    # Board summary
    base_sc = results["scenarios"].get("base", {})
    results["board_summary"] = {
        "headline": f"Projected ARR: ${pw_arr:,.0f} (probability-weighted, {quarters}Q horizon)",
        "base_case_arr": f"${base_sc.get('year_2_arr', 0):,.0f}",
        "upside_arr": f"${results['scenarios'].get('upside', {}).get('year_2_arr', 0):,.0f}",
        "downside_arr": f"${results['scenarios'].get('downside', {}).get('year_2_arr', 0):,.0f}",
        "key_assumption": f"Base case: {scenarios_config.get('base', {}).get('quarterly_arr_growth_pct', 0)}% quarterly growth, {scenarios_config.get('base', {}).get('quarterly_churn_pct', 0)}% churn",
        "key_risk": "Downside churn or slower growth depletes runway" if any(t["severity"] == "critical" for t in results["decision_triggers"]) else "No critical triggers in projection window",
    }

    return results


def format_text(results: dict) -> str:
    """Format as board-ready text."""
    lines = [
        "=" * 70,
        "FINANCIAL SCENARIO MODEL",
        "=" * 70,
        f"Company: {results['company']}",
        f"Starting ARR: ${results['starting_arr']:,.0f}  |  Cash: ${results['starting_cash']:,.0f}",
        f"Horizon: {results['projection_quarters']} quarters",
        "",
        "SCENARIO COMPARISON (End of Projection):",
        f"{'Scenario':<18} {'Prob':>5} {'ARR':>12} {'Op Margin':>10} {'Cash':>12} {'Ro40':>6} {'Profit Q':>9}",
        "-" * 70,
    ]

    for key, sc in results["scenarios"].items():
        profit_q = f"Q{sc['profitability_quarter']}" if sc["profitability_quarter"] else "N/A"
        lines.append(
            f"{sc['name']:<18} {sc['probability']:>4.0%} ${sc['year_2_arr']:>10,.0f} "
            f"{sc['year_2_operating_margin']:>9.1f}% ${sc['year_2_cash']:>10,.0f} "
            f"{sc.get('year_2_rule_of_40', 0):>5.0f} {profit_q:>9}"
        )

    pw = results["probability_weighted"]
    lines.extend([
        "",
        f"PROBABILITY-WEIGHTED: ARR ${pw['expected_arr']:,.0f}  |  "
        f"Margin {pw['expected_operating_margin']:.1f}%  |  Cash ${pw['expected_cash']:,.0f}",
        f"ARR Range: {pw['arr_range']}",
    ])

    # Sensitivity
    lines.extend(["", "SENSITIVITY ANALYSIS (impact on Year 2 ARR):"])
    for var, data in results["sensitivity"].items():
        impacts = "  ".join(f"{d['delta']}:{d['impact_pct']:+.1f}%" for d in data)
        lines.append(f"  {var.title()}: {impacts}")

    # Triggers
    if results["decision_triggers"]:
        lines.extend(["", "DECISION TRIGGERS:"])
        for t in results["decision_triggers"]:
            lines.append(f"  [{t['severity'].upper()}] {t['trigger']} -> {t['action']}")

    # Board summary
    bs = results["board_summary"]
    lines.extend([
        "",
        "BOARD SUMMARY:",
        f"  {bs['headline']}",
        f"  Key Assumption: {bs['key_assumption']}",
        f"  Key Risk: {bs['key_risk']}",
    ])

    lines.extend(["", "=" * 70])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Model financial scenarios with probability weighting")
    parser.add_argument("--input", "-i", help="JSON file with scenario data")
    parser.add_argument("--arr", type=float, help="Current ARR")
    parser.add_argument("--expenses", type=float, help="Quarterly expenses")
    parser.add_argument("--cash", type=float, help="Cash balance")
    parser.add_argument("--quarters", type=int, default=8, help="Projection quarters (default: 8)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    elif args.arr:
        data = {
            "company": "Company",
            "arr": args.arr,
            "quarterly_expenses": args.expenses or args.arr * 0.35,
            "cash_balance": args.cash or 5000000,
            "projection_quarters": args.quarters,
        }
    else:
        data = {
            "company": "SaaSCo",
            "arr": 3000000,
            "quarterly_expenses": 900000,
            "cash_balance": 5200000,
            "projection_quarters": args.quarters,
        }

    results = model_scenarios(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
