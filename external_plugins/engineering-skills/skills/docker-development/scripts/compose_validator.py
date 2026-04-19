#!/usr/bin/env python3
"""
Docker Compose Validator - Validate docker-compose files for correctness and best practices.

Checks service dependencies, port conflicts, volume configurations,
network definitions, and common misconfigurations.

Author: Claude Skills Engineering Team
License: MIT
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple


@dataclass
class Finding:
    """A validation finding."""
    severity: str
    category: str
    service: str
    message: str
    recommendation: str


class ComposeParser:
    """Minimal YAML-like parser for docker-compose files (stdlib only)."""

    def __init__(self, content: str):
        self.content = content
        self.lines = content.split("\n")

    def parse(self) -> Dict[str, Any]:
        """Parse compose file into a structured dict."""
        result: Dict[str, Any] = {}
        current_top_key = None
        current_service = None
        current_sub_key = None
        indent_stack: List[Tuple[int, str]] = []

        for line in self.lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())
            # Top-level keys
            if indent == 0 and ":" in stripped:
                key = stripped.split(":")[0].strip()
                current_top_key = key
                result[key] = {}
                current_service = None
                current_sub_key = None
                continue

            if current_top_key == "services" and indent == 2 and ":" in stripped:
                svc_name = stripped.split(":")[0].strip()
                current_service = svc_name
                result.setdefault("services", {})[svc_name] = {}
                current_sub_key = None
                continue

            if current_service and current_top_key == "services":
                svc = result["services"][current_service]
                if indent == 4 and ":" in stripped:
                    key = stripped.split(":")[0].strip()
                    value = ":".join(stripped.split(":")[1:]).strip()
                    current_sub_key = key
                    if value:
                        svc[key] = value
                    else:
                        svc.setdefault(key, [])
                elif indent >= 6 and stripped.startswith("- "):
                    item = stripped[2:].strip()
                    if current_sub_key:
                        if not isinstance(svc.get(current_sub_key), list):
                            svc[current_sub_key] = []
                        svc[current_sub_key].append(item)

        return result


class ComposeValidator:
    """Validates docker-compose configurations."""

    def __init__(self, content: str, check_ports: bool = False):
        self.content = content
        self.check_ports_only = check_ports
        self.findings: List[Finding] = []
        parser = ComposeParser(content)
        self.config = parser.parse()
        self.services = self.config.get("services", {})

    def validate(self) -> List[Finding]:
        """Run all validation checks."""
        if self.check_ports_only:
            self._check_port_conflicts()
            return self.findings

        self._check_structure()
        self._check_port_conflicts()
        self._check_dependencies()
        self._check_volumes()
        self._check_security()
        self._check_best_practices()
        return self.findings

    def _check_structure(self):
        """Check basic compose file structure."""
        if not self.services:
            self.findings.append(Finding(
                severity="critical",
                category="structure",
                service="(global)",
                message="No services defined in compose file.",
                recommendation="Add a 'services' section with at least one service.",
            ))
            return

        for name, svc in self.services.items():
            if not isinstance(svc, dict):
                continue
            has_image = "image" in svc
            has_build = "build" in svc
            if not has_image and not has_build:
                self.findings.append(Finding(
                    severity="critical",
                    category="structure",
                    service=name,
                    message=f"Service '{name}' has neither 'image' nor 'build' defined.",
                    recommendation="Add 'image: <name>:<tag>' or 'build: <context>' to the service.",
                ))

    def _check_port_conflicts(self):
        """Detect duplicate host port bindings."""
        port_map: Dict[str, List[str]] = {}

        for name, svc in self.services.items():
            if not isinstance(svc, dict):
                continue
            ports = svc.get("ports", [])
            if not isinstance(ports, list):
                continue
            for port_spec in ports:
                port_str = str(port_spec).strip().strip('"').strip("'")
                # Parse host port from spec like "8080:80" or "127.0.0.1:8080:80"
                parts = port_str.split(":")
                if len(parts) >= 2:
                    host_port = parts[-2]
                    # Handle port ranges
                    host_key = f"0.0.0.0:{host_port}"
                    if len(parts) == 3:
                        host_key = f"{parts[0]}:{parts[1]}"
                    port_map.setdefault(host_key, []).append(name)

        for port, services in port_map.items():
            if len(services) > 1:
                self.findings.append(Finding(
                    severity="critical",
                    category="ports",
                    service=", ".join(services),
                    message=f"Port conflict: host port {port} is used by services: {', '.join(services)}.",
                    recommendation="Assign unique host ports to each service.",
                ))

    def _check_dependencies(self):
        """Validate service dependencies and detect circular deps."""
        dep_graph: Dict[str, Set[str]] = {}
        for name, svc in self.services.items():
            if not isinstance(svc, dict):
                continue
            deps = svc.get("depends_on", [])
            if isinstance(deps, list):
                dep_graph[name] = set(deps)
            elif isinstance(deps, str):
                dep_graph[name] = {deps}
            else:
                dep_graph[name] = set()

        # Check for references to undefined services
        all_services = set(self.services.keys())
        for name, deps in dep_graph.items():
            for dep in deps:
                if dep not in all_services:
                    self.findings.append(Finding(
                        severity="critical",
                        category="dependencies",
                        service=name,
                        message=f"Service '{name}' depends on undefined service '{dep}'.",
                        recommendation=f"Define service '{dep}' or remove the dependency.",
                    ))

        # Detect circular dependencies using DFS
        visited: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> bool:
            if node in path:
                cycle = path[path.index(node):] + [node]
                self.findings.append(Finding(
                    severity="critical",
                    category="dependencies",
                    service=node,
                    message=f"Circular dependency detected: {' -> '.join(cycle)}.",
                    recommendation="Break the circular dependency chain.",
                ))
                return True
            if node in visited:
                return False
            visited.add(node)
            path.append(node)
            for dep in dep_graph.get(node, set()):
                if dfs(dep):
                    return True
            path.pop()
            return False

        for name in self.services:
            visited.clear()
            path.clear()
            dfs(name)

    def _check_volumes(self):
        """Check volume configurations."""
        for name, svc in self.services.items():
            if not isinstance(svc, dict):
                continue
            volumes = svc.get("volumes", [])
            if not isinstance(volumes, list):
                continue
            for vol in volumes:
                vol_str = str(vol)
                # Check for mounting Docker socket
                if "/var/run/docker.sock" in vol_str:
                    self.findings.append(Finding(
                        severity="warning",
                        category="security",
                        service=name,
                        message=f"Service '{name}' mounts Docker socket.",
                        recommendation="Docker socket access grants container root-equivalent privileges. Ensure this is necessary.",
                    ))
                # Check for mounting sensitive host paths
                sensitive_paths = ["/etc/shadow", "/etc/passwd", "/root"]
                for sp in sensitive_paths:
                    if vol_str.startswith(sp + ":") or f":{sp}" in vol_str:
                        self.findings.append(Finding(
                            severity="critical",
                            category="security",
                            service=name,
                            message=f"Service '{name}' mounts sensitive host path: {sp}.",
                            recommendation="Avoid mounting sensitive host paths into containers.",
                        ))

    def _check_security(self):
        """Check security-related configurations."""
        for name, svc in self.services.items():
            if not isinstance(svc, dict):
                continue

            # Check for privileged mode
            if svc.get("privileged") in ("true", True):
                self.findings.append(Finding(
                    severity="critical",
                    category="security",
                    service=name,
                    message=f"Service '{name}' runs in privileged mode.",
                    recommendation="Remove privileged mode. Use specific capabilities instead (cap_add).",
                ))

            # Check for host network mode
            if svc.get("network_mode") == "host":
                self.findings.append(Finding(
                    severity="warning",
                    category="security",
                    service=name,
                    message=f"Service '{name}' uses host network mode.",
                    recommendation="Use bridge or custom networks for better isolation.",
                ))

    def _check_best_practices(self):
        """Check general best practices."""
        for name, svc in self.services.items():
            if not isinstance(svc, dict):
                continue

            # Check restart policy
            if "restart" not in svc:
                self.findings.append(Finding(
                    severity="info",
                    category="best-practice",
                    service=name,
                    message=f"Service '{name}' has no restart policy.",
                    recommendation="Add 'restart: unless-stopped' for production services.",
                ))

            # Check for resource limits
            deploy = svc.get("deploy", "")
            if not deploy or "resources" not in str(deploy):
                self.findings.append(Finding(
                    severity="info",
                    category="best-practice",
                    service=name,
                    message=f"Service '{name}' has no resource limits defined.",
                    recommendation="Add deploy.resources.limits for CPU and memory.",
                ))

            # Check image tags
            image = svc.get("image", "")
            if image and ":" not in image:
                self.findings.append(Finding(
                    severity="warning",
                    category="best-practice",
                    service=name,
                    message=f"Service '{name}' uses image '{image}' without version tag.",
                    recommendation="Pin image to a specific version tag.",
                ))


def format_text(findings: List[Finding], services: Dict) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("DOCKER COMPOSE VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append(f"\nServices found: {len(services)}")
    for name in services:
        lines.append(f"  - {name}")

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
            lines.append(f"  [{f.category}] {f.service}: {f.message}")
            lines.append(f"    Fix: {f.recommendation}")
            lines.append("")

    if not findings:
        lines.append("\nNo issues found. Compose file follows best practices.")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json(findings: List[Finding], services: Dict) -> str:
    """Format results as JSON."""
    return json.dumps({
        "services": list(services.keys()),
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
        description="Validate docker-compose files for correctness and best practices."
    )
    parser.add_argument("--file", "-f", required=True, help="Path to docker-compose file")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--check-ports", action="store_true", help="Only check for port conflicts")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    content = path.read_text()
    validator = ComposeValidator(content, check_ports=args.check_ports)
    findings = validator.validate()

    if args.format == "json":
        print(format_json(findings, validator.services))
    else:
        print(format_text(findings, validator.services))

    if any(f.severity == "critical" for f in findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
