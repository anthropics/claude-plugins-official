#!/usr/bin/env python3
"""
EU AI Act Bias Detector

Analyzes dataset statistics for bias indicators and generates a fairness
assessment report mapped to EU AI Act data governance requirements (Art. 10).
Works with JSON input describing dataset demographics and outcomes — does NOT
perform actual ML or process raw data.

Usage:
    python ai_bias_detector.py --input dataset_stats.json
    python ai_bias_detector.py --input dataset_stats.json --json
    python ai_bias_detector.py --input dataset_stats.json --protected-attributes gender,age_group,ethnicity
    python ai_bias_detector.py --input dataset_stats.json --output report.json

Input JSON schema:
{
    "dataset_name": "Training Dataset v2.1",
    "total_samples": 50000,
    "description": "Loan application dataset for credit scoring model",
    "target_variable": "loan_approved",
    "positive_label": "approved",
    "demographics": {
        "gender": {
            "male": {"count": 30000, "positive_outcomes": 24000},
            "female": {"count": 20000, "positive_outcomes": 14000}
        },
        "age_group": {
            "18-25": {"count": 8000, "positive_outcomes": 4800},
            "26-40": {"count": 20000, "positive_outcomes": 16000},
            "41-60": {"count": 15000, "positive_outcomes": 12000},
            "60+": {"count": 7000, "positive_outcomes": 5250}
        },
        "ethnicity": {
            "group_a": {"count": 35000, "positive_outcomes": 28000},
            "group_b": {"count": 10000, "positive_outcomes": 7000},
            "group_c": {"count": 5000, "positive_outcomes": 3000}
        }
    },
    "population_distribution": {
        "gender": {"male": 0.49, "female": 0.51},
        "age_group": {"18-25": 0.15, "26-40": 0.35, "41-60": 0.30, "60+": 0.20},
        "ethnicity": {"group_a": 0.60, "group_b": 0.25, "group_c": 0.15}
    },
    "feature_correlations": {
        "zip_code": {"gender": 0.05, "ethnicity": 0.72},
        "education_level": {"gender": 0.12, "age_group": 0.35},
        "income": {"gender": 0.28, "ethnicity": 0.31}
    }
}
"""

import argparse
import json
import math
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Thresholds and configuration
# ---------------------------------------------------------------------------

# Representation ratio: dataset proportion / population proportion
# Acceptable range: 0.8 to 1.25 (within 20% of expected)
REPRESENTATION_RATIO_MIN = 0.8
REPRESENTATION_RATIO_MAX = 1.25

# Class imbalance: smallest group / largest group
# Acceptable: > 0.5 (no group less than half the largest)
CLASS_IMBALANCE_THRESHOLD = 0.5

# Four-fifths rule for disparate impact
# Ratio of positive outcome rates: minority / majority must be >= 0.8
FOUR_FIFTHS_THRESHOLD = 0.8

# Feature correlation threshold for proxy variable detection
PROXY_CORRELATION_THRESHOLD = 0.5

# Minimum group size for reliable statistical analysis
MIN_GROUP_SIZE = 30


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def analyze_representation(
    demographics: Dict[str, Dict],
    population: Optional[Dict[str, Dict]],
    total_samples: int,
) -> List[Dict[str, Any]]:
    """Analyze demographic representation in the dataset."""
    findings = []

    for attribute, groups in demographics.items():
        pop_dist = population.get(attribute, {}) if population else {}
        group_counts = {name: info["count"] for name, info in groups.items()}
        total_in_attr = sum(group_counts.values())

        # Class imbalance check
        if group_counts:
            max_count = max(group_counts.values())
            min_count = min(group_counts.values())
            min_group = [k for k, v in group_counts.items() if v == min_count][0]
            max_group = [k for k, v in group_counts.items() if v == max_count][0]
            imbalance_ratio = min_count / max_count if max_count > 0 else 0

            finding = {
                "attribute": attribute,
                "type": "class_imbalance",
                "metric": "imbalance_ratio",
                "value": round(imbalance_ratio, 4),
                "threshold": CLASS_IMBALANCE_THRESHOLD,
                "smallest_group": min_group,
                "smallest_count": min_count,
                "largest_group": max_group,
                "largest_count": max_count,
                "passed": imbalance_ratio >= CLASS_IMBALANCE_THRESHOLD,
                "severity": "LOW" if imbalance_ratio >= CLASS_IMBALANCE_THRESHOLD else (
                    "MEDIUM" if imbalance_ratio >= 0.25 else "HIGH"
                ),
            }
            findings.append(finding)

        # Representation ratio check (if population data available)
        if pop_dist:
            for group_name, group_info in groups.items():
                expected_prop = pop_dist.get(group_name)
                if expected_prop is None or expected_prop == 0:
                    continue

                actual_prop = group_info["count"] / total_in_attr if total_in_attr > 0 else 0
                rep_ratio = actual_prop / expected_prop

                finding = {
                    "attribute": attribute,
                    "group": group_name,
                    "type": "representation_ratio",
                    "metric": "representation_ratio",
                    "actual_proportion": round(actual_prop, 4),
                    "expected_proportion": round(expected_prop, 4),
                    "value": round(rep_ratio, 4),
                    "threshold_min": REPRESENTATION_RATIO_MIN,
                    "threshold_max": REPRESENTATION_RATIO_MAX,
                    "passed": REPRESENTATION_RATIO_MIN <= rep_ratio <= REPRESENTATION_RATIO_MAX,
                    "severity": "LOW" if REPRESENTATION_RATIO_MIN <= rep_ratio <= REPRESENTATION_RATIO_MAX else (
                        "MEDIUM" if 0.5 <= rep_ratio <= 2.0 else "HIGH"
                    ),
                }

                if rep_ratio < REPRESENTATION_RATIO_MIN:
                    finding["issue"] = f"Group '{group_name}' is UNDERREPRESENTED (ratio {rep_ratio:.2f})"
                elif rep_ratio > REPRESENTATION_RATIO_MAX:
                    finding["issue"] = f"Group '{group_name}' is OVERREPRESENTED (ratio {rep_ratio:.2f})"

                findings.append(finding)

        # Small group size warning
        for group_name, group_info in groups.items():
            if group_info["count"] < MIN_GROUP_SIZE:
                findings.append({
                    "attribute": attribute,
                    "group": group_name,
                    "type": "small_sample",
                    "metric": "group_size",
                    "value": group_info["count"],
                    "threshold": MIN_GROUP_SIZE,
                    "passed": False,
                    "severity": "HIGH",
                    "issue": f"Group '{group_name}' has fewer than {MIN_GROUP_SIZE} samples — statistical analysis unreliable",
                })

    return findings


def analyze_outcome_fairness(
    demographics: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    """Analyze outcome fairness across demographic groups."""
    findings = []

    for attribute, groups in demographics.items():
        # Calculate positive outcome rates for each group
        rates = {}
        for group_name, group_info in groups.items():
            count = group_info.get("count", 0)
            positive = group_info.get("positive_outcomes", 0)
            if count > 0:
                rates[group_name] = positive / count
            else:
                rates[group_name] = 0.0

        if not rates:
            continue

        max_rate = max(rates.values())
        min_rate = min(rates.values())
        max_group = [k for k, v in rates.items() if v == max_rate][0]
        min_group = [k for k, v in rates.items() if v == min_rate][0]

        # Demographic parity (four-fifths rule)
        if max_rate > 0:
            parity_ratio = min_rate / max_rate
        else:
            parity_ratio = 1.0  # Both zero

        finding = {
            "attribute": attribute,
            "type": "demographic_parity",
            "metric": "four_fifths_ratio",
            "value": round(parity_ratio, 4),
            "threshold": FOUR_FIFTHS_THRESHOLD,
            "advantaged_group": max_group,
            "advantaged_rate": round(max_rate, 4),
            "disadvantaged_group": min_group,
            "disadvantaged_rate": round(min_rate, 4),
            "passed": parity_ratio >= FOUR_FIFTHS_THRESHOLD,
            "severity": "LOW" if parity_ratio >= FOUR_FIFTHS_THRESHOLD else (
                "MEDIUM" if parity_ratio >= 0.6 else "HIGH"
            ),
        }

        if not finding["passed"]:
            diff_pct = round((1 - parity_ratio) * 100, 1)
            finding["issue"] = (
                f"Potential disparate impact: '{min_group}' has {diff_pct}% lower positive outcome rate "
                f"than '{max_group}' ({min_rate:.1%} vs {max_rate:.1%})"
            )

        findings.append(finding)

        # Pairwise group comparisons
        group_names = list(rates.keys())
        for i in range(len(group_names)):
            for j in range(i + 1, len(group_names)):
                g1, g2 = group_names[i], group_names[j]
                r1, r2 = rates[g1], rates[g2]
                higher = max(r1, r2)
                lower = min(r1, r2)

                if higher > 0:
                    pair_ratio = lower / higher
                else:
                    pair_ratio = 1.0

                if pair_ratio < FOUR_FIFTHS_THRESHOLD:
                    adv = g1 if r1 > r2 else g2
                    dis = g2 if r1 > r2 else g1
                    findings.append({
                        "attribute": attribute,
                        "type": "pairwise_disparity",
                        "metric": "pairwise_ratio",
                        "group_1": g1,
                        "group_1_rate": round(r1, 4),
                        "group_2": g2,
                        "group_2_rate": round(r2, 4),
                        "value": round(pair_ratio, 4),
                        "threshold": FOUR_FIFTHS_THRESHOLD,
                        "advantaged_group": adv,
                        "disadvantaged_group": dis,
                        "passed": False,
                        "severity": "MEDIUM" if pair_ratio >= 0.6 else "HIGH",
                        "issue": f"Disparity between '{dis}' and '{adv}': ratio {pair_ratio:.2f} < {FOUR_FIFTHS_THRESHOLD}",
                    })

    return findings


def analyze_proxy_variables(
    correlations: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    """Identify features correlated with protected attributes (proxy variables)."""
    findings = []

    for feature, attr_correlations in correlations.items():
        for protected_attr, corr_value in attr_correlations.items():
            abs_corr = abs(corr_value)

            if abs_corr >= PROXY_CORRELATION_THRESHOLD:
                findings.append({
                    "type": "proxy_variable",
                    "feature": feature,
                    "protected_attribute": protected_attr,
                    "correlation": round(corr_value, 4),
                    "absolute_correlation": round(abs_corr, 4),
                    "threshold": PROXY_CORRELATION_THRESHOLD,
                    "passed": False,
                    "severity": "MEDIUM" if abs_corr < 0.7 else "HIGH",
                    "issue": (
                        f"Feature '{feature}' has high correlation ({corr_value:.2f}) with protected "
                        f"attribute '{protected_attr}' — potential proxy variable for discrimination"
                    ),
                })
            elif abs_corr >= 0.3:
                findings.append({
                    "type": "proxy_variable_warning",
                    "feature": feature,
                    "protected_attribute": protected_attr,
                    "correlation": round(corr_value, 4),
                    "absolute_correlation": round(abs_corr, 4),
                    "threshold": PROXY_CORRELATION_THRESHOLD,
                    "passed": True,
                    "severity": "LOW",
                    "issue": (
                        f"Feature '{feature}' has moderate correlation ({corr_value:.2f}) with "
                        f"'{protected_attr}' — monitor for proxy effects"
                    ),
                })

    return findings


def generate_mitigation_recommendations(
    representation_findings: List[Dict],
    fairness_findings: List[Dict],
    proxy_findings: List[Dict],
) -> List[Dict[str, str]]:
    """Generate bias mitigation recommendations based on findings."""
    recommendations = []

    # Representation issues
    underrepresented = [
        f for f in representation_findings
        if f["type"] == "representation_ratio" and not f["passed"]
        and f.get("value", 1.0) < REPRESENTATION_RATIO_MIN
    ]
    if underrepresented:
        groups = ", ".join(set(f"{f['group']} ({f['attribute']})" for f in underrepresented))
        recommendations.append({
            "category": "Data Augmentation",
            "priority": "HIGH",
            "recommendation": f"Augment training data for underrepresented groups: {groups}. "
                "Consider synthetic data generation, targeted data collection, or oversampling techniques.",
            "ai_act_reference": "Art. 10(2)(f) — datasets shall be representative",
        })

    overrepresented = [
        f for f in representation_findings
        if f["type"] == "representation_ratio" and not f["passed"]
        and f.get("value", 1.0) > REPRESENTATION_RATIO_MAX
    ]
    if overrepresented:
        groups = ", ".join(set(f"{f['group']} ({f['attribute']})" for f in overrepresented))
        recommendations.append({
            "category": "Data Re-sampling",
            "priority": "MEDIUM",
            "recommendation": f"Consider undersampling overrepresented groups: {groups}. "
                "Alternatively, apply sample weighting to balance group influence during training.",
            "ai_act_reference": "Art. 10(2)(f) — datasets shall be representative",
        })

    # Class imbalance
    imbalanced = [
        f for f in representation_findings
        if f["type"] == "class_imbalance" and not f["passed"]
    ]
    if imbalanced:
        for f in imbalanced:
            recommendations.append({
                "category": "Class Balancing",
                "priority": "HIGH" if f["severity"] == "HIGH" else "MEDIUM",
                "recommendation": (
                    f"Address class imbalance in '{f['attribute']}': smallest group '{f['smallest_group']}' "
                    f"({f['smallest_count']}) is {f['value']:.0%} of largest group '{f['largest_group']}' "
                    f"({f['largest_count']}). Apply SMOTE, random oversampling, or class weights."
                ),
                "ai_act_reference": "Art. 10(2)(f) — datasets shall be representative",
            })

    # Outcome fairness
    disparities = [f for f in fairness_findings if f["type"] == "demographic_parity" and not f["passed"]]
    if disparities:
        for f in disparities:
            recommendations.append({
                "category": "Fairness Constraint",
                "priority": "HIGH",
                "recommendation": (
                    f"Disparate impact detected for '{f['attribute']}': '{f['disadvantaged_group']}' receives "
                    f"positive outcomes at {f['disadvantaged_rate']:.1%} vs '{f['advantaged_group']}' at "
                    f"{f['advantaged_rate']:.1%}. Consider: (1) threshold calibration per group, "
                    f"(2) adversarial debiasing during training, (3) reject-option classification for borderline cases."
                ),
                "ai_act_reference": "Art. 10(2)(f)(g) — bias examination and mitigation",
            })

    # Proxy variables
    proxies = [f for f in proxy_findings if f["type"] == "proxy_variable"]
    if proxies:
        features = ", ".join(set(f["feature"] for f in proxies))
        recommendations.append({
            "category": "Proxy Variable Mitigation",
            "priority": "HIGH",
            "recommendation": (
                f"High-correlation proxy variables detected: {features}. "
                "Options: (1) remove proxy features, (2) apply fair representation learning, "
                "(3) use causal inference to separate legitimate from discriminatory effects, "
                "(4) apply feature importance analysis to quantify proxy influence on outcomes."
            ),
            "ai_act_reference": "Art. 10(2)(f)(g) — bias examination and mitigation",
        })

    # Small samples
    small = [f for f in representation_findings if f["type"] == "small_sample"]
    if small:
        groups = ", ".join(f"{f['group']} ({f['attribute']}, n={f['value']})" for f in small)
        recommendations.append({
            "category": "Data Collection",
            "priority": "HIGH",
            "recommendation": (
                f"Insufficient sample sizes for reliable analysis: {groups}. "
                "Collect additional data for these groups before deployment. "
                "Statistical conclusions about these groups may be unreliable."
            ),
            "ai_act_reference": "Art. 10(2)(e) — data shall be sufficient for intended purpose",
        })

    # General recommendations
    if not recommendations:
        recommendations.append({
            "category": "Ongoing Monitoring",
            "priority": "LOW",
            "recommendation": "No significant bias indicators detected. Continue monitoring fairness metrics "
                "during deployment through the post-market monitoring system (Art. 72).",
            "ai_act_reference": "Art. 72 — Post-market monitoring",
        })
    else:
        recommendations.append({
            "category": "Documentation",
            "priority": "MEDIUM",
            "recommendation": "Document all bias examination findings, mitigation measures applied, and "
                "residual bias levels in the technical documentation (Art. 11) and data governance "
                "documentation (Art. 10).",
            "ai_act_reference": "Art. 10, Art. 11 — Data governance and technical documentation",
        })
        recommendations.append({
            "category": "Re-evaluation",
            "priority": "MEDIUM",
            "recommendation": "After implementing mitigation measures, re-run bias analysis to verify improvement. "
                "Establish ongoing fairness monitoring as part of post-market monitoring (Art. 72).",
            "ai_act_reference": "Art. 9(6) — Testing throughout lifecycle; Art. 72 — Post-market monitoring",
        })

    return recommendations


def run_bias_analysis(data: Dict[str, Any], protected_attrs: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run complete bias analysis on dataset statistics."""
    result = {
        "dataset_name": data.get("dataset_name", "Unknown"),
        "total_samples": data.get("total_samples", 0),
        "description": data.get("description", ""),
        "target_variable": data.get("target_variable", "Unknown"),
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "protected_attributes_analyzed": [],
        "representation_findings": [],
        "fairness_findings": [],
        "proxy_findings": [],
        "mitigation_recommendations": [],
        "art10_compliance": {},
        "overall_assessment": {},
    }

    demographics = data.get("demographics", {})
    population = data.get("population_distribution", {})
    correlations = data.get("feature_correlations", {})

    # Filter to requested protected attributes
    if protected_attrs:
        demographics = {k: v for k, v in demographics.items() if k in protected_attrs}
        population = {k: v for k, v in population.items() if k in protected_attrs}

    result["protected_attributes_analyzed"] = list(demographics.keys())

    # Run analyses
    representation = analyze_representation(demographics, population, data.get("total_samples", 0))
    result["representation_findings"] = representation

    fairness = analyze_outcome_fairness(demographics)
    result["fairness_findings"] = fairness

    proxy = analyze_proxy_variables(correlations)
    result["proxy_findings"] = proxy

    # Generate recommendations
    result["mitigation_recommendations"] = generate_mitigation_recommendations(
        representation, fairness, proxy
    )

    # Art. 10 compliance mapping
    result["art10_compliance"] = _assess_art10_compliance(data, representation, fairness, proxy)

    # Overall assessment
    all_findings = representation + fairness + proxy
    high_severity = [f for f in all_findings if f.get("severity") == "HIGH" and not f.get("passed", True)]
    medium_severity = [f for f in all_findings if f.get("severity") == "MEDIUM" and not f.get("passed", True)]
    failed = [f for f in all_findings if not f.get("passed", True)]

    if high_severity:
        assessment = "HIGH_RISK"
        description = (
            f"Significant bias indicators detected: {len(high_severity)} high-severity issues. "
            "Bias mitigation is REQUIRED before deployment per Art. 10(2)(f)(g)."
        )
    elif medium_severity:
        assessment = "MODERATE_RISK"
        description = (
            f"Moderate bias indicators detected: {len(medium_severity)} medium-severity issues. "
            "Bias mitigation is RECOMMENDED. Document findings and rationale for any accepted risks."
        )
    elif failed:
        assessment = "LOW_RISK"
        description = (
            f"Minor bias indicators detected: {len(failed)} low-severity issues. "
            "Monitor during deployment. Document examination results."
        )
    else:
        assessment = "ACCEPTABLE"
        description = "No significant bias indicators detected. Continue monitoring during deployment."

    result["overall_assessment"] = {
        "risk_level": assessment,
        "description": description,
        "total_findings": len(all_findings),
        "findings_passed": len(all_findings) - len(failed),
        "findings_failed": len(failed),
        "high_severity_count": len(high_severity),
        "medium_severity_count": len(medium_severity),
    }

    return result


def _assess_art10_compliance(
    data: Dict,
    representation: List[Dict],
    fairness: List[Dict],
    proxy: List[Dict],
) -> Dict[str, Any]:
    """Map findings to Art. 10 data governance requirements."""
    compliance = {
        "art_10_2_a": {
            "requirement": "Design choices about data documented",
            "status": "PRESENT" if data.get("description") else "MISSING",
            "note": "Dataset description provided" if data.get("description") else "No dataset description provided — document data collection design choices",
        },
        "art_10_2_e": {
            "requirement": "Data sufficient for intended purpose",
            "status": "UNKNOWN",
            "note": f"Dataset contains {data.get('total_samples', 0)} samples. Sufficiency depends on model complexity and intended purpose — requires domain assessment.",
        },
        "art_10_2_f_representativeness": {
            "requirement": "Data representative of target population",
            "status": "ASSESSED",
            "issues_found": len([f for f in representation if f["type"] == "representation_ratio" and not f["passed"]]),
            "note": "",
        },
        "art_10_2_f_bias_examination": {
            "requirement": "Datasets examined for possible biases",
            "status": "COMPLETED",
            "note": f"Bias examination completed. {len(representation) + len(fairness) + len(proxy)} checks performed.",
        },
        "art_10_2_g_bias_mitigation": {
            "requirement": "Appropriate bias mitigation measures",
            "status": "RECOMMENDATIONS_PROVIDED",
            "note": "See mitigation recommendations section for specific measures to address identified biases.",
        },
    }

    rep_issues = compliance["art_10_2_f_representativeness"]["issues_found"]
    if rep_issues == 0:
        compliance["art_10_2_f_representativeness"]["note"] = "No significant representation gaps detected."
    else:
        compliance["art_10_2_f_representativeness"]["note"] = (
            f"{rep_issues} representation issues detected. Mitigation required."
        )

    # Check for population distribution availability
    if data.get("population_distribution"):
        compliance["art_10_2_f_representativeness"]["population_data"] = "PROVIDED"
    else:
        compliance["art_10_2_f_representativeness"]["population_data"] = "NOT_PROVIDED"
        compliance["art_10_2_f_representativeness"]["note"] += (
            " Population distribution data not provided — representativeness assessment is limited."
        )

    return compliance


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_text_report(result: Dict[str, Any]) -> str:
    """Format bias analysis result as a human-readable report."""
    lines = []
    lines.append("=" * 72)
    lines.append("EU AI ACT BIAS DETECTION REPORT")
    lines.append("Art. 10 — Data and Data Governance")
    lines.append("Regulation (EU) 2024/1689")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Dataset:              {result['dataset_name']}")
    lines.append(f"Total Samples:        {result['total_samples']:,}")
    lines.append(f"Target Variable:      {result['target_variable']}")
    lines.append(f"Analysis Date:        {result['analysis_date']}")
    lines.append(f"Attributes Analyzed:  {', '.join(result['protected_attributes_analyzed'])}")
    lines.append("")

    # Overall assessment
    assessment = result["overall_assessment"]
    lines.append("-" * 72)
    lines.append("OVERALL ASSESSMENT")
    lines.append("-" * 72)
    lines.append(f"  Risk Level:         {assessment['risk_level']}")
    lines.append(f"  Total Checks:       {assessment['total_findings']}")
    lines.append(f"  Passed:             {assessment['findings_passed']}")
    lines.append(f"  Failed:             {assessment['findings_failed']}")
    lines.append(f"  High Severity:      {assessment['high_severity_count']}")
    lines.append(f"  Medium Severity:    {assessment['medium_severity_count']}")
    lines.append(f"  Assessment:         {assessment['description']}")
    lines.append("")

    # Representation findings
    rep = result["representation_findings"]
    if rep:
        lines.append("-" * 72)
        lines.append("REPRESENTATION ANALYSIS")
        lines.append("-" * 72)
        for f in rep:
            status = "PASS" if f["passed"] else "FAIL"
            lines.append(f"\n  [{status}] {f['type'].replace('_', ' ').title()}")
            if "attribute" in f:
                lines.append(f"    Attribute: {f['attribute']}")
            if "group" in f:
                lines.append(f"    Group: {f['group']}")
            lines.append(f"    Value: {f['value']}")
            if "threshold" in f:
                lines.append(f"    Threshold: {f['threshold']}")
            if "issue" in f:
                lines.append(f"    Issue: {f['issue']}")
            lines.append(f"    Severity: {f['severity']}")
        lines.append("")

    # Fairness findings
    fair = result["fairness_findings"]
    if fair:
        lines.append("-" * 72)
        lines.append("OUTCOME FAIRNESS ANALYSIS")
        lines.append("-" * 72)
        for f in fair:
            status = "PASS" if f["passed"] else "FAIL"
            lines.append(f"\n  [{status}] {f['type'].replace('_', ' ').title()}")
            lines.append(f"    Attribute: {f['attribute']}")
            if f["type"] == "demographic_parity":
                lines.append(f"    Four-fifths ratio: {f['value']:.4f} (threshold: {f['threshold']})")
                lines.append(f"    Advantaged: {f['advantaged_group']} ({f['advantaged_rate']:.1%})")
                lines.append(f"    Disadvantaged: {f['disadvantaged_group']} ({f['disadvantaged_rate']:.1%})")
            elif f["type"] == "pairwise_disparity":
                lines.append(f"    {f['group_1']} ({f['group_1_rate']:.1%}) vs {f['group_2']} ({f['group_2_rate']:.1%})")
                lines.append(f"    Ratio: {f['value']:.4f}")
            if "issue" in f:
                lines.append(f"    Issue: {f['issue']}")
            lines.append(f"    Severity: {f['severity']}")
        lines.append("")

    # Proxy variable findings
    proxy = result["proxy_findings"]
    if proxy:
        lines.append("-" * 72)
        lines.append("PROXY VARIABLE ANALYSIS")
        lines.append("-" * 72)
        for f in proxy:
            status = "PASS" if f["passed"] else "FAIL"
            lines.append(f"\n  [{status}] {f['feature']} <-> {f['protected_attribute']}")
            lines.append(f"    Correlation: {f['correlation']:.4f}")
            lines.append(f"    Threshold: {f['threshold']}")
            if "issue" in f:
                lines.append(f"    Issue: {f['issue']}")
            lines.append(f"    Severity: {f['severity']}")
        lines.append("")

    # Art. 10 compliance mapping
    art10 = result["art10_compliance"]
    if art10:
        lines.append("-" * 72)
        lines.append("ART. 10 DATA GOVERNANCE COMPLIANCE MAPPING")
        lines.append("-" * 72)
        for key, item in art10.items():
            lines.append(f"\n  [{item['status']}] {item['requirement']}")
            lines.append(f"    {item['note']}")
        lines.append("")

    # Mitigation recommendations
    recs = result["mitigation_recommendations"]
    if recs:
        lines.append("-" * 72)
        lines.append("MITIGATION RECOMMENDATIONS")
        lines.append("-" * 72)
        for r in recs:
            lines.append(f"\n  [{r['priority']}] {r['category']}")
            lines.append(f"    {r['recommendation']}")
            lines.append(f"    Reference: {r['ai_act_reference']}")
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
        description="EU AI Act Bias Detector — Analyze dataset statistics for bias indicators (Art. 10)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input dataset_stats.json
  %(prog)s --input dataset_stats.json --json
  %(prog)s --input dataset_stats.json --protected-attributes gender,age_group,ethnicity
  %(prog)s --input dataset_stats.json --output report.json
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="Path to JSON file with dataset statistics")
    parser.add_argument("--output", "-o", help="Path to write output report (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--protected-attributes",
        help="Comma-separated list of protected attributes to analyze (default: all in input)",
    )

    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found — {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input} — {e}", file=sys.stderr)
        sys.exit(1)

    protected_attrs = None
    if args.protected_attributes:
        protected_attrs = [a.strip() for a in args.protected_attributes.split(",")]

    result = run_bias_analysis(data, protected_attrs)

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
