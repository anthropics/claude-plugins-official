#!/usr/bin/env python3
"""
Compliance Framework Tracker - Track progress across compliance certifications.

Monitors SOC 2, ISO 27001, HIPAA, GDPR, and other framework readiness.
Calculates gap analysis, effort estimates, and produces audit-ready status reports.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta


FRAMEWORKS = {
    "soc2_type1": {
        "name": "SOC 2 Type I",
        "domains": {
            "security": {"controls": 25, "description": "Security trust service criteria"},
            "availability": {"controls": 8, "description": "System availability commitments"},
            "processing_integrity": {"controls": 6, "description": "Processing accuracy and completeness"},
            "confidentiality": {"controls": 7, "description": "Confidential information protection"},
            "privacy": {"controls": 12, "description": "Personal information handling"},
        },
        "typical_timeline_months": 4,
        "typical_cost_range": "$50K-$100K",
        "prerequisite": None,
    },
    "soc2_type2": {
        "name": "SOC 2 Type II",
        "domains": {
            "security": {"controls": 25},
            "availability": {"controls": 8},
            "processing_integrity": {"controls": 6},
            "confidentiality": {"controls": 7},
            "privacy": {"controls": 12},
        },
        "typical_timeline_months": 9,
        "typical_cost_range": "$80K-$150K",
        "prerequisite": "soc2_type1",
    },
    "iso27001": {
        "name": "ISO 27001",
        "domains": {
            "organizational": {"controls": 37, "description": "Organizational controls (Annex A.5-A.8)"},
            "people": {"controls": 8, "description": "People controls"},
            "physical": {"controls": 14, "description": "Physical controls"},
            "technological": {"controls": 34, "description": "Technological controls"},
        },
        "typical_timeline_months": 12,
        "typical_cost_range": "$100K-$200K",
        "prerequisite": None,
    },
    "hipaa": {
        "name": "HIPAA",
        "domains": {
            "administrative": {"controls": 18, "description": "Administrative safeguards"},
            "physical": {"controls": 10, "description": "Physical safeguards"},
            "technical": {"controls": 12, "description": "Technical safeguards"},
            "breach_notification": {"controls": 5, "description": "Breach notification requirements"},
        },
        "typical_timeline_months": 8,
        "typical_cost_range": "$80K-$200K",
        "prerequisite": None,
    },
    "gdpr": {
        "name": "GDPR",
        "domains": {
            "lawful_basis": {"controls": 6, "description": "Lawful basis for processing"},
            "data_rights": {"controls": 8, "description": "Data subject rights"},
            "data_protection": {"controls": 10, "description": "Data protection measures"},
            "accountability": {"controls": 7, "description": "Documentation and accountability"},
            "transfers": {"controls": 4, "description": "International data transfers"},
        },
        "typical_timeline_months": 5,
        "typical_cost_range": "$30K-$80K",
        "prerequisite": None,
    },
}


def assess_compliance(data: dict) -> dict:
    """Assess compliance readiness across frameworks."""
    target_frameworks = data.get("target_frameworks", ["soc2_type1"])
    control_status = data.get("control_status", {})

    results = {
        "timestamp": datetime.now().isoformat(),
        "company": data.get("company", "Company"),
        "frameworks_assessed": [],
        "overall_readiness_pct": 0,
        "framework_details": {},
        "gap_analysis": [],
        "overlap_savings": {},
        "roadmap": [],
        "effort_estimate": {},
    }

    total_controls = 0
    total_implemented = 0

    for fw_key in target_frameworks:
        fw_config = FRAMEWORKS.get(fw_key)
        if not fw_config:
            continue

        results["frameworks_assessed"].append(fw_config["name"])
        fw_status = control_status.get(fw_key, {})

        fw_total = 0
        fw_implemented = 0
        domain_results = {}
        gaps = []

        for domain_key, domain_config in fw_config["domains"].items():
            domain_total = domain_config["controls"]
            domain_done = fw_status.get(domain_key, {}).get("implemented", 0)
            domain_in_progress = fw_status.get(domain_key, {}).get("in_progress", 0)
            domain_pct = (domain_done / domain_total * 100) if domain_total > 0 else 0

            fw_total += domain_total
            fw_implemented += domain_done
            total_controls += domain_total
            total_implemented += domain_done

            domain_results[domain_key] = {
                "total": domain_total,
                "implemented": domain_done,
                "in_progress": domain_in_progress,
                "gap": domain_total - domain_done - domain_in_progress,
                "readiness_pct": round(domain_pct, 1),
                "status": "Complete" if domain_pct >= 100 else "Near Complete" if domain_pct >= 80 else "In Progress" if domain_pct >= 40 else "Early Stage",
            }

            if domain_pct < 80:
                gaps.append({
                    "framework": fw_config["name"],
                    "domain": domain_key,
                    "gap_count": domain_total - domain_done - domain_in_progress,
                    "readiness_pct": round(domain_pct, 1),
                    "description": domain_config.get("description", ""),
                })

        fw_readiness = (fw_implemented / fw_total * 100) if fw_total > 0 else 0

        results["framework_details"][fw_key] = {
            "name": fw_config["name"],
            "total_controls": fw_total,
            "implemented": fw_implemented,
            "readiness_pct": round(fw_readiness, 1),
            "typical_timeline": fw_config["typical_timeline_months"],
            "typical_cost": fw_config["typical_cost_range"],
            "prerequisite": fw_config.get("prerequisite"),
            "domains": domain_results,
            "audit_ready": fw_readiness >= 90,
        }

        results["gap_analysis"].extend(gaps)

    results["overall_readiness_pct"] = round(total_implemented / total_controls * 100, 1) if total_controls > 0 else 0

    # Calculate framework overlaps
    if len(target_frameworks) > 1:
        overlap_controls = min(25, total_controls * 0.3)  # ~30% overlap typical
        results["overlap_savings"] = {
            "shared_controls_estimate": round(overlap_controls),
            "effort_reduction_pct": 30,
            "note": "SOC 2 + ISO 27001 share ~70% of controls. Do SOC 2 first, extend to ISO 27001 with ~30% incremental effort.",
        }

    # Roadmap
    sorted_gaps = sorted(results["gap_analysis"], key=lambda x: x["gap_count"], reverse=True)
    month = 1
    for gap in sorted_gaps:
        effort_months = max(1, gap["gap_count"] // 5)
        results["roadmap"].append({
            "start_month": month,
            "end_month": month + effort_months,
            "framework": gap["framework"],
            "domain": gap["domain"],
            "controls_to_implement": gap["gap_count"],
            "description": gap["description"],
        })
        month += effort_months

    # Effort estimate
    results["effort_estimate"] = {
        "total_gaps": sum(g["gap_count"] for g in results["gap_analysis"]),
        "estimated_months": month,
        "estimated_fte_months": round(month * 1.5, 1),
        "recommended_approach": "Internal + consultant" if month > 6 else "Internal team",
    }

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 70,
        "COMPLIANCE FRAMEWORK TRACKER",
        "=" * 70,
        f"Company: {results['company']}",
        f"Date: {results['timestamp'][:10]}",
        f"Frameworks: {', '.join(results['frameworks_assessed'])}",
        f"Overall Readiness: {results['overall_readiness_pct']:.0f}%",
        "",
    ]

    for fw_key, fw in results["framework_details"].items():
        audit_icon = "[READY]" if fw["audit_ready"] else "[NOT READY]"
        lines.extend([
            f"{fw['name']} {audit_icon}",
            f"  Readiness: {fw['readiness_pct']:.0f}% ({fw['implemented']}/{fw['total_controls']} controls)",
            f"  Timeline: {fw['typical_timeline']} months  |  Cost: {fw['typical_cost']}",
        ])
        if fw.get("prerequisite"):
            lines.append(f"  Prerequisite: {FRAMEWORKS.get(fw['prerequisite'], {}).get('name', fw['prerequisite'])}")

        for domain, d in fw["domains"].items():
            bar_len = int(d["readiness_pct"] / 5)
            bar = "#" * bar_len + "." * (20 - bar_len)
            lines.append(f"    {domain:<22} [{bar}] {d['readiness_pct']:>5.0f}% ({d['implemented']}/{d['total']})")
        lines.append("")

    if results["gap_analysis"]:
        lines.extend(["GAP ANALYSIS:"])
        for gap in results["gap_analysis"][:8]:
            lines.append(f"  {gap['framework']}/{gap['domain']}: {gap['gap_count']} controls remaining ({gap['readiness_pct']:.0f}% done)")
        lines.append("")

    if results["overlap_savings"]:
        os = results["overlap_savings"]
        lines.extend([
            "FRAMEWORK OVERLAP:",
            f"  {os['note']}",
            f"  Estimated shared controls: ~{os['shared_controls_estimate']}",
            "",
        ])

    ee = results["effort_estimate"]
    lines.extend([
        "EFFORT ESTIMATE:",
        f"  Controls to implement: {ee['total_gaps']}",
        f"  Estimated timeline: {ee['estimated_months']} months",
        f"  FTE-months: {ee['estimated_fte_months']}",
        f"  Approach: {ee['recommended_approach']}",
        "",
        "=" * 70,
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Track compliance framework readiness")
    parser.add_argument("--input", "-i", help="JSON file with compliance data")
    parser.add_argument("--frameworks", "-f", nargs="*", default=["soc2_type1"], help="Target frameworks (default: soc2_type1)")
    parser.add_argument("--list-frameworks", action="store_true", help="List available frameworks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list_frameworks:
        print("Available frameworks:")
        for key, fw in FRAMEWORKS.items():
            prereq = f" (requires: {fw['prerequisite']})" if fw.get("prerequisite") else ""
            print(f"  {key}: {fw['name']} - {fw['typical_timeline_months']} months, {fw['typical_cost_range']}{prereq}")
        return

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        data = {
            "company": "SaaSCo",
            "target_frameworks": args.frameworks,
            "control_status": {
                "soc2_type1": {
                    "security": {"implemented": 18, "in_progress": 4},
                    "availability": {"implemented": 5, "in_progress": 2},
                    "processing_integrity": {"implemented": 3, "in_progress": 1},
                    "confidentiality": {"implemented": 4, "in_progress": 2},
                    "privacy": {"implemented": 6, "in_progress": 3},
                },
                "iso27001": {
                    "organizational": {"implemented": 20, "in_progress": 8},
                    "people": {"implemented": 5, "in_progress": 2},
                    "physical": {"implemented": 8, "in_progress": 3},
                    "technological": {"implemented": 22, "in_progress": 6},
                },
                "gdpr": {
                    "lawful_basis": {"implemented": 4, "in_progress": 1},
                    "data_rights": {"implemented": 5, "in_progress": 2},
                    "data_protection": {"implemented": 7, "in_progress": 2},
                    "accountability": {"implemented": 3, "in_progress": 2},
                    "transfers": {"implemented": 2, "in_progress": 1},
                },
            },
        }

    results = assess_compliance(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
