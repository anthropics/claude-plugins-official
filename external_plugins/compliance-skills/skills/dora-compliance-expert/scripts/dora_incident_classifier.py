#!/usr/bin/env python3
"""
DORA Incident Classifier

Classifies ICT-related incidents per DORA (EU 2022/2554) Article 18 criteria,
determines whether an incident qualifies as "major," calculates reporting
deadlines, and generates incident notification templates.

Usage:
    python dora_incident_classifier.py --clients-affected 5000 --duration-hours 4 --data-loss yes --services-critical yes --economic-impact 500000
    python dora_incident_classifier.py --config incident.json --json
    python dora_incident_classifier.py --config incident.json --generate-template --output notification.json
    python dora_incident_classifier.py --template > incident_input.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# --- DORA Incident Classification Criteria (Article 18) ---

CLASSIFICATION_CRITERIA = {
    "clients_affected": {
        "name": "Number of Clients/Financial Counterparts Affected",
        "article": "Article 18(1)(a)",
        "thresholds": {
            "low": {"max": 100, "score": 1, "label": "Low (< 100 clients)"},
            "medium": {"max": 1000, "score": 2, "label": "Medium (100–1,000 clients)"},
            "high": {"max": 10000, "score": 3, "label": "High (1,000–10,000 clients)"},
            "very_high": {"max": float("inf"), "score": 4, "label": "Very High (> 10,000 clients)"},
        },
    },
    "duration_hours": {
        "name": "Duration of the Incident",
        "article": "Article 18(1)(b)",
        "thresholds": {
            "low": {"max": 2, "score": 1, "label": "Low (< 2 hours)"},
            "medium": {"max": 12, "score": 2, "label": "Medium (2–12 hours)"},
            "high": {"max": 24, "score": 3, "label": "High (12–24 hours)"},
            "very_high": {"max": float("inf"), "score": 4, "label": "Very High (> 24 hours)"},
        },
    },
    "geographic_spread": {
        "name": "Geographic Spread",
        "article": "Article 18(1)(c)",
        "levels": {
            "local": {"score": 1, "label": "Local (single office/region)"},
            "national": {"score": 2, "label": "National (single Member State)"},
            "eu_multiple": {"score": 3, "label": "EU Multiple (2+ Member States)"},
            "global": {"score": 4, "label": "Global (beyond EU)"},
        },
    },
    "data_loss": {
        "name": "Data Losses (Availability, Authenticity, Integrity, Confidentiality)",
        "article": "Article 18(1)(d)",
        "levels": {
            "none": {"score": 0, "label": "No data loss"},
            "availability": {"score": 2, "label": "Availability impact (service disruption)"},
            "integrity": {"score": 3, "label": "Integrity compromise (data modified/corrupted)"},
            "confidentiality": {"score": 4, "label": "Confidentiality breach (data exposed/exfiltrated)"},
            "multiple": {"score": 4, "label": "Multiple data dimensions affected"},
        },
    },
    "services_critical": {
        "name": "Criticality of Services Affected",
        "article": "Article 18(1)(e)",
        "levels": {
            "non_critical": {"score": 1, "label": "Non-critical services only"},
            "important": {"score": 2, "label": "Important (but not critical) functions"},
            "critical": {"score": 3, "label": "Critical functions affected"},
            "multiple_critical": {"score": 4, "label": "Multiple critical functions affected"},
        },
    },
    "economic_impact": {
        "name": "Economic Impact",
        "article": "Article 18(1)(f)",
        "thresholds": {
            "low": {"max": 100000, "score": 1, "label": "Low (< EUR 100K)"},
            "medium": {"max": 500000, "score": 2, "label": "Medium (EUR 100K–500K)"},
            "high": {"max": 5000000, "score": 3, "label": "High (EUR 500K–5M)"},
            "very_high": {"max": float("inf"), "score": 4, "label": "Very High (> EUR 5M)"},
        },
    },
}

# Major incident threshold: total score across all criteria
MAJOR_INCIDENT_THRESHOLD = 14  # Out of maximum 24
HIGH_SEVERITY_THRESHOLD = 18


def classify_numeric(value: float, thresholds: Dict) -> Dict:
    """Classify a numeric value against thresholds."""
    for level_name, level_data in thresholds.items():
        if value <= level_data["max"]:
            return {"level": level_name, "score": level_data["score"], "label": level_data["label"]}
    # Fallback to highest
    last = list(thresholds.values())[-1]
    return {"level": list(thresholds.keys())[-1], "score": last["score"], "label": last["label"]}


def classify_categorical(value: str, levels: Dict) -> Dict:
    """Classify a categorical value."""
    if value in levels:
        return {"level": value, "score": levels[value]["score"], "label": levels[value]["label"]}
    return {"level": "unknown", "score": 0, "label": f"Unknown value: {value}"}


def classify_incident(
    clients_affected: int = 0,
    duration_hours: float = 0,
    geographic_spread: str = "local",
    data_loss: str = "none",
    services_critical: str = "non_critical",
    economic_impact: float = 0,
    detection_time: Optional[str] = None,
    incident_description: str = "",
    malicious: Optional[bool] = None,
) -> Dict[str, Any]:
    """Classify an ICT incident per DORA Article 18 criteria."""

    now = datetime.now()
    detection_dt = None
    if detection_time:
        try:
            detection_dt = datetime.fromisoformat(detection_time)
        except ValueError:
            detection_dt = now

    result = {
        "timestamp": now.isoformat(),
        "input": {
            "clients_affected": clients_affected,
            "duration_hours": duration_hours,
            "geographic_spread": geographic_spread,
            "data_loss": data_loss,
            "services_critical": services_critical,
            "economic_impact_eur": economic_impact,
            "detection_time": detection_time,
            "incident_description": incident_description,
            "suspected_malicious": malicious,
        },
        "classification": {},
        "severity": {},
        "reporting": {},
        "notification_template": {},
    }

    # Classify each criterion
    criteria_results = {}
    total_score = 0

    # Clients affected
    c = classify_numeric(clients_affected, CLASSIFICATION_CRITERIA["clients_affected"]["thresholds"])
    criteria_results["clients_affected"] = {
        "criterion": CLASSIFICATION_CRITERIA["clients_affected"]["name"],
        "article": CLASSIFICATION_CRITERIA["clients_affected"]["article"],
        "value": clients_affected,
        **c,
    }
    total_score += c["score"]

    # Duration
    c = classify_numeric(duration_hours, CLASSIFICATION_CRITERIA["duration_hours"]["thresholds"])
    criteria_results["duration"] = {
        "criterion": CLASSIFICATION_CRITERIA["duration_hours"]["name"],
        "article": CLASSIFICATION_CRITERIA["duration_hours"]["article"],
        "value": f"{duration_hours} hours",
        **c,
    }
    total_score += c["score"]

    # Geographic spread
    c = classify_categorical(geographic_spread, CLASSIFICATION_CRITERIA["geographic_spread"]["levels"])
    criteria_results["geographic_spread"] = {
        "criterion": CLASSIFICATION_CRITERIA["geographic_spread"]["name"],
        "article": CLASSIFICATION_CRITERIA["geographic_spread"]["article"],
        "value": geographic_spread,
        **c,
    }
    total_score += c["score"]

    # Data loss
    c = classify_categorical(data_loss, CLASSIFICATION_CRITERIA["data_loss"]["levels"])
    criteria_results["data_loss"] = {
        "criterion": CLASSIFICATION_CRITERIA["data_loss"]["name"],
        "article": CLASSIFICATION_CRITERIA["data_loss"]["article"],
        "value": data_loss,
        **c,
    }
    total_score += c["score"]

    # Services criticality
    c = classify_categorical(services_critical, CLASSIFICATION_CRITERIA["services_critical"]["levels"])
    criteria_results["services_critical"] = {
        "criterion": CLASSIFICATION_CRITERIA["services_critical"]["name"],
        "article": CLASSIFICATION_CRITERIA["services_critical"]["article"],
        "value": services_critical,
        **c,
    }
    total_score += c["score"]

    # Economic impact
    c = classify_numeric(economic_impact, CLASSIFICATION_CRITERIA["economic_impact"]["thresholds"])
    criteria_results["economic_impact"] = {
        "criterion": CLASSIFICATION_CRITERIA["economic_impact"]["name"],
        "article": CLASSIFICATION_CRITERIA["economic_impact"]["article"],
        "value": f"EUR {economic_impact:,.0f}",
        **c,
    }
    total_score += c["score"]

    result["classification"]["criteria"] = criteria_results
    result["classification"]["total_score"] = total_score
    result["classification"]["max_score"] = 24

    # Determine if major
    is_major = total_score >= MAJOR_INCIDENT_THRESHOLD
    result["severity"]["is_major_incident"] = is_major
    result["severity"]["total_score"] = total_score

    if total_score >= HIGH_SEVERITY_THRESHOLD:
        result["severity"]["level"] = "critical"
        result["severity"]["description"] = "Critical incident — highest priority, immediate executive escalation required"
    elif total_score >= MAJOR_INCIDENT_THRESHOLD:
        result["severity"]["level"] = "major"
        result["severity"]["description"] = "Major incident — mandatory DORA reporting to competent authority"
    elif total_score >= 8:
        result["severity"]["level"] = "significant"
        result["severity"]["description"] = "Significant incident — internal escalation, monitor for escalation to major"
    else:
        result["severity"]["level"] = "standard"
        result["severity"]["description"] = "Standard incident — handle per normal incident management process"

    # Reporting deadlines
    if is_major:
        classification_time = detection_dt if detection_dt else now
        # 4 hours from classification (or 24 hours from detection)
        initial_deadline = classification_time + timedelta(hours=4)
        detection_fallback = (detection_dt or now) + timedelta(hours=24)
        actual_initial = min(initial_deadline, detection_fallback)

        intermediate_deadline = actual_initial + timedelta(hours=72)
        final_deadline = intermediate_deadline + timedelta(days=30)

        result["reporting"] = {
            "mandatory": True,
            "classification_as_major": classification_time.isoformat(),
            "deadlines": {
                "initial_notification": {
                    "deadline": actual_initial.isoformat(),
                    "requirement": "Within 4 hours of classifying as major (or 24 hours from detection)",
                    "article": "Article 19(4)(a)",
                    "content": "Basic facts, initial classification, estimated impact",
                },
                "intermediate_report": {
                    "deadline": intermediate_deadline.isoformat(),
                    "requirement": "Within 72 hours of initial notification",
                    "article": "Article 19(4)(b)",
                    "content": "Updated severity, root cause assessment, recovery status, indicators of compromise",
                },
                "final_report": {
                    "deadline": final_deadline.isoformat(),
                    "requirement": "Within 1 month of intermediate report",
                    "article": "Article 19(4)(c)",
                    "content": "Root cause analysis, complete impact assessment, mitigation measures, lessons learned",
                },
            },
            "client_notification": {
                "required": True,
                "requirement": "Without undue delay if incident affects clients' financial interests",
                "article": "Article 19(1)",
            },
        }
    else:
        result["reporting"] = {
            "mandatory": False,
            "note": "Incident does not meet major incident threshold. Handle per internal incident management process.",
            "voluntary_reporting": "Consider voluntary reporting if incident reveals significant cyber threats (Article 19(2))",
        }

    return result


def generate_notification_template(result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate incident notification templates for all reporting stages."""
    inp = result["input"]
    severity = result.get("severity", {})
    reporting = result.get("reporting", {})

    template = {
        "initial_notification": {
            "_instructions": "Submit within 4 hours of classifying as major incident",
            "reporting_entity": {
                "entity_name": "[ENTITY NAME]",
                "entity_lei": "[LEI CODE]",
                "entity_type": "[e.g., credit_institution]",
                "contact_person": "[NAME]",
                "contact_email": "[EMAIL]",
                "contact_phone": "[PHONE]",
            },
            "incident_details": {
                "incident_id": "[INTERNAL REFERENCE]",
                "detection_date_time": inp.get("detection_time", "[YYYY-MM-DDTHH:MM:SS]"),
                "classification_date_time": result.get("timestamp", ""),
                "incident_description": inp.get("incident_description", "[BRIEF DESCRIPTION]"),
                "suspected_malicious": inp.get("suspected_malicious"),
                "services_affected": "[LIST AFFECTED SERVICES]",
                "initial_impact_assessment": severity.get("description", ""),
                "severity_level": severity.get("level", ""),
            },
            "initial_classification": {
                "clients_affected_estimate": inp.get("clients_affected", 0),
                "estimated_duration": inp.get("duration_hours", 0),
                "geographic_scope": inp.get("geographic_spread", ""),
                "data_impact": inp.get("data_loss", ""),
                "critical_functions_affected": inp.get("services_critical", ""),
                "estimated_economic_impact_eur": inp.get("economic_impact_eur", 0),
            },
            "immediate_actions_taken": "[DESCRIBE CONTAINMENT AND INITIAL RESPONSE MEASURES]",
        },
        "intermediate_report": {
            "_instructions": "Submit within 72 hours of initial notification",
            "reference": {
                "initial_notification_id": "[REFERENCE TO INITIAL NOTIFICATION]",
                "initial_notification_date": "[DATE]",
            },
            "updated_assessment": {
                "updated_severity": "[UPDATED SEVERITY LEVEL]",
                "updated_clients_affected": "[UPDATED COUNT]",
                "updated_duration": "[ACTUAL OR ESTIMATED TOTAL DURATION]",
                "updated_economic_impact": "[UPDATED ESTIMATE]",
            },
            "root_cause_assessment": {
                "suspected_root_cause": "[INITIAL ROOT CAUSE ASSESSMENT]",
                "attack_vector": "[IF APPLICABLE — e.g., phishing, vulnerability exploitation, supply chain]",
                "threat_actor_assessment": "[IF KNOWN — nation-state, criminal, hacktivist, insider]",
            },
            "indicators_of_compromise": {
                "ip_addresses": [],
                "domains": [],
                "file_hashes": [],
                "signatures": [],
                "other_iocs": [],
            },
            "recovery_status": {
                "containment_status": "[CONTAINED / PARTIALLY CONTAINED / NOT CONTAINED]",
                "recovery_progress": "[PERCENTAGE OR STATUS DESCRIPTION]",
                "estimated_full_recovery": "[ESTIMATED DATE/TIME]",
                "services_restored": "[LIST SERVICES RESTORED]",
                "services_still_affected": "[LIST SERVICES STILL AFFECTED]",
            },
            "additional_measures_taken": "[DESCRIBE ADDITIONAL RESPONSE ACTIONS]",
        },
        "final_report": {
            "_instructions": "Submit within 1 month of intermediate report",
            "reference": {
                "initial_notification_id": "[REFERENCE]",
                "intermediate_report_id": "[REFERENCE]",
            },
            "complete_timeline": {
                "incident_start": "[DATE/TIME]",
                "detection": "[DATE/TIME]",
                "classification_as_major": "[DATE/TIME]",
                "containment_achieved": "[DATE/TIME]",
                "full_recovery": "[DATE/TIME]",
                "key_events": "[CHRONOLOGICAL LIST OF KEY EVENTS]",
            },
            "root_cause_analysis": {
                "root_cause": "[DETAILED ROOT CAUSE]",
                "contributing_factors": "[LIST CONTRIBUTING FACTORS]",
                "methodology_used": "[e.g., 5-Why, Fishbone, FTA]",
            },
            "complete_impact_assessment": {
                "total_clients_affected": "[FINAL COUNT]",
                "total_duration": "[TOTAL HOURS/DAYS]",
                "geographic_impact": "[MEMBER STATES / REGIONS AFFECTED]",
                "data_impact_detail": "[DETAILED DATA IMPACT DESCRIPTION]",
                "financial_impact_eur": "[TOTAL DIRECT AND INDIRECT COSTS]",
                "regulatory_impact": "[ANY REGULATORY CONSEQUENCES]",
                "reputational_impact": "[ASSESSMENT]",
            },
            "mitigation_measures": {
                "immediate_measures": "[MEASURES TAKEN DURING INCIDENT]",
                "short_term_measures": "[MEASURES IMPLEMENTED POST-INCIDENT]",
                "long_term_measures": "[PLANNED IMPROVEMENTS TO PREVENT RECURRENCE]",
                "timeline_for_implementation": "[DATES FOR EACH MEASURE]",
            },
            "lessons_learned": {
                "what_worked_well": "[LIST]",
                "areas_for_improvement": "[LIST]",
                "process_changes": "[PLANNED CHANGES TO PROCEDURES]",
                "technology_changes": "[PLANNED TECHNOLOGY INVESTMENTS]",
                "training_needs": "[IDENTIFIED TRAINING GAPS]",
            },
        },
    }

    if reporting.get("deadlines"):
        template["reporting_deadlines"] = reporting["deadlines"]

    return template


def format_text_report(result: Dict[str, Any]) -> str:
    """Format classification result as human-readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("DORA INCIDENT CLASSIFICATION REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {result['timestamp']}")
    lines.append("")

    # Input summary
    inp = result["input"]
    lines.append("INCIDENT DETAILS")
    lines.append("-" * 40)
    if inp.get("incident_description"):
        lines.append(f"  Description:    {inp['incident_description']}")
    if inp.get("detection_time"):
        lines.append(f"  Detected:       {inp['detection_time']}")
    if inp.get("suspected_malicious") is not None:
        lines.append(f"  Malicious:      {'Yes' if inp['suspected_malicious'] else 'No'}")
    lines.append("")

    # Classification criteria
    lines.append("CLASSIFICATION CRITERIA (Article 18)")
    lines.append("-" * 40)
    criteria = result.get("classification", {}).get("criteria", {})
    for key, criterion in criteria.items():
        lines.append(f"  {criterion['criterion']}")
        lines.append(f"    Value:  {criterion.get('value', 'N/A')}")
        lines.append(f"    Level:  {criterion.get('label', 'N/A')}")
        lines.append(f"    Score:  {criterion.get('score', 0)}/4")
        lines.append("")

    total = result.get("classification", {}).get("total_score", 0)
    max_score = result.get("classification", {}).get("max_score", 24)
    lines.append(f"  TOTAL SCORE: {total}/{max_score}")
    lines.append(f"  Major incident threshold: {MAJOR_INCIDENT_THRESHOLD}/{max_score}")
    lines.append("")

    # Severity
    severity = result.get("severity", {})
    lines.append("SEVERITY DETERMINATION")
    lines.append("-" * 40)
    is_major = severity.get("is_major_incident", False)
    lines.append(f"  Major incident:  {'YES' if is_major else 'NO'}")
    lines.append(f"  Severity level:  {severity.get('level', 'N/A').upper()}")
    lines.append(f"  Assessment:      {severity.get('description', 'N/A')}")
    lines.append("")

    # Reporting
    reporting = result.get("reporting", {})
    lines.append("REPORTING OBLIGATIONS")
    lines.append("-" * 40)
    if reporting.get("mandatory"):
        lines.append("  MANDATORY REPORTING REQUIRED")
        lines.append("")
        deadlines = reporting.get("deadlines", {})
        for stage_key, stage_data in deadlines.items():
            lines.append(f"  {stage_key.replace('_', ' ').title()}")
            lines.append(f"    Deadline:    {stage_data.get('deadline', 'N/A')}")
            lines.append(f"    Requirement: {stage_data.get('requirement', 'N/A')}")
            lines.append(f"    Content:     {stage_data.get('content', 'N/A')}")
            lines.append(f"    Reference:   {stage_data.get('article', 'N/A')}")
            lines.append("")

        client = reporting.get("client_notification", {})
        if client.get("required"):
            lines.append("  Client Notification")
            lines.append(f"    Required: Yes — {client.get('requirement', '')}")
            lines.append(f"    Reference: {client.get('article', '')}")
    else:
        lines.append(f"  {reporting.get('note', 'No mandatory reporting required.')}")
        if reporting.get("voluntary_reporting"):
            lines.append(f"  Note: {reporting['voluntary_reporting']}")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def generate_input_template() -> Dict[str, Any]:
    """Generate an incident input template."""
    return {
        "_instructions": "Fill in incident details. See field descriptions for accepted values.",
        "clients_affected": 0,
        "duration_hours": 0,
        "geographic_spread": "local | national | eu_multiple | global",
        "data_loss": "none | availability | integrity | confidentiality | multiple",
        "services_critical": "non_critical | important | critical | multiple_critical",
        "economic_impact_eur": 0,
        "detection_time": "YYYY-MM-DDTHH:MM:SS (ISO 8601 format)",
        "incident_description": "Brief description of the incident",
        "suspected_malicious": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="DORA Incident Classifier — Classify ICT incidents per DORA Article 18",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --clients-affected 5000 --duration-hours 4 --data-loss confidentiality --services-critical critical --economic-impact 500000
  %(prog)s --config incident.json --json
  %(prog)s --config incident.json --generate-template --output notification.json
  %(prog)s --template > incident_input.json

Geographic spread values: local, national, eu_multiple, global
Data loss values: none, availability, integrity, confidentiality, multiple
Services criticality values: non_critical, important, critical, multiple_critical
        """,
    )

    parser.add_argument("--clients-affected", type=int, dest="clients_affected",
                        help="Number of clients/counterparts affected")
    parser.add_argument("--duration-hours", type=float, dest="duration_hours",
                        help="Duration of incident in hours")
    parser.add_argument("--geographic-spread", dest="geographic_spread",
                        choices=["local", "national", "eu_multiple", "global"],
                        help="Geographic spread of the incident")
    parser.add_argument("--data-loss", dest="data_loss",
                        choices=["none", "availability", "integrity", "confidentiality", "multiple"],
                        help="Type of data loss")
    parser.add_argument("--services-critical", dest="services_critical",
                        choices=["non_critical", "important", "critical", "multiple_critical"],
                        help="Criticality of affected services")
    parser.add_argument("--economic-impact", type=float, dest="economic_impact",
                        help="Estimated economic impact in EUR")
    parser.add_argument("--detection-time", dest="detection_time",
                        help="Time incident was detected (ISO 8601)")
    parser.add_argument("--description", help="Brief incident description")
    parser.add_argument("--malicious", action="store_true", help="Incident is suspected malicious")
    parser.add_argument("--config", help="Path to JSON incident description file")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--output", help="Write output to file")
    parser.add_argument("--generate-template", action="store_true", dest="generate_template",
                        help="Generate incident notification templates based on classification")
    parser.add_argument("--template", action="store_true",
                        help="Generate incident input template")

    args = parser.parse_args()

    # Input template mode
    if args.template:
        print(json.dumps(generate_input_template(), indent=2))
        return

    # Load from config or CLI args
    if args.config:
        try:
            with open(args.config) as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)

        clients_affected = config.get("clients_affected", 0)
        duration_hours = config.get("duration_hours", 0)
        geographic_spread = config.get("geographic_spread", "local")
        data_loss = config.get("data_loss", "none")
        services_critical = config.get("services_critical", "non_critical")
        economic_impact = config.get("economic_impact_eur", config.get("economic_impact", 0))
        detection_time = config.get("detection_time")
        description = config.get("incident_description", config.get("description", ""))
        malicious = config.get("suspected_malicious", False)
    else:
        clients_affected = args.clients_affected or 0
        duration_hours = args.duration_hours or 0
        geographic_spread = args.geographic_spread or "local"
        data_loss = args.data_loss or "none"
        services_critical = args.services_critical or "non_critical"
        economic_impact = args.economic_impact or 0
        detection_time = args.detection_time
        description = args.description or ""
        malicious = args.malicious

    # Classify
    result = classify_incident(
        clients_affected=clients_affected,
        duration_hours=duration_hours,
        geographic_spread=geographic_spread,
        data_loss=data_loss,
        services_critical=services_critical,
        economic_impact=economic_impact,
        detection_time=detection_time,
        incident_description=description,
        malicious=malicious,
    )

    # Generate notification template if requested
    if args.generate_template:
        template = generate_notification_template(result)
        output = json.dumps(template, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Notification templates written to {args.output}")
        else:
            print(output)
        return

    # Format output
    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_text_report(result)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
