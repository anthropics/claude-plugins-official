#!/usr/bin/env python3
"""
Burn Rate Calculator - Models burn rate, runway, and cash-out scenarios.

Calculates gross burn, net burn, runway under multiple scenarios,
and generates a 13-week cash flow forecast with action triggers.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


def calculate_burn(data: dict) -> dict:
    """Calculate burn metrics and runway scenarios."""
    cash = data.get("cash_balance", 0)
    monthly_revenue = data.get("monthly_revenue", 0)
    monthly_expenses = data.get("monthly_expenses", 0)
    revenue_growth_pct = data.get("monthly_revenue_growth_pct", 3)
    expense_growth_pct = data.get("monthly_expense_growth_pct", 2)
    headcount = data.get("headcount", 0)
    avg_salary = data.get("avg_fully_loaded_salary", 0)
    non_people_expenses = data.get("non_people_monthly", 0)

    # If detailed breakdown available, compute expenses
    if headcount > 0 and avg_salary > 0:
        people_cost = headcount * avg_salary
        total_expenses = people_cost + non_people_expenses
    else:
        total_expenses = monthly_expenses
        people_cost = total_expenses * 0.65  # typical SaaS split

    gross_burn = total_expenses
    net_burn = total_expenses - monthly_revenue

    results = {
        "timestamp": datetime.now().isoformat(),
        "current_state": {
            "cash_balance": cash,
            "monthly_revenue": monthly_revenue,
            "gross_burn": round(gross_burn),
            "net_burn": round(net_burn),
            "people_cost": round(people_cost),
            "non_people_cost": round(total_expenses - people_cost),
            "runway_months": round(cash / net_burn, 1) if net_burn > 0 else 999,
            "gross_margin_pct": round((1 - (monthly_revenue * 0.25) / monthly_revenue) * 100, 1) if monthly_revenue > 0 else 0,
        },
        "scenarios": [],
        "cash_forecast_13_week": [],
        "action_triggers": [],
        "preservation_levers": [],
    }

    # Scenario modeling
    scenarios = [
        {"name": "Current Trajectory", "rev_growth": revenue_growth_pct, "exp_growth": expense_growth_pct, "headcount_change": 0},
        {"name": "Hiring Freeze", "rev_growth": revenue_growth_pct, "exp_growth": 0.5, "headcount_change": 0},
        {"name": "10% Cost Cut", "rev_growth": revenue_growth_pct * 0.8, "exp_growth": -10, "headcount_change": -round(headcount * 0.1)},
        {"name": "20% Cost Cut", "rev_growth": revenue_growth_pct * 0.6, "exp_growth": -20, "headcount_change": -round(headcount * 0.2)},
        {"name": "Revenue Acceleration (+50%)", "rev_growth": revenue_growth_pct * 1.5, "exp_growth": expense_growth_pct * 1.2, "headcount_change": 0},
    ]

    for sc in scenarios:
        sc_rev = monthly_revenue
        sc_exp = total_expenses
        sc_cash = cash
        months = 0

        # Apply one-time cuts
        if sc["exp_growth"] < 0:
            sc_exp = total_expenses * (1 + sc["exp_growth"] / 100)

        while sc_cash > 0 and months < 36:
            sc_rev *= (1 + sc["rev_growth"] / 100)
            if sc["exp_growth"] >= 0:
                sc_exp *= (1 + sc["exp_growth"] / 100)
            sc_cash -= (sc_exp - sc_rev)
            months += 1

        scenario_result = {
            "name": sc["name"],
            "runway_months": months if sc_cash <= 0 else 36,
            "monthly_net_burn_adjusted": round(sc_exp - sc_rev),
            "headcount_change": sc["headcount_change"],
            "cash_out_date": (datetime.now() + timedelta(days=months * 30)).strftime("%Y-%m-%d") if sc_cash <= 0 else "36+ months",
            "runway_extension_vs_current": 0,
        }
        results["scenarios"].append(scenario_result)

    # Calculate extension vs current
    base_runway = results["scenarios"][0]["runway_months"]
    for sc in results["scenarios"]:
        sc["runway_extension_vs_current"] = sc["runway_months"] - base_runway

    # 13-week cash flow forecast
    weekly_revenue = monthly_revenue / 4.33
    weekly_payroll = people_cost / 4.33
    weekly_vendors = (total_expenses - people_cost) / 4.33
    forecast_cash = cash

    for week in range(1, 14):
        inflow = weekly_revenue * (1 + revenue_growth_pct / 100 * week / 52)
        # Payroll typically biweekly
        payroll = weekly_payroll if week % 2 == 0 else weekly_payroll * 0.1
        vendors = weekly_vendors
        total_out = payroll + vendors
        net = inflow - total_out
        forecast_cash += net

        results["cash_forecast_13_week"].append({
            "week": week,
            "date": (datetime.now() + timedelta(weeks=week)).strftime("%Y-%m-%d"),
            "inflow": round(inflow),
            "payroll": round(payroll),
            "vendors": round(vendors),
            "total_outflow": round(total_out),
            "net": round(net),
            "closing_cash": round(forecast_cash),
        })

    # Action triggers
    triggers = [
        {"runway_threshold": 12, "action": "Begin fundraising process", "severity": "info"},
        {"runway_threshold": 9, "action": "Hiring freeze on non-critical roles", "severity": "warning"},
        {"runway_threshold": 6, "action": "Discretionary spend freeze + vendor renegotiation", "severity": "high"},
        {"runway_threshold": 4, "action": "Headcount reduction plan + bridge financing", "severity": "critical"},
        {"runway_threshold": 2, "action": "Emergency cost reduction + wind-down planning", "severity": "critical"},
    ]
    current_runway = results["current_state"]["runway_months"]
    for t in triggers:
        t["triggered"] = current_runway <= t["runway_threshold"]
        results["action_triggers"].append(t)

    # Preservation levers
    results["preservation_levers"] = [
        {"lever": "Hiring freeze", "monthly_savings": round(avg_salary * 2), "runway_impact_months": round(avg_salary * 2 * 12 / net_burn, 1) if net_burn > 0 else 0},
        {"lever": "Vendor renegotiation (15%)", "monthly_savings": round(non_people_expenses * 0.15), "runway_impact_months": round(non_people_expenses * 0.15 * 12 / net_burn, 1) if net_burn > 0 else 0},
        {"lever": "Discretionary cuts", "monthly_savings": round(total_expenses * 0.05), "runway_impact_months": round(total_expenses * 0.05 * 12 / net_burn, 1) if net_burn > 0 else 0},
        {"lever": "10% headcount reduction", "monthly_savings": round(people_cost * 0.10), "runway_impact_months": round(people_cost * 0.10 * 12 / net_burn, 1) if net_burn > 0 else 0},
        {"lever": "Payment term extension (Net-60)", "monthly_savings": round(non_people_expenses * 0.08), "runway_impact_months": round(non_people_expenses * 0.08 * 12 / net_burn, 1) if net_burn > 0 else 0},
    ]

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    cs = results["current_state"]
    lines = [
        "=" * 65,
        "BURN RATE & RUNWAY ANALYSIS",
        "=" * 65,
        f"Date: {results['timestamp'][:10]}",
        "",
        "CURRENT STATE:",
        f"  Cash Balance:    ${cs['cash_balance']:>12,.0f}",
        f"  Monthly Revenue: ${cs['monthly_revenue']:>12,.0f}",
        f"  Gross Burn:      ${cs['gross_burn']:>12,.0f}",
        f"  Net Burn:        ${cs['net_burn']:>12,.0f}",
        f"  Runway:          {cs['runway_months']:>12.1f} months",
        f"  People Cost:     ${cs['people_cost']:>12,.0f} ({cs['people_cost']/cs['gross_burn']*100:.0f}% of burn)" if cs['gross_burn'] > 0 else "",
        "",
        "SCENARIO ANALYSIS:",
        f"{'Scenario':<30} {'Runway':>8} {'Extension':>10} {'Cash-Out Date':>14}",
        "-" * 65,
    ]

    for sc in results["scenarios"]:
        ext = f"+{sc['runway_extension_vs_current']}" if sc["runway_extension_vs_current"] > 0 else str(sc["runway_extension_vs_current"])
        lines.append(
            f"{sc['name']:<30} {sc['runway_months']:>6} mo {ext:>9} mo {sc['cash_out_date']:>14}"
        )

    lines.extend(["", "ACTION TRIGGERS:"])
    for t in results["action_triggers"]:
        icon = "[!!]" if t["triggered"] else "[ ]"
        lines.append(f"  {icon} At {t['runway_threshold']} months: {t['action']} [{t['severity'].upper()}]")

    lines.extend(["", "CASH PRESERVATION LEVERS:"])
    for lev in results["preservation_levers"]:
        lines.append(
            f"  {lev['lever']:<35} Saves ${lev['monthly_savings']:>8,.0f}/mo  (+{lev['runway_impact_months']:.1f} mo runway)"
        )

    lines.extend(["", "13-WEEK CASH FORECAST (summary):"])
    forecast = results["cash_forecast_13_week"]
    for week_data in [forecast[0], forecast[3], forecast[7], forecast[12]]:
        lines.append(
            f"  Week {week_data['week']:>2} ({week_data['date']}): "
            f"In ${week_data['inflow']:>8,.0f}  Out ${week_data['total_outflow']:>8,.0f}  "
            f"Balance ${week_data['closing_cash']:>10,.0f}"
        )

    lines.extend(["", "=" * 65])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Calculate burn rate, runway, and scenarios")
    parser.add_argument("--input", "-i", help="JSON file with financial data")
    parser.add_argument("--cash", type=float, help="Current cash balance")
    parser.add_argument("--revenue", type=float, help="Monthly revenue")
    parser.add_argument("--expenses", type=float, help="Monthly expenses")
    parser.add_argument("--headcount", type=int, help="Current headcount")
    parser.add_argument("--avg-salary", type=float, help="Average fully-loaded monthly salary")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    elif args.cash:
        data = {
            "cash_balance": args.cash,
            "monthly_revenue": args.revenue or 0,
            "monthly_expenses": args.expenses or 0,
            "headcount": args.headcount or 0,
            "avg_fully_loaded_salary": args.avg_salary or 12000,
            "non_people_monthly": (args.expenses or 0) * 0.35,
        }
    else:
        data = {
            "cash_balance": 5200000,
            "monthly_revenue": 250000,
            "monthly_expenses": 600000,
            "monthly_revenue_growth_pct": 5,
            "monthly_expense_growth_pct": 2,
            "headcount": 35,
            "avg_fully_loaded_salary": 11000,
            "non_people_monthly": 215000,
        }

    results = calculate_burn(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
