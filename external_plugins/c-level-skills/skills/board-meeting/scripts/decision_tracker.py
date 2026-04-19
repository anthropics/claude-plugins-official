#!/usr/bin/env python3
"""
Board Decision Tracker - Track and audit board meeting decisions.

Manages decision logs with ownership, deadlines, review dates,
conflict detection, and DO_NOT_RESURFACE flags. Produces audit reports.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


def track_decisions(data: dict) -> dict:
    """Analyze decision history and identify issues."""
    decisions = data.get("decisions", [])
    today = datetime.now()

    results = {
        "timestamp": today.isoformat(),
        "total_decisions": len(decisions),
        "summary": {"active": 0, "overdue_review": 0, "overdue_action": 0, "completed": 0, "superseded": 0, "do_not_resurface": 0},
        "decisions": [],
        "overdue_reviews": [],
        "overdue_actions": [],
        "conflicts": [],
        "recurring_topics": {},
        "owner_workload": {},
        "recommendations": [],
    }

    topic_count = {}
    for d in decisions:
        decision_id = d.get("id", "")
        topic = d.get("topic", "")
        status = d.get("status", "active")
        owner = d.get("owner", "Unassigned")
        action_items = d.get("action_items", [])
        review_date_str = d.get("review_date", "")
        decision_date_str = d.get("decision_date", "")
        dnr = d.get("do_not_resurface", False)
        superseded_by = d.get("superseded_by", None)

        # Parse dates
        review_date = None
        decision_date = None
        try:
            if review_date_str:
                review_date = datetime.strptime(review_date_str, "%Y-%m-%d")
            if decision_date_str:
                decision_date = datetime.strptime(decision_date_str, "%Y-%m-%d")
        except ValueError:
            pass

        # Check overdue review
        review_overdue = review_date and today > review_date and status == "active"
        # Check overdue actions
        overdue_items = []
        for ai in action_items:
            due_str = ai.get("due_date", "")
            try:
                due = datetime.strptime(due_str, "%Y-%m-%d")
                if today > due and ai.get("status", "") != "complete":
                    overdue_items.append(ai)
            except ValueError:
                pass

        # Track topics
        topic_key = topic.lower().strip()
        topic_count[topic_key] = topic_count.get(topic_key, 0) + 1

        # Track owner workload
        if owner not in results["owner_workload"]:
            results["owner_workload"][owner] = {"active": 0, "overdue": 0}
        if status == "active":
            results["owner_workload"][owner]["active"] += 1
        if review_overdue or overdue_items:
            results["owner_workload"][owner]["overdue"] += len(overdue_items) + (1 if review_overdue else 0)

        decision_result = {
            "id": decision_id,
            "topic": topic,
            "status": status,
            "owner": owner,
            "decision_date": decision_date_str,
            "review_date": review_date_str,
            "review_overdue": review_overdue,
            "days_since_review_due": (today - review_date).days if review_overdue else 0,
            "action_items_total": len(action_items),
            "action_items_overdue": len(overdue_items),
            "do_not_resurface": dnr,
            "superseded_by": superseded_by,
        }
        results["decisions"].append(decision_result)

        # Summary counts
        if dnr:
            results["summary"]["do_not_resurface"] += 1
        elif superseded_by:
            results["summary"]["superseded"] += 1
        elif status == "completed":
            results["summary"]["completed"] += 1
        else:
            results["summary"]["active"] += 1

        if review_overdue:
            results["summary"]["overdue_review"] += 1
            results["overdue_reviews"].append(decision_result)
        if overdue_items:
            results["summary"]["overdue_action"] += len(overdue_items)
            results["overdue_actions"].extend([
                {"decision_id": decision_id, "topic": topic, **ai}
                for ai in overdue_items
            ])

    # Recurring topics
    for topic, count in topic_count.items():
        if count >= 3:
            results["recurring_topics"][topic] = {
                "count": count,
                "alert": "Same topic discussed 3+ times without resolution. Escalate to board meeting."
            }

    # Conflict detection
    active_decisions = [d for d in decisions if d.get("status") == "active" and not d.get("do_not_resurface")]
    for i, d1 in enumerate(active_decisions):
        for d2 in active_decisions[i+1:]:
            if d1.get("topic", "").lower() == d2.get("topic", "").lower():
                results["conflicts"].append({
                    "decision_1": d1.get("id", ""),
                    "decision_2": d2.get("id", ""),
                    "topic": d1.get("topic", ""),
                    "type": "duplicate_topic",
                    "message": "Two active decisions on the same topic. One should supersede the other."
                })

    # Recommendations
    if results["summary"]["overdue_review"] > 0:
        results["recommendations"].append(
            f"{results['summary']['overdue_review']} decision(s) past review date. Schedule review."
        )
    if results["summary"]["overdue_action"] > 0:
        results["recommendations"].append(
            f"{results['summary']['overdue_action']} action item(s) overdue. Follow up with owners."
        )
    if results["recurring_topics"]:
        results["recommendations"].append(
            f"{len(results['recurring_topics'])} recurring topic(s) need escalation."
        )
    if results["conflicts"]:
        results["recommendations"].append(
            f"{len(results['conflicts'])} conflict(s) detected. Resolve before next meeting."
        )

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    s = results["summary"]
    lines = [
        "=" * 65,
        "BOARD DECISION TRACKER",
        "=" * 65,
        f"Date: {results['timestamp'][:10]}",
        f"Total Decisions: {results['total_decisions']}",
        f"Active: {s['active']} | Completed: {s['completed']} | Superseded: {s['superseded']} | DNR: {s['do_not_resurface']}",
        f"Overdue Reviews: {s['overdue_review']} | Overdue Actions: {s['overdue_action']}",
        "",
    ]

    if results["overdue_reviews"]:
        lines.append("OVERDUE REVIEWS:")
        for d in results["overdue_reviews"]:
            lines.append(f"  [!] {d['id']}: {d['topic']} ({d['owner']}) - {d['days_since_review_due']} days overdue")
        lines.append("")

    if results["overdue_actions"]:
        lines.append("OVERDUE ACTION ITEMS:")
        for a in results["overdue_actions"][:10]:
            lines.append(f"  [!] {a.get('decision_id','')}: {a.get('action','')} ({a.get('owner','')}, due: {a.get('due_date','')})")
        lines.append("")

    if results["conflicts"]:
        lines.append("CONFLICTS:")
        for c in results["conflicts"]:
            lines.append(f"  [!] {c['message']} ({c['decision_1']} vs {c['decision_2']})")
        lines.append("")

    if results["recurring_topics"]:
        lines.append("RECURRING TOPICS (3+ discussions):")
        for topic, info in results["recurring_topics"].items():
            lines.append(f"  [W] '{topic}' discussed {info['count']} times. {info['alert']}")
        lines.append("")

    lines.append("OWNER WORKLOAD:")
    for owner, wl in sorted(results["owner_workload"].items(), key=lambda x: x[1]["overdue"], reverse=True):
        flag = " [!]" if wl["overdue"] > 0 else ""
        lines.append(f"  {owner}: {wl['active']} active, {wl['overdue']} overdue{flag}")

    if results["recommendations"]:
        lines.extend(["", "RECOMMENDATIONS:"])
        for r in results["recommendations"]:
            lines.append(f"  -> {r}")

    lines.extend(["", "=" * 65])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Track and audit board meeting decisions")
    parser.add_argument("--input", "-i", help="JSON file with decisions data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        today = datetime.now()
        data = {
            "decisions": [
                {"id": "D-001", "topic": "Series B fundraising", "status": "active", "owner": "CEO", "decision_date": "2025-10-15", "review_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"), "action_items": [{"action": "Engage 3 investment banks", "owner": "CFO", "due_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"), "status": "in_progress"}]},
                {"id": "D-002", "topic": "Engineering reorg", "status": "completed", "owner": "CTO", "decision_date": "2025-09-01", "review_date": "2025-12-01", "action_items": []},
                {"id": "D-003", "topic": "Market expansion EU", "status": "active", "owner": "CMO", "decision_date": "2025-11-01", "review_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"), "action_items": [{"action": "Complete GDPR assessment", "owner": "CISO", "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"), "status": "in_progress"}]},
                {"id": "D-004", "topic": "Series B fundraising", "status": "active", "owner": "CFO", "decision_date": "2025-11-15", "review_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"), "action_items": []},
                {"id": "D-005", "topic": "Pricing model change", "status": "active", "owner": "CRO", "decision_date": "2025-10-01", "review_date": (today - timedelta(days=20)).strftime("%Y-%m-%d"), "do_not_resurface": False, "action_items": []},
            ],
        }

    results = track_decisions(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
