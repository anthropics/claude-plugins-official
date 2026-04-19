#!/usr/bin/env python3
"""
Dockerfile Analyzer - Analyze Dockerfiles for best practices, security, and optimization.

Scans Dockerfiles for common issues including layer optimization, security
misconfigurations, base image recommendations, and cache efficiency.

Author: Claude Skills Engineering Team
License: MIT
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class Finding:
    """A single analysis finding."""
    severity: str  # critical, warning, info
    category: str  # security, optimization, best-practice
    line: int
    instruction: str
    message: str
    recommendation: str


@dataclass
class StageInfo:
    """Information about a build stage."""
    name: Optional[str]
    base_image: str
    line: int
    instruction_count: int
    run_count: int
    copy_count: int


class DockerfileAnalyzer:
    """Analyzes Dockerfiles for best practices and issues."""

    LARGE_BASE_IMAGES = {
        "ubuntu", "debian", "centos", "fedora", "node", "python",
        "ruby", "golang", "java", "openjdk", "php",
    }

    SLIM_ALTERNATIVES = {
        "ubuntu": "ubuntu:22.04 (pin version) or use debian-slim",
        "debian": "debian:bookworm-slim",
        "node": "node:<version>-alpine or node:<version>-slim",
        "python": "python:<version>-slim or python:<version>-alpine",
        "ruby": "ruby:<version>-slim or ruby:<version>-alpine",
        "golang": "golang:<version>-alpine (or multi-stage with scratch)",
        "java": "eclipse-temurin:<version>-jre-alpine",
        "openjdk": "eclipse-temurin:<version>-jre-alpine",
        "php": "php:<version>-alpine",
    }

    SENSITIVE_PATTERNS = [
        (r"(?i)(password|passwd|secret|token|api_key|apikey)\s*=", "Potential secret in ENV or ARG"),
        (r"COPY.*\.(env|pem|key|crt|p12|pfx)", "Sensitive file copied into image"),
        (r"curl.*\|.*sh", "Piping curl to shell is risky"),
        (r"wget.*\|.*sh", "Piping wget to shell is risky"),
    ]

    def __init__(self, content: str, security_only: bool = False):
        self.content = content
        self.lines = content.strip().split("\n")
        self.findings: List[Finding] = []
        self.stages: List[StageInfo] = []
        self.security_only = security_only
        self._parse_stages()

    def _parse_stages(self):
        """Parse multi-stage build information."""
        current_stage = None
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            upper = stripped.upper()
            if upper.startswith("FROM "):
                parts = stripped.split()
                image = parts[1] if len(parts) > 1 else "unknown"
                name = None
                if "AS" in [p.upper() for p in parts]:
                    as_idx = next(j for j, p in enumerate(parts) if p.upper() == "AS")
                    if as_idx + 1 < len(parts):
                        name = parts[as_idx + 1]
                if current_stage:
                    self.stages.append(current_stage)
                current_stage = StageInfo(
                    name=name, base_image=image, line=i,
                    instruction_count=0, run_count=0, copy_count=0,
                )
            elif current_stage:
                current_stage.instruction_count += 1
                if upper.startswith("RUN "):
                    current_stage.run_count += 1
                elif upper.startswith("COPY "):
                    current_stage.copy_count += 1
        if current_stage:
            self.stages.append(current_stage)

    def analyze(self) -> List[Finding]:
        """Run all analysis checks."""
        self._check_base_images()
        self._check_security()
        self._check_layer_optimization()
        self._check_cache_efficiency()
        self._check_best_practices()
        return self.findings

    def _check_base_images(self):
        """Check base image selections."""
        for stage in self.stages:
            image = stage.base_image
            tag = ""
            if ":" in image:
                name, tag = image.rsplit(":", 1)
            else:
                name = image
                tag = "latest"

            if tag == "latest" or ":" not in stage.base_image:
                self.findings.append(Finding(
                    severity="warning",
                    category="best-practice",
                    line=stage.line,
                    instruction=f"FROM {stage.base_image}",
                    message="Using 'latest' tag or no tag is non-deterministic.",
                    recommendation="Pin to a specific version tag for reproducible builds.",
                ))

            base_name = name.split("/")[-1]
            if base_name in self.LARGE_BASE_IMAGES and "slim" not in tag and "alpine" not in tag:
                alt = self.SLIM_ALTERNATIVES.get(base_name, "a slim or alpine variant")
                if not self.security_only:
                    self.findings.append(Finding(
                        severity="info",
                        category="optimization",
                        line=stage.line,
                        instruction=f"FROM {stage.base_image}",
                        message=f"Base image '{base_name}' may be larger than necessary.",
                        recommendation=f"Consider using {alt} to reduce image size.",
                    ))

    def _check_security(self):
        """Check for security issues."""
        has_user = False
        has_healthcheck = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            upper = stripped.upper()

            if upper.startswith("USER ") and not upper.startswith("USER ROOT"):
                has_user = True

            if upper.startswith("HEALTHCHECK "):
                has_healthcheck = True

            # Check for sensitive patterns
            for pattern, msg in self.SENSITIVE_PATTERNS:
                if re.search(pattern, stripped):
                    self.findings.append(Finding(
                        severity="critical",
                        category="security",
                        line=i,
                        instruction=stripped[:80],
                        message=msg,
                        recommendation="Use Docker secrets, build args, or runtime environment variables instead.",
                    ))

            # Check for ADD with URL (prefer COPY or curl)
            if upper.startswith("ADD ") and ("http://" in stripped or "https://" in stripped):
                self.findings.append(Finding(
                    severity="warning",
                    category="security",
                    line=i,
                    instruction=stripped[:80],
                    message="ADD with URL is less transparent than COPY + curl.",
                    recommendation="Use RUN curl/wget to download, then COPY. This provides better caching and verification.",
                ))

            # Check for privileged apt-get
            if "apt-get" in stripped and "--no-install-recommends" not in stripped and "install" in stripped:
                if not self.security_only:
                    self.findings.append(Finding(
                        severity="info",
                        category="optimization",
                        line=i,
                        instruction=stripped[:80],
                        message="apt-get install without --no-install-recommends installs extra packages.",
                        recommendation="Add --no-install-recommends to reduce image size.",
                    ))

        if not has_user:
            self.findings.append(Finding(
                severity="critical",
                category="security",
                line=0,
                instruction="(global)",
                message="No USER instruction found. Container will run as root.",
                recommendation="Add 'RUN addgroup -S app && adduser -S app -G app' and 'USER app' before CMD/ENTRYPOINT.",
            ))

        if not has_healthcheck and not self.security_only:
            self.findings.append(Finding(
                severity="info",
                category="best-practice",
                line=0,
                instruction="(global)",
                message="No HEALTHCHECK instruction found.",
                recommendation="Add HEALTHCHECK to enable container orchestrators to monitor health.",
            ))

    def _check_layer_optimization(self):
        """Check for layer optimization opportunities."""
        if self.security_only:
            return

        consecutive_runs = []
        current_run_streak = 0
        streak_start = 0

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if stripped.upper().startswith("RUN "):
                if current_run_streak == 0:
                    streak_start = i
                current_run_streak += 1
            else:
                if current_run_streak >= 3:
                    consecutive_runs.append((streak_start, current_run_streak))
                current_run_streak = 0

        if current_run_streak >= 3:
            consecutive_runs.append((streak_start, current_run_streak))

        for start, count in consecutive_runs:
            self.findings.append(Finding(
                severity="warning",
                category="optimization",
                line=start,
                instruction=f"{count} consecutive RUN instructions",
                message=f"{count} consecutive RUN instructions create unnecessary layers.",
                recommendation="Combine into a single RUN with && to reduce layer count.",
            ))

    def _check_cache_efficiency(self):
        """Check for cache-busting patterns."""
        if self.security_only:
            return

        copy_all_line = 0
        run_install_after = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            upper = stripped.upper()

            if upper.startswith("COPY . ") or upper.startswith("COPY ./ "):
                copy_all_line = i

            if copy_all_line and upper.startswith("RUN "):
                if any(cmd in stripped for cmd in ["pip install", "npm install", "yarn install", "go mod download", "bundle install"]):
                    run_install_after = True

        if copy_all_line and run_install_after:
            self.findings.append(Finding(
                severity="warning",
                category="optimization",
                line=copy_all_line,
                instruction="COPY . (followed by dependency install)",
                message="Copying all files before installing dependencies breaks Docker cache.",
                recommendation="Copy dependency files first (requirements.txt, package.json), install, then copy the rest.",
            ))

    def _check_best_practices(self):
        """Check general best practices."""
        if self.security_only:
            return

        has_dockerignore = Path(".dockerignore").exists()
        if not has_dockerignore:
            self.findings.append(Finding(
                severity="info",
                category="best-practice",
                line=0,
                instruction="(project)",
                message="No .dockerignore file found in current directory.",
                recommendation="Create a .dockerignore to exclude .git, node_modules, __pycache__, etc.",
            ))

        if len(self.stages) == 1 and self.stages[0].run_count > 5:
            self.findings.append(Finding(
                severity="info",
                category="optimization",
                line=1,
                instruction="(global)",
                message="Single-stage build with many instructions. Consider multi-stage builds.",
                recommendation="Use a builder stage for compilation and a minimal runtime stage.",
            ))


def format_text(findings: List[Finding], stages: List[StageInfo]) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("DOCKERFILE ANALYSIS REPORT")
    lines.append("=" * 60)

    # Stage summary
    lines.append(f"\nBuild Stages: {len(stages)}")
    for s in stages:
        name = s.name or "(unnamed)"
        lines.append(f"  Stage '{name}': {s.base_image} ({s.instruction_count} instructions)")

    # Findings by severity
    critical = [f for f in findings if f.severity == "critical"]
    warnings = [f for f in findings if f.severity == "warning"]
    info = [f for f in findings if f.severity == "info"]

    lines.append(f"\nFindings: {len(critical)} critical, {len(warnings)} warnings, {len(info)} info")
    lines.append("-" * 60)

    for severity, group in [("CRITICAL", critical), ("WARNING", warnings), ("INFO", info)]:
        if not group:
            continue
        lines.append(f"\n[{severity}]")
        for f in group:
            loc = f"line {f.line}" if f.line > 0 else "global"
            lines.append(f"  [{f.category}] {loc}: {f.message}")
            lines.append(f"    Instruction: {f.instruction}")
            lines.append(f"    Fix: {f.recommendation}")
            lines.append("")

    if not findings:
        lines.append("\nNo issues found. Dockerfile follows best practices.")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json(findings: List[Finding], stages: List[StageInfo]) -> str:
    """Format results as JSON."""
    return json.dumps({
        "stages": [asdict(s) for s in stages],
        "findings": [asdict(f) for f in findings],
        "summary": {
            "total": len(findings),
            "critical": sum(1 for f in findings if f.severity == "critical"),
            "warnings": sum(1 for f in findings if f.severity == "warning"),
            "info": sum(1 for f in findings if f.severity == "info"),
        }
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Dockerfiles for best practices, security, and optimization."
    )
    parser.add_argument("--file", "-f", required=True, help="Path to Dockerfile")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--security-only", action="store_true", help="Only report security findings")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text()
    analyzer = DockerfileAnalyzer(content, security_only=args.security_only)
    findings = analyzer.analyze()

    if args.format == "json":
        print(format_json(findings, analyzer.stages))
    else:
        print(format_text(findings, analyzer.stages))

    # Exit with non-zero if critical findings
    if any(f.severity == "critical" for f in findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
