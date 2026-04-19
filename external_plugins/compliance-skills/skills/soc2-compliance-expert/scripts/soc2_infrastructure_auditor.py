#!/usr/bin/env python3
"""
SOC 2 Infrastructure Auditor

Audits infrastructure configurations from JSON input against SOC 2 requirements.
Checks DNS records, TLS/SSL, cloud security, endpoint security, CI/CD pipeline
security, and secrets management. Outputs compliance gaps with severity ratings.

Usage:
    python soc2_infrastructure_auditor.py --config infra-config.json
    python soc2_infrastructure_auditor.py --config infra-config.json --format json
    python soc2_infrastructure_auditor.py --config infra-config.json --domains dns tls cloud
    python soc2_infrastructure_auditor.py --generate-template > infra-config.json
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Severity Levels
# ---------------------------------------------------------------------------

SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITY_INFO = "info"

SEVERITY_ORDER = {
    SEVERITY_CRITICAL: 0,
    SEVERITY_HIGH: 1,
    SEVERITY_MEDIUM: 2,
    SEVERITY_LOW: 3,
    SEVERITY_INFO: 4,
}


# ---------------------------------------------------------------------------
# Finding Helpers
# ---------------------------------------------------------------------------

def finding(
    domain: str,
    check_id: str,
    title: str,
    severity: str,
    description: str,
    remediation: str,
    tsc_mapping: list[str],
    status: str = "fail",
) -> dict:
    """Create a standardized finding dict."""
    return {
        "domain": domain,
        "check_id": check_id,
        "title": title,
        "severity": severity,
        "status": status,
        "description": description,
        "remediation": remediation,
        "tsc_mapping": tsc_mapping,
    }


def pass_finding(domain: str, check_id: str, title: str, tsc_mapping: list[str]) -> dict:
    """Create a passing check result."""
    return finding(
        domain=domain,
        check_id=check_id,
        title=title,
        severity=SEVERITY_INFO,
        description="Control requirement met.",
        remediation="No action required.",
        tsc_mapping=tsc_mapping,
        status="pass",
    )


# ---------------------------------------------------------------------------
# DNS Security Checks
# ---------------------------------------------------------------------------

def audit_dns(config: dict) -> list[dict]:
    """Audit DNS security configuration."""
    findings = []
    dns = config.get("dns", {})

    if not dns:
        findings.append(finding(
            "dns", "DNS-001", "DNS Configuration Not Provided",
            SEVERITY_HIGH,
            "No DNS security configuration was provided for audit.",
            "Provide DNS configuration including SPF, DKIM, DMARC, DNSSEC, and CAA records.",
            ["CC6.6", "CC2.2"],
        ))
        return findings

    # SPF
    spf = dns.get("spf", {})
    if not spf.get("enabled"):
        findings.append(finding(
            "dns", "DNS-SPF-001", "SPF Record Not Configured",
            SEVERITY_HIGH,
            "No SPF record configured. Email spoofing is possible for your domain.",
            "Publish SPF record: v=spf1 include:_spf.google.com -all (adjust for your email providers). Use -all (hard fail) instead of ~all.",
            ["CC6.6", "CC2.2"],
        ))
    else:
        qualifier = spf.get("qualifier", "~all")
        if qualifier != "-all":
            findings.append(finding(
                "dns", "DNS-SPF-002", "SPF Soft Fail Configured",
                SEVERITY_MEDIUM,
                f"SPF record uses '{qualifier}' instead of '-all' (hard fail). Spoofed emails may still be delivered.",
                "Update SPF record to use '-all' qualifier for strict enforcement.",
                ["CC6.6"],
            ))
        else:
            findings.append(pass_finding("dns", "DNS-SPF-001", "SPF Record Configured with Hard Fail", ["CC6.6"]))

    # DKIM
    dkim = dns.get("dkim", {})
    if not dkim.get("enabled"):
        findings.append(finding(
            "dns", "DNS-DKIM-001", "DKIM Not Configured",
            SEVERITY_HIGH,
            "DKIM signing not configured. Email authenticity cannot be verified.",
            "Configure DKIM signing with 2048-bit RSA keys. Publish DKIM DNS records for each sending domain.",
            ["CC6.6", "CC2.2"],
        ))
    else:
        key_size = dkim.get("key_size_bits", 1024)
        if key_size < 2048:
            findings.append(finding(
                "dns", "DNS-DKIM-002", "DKIM Key Size Below Recommended",
                SEVERITY_MEDIUM,
                f"DKIM key size is {key_size} bits. 2048-bit minimum recommended.",
                "Rotate to 2048-bit RSA DKIM keys. Update DNS records after rotation.",
                ["CC6.6"],
            ))
        else:
            findings.append(pass_finding("dns", "DNS-DKIM-001", "DKIM Configured with Adequate Key Size", ["CC6.6"]))

    # DMARC
    dmarc = dns.get("dmarc", {})
    if not dmarc.get("enabled"):
        findings.append(finding(
            "dns", "DNS-DMARC-001", "DMARC Not Configured",
            SEVERITY_HIGH,
            "No DMARC policy configured. No reporting or enforcement for email authentication failures.",
            "Publish DMARC record: v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com; ruf=mailto:dmarc@yourdomain.com",
            ["CC6.6", "CC2.2"],
        ))
    else:
        policy = dmarc.get("policy", "none")
        if policy == "none":
            findings.append(finding(
                "dns", "DNS-DMARC-002", "DMARC Policy Set to None (Monitoring Only)",
                SEVERITY_MEDIUM,
                "DMARC policy is 'none' (monitoring only). Spoofed emails are not rejected.",
                "Upgrade DMARC policy to 'quarantine' or 'reject' after reviewing DMARC aggregate reports.",
                ["CC6.6"],
            ))
        elif policy == "quarantine":
            findings.append(finding(
                "dns", "DNS-DMARC-003", "DMARC Policy Set to Quarantine",
                SEVERITY_LOW,
                "DMARC policy is 'quarantine'. Recommend upgrading to 'reject' for maximum protection.",
                "After confirming no legitimate email failures, upgrade DMARC policy to 'reject'.",
                ["CC6.6"],
                status="warn",
            ))
        else:
            findings.append(pass_finding("dns", "DNS-DMARC-001", "DMARC Policy Set to Reject", ["CC6.6"]))

    # DNSSEC
    if not dns.get("dnssec_enabled"):
        findings.append(finding(
            "dns", "DNS-SEC-001", "DNSSEC Not Enabled",
            SEVERITY_MEDIUM,
            "DNSSEC is not enabled. DNS responses are not authenticated, enabling DNS spoofing attacks.",
            "Enable DNSSEC for domain. Publish DS records at domain registrar. Verify with dig +dnssec.",
            ["CC6.6"],
        ))
    else:
        findings.append(pass_finding("dns", "DNS-SEC-001", "DNSSEC Enabled", ["CC6.6"]))

    # CAA
    if not dns.get("caa_records"):
        findings.append(finding(
            "dns", "DNS-CAA-001", "CAA Records Not Configured",
            SEVERITY_MEDIUM,
            "No CAA records configured. Any Certificate Authority can issue certificates for your domain.",
            "Publish CAA records restricting certificate issuance to authorized CAs: 0 issue \"letsencrypt.org\"",
            ["CC6.6"],
        ))
    else:
        findings.append(pass_finding("dns", "DNS-CAA-001", "CAA Records Configured", ["CC6.6"]))

    return findings


# ---------------------------------------------------------------------------
# TLS/SSL Checks
# ---------------------------------------------------------------------------

def audit_tls(config: dict) -> list[dict]:
    """Audit TLS/SSL configuration."""
    findings = []
    tls = config.get("tls", {})

    if not tls:
        findings.append(finding(
            "tls", "TLS-001", "TLS Configuration Not Provided",
            SEVERITY_HIGH,
            "No TLS configuration provided for audit.",
            "Provide TLS configuration including minimum version, cipher suites, HSTS settings, and certificate management.",
            ["CC6.7"],
        ))
        return findings

    # Minimum TLS version
    min_version = tls.get("minimum_version", "")
    acceptable_versions = {"1.2", "1.3", "TLS 1.2", "TLS 1.3", "TLSv1.2", "TLSv1.3"}
    deprecated_versions = {"1.0", "1.1", "TLS 1.0", "TLS 1.1", "TLSv1.0", "TLSv1.1", "SSLv3"}

    if min_version in deprecated_versions or not min_version:
        findings.append(finding(
            "tls", "TLS-VER-001", "Deprecated TLS Version Allowed",
            SEVERITY_CRITICAL,
            f"Minimum TLS version is '{min_version or 'not set'}'. TLS 1.0 and 1.1 have known vulnerabilities.",
            "Set minimum TLS version to 1.2. Prefer TLS 1.3 where supported. Disable SSLv3, TLS 1.0, and TLS 1.1.",
            ["CC6.7"],
        ))
    elif min_version in acceptable_versions:
        findings.append(pass_finding("tls", "TLS-VER-001", f"Minimum TLS Version: {min_version}", ["CC6.7"]))
    else:
        findings.append(finding(
            "tls", "TLS-VER-002", "Unknown TLS Version Configuration",
            SEVERITY_MEDIUM,
            f"TLS minimum version '{min_version}' could not be validated.",
            "Verify TLS configuration. Acceptable values: 1.2, 1.3.",
            ["CC6.7"],
        ))

    # HSTS
    hsts = tls.get("hsts", {})
    if not hsts.get("enabled"):
        findings.append(finding(
            "tls", "TLS-HSTS-001", "HSTS Not Enabled",
            SEVERITY_HIGH,
            "HTTP Strict Transport Security (HSTS) is not enabled. Users may connect over unencrypted HTTP.",
            "Enable HSTS with header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
            ["CC6.7"],
        ))
    else:
        max_age = hsts.get("max_age", 0)
        if max_age < 31536000:
            findings.append(finding(
                "tls", "TLS-HSTS-002", "HSTS Max-Age Too Short",
                SEVERITY_MEDIUM,
                f"HSTS max-age is {max_age} seconds ({max_age // 86400} days). Minimum recommended: 31536000 (1 year).",
                "Set HSTS max-age to 31536000 (1 year) minimum.",
                ["CC6.7"],
            ))
        else:
            findings.append(pass_finding("tls", "TLS-HSTS-001", "HSTS Properly Configured", ["CC6.7"]))

        if not hsts.get("include_subdomains"):
            findings.append(finding(
                "tls", "TLS-HSTS-003", "HSTS includeSubDomains Not Set",
                SEVERITY_LOW,
                "HSTS does not include subdomains. Subdomains may be accessed over HTTP.",
                "Add includeSubDomains directive to HSTS header.",
                ["CC6.7"],
            ))

    # Cipher suites
    weak_ciphers = tls.get("weak_ciphers_enabled", [])
    if weak_ciphers:
        findings.append(finding(
            "tls", "TLS-CIPHER-001", "Weak Cipher Suites Enabled",
            SEVERITY_HIGH,
            f"Weak cipher suites enabled: {', '.join(weak_ciphers)}. These are vulnerable to known attacks.",
            "Disable all weak ciphers. Allow only AEAD ciphers: AES-128-GCM, AES-256-GCM, ChaCha20-Poly1305.",
            ["CC6.7"],
        ))
    else:
        findings.append(pass_finding("tls", "TLS-CIPHER-001", "No Weak Cipher Suites Detected", ["CC6.7"]))

    # Certificate management
    cert = tls.get("certificate", {})
    if cert:
        if not cert.get("automated_renewal"):
            findings.append(finding(
                "tls", "TLS-CERT-001", "Certificate Renewal Not Automated",
                SEVERITY_MEDIUM,
                "TLS certificate renewal is not automated. Manual renewal risks expiration outages.",
                "Implement automated certificate renewal via ACME protocol (Let's Encrypt) or cloud provider (ACM, Certificate Manager).",
                ["CC6.7"],
            ))
        else:
            findings.append(pass_finding("tls", "TLS-CERT-001", "Automated Certificate Renewal Configured", ["CC6.7"]))

        sig_algo = cert.get("signature_algorithm", "")
        if "sha1" in sig_algo.lower():
            findings.append(finding(
                "tls", "TLS-CERT-002", "SHA-1 Certificate Signature",
                SEVERITY_CRITICAL,
                "Certificate uses SHA-1 signature algorithm, which is cryptographically broken.",
                "Reissue certificate with SHA-256 or SHA-384 signature algorithm.",
                ["CC6.7"],
            ))

    # OCSP stapling
    if not tls.get("ocsp_stapling"):
        findings.append(finding(
            "tls", "TLS-OCSP-001", "OCSP Stapling Not Enabled",
            SEVERITY_LOW,
            "OCSP stapling is not enabled. Certificate revocation checks may be slow or leak privacy.",
            "Enable OCSP stapling on web servers and load balancers.",
            ["CC6.7"],
            status="warn",
        ))

    return findings


# ---------------------------------------------------------------------------
# Cloud Security Checks
# ---------------------------------------------------------------------------

def audit_cloud(config: dict) -> list[dict]:
    """Audit cloud security configuration."""
    findings = []
    cloud = config.get("cloud", {})

    if not cloud:
        findings.append(finding(
            "cloud", "CLOUD-001", "Cloud Configuration Not Provided",
            SEVERITY_HIGH,
            "No cloud security configuration provided for audit.",
            "Provide cloud configuration including encryption, logging, access management, and network security settings.",
            ["CC6.1", "CC7.2"],
        ))
        return findings

    provider = cloud.get("provider", "unknown").lower()

    # Encryption at rest
    encryption = cloud.get("encryption_at_rest", {})
    if not encryption.get("enabled"):
        findings.append(finding(
            "cloud", "CLOUD-ENC-001", "Encryption at Rest Not Enabled",
            SEVERITY_CRITICAL,
            "Cloud data stores do not have encryption at rest enabled.",
            "Enable encryption at rest for all storage services. Use AES-256 with provider-managed or customer-managed keys (CMK).",
            ["CC6.1", "C1.1"],
        ))
    else:
        if encryption.get("key_management") == "customer_managed":
            findings.append(pass_finding("cloud", "CLOUD-ENC-001", "Encryption at Rest with Customer-Managed Keys", ["CC6.1", "C1.1"]))
        else:
            findings.append(pass_finding("cloud", "CLOUD-ENC-001", "Encryption at Rest Enabled (Provider-Managed Keys)", ["CC6.1", "C1.1"]))

    # Key rotation
    if encryption.get("enabled") and not encryption.get("key_rotation_enabled"):
        findings.append(finding(
            "cloud", "CLOUD-ENC-002", "Encryption Key Rotation Not Enabled",
            SEVERITY_MEDIUM,
            "Encryption key rotation is not enabled. Compromised keys have indefinite exposure.",
            "Enable annual key rotation (90 days for high-sensitivity data). Use cloud KMS automatic rotation.",
            ["CC6.1", "C1.1"],
        ))

    # Logging
    logging_cfg = cloud.get("logging", {})
    if not logging_cfg.get("audit_logging_enabled"):
        findings.append(finding(
            "cloud", "CLOUD-LOG-001", "Cloud Audit Logging Not Enabled",
            SEVERITY_CRITICAL,
            "Cloud audit logging (CloudTrail/Activity Log/Audit Logs) is not enabled. Cannot detect unauthorized access.",
            f"Enable audit logging: {'CloudTrail' if provider == 'aws' else 'Activity Log' if provider == 'azure' else 'Cloud Audit Logs'} for all regions and services.",
            ["CC7.2", "CC4.1"],
        ))
    else:
        findings.append(pass_finding("cloud", "CLOUD-LOG-001", "Cloud Audit Logging Enabled", ["CC7.2", "CC4.1"]))

    log_retention = logging_cfg.get("retention_days", 0)
    if log_retention < 90:
        findings.append(finding(
            "cloud", "CLOUD-LOG-002", "Insufficient Log Retention",
            SEVERITY_MEDIUM,
            f"Log retention is {log_retention} days. SOC 2 requires sufficient retention for audit review (90 days minimum recommended).",
            "Configure log retention to 90 days minimum (365 days recommended for SOC 2 Type II).",
            ["CC7.2"],
        ))

    if not logging_cfg.get("flow_logs_enabled"):
        findings.append(finding(
            "cloud", "CLOUD-LOG-003", "Network Flow Logs Not Enabled",
            SEVERITY_MEDIUM,
            "Network flow logs (VPC Flow Logs/NSG Flow Logs) not enabled. Cannot analyze network traffic patterns.",
            "Enable VPC/NSG flow logs for all production subnets. Forward to SIEM for analysis.",
            ["CC7.2", "CC6.6"],
        ))

    # IAM
    iam = cloud.get("iam", {})
    if iam.get("root_account_mfa") is False:
        findings.append(finding(
            "cloud", "CLOUD-IAM-001", "Root/Global Admin Account Without MFA",
            SEVERITY_CRITICAL,
            "Root or global administrator account does not have MFA enabled. This is the highest-privilege account.",
            "Enable MFA on root/global admin account immediately. Use hardware security key (YubiKey) for root MFA.",
            ["CC6.1"],
        ))

    if iam.get("root_account_used_recently"):
        findings.append(finding(
            "cloud", "CLOUD-IAM-002", "Root Account Used for Routine Operations",
            SEVERITY_HIGH,
            "Root/global admin account has been used recently. Root should only be used for break-glass scenarios.",
            "Stop using root account for routine operations. Create individual IAM users/roles. Use root only for account-level operations.",
            ["CC6.1", "CC6.3"],
        ))

    if not iam.get("password_policy_enforced"):
        findings.append(finding(
            "cloud", "CLOUD-IAM-003", "IAM Password Policy Not Enforced",
            SEVERITY_HIGH,
            "No IAM password policy enforced. Weak passwords may be in use.",
            "Configure IAM password policy: minimum 12 characters, complexity requirements, 90-day rotation, prevent reuse of last 12 passwords.",
            ["CC6.1"],
        ))

    if not iam.get("sso_enabled"):
        findings.append(finding(
            "cloud", "CLOUD-IAM-004", "SSO Not Configured for Cloud Console",
            SEVERITY_MEDIUM,
            "Single Sign-On not configured for cloud provider console. Users manage separate credentials.",
            "Configure SSO integration with corporate identity provider. Disable local IAM user passwords where possible.",
            ["CC6.1"],
        ))

    # Security services
    security = cloud.get("security_services", {})
    if not security.get("cspm_enabled"):
        findings.append(finding(
            "cloud", "CLOUD-SEC-001", "Cloud Security Posture Management Not Enabled",
            SEVERITY_MEDIUM,
            "CSPM not enabled. Configuration drift and misconfigurations may go undetected.",
            f"Enable {'Security Hub' if provider == 'aws' else 'Defender for Cloud' if provider == 'azure' else 'Security Command Center'}.",
            ["CC4.1", "CC5.2"],
        ))

    if not security.get("threat_detection_enabled"):
        findings.append(finding(
            "cloud", "CLOUD-SEC-002", "Threat Detection Not Enabled",
            SEVERITY_HIGH,
            "Cloud-native threat detection not enabled. Advanced threats may go undetected.",
            f"Enable {'GuardDuty' if provider == 'aws' else 'Microsoft Defender' if provider == 'azure' else 'Event Threat Detection'}.",
            ["CC7.2"],
        ))

    # Network
    network = cloud.get("network", {})
    if network.get("default_vpc_in_use"):
        findings.append(finding(
            "cloud", "CLOUD-NET-001", "Default VPC/Network in Use",
            SEVERITY_MEDIUM,
            "Default VPC/network is in use. Default networks have permissive security configurations.",
            "Create custom VPC/networks with restricted security groups/NSGs. Avoid using default VPCs.",
            ["CC6.6"],
        ))

    if not network.get("environment_segmentation"):
        findings.append(finding(
            "cloud", "CLOUD-NET-002", "No Environment Segmentation",
            SEVERITY_HIGH,
            "Production, staging, and development are not segmented into separate networks/accounts.",
            "Implement network segmentation: separate VPCs/accounts for production, staging, and development.",
            ["CC6.6"],
        ))

    # Public access
    storage = cloud.get("storage", {})
    if storage.get("public_buckets"):
        findings.append(finding(
            "cloud", "CLOUD-STOR-001", "Public Cloud Storage Buckets Detected",
            SEVERITY_CRITICAL,
            f"Public storage buckets detected: {', '.join(storage['public_buckets'])}. Data may be exposed.",
            "Remove public access from all storage buckets unless explicitly required (and documented). Enable bucket-level public access blocks.",
            ["CC6.1", "C1.1"],
        ))

    return findings


# ---------------------------------------------------------------------------
# Endpoint Security Checks
# ---------------------------------------------------------------------------

def audit_endpoints(config: dict) -> list[dict]:
    """Audit endpoint security configuration."""
    findings = []
    endpoints = config.get("endpoints", {})

    if not endpoints:
        findings.append(finding(
            "endpoint", "EP-001", "Endpoint Configuration Not Provided",
            SEVERITY_MEDIUM,
            "No endpoint security configuration provided for audit.",
            "Provide endpoint security configuration including MDM, EDR, disk encryption, and patch management settings.",
            ["CC6.8"],
        ))
        return findings

    # MDM
    mdm = endpoints.get("mdm", {})
    if not mdm.get("enabled"):
        findings.append(finding(
            "endpoint", "EP-MDM-001", "MDM Not Deployed",
            SEVERITY_HIGH,
            "Mobile Device Management is not deployed. Company devices cannot be managed or secured remotely.",
            "Deploy MDM solution (Jamf, Intune, Kandji). Enroll all company-managed devices.",
            ["CC6.8"],
        ))
    else:
        enrollment_pct = mdm.get("enrollment_percentage", 0)
        if enrollment_pct < 100:
            findings.append(finding(
                "endpoint", "EP-MDM-002", f"MDM Enrollment Incomplete ({enrollment_pct}%)",
                SEVERITY_MEDIUM,
                f"Only {enrollment_pct}% of company devices are enrolled in MDM.",
                "Enroll all remaining devices. Implement policy blocking unenrolled devices from accessing company resources.",
                ["CC6.8"],
            ))
        else:
            findings.append(pass_finding("endpoint", "EP-MDM-001", "MDM Fully Deployed", ["CC6.8"]))

    # Disk encryption
    encryption = endpoints.get("disk_encryption", {})
    if not encryption.get("enforced"):
        findings.append(finding(
            "endpoint", "EP-ENC-001", "Disk Encryption Not Enforced",
            SEVERITY_CRITICAL,
            "Disk encryption (FileVault/BitLocker) is not enforced. Lost/stolen devices expose data.",
            "Enforce disk encryption via MDM policy. Verify 100% compliance. Escrow recovery keys.",
            ["CC6.1", "C1.1"],
        ))
    else:
        compliance_pct = encryption.get("compliance_percentage", 0)
        if compliance_pct < 100:
            findings.append(finding(
                "endpoint", "EP-ENC-002", f"Disk Encryption Compliance at {compliance_pct}%",
                SEVERITY_HIGH,
                f"Disk encryption compliance is {compliance_pct}%. Some devices have unencrypted disks.",
                "Remediate non-compliant devices. Block access until encryption is enabled.",
                ["CC6.1", "C1.1"],
            ))
        else:
            findings.append(pass_finding("endpoint", "EP-ENC-001", "Disk Encryption 100% Compliant", ["CC6.1", "C1.1"]))

    # EDR
    edr = endpoints.get("edr", {})
    if not edr.get("deployed"):
        findings.append(finding(
            "endpoint", "EP-EDR-001", "EDR/Antivirus Not Deployed",
            SEVERITY_CRITICAL,
            "No endpoint detection and response (EDR) or antivirus solution deployed.",
            "Deploy EDR solution (CrowdStrike Falcon, SentinelOne, Microsoft Defender for Endpoint). Ensure coverage on all endpoints.",
            ["CC6.8"],
        ))
    else:
        coverage = edr.get("coverage_percentage", 0)
        if coverage < 95:
            findings.append(finding(
                "endpoint", "EP-EDR-002", f"EDR Coverage Below Target ({coverage}%)",
                SEVERITY_HIGH,
                f"EDR coverage is {coverage}%. Target is 100% for all managed endpoints.",
                "Deploy EDR agent to remaining endpoints. Investigate and remediate any installation failures.",
                ["CC6.8"],
            ))
        else:
            findings.append(pass_finding("endpoint", "EP-EDR-001", f"EDR Deployed ({coverage}% coverage)", ["CC6.8"]))

    # Patch management
    patching = endpoints.get("patch_management", {})
    if not patching.get("automated"):
        findings.append(finding(
            "endpoint", "EP-PATCH-001", "Patch Management Not Automated",
            SEVERITY_HIGH,
            "OS and application patching is not automated. Vulnerable systems may persist.",
            "Implement automated patch management. Define SLAs: critical patches within 14 days, high within 30 days.",
            ["CC7.1"],
        ))
    else:
        critical_sla = patching.get("critical_patch_sla_days", 999)
        if critical_sla > 14:
            findings.append(finding(
                "endpoint", "EP-PATCH-002", f"Critical Patch SLA Too Long ({critical_sla} days)",
                SEVERITY_MEDIUM,
                f"Critical patch SLA is {critical_sla} days. Recommended: 14 days maximum.",
                "Reduce critical patch SLA to 14 days. Implement exception process for systems that cannot be patched within SLA.",
                ["CC7.1"],
            ))
        else:
            findings.append(pass_finding("endpoint", "EP-PATCH-001", "Patch Management Properly Configured", ["CC7.1"]))

    # Screen lock
    if not endpoints.get("screen_lock_enforced"):
        findings.append(finding(
            "endpoint", "EP-LOCK-001", "Screen Lock Not Enforced",
            SEVERITY_MEDIUM,
            "Auto screen lock is not enforced via MDM policy.",
            "Enforce screen lock via MDM: maximum 5-minute idle timeout.",
            ["CC6.1"],
        ))

    # Firewall
    if not endpoints.get("host_firewall_enabled"):
        findings.append(finding(
            "endpoint", "EP-FW-001", "Host Firewall Not Enabled",
            SEVERITY_MEDIUM,
            "Host-based firewall is not enabled on endpoints.",
            "Enable host firewall via MDM policy on all managed devices.",
            ["CC6.6"],
        ))

    return findings


# ---------------------------------------------------------------------------
# CI/CD Security Checks
# ---------------------------------------------------------------------------

def audit_cicd(config: dict) -> list[dict]:
    """Audit CI/CD pipeline security configuration."""
    findings = []
    cicd = config.get("cicd", {})

    if not cicd:
        findings.append(finding(
            "cicd", "CICD-001", "CI/CD Configuration Not Provided",
            SEVERITY_MEDIUM,
            "No CI/CD pipeline security configuration provided for audit.",
            "Provide CI/CD configuration including branch protection, code review, SAST/DAST, and deployment controls.",
            ["CC8.1"],
        ))
        return findings

    # Branch protection
    branch = cicd.get("branch_protection", {})
    if not branch.get("enabled"):
        findings.append(finding(
            "cicd", "CICD-BP-001", "Branch Protection Not Enabled",
            SEVERITY_CRITICAL,
            "Branch protection rules not enabled on main/production branches. Direct pushes are possible.",
            "Enable branch protection: require PR, minimum 1 approval, no force push, status checks required.",
            ["CC8.1"],
        ))
    else:
        if not branch.get("require_approvals"):
            findings.append(finding(
                "cicd", "CICD-BP-002", "Code Review Approval Not Required",
                SEVERITY_HIGH,
                "Pull requests do not require approval reviews before merge.",
                "Require minimum 1 approval for standard changes, 2 for critical system changes.",
                ["CC8.1"],
            ))

        if branch.get("allow_force_push"):
            findings.append(finding(
                "cicd", "CICD-BP-003", "Force Push Allowed on Protected Branches",
                SEVERITY_HIGH,
                "Force push is allowed on protected branches. Audit history can be overwritten.",
                "Disable force push on all protected branches. This preserves git history for audit trail.",
                ["CC8.1", "CC4.1"],
            ))

        if not branch.get("require_status_checks"):
            findings.append(finding(
                "cicd", "CICD-BP-004", "Status Checks Not Required Before Merge",
                SEVERITY_MEDIUM,
                "CI/CD status checks not required before merge. Broken code may be deployed.",
                "Require passing CI status checks (tests, linting, security scans) before merge is allowed.",
                ["CC8.1"],
            ))

        if branch.get("enabled") and branch.get("require_approvals") and not branch.get("allow_force_push"):
            findings.append(pass_finding("cicd", "CICD-BP-001", "Branch Protection Properly Configured", ["CC8.1"]))

    # Signed commits
    if not cicd.get("signed_commits_required"):
        findings.append(finding(
            "cicd", "CICD-SC-001", "Signed Commits Not Required",
            SEVERITY_LOW,
            "GPG-signed commits are not required. Commit authorship cannot be cryptographically verified.",
            "Enable signed commit requirement. Distribute GPG keys to all developers. Configure git to sign commits by default.",
            ["CC8.1"],
            status="warn",
        ))

    # SAST
    if not cicd.get("sast_enabled"):
        findings.append(finding(
            "cicd", "CICD-SAST-001", "Static Application Security Testing Not Implemented",
            SEVERITY_HIGH,
            "SAST is not integrated into the CI/CD pipeline. Code vulnerabilities may reach production.",
            "Integrate SAST tool (Semgrep, SonarQube, CodeQL) into CI pipeline. Run on every pull request.",
            ["CC7.1", "CC8.1"],
        ))
    else:
        findings.append(pass_finding("cicd", "CICD-SAST-001", "SAST Integrated in CI/CD Pipeline", ["CC7.1", "CC8.1"]))

    # Dependency scanning
    if not cicd.get("dependency_scanning_enabled"):
        findings.append(finding(
            "cicd", "CICD-DEP-001", "Dependency Scanning Not Implemented",
            SEVERITY_HIGH,
            "Software composition analysis (SCA) not integrated. Vulnerable dependencies may be deployed.",
            "Enable dependency scanning (Dependabot, Snyk, Renovate). Configure automated PRs for vulnerable dependencies.",
            ["CC7.1"],
        ))
    else:
        findings.append(pass_finding("cicd", "CICD-DEP-001", "Dependency Scanning Enabled", ["CC7.1"]))

    # Secret scanning
    if not cicd.get("secret_scanning_enabled"):
        findings.append(finding(
            "cicd", "CICD-SEC-001", "Secret Scanning Not Implemented",
            SEVERITY_CRITICAL,
            "Secret scanning not enabled. Credentials may be committed to repositories.",
            "Enable secret scanning: pre-commit hooks (gitleaks, trufflehog) and CI-level scanning. Block commits containing secrets.",
            ["CC6.1"],
        ))
    else:
        findings.append(pass_finding("cicd", "CICD-SEC-001", "Secret Scanning Enabled", ["CC6.1"]))

    # Container scanning
    if cicd.get("uses_containers") and not cicd.get("container_scanning_enabled"):
        findings.append(finding(
            "cicd", "CICD-CONT-001", "Container Image Scanning Not Implemented",
            SEVERITY_HIGH,
            "Container images are not scanned for vulnerabilities before deployment.",
            "Integrate container scanning (Trivy, Snyk Container, Grype) into CI pipeline. Fail builds on critical/high vulnerabilities.",
            ["CC7.1"],
        ))

    # Separation of environments
    if not cicd.get("environment_separation"):
        findings.append(finding(
            "cicd", "CICD-ENV-001", "No Separation of Development and Production",
            SEVERITY_HIGH,
            "Development, staging, and production environments are not properly separated.",
            "Implement environment separation: separate accounts/projects, no developer access to production data.",
            ["CC6.6", "CC8.1"],
        ))

    return findings


# ---------------------------------------------------------------------------
# Secrets Management Checks
# ---------------------------------------------------------------------------

def audit_secrets(config: dict) -> list[dict]:
    """Audit secrets management configuration."""
    findings = []
    secrets = config.get("secrets_management", {})

    if not secrets:
        findings.append(finding(
            "secrets", "SEC-001", "Secrets Management Configuration Not Provided",
            SEVERITY_HIGH,
            "No secrets management configuration provided for audit.",
            "Provide secrets management configuration including vault usage, rotation policies, and access controls.",
            ["CC6.1"],
        ))
        return findings

    # Centralized vault
    if not secrets.get("centralized_vault"):
        findings.append(finding(
            "secrets", "SEC-VAULT-001", "No Centralized Secrets Vault",
            SEVERITY_HIGH,
            "Secrets are not managed in a centralized vault. Secrets may be stored in code, configs, or environment variables without audit trail.",
            "Deploy centralized secrets management (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager).",
            ["CC6.1"],
        ))
    else:
        findings.append(pass_finding("secrets", "SEC-VAULT-001", "Centralized Secrets Vault Deployed", ["CC6.1"]))

    # Rotation
    if not secrets.get("rotation_policy_enabled"):
        findings.append(finding(
            "secrets", "SEC-ROT-001", "Secret Rotation Policy Not Implemented",
            SEVERITY_HIGH,
            "No automated secret rotation policy. Long-lived secrets increase exposure from compromise.",
            "Implement secret rotation: API keys every 90 days, database credentials every 90 days, TLS certificates every 90 days.",
            ["CC6.1"],
        ))
    else:
        max_age = secrets.get("max_secret_age_days", 999)
        if max_age > 90:
            findings.append(finding(
                "secrets", "SEC-ROT-002", f"Secret Maximum Age Too Long ({max_age} days)",
                SEVERITY_MEDIUM,
                f"Maximum secret age is {max_age} days. Recommended: 90 days for API keys and credentials.",
                "Reduce maximum secret age to 90 days. Implement automated rotation where possible.",
                ["CC6.1"],
            ))
        else:
            findings.append(pass_finding("secrets", "SEC-ROT-001", "Secret Rotation Policy Configured", ["CC6.1"]))

    # Hardcoded secrets
    if secrets.get("hardcoded_secrets_detected"):
        findings.append(finding(
            "secrets", "SEC-HARD-001", "Hardcoded Secrets Detected",
            SEVERITY_CRITICAL,
            "Hardcoded secrets have been detected in code repositories.",
            "Remove all hardcoded secrets immediately. Rotate compromised credentials. Migrate to secrets vault. Enable pre-commit secret scanning.",
            ["CC6.1"],
        ))

    # Service account keys
    if secrets.get("long_lived_service_account_keys"):
        findings.append(finding(
            "secrets", "SEC-SA-001", "Long-Lived Service Account Keys in Use",
            SEVERITY_MEDIUM,
            "Long-lived service account keys are in use. Prefer short-lived tokens or workload identity.",
            "Migrate to workload identity federation (AWS IAM Roles, GCP Workload Identity, Azure Managed Identity). Eliminate static service account keys.",
            ["CC6.1"],
        ))

    return findings


# ---------------------------------------------------------------------------
# Access Control Checks
# ---------------------------------------------------------------------------

def audit_access(config: dict) -> list[dict]:
    """Audit access control configuration."""
    findings = []
    access = config.get("access_control", {})

    if not access:
        return findings

    # MFA
    mfa = access.get("mfa", {})
    if not mfa.get("enforced"):
        findings.append(finding(
            "access", "AC-MFA-001", "MFA Not Enforced for All Users",
            SEVERITY_CRITICAL,
            "Multi-factor authentication is not enforced for all users.",
            "Enforce MFA for all users via identity provider. Block access for users without MFA enrolled.",
            ["CC6.1"],
        ))
    else:
        findings.append(pass_finding("access", "AC-MFA-001", "MFA Enforced for All Users", ["CC6.1"]))

        if mfa.get("sms_allowed"):
            findings.append(finding(
                "access", "AC-MFA-002", "SMS-Based MFA Allowed",
                SEVERITY_MEDIUM,
                "SMS-based MFA is allowed. SMS is vulnerable to SIM swap attacks.",
                "Disable SMS-based MFA. Require TOTP, FIDO2/WebAuthn, or hardware security keys.",
                ["CC6.1"],
            ))

        if not mfa.get("hardware_keys_for_admins"):
            findings.append(finding(
                "access", "AC-MFA-003", "Hardware Security Keys Not Required for Admins",
                SEVERITY_MEDIUM,
                "Hardware security keys (YubiKey, FIDO2) are not required for privileged/admin accounts.",
                "Require hardware security keys for all admin, root, and privileged access accounts.",
                ["CC6.1"],
            ))

    # SSO
    sso = access.get("sso", {})
    if not sso.get("enabled"):
        findings.append(finding(
            "access", "AC-SSO-001", "SSO Not Implemented",
            SEVERITY_HIGH,
            "Single Sign-On not implemented. Users manage multiple credentials across applications.",
            "Implement SSO via SAML 2.0 or OIDC. Onboard all SaaS applications to SSO.",
            ["CC6.1"],
        ))
    else:
        coverage = sso.get("application_coverage_pct", 0)
        if coverage < 90:
            findings.append(finding(
                "access", "AC-SSO-002", f"SSO Coverage Incomplete ({coverage}%)",
                SEVERITY_MEDIUM,
                f"Only {coverage}% of applications are onboarded to SSO.",
                "Onboard remaining applications to SSO. For apps without SSO support, use password manager with MFA.",
                ["CC6.1"],
            ))
        else:
            findings.append(pass_finding("access", "AC-SSO-001", f"SSO Configured ({coverage}% coverage)", ["CC6.1"]))

    # Access reviews
    reviews = access.get("access_reviews", {})
    if not reviews.get("performed"):
        findings.append(finding(
            "access", "AC-REV-001", "Access Reviews Not Performed",
            SEVERITY_CRITICAL,
            "Periodic access reviews are not performed. Excessive privileges may accumulate.",
            "Implement quarterly access reviews for privileged access, semi-annual for standard access. Document review results.",
            ["CC6.3"],
        ))
    else:
        frequency = reviews.get("frequency", "")
        if frequency not in ("quarterly", "monthly"):
            findings.append(finding(
                "access", "AC-REV-002", f"Access Review Frequency Insufficient ({frequency})",
                SEVERITY_MEDIUM,
                f"Access reviews performed {frequency}. Privileged access should be reviewed quarterly.",
                "Increase access review frequency: quarterly for privileged access, semi-annual for standard access.",
                ["CC6.3"],
            ))
        else:
            findings.append(pass_finding("access", "AC-REV-001", "Access Reviews Regularly Performed", ["CC6.3"]))

    # Offboarding
    offboarding = access.get("offboarding", {})
    if not offboarding.get("automated"):
        findings.append(finding(
            "access", "AC-OFF-001", "Access Deprovisioning Not Automated",
            SEVERITY_HIGH,
            "User access deprovisioning is not automated on termination. Departed employees may retain access.",
            "Automate deprovisioning via HRIS-IdP integration (SCIM). Require same-day access removal on termination.",
            ["CC6.3", "CC6.5"],
        ))

    return findings


# ---------------------------------------------------------------------------
# Aggregation and Scoring
# ---------------------------------------------------------------------------

AUDIT_DOMAINS = {
    "dns": audit_dns,
    "tls": audit_tls,
    "cloud": audit_cloud,
    "endpoints": audit_endpoints,
    "cicd": audit_cicd,
    "secrets": audit_secrets,
    "access": audit_access,
}


def run_audit(config: dict, domains: list[str] | None = None) -> dict:
    """Run infrastructure audit across specified domains."""
    if domains:
        active = {k: v for k, v in AUDIT_DOMAINS.items() if k in domains}
    else:
        active = AUDIT_DOMAINS

    all_findings = []
    domain_summaries = []

    for domain_name, audit_func in active.items():
        domain_findings = audit_func(config)
        all_findings.extend(domain_findings)

        # Summarize
        total = len(domain_findings)
        passed = sum(1 for f in domain_findings if f["status"] == "pass")
        failed = sum(1 for f in domain_findings if f["status"] == "fail")
        warned = sum(1 for f in domain_findings if f["status"] == "warn")

        severity_counts = {}
        for f in domain_findings:
            if f["status"] == "fail":
                sev = f["severity"]
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

        domain_summaries.append({
            "domain": domain_name,
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warned,
            "severity_breakdown": severity_counts,
        })

    # Overall severity summary
    overall_severity = {SEVERITY_CRITICAL: 0, SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 0, SEVERITY_LOW: 0}
    for f in all_findings:
        if f["status"] == "fail" and f["severity"] in overall_severity:
            overall_severity[f["severity"]] += 1

    total_checks = len(all_findings)
    total_passed = sum(1 for f in all_findings if f["status"] == "pass")
    total_failed = sum(1 for f in all_findings if f["status"] == "fail")
    compliance_pct = round((total_passed / total_checks) * 100, 1) if total_checks > 0 else 0

    # Sort findings by severity
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))

    return {
        "audit_date": datetime.now().isoformat(),
        "domains_audited": list(active.keys()),
        "total_checks": total_checks,
        "passed": total_passed,
        "failed": total_failed,
        "compliance_percentage": compliance_pct,
        "severity_summary": overall_severity,
        "domain_summaries": domain_summaries,
        "findings": all_findings,
    }


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def format_audit_human(audit: dict) -> str:
    """Format audit results as human-readable report."""
    lines = []
    lines.append("=" * 78)
    lines.append("SOC 2 INFRASTRUCTURE AUDIT REPORT")
    lines.append("=" * 78)
    lines.append(f"Audit Date: {audit['audit_date'][:10]}")
    lines.append(f"Domains Audited: {', '.join(audit['domains_audited'])}")
    lines.append("")

    lines.append(f"COMPLIANCE SCORE: {audit['compliance_percentage']}%  ({audit['passed']}/{audit['total_checks']} checks passed)")
    sev = audit["severity_summary"]
    lines.append(f"Findings: {sev['critical']} Critical | {sev['high']} High | {sev['medium']} Medium | {sev['low']} Low")
    lines.append("")

    # Domain summaries
    lines.append("-" * 78)
    lines.append("DOMAIN SUMMARY")
    lines.append("-" * 78)
    for ds in audit["domain_summaries"]:
        score = round((ds["passed"] / ds["total_checks"]) * 100) if ds["total_checks"] > 0 else 0
        bar_filled = int(score / 5)
        bar = "#" * bar_filled + "." * (20 - bar_filled)
        status = "PASS" if ds["failed"] == 0 else "FAIL"
        lines.append(f"  [{status}] {ds['domain']:<15} [{bar}] {score:>3}%  ({ds['passed']}/{ds['total_checks']} passed)")
    lines.append("")

    # Findings by severity
    failed_findings = [f for f in audit["findings"] if f["status"] == "fail"]
    if failed_findings:
        lines.append("-" * 78)
        lines.append("FINDINGS (sorted by severity)")
        lines.append("-" * 78)

        current_severity = None
        for f in failed_findings:
            if f["severity"] != current_severity:
                current_severity = f["severity"]
                lines.append(f"\n  --- {current_severity.upper()} ---")

            lines.append(f"\n  [{f['check_id']}] {f['title']}")
            lines.append(f"    Domain: {f['domain']} | TSC: {', '.join(f['tsc_mapping'])}")
            lines.append(f"    Issue: {f['description']}")
            lines.append(f"    Fix: {f['remediation']}")

    # Passing checks
    passed_findings = [f for f in audit["findings"] if f["status"] == "pass"]
    if passed_findings:
        lines.append("")
        lines.append("-" * 78)
        lines.append(f"PASSING CHECKS ({len(passed_findings)})")
        lines.append("-" * 78)
        for f in passed_findings:
            lines.append(f"  [PASS] {f['check_id']}: {f['title']}")

    lines.append("")
    lines.append("=" * 78)
    lines.append("END OF REPORT")
    lines.append("=" * 78)

    return "\n".join(lines)


def generate_template() -> dict:
    """Generate a sample infrastructure configuration template."""
    return {
        "dns": {
            "spf": {"enabled": True, "qualifier": "-all"},
            "dkim": {"enabled": True, "key_size_bits": 2048},
            "dmarc": {"enabled": True, "policy": "reject"},
            "dnssec_enabled": True,
            "caa_records": ["letsencrypt.org"],
        },
        "tls": {
            "minimum_version": "1.2",
            "hsts": {"enabled": True, "max_age": 31536000, "include_subdomains": True, "preload": True},
            "weak_ciphers_enabled": [],
            "certificate": {
                "automated_renewal": True,
                "signature_algorithm": "SHA-256",
            },
            "ocsp_stapling": True,
        },
        "cloud": {
            "provider": "aws",
            "encryption_at_rest": {
                "enabled": True,
                "key_management": "customer_managed",
                "key_rotation_enabled": True,
            },
            "logging": {
                "audit_logging_enabled": True,
                "retention_days": 365,
                "flow_logs_enabled": True,
            },
            "iam": {
                "root_account_mfa": True,
                "root_account_used_recently": False,
                "password_policy_enforced": True,
                "sso_enabled": True,
            },
            "security_services": {
                "cspm_enabled": True,
                "threat_detection_enabled": True,
            },
            "network": {
                "default_vpc_in_use": False,
                "environment_segmentation": True,
            },
            "storage": {
                "public_buckets": [],
            },
        },
        "endpoints": {
            "mdm": {"enabled": True, "enrollment_percentage": 100},
            "disk_encryption": {"enforced": True, "compliance_percentage": 100},
            "edr": {"deployed": True, "coverage_percentage": 100},
            "patch_management": {"automated": True, "critical_patch_sla_days": 14},
            "screen_lock_enforced": True,
            "host_firewall_enabled": True,
        },
        "cicd": {
            "branch_protection": {
                "enabled": True,
                "require_approvals": True,
                "minimum_approvals": 1,
                "allow_force_push": False,
                "require_status_checks": True,
            },
            "signed_commits_required": True,
            "sast_enabled": True,
            "dependency_scanning_enabled": True,
            "secret_scanning_enabled": True,
            "uses_containers": True,
            "container_scanning_enabled": True,
            "environment_separation": True,
        },
        "secrets_management": {
            "centralized_vault": True,
            "vault_provider": "hashicorp_vault",
            "rotation_policy_enabled": True,
            "max_secret_age_days": 90,
            "hardcoded_secrets_detected": False,
            "long_lived_service_account_keys": False,
        },
        "access_control": {
            "mfa": {
                "enforced": True,
                "sms_allowed": False,
                "hardware_keys_for_admins": True,
            },
            "sso": {
                "enabled": True,
                "provider": "okta",
                "application_coverage_pct": 95,
            },
            "access_reviews": {
                "performed": True,
                "frequency": "quarterly",
            },
            "offboarding": {
                "automated": True,
                "sla_hours": 1,
            },
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SOC 2 Infrastructure Auditor - Validate infrastructure configurations against SOC 2 requirements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config infra-config.json
  %(prog)s --config infra-config.json --format json
  %(prog)s --config infra-config.json --domains dns tls cloud
  %(prog)s --generate-template > infra-config.json

Audit Domains:
  dns         SPF, DKIM, DMARC, DNSSEC, CAA records
  tls         TLS version, HSTS, cipher suites, certificate management
  cloud       Encryption, logging, IAM, network, storage security
  endpoints   MDM, disk encryption, EDR, patch management
  cicd        Branch protection, SAST/DAST, dependency/secret scanning
  secrets     Vault, rotation, hardcoded secrets, service accounts
  access      MFA, SSO, access reviews, offboarding automation
        """,
    )

    parser.add_argument(
        "--config",
        help="Path to JSON infrastructure configuration file",
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        choices=list(AUDIT_DOMAINS.keys()),
        help="Specific domains to audit (default: all)",
    )
    parser.add_argument(
        "--generate-template",
        action="store_true",
        help="Generate a sample infrastructure configuration template",
    )

    args = parser.parse_args()

    if args.generate_template:
        print(json.dumps(generate_template(), indent=2))
        return

    if not args.config:
        parser.error("--config is required unless using --generate-template")

    try:
        with open(args.config, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}", file=sys.stderr)
        sys.exit(1)

    audit_result = run_audit(config, args.domains)

    if args.format == "json":
        print(json.dumps(audit_result, indent=2))
    else:
        print(format_audit_human(audit_result))


if __name__ == "__main__":
    main()
