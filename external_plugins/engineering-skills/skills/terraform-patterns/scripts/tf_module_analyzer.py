#!/usr/bin/env python3
"""
Terraform Module Analyzer - Analyze Terraform modules for complexity and quality.

Examines module structure, variable documentation, output coverage,
resource complexity, and dependency patterns.

Author: Claude Skills Engineering Team
License: MIT
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


@dataclass
class Variable:
    """A Terraform variable."""
    name: str
    type_defined: bool
    has_default: bool
    has_description: bool
    description: str = ""


@dataclass
class Output:
    """A Terraform output."""
    name: str
    has_description: bool
    has_value: bool


@dataclass
class Resource:
    """A Terraform resource."""
    type: str
    name: str
    provider: str


@dataclass
class ModuleCall:
    """A module call."""
    name: str
    source: str


@dataclass
class ModuleAnalysis:
    """Complete module analysis result."""
    path: str
    files: List[str]
    resources: List[Resource]
    variables: List[Variable]
    outputs: List[Output]
    module_calls: List[ModuleCall]
    data_sources: List[str]
    complexity_score: int
    findings: List[Dict[str, str]]


class TerraformParser:
    """Parse Terraform HCL files for structure analysis."""

    RESOURCE_PATTERN = re.compile(r'resource\s+"(\w+)"\s+"(\w+)"')
    DATA_PATTERN = re.compile(r'data\s+"(\w+)"\s+"(\w+)"')
    VARIABLE_PATTERN = re.compile(r'variable\s+"(\w+)"')
    OUTPUT_PATTERN = re.compile(r'output\s+"(\w+)"')
    MODULE_PATTERN = re.compile(r'module\s+"(\w+)"')
    TYPE_PATTERN = re.compile(r'^\s+type\s*=')
    DEFAULT_PATTERN = re.compile(r'^\s+default\s*=')
    DESCRIPTION_PATTERN = re.compile(r'^\s+description\s*=\s*"([^"]*)"')
    VALUE_PATTERN = re.compile(r'^\s+value\s*=')
    SOURCE_PATTERN = re.compile(r'^\s+source\s*=\s*"([^"]*)"')

    def parse_file(self, filepath: Path) -> Dict[str, Any]:
        """Parse a single .tf file."""
        content = filepath.read_text()
        lines = content.split("\n")

        resources = []
        data_sources = []
        variables = []
        outputs = []
        module_calls = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Resources
            m = self.RESOURCE_PATTERN.search(line)
            if m:
                provider = m.group(1).split("_")[0]
                resources.append(Resource(type=m.group(1), name=m.group(2), provider=provider))

            # Data sources
            m = self.DATA_PATTERN.search(line)
            if m:
                data_sources.append(f"{m.group(1)}.{m.group(2)}")

            # Variables
            m = self.VARIABLE_PATTERN.search(line)
            if m:
                var = self._parse_variable_block(lines, i, m.group(1))
                variables.append(var)

            # Outputs
            m = self.OUTPUT_PATTERN.search(line)
            if m:
                out = self._parse_output_block(lines, i, m.group(1))
                outputs.append(out)

            # Module calls
            m = self.MODULE_PATTERN.search(line)
            if m:
                mod = self._parse_module_block(lines, i, m.group(1))
                module_calls.append(mod)

            i += 1

        return {
            "resources": resources,
            "data_sources": data_sources,
            "variables": variables,
            "outputs": outputs,
            "module_calls": module_calls,
        }

    def _parse_variable_block(self, lines: List[str], start: int, name: str) -> Variable:
        """Parse a variable block for type, default, description."""
        has_type = False
        has_default = False
        has_description = False
        description = ""
        brace_depth = 0
        started = False

        for i in range(start, min(start + 30, len(lines))):
            line = lines[i]
            if "{" in line:
                brace_depth += line.count("{")
                started = True
            if "}" in line:
                brace_depth -= line.count("}")
            if started and brace_depth <= 0:
                break

            if self.TYPE_PATTERN.search(line):
                has_type = True
            if self.DEFAULT_PATTERN.search(line):
                has_default = True
            m = self.DESCRIPTION_PATTERN.search(line)
            if m:
                has_description = True
                description = m.group(1)

        return Variable(name=name, type_defined=has_type, has_default=has_default,
                       has_description=has_description, description=description)

    def _parse_output_block(self, lines: List[str], start: int, name: str) -> Output:
        """Parse an output block."""
        has_description = False
        has_value = False
        brace_depth = 0
        started = False

        for i in range(start, min(start + 15, len(lines))):
            line = lines[i]
            if "{" in line:
                brace_depth += line.count("{")
                started = True
            if "}" in line:
                brace_depth -= line.count("}")
            if started and brace_depth <= 0:
                break
            if self.DESCRIPTION_PATTERN.search(line):
                has_description = True
            if self.VALUE_PATTERN.search(line):
                has_value = True

        return Output(name=name, has_description=has_description, has_value=has_value)

    def _parse_module_block(self, lines: List[str], start: int, name: str) -> ModuleCall:
        """Parse a module call block."""
        source = ""
        brace_depth = 0
        started = False

        for i in range(start, min(start + 30, len(lines))):
            line = lines[i]
            if "{" in line:
                brace_depth += line.count("{")
                started = True
            if "}" in line:
                brace_depth -= line.count("}")
            if started and brace_depth <= 0:
                break
            m = self.SOURCE_PATTERN.search(line)
            if m:
                source = m.group(1)

        return ModuleCall(name=name, source=source)


def calculate_complexity(analysis: Dict[str, Any]) -> int:
    """Calculate complexity score 0-100."""
    score = 0
    num_resources = len(analysis["resources"])
    num_variables = len(analysis["variables"])
    num_outputs = len(analysis["outputs"])
    num_modules = len(analysis["module_calls"])
    num_data = len(analysis["data_sources"])

    # Resource count contribution (0-30)
    if num_resources > 25:
        score += 30
    elif num_resources > 15:
        score += 20
    elif num_resources > 8:
        score += 10
    else:
        score += min(num_resources, 5)

    # Variable sprawl (0-25)
    if num_variables > 30:
        score += 25
    elif num_variables > 20:
        score += 15
    elif num_variables > 10:
        score += 8
    else:
        score += min(num_variables, 4)

    # Module dependencies (0-20)
    score += min(num_modules * 4, 20)

    # Data source complexity (0-15)
    score += min(num_data * 3, 15)

    # Output count (0-10)
    score += min(num_outputs, 10)

    return min(score, 100)


def generate_findings(analysis: Dict[str, Any], complexity: int) -> List[Dict[str, str]]:
    """Generate findings from analysis."""
    findings = []

    # Undocumented variables
    undoc_vars = [v for v in analysis["variables"] if not v.has_description]
    if undoc_vars:
        findings.append({
            "severity": "warning",
            "category": "documentation",
            "message": f"{len(undoc_vars)} variable(s) missing description: {', '.join(v.name for v in undoc_vars[:5])}",
            "recommendation": "Add description to all variables for maintainability.",
        })

    # Untyped variables
    untyped = [v for v in analysis["variables"] if not v.type_defined]
    if untyped:
        findings.append({
            "severity": "warning",
            "category": "quality",
            "message": f"{len(untyped)} variable(s) missing type constraint: {', '.join(v.name for v in untyped[:5])}",
            "recommendation": "Add type constraints to prevent misconfiguration.",
        })

    # Undocumented outputs
    undoc_out = [o for o in analysis["outputs"] if not o.has_description]
    if undoc_out:
        findings.append({
            "severity": "info",
            "category": "documentation",
            "message": f"{len(undoc_out)} output(s) missing description.",
            "recommendation": "Add descriptions to outputs for downstream consumers.",
        })

    # High complexity
    if complexity > 80:
        findings.append({
            "severity": "critical",
            "category": "complexity",
            "message": f"Module complexity score is {complexity}/100 (critical).",
            "recommendation": "Break this module into smaller, focused sub-modules.",
        })
    elif complexity > 60:
        findings.append({
            "severity": "warning",
            "category": "complexity",
            "message": f"Module complexity score is {complexity}/100 (high).",
            "recommendation": "Consider splitting this module to reduce complexity.",
        })

    # Multiple providers
    providers = set(r.provider for r in analysis["resources"])
    if len(providers) > 2:
        findings.append({
            "severity": "info",
            "category": "structure",
            "message": f"Module uses {len(providers)} different providers: {', '.join(providers)}.",
            "recommendation": "Consider separating resources by provider into distinct modules.",
        })

    return findings


def analyze_module(path: Path) -> Optional[ModuleAnalysis]:
    """Analyze a single Terraform module directory."""
    tf_files = list(path.glob("*.tf"))
    if not tf_files:
        return None

    parser = TerraformParser()
    all_resources = []
    all_variables = []
    all_outputs = []
    all_modules = []
    all_data = []

    for tf_file in tf_files:
        try:
            parsed = parser.parse_file(tf_file)
            all_resources.extend(parsed["resources"])
            all_variables.extend(parsed["variables"])
            all_outputs.extend(parsed["outputs"])
            all_modules.extend(parsed["module_calls"])
            all_data.extend(parsed["data_sources"])
        except Exception as e:
            pass

    combined = {
        "resources": all_resources,
        "variables": all_variables,
        "outputs": all_outputs,
        "module_calls": all_modules,
        "data_sources": all_data,
    }

    complexity = calculate_complexity(combined)
    findings = generate_findings(combined, complexity)

    return ModuleAnalysis(
        path=str(path),
        files=[f.name for f in tf_files],
        resources=all_resources,
        variables=all_variables,
        outputs=all_outputs,
        module_calls=all_modules,
        data_sources=all_data,
        complexity_score=complexity,
        findings=findings,
    )


def format_text(results: List[ModuleAnalysis]) -> str:
    """Format as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("TERRAFORM MODULE ANALYSIS REPORT")
    lines.append("=" * 60)

    for mod in results:
        lines.append(f"\nModule: {mod.path}")
        lines.append(f"  Files: {', '.join(mod.files)}")
        lines.append(f"  Resources: {len(mod.resources)}")
        lines.append(f"  Variables: {len(mod.variables)}")
        lines.append(f"  Outputs: {len(mod.outputs)}")
        lines.append(f"  Module calls: {len(mod.module_calls)}")
        lines.append(f"  Data sources: {len(mod.data_sources)}")
        lines.append(f"  Complexity: {mod.complexity_score}/100")
        lines.append("-" * 40)

        if mod.findings:
            for f in mod.findings:
                lines.append(f"  [{f['severity'].upper()}] {f['message']}")
                lines.append(f"    Fix: {f['recommendation']}")
        else:
            lines.append("  No issues found.")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json(results: List[ModuleAnalysis]) -> str:
    """Format as JSON."""
    data = []
    for mod in results:
        data.append({
            "path": mod.path,
            "files": mod.files,
            "resources": [asdict(r) for r in mod.resources],
            "variables": [asdict(v) for v in mod.variables],
            "outputs": [asdict(o) for o in mod.outputs],
            "module_calls": [asdict(m) for m in mod.module_calls],
            "data_sources": mod.data_sources,
            "complexity_score": mod.complexity_score,
            "findings": mod.findings,
        })
    return json.dumps({"modules": data}, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Terraform modules for complexity and quality."
    )
    parser.add_argument("--path", "-p", required=True, help="Path to Terraform module or directory")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively scan subdirectories")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(2)

    results = []
    if args.recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            if any(f.endswith(".tf") for f in filenames):
                result = analyze_module(Path(dirpath))
                if result:
                    results.append(result)
    else:
        result = analyze_module(root)
        if result:
            results.append(result)

    if not results:
        print("No Terraform files found.", file=sys.stderr)
        sys.exit(2)

    if args.format == "json":
        print(format_json(results))
    else:
        print(format_text(results))

    if any(f["severity"] == "critical" for r in results for f in r.findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
