#!/usr/bin/env python3
"""
Board Meeting Preparation Checklist - Tracks board meeting prep timeline and readiness.

Generates a T-minus timeline checklist for board meeting preparation,
tracks completion status, identifies blockers, and calculates overall readiness.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


DEFAULT_CHECKLIST = {
    "t_minus_14": {
        "label": "T-14 days: Agenda & Key Messages",
        "tasks": [
            {"id": "agenda_set", "task": "CEO sets agenda and identifies key messages", "owner": "CEO", "critical": True},
            {"id": "topics_confirmed", "task": "Board chair confirms or adjusts proposed topics", "owner": "CEO", "critical": True},
            {"id": "decision_items", "task": "List specific decisions requiring board vote", "owner": "CEO", "critical": False},
            {"id": "section_owners", "task": "Assign section owners and brief them", "owner": "Chief of Staff", "critical": True},
            {"id": "previous_actions", "task": "Review action items from previous meeting", "owner": "Chief of Staff", "critical": False},
        ]
    },
    "t_minus_10": {
        "label": "T-10 days: Section Drafting Begins",
        "tasks": [
            {"id": "cfo_draft", "task": "CFO financial section first draft", "owner": "CFO", "critical": True},
            {"id": "cro_draft", "task": "CRO revenue/pipeline section first draft", "owner": "CRO", "critical": True},
            {"id": "cpo_draft", "task": "CPO product update first draft", "owner": "CPO", "critical": False},
            {"id": "chro_draft", "task": "CHRO people section first draft", "owner": "CHRO", "critical": False},
            {"id": "cmo_draft", "task": "CMO growth/marketing first draft", "owner": "CMO", "critical": False},
            {"id": "cto_draft", "task": "CTO engineering/tech first draft", "owner": "CTO", "critical": False},
            {"id": "ciso_draft", "task": "CISO risk/security first draft", "owner": "CISO", "critical": False},
        ]
    },
    "t_minus_7": {
        "label": "T-7 days: First Drafts Due / CEO Review",
        "tasks": [
            {"id": "all_drafts_in", "task": "All section first drafts submitted", "owner": "All C-suite", "critical": True},
            {"id": "ceo_narrative", "task": "CEO reviews for narrative alignment and through-line", "owner": "CEO", "critical": True},
            {"id": "feedback_sent", "task": "CEO sends feedback to section owners", "owner": "CEO", "critical": True},
            {"id": "bad_news_identified", "task": "Any bad news identified and SOUF framework prepared", "owner": "CEO", "critical": True},
        ]
    },
    "t_minus_5": {
        "label": "T-5 days: Second Drafts / Financial Validation",
        "tasks": [
            {"id": "second_drafts", "task": "Second drafts incorporating CEO feedback", "owner": "All C-suite", "critical": True},
            {"id": "cfo_validates", "task": "CFO validates all numbers across all sections match", "owner": "CFO", "critical": True},
            {"id": "metrics_consistent", "task": "Metrics dashboard cross-checked against section data", "owner": "COO", "critical": True},
            {"id": "asks_finalized", "task": "Specific board asks finalized with CEO", "owner": "CEO", "critical": False},
        ]
    },
    "t_minus_3": {
        "label": "T-3 days: Final Assembly / Narrative Check",
        "tasks": [
            {"id": "deck_assembled", "task": "Final deck assembled in presentation format", "owner": "Chief of Staff", "critical": True},
            {"id": "narrative_check", "task": "End-to-end narrative review (4-act structure)", "owner": "CEO", "critical": True},
            {"id": "formatting_consistent", "task": "Formatting, fonts, colors consistent throughout", "owner": "Chief of Staff", "critical": False},
            {"id": "appendix_current", "task": "Appendix materials are current and accurate", "owner": "CFO", "critical": False},
            {"id": "speaker_notes", "task": "Speaker notes added for presentation slides", "owner": "CEO", "critical": False},
        ]
    },
    "t_minus_2": {
        "label": "T-2 days: Board Distribution",
        "tasks": [
            {"id": "cover_note", "task": "Cover note with 3 key takeaways drafted", "owner": "CEO", "critical": True},
            {"id": "deck_sent", "task": "Deck + cover note sent to all board members", "owner": "Chief of Staff", "critical": True},
            {"id": "calendar_confirmed", "task": "Meeting logistics confirmed (time, location/link)", "owner": "Chief of Staff", "critical": True},
        ]
    },
    "t_minus_0": {
        "label": "T-0: Meeting Day",
        "tasks": [
            {"id": "presenters_briefed", "task": "All presenters briefed on their section timing", "owner": "CEO", "critical": True},
            {"id": "backup_ready", "task": "Backup presenter assigned for each section", "owner": "Chief of Staff", "critical": False},
            {"id": "note_taker", "task": "Designated note-taker for decisions and action items", "owner": "Chief of Staff", "critical": True},
            {"id": "tech_tested", "task": "Video/screen sharing tested (if remote)", "owner": "Chief of Staff", "critical": False},
        ]
    },
}


def generate_checklist(meeting_date: str, completed: list = None, deck_type: str = "quarterly") -> dict:
    """Generate a board prep checklist with dates and status."""
    completed = completed or []

    try:
        meeting_dt = datetime.strptime(meeting_date, "%Y-%m-%d")
    except ValueError:
        meeting_dt = datetime.now() + timedelta(days=14)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_until = (meeting_dt - today).days

    results = {
        "meeting_date": meeting_dt.strftime("%Y-%m-%d"),
        "generated": datetime.now().isoformat(),
        "days_until_meeting": days_until,
        "deck_type": deck_type,
        "overall_readiness_pct": 0,
        "phases": [],
        "overdue_tasks": [],
        "upcoming_tasks": [],
        "blockers": [],
        "summary": {
            "total_tasks": 0,
            "completed": 0,
            "pending": 0,
            "overdue": 0,
            "critical_incomplete": 0,
        },
    }

    total_tasks = 0
    completed_count = 0

    t_minus_map = {
        "t_minus_14": 14,
        "t_minus_10": 10,
        "t_minus_7": 7,
        "t_minus_5": 5,
        "t_minus_3": 3,
        "t_minus_2": 2,
        "t_minus_0": 0,
    }

    for phase_key, phase_data in DEFAULT_CHECKLIST.items():
        t_days = t_minus_map[phase_key]
        phase_date = meeting_dt - timedelta(days=t_days)
        phase_overdue = today > phase_date

        phase_result = {
            "phase": phase_data["label"],
            "due_date": phase_date.strftime("%Y-%m-%d"),
            "is_overdue": phase_overdue and not all(t["id"] in completed for t in phase_data["tasks"]),
            "tasks": [],
        }

        for task in phase_data["tasks"]:
            total_tasks += 1
            is_done = task["id"] in completed
            if is_done:
                completed_count += 1

            task_result = {
                "id": task["id"],
                "task": task["task"],
                "owner": task["owner"],
                "critical": task["critical"],
                "status": "done" if is_done else ("overdue" if phase_overdue else "pending"),
            }
            phase_result["tasks"].append(task_result)

            if not is_done and phase_overdue:
                results["overdue_tasks"].append(task_result)
                results["summary"]["overdue"] += 1
                if task["critical"]:
                    results["blockers"].append({
                        "task": task["task"],
                        "owner": task["owner"],
                        "due": phase_date.strftime("%Y-%m-%d"),
                        "days_overdue": (today - phase_date).days,
                    })
                    results["summary"]["critical_incomplete"] += 1
            elif not is_done and not phase_overdue:
                days_until_phase = (phase_date - today).days
                if days_until_phase <= 3:
                    results["upcoming_tasks"].append({
                        "task": task["task"],
                        "owner": task["owner"],
                        "due_in_days": days_until_phase,
                    })

        results["phases"].append(phase_result)

    results["summary"]["total_tasks"] = total_tasks
    results["summary"]["completed"] = completed_count
    results["summary"]["pending"] = total_tasks - completed_count - results["summary"]["overdue"]
    results["overall_readiness_pct"] = round(completed_count / total_tasks * 100) if total_tasks > 0 else 0

    return results


def format_text(results: dict) -> str:
    """Format checklist as human-readable text."""
    lines = [
        "=" * 65,
        "BOARD MEETING PREPARATION CHECKLIST",
        "=" * 65,
        f"Meeting Date: {results['meeting_date']}",
        f"Days Until Meeting: {results['days_until_meeting']}",
        f"Overall Readiness: {results['overall_readiness_pct']}%",
        f"Tasks: {results['summary']['completed']}/{results['summary']['total_tasks']} complete "
        f"({results['summary']['overdue']} overdue, {results['summary']['critical_incomplete']} critical blockers)",
        "",
    ]

    # Blockers first
    if results["blockers"]:
        lines.append("CRITICAL BLOCKERS:")
        for b in results["blockers"]:
            lines.append(f"  [!!] {b['task']} (Owner: {b['owner']}, {b['days_overdue']} days overdue)")
        lines.append("")

    # Phase by phase
    for phase in results["phases"]:
        overdue_marker = " ** OVERDUE **" if phase["is_overdue"] else ""
        lines.append(f"{phase['phase']} (Due: {phase['due_date']}){overdue_marker}")
        for t in phase["tasks"]:
            if t["status"] == "done":
                icon = "[x]"
            elif t["status"] == "overdue":
                icon = "[!]" if t["critical"] else "[ ]"
            else:
                icon = "[ ]"
            critical_mark = " *" if t["critical"] else ""
            lines.append(f"  {icon} {t['task']} ({t['owner']}){critical_mark}")
        lines.append("")

    # Upcoming tasks
    if results["upcoming_tasks"]:
        lines.append("UPCOMING (next 3 days):")
        for t in results["upcoming_tasks"]:
            lines.append(f"  -> {t['task']} ({t['owner']}, due in {t['due_in_days']} days)")
        lines.append("")

    lines.append("* = critical task")
    lines.append("=" * 65)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate and track board meeting preparation checklist"
    )
    parser.add_argument(
        "--meeting-date", "-d",
        default=(datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        help="Meeting date in YYYY-MM-DD format (default: 14 days from now)"
    )
    parser.add_argument(
        "--completed", "-c",
        nargs="*",
        default=[],
        help="List of completed task IDs"
    )
    parser.add_argument(
        "--input", "-i",
        help="JSON file with completion status"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["quarterly", "monthly", "fundraising", "emergency"],
        default="quarterly",
        help="Deck type (default: quarterly)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--list-tasks", action="store_true",
        help="List all task IDs for reference"
    )
    args = parser.parse_args()

    if args.list_tasks:
        print("Available task IDs:")
        for phase_data in DEFAULT_CHECKLIST.values():
            print(f"\n{phase_data['label']}:")
            for task in phase_data["tasks"]:
                crit = " [CRITICAL]" if task["critical"] else ""
                print(f"  {task['id']}: {task['task']}{crit}")
        return

    completed = args.completed or []
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
            completed = data.get("completed", [])

    results = generate_checklist(args.meeting_date, completed, args.type)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
