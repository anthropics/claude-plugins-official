#!/usr/bin/env python3
"""
Security Posture Scorer - Assess organizational security maturity.

Scores security posture across NIST CSF 2.0 functions (Govern, Identify, Protect,
Detect, Respond, Recover) and CISA Zero Trust pillars. Produces board-ready
security health report with prioritized remediation roadmap.
"""

import argparse
import json
import sys
from datetime import datetime


NIST_CSF_FUNCTIONS = {
    "govern": {
        "weight": 0.15,
        "controls": [
            {"id": "GV-1", "name": "Security policy documented", "description": "Formal security policy exists, approved by leadership"},
            {"id": "GV-2", "name": "Risk management strategy", "description": "Risk appetite defined and communicated"},
            {"id": "GV-3", "name": "Roles and responsibilities", "description": "Security roles clearly defined with accountability"},
            {"id": "GV-4", "name": "Supply chain risk policy", "description": "Vendor security requirements documented"},
            {"id": "GV-5", "name": "Security reporting to leadership", "description": "Regular board/exec security reporting cadence"},
        ]
    },
    "identify": {
        "weight": 0.15,
        "controls": [
            {"id": "ID-1", "name": "Asset inventory", "description": "Complete inventory of hardware, software, data assets"},
            {"id": "ID-2", "name": "Data classification", "description": "Data classified by sensitivity (public, internal, confidential, restricted)"},
            {"id": "ID-3", "name": "Risk assessment", "description": "Annual risk assessment with quantified ALE"},
            {"id": "ID-4", "name": "Vulnerability management", "description": "Regular vulnerability scanning with SLA-based patching"},
            {"id": "ID-5", "name": "Threat modeling", "description": "Threat models for critical systems"},
        ]
    },
    "protect": {
        "weight": 0.25,
        "controls": [
            {"id": "PR-1", "name": "MFA enforcement", "description": "MFA required for all users on all systems"},
            {"id": "PR-2", "name": "Endpoint protection (EDR)", "description": "EDR deployed on all endpoints"},
            {"id": "PR-3", "name": "Encryption at rest", "description": "All sensitive data encrypted at rest (AES-256)"},
            {"id": "PR-4", "name": "Encryption in transit", "description": "TLS 1.2+ for all data in transit"},
            {"id": "PR-5", "name": "Access control (RBAC)", "description": "Role-based access with least privilege"},
            {"id": "PR-6", "name": "Security awareness training", "description": "Annual training with phishing simulations"},
            {"id": "PR-7", "name": "Backup and recovery", "description": "Regular backups tested for restoration"},
            {"id": "PR-8", "name": "Network segmentation", "description": "Production isolated from corporate network"},
        ]
    },
    "detect": {
        "weight": 0.20,
        "controls": [
            {"id": "DE-1", "name": "Centralized logging", "description": "All critical systems send logs to SIEM"},
            {"id": "DE-2", "name": "Alerting rules", "description": "Detection rules for common attack patterns"},
            {"id": "DE-3", "name": "Anomaly detection", "description": "Behavioral analytics for user/network anomalies"},
            {"id": "DE-4", "name": "Penetration testing", "description": "Annual pen test by qualified third party"},
            {"id": "DE-5", "name": "Monitoring 24/7", "description": "Security monitoring with defined on-call rotation"},
        ]
    },
    "respond": {
        "weight": 0.15,
        "controls": [
            {"id": "RS-1", "name": "Incident response plan", "description": "Documented IR plan with severity classification"},
            {"id": "RS-2", "name": "IR team defined", "description": "Named incident response team with contact info"},
            {"id": "RS-3", "name": "Tabletop exercises", "description": "Annual IR tabletop exercise conducted"},
            {"id": "RS-4", "name": "Communication plan", "description": "Stakeholder notification procedures defined"},
            {"id": "RS-5", "name": "Forensic capability", "description": "Ability to preserve evidence and investigate"},
        ]
    },
    "recover": {
        "weight": 0.10,
        "controls": [
            {"id": "RC-1", "name": "Recovery plan", "description": "Documented recovery procedures for critical systems"},
            {"id": "RC-2", "name": "RTO/RPO defined", "description": "Recovery objectives set and communicated"},
            {"id": "RC-3", "name": "DR testing", "description": "Disaster recovery tested within last 12 months"},
            {"id": "RC-4", "name": "Lessons learned", "description": "Post-incident reviews conducted and tracked"},
        ]
    },
}

ZERO_TRUST_PILLARS = {
    "identity": {"controls": ["MFA enforcement", "SSO", "Privileged access management", "Identity governance"], "weight": 0.25},
    "devices": {"controls": ["EDR", "Device compliance", "Patch management", "Mobile device management"], "weight": 0.20},
    "networks": {"controls": ["Micro-segmentation", "ZTNA/SDP", "DNS filtering", "DDoS protection"], "weight": 0.15},
    "applications": {"controls": ["SAST/DAST", "WAF", "API security", "Container security"], "weight": 0.20},
    "data": {"controls": ["Classification", "DLP", "Encryption", "Rights management"], "weight": 0.20},
}

MATURITY_LEVELS = {
    0: {"label": "Ad Hoc", "description": "No formal processes"},
    1: {"label": "Initial", "description": "Some processes defined but inconsistent"},
    2: {"label": "Developing", "description": "Processes defined and partially implemented"},
    3: {"label": "Managed", "description": "Processes implemented and measured"},
    4: {"label": "Optimized", "description": "Continuous improvement, fully automated where possible"},
}


def score_posture(data: dict) -> dict:
    """Score security posture across all frameworks."""
    control_scores = data.get("controls", {})
    zt_scores = data.get("zero_trust", {})

    results = {
        "timestamp": datetime.now().isoformat(),
        "company": data.get("company", "Company"),
        "overall_score": 0,
        "overall_maturity": 0,
        "maturity_label": "",
        "nist_csf_scores": {},
        "zero_trust_scores": {},
        "critical_gaps": [],
        "quick_wins": [],
        "remediation_roadmap": [],
        "board_summary": {},
    }

    # Score NIST CSF functions
    total_weighted = 0
    for func_name, func_config in NIST_CSF_FUNCTIONS.items():
        func_total = 0
        func_count = 0
        gaps = []
        for ctrl in func_config["controls"]:
            score = control_scores.get(ctrl["id"], 0)  # 0-4 maturity
            func_total += score
            func_count += 1
            if score < 2:
                gaps.append({"control": ctrl["id"], "name": ctrl["name"], "current": score, "description": ctrl["description"]})

        avg_maturity = func_total / func_count if func_count > 0 else 0
        pct_score = avg_maturity / 4 * 100
        weighted = pct_score * func_config["weight"]
        total_weighted += weighted

        results["nist_csf_scores"][func_name] = {
            "maturity": round(avg_maturity, 1),
            "score_pct": round(pct_score, 1),
            "weight": func_config["weight"],
            "weighted_score": round(weighted, 1),
            "controls_assessed": func_count,
            "gaps": gaps,
        }

        # Critical gaps (Protect and Detect are highest priority)
        for gap in gaps:
            severity = "critical" if func_name in ["protect", "detect"] and gap["current"] == 0 else "high" if gap["current"] == 0 else "medium"
            results["critical_gaps"].append({
                "function": func_name,
                "control": gap["control"],
                "name": gap["name"],
                "current_maturity": gap["current"],
                "severity": severity,
            })

    results["overall_score"] = round(total_weighted, 1)
    overall_maturity = total_weighted / 25  # Convert to 0-4 scale
    results["overall_maturity"] = round(overall_maturity, 1)
    results["maturity_label"] = MATURITY_LEVELS.get(round(overall_maturity), {}).get("label", "Unknown")

    # Zero Trust scoring
    zt_total = 0
    for pillar, config in ZERO_TRUST_PILLARS.items():
        pillar_scores = zt_scores.get(pillar, {})
        implemented = sum(1 for c in config["controls"] if pillar_scores.get(c, False))
        total = len(config["controls"])
        pct = (implemented / total * 100) if total > 0 else 0
        stage = "Optimal" if pct >= 90 else "Advanced" if pct >= 65 else "Initial" if pct >= 30 else "Traditional"
        zt_total += pct * config["weight"]
        results["zero_trust_scores"][pillar] = {
            "implemented": implemented,
            "total": total,
            "pct": round(pct, 1),
            "stage": stage,
        }
    results["zero_trust_overall_pct"] = round(zt_total, 1)

    # Quick wins (low effort, high impact)
    for gap in results["critical_gaps"]:
        if gap["current_maturity"] == 0 and gap["name"] in ["MFA enforcement", "Backup and recovery", "Security awareness training", "Incident response plan"]:
            results["quick_wins"].append({
                "control": gap["name"],
                "effort": "Low-Medium",
                "impact": "High",
                "timeline": "2-4 weeks",
            })

    # Remediation roadmap
    sorted_gaps = sorted(results["critical_gaps"], key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["severity"], 3))
    phase = 1
    for i, gap in enumerate(sorted_gaps[:12]):
        if i < 4:
            phase = 1
            timeline = "Month 1-2"
        elif i < 8:
            phase = 2
            timeline = "Month 3-4"
        else:
            phase = 3
            timeline = "Month 5-6"
        results["remediation_roadmap"].append({
            "phase": phase,
            "timeline": timeline,
            "control": gap["name"],
            "function": gap["function"],
            "severity": gap["severity"],
            "target_maturity": 3,
        })

    # Board summary
    critical_count = sum(1 for g in results["critical_gaps"] if g["severity"] == "critical")
    results["board_summary"] = {
        "posture_score": f"{results['overall_score']:.0f}/100",
        "maturity_level": f"{results['maturity_label']} ({results['overall_maturity']:.1f}/4.0)",
        "critical_gaps": critical_count,
        "zero_trust_progress": f"{results['zero_trust_overall_pct']:.0f}%",
        "top_risk": sorted_gaps[0]["name"] if sorted_gaps else "None identified",
        "recommendation": "Immediate action on critical gaps" if critical_count > 2 else "Continue maturity improvement" if results["overall_score"] < 70 else "Strong posture - maintain and optimize",
    }

    return results


def format_text(results: dict) -> str:
    """Format as human-readable report."""
    lines = [
        "=" * 68,
        "SECURITY POSTURE ASSESSMENT",
        "=" * 68,
        f"Company: {results['company']}",
        f"Date: {results['timestamp'][:10]}",
        f"Overall Score: {results['overall_score']:.0f}/100  |  Maturity: {results['maturity_label']} ({results['overall_maturity']:.1f}/4.0)",
        "",
        "NIST CSF 2.0 FUNCTION SCORES:",
        f"{'Function':<12} {'Maturity':>9} {'Score':>7} {'Weighted':>9} {'Gaps':>5}",
        "-" * 50,
    ]

    for func, data in results["nist_csf_scores"].items():
        gap_count = len(data["gaps"])
        lines.append(
            f"{func.title():<12} {data['maturity']:>7.1f}/4 {data['score_pct']:>6.0f}% {data['weighted_score']:>8.1f} {gap_count:>5}"
        )

    lines.extend(["", "ZERO TRUST MATURITY:"])
    for pillar, data in results["zero_trust_scores"].items():
        bar_len = int(data["pct"] / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        lines.append(f"  {pillar.title():<15} [{bar}] {data['pct']:>5.0f}% ({data['stage']})")

    if results["critical_gaps"]:
        lines.extend(["", "CRITICAL GAPS (top 5):"])
        for gap in results["critical_gaps"][:5]:
            lines.append(f"  [{gap['severity'].upper():<8}] {gap['function'].title()}/{gap['name']} (maturity: {gap['current_maturity']}/4)")

    if results["quick_wins"]:
        lines.extend(["", "QUICK WINS:"])
        for qw in results["quick_wins"]:
            lines.append(f"  -> {qw['control']} ({qw['timeline']}, {qw['impact']} impact)")

    if results["remediation_roadmap"]:
        lines.extend(["", "REMEDIATION ROADMAP:"])
        current_phase = 0
        for item in results["remediation_roadmap"]:
            if item["phase"] != current_phase:
                current_phase = item["phase"]
                lines.append(f"  Phase {current_phase} ({item['timeline']}):")
            lines.append(f"    - {item['control']} [{item['severity']}]")

    bs = results["board_summary"]
    lines.extend([
        "",
        "BOARD SUMMARY:",
        f"  Score: {bs['posture_score']}  |  Maturity: {bs['maturity_level']}",
        f"  Critical Gaps: {bs['critical_gaps']}  |  Zero Trust: {bs['zero_trust_progress']}",
        f"  Top Risk: {bs['top_risk']}",
        f"  Recommendation: {bs['recommendation']}",
        "",
        "=" * 68,
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Score organizational security posture")
    parser.add_argument("--input", "-i", help="JSON file with control assessments")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        # Demo data - realistic Series B company
        data = {
            "company": "SaaSCo",
            "controls": {
                "GV-1": 3, "GV-2": 2, "GV-3": 2, "GV-4": 1, "GV-5": 2,
                "ID-1": 2, "ID-2": 1, "ID-3": 2, "ID-4": 3, "ID-5": 1,
                "PR-1": 4, "PR-2": 3, "PR-3": 3, "PR-4": 4, "PR-5": 2, "PR-6": 2, "PR-7": 3, "PR-8": 1,
                "DE-1": 2, "DE-2": 2, "DE-3": 1, "DE-4": 3, "DE-5": 1,
                "RS-1": 3, "RS-2": 3, "RS-3": 1, "RS-4": 2, "RS-5": 1,
                "RC-1": 2, "RC-2": 2, "RC-3": 1, "RC-4": 1,
            },
            "zero_trust": {
                "identity": {"MFA enforcement": True, "SSO": True, "Privileged access management": False, "Identity governance": False},
                "devices": {"EDR": True, "Device compliance": True, "Patch management": True, "Mobile device management": False},
                "networks": {"Micro-segmentation": False, "ZTNA/SDP": False, "DNS filtering": True, "DDoS protection": True},
                "applications": {"SAST/DAST": True, "WAF": True, "API security": False, "Container security": False},
                "data": {"Classification": False, "DLP": False, "Encryption": True, "Rights management": False},
            },
        }

    results = score_posture(data)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
