#!/usr/bin/env python3
"""
Terraform Security Scanner - Scan Terraform configs for security misconfigurations.

Detects open ports, public buckets, missing encryption, overly broad IAM,
and other common security anti-patterns in Terraform code.

Author: Claude Skills Engineering Team
License: MIT
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class SecurityFinding:
    """A security finding."""
    severity: str  # critical, high, medium, low
    category: str
    file: str
    line: int
    resource: str
    message: str
    recommendation: str


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class TerraformSecurityScanner:
    """Scans Terraform files for security misconfigurations."""

    # Patterns for insecure configurations
    OPEN_CIDR_PATTERN = re.compile(r'cidr_blocks\s*=\s*\[\s*"0\.0\.0\.0/0"\s*\]')
    OPEN_IPV6_PATTERN = re.compile(r'ipv6_cidr_blocks\s*=\s*\[\s*"::/0"\s*\]')
    PUBLIC_ACL_PATTERN = re.compile(r'acl\s*=\s*"(public-read|public-read-write|authenticated-read)"')
    PUBLIC_ACCESS_PATTERN = re.compile(r'publicly_accessible\s*=\s*true')
    WILDCARD_ACTION_PATTERN = re.compile(r'"Action"\s*:\s*"\*"')
    WILDCARD_RESOURCE_PATTERN = re.compile(r'"Resource"\s*:\s*"\*"')
    NO_ENCRYPTION_S3 = re.compile(r'resource\s+"aws_s3_bucket"\s+"(\w+)"')
    RESOURCE_PATTERN = re.compile(r'resource\s+"(\w+)"\s+"(\w+)"')
    INGRESS_PATTERN = re.compile(r'ingress\s*\{')

    def __init__(self, min_severity: str = "low"):
        self.findings: List[SecurityFinding] = []
        self.min_severity = min_severity

    def scan_directory(self, path: Path) -> List[SecurityFinding]:
        """Scan all .tf files in a directory."""
        for dirpath, _, filenames in os.walk(path):
            for fname in filenames:
                if fname.endswith(".tf"):
                    filepath = Path(dirpath) / fname
                    self._scan_file(filepath)
        return self._filter_by_severity()

    def _filter_by_severity(self) -> List[SecurityFinding]:
        """Filter findings by minimum severity."""
        min_order = SEVERITY_ORDER.get(self.min_severity, 3)
        return [f for f in self.findings if SEVERITY_ORDER.get(f.severity, 3) <= min_order]

    def _scan_file(self, filepath: Path):
        """Scan a single Terraform file."""
        try:
            content = filepath.read_text()
        except Exception:
            return

        lines = content.split("\n")
        rel_path = str(filepath)

        self._check_open_cidrs(lines, rel_path)
        self._check_public_access(lines, rel_path)
        self._check_iam_policies(lines, rel_path)
        self._check_encryption(lines, rel_path, content)
        self._check_logging(lines, rel_path, content)
        self._check_security_groups(lines, rel_path)
        self._check_sensitive_outputs(lines, rel_path)

    def _check_open_cidrs(self, lines: List[str], filepath: str):
        """Check for open CIDR blocks in security groups."""
        current_resource = ""
        in_ingress = False

        for i, line in enumerate(lines, 1):
            rm = self.RESOURCE_PATTERN.search(line)
            if rm:
                current_resource = f"{rm.group(1)}.{rm.group(2)}"

            if self.INGRESS_PATTERN.search(line):
                in_ingress = True

            if self.OPEN_CIDR_PATTERN.search(line):
                sev = "critical" if in_ingress else "high"
                self.findings.append(SecurityFinding(
                    severity=sev,
                    category="network",
                    file=filepath,
                    line=i,
                    resource=current_resource,
                    message="Open CIDR block 0.0.0.0/0 allows access from any IP.",
                    recommendation="Restrict to specific CIDR ranges for the required source IPs.",
                ))

            if self.OPEN_IPV6_PATTERN.search(line):
                self.findings.append(SecurityFinding(
                    severity="critical",
                    category="network",
                    file=filepath,
                    line=i,
                    resource=current_resource,
                    message="Open IPv6 CIDR ::/0 allows access from any IPv6 address.",
                    recommendation="Restrict to specific IPv6 CIDR ranges.",
                ))

            if "}" in line and in_ingress:
                in_ingress = False

    def _check_public_access(self, lines: List[str], filepath: str):
        """Check for publicly accessible resources."""
        current_resource = ""

        for i, line in enumerate(lines, 1):
            rm = self.RESOURCE_PATTERN.search(line)
            if rm:
                current_resource = f"{rm.group(1)}.{rm.group(2)}"

            if self.PUBLIC_ACL_PATTERN.search(line):
                self.findings.append(SecurityFinding(
                    severity="critical",
                    category="access",
                    file=filepath,
                    line=i,
                    resource=current_resource,
                    message=f"Public ACL detected on S3 bucket.",
                    recommendation="Remove public ACL. Use bucket policies with specific principal access.",
                ))

            if self.PUBLIC_ACCESS_PATTERN.search(line):
                self.findings.append(SecurityFinding(
                    severity="high",
                    category="access",
                    file=filepath,
                    line=i,
                    resource=current_resource,
                    message="Resource is publicly accessible.",
                    recommendation="Set publicly_accessible = false unless explicitly required.",
                ))

    def _check_iam_policies(self, lines: List[str], filepath: str):
        """Check for overly broad IAM policies."""
        current_resource = ""

        for i, line in enumerate(lines, 1):
            rm = self.RESOURCE_PATTERN.search(line)
            if rm:
                current_resource = f"{rm.group(1)}.{rm.group(2)}"

            if self.WILDCARD_ACTION_PATTERN.search(line):
                self.findings.append(SecurityFinding(
                    severity="critical",
                    category="iam",
                    file=filepath,
                    line=i,
                    resource=current_resource,
                    message="IAM policy uses wildcard Action (*), granting all permissions.",
                    recommendation="Apply least-privilege: specify only the required actions.",
                ))

            if self.WILDCARD_RESOURCE_PATTERN.search(line):
                self.findings.append(SecurityFinding(
                    severity="high",
                    category="iam",
                    file=filepath,
                    line=i,
                    resource=current_resource,
                    message="IAM policy uses wildcard Resource (*), applying to all resources.",
                    recommendation="Scope to specific resource ARNs.",
                ))

            # Check for AssumeRole with broad principal
            if re.search(r'"Principal"\s*:\s*"\*"', line):
                self.findings.append(SecurityFinding(
                    severity="critical",
                    category="iam",
                    file=filepath,
                    line=i,
                    resource=current_resource,
                    message="IAM trust policy allows any principal to assume role.",
                    recommendation="Restrict Principal to specific AWS accounts or services.",
                ))

    def _check_encryption(self, lines: List[str], filepath: str, content: str):
        """Check for missing encryption configurations."""
        current_resource = ""
        current_type = ""
        block_start = 0

        for i, line in enumerate(lines, 1):
            rm = self.RESOURCE_PATTERN.search(line)
            if rm:
                # Check previous resource for missing encryption
                if current_type and block_start:
                    self._check_resource_encryption(current_type, current_resource, filepath, block_start, lines)
                current_type = rm.group(1)
                current_resource = f"{rm.group(1)}.{rm.group(2)}"
                block_start = i

        # Check last resource
        if current_type and block_start:
            self._check_resource_encryption(current_type, current_resource, filepath, block_start, lines)

    def _check_resource_encryption(self, res_type: str, resource: str, filepath: str,
                                    start: int, lines: List[str]):
        """Check a specific resource for encryption."""
        encryption_resources = {
            "aws_s3_bucket": "server_side_encryption_configuration",
            "aws_ebs_volume": "encrypted",
            "aws_rds_instance": "storage_encrypted",
            "aws_rds_cluster": "storage_encrypted",
            "aws_redshift_cluster": "encrypted",
            "aws_efs_file_system": "encrypted",
            "aws_kinesis_firehose_delivery_stream": "server_side_encryption",
        }

        expected = encryption_resources.get(res_type)
        if not expected:
            return

        # Look within the resource block (up to 50 lines)
        block_content = "\n".join(lines[start - 1:min(start + 50, len(lines))])
        if expected not in block_content:
            self.findings.append(SecurityFinding(
                severity="high",
                category="encryption",
                file=filepath,
                line=start,
                resource=resource,
                message=f"Resource {res_type} may be missing encryption ({expected}).",
                recommendation=f"Add {expected} = true or configure encryption block.",
            ))

    def _check_logging(self, lines: List[str], filepath: str, content: str):
        """Check for missing logging configurations."""
        current_resource = ""

        # Check for S3 bucket without logging
        s3_buckets = re.finditer(r'resource\s+"aws_s3_bucket"\s+"(\w+)"', content)
        for match in s3_buckets:
            bucket_name = match.group(1)
            # Simple check: look for logging block after this resource
            start_pos = match.end()
            next_resource = re.search(r'\nresource\s+', content[start_pos:])
            block = content[start_pos:start_pos + (next_resource.start() if next_resource else 500)]
            if "logging" not in block and "aws_s3_bucket_logging" not in content:
                line_num = content[:match.start()].count("\n") + 1
                self.findings.append(SecurityFinding(
                    severity="medium",
                    category="logging",
                    file=filepath,
                    line=line_num,
                    resource=f"aws_s3_bucket.{bucket_name}",
                    message="S3 bucket may not have access logging enabled.",
                    recommendation="Enable S3 access logging with aws_s3_bucket_logging resource.",
                ))

    def _check_security_groups(self, lines: List[str], filepath: str):
        """Check security group configurations."""
        current_resource = ""

        for i, line in enumerate(lines, 1):
            rm = self.RESOURCE_PATTERN.search(line)
            if rm:
                current_resource = f"{rm.group(1)}.{rm.group(2)}"

            # Check for unrestricted egress
            if re.search(r'from_port\s*=\s*0', line):
                # Look ahead for to_port = 0 (all ports)
                if i < len(lines) and re.search(r'to_port\s*=\s*0', lines[i]):
                    if i + 1 < len(lines) and re.search(r'protocol\s*=\s*"-1"', lines[i + 1]):
                        pass  # Egress all is often intentional, skip

            # Check for SSH from anywhere
            if re.search(r'from_port\s*=\s*22', line):
                nearby = "\n".join(lines[max(0, i - 3):min(len(lines), i + 5)])
                if "0.0.0.0/0" in nearby:
                    self.findings.append(SecurityFinding(
                        severity="critical",
                        category="network",
                        file=filepath,
                        line=i,
                        resource=current_resource,
                        message="SSH (port 22) open to the internet (0.0.0.0/0).",
                        recommendation="Restrict SSH access to specific IPs or use a bastion host.",
                    ))

            # Check for RDP from anywhere
            if re.search(r'from_port\s*=\s*3389', line):
                nearby = "\n".join(lines[max(0, i - 3):min(len(lines), i + 5)])
                if "0.0.0.0/0" in nearby:
                    self.findings.append(SecurityFinding(
                        severity="critical",
                        category="network",
                        file=filepath,
                        line=i,
                        resource=current_resource,
                        message="RDP (port 3389) open to the internet (0.0.0.0/0).",
                        recommendation="Restrict RDP access to specific IPs or use a VPN.",
                    ))

    def _check_sensitive_outputs(self, lines: List[str], filepath: str):
        """Check for sensitive values in outputs without sensitive flag."""
        in_output = False
        output_name = ""
        has_sensitive = False
        output_start = 0

        sensitive_keywords = ["password", "secret", "key", "token", "credential"]

        for i, line in enumerate(lines, 1):
            m = re.search(r'output\s+"(\w+)"', line)
            if m:
                if in_output and not has_sensitive:
                    for kw in sensitive_keywords:
                        if kw in output_name.lower():
                            self.findings.append(SecurityFinding(
                                severity="medium",
                                category="secrets",
                                file=filepath,
                                line=output_start,
                                resource=f"output.{output_name}",
                                message=f"Output '{output_name}' may contain sensitive data but is not marked sensitive.",
                                recommendation="Add 'sensitive = true' to this output.",
                            ))
                            break
                in_output = True
                output_name = m.group(1)
                has_sensitive = False
                output_start = i

            if in_output and "sensitive" in line and "true" in line:
                has_sensitive = True


def format_text(findings: List[SecurityFinding]) -> str:
    """Format as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("TERRAFORM SECURITY SCAN REPORT")
    lines.append("=" * 60)

    by_severity = {}
    for f in findings:
        by_severity.setdefault(f.severity, []).append(f)

    total = len(findings)
    lines.append(f"\nTotal findings: {total}")
    for sev in ["critical", "high", "medium", "low"]:
        count = len(by_severity.get(sev, []))
        if count:
            lines.append(f"  {sev.upper()}: {count}")

    lines.append("-" * 60)

    for sev in ["critical", "high", "medium", "low"]:
        group = by_severity.get(sev, [])
        if not group:
            continue
        lines.append(f"\n[{sev.upper()}]")
        for f in group:
            lines.append(f"  [{f.category}] {f.file}:{f.line}")
            lines.append(f"    Resource: {f.resource}")
            lines.append(f"    Issue: {f.message}")
            lines.append(f"    Fix: {f.recommendation}")
            lines.append("")

    if not findings:
        lines.append("\nNo security issues found.")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json(findings: List[SecurityFinding]) -> str:
    """Format as JSON."""
    return json.dumps({
        "findings": [asdict(f) for f in findings],
        "summary": {
            "total": len(findings),
            "critical": sum(1 for f in findings if f.severity == "critical"),
            "high": sum(1 for f in findings if f.severity == "high"),
            "medium": sum(1 for f in findings if f.severity == "medium"),
            "low": sum(1 for f in findings if f.severity == "low"),
        }
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Scan Terraform configurations for security misconfigurations."
    )
    parser.add_argument("--path", "-p", required=True, help="Path to scan")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--min-severity", choices=["critical", "high", "medium", "low"],
                       default="low", help="Minimum severity to report")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(2)

    scanner = TerraformSecurityScanner(min_severity=args.min_severity)
    findings = scanner.scan_directory(path)

    if args.format == "json":
        print(format_json(findings))
    else:
        print(format_text(findings))

    if any(f.severity == "critical" for f in findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
