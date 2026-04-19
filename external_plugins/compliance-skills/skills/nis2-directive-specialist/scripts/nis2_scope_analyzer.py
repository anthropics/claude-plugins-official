#!/usr/bin/env python3
"""
NIS2 Scope Analyzer

Determines whether an organization falls within the scope of the NIS2 Directive
(EU 2022/2555), classifies it as Essential or Important entity, identifies
applicable obligations, and generates a compliance checklist.

Usage:
    python nis2_scope_analyzer.py --sector energy --sub-sector electricity --employees 500 --turnover 100
    python nis2_scope_analyzer.py --config organization.json --json --output scope_report.json
    python nis2_scope_analyzer.py --sector health --sub-sector healthcare_providers --employees 75 --turnover 15 --checklist
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# --- NIS2 Sector Definitions ---

ANNEX_I_SECTORS = {
    "energy": {
        "name": "Energy",
        "sub_sectors": {
            "electricity": "Electricity undertakings, DSOs, TSOs, producers, nominated electricity market operators, storage operators",
            "oil": "Operators of oil pipelines, oil production, refining, treatment, storage, transmission",
            "gas": "Supply undertakings, DSOs, TSOs, storage operators, LNG terminal operators",
            "hydrogen": "Operators of hydrogen production, storage, and transmission",
            "district_heating_cooling": "District heating and cooling operators",
        },
        "annex": "I",
    },
    "transport": {
        "name": "Transport",
        "sub_sectors": {
            "air": "Air carriers, airport management bodies, traffic management control operators",
            "rail": "Infrastructure managers, railway undertakings",
            "water": "Inland, sea and coastal passenger/freight water transport companies, port managing bodies, vessel traffic services",
            "road": "Road authorities responsible for traffic management control, operators of ITS",
        },
        "annex": "I",
    },
    "banking": {
        "name": "Banking",
        "sub_sectors": {
            "credit_institutions": "Credit institutions as defined in Regulation (EU) No 575/2013",
        },
        "annex": "I",
    },
    "financial_market": {
        "name": "Financial Market Infrastructure",
        "sub_sectors": {
            "trading_venues": "Operators of trading venues",
            "central_counterparties": "Central counterparties (CCPs)",
        },
        "annex": "I",
    },
    "health": {
        "name": "Health",
        "sub_sectors": {
            "healthcare_providers": "Healthcare providers as defined in Directive 2011/24/EU",
            "eu_reference_labs": "EU reference laboratories under Regulation (EU) 2022/2371",
            "pharma_manufacturing": "Entities manufacturing pharmaceutical preparations and products",
            "medical_devices_critical": "Entities manufacturing medical devices considered critical during public health emergencies",
        },
        "annex": "I",
    },
    "drinking_water": {
        "name": "Drinking Water",
        "sub_sectors": {
            "water_supply": "Suppliers and distributors of water intended for human consumption (excl. distributors for whom distribution is a non-essential part of general retail activity)",
        },
        "annex": "I",
    },
    "waste_water": {
        "name": "Waste Water",
        "sub_sectors": {
            "waste_water_treatment": "Entities collecting, disposing, or treating urban waste water, domestic waste water, or industrial waste water",
        },
        "annex": "I",
    },
    "digital_infrastructure": {
        "name": "Digital Infrastructure",
        "sub_sectors": {
            "ixp": "Internet Exchange Point providers",
            "dns": "DNS service providers (excluding root name servers)",
            "tld_registry": "TLD name registries",
            "cloud_computing": "Cloud computing service providers",
            "data_center": "Data centre service providers",
            "cdn": "Content delivery network providers",
            "trust_services": "Trust service providers",
            "public_ecn": "Providers of public electronic communications networks",
            "public_ecs": "Providers of publicly available electronic communications services",
        },
        "annex": "I",
    },
    "ict_service_management": {
        "name": "ICT Service Management (B2B)",
        "sub_sectors": {
            "managed_service": "Managed service providers",
            "managed_security_service": "Managed security service providers",
        },
        "annex": "I",
    },
    "public_administration": {
        "name": "Public Administration",
        "sub_sectors": {
            "central_government": "Central government entities of a Member State",
            "regional_government": "Public administration entities at regional level (NUTS level 1 and 2)",
        },
        "annex": "I",
    },
    "space": {
        "name": "Space",
        "sub_sectors": {
            "ground_infrastructure": "Operators of ground-based infrastructure supporting provision of space-based services",
        },
        "annex": "I",
    },
}

ANNEX_II_SECTORS = {
    "postal_services": {
        "name": "Postal and Courier Services",
        "sub_sectors": {
            "postal_providers": "Providers of postal services including courier services",
        },
        "annex": "II",
    },
    "waste_management": {
        "name": "Waste Management",
        "sub_sectors": {
            "waste_operators": "Entities carrying out waste management (excluding those for whom it is not their principal economic activity)",
        },
        "annex": "II",
    },
    "chemicals": {
        "name": "Manufacture, Production and Distribution of Chemicals",
        "sub_sectors": {
            "chemical_entities": "Entities manufacturing, producing, or distributing substances and mixtures (REACH regulation)",
        },
        "annex": "II",
    },
    "food": {
        "name": "Food Production, Processing and Distribution",
        "sub_sectors": {
            "food_businesses": "Food businesses engaged in wholesale distribution, industrial production, and processing",
        },
        "annex": "II",
    },
    "manufacturing": {
        "name": "Manufacturing",
        "sub_sectors": {
            "medical_devices": "Manufacture of medical devices and in vitro diagnostic medical devices",
            "computers_electronics": "Manufacture of computer, electronic, and optical products",
            "electrical_equipment": "Manufacture of electrical equipment",
            "machinery": "Manufacture of machinery and equipment n.e.c.",
            "motor_vehicles": "Manufacture of motor vehicles, trailers, and semi-trailers",
            "other_transport": "Manufacture of other transport equipment",
        },
        "annex": "II",
    },
    "digital_providers": {
        "name": "Digital Providers",
        "sub_sectors": {
            "online_marketplaces": "Providers of online marketplaces",
            "search_engines": "Providers of online search engines",
            "social_networks": "Providers of social networking services platforms",
        },
        "annex": "II",
    },
    "research": {
        "name": "Research",
        "sub_sectors": {
            "research_organizations": "Research organizations",
        },
        "annex": "II",
    },
}

# Sub-sectors automatically in scope regardless of size
AUTO_INCLUDE_SUB_SECTORS = {
    "trust_services",
    "tld_registry",
    "dns",
    "public_ecn",
    "public_ecs",
    "central_government",
    "regional_government",
}

# Sub-sectors that are always classified as Essential
ALWAYS_ESSENTIAL_SUB_SECTORS = {
    "trust_services",  # Qualified trust service providers
    "tld_registry",
    "dns",
    "public_ecn",
    "public_ecs",
    "central_government",
}

NIS2_MINIMUM_MEASURES = [
    "Risk analysis and information system security policies",
    "Incident handling",
    "Business continuity and crisis management",
    "Supply chain security",
    "Security in network and information systems acquisition, development, and maintenance",
    "Policies and procedures for assessing effectiveness of cybersecurity risk management",
    "Basic cyber hygiene practices and cybersecurity training",
    "Policies and procedures regarding use of cryptography and encryption",
    "Human resources security, access control policies, and asset management",
    "Use of multi-factor authentication, secured communications, and secured emergency communications",
]


def determine_size_category(
    employees: int, turnover_millions: float, balance_sheet_millions: float = 0.0
) -> str:
    """Determine organization size category per EU recommendation 2003/361/EC."""
    if employees >= 250 or turnover_millions >= 50 or balance_sheet_millions >= 43:
        return "large"
    elif employees >= 50 or turnover_millions >= 10 or balance_sheet_millions >= 10:
        return "medium"
    elif employees >= 10 or turnover_millions >= 2 or balance_sheet_millions >= 2:
        return "small"
    else:
        return "micro"


def find_sector(sector_key: str) -> Optional[Dict[str, Any]]:
    """Look up sector in both annexes."""
    if sector_key in ANNEX_I_SECTORS:
        return ANNEX_I_SECTORS[sector_key]
    if sector_key in ANNEX_II_SECTORS:
        return ANNEX_II_SECTORS[sector_key]
    return None


def analyze_scope(
    sector: str,
    sub_sector: str,
    employees: int,
    turnover_millions: float,
    balance_sheet_millions: float = 0.0,
    sole_provider: bool = False,
    significant_impact: bool = False,
    systemic_risk: bool = False,
) -> Dict[str, Any]:
    """Analyze whether an organization is in scope of NIS2 and classify it."""

    result = {
        "timestamp": datetime.now().isoformat(),
        "input": {
            "sector": sector,
            "sub_sector": sub_sector,
            "employees": employees,
            "turnover_millions_eur": turnover_millions,
            "balance_sheet_millions_eur": balance_sheet_millions,
            "sole_provider": sole_provider,
            "significant_impact": significant_impact,
            "systemic_risk": systemic_risk,
        },
        "analysis": {},
        "classification": {},
        "obligations": [],
        "checklist": [],
    }

    # Find sector
    sector_info = find_sector(sector)
    if not sector_info:
        result["analysis"]["in_scope"] = False
        result["analysis"]["reason"] = f"Sector '{sector}' not found in NIS2 Annex I or Annex II"
        result["analysis"]["available_sectors"] = sorted(
            list(ANNEX_I_SECTORS.keys()) + list(ANNEX_II_SECTORS.keys())
        )
        return result

    # Validate sub-sector
    if sub_sector not in sector_info["sub_sectors"]:
        result["analysis"]["in_scope"] = False
        result["analysis"]["reason"] = f"Sub-sector '{sub_sector}' not found in sector '{sector}'"
        result["analysis"]["available_sub_sectors"] = list(sector_info["sub_sectors"].keys())
        return result

    annex = sector_info["annex"]
    size_category = determine_size_category(employees, turnover_millions, balance_sheet_millions)

    result["analysis"]["sector_name"] = sector_info["name"]
    result["analysis"]["sub_sector_description"] = sector_info["sub_sectors"][sub_sector]
    result["analysis"]["annex"] = annex
    result["analysis"]["size_category"] = size_category

    # Determine if in scope
    auto_included = sub_sector in AUTO_INCLUDE_SUB_SECTORS
    size_eligible = size_category in ("medium", "large")
    special_designation = sole_provider or significant_impact or systemic_risk

    in_scope = auto_included or size_eligible or special_designation

    result["analysis"]["in_scope"] = in_scope
    result["analysis"]["auto_included"] = auto_included
    result["analysis"]["size_eligible"] = size_eligible
    result["analysis"]["special_designation"] = special_designation

    if not in_scope:
        reasons = []
        if not auto_included:
            reasons.append("Not in automatic inclusion category")
        if not size_eligible:
            reasons.append(
                f"Below size threshold ({size_category} enterprise — need medium or large)"
            )
        if not special_designation:
            reasons.append("No special designation criteria met")
        result["analysis"]["exclusion_reasons"] = reasons
        result["analysis"]["recommendation"] = (
            "Organization appears to be outside NIS2 scope. However, verify with national "
            "transposition legislation as Member States may extend scope. Also check if "
            "the organization is a sole provider or has significant impact on public safety."
        )
        return result

    # Classify entity type
    inclusion_reasons = []
    if auto_included:
        inclusion_reasons.append(f"Automatic inclusion: {sub_sector} entities are included regardless of size")
    if size_eligible:
        inclusion_reasons.append(f"Size threshold met: {size_category} enterprise")
    if sole_provider:
        inclusion_reasons.append("Sole provider of service in Member State")
    if significant_impact:
        inclusion_reasons.append("Significant impact on public safety, security, or health")
    if systemic_risk:
        inclusion_reasons.append("Could induce systemic risk (especially cross-border)")

    result["analysis"]["inclusion_reasons"] = inclusion_reasons

    # Determine Essential vs Important
    is_essential = False
    entity_type_reasons = []

    if annex == "I" and size_category == "large":
        is_essential = True
        entity_type_reasons.append("Large entity in Annex I (high criticality) sector")
    if sub_sector in ALWAYS_ESSENTIAL_SUB_SECTORS:
        is_essential = True
        entity_type_reasons.append(f"Sub-sector '{sub_sector}' is always classified as Essential")
    if annex == "I" and (sole_provider or significant_impact or systemic_risk):
        is_essential = True
        entity_type_reasons.append("Special designation in Annex I sector")

    entity_type = "essential" if is_essential else "important"

    result["classification"]["entity_type"] = entity_type
    result["classification"]["entity_type_reasons"] = entity_type_reasons

    # Penalties
    if entity_type == "essential":
        result["classification"]["max_fine"] = "EUR 10,000,000 or 2% of total worldwide annual turnover, whichever is higher"
        result["classification"]["supervision"] = "Ex-ante (proactive supervision)"
        result["classification"]["management_ban_possible"] = True
    else:
        result["classification"]["max_fine"] = "EUR 7,000,000 or 1.4% of total worldwide annual turnover, whichever is higher"
        result["classification"]["supervision"] = "Ex-post (reactive, complaint-based)"
        result["classification"]["management_ban_possible"] = False

    # Obligations
    obligations = [
        "Implement all 10 minimum security measures (Article 21)",
        "Report significant incidents to CSIRT/competent authority (Article 23)",
        "Register with competent authority (Article 27)",
        "Management body must approve and oversee cybersecurity measures (Article 20)",
        "Management body members must undergo cybersecurity training (Article 20)",
        "Cooperate with competent authority during inspections and audits",
    ]

    if entity_type == "essential":
        obligations.extend([
            "Subject to proactive supervision including regular security audits",
            "Subject to on-site inspections",
            "Subject to ad hoc audits in case of significant incidents or non-compliance",
        ])

    # Supply chain obligations
    if annex == "I":
        obligations.append(
            "Participate in coordinated supply chain security risk assessments if requested (Article 22)"
        )

    result["obligations"] = obligations

    # Compliance checklist
    result["checklist"] = _generate_checklist(entity_type, annex)

    return result


def _generate_checklist(entity_type: str, annex: str) -> List[Dict[str, str]]:
    """Generate a compliance checklist based on entity classification."""
    checklist = []

    # Registration
    checklist.append({
        "category": "Registration",
        "item": "Register with national competent authority",
        "priority": "critical",
        "deadline": "Before enforcement deadline",
        "reference": "Article 27",
    })

    # Management accountability
    checklist.append({
        "category": "Governance",
        "item": "Obtain management body approval for cybersecurity risk management measures",
        "priority": "critical",
        "reference": "Article 20(1)",
    })
    checklist.append({
        "category": "Governance",
        "item": "Arrange cybersecurity training for management body members",
        "priority": "critical",
        "reference": "Article 20(2)",
    })

    # 10 minimum measures
    for i, measure in enumerate(NIS2_MINIMUM_MEASURES, 1):
        checklist.append({
            "category": f"Measure {i}",
            "item": f"Implement: {measure}",
            "priority": "high",
            "reference": f"Article 21(2)({chr(96 + i)})",
        })

    # Incident reporting
    checklist.append({
        "category": "Incident Reporting",
        "item": "Establish 24-hour early warning capability",
        "priority": "critical",
        "reference": "Article 23(4)(a)",
    })
    checklist.append({
        "category": "Incident Reporting",
        "item": "Establish 72-hour incident notification process",
        "priority": "critical",
        "reference": "Article 23(4)(b)",
    })
    checklist.append({
        "category": "Incident Reporting",
        "item": "Establish process for 1-month final incident reports",
        "priority": "high",
        "reference": "Article 23(4)(d)",
    })
    checklist.append({
        "category": "Incident Reporting",
        "item": "Define process for informing service recipients of significant incidents",
        "priority": "high",
        "reference": "Article 23(1)",
    })

    # Supply chain
    checklist.append({
        "category": "Supply Chain",
        "item": "Conduct supply chain risk assessments for direct suppliers",
        "priority": "high",
        "reference": "Article 21(2)(d)",
    })
    checklist.append({
        "category": "Supply Chain",
        "item": "Include security requirements in supplier contracts",
        "priority": "high",
        "reference": "Article 21(3)",
    })

    # Audit readiness (essential entities)
    if entity_type == "essential":
        checklist.append({
            "category": "Audit Readiness",
            "item": "Prepare for regular proactive security audits by competent authority",
            "priority": "high",
            "reference": "Article 32",
        })
        checklist.append({
            "category": "Audit Readiness",
            "item": "Prepare for on-site and off-site inspections",
            "priority": "medium",
            "reference": "Article 32(2)",
        })

    return checklist


def format_text_report(result: Dict[str, Any]) -> str:
    """Format analysis result as human-readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("NIS2 DIRECTIVE — SCOPE ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {result['timestamp']}")
    lines.append("")

    inp = result["input"]
    lines.append("ORGANIZATION PROFILE")
    lines.append("-" * 40)
    lines.append(f"  Sector:       {inp['sector']}")
    lines.append(f"  Sub-sector:   {inp['sub_sector']}")
    lines.append(f"  Employees:    {inp['employees']}")
    lines.append(f"  Turnover:     EUR {inp['turnover_millions_eur']}M")
    if inp.get("balance_sheet_millions_eur"):
        lines.append(f"  Balance sheet: EUR {inp['balance_sheet_millions_eur']}M")
    lines.append("")

    analysis = result["analysis"]

    if "sector_name" in analysis:
        lines.append(f"  Sector name:       {analysis['sector_name']}")
        lines.append(f"  Sub-sector detail: {analysis.get('sub_sector_description', 'N/A')}")
        lines.append(f"  Annex:             {analysis['annex']}")
        lines.append(f"  Size category:     {analysis['size_category']}")
        lines.append("")

    in_scope = analysis.get("in_scope", False)
    lines.append("SCOPE DETERMINATION")
    lines.append("-" * 40)
    lines.append(f"  In NIS2 scope: {'YES' if in_scope else 'NO'}")

    if in_scope:
        lines.append("")
        lines.append("  Inclusion reasons:")
        for reason in analysis.get("inclusion_reasons", []):
            lines.append(f"    - {reason}")

        classification = result.get("classification", {})
        lines.append("")
        lines.append("ENTITY CLASSIFICATION")
        lines.append("-" * 40)
        lines.append(f"  Entity type:  {classification.get('entity_type', 'N/A').upper()}")
        lines.append(f"  Max fine:     {classification.get('max_fine', 'N/A')}")
        lines.append(f"  Supervision:  {classification.get('supervision', 'N/A')}")
        lines.append(f"  Management ban possible: {'Yes' if classification.get('management_ban_possible') else 'No'}")

        if classification.get("entity_type_reasons"):
            lines.append("")
            lines.append("  Classification reasons:")
            for reason in classification["entity_type_reasons"]:
                lines.append(f"    - {reason}")

        lines.append("")
        lines.append("APPLICABLE OBLIGATIONS")
        lines.append("-" * 40)
        for i, obligation in enumerate(result.get("obligations", []), 1):
            lines.append(f"  {i}. {obligation}")

        if result.get("checklist"):
            lines.append("")
            lines.append("COMPLIANCE CHECKLIST")
            lines.append("-" * 40)
            current_category = ""
            for item in result["checklist"]:
                if item["category"] != current_category:
                    current_category = item["category"]
                    lines.append(f"\n  [{current_category}]")
                priority_marker = {"critical": "[!!!]", "high": "[!!]", "medium": "[!]"}.get(
                    item["priority"], "[ ]"
                )
                lines.append(f"    {priority_marker} {item['item']}")
                lines.append(f"          Ref: {item['reference']}")
    else:
        if analysis.get("exclusion_reasons"):
            lines.append("")
            for reason in analysis["exclusion_reasons"]:
                lines.append(f"    - {reason}")
        if analysis.get("recommendation"):
            lines.append("")
            lines.append(f"  Note: {analysis['recommendation']}")
        if analysis.get("available_sectors"):
            lines.append("")
            lines.append("  Available sectors:")
            for s in analysis["available_sectors"]:
                lines.append(f"    - {s}")
        if analysis.get("available_sub_sectors"):
            lines.append("")
            lines.append("  Available sub-sectors:")
            for s in analysis["available_sub_sectors"]:
                lines.append(f"    - {s}")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def list_sectors() -> Dict[str, Any]:
    """Return a structured listing of all NIS2 sectors and sub-sectors."""
    sectors = {"annex_i": {}, "annex_ii": {}}
    for key, info in ANNEX_I_SECTORS.items():
        sectors["annex_i"][key] = {
            "name": info["name"],
            "sub_sectors": list(info["sub_sectors"].keys()),
        }
    for key, info in ANNEX_II_SECTORS.items():
        sectors["annex_ii"][key] = {
            "name": info["name"],
            "sub_sectors": list(info["sub_sectors"].keys()),
        }
    return sectors


def main():
    parser = argparse.ArgumentParser(
        description="NIS2 Directive Scope Analyzer — Determine if an organization falls within NIS2 scope",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --sector energy --sub-sector electricity --employees 500 --turnover 100
  %(prog)s --sector health --sub-sector healthcare_providers --employees 75 --turnover 15 --json
  %(prog)s --config organization.json --json --output scope_report.json
  %(prog)s --list-sectors
  %(prog)s --sector digital_infrastructure --sub-sector cloud_computing --employees 200 --turnover 50 --checklist
        """,
    )

    parser.add_argument("--sector", help="Organization sector (e.g., energy, health, transport)")
    parser.add_argument("--sub-sector", dest="sub_sector", help="Sub-sector within the sector")
    parser.add_argument("--employees", type=int, help="Number of employees")
    parser.add_argument("--turnover", type=float, help="Annual turnover in millions EUR")
    parser.add_argument("--balance-sheet", type=float, default=0.0, dest="balance_sheet",
                        help="Annual balance sheet total in millions EUR (default: 0)")
    parser.add_argument("--sole-provider", action="store_true", dest="sole_provider",
                        help="Organization is the sole provider of a service in a Member State")
    parser.add_argument("--significant-impact", action="store_true", dest="significant_impact",
                        help="Disruption could have significant impact on public safety/security/health")
    parser.add_argument("--systemic-risk", action="store_true", dest="systemic_risk",
                        help="Disruption could induce systemic risk (especially cross-border)")
    parser.add_argument("--config", help="Path to JSON configuration file with organization details")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--output", help="Write output to file")
    parser.add_argument("--checklist", action="store_true", help="Include detailed compliance checklist")
    parser.add_argument("--list-sectors", action="store_true", dest="list_sectors",
                        help="List all NIS2 sectors and sub-sectors")

    args = parser.parse_args()

    # List sectors mode
    if args.list_sectors:
        sectors = list_sectors()
        if args.json:
            output = json.dumps(sectors, indent=2)
        else:
            lines = ["NIS2 Sectors and Sub-sectors", "=" * 40, ""]
            lines.append("ANNEX I — High Criticality Sectors")
            lines.append("-" * 40)
            for key, info in sectors["annex_i"].items():
                lines.append(f"  {key}: {info['name']}")
                for ss in info["sub_sectors"]:
                    lines.append(f"    - {ss}")
            lines.append("")
            lines.append("ANNEX II — Other Critical Sectors")
            lines.append("-" * 40)
            for key, info in sectors["annex_ii"].items():
                lines.append(f"  {key}: {info['name']}")
                for ss in info["sub_sectors"]:
                    lines.append(f"    - {ss}")
            output = "\n".join(lines)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Sector listing written to {args.output}")
        else:
            print(output)
        return

    # Load from config file
    if args.config:
        try:
            with open(args.config) as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)

        sector = config.get("sector", args.sector)
        sub_sector = config.get("sub_sector", args.sub_sector)
        employees = config.get("employees", args.employees)
        turnover = config.get("turnover_millions_eur", args.turnover)
        balance_sheet = config.get("balance_sheet_millions_eur", args.balance_sheet or 0.0)
        sole_provider = config.get("sole_provider", args.sole_provider)
        significant_impact = config.get("significant_impact", args.significant_impact)
        systemic_risk = config.get("systemic_risk", args.systemic_risk)
    else:
        sector = args.sector
        sub_sector = args.sub_sector
        employees = args.employees
        turnover = args.turnover
        balance_sheet = args.balance_sheet
        sole_provider = args.sole_provider
        significant_impact = args.significant_impact
        systemic_risk = args.systemic_risk

    # Validate required fields
    if not all([sector, sub_sector, employees is not None, turnover is not None]):
        parser.error("Required: --sector, --sub-sector, --employees, --turnover (or --config with these fields)")

    # Run analysis
    result = analyze_scope(
        sector=sector,
        sub_sector=sub_sector,
        employees=employees,
        turnover_millions=turnover,
        balance_sheet_millions=balance_sheet,
        sole_provider=sole_provider,
        significant_impact=significant_impact,
        systemic_risk=systemic_risk,
    )

    # Remove checklist from output if not requested
    if not args.checklist and not args.json:
        result.pop("checklist", None)

    # Format output
    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_text_report(result)

    # Write or print
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
