#!/usr/bin/env python3
"""
EU AI Act Compliance Checker

Validates AI system compliance status against all provider and deployer
obligations under Regulation (EU) 2024/1689. Generates gap analysis with
remediation steps and scores overall compliance readiness (0-100).

Usage:
    python ai_compliance_checker.py --input compliance_status.json
    python ai_compliance_checker.py --input compliance_status.json --json
    python ai_compliance_checker.py --input compliance_status.json --role deployer
    python ai_compliance_checker.py --input compliance_status.json --output report.json

Input JSON schema:
{
    "system_name": "AI System Name",
    "risk_level": "HIGH",
    "role": "provider",
    "is_gpai": false,
    "is_systemic_risk": false,
    "is_public_body": false,
    "risk_management": {
        "process_established": true,
        "risks_identified": true,
        "risks_evaluated": true,
        "measures_adopted": true,
        "residual_risk_acceptable": true,
        "testing_performed": true,
        "lifecycle_coverage": true
    },
    "data_governance": {
        "design_choices_documented": true,
        "preparation_documented": true,
        "assumptions_documented": true,
        "data_sufficient": true,
        "data_representative": true,
        "bias_examined": true,
        "bias_mitigated": true,
        "special_categories_handled": true
    },
    "technical_documentation": {
        "system_description": true,
        "development_process": true,
        "monitoring_description": true,
        "risk_management_docs": true,
        "data_governance_docs": true,
        "performance_metrics": true,
        "training_data_info": true,
        "lifecycle_changes": true,
        "kept_up_to_date": true
    },
    "record_keeping": {
        "automatic_logging": true,
        "usage_period_logged": true,
        "reference_db_logged": true,
        "input_matches_logged": true,
        "verification_persons_logged": true,
        "retention_period_defined": true
    },
    "transparency": {
        "instructions_provided": true,
        "provider_identity": true,
        "capabilities_limitations": true,
        "intended_purpose_stated": true,
        "accuracy_levels_declared": true,
        "risk_circumstances_documented": true,
        "group_performance_documented": true,
        "input_specs_provided": true,
        "oversight_measures_described": true,
        "resource_needs_stated": true,
        "lifetime_maintenance_described": true,
        "logging_mechanism_described": true
    },
    "human_oversight": {
        "oversight_level_defined": true,
        "understand_capacities": true,
        "interpret_output": true,
        "can_disregard_output": true,
        "intervention_mechanism": true,
        "automation_bias_safeguards": true
    },
    "accuracy_robustness_cybersecurity": {
        "accuracy_levels_achieved": true,
        "robustness_ensured": true,
        "redundancy_failsafe": true,
        "data_poisoning_protection": true,
        "adversarial_protection": true,
        "model_manipulation_protection": true,
        "confidentiality_protection": true,
        "security_proportionate": true
    },
    "quality_management": {
        "compliance_strategy": true,
        "design_verification": true,
        "development_processes": true,
        "test_procedures": true,
        "standards_documented": true,
        "data_management_systems": true,
        "risk_management_integrated": true,
        "post_market_monitoring": true,
        "incident_reporting_procedures": true,
        "authority_communication": true,
        "record_keeping_procedures": true,
        "resource_management": true,
        "accountability_framework": true
    },
    "conformity_assessment": {
        "path_determined": true,
        "documentation_compiled": true,
        "assessment_completed": true,
        "declaration_signed": true
    },
    "ce_marking": {
        "marking_affixed": true,
        "notified_body_number": true,
        "precedes_market_placement": true
    },
    "eu_database": {
        "provider_registered": true,
        "system_description_entered": true,
        "conformity_status_entered": true,
        "member_states_entered": true,
        "restrictions_documented": true
    },
    "post_market_monitoring": {
        "system_established": true,
        "data_collection_defined": true,
        "risk_management_updated": true,
        "plan_in_documentation": true,
        "incident_reporting_defined": true,
        "interaction_analysis": true
    },
    "deployer": {
        "use_per_instructions": true,
        "human_oversight_assigned": true,
        "input_data_relevant": true,
        "monitoring_active": true,
        "logs_retained": true,
        "workers_informed": true,
        "dpia_completed": true,
        "fria_completed": true,
        "incidents_reported": true
    },
    "gpai": {
        "technical_docs": true,
        "downstream_info": true,
        "copyright_policy": true,
        "training_summary_public": true,
        "eu_representative": true
    },
    "gpai_systemic": {
        "model_evaluation": true,
        "red_teaming": true,
        "risk_assessment": true,
        "incident_tracking": true,
        "cybersecurity": true,
        "energy_reporting": true
    }
}
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Obligation definitions with weights and remediation guidance
# ---------------------------------------------------------------------------

PROVIDER_OBLIGATION_SECTIONS = {
    "risk_management": {
        "article": "Art. 9",
        "title": "Risk Management System",
        "weight": 12,
        "deadline": "2 Aug 2026",
        "fields": {
            "process_established": {
                "label": "Continuous iterative risk management process established",
                "remediation": "Establish a documented risk management process that operates throughout the AI system lifecycle. Define risk identification, evaluation, and control procedures. Assign a risk management owner.",
                "priority": "HIGH",
            },
            "risks_identified": {
                "label": "Known and foreseeable risks identified and analysed",
                "remediation": "Conduct a comprehensive risk identification workshop covering health, safety, and fundamental rights risks. Use structured techniques (FMEA, HAZOP, fault tree analysis).",
                "priority": "HIGH",
            },
            "risks_evaluated": {
                "label": "Risks estimated and evaluated for intended use and foreseeable misuse",
                "remediation": "Evaluate each risk for likelihood and severity under both intended use and reasonably foreseeable misuse scenarios. Document evaluation criteria and results.",
                "priority": "HIGH",
            },
            "measures_adopted": {
                "label": "Suitable risk management measures adopted",
                "remediation": "Define and implement risk control measures for each identified risk. Prioritize elimination, then reduction, then protective measures. Document rationale for each measure.",
                "priority": "HIGH",
            },
            "residual_risk_acceptable": {
                "label": "Residual risk determined acceptable",
                "remediation": "Assess residual risk after control measures. Document acceptability criteria, the risk-benefit analysis, and the basis for determining residual risks are acceptable.",
                "priority": "HIGH",
            },
            "testing_performed": {
                "label": "System tested against defined metrics and thresholds",
                "remediation": "Define quantitative performance metrics and acceptable thresholds. Test the system against these before deployment and periodically throughout lifecycle.",
                "priority": "MEDIUM",
            },
            "lifecycle_coverage": {
                "label": "Risk management covers full system lifecycle",
                "remediation": "Ensure the risk management process extends from design through development, deployment, operation, and decommissioning. Include post-market monitoring feedback loops.",
                "priority": "MEDIUM",
            },
        },
    },
    "data_governance": {
        "article": "Art. 10",
        "title": "Data and Data Governance",
        "weight": 11,
        "deadline": "2 Aug 2026",
        "fields": {
            "design_choices_documented": {
                "label": "Data collection design choices documented",
                "remediation": "Document the rationale for data collection methods, sources selected, volume targets, and labelling strategies. Include what data was excluded and why.",
                "priority": "HIGH",
            },
            "preparation_documented": {
                "label": "Data preparation processes documented (annotation, labelling, cleaning)",
                "remediation": "Create detailed documentation of all data preparation steps: annotation guidelines, labelling protocols, cleaning rules, enrichment processes, and quality checks applied.",
                "priority": "HIGH",
            },
            "assumptions_documented": {
                "label": "Assumptions about data representation documented",
                "remediation": "Document what the data is meant to measure and represent. State assumptions about the relationship between training data and the real-world population/use case.",
                "priority": "MEDIUM",
            },
            "data_sufficient": {
                "label": "Data volume sufficient for intended purpose",
                "remediation": "Assess whether the quantity of training, validation, and testing data is adequate. Document the analysis and any limitations due to data scarcity.",
                "priority": "MEDIUM",
            },
            "data_representative": {
                "label": "Data representative of target population",
                "remediation": "Analyse whether the dataset demographics and characteristics match the intended deployment population. Address any underrepresentation gaps.",
                "priority": "HIGH",
            },
            "bias_examined": {
                "label": "Datasets examined for possible biases",
                "remediation": "Conduct systematic bias examination across protected attributes (age, gender, ethnicity, disability). Use statistical tests and the ai_bias_detector.py tool.",
                "priority": "HIGH",
            },
            "bias_mitigated": {
                "label": "Bias mitigation measures implemented",
                "remediation": "Implement appropriate bias mitigation strategies: data augmentation, re-sampling, re-weighting, or algorithmic fairness constraints. Document measures and their effectiveness.",
                "priority": "HIGH",
            },
            "special_categories_handled": {
                "label": "Special category data processing handled appropriately",
                "remediation": "If processing special category data (Art. 9 GDPR) for bias detection/correction, ensure strict necessity is documented and appropriate safeguards (encryption, access controls, purpose limitation) are in place.",
                "priority": "MEDIUM",
            },
        },
    },
    "technical_documentation": {
        "article": "Art. 11",
        "title": "Technical Documentation",
        "weight": 10,
        "deadline": "2 Aug 2026",
        "fields": {
            "system_description": {
                "label": "General system description and intended purpose documented",
                "remediation": "Create a comprehensive system description covering: model architecture, input/output modalities, intended purpose, target users, affected persons, and deployment context.",
                "priority": "HIGH",
            },
            "development_process": {
                "label": "Development process and system elements described",
                "remediation": "Document the system design, development methodology, component architecture, training procedures, and validation approach. Include version history.",
                "priority": "HIGH",
            },
            "monitoring_description": {
                "label": "Monitoring, functioning, and control mechanisms described",
                "remediation": "Document how the system is monitored in operation, how it functions (decision logic), and what control mechanisms exist for operators.",
                "priority": "MEDIUM",
            },
            "risk_management_docs": {
                "label": "Risk management documentation included",
                "remediation": "Include or reference the complete risk management system documentation (Art. 9) within the technical file.",
                "priority": "HIGH",
            },
            "data_governance_docs": {
                "label": "Data governance documentation included",
                "remediation": "Include or reference the complete data governance documentation (Art. 10) within the technical file.",
                "priority": "HIGH",
            },
            "performance_metrics": {
                "label": "Performance metrics documented, including for specific groups",
                "remediation": "Document all performance metrics (accuracy, precision, recall, F1, etc.) with breakdowns by relevant demographic groups and deployment contexts.",
                "priority": "HIGH",
            },
            "training_data_info": {
                "label": "Training data information included or referenced",
                "remediation": "Include a description of training datasets or reference where this information is maintained. Cover data sources, volumes, characteristics, and provenance.",
                "priority": "MEDIUM",
            },
            "lifecycle_changes": {
                "label": "Lifecycle changes documented",
                "remediation": "Establish a change log documenting all significant changes to the system throughout its lifecycle, including model updates, data refreshes, and configuration changes.",
                "priority": "MEDIUM",
            },
            "kept_up_to_date": {
                "label": "Technical documentation kept up to date",
                "remediation": "Implement a process to review and update technical documentation at defined intervals and after any significant change to the system.",
                "priority": "MEDIUM",
            },
        },
    },
    "record_keeping": {
        "article": "Art. 12",
        "title": "Record-Keeping / Automatic Logging",
        "weight": 7,
        "deadline": "2 Aug 2026",
        "fields": {
            "automatic_logging": {
                "label": "Automatic event logging implemented",
                "remediation": "Implement automated logging infrastructure that records system events, decisions, inputs, and outputs throughout the system's operation.",
                "priority": "HIGH",
            },
            "usage_period_logged": {
                "label": "Usage period (start/end) logged for each use",
                "remediation": "Ensure logs capture the start and end timestamp of each usage session or inference request.",
                "priority": "MEDIUM",
            },
            "reference_db_logged": {
                "label": "Reference database for input checking logged",
                "remediation": "Log the version or state of any reference database used for input validation or matching during each operation.",
                "priority": "MEDIUM",
            },
            "input_matches_logged": {
                "label": "Input data matches logged",
                "remediation": "Log cases where input data matched entries in a reference database, including the specific match results.",
                "priority": "MEDIUM",
            },
            "verification_persons_logged": {
                "label": "Verification personnel identified in logs",
                "remediation": "Log the identity of natural persons involved in reviewing or verifying system outputs.",
                "priority": "MEDIUM",
            },
            "retention_period_defined": {
                "label": "Log retention period defined and implemented",
                "remediation": "Define a log retention period appropriate to the system's intended purpose. Ensure minimum compliance with EU/national law requirements. Implement automated retention management.",
                "priority": "HIGH",
            },
        },
    },
    "transparency": {
        "article": "Art. 13",
        "title": "Transparency and Information to Deployers",
        "weight": 9,
        "deadline": "2 Aug 2026",
        "fields": {
            "instructions_provided": {
                "label": "Instructions for use provided with the system",
                "remediation": "Create comprehensive instructions for use covering all items required by Art. 13. Package with the system delivery.",
                "priority": "HIGH",
            },
            "provider_identity": {
                "label": "Provider identity and contact details included",
                "remediation": "Include the provider's legal name, registered address, and contact information in the instructions for use.",
                "priority": "LOW",
            },
            "capabilities_limitations": {
                "label": "System characteristics, capabilities, and limitations described",
                "remediation": "Document what the system can and cannot do. Include known edge cases, failure modes, and conditions where performance degrades.",
                "priority": "HIGH",
            },
            "intended_purpose_stated": {
                "label": "Intended purpose and foreseeable misuse stated",
                "remediation": "Clearly state the intended purpose and explicitly describe foreseeable misuse scenarios with warnings against them.",
                "priority": "HIGH",
            },
            "accuracy_levels_declared": {
                "label": "Accuracy, robustness, and cybersecurity levels declared",
                "remediation": "Quantify and declare the system's tested accuracy levels, robustness characteristics, and cybersecurity posture in the instructions for use.",
                "priority": "HIGH",
            },
            "risk_circumstances_documented": {
                "label": "Known risk circumstances documented",
                "remediation": "Document all known or foreseeable circumstances that may create risks to health, safety, or fundamental rights.",
                "priority": "MEDIUM",
            },
            "group_performance_documented": {
                "label": "Performance for specific groups documented",
                "remediation": "Document performance metrics disaggregated by relevant demographic groups (age, gender, ethnicity, etc.) the system will affect.",
                "priority": "HIGH",
            },
            "input_specs_provided": {
                "label": "Input data specifications provided",
                "remediation": "Document the specifications for input data: format, quality requirements, constraints, and any pre-processing requirements.",
                "priority": "MEDIUM",
            },
            "oversight_measures_described": {
                "label": "Human oversight measures described",
                "remediation": "Describe the human oversight mechanisms available and how deployers should implement effective oversight.",
                "priority": "HIGH",
            },
            "resource_needs_stated": {
                "label": "Computational and hardware resource needs stated",
                "remediation": "Document the computational and hardware requirements for operating the system, including minimum and recommended specifications.",
                "priority": "LOW",
            },
            "lifetime_maintenance_described": {
                "label": "Expected lifetime and maintenance described",
                "remediation": "State the expected operational lifetime and describe maintenance, update, and support procedures.",
                "priority": "LOW",
            },
            "logging_mechanism_described": {
                "label": "Logging mechanism described in instructions",
                "remediation": "Describe the automatic logging mechanism (Art. 12) in the instructions for use so deployers understand what is logged and how to access logs.",
                "priority": "MEDIUM",
            },
        },
    },
    "human_oversight": {
        "article": "Art. 14",
        "title": "Human Oversight",
        "weight": 10,
        "deadline": "2 Aug 2026",
        "fields": {
            "oversight_level_defined": {
                "label": "Oversight level defined (in-the-loop / on-the-loop / in-command)",
                "remediation": "Define the appropriate oversight level based on the risk profile and decision impact. Document the rationale for the chosen level.",
                "priority": "HIGH",
            },
            "understand_capacities": {
                "label": "Overseers can understand system capacities and limitations",
                "remediation": "Provide training materials and documentation that enable oversight personnel to fully understand the system's capabilities, limitations, and typical failure modes.",
                "priority": "HIGH",
            },
            "interpret_output": {
                "label": "Overseers can correctly interpret system output",
                "remediation": "Design output interfaces that are interpretable. Provide guidance on how to read and evaluate system outputs, including confidence scores and uncertainty indicators.",
                "priority": "HIGH",
            },
            "can_disregard_output": {
                "label": "Overseers can disregard or reverse system output",
                "remediation": "Implement clear mechanisms allowing oversight personnel to override, disregard, or reverse any system decision or recommendation.",
                "priority": "HIGH",
            },
            "intervention_mechanism": {
                "label": "Intervention/interruption mechanism (stop button) implemented",
                "remediation": "Implement a readily accessible mechanism to interrupt or stop the system's operation. Test that it functions reliably under all operating conditions.",
                "priority": "HIGH",
            },
            "automation_bias_safeguards": {
                "label": "Automation bias safeguards implemented",
                "remediation": "Implement safeguards against over-reliance on AI output: mandatory review steps, randomized verification, confidence thresholds requiring human judgment, and regular calibration exercises.",
                "priority": "HIGH",
            },
        },
    },
    "accuracy_robustness_cybersecurity": {
        "article": "Art. 15",
        "title": "Accuracy, Robustness, and Cybersecurity",
        "weight": 9,
        "deadline": "2 Aug 2026",
        "fields": {
            "accuracy_levels_achieved": {
                "label": "Appropriate accuracy levels achieved and declared",
                "remediation": "Establish accuracy benchmarks appropriate for the intended purpose. Test against these benchmarks and declare results in instructions for use.",
                "priority": "HIGH",
            },
            "robustness_ensured": {
                "label": "Robustness against errors/faults ensured",
                "remediation": "Test system resilience to input errors, noisy data, missing values, and unexpected inputs. Document robustness characteristics.",
                "priority": "HIGH",
            },
            "redundancy_failsafe": {
                "label": "Redundancy and fail-safe measures in place",
                "remediation": "Implement redundancy for critical components and fail-safe mechanisms that default to a safe state when errors occur.",
                "priority": "MEDIUM",
            },
            "data_poisoning_protection": {
                "label": "Protection against data poisoning attacks",
                "remediation": "Implement data integrity validation, anomaly detection in training pipelines, and input sanitization to protect against data poisoning.",
                "priority": "HIGH",
            },
            "adversarial_protection": {
                "label": "Protection against adversarial examples",
                "remediation": "Test for adversarial vulnerabilities. Implement adversarial training, input validation, and detection mechanisms as appropriate.",
                "priority": "HIGH",
            },
            "model_manipulation_protection": {
                "label": "Protection against model manipulation (flipping)",
                "remediation": "Implement model integrity verification, secure model storage, and access controls to prevent unauthorised model modifications.",
                "priority": "MEDIUM",
            },
            "confidentiality_protection": {
                "label": "Protection against confidentiality attacks",
                "remediation": "Protect against model inversion, membership inference, and data extraction attacks. Implement differential privacy or other privacy-preserving techniques where appropriate.",
                "priority": "MEDIUM",
            },
            "security_proportionate": {
                "label": "Security measures proportionate to risks",
                "remediation": "Conduct a cybersecurity risk assessment specific to the AI system. Ensure security measures are proportionate to the identified risks.",
                "priority": "MEDIUM",
            },
        },
    },
    "quality_management": {
        "article": "Art. 17",
        "title": "Quality Management System",
        "weight": 8,
        "deadline": "2 Aug 2026",
        "fields": {
            "compliance_strategy": {
                "label": "Regulatory compliance strategy defined",
                "remediation": "Document a strategy for achieving and maintaining compliance with the AI Act, including roles, responsibilities, timelines, and resource allocation.",
                "priority": "HIGH",
            },
            "design_verification": {
                "label": "Design verification/validation techniques documented",
                "remediation": "Document the verification and validation techniques used to confirm the system meets its design specifications and intended purpose.",
                "priority": "MEDIUM",
            },
            "development_processes": {
                "label": "Development, QC, and QA processes documented",
                "remediation": "Document all development, quality control, and quality assurance processes including code review, testing protocols, and release management.",
                "priority": "MEDIUM",
            },
            "test_procedures": {
                "label": "Examination, test, and validation procedures documented",
                "remediation": "Document pre-development, during-development, and post-development testing and validation procedures.",
                "priority": "MEDIUM",
            },
            "standards_documented": {
                "label": "Technical specifications and standards applied documented",
                "remediation": "List all technical standards, harmonised standards, and common specifications applied in system development and operation.",
                "priority": "LOW",
            },
            "data_management_systems": {
                "label": "Data management systems and procedures in place",
                "remediation": "Implement documented data management systems covering collection, analysis, labelling, storage, filtration, aggregation, retention, and disposal.",
                "priority": "MEDIUM",
            },
            "risk_management_integrated": {
                "label": "Risk management system (Art. 9) integrated into QMS",
                "remediation": "Ensure the AI risk management system is formally integrated into the broader QMS, with clear interfaces and feedback loops.",
                "priority": "HIGH",
            },
            "post_market_monitoring": {
                "label": "Post-market monitoring (Art. 72) integrated into QMS",
                "remediation": "Integrate post-market monitoring processes into the QMS with defined data flows, triggers for corrective action, and management review.",
                "priority": "HIGH",
            },
            "incident_reporting_procedures": {
                "label": "Incident and malfunction reporting procedures defined",
                "remediation": "Define procedures for identifying, documenting, and reporting incidents and malfunctions, including the 15-day serious incident reporting deadline.",
                "priority": "HIGH",
            },
            "authority_communication": {
                "label": "Authority and notified body communication procedures defined",
                "remediation": "Establish procedures for communicating with market surveillance authorities and notified bodies, including designated contacts and response timelines.",
                "priority": "LOW",
            },
            "record_keeping_procedures": {
                "label": "Record-keeping procedures defined",
                "remediation": "Define procedures for creating, maintaining, and retaining QMS records including retention periods and access controls.",
                "priority": "LOW",
            },
            "resource_management": {
                "label": "Resource management including supply-chain measures defined",
                "remediation": "Document resource management practices including personnel competency requirements, infrastructure needs, and supply-chain due diligence for AI components.",
                "priority": "MEDIUM",
            },
            "accountability_framework": {
                "label": "Accountability framework established",
                "remediation": "Establish a clear accountability framework with defined roles, responsibilities, and reporting lines for AI Act compliance.",
                "priority": "HIGH",
            },
        },
    },
    "conformity_assessment": {
        "article": "Art. 43",
        "title": "Conformity Assessment",
        "weight": 8,
        "deadline": "2 Aug 2026",
        "fields": {
            "path_determined": {
                "label": "Assessment path determined (internal control vs third-party)",
                "remediation": "Determine whether internal control (Annex VI) or third-party assessment (Annex VII) is required based on the system category and applicable harmonised standards.",
                "priority": "HIGH",
            },
            "documentation_compiled": {
                "label": "All required documentation compiled",
                "remediation": "Compile the complete technical file including all documentation required for the chosen conformity assessment path.",
                "priority": "HIGH",
            },
            "assessment_completed": {
                "label": "Assessment procedure completed (Annex VI or VII)",
                "remediation": "Complete the full conformity assessment procedure. For internal control: self-assess all requirements. For third-party: engage notified body and complete review.",
                "priority": "HIGH",
            },
            "declaration_signed": {
                "label": "EU Declaration of Conformity signed (Art. 47)",
                "remediation": "Prepare and sign the EU Declaration of Conformity containing all required information per Art. 47. Keep available for 10 years after system is placed on market.",
                "priority": "HIGH",
            },
        },
    },
    "ce_marking": {
        "article": "Art. 48",
        "title": "CE Marking",
        "weight": 4,
        "deadline": "2 Aug 2026",
        "fields": {
            "marking_affixed": {
                "label": "CE marking affixed visibly, legibly, and indelibly",
                "remediation": "Affix the CE marking to the AI system, its packaging, or accompanying documentation in a visible, legible, and indelible manner.",
                "priority": "HIGH",
            },
            "notified_body_number": {
                "label": "Notified body identification number included (if applicable)",
                "remediation": "If a notified body was involved in conformity assessment, include its identification number alongside the CE marking.",
                "priority": "MEDIUM",
            },
            "precedes_market_placement": {
                "label": "CE marking precedes placing on market",
                "remediation": "Ensure CE marking is applied before the system is placed on the market or put into service.",
                "priority": "HIGH",
            },
        },
    },
    "eu_database": {
        "article": "Art. 49",
        "title": "EU Database Registration",
        "weight": 5,
        "deadline": "2 Aug 2026",
        "fields": {
            "provider_registered": {
                "label": "Provider registered in EU database",
                "remediation": "Register the provider entity in the EU AI database established under Art. 71.",
                "priority": "HIGH",
            },
            "system_description_entered": {
                "label": "System description and intended purpose entered",
                "remediation": "Enter a description of the AI system and its intended purpose in the EU database.",
                "priority": "HIGH",
            },
            "conformity_status_entered": {
                "label": "Conformity assessment status entered",
                "remediation": "Enter the conformity assessment status and any relevant certificate numbers.",
                "priority": "MEDIUM",
            },
            "member_states_entered": {
                "label": "Member states of availability entered",
                "remediation": "Enter the list of EU member states where the system is or will be made available.",
                "priority": "MEDIUM",
            },
            "restrictions_documented": {
                "label": "Any usage restrictions documented",
                "remediation": "Document any restrictions or conditions on the use of the system in the database entry.",
                "priority": "LOW",
            },
        },
    },
    "post_market_monitoring": {
        "article": "Art. 72",
        "title": "Post-Market Monitoring",
        "weight": 7,
        "deadline": "2 Aug 2026",
        "fields": {
            "system_established": {
                "label": "Post-market monitoring system established",
                "remediation": "Establish a documented post-market monitoring system proportionate to the system's risks. Define responsibilities, data sources, and procedures.",
                "priority": "HIGH",
            },
            "data_collection_defined": {
                "label": "Data collection and analysis procedures defined",
                "remediation": "Define procedures for actively collecting, documenting, and analysing relevant performance and safety data from deployers and other sources.",
                "priority": "HIGH",
            },
            "risk_management_updated": {
                "label": "Findings feed into risk management updates",
                "remediation": "Establish a formal feedback loop from post-market monitoring findings to risk management system updates.",
                "priority": "HIGH",
            },
            "plan_in_documentation": {
                "label": "Post-market monitoring plan included in technical documentation",
                "remediation": "Include the post-market monitoring plan as part of the technical documentation file.",
                "priority": "MEDIUM",
            },
            "incident_reporting_defined": {
                "label": "Serious incident reporting procedures defined (Art. 73, 15-day deadline)",
                "remediation": "Define procedures for reporting serious incidents to market surveillance authorities within 15 days. Include escalation criteria, report templates, and responsible persons.",
                "priority": "HIGH",
            },
            "interaction_analysis": {
                "label": "Analysis of interaction with other AI systems included",
                "remediation": "Include analysis of how the AI system interacts with other AI systems in the post-market monitoring plan.",
                "priority": "MEDIUM",
            },
        },
    },
}

DEPLOYER_OBLIGATION_SECTION = {
    "deployer": {
        "article": "Art. 26",
        "title": "Deployer Obligations",
        "weight": 10,
        "deadline": "2 Aug 2026",
        "fields": {
            "use_per_instructions": {
                "label": "System used according to provider's instructions",
                "remediation": "Review and follow the provider's instructions for use. Train all operators on proper system usage. Document any deviations.",
                "priority": "HIGH",
            },
            "human_oversight_assigned": {
                "label": "Human oversight assigned to competent, trained persons",
                "remediation": "Assign human oversight responsibilities to persons with appropriate competence, training, and authority. Provide role-specific training.",
                "priority": "HIGH",
            },
            "input_data_relevant": {
                "label": "Input data is relevant and sufficiently representative",
                "remediation": "Validate that the input data used in operation is relevant to the system's intended purpose and representative of the target context.",
                "priority": "MEDIUM",
            },
            "monitoring_active": {
                "label": "System operation monitored; provider informed of risks/incidents",
                "remediation": "Implement operational monitoring based on the provider's instructions. Establish procedures for informing the provider of any risks, incidents, or malfunctions.",
                "priority": "HIGH",
            },
            "logs_retained": {
                "label": "Automatically generated logs retained (minimum 6 months)",
                "remediation": "Retain all automatically generated system logs for the required period (minimum 6 months unless otherwise specified by law). Implement log storage with appropriate access controls.",
                "priority": "MEDIUM",
            },
            "workers_informed": {
                "label": "Workers and representatives informed before deployment",
                "remediation": "Inform all workers and their representatives who will be subject to the AI system before it is put into service. Document the notification.",
                "priority": "MEDIUM",
            },
            "dpia_completed": {
                "label": "Data Protection Impact Assessment completed (when required)",
                "remediation": "Assess whether a DPIA is required under GDPR Art. 35. If so, complete and document the DPIA before deploying the AI system.",
                "priority": "HIGH",
            },
            "fria_completed": {
                "label": "Fundamental Rights Impact Assessment completed (public bodies)",
                "remediation": "If the deployer is a public body or provides public services, complete a Fundamental Rights Impact Assessment per Art. 27. Submit results to the market surveillance authority.",
                "priority": "HIGH",
            },
            "incidents_reported": {
                "label": "Serious incidents reported to provider and authorities",
                "remediation": "Establish procedures for reporting serious incidents to the provider and market surveillance authority. Train staff on incident identification and reporting.",
                "priority": "HIGH",
            },
        },
    },
}

GPAI_OBLIGATION_SECTION = {
    "gpai": {
        "article": "Art. 53",
        "title": "GPAI Model Obligations",
        "weight": 10,
        "deadline": "2 Aug 2025",
        "fields": {
            "technical_docs": {
                "label": "Technical documentation of model and training process maintained",
                "remediation": "Create and maintain technical documentation per Annex XI covering model architecture, training methodology, data sources, compute resources, and evaluation results.",
                "priority": "HIGH",
            },
            "downstream_info": {
                "label": "Information provided for downstream AI system providers",
                "remediation": "Provide downstream providers with sufficient information about the model's capabilities, limitations, and proper integration to enable their own compliance.",
                "priority": "HIGH",
            },
            "copyright_policy": {
                "label": "Copyright compliance policy in place",
                "remediation": "Implement a policy to comply with EU copyright law (Directive 2019/790), including mechanisms for rights holders to exercise text and data mining opt-out rights.",
                "priority": "HIGH",
            },
            "training_summary_public": {
                "label": "Training data summary publicly available",
                "remediation": "Prepare and publish a sufficiently detailed summary of training data content per the AI Office template.",
                "priority": "HIGH",
            },
            "eu_representative": {
                "label": "EU authorised representative appointed (non-EU providers)",
                "remediation": "Appoint an authorised representative established in the EU if the provider is based outside the EU.",
                "priority": "HIGH",
            },
        },
    },
}

GPAI_SYSTEMIC_SECTION = {
    "gpai_systemic": {
        "article": "Art. 55",
        "title": "GPAI Systemic Risk Obligations",
        "weight": 10,
        "deadline": "2 Aug 2025",
        "fields": {
            "model_evaluation": {
                "label": "Standardized model evaluation performed including adversarial testing",
                "remediation": "Perform model evaluations using standardized protocols and benchmarks. Include adversarial testing scenarios proportionate to the risk level.",
                "priority": "HIGH",
            },
            "red_teaming": {
                "label": "Adversarial red-teaming conducted",
                "remediation": "Conduct structured red-teaming exercises with qualified personnel to identify vulnerabilities, harmful outputs, and misuse potential.",
                "priority": "HIGH",
            },
            "risk_assessment": {
                "label": "Systemic risk assessment and mitigation performed",
                "remediation": "Assess possible systemic risks at EU level (including their sources) and implement mitigation measures. Document the assessment methodology and findings.",
                "priority": "HIGH",
            },
            "incident_tracking": {
                "label": "Serious incidents tracked, documented, and reported to AI Office",
                "remediation": "Implement incident tracking, documentation, and reporting procedures. Report serious incidents and corrective measures to the AI Office and national authorities.",
                "priority": "HIGH",
            },
            "cybersecurity": {
                "label": "Adequate cybersecurity for model and infrastructure ensured",
                "remediation": "Implement cybersecurity protections for the model (against adversarial attacks, data poisoning) and its physical infrastructure.",
                "priority": "HIGH",
            },
            "energy_reporting": {
                "label": "Energy consumption reported",
                "remediation": "Report the model's energy consumption for training and, where technically feasible, inference. Include overall energy efficiency metrics.",
                "priority": "MEDIUM",
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Compliance checking logic
# ---------------------------------------------------------------------------

def check_section(section_def: Dict, status: Dict) -> Dict[str, Any]:
    """Check compliance for a single obligation section."""
    total = len(section_def["fields"])
    compliant = 0
    gaps = []
    met = []

    for field_id, field_def in section_def["fields"].items():
        value = status.get(field_id, False)
        if value:
            compliant += 1
            met.append({
                "item": field_def["label"],
                "status": "COMPLIANT",
            })
        else:
            gaps.append({
                "item": field_def["label"],
                "status": "GAP",
                "priority": field_def["priority"],
                "remediation": field_def["remediation"],
            })

    score = (compliant / total * 100) if total > 0 else 0

    return {
        "article": section_def["article"],
        "title": section_def["title"],
        "deadline": section_def["deadline"],
        "weight": section_def["weight"],
        "total_items": total,
        "compliant_items": compliant,
        "section_score": round(score, 1),
        "gaps": gaps,
        "met": met,
    }


def calculate_overall_score(section_results: List[Dict]) -> float:
    """Calculate weighted overall compliance score (0-100)."""
    total_weight = sum(s["weight"] for s in section_results)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(s["section_score"] * s["weight"] for s in section_results)
    return round(weighted_sum / total_weight, 1)


def determine_readiness(score: float) -> Dict[str, str]:
    """Determine compliance readiness level from score."""
    if score >= 90:
        return {
            "level": "READY",
            "description": "System meets compliance requirements. Minor items may remain. Proceed to conformity assessment.",
            "color": "GREEN",
        }
    elif score >= 70:
        return {
            "level": "MOSTLY_READY",
            "description": "System substantially compliant with some gaps. Address remaining items before conformity assessment.",
            "color": "YELLOW",
        }
    elif score >= 50:
        return {
            "level": "PARTIALLY_READY",
            "description": "Significant compliance gaps exist. Prioritize high-priority remediation items.",
            "color": "ORANGE",
        }
    elif score >= 25:
        return {
            "level": "EARLY_STAGE",
            "description": "Compliance program in early stages. Major effort required across multiple obligation areas.",
            "color": "RED",
        }
    else:
        return {
            "level": "NOT_STARTED",
            "description": "Compliance program not yet established. Begin with AI system inventory and risk classification.",
            "color": "RED",
        }


def run_compliance_check(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run full compliance check against the provided configuration."""
    result = {
        "system_name": config.get("system_name", "Unknown"),
        "risk_level": config.get("risk_level", "HIGH"),
        "role": config.get("role", "provider"),
        "check_date": datetime.now().strftime("%Y-%m-%d"),
        "sections": [],
        "overall_score": 0.0,
        "readiness": {},
        "priority_gaps": [],
        "summary": {},
    }

    role = config.get("role", "provider").lower()
    risk_level = config.get("risk_level", "HIGH").upper()

    # Determine which sections to check
    sections_to_check = {}

    if role == "provider" and risk_level in ("HIGH", "UNACCEPTABLE"):
        sections_to_check.update(PROVIDER_OBLIGATION_SECTIONS)

    if role == "deployer":
        sections_to_check.update(DEPLOYER_OBLIGATION_SECTION)

    if config.get("is_gpai"):
        sections_to_check.update(GPAI_OBLIGATION_SECTION)

    if config.get("is_systemic_risk"):
        sections_to_check.update(GPAI_SYSTEMIC_SECTION)

    # If provider also has deployer obligations flagged
    if role == "provider" and "deployer" in config:
        sections_to_check.update(DEPLOYER_OBLIGATION_SECTION)

    # Run checks
    section_results = []
    all_gaps = []

    for section_id, section_def in sections_to_check.items():
        status = config.get(section_id, {})
        section_result = check_section(section_def, status)
        section_result["section_id"] = section_id
        section_results.append(section_result)

        for gap in section_result["gaps"]:
            gap["section"] = section_result["title"]
            gap["article"] = section_result["article"]
            gap["deadline"] = section_result["deadline"]
            all_gaps.append(gap)

    result["sections"] = section_results

    # Calculate overall score
    result["overall_score"] = calculate_overall_score(section_results)
    result["readiness"] = determine_readiness(result["overall_score"])

    # Sort gaps by priority
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_gaps.sort(key=lambda g: priority_order.get(g["priority"], 3))
    result["priority_gaps"] = all_gaps

    # Summary
    total_items = sum(s["total_items"] for s in section_results)
    compliant_items = sum(s["compliant_items"] for s in section_results)
    result["summary"] = {
        "total_obligations_checked": total_items,
        "obligations_met": compliant_items,
        "obligations_gaps": total_items - compliant_items,
        "high_priority_gaps": len([g for g in all_gaps if g["priority"] == "HIGH"]),
        "medium_priority_gaps": len([g for g in all_gaps if g["priority"] == "MEDIUM"]),
        "low_priority_gaps": len([g for g in all_gaps if g["priority"] == "LOW"]),
        "sections_checked": len(section_results),
    }

    return result


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_text_report(result: Dict[str, Any]) -> str:
    """Format compliance check result as a human-readable report."""
    lines = []
    lines.append("=" * 72)
    lines.append("EU AI ACT COMPLIANCE CHECK REPORT")
    lines.append("Regulation (EU) 2024/1689")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"System:         {result['system_name']}")
    lines.append(f"Risk Level:     {result['risk_level']}")
    lines.append(f"Role:           {result['role'].title()}")
    lines.append(f"Check Date:     {result['check_date']}")
    lines.append(f"Overall Score:  {result['overall_score']}%")
    lines.append(f"Readiness:      {result['readiness']['level']} ({result['readiness']['color']})")
    lines.append(f"                {result['readiness']['description']}")
    lines.append("")

    # Summary
    s = result["summary"]
    lines.append("-" * 72)
    lines.append("SUMMARY")
    lines.append("-" * 72)
    lines.append(f"  Obligations checked:    {s['total_obligations_checked']}")
    lines.append(f"  Obligations met:        {s['obligations_met']}")
    lines.append(f"  Gaps found:             {s['obligations_gaps']}")
    lines.append(f"    High priority:        {s['high_priority_gaps']}")
    lines.append(f"    Medium priority:      {s['medium_priority_gaps']}")
    lines.append(f"    Low priority:         {s['low_priority_gaps']}")
    lines.append("")

    # Section scores
    lines.append("-" * 72)
    lines.append("SECTION SCORES")
    lines.append("-" * 72)
    for sec in result["sections"]:
        bar_filled = int(sec["section_score"] / 5)
        bar_empty = 20 - bar_filled
        bar = "#" * bar_filled + "." * bar_empty
        lines.append(f"  [{bar}] {sec['section_score']:5.1f}%  {sec['title']} ({sec['article']})")
    lines.append("")

    # Priority gaps
    if result["priority_gaps"]:
        lines.append("-" * 72)
        lines.append("GAP ANALYSIS (sorted by priority)")
        lines.append("-" * 72)
        current_priority = None
        for gap in result["priority_gaps"]:
            if gap["priority"] != current_priority:
                current_priority = gap["priority"]
                lines.append(f"\n  === {current_priority} PRIORITY ===")
            lines.append(f"\n  [{gap['article']}] {gap['section']}")
            lines.append(f"    Gap:         {gap['item']}")
            lines.append(f"    Deadline:    {gap['deadline']}")
            lines.append(f"    Remediation: {gap['remediation']}")

        lines.append("")

    # Section details
    lines.append("-" * 72)
    lines.append("DETAILED SECTION RESULTS")
    lines.append("-" * 72)
    for sec in result["sections"]:
        lines.append(f"\n  {sec['title']} ({sec['article']}) — {sec['section_score']}%")
        lines.append(f"  Deadline: {sec['deadline']}")
        lines.append(f"  {sec['compliant_items']}/{sec['total_items']} items compliant")

        for item in sec["met"]:
            lines.append(f"    [PASS] {item['item']}")
        for gap in sec["gaps"]:
            lines.append(f"    [FAIL] {gap['item']}")

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
        description="EU AI Act Compliance Checker — Validate compliance against Regulation (EU) 2024/1689",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input compliance_status.json
  %(prog)s --input compliance_status.json --json
  %(prog)s --input compliance_status.json --role deployer
  %(prog)s --input compliance_status.json --output report.json
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="Path to JSON file with compliance status")
    parser.add_argument("--output", "-o", help="Path to write output report (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--role", choices=["provider", "deployer"], help="Override role (default: from input)")

    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found — {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input} — {e}", file=sys.stderr)
        sys.exit(1)

    if args.role:
        config["role"] = args.role

    result = run_compliance_check(config)

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
