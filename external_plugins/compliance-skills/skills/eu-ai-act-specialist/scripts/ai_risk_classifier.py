#!/usr/bin/env python3
"""
EU AI Act Risk Classifier

Classifies AI systems into EU AI Act (Regulation EU 2024/1689) risk categories
based on a JSON description. Checks against all Annex III high-risk categories,
identifies applicable obligations, and generates a compliance checklist.

Usage:
    python ai_risk_classifier.py --input system_description.json
    python ai_risk_classifier.py --inline '{"name": "...", "description": "..."}'
    python ai_risk_classifier.py --input system.json --json
    python ai_risk_classifier.py --input system.json --output report.json

Input JSON schema:
{
    "name": "System Name",
    "description": "What the system does",
    "domain": "employment|education|law_enforcement|...",
    "sub_domain": "recruitment|assessment|...",
    "uses_biometrics": true|false,
    "biometric_type": "facial_recognition|fingerprint|voice|emotion|...",
    "biometric_context": "real_time_public|remote|workplace|education|...",
    "interacts_with_persons": true|false,
    "generates_content": true|false,
    "content_type": "text|image|audio|video|deepfake",
    "decision_type": "advisory|automated_with_review|fully_automated",
    "affected_persons": "description of who is affected",
    "is_safety_component": true|false,
    "product_legislation": "machinery|toys|lifts|...",
    "eu_deployment": true|false,
    "social_scoring": true|false,
    "manipulates_behavior": true|false,
    "targets_vulnerable_groups": true|false,
    "predictive_policing_individual": true|false,
    "untargeted_scraping": true|false,
    "is_gpai": true|false,
    "training_compute_flops": 1e25,
    "critical_infrastructure": true|false,
    "infrastructure_type": "water|gas|electricity|heating|transport|digital"
}
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Risk classification data
# ---------------------------------------------------------------------------

PROHIBITED_PRACTICES = {
    "social_scoring": {
        "article": "Art. 5(1)(c)",
        "description": "Social scoring by public authorities leading to detrimental treatment",
        "check_fields": ["social_scoring"],
    },
    "real_time_biometric_public": {
        "article": "Art. 5(1)(h)",
        "description": "Real-time remote biometric identification in publicly accessible spaces for law enforcement",
        "check_fields": ["biometric_context"],
        "match_value": "real_time_public",
    },
    "emotion_recognition_workplace_education": {
        "article": "Art. 5(1)(f)",
        "description": "Emotion recognition in the workplace or educational institutions (except medical/safety)",
        "check_fields": ["biometric_type", "biometric_context"],
    },
    "predictive_policing_individual": {
        "article": "Art. 5(1)(d)",
        "description": "Individual predictive policing based solely on profiling or personality traits",
        "check_fields": ["predictive_policing_individual"],
    },
    "exploitation_of_vulnerabilities": {
        "article": "Art. 5(1)(b)",
        "description": "Exploiting vulnerabilities of age, disability, or social/economic situation",
        "check_fields": ["manipulates_behavior", "targets_vulnerable_groups"],
    },
    "subliminal_manipulation": {
        "article": "Art. 5(1)(a)",
        "description": "Subliminal manipulation causing significant harm",
        "check_fields": ["manipulates_behavior"],
    },
    "untargeted_scraping": {
        "article": "Art. 5(1)(e)",
        "description": "Untargeted scraping of facial images from internet or CCTV",
        "check_fields": ["untargeted_scraping"],
    },
    "biometric_categorization_sensitive": {
        "article": "Art. 5(1)(g)",
        "description": "Biometric categorization to deduce race, political opinions, religion, sexual orientation",
        "check_fields": ["biometric_type"],
        "match_value": "categorization_sensitive",
    },
}

ANNEX_III_CATEGORIES = {
    "biometric_identification": {
        "number": 1,
        "title": "Biometric identification and categorisation of natural persons",
        "description": "AI systems intended to be used for remote biometric identification (excluding real-time in public by law enforcement, which is prohibited), biometric categorisation by sensitive or protected attributes, or emotion recognition.",
        "domains": ["biometrics"],
        "keywords": ["biometric", "facial_recognition", "fingerprint", "iris", "voice_recognition", "emotion_recognition", "categorization"],
    },
    "critical_infrastructure": {
        "number": 2,
        "title": "Management and operation of critical infrastructure",
        "description": "AI systems intended as safety components in management and operation of critical digital infrastructure, road traffic, or supply of water, gas, heating, or electricity.",
        "domains": ["critical_infrastructure", "infrastructure", "utilities", "transport"],
        "keywords": ["infrastructure", "water", "gas", "electricity", "heating", "transport", "traffic", "digital_infrastructure"],
    },
    "education": {
        "number": 3,
        "title": "Education and vocational training",
        "description": "AI systems determining access/admission to educational institutions, evaluating learning outcomes, assessing appropriate education level, or monitoring prohibited behaviour during tests.",
        "domains": ["education", "training", "academic"],
        "keywords": ["education", "admission", "grading", "assessment", "exam", "proctoring", "student", "learning"],
    },
    "employment": {
        "number": 4,
        "title": "Employment, workers management, and access to self-employment",
        "description": "AI systems for recruitment, screening, filtering, or evaluating candidates; making decisions on promotion, termination, task allocation, or performance monitoring.",
        "domains": ["employment", "hr", "recruitment", "workforce"],
        "keywords": ["recruitment", "hiring", "screening", "resume", "cv", "candidate", "employee", "performance", "promotion", "termination", "task_allocation"],
    },
    "essential_services": {
        "number": 5,
        "title": "Access to and enjoyment of essential private services and essential public services and benefits",
        "description": "AI systems evaluating creditworthiness, risk assessment and pricing in life/health insurance, evaluating eligibility for public assistance, or prioritizing emergency dispatch.",
        "domains": ["finance", "insurance", "credit", "public_services", "emergency"],
        "keywords": ["credit", "creditworthiness", "insurance", "risk_assessment", "benefits", "eligibility", "emergency", "dispatch", "scoring", "loan"],
    },
    "law_enforcement": {
        "number": 6,
        "title": "Law enforcement",
        "description": "AI systems used by law enforcement for individual risk assessment, polygraph or emotional state detection, deepfake detection in investigations, crime analytics, or profiling.",
        "domains": ["law_enforcement", "police", "security"],
        "keywords": ["law_enforcement", "police", "polygraph", "crime", "investigation", "profiling", "surveillance"],
    },
    "migration": {
        "number": 7,
        "title": "Migration, asylum, and border control management",
        "description": "AI systems for asylum risk assessment, examining applications for visas/residence permits, or identification at border checks.",
        "domains": ["migration", "border", "asylum", "immigration"],
        "keywords": ["migration", "asylum", "border", "visa", "immigration", "refugee", "passport"],
    },
    "justice_democracy": {
        "number": 8,
        "title": "Administration of justice and democratic processes",
        "description": "AI systems assisting judicial authorities in fact-finding and law interpretation, or intended to influence election/referendum outcomes.",
        "domains": ["justice", "legal", "democracy", "elections"],
        "keywords": ["justice", "judicial", "court", "legal", "election", "referendum", "voting", "democracy"],
    },
}

TRANSPARENCY_TRIGGERS = {
    "chatbot": {
        "article": "Art. 50(1)",
        "description": "AI system interacting directly with natural persons — must inform users they are interacting with AI",
    },
    "emotion_recognition": {
        "article": "Art. 50(3)",
        "description": "Emotion recognition or biometric categorization system — must inform exposed persons",
    },
    "deepfake": {
        "article": "Art. 50(4)",
        "description": "AI-generated or manipulated content (deepfake) — must disclose artificial generation/manipulation",
    },
    "ai_generated_text": {
        "article": "Art. 50(4)",
        "description": "AI-generated text published to inform public on matters of public interest — must disclose AI generation",
    },
}

# ---------------------------------------------------------------------------
# Provider obligations for high-risk AI systems
# ---------------------------------------------------------------------------

HIGH_RISK_OBLIGATIONS = [
    {
        "id": "risk_management",
        "article": "Art. 9",
        "title": "Risk Management System",
        "description": "Establish, document, and maintain a continuous iterative risk management process throughout the AI system lifecycle.",
        "checklist": [
            "Identify and analyse known and foreseeable risks",
            "Estimate and evaluate risks under intended use and foreseeable misuse",
            "Evaluate risks from post-market monitoring data",
            "Adopt suitable risk management measures",
            "Determine residual risk acceptability",
            "Test system against defined metrics and thresholds",
        ],
    },
    {
        "id": "data_governance",
        "article": "Art. 10",
        "title": "Data and Data Governance",
        "description": "Ensure training, validation, and testing datasets meet quality criteria.",
        "checklist": [
            "Document data collection design choices",
            "Document data preparation processes (annotation, labelling, cleaning)",
            "Document assumptions about data representation",
            "Ensure data sufficiency for intended purpose",
            "Verify data representativeness for target population",
            "Examine datasets for possible biases",
            "Implement bias mitigation measures",
            "Document special category data processing (if applicable)",
        ],
    },
    {
        "id": "technical_documentation",
        "article": "Art. 11",
        "title": "Technical Documentation",
        "description": "Draw up and maintain comprehensive technical documentation before placing on market.",
        "checklist": [
            "Document general system description and intended purpose",
            "Document system elements and development process",
            "Describe monitoring, functioning, and control mechanisms",
            "Include risk management documentation",
            "Include data governance documentation",
            "Document performance metrics including for specific groups",
            "Describe training data or reference its location",
            "Document changes throughout lifecycle",
        ],
    },
    {
        "id": "record_keeping",
        "article": "Art. 12",
        "title": "Record-Keeping / Automatic Logging",
        "description": "Enable automatic recording of events (logs) throughout system lifetime.",
        "checklist": [
            "Implement automatic event logging",
            "Log period of each use (start/end)",
            "Log reference database for input checking",
            "Log input data matches",
            "Log identification of verification personnel",
            "Define log retention period",
        ],
    },
    {
        "id": "transparency",
        "article": "Art. 13",
        "title": "Transparency and Information to Deployers",
        "description": "Design system for sufficient transparency; provide comprehensive instructions for use.",
        "checklist": [
            "Provide instructions for use with system",
            "Include provider identity and contact details",
            "Describe system characteristics, capabilities, limitations",
            "State intended purpose and foreseeable misuse",
            "Declare accuracy, robustness, cybersecurity levels",
            "Document known circumstances creating risks",
            "Document performance for specific groups",
            "Specify input data requirements",
            "Describe human oversight measures",
            "State computational/hardware resource needs",
            "Describe expected lifetime and maintenance",
            "Describe logging mechanism",
        ],
    },
    {
        "id": "human_oversight",
        "article": "Art. 14",
        "title": "Human Oversight",
        "description": "Design system to be effectively overseen by natural persons during use.",
        "checklist": [
            "Define oversight level (in-the-loop / on-the-loop / in-command)",
            "Enable overseers to understand system capacities and limitations",
            "Enable correct interpretation of system output",
            "Enable decision not to use or to disregard/reverse output",
            "Implement intervention/interruption mechanism (stop button)",
            "Implement automation bias safeguards",
        ],
    },
    {
        "id": "accuracy_robustness_cybersecurity",
        "article": "Art. 15",
        "title": "Accuracy, Robustness, and Cybersecurity",
        "description": "Achieve appropriate accuracy levels; ensure robustness and cybersecurity.",
        "checklist": [
            "Achieve and declare accuracy levels for intended purpose",
            "Implement robustness against errors/faults in input",
            "Include redundancy and fail-safe measures",
            "Protect against data poisoning attacks",
            "Protect against adversarial examples",
            "Protect against model manipulation (flipping)",
            "Protect against confidentiality attacks",
            "Ensure security proportionate to risks",
        ],
    },
    {
        "id": "quality_management",
        "article": "Art. 17",
        "title": "Quality Management System",
        "description": "Establish a documented quality management system.",
        "checklist": [
            "Define regulatory compliance strategy",
            "Document design verification/validation techniques",
            "Document development and quality control processes",
            "Document examination, test, and validation procedures",
            "Document technical specifications and standards applied",
            "Implement data management systems and procedures",
            "Integrate risk management system (Art. 9)",
            "Implement post-market monitoring (Art. 72)",
            "Define incident and malfunction reporting procedures",
            "Establish authority/notified body communication procedures",
            "Implement record-keeping procedures",
            "Define resource management including supply-chain measures",
            "Establish accountability framework",
        ],
    },
    {
        "id": "conformity_assessment",
        "article": "Art. 43",
        "title": "Conformity Assessment",
        "description": "Complete conformity assessment before placing on market.",
        "checklist": [
            "Determine assessment path (internal control vs third-party)",
            "Compile all required documentation",
            "Complete assessment procedure (Annex VI or VII)",
            "Sign EU Declaration of Conformity (Art. 47)",
        ],
    },
    {
        "id": "ce_marking",
        "article": "Art. 48",
        "title": "CE Marking",
        "description": "Affix CE marking to indicate conformity.",
        "checklist": [
            "Affix CE marking visibly, legibly, and indelibly",
            "Include notified body number (if applicable)",
            "Ensure marking precedes placing on market",
        ],
    },
    {
        "id": "eu_database",
        "article": "Art. 49",
        "title": "EU Database Registration",
        "description": "Register in the EU database before placing on market.",
        "checklist": [
            "Register provider identity in EU database",
            "Enter system description and intended purpose",
            "Enter conformity assessment status",
            "Enter member states of availability",
            "Document any restrictions on use",
        ],
    },
    {
        "id": "post_market_monitoring",
        "article": "Art. 72",
        "title": "Post-Market Monitoring",
        "description": "Establish and maintain a post-market monitoring system.",
        "checklist": [
            "Establish post-market monitoring system",
            "Define data collection and analysis procedures",
            "Integrate findings into risk management updates",
            "Include post-market monitoring plan in technical documentation",
            "Define serious incident reporting procedures (Art. 73, 15-day deadline)",
            "Analyse interaction with other AI systems",
        ],
    },
]

DEPLOYER_OBLIGATIONS = [
    {
        "id": "use_per_instructions",
        "article": "Art. 26(1)",
        "title": "Use According to Instructions",
        "description": "Operate the system per the provider's instructions for use.",
    },
    {
        "id": "human_oversight_assignment",
        "article": "Art. 26(2)",
        "title": "Human Oversight Assignment",
        "description": "Assign human oversight to competent, trained, and authorized persons.",
    },
    {
        "id": "input_data_relevance",
        "article": "Art. 26(4)",
        "title": "Input Data Relevance",
        "description": "Ensure input data is relevant and sufficiently representative.",
    },
    {
        "id": "monitoring",
        "article": "Art. 26(5)",
        "title": "Monitoring and Incident Reporting",
        "description": "Monitor operation and inform provider of risks or incidents.",
    },
    {
        "id": "log_retention",
        "article": "Art. 26(6)",
        "title": "Log Retention",
        "description": "Keep automatically generated logs for minimum 6 months.",
    },
    {
        "id": "worker_information",
        "article": "Art. 26(7)",
        "title": "Inform Workers",
        "description": "Inform workers and their representatives before system deployment.",
    },
    {
        "id": "dpia",
        "article": "Art. 26(9)",
        "title": "Data Protection Impact Assessment",
        "description": "Carry out DPIA (GDPR Art. 35) when required.",
    },
    {
        "id": "fria",
        "article": "Art. 27",
        "title": "Fundamental Rights Impact Assessment",
        "description": "Public bodies and private entities providing public services must perform FRIA.",
    },
]

GPAI_OBLIGATIONS = [
    {
        "id": "gpai_technical_docs",
        "article": "Art. 53(1)(a)",
        "title": "Technical Documentation",
        "description": "Draw up and maintain technical documentation of the model and training/testing process.",
    },
    {
        "id": "gpai_downstream_info",
        "article": "Art. 53(1)(b)",
        "title": "Information for Downstream Providers",
        "description": "Provide sufficient information for downstream AI system providers to comply with their obligations.",
    },
    {
        "id": "gpai_copyright",
        "article": "Art. 53(1)(c)",
        "title": "Copyright Compliance",
        "description": "Put in place a policy to comply with EU copyright law including opt-out mechanisms.",
    },
    {
        "id": "gpai_training_summary",
        "article": "Art. 53(1)(d)",
        "title": "Training Data Summary",
        "description": "Make publicly available a sufficiently detailed summary of training data content.",
    },
    {
        "id": "gpai_eu_representative",
        "article": "Art. 54",
        "title": "EU Representative (Non-EU Providers)",
        "description": "Appoint an authorised representative established in the EU.",
    },
]

GPAI_SYSTEMIC_RISK_OBLIGATIONS = [
    {
        "id": "systemic_model_evaluation",
        "article": "Art. 55(1)(a)",
        "title": "Model Evaluation",
        "description": "Perform standardized model evaluation including adversarial testing.",
    },
    {
        "id": "systemic_red_teaming",
        "article": "Art. 55(1)(a)",
        "title": "Red-Teaming",
        "description": "Conduct adversarial red-teaming proportionate to risk level.",
    },
    {
        "id": "systemic_risk_assessment",
        "article": "Art. 55(1)(b)",
        "title": "Systemic Risk Assessment and Mitigation",
        "description": "Assess and mitigate possible systemic risks at EU level.",
    },
    {
        "id": "systemic_incident_reporting",
        "article": "Art. 55(1)(c)",
        "title": "Incident Tracking and Reporting",
        "description": "Track, document, and report serious incidents to the AI Office.",
    },
    {
        "id": "systemic_cybersecurity",
        "article": "Art. 55(1)(d)",
        "title": "Cybersecurity Protection",
        "description": "Ensure adequate cybersecurity for the model and physical infrastructure.",
    },
    {
        "id": "systemic_energy_reporting",
        "article": "Art. 55(1)(e)",
        "title": "Energy Consumption Reporting",
        "description": "Report energy consumption and, where feasible, overall energy efficiency.",
    },
]


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

def check_prohibited_practices(system: Dict[str, Any]) -> List[Dict[str, str]]:
    """Check if the AI system engages in any prohibited practices under Art. 5."""
    violations = []

    if system.get("social_scoring"):
        violations.append({
            "practice": "Social scoring",
            "article": "Art. 5(1)(c)",
            "description": "System performs social scoring leading to detrimental treatment.",
            "severity": "PROHIBITED",
        })

    if system.get("uses_biometrics") and system.get("biometric_context") == "real_time_public":
        violations.append({
            "practice": "Real-time remote biometric identification in public spaces",
            "article": "Art. 5(1)(h)",
            "description": "System performs real-time remote biometric identification in publicly accessible spaces.",
            "severity": "PROHIBITED",
        })

    if system.get("biometric_type") == "emotion" and system.get("biometric_context") in ("workplace", "education"):
        violations.append({
            "practice": "Emotion recognition in workplace/education",
            "article": "Art. 5(1)(f)",
            "description": "System performs emotion recognition in workplace or educational context.",
            "severity": "PROHIBITED",
        })

    if system.get("predictive_policing_individual"):
        violations.append({
            "practice": "Individual predictive policing",
            "article": "Art. 5(1)(d)",
            "description": "System performs individual risk assessment for predicting criminal offending based on profiling.",
            "severity": "PROHIBITED",
        })

    if system.get("manipulates_behavior") and system.get("targets_vulnerable_groups"):
        violations.append({
            "practice": "Exploitation of vulnerabilities",
            "article": "Art. 5(1)(b)",
            "description": "System exploits vulnerabilities of specific groups to distort behaviour.",
            "severity": "PROHIBITED",
        })

    if system.get("manipulates_behavior") and not system.get("targets_vulnerable_groups"):
        violations.append({
            "practice": "Potential subliminal manipulation",
            "article": "Art. 5(1)(a)",
            "description": "System may deploy techniques beyond consciousness to materially distort behaviour. Further review needed.",
            "severity": "REVIEW_REQUIRED",
        })

    if system.get("untargeted_scraping"):
        violations.append({
            "practice": "Untargeted facial image scraping",
            "article": "Art. 5(1)(e)",
            "description": "System creates/expands facial recognition databases through untargeted scraping.",
            "severity": "PROHIBITED",
        })

    if system.get("biometric_type") == "categorization_sensitive":
        violations.append({
            "practice": "Biometric categorization by sensitive attributes",
            "article": "Art. 5(1)(g)",
            "description": "System categorizes persons by biometric data to deduce sensitive/protected attributes.",
            "severity": "PROHIBITED",
        })

    return violations


def check_annex_iii(system: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check if the AI system falls under any Annex III high-risk category."""
    matches = []
    domain = system.get("domain", "").lower()
    description = system.get("description", "").lower()
    sub_domain = system.get("sub_domain", "").lower()

    for cat_id, cat in ANNEX_III_CATEGORIES.items():
        matched = False
        match_reason = []

        # Check domain match
        if domain in cat["domains"]:
            matched = True
            match_reason.append(f"Domain '{domain}' matches category")

        # Check keyword match in description
        for kw in cat["keywords"]:
            if kw.lower() in description or kw.lower() in sub_domain:
                matched = True
                match_reason.append(f"Keyword '{kw}' found in description/sub_domain")
                break

        # Special checks
        if cat_id == "biometric_identification" and system.get("uses_biometrics"):
            matched = True
            match_reason.append("System uses biometric identification")

        if cat_id == "critical_infrastructure" and system.get("critical_infrastructure"):
            matched = True
            match_reason.append("System operates on critical infrastructure")

        if matched:
            matches.append({
                "category_number": cat["number"],
                "category_id": cat_id,
                "title": cat["title"],
                "description": cat["description"],
                "match_reasons": match_reason,
            })

    return matches


def check_transparency_obligations(system: Dict[str, Any]) -> List[Dict[str, str]]:
    """Check if Art. 50 transparency obligations apply."""
    obligations = []

    if system.get("interacts_with_persons"):
        obligations.append({
            "type": "chatbot_disclosure",
            "article": "Art. 50(1)",
            "description": "System interacts with persons — must inform users they are interacting with AI.",
        })

    if system.get("biometric_type") == "emotion":
        obligations.append({
            "type": "emotion_recognition_disclosure",
            "article": "Art. 50(3)",
            "description": "Emotion recognition system — must inform exposed persons.",
        })

    if system.get("generates_content"):
        content_type = system.get("content_type", "")
        if content_type in ("deepfake", "image", "video", "audio"):
            obligations.append({
                "type": "deepfake_disclosure",
                "article": "Art. 50(4)",
                "description": f"AI-generated {content_type} content — must disclose artificial generation and apply machine-readable labelling.",
            })
        elif content_type == "text":
            obligations.append({
                "type": "text_disclosure",
                "article": "Art. 50(4)",
                "description": "AI-generated text — must disclose if published on matters of public interest (unless editorially reviewed).",
            })

    return obligations


def check_gpai(system: Dict[str, Any]) -> Dict[str, Any]:
    """Check GPAI model obligations."""
    result = {"is_gpai": False, "is_systemic_risk": False, "obligations": []}

    if not system.get("is_gpai"):
        return result

    result["is_gpai"] = True
    result["obligations"] = list(GPAI_OBLIGATIONS)

    flops = system.get("training_compute_flops", 0)
    if flops and flops >= 1e25:
        result["is_systemic_risk"] = True
        result["systemic_risk_reason"] = f"Training compute ({flops:.1e} FLOPs) exceeds 10^25 threshold"
        result["obligations"].extend(GPAI_SYSTEMIC_RISK_OBLIGATIONS)

    return result


def classify_system(system: Dict[str, Any]) -> Dict[str, Any]:
    """Classify an AI system under the EU AI Act risk framework."""
    result = {
        "system_name": system.get("name", "Unknown"),
        "classification_date": datetime.now().strftime("%Y-%m-%d"),
        "risk_level": None,
        "prohibited_practices": [],
        "high_risk_categories": [],
        "transparency_obligations": [],
        "gpai_assessment": {"is_gpai": False, "is_systemic_risk": False},
        "applicable_obligations": [],
        "compliance_checklist": [],
        "regulatory_references": [],
        "warnings": [],
        "recommendations": [],
    }

    # Check EU deployment scope
    if not system.get("eu_deployment", True):
        result["warnings"].append(
            "System is not deployed in the EU. However, the AI Act has extraterritorial reach — "
            "if the AI system's output is used in the EU, the regulation may still apply (Art. 2(1)(c))."
        )

    # Step 1: Check prohibited practices
    prohibited = check_prohibited_practices(system)
    result["prohibited_practices"] = prohibited
    hard_prohibitions = [p for p in prohibited if p["severity"] == "PROHIBITED"]

    if hard_prohibitions:
        result["risk_level"] = "UNACCEPTABLE"
        result["regulatory_references"].append("Art. 5 — Prohibited AI Practices")
        result["recommendations"].append(
            "CRITICAL: This AI system engages in prohibited practices. It MUST be discontinued "
            "immediately. Prohibited AI practices have been enforceable since 2 February 2025. "
            "Penalties: up to EUR 35 million or 7% of global annual turnover."
        )
        # Still continue analysis to provide full picture

    # Step 2: Check Annex III high-risk categories
    annex_iii_matches = check_annex_iii(system)
    result["high_risk_categories"] = annex_iii_matches

    if annex_iii_matches and result["risk_level"] != "UNACCEPTABLE":
        result["risk_level"] = "HIGH"
        result["regulatory_references"].append("Art. 6(2) — High-risk AI systems per Annex III")
        for cat in annex_iii_matches:
            result["regulatory_references"].append(
                f"Annex III, point {cat['category_number']} — {cat['title']}"
            )

    # Check safety component path
    if system.get("is_safety_component"):
        if result["risk_level"] != "UNACCEPTABLE":
            result["risk_level"] = "HIGH"
        product = system.get("product_legislation", "unspecified")
        result["regulatory_references"].append(
            f"Art. 6(1) — Safety component of product under Annex I legislation ({product})"
        )
        result["warnings"].append(
            f"System is a safety component of a product under EU harmonisation legislation ({product}). "
            "Third-party conformity assessment may be required under the applicable product legislation."
        )

    # Step 3: Check transparency obligations
    transparency = check_transparency_obligations(system)
    result["transparency_obligations"] = transparency

    if transparency and result["risk_level"] is None:
        result["risk_level"] = "LIMITED"
        result["regulatory_references"].append("Art. 50 — Transparency obligations")

    # Step 4: GPAI assessment
    gpai = check_gpai(system)
    result["gpai_assessment"] = gpai

    if gpai["is_gpai"]:
        result["regulatory_references"].append("Chapter V — General-Purpose AI Models")
        if gpai["is_systemic_risk"]:
            result["regulatory_references"].append("Art. 51 — Classification of GPAI with systemic risk")
            result["regulatory_references"].append("Art. 55 — Obligations for systemic risk GPAI")

    # Step 5: Default to minimal if no other classification
    if result["risk_level"] is None:
        result["risk_level"] = "MINIMAL"
        result["regulatory_references"].append("Art. 95 — Voluntary codes of conduct")
        result["recommendations"].append(
            "System is classified as minimal risk. No mandatory requirements apply, "
            "but voluntary adherence to codes of conduct is encouraged (Art. 95)."
        )

    # Step 6: Build applicable obligations and checklist
    if result["risk_level"] in ("HIGH", "UNACCEPTABLE"):
        result["applicable_obligations"] = [
            {"id": o["id"], "article": o["article"], "title": o["title"], "description": o["description"]}
            for o in HIGH_RISK_OBLIGATIONS
        ]
        for obligation in HIGH_RISK_OBLIGATIONS:
            for item in obligation["checklist"]:
                result["compliance_checklist"].append({
                    "obligation": obligation["title"],
                    "article": obligation["article"],
                    "item": item,
                    "status": "NOT_ASSESSED",
                })

    if result["risk_level"] == "HIGH":
        result["applicable_obligations"].extend([
            {"id": o["id"], "article": o["article"], "title": o["title"], "description": o["description"]}
            for o in DEPLOYER_OBLIGATIONS
        ])

    if gpai["is_gpai"]:
        result["applicable_obligations"].extend([
            {"id": o["id"], "article": o["article"], "title": o["title"], "description": o["description"]}
            for o in gpai["obligations"]
        ])

    # Transparency obligations are additive
    if transparency:
        for t in transparency:
            result["applicable_obligations"].append({
                "id": t["type"],
                "article": t["article"],
                "title": t["type"].replace("_", " ").title(),
                "description": t["description"],
            })

    # Step 7: Add timeline recommendations
    _add_timeline_recommendations(result)

    return result


def _add_timeline_recommendations(result: Dict[str, Any]) -> None:
    """Add implementation timeline recommendations."""
    if result["risk_level"] == "UNACCEPTABLE":
        result["recommendations"].append(
            "DEADLINE PASSED: Prohibited practices have been enforceable since 2 February 2025. "
            "Immediate action required."
        )
    elif result["risk_level"] == "HIGH":
        result["recommendations"].append(
            "DEADLINE: Full high-risk AI obligations apply from 2 August 2026. "
            "For safety components of Annex I Section B products, the deadline extends to 2 August 2027."
        )
        result["recommendations"].append(
            "ACTION: Begin compliance program immediately. Key areas: risk management system, "
            "data governance, technical documentation, human oversight design, and conformity assessment preparation."
        )
    elif result["risk_level"] == "LIMITED":
        result["recommendations"].append(
            "DEADLINE: Transparency obligations apply from 2 August 2026. "
            "Implement disclosure mechanisms for AI interaction, content generation, or emotion recognition."
        )

    gpai = result.get("gpai_assessment", {})
    if gpai.get("is_gpai"):
        result["recommendations"].append(
            "DEADLINE: GPAI obligations apply from 2 August 2025. "
            "Prepare technical documentation, training data summary, and copyright compliance policy."
        )
        if gpai.get("is_systemic_risk"):
            result["recommendations"].append(
                "SYSTEMIC RISK: Additional obligations apply — model evaluation, red-teaming, "
                "systemic risk assessment, incident reporting, and cybersecurity. Engage with AI Office."
            )


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_text_report(result: Dict[str, Any]) -> str:
    """Format classification result as a human-readable report."""
    lines = []
    lines.append("=" * 72)
    lines.append("EU AI ACT RISK CLASSIFICATION REPORT")
    lines.append("Regulation (EU) 2024/1689")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"System:              {result['system_name']}")
    lines.append(f"Classification Date: {result['classification_date']}")
    lines.append(f"Risk Level:          {result['risk_level']}")
    lines.append("")

    # Warnings
    if result["warnings"]:
        lines.append("-" * 72)
        lines.append("WARNINGS")
        lines.append("-" * 72)
        for w in result["warnings"]:
            lines.append(f"  [!] {w}")
        lines.append("")

    # Prohibited practices
    if result["prohibited_practices"]:
        lines.append("-" * 72)
        lines.append("PROHIBITED PRACTICES DETECTED")
        lines.append("-" * 72)
        for p in result["prohibited_practices"]:
            severity_marker = "PROHIBITED" if p["severity"] == "PROHIBITED" else "REVIEW NEEDED"
            lines.append(f"  [{severity_marker}] {p['practice']}")
            lines.append(f"    Article: {p['article']}")
            lines.append(f"    Detail:  {p['description']}")
            lines.append("")

    # High-risk categories
    if result["high_risk_categories"]:
        lines.append("-" * 72)
        lines.append("HIGH-RISK CATEGORIES (Annex III)")
        lines.append("-" * 72)
        for cat in result["high_risk_categories"]:
            lines.append(f"  [{cat['category_number']}] {cat['title']}")
            lines.append(f"      {cat['description']}")
            lines.append(f"      Match reasons: {', '.join(cat['match_reasons'])}")
            lines.append("")

    # Transparency obligations
    if result["transparency_obligations"]:
        lines.append("-" * 72)
        lines.append("TRANSPARENCY OBLIGATIONS (Art. 50)")
        lines.append("-" * 72)
        for t in result["transparency_obligations"]:
            lines.append(f"  [{t['article']}] {t['description']}")
        lines.append("")

    # GPAI assessment
    gpai = result.get("gpai_assessment", {})
    if gpai.get("is_gpai"):
        lines.append("-" * 72)
        lines.append("GENERAL-PURPOSE AI MODEL (GPAI)")
        lines.append("-" * 72)
        lines.append(f"  GPAI Model:     Yes")
        lines.append(f"  Systemic Risk:  {'Yes' if gpai.get('is_systemic_risk') else 'No'}")
        if gpai.get("systemic_risk_reason"):
            lines.append(f"  Reason:         {gpai['systemic_risk_reason']}")
        lines.append("")

    # Applicable obligations
    if result["applicable_obligations"]:
        lines.append("-" * 72)
        lines.append("APPLICABLE OBLIGATIONS")
        lines.append("-" * 72)
        for i, o in enumerate(result["applicable_obligations"], 1):
            lines.append(f"  {i:2d}. [{o['article']}] {o['title']}")
            lines.append(f"      {o['description']}")
        lines.append("")

    # Compliance checklist
    if result["compliance_checklist"]:
        lines.append("-" * 72)
        lines.append("COMPLIANCE CHECKLIST")
        lines.append("-" * 72)
        current_obligation = None
        for item in result["compliance_checklist"]:
            if item["obligation"] != current_obligation:
                current_obligation = item["obligation"]
                lines.append(f"\n  {current_obligation} ({item['article']})")
            lines.append(f"    [ ] {item['item']}")
        lines.append("")

    # Regulatory references
    if result["regulatory_references"]:
        lines.append("-" * 72)
        lines.append("REGULATORY REFERENCES")
        lines.append("-" * 72)
        for ref in result["regulatory_references"]:
            lines.append(f"  - {ref}")
        lines.append("")

    # Recommendations
    if result["recommendations"]:
        lines.append("-" * 72)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 72)
        for r in result["recommendations"]:
            lines.append(f"  > {r}")
            lines.append("")

    lines.append("=" * 72)
    lines.append("End of Report")
    lines.append("=" * 72)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EU AI Act Risk Classifier — Classify AI systems under Regulation (EU) 2024/1689",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input system.json
  %(prog)s --input system.json --json
  %(prog)s --input system.json --output report.json
  %(prog)s --inline '{"name": "Resume Screener", "domain": "employment", "description": "screens job applications"}'
        """,
    )
    parser.add_argument("--input", "-i", help="Path to JSON file describing the AI system")
    parser.add_argument("--inline", help="Inline JSON string describing the AI system")
    parser.add_argument("--output", "-o", help="Path to write output report (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    if not args.input and not args.inline:
        parser.error("Either --input or --inline is required")

    # Load system description
    if args.inline:
        try:
            system = json.loads(args.inline)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid inline JSON — {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                system = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found — {args.input}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {args.input} — {e}", file=sys.stderr)
            sys.exit(1)

    # Classify
    result = classify_system(system)

    # Output
    if args.json:
        output = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        output = format_text_report(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
