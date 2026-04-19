#!/usr/bin/env python3
"""
Code Quality Checker

Analyzes source code for quality issues, code smells, complexity metrics,
and SOLID principle violations.

Usage:
    python code_quality_checker.py /path/to/file.py
    python code_quality_checker.py /path/to/directory --recursive
    python code_quality_checker.py . --language typescript --json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


# Language-specific file extensions
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "typescript": [".ts", ".tsx"],
    "javascript": [".js", ".jsx", ".mjs"],
    "go": [".go"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"]
}

# Code smell thresholds
THRESHOLDS = {
    "long_function_lines": 50,
    "too_many_parameters": 5,
    "high_complexity": 10,
    "god_class_methods": 20,
    "max_imports": 15
}


def get_file_extension(filepath: Path) -> str:
    """Get file extension."""
    return filepath.suffix.lower()


def detect_language(filepath: Path) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = get_file_extension(filepath)
    for lang, extensions in LANGUAGE_EXTENSIONS.items():
        if ext in extensions:
            return lang
    return None


def read_file_content(filepath: Path) -> str:
    """Read file content safely."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def calculate_cyclomatic_complexity(content: str) -> int:
    """
    Estimate cyclomatic complexity based on control flow keywords.
    """
    complexity = 1  # Base complexity

    # Control flow patterns that increase complexity
    patterns = [
        r"\bif\b",
        r"\belif\b",
        r"\belse\b",
        r"\bfor\b",
        r"\bwhile\b",
        r"\bcase\b",
        r"\bcatch\b",
        r"\bexcept\b",
        r"\band\b",
        r"\bor\b",
        r"\|\|",
        r"&&"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        complexity += len(matches)

    return complexity


def count_lines(content: str) -> Dict[str, int]:
    """Count different types of lines in code."""
    lines = content.split("\n")
    total = len(lines)
    blank = sum(1 for line in lines if not line.strip())
    comment = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            comment += 1
        elif stripped.startswith("/*") or stripped.startswith("'''") or stripped.startswith('"""'):
            comment += 1

    code = total - blank - comment

    return {
        "total": total,
        "code": code,
        "blank": blank,
        "comment": comment
    }


def find_functions(content: str, language: str) -> List[Dict]:
    """Find function definitions and their metrics."""
    functions = []

    # Language-specific function patterns
    patterns = {
        "python": r"def\s+(\w+)\s*\(([^)]*)\)",
        "typescript": r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>)",
        "javascript": r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>)",
        "go": r"func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(([^)]*)\)",
        "swift": r"func\s+(\w+)\s*\(([^)]*)\)",
        "kotlin": r"fun\s+(\w+)\s*\(([^)]*)\)"
    }

    pattern = patterns.get(language, patterns["python"])
    matches = re.finditer(pattern, content, re.MULTILINE)

    for match in matches:
        name = next((g for g in match.groups() if g), "anonymous")
        params_str = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""

        # Count parameters
        params = [p.strip() for p in params_str.split(",") if p.strip()]
        param_count = len(params)

        # Estimate function length
        start_pos = match.end()
        remaining = content[start_pos:]

        next_func = re.search(pattern, remaining)
        if next_func:
            func_body = remaining[:next_func.start()]
        else:
            func_body = remaining[:min(2000, len(remaining))]

        line_count = len(func_body.split("\n"))
        complexity = calculate_cyclomatic_complexity(func_body)

        functions.append({
            "name": name,
            "parameters": param_count,
            "lines": line_count,
            "complexity": complexity
        })

    return functions


def find_classes(content: str, language: str) -> List[Dict]:
    """Find class definitions and their metrics."""
    classes = []

    patterns = {
        "python": r"class\s+(\w+)",
        "typescript": r"class\s+(\w+)",
        "javascript": r"class\s+(\w+)",
        "go": r"type\s+(\w+)\s+struct",
        "swift": r"class\s+(\w+)",
        "kotlin": r"class\s+(\w+)"
    }

    pattern = patterns.get(language, patterns["python"])
    matches = re.finditer(pattern, content)

    for match in matches:
        name = match.group(1)

        start_pos = match.end()
        remaining = content[start_pos:]

        next_class = re.search(pattern, remaining)
        if next_class:
            class_body = remaining[:next_class.start()]
        else:
            class_body = remaining

        # Count methods
        method_patterns = {
            "python": r"def\s+\w+\s*\(",
            "typescript": r"(?:public|private|protected)?\s*\w+\s*\([^)]*\)\s*[:{]",
            "javascript": r"\w+\s*\([^)]*\)\s*\{",
            "go": r"func\s+\(",
            "swift": r"func\s+\w+",
            "kotlin": r"fun\s+\w+"
        }
        method_pattern = method_patterns.get(language, method_patterns["python"])
        methods = len(re.findall(method_pattern, class_body))

        classes.append({
            "name": name,
            "methods": methods,
            "lines": len(class_body.split("\n"))
        })

    return classes


def check_code_smells(content: str, functions: List[Dict], classes: List[Dict]) -> List[Dict]:
    """Check for code smells in the content."""
    smells = []

    # Long functions
    for func in functions:
        if func["lines"] > THRESHOLDS["long_function_lines"]:
            smells.append({
                "type": "long_function",
                "severity": "medium",
                "message": f"Function '{func['name']}' has {func['lines']} lines (max: {THRESHOLDS['long_function_lines']})",
                "location": func["name"]
            })

    # Too many parameters
    for func in functions:
        if func["parameters"] > THRESHOLDS["too_many_parameters"]:
            smells.append({
                "type": "too_many_parameters",
                "severity": "low",
                "message": f"Function '{func['name']}' has {func['parameters']} parameters (max: {THRESHOLDS['too_many_parameters']})",
                "location": func["name"]
            })

    # High complexity
    for func in functions:
        if func["complexity"] > THRESHOLDS["high_complexity"]:
            severity = "high" if func["complexity"] > 20 else "medium"
            smells.append({
                "type": "high_complexity",
                "severity": severity,
                "message": f"Function '{func['name']}' has complexity {func['complexity']} (max: {THRESHOLDS['high_complexity']})",
                "location": func["name"]
            })

    # God classes
    for cls in classes:
        if cls["methods"] > THRESHOLDS["god_class_methods"]:
            smells.append({
                "type": "god_class",
                "severity": "high",
                "message": f"Class '{cls['name']}' has {cls['methods']} methods (max: {THRESHOLDS['god_class_methods']})",
                "location": cls["name"]
            })

    # Magic numbers
    magic_pattern = r"\b(?<![.\"\'])\d{3,}\b(?!\.\d)"
    for i, line in enumerate(content.split("\n"), 1):
        if line.strip().startswith(("#", "//", "import", "from")):
            continue
        matches = re.findall(magic_pattern, line)
        for match in matches[:1]:  # One per line
            smells.append({
                "type": "magic_number",
                "severity": "low",
                "message": f"Magic number {match} should be a named constant",
                "location": f"line {i}"
            })

    # Commented code patterns
    commented_code_pattern = r"^\s*[#//]+\s*(if|for|while|def|function|class|const|let|var)\s"
    for i, line in enumerate(content.split("\n"), 1):
        if re.match(commented_code_pattern, line, re.IGNORECASE):
            smells.append({
                "type": "commented_code",
                "severity": "low",
                "message": "Commented-out code should be removed",
                "location": f"line {i}"
            })

    return smells


def check_solid_violations(content: str) -> List[Dict]:
    """Check for potential SOLID principle violations."""
    violations = []

    # OCP: Type checking instead of polymorphism
    type_checks = len(re.findall(r"isinstance\(|type\(.*\)\s*==|typeof\s+\w+\s*===", content))
    if type_checks > 2:
        violations.append({
            "principle": "OCP",
            "name": "Open/Closed Principle",
            "severity": "medium",
            "message": f"Found {type_checks} type checks - consider using polymorphism"
        })

    # LSP/ISP: NotImplementedError
    not_impl = len(re.findall(r"raise\s+NotImplementedError|not\s+implemented", content, re.IGNORECASE))
    if not_impl:
        violations.append({
            "principle": "LSP/ISP",
            "name": "Liskov/Interface Segregation",
            "severity": "low",
            "message": f"Found {not_impl} unimplemented methods - may indicate oversized interface"
        })

    # DIP: Too many direct imports
    imports = len(re.findall(r"^(?:import|from)\s+", content, re.MULTILINE))
    if imports > THRESHOLDS["max_imports"]:
        violations.append({
            "principle": "DIP",
            "name": "Dependency Inversion Principle",
            "severity": "low",
            "message": f"File has {imports} imports - consider dependency injection"
        })

    return violations


def calculate_quality_score(
    line_metrics: Dict,
    functions: List[Dict],
    classes: List[Dict],
    smells: List[Dict],
    violations: List[Dict]
) -> int:
    """Calculate overall quality score (0-100)."""
    score = 100

    # Deduct for code smells
    for smell in smells:
        if smell["severity"] == "high":
            score -= 10
        elif smell["severity"] == "medium":
            score -= 5
        elif smell["severity"] == "low":
            score -= 2

    # Deduct for SOLID violations
    for violation in violations:
        if violation["severity"] == "high":
            score -= 8
        elif violation["severity"] == "medium":
            score -= 4
        elif violation["severity"] == "low":
            score -= 2

    # Bonus for good comment ratio (10-30%)
    if line_metrics["total"] > 0:
        comment_ratio = line_metrics["comment"] / line_metrics["total"]
        if 0.1 <= comment_ratio <= 0.3:
            score += 5

    # Bonus for reasonable function sizes
    if functions:
        avg_lines = sum(f["lines"] for f in functions) / len(functions)
        if avg_lines < 30:
            score += 5

    return max(0, min(100, score))


def get_grade(score: int) -> str:
    """Convert score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def analyze_file(filepath: Path) -> Dict:
    """Analyze a single file for code quality."""
    language = detect_language(filepath)
    if not language:
        return {"error": f"Unsupported file type: {filepath.suffix}"}

    content = read_file_content(filepath)
    if not content:
        return {"error": f"Could not read file: {filepath}"}

    line_metrics = count_lines(content)
    functions = find_functions(content, language)
    classes = find_classes(content, language)
    smells = check_code_smells(content, functions, classes)
    violations = check_solid_violations(content)
    score = calculate_quality_score(line_metrics, functions, classes, smells, violations)

    return {
        "file": str(filepath),
        "language": language,
        "metrics": {
            "lines": line_metrics,
            "functions": len(functions),
            "classes": len(classes),
            "avg_complexity": round(sum(f["complexity"] for f in functions) / max(1, len(functions)), 1)
        },
        "quality_score": score,
        "grade": get_grade(score),
        "smells": smells,
        "solid_violations": violations,
        "function_details": functions[:10],
        "class_details": classes[:10]
    }


def analyze_directory(
    dir_path: Path,
    recursive: bool = True,
    language: Optional[str] = None
) -> Dict:
    """Analyze all files in a directory."""
    results = []
    extensions = []

    if language:
        extensions = LANGUAGE_EXTENSIONS.get(language, [])
    else:
        for exts in LANGUAGE_EXTENSIONS.values():
            extensions.extend(exts)

    pattern = "**/*" if recursive else "*"

    for ext in extensions:
        for filepath in dir_path.glob(f"{pattern}{ext}"):
            if "node_modules" in str(filepath) or ".git" in str(filepath):
                continue
            result = analyze_file(filepath)
            if "error" not in result:
                results.append(result)

    if not results:
        return {"error": "No supported files found"}

    total_score = sum(r["quality_score"] for r in results)
    avg_score = total_score / len(results)
    total_smells = sum(len(r["smells"]) for r in results)
    total_violations = sum(len(r["solid_violations"]) for r in results)

    return {
        "directory": str(dir_path),
        "files_analyzed": len(results),
        "average_score": round(avg_score, 1),
        "overall_grade": get_grade(int(avg_score)),
        "total_code_smells": total_smells,
        "total_solid_violations": total_violations,
        "files": sorted(results, key=lambda x: x["quality_score"])
    }


def print_report(analysis: Dict) -> None:
    """Print human-readable analysis report."""
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return

    print("=" * 60)
    print("CODE QUALITY REPORT")
    print("=" * 60)

    if "file" in analysis:
        print(f"\nFile: {analysis['file']}")
        print(f"Language: {analysis['language']}")
        print(f"Quality Score: {analysis['quality_score']}/100 ({analysis['grade']})")

        metrics = analysis["metrics"]
        print(f"\nLines: {metrics['lines']['total']} ({metrics['lines']['code']} code, {metrics['lines']['comment']} comments)")
        print(f"Functions: {metrics['functions']}")
        print(f"Classes: {metrics['classes']}")
        print(f"Avg Complexity: {metrics['avg_complexity']}")

        if analysis["smells"]:
            print("\n--- CODE SMELLS ---")
            for smell in analysis["smells"][:10]:
                print(f"  [{smell['severity'].upper()}] {smell['message']} ({smell['location']})")

        if analysis["solid_violations"]:
            print("\n--- SOLID VIOLATIONS ---")
            for v in analysis["solid_violations"]:
                print(f"  [{v['principle']}] {v['message']}")
    else:
        print(f"\nDirectory: {analysis['directory']}")
        print(f"Files Analyzed: {analysis['files_analyzed']}")
        print(f"Average Score: {analysis['average_score']}/100 ({analysis['overall_grade']})")
        print(f"Total Code Smells: {analysis['total_code_smells']}")
        print(f"Total SOLID Violations: {analysis['total_solid_violations']}")

        print("\n--- FILES BY QUALITY ---")
        for f in analysis["files"][:10]:
            print(f"  {f['quality_score']:3d}/100 [{f['grade']}] {f['file']}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze code quality, smells, and SOLID violations"
    )
    parser.add_argument(
        "path",
        help="File or directory to analyze"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        default=True,
        help="Recursively analyze directories (default: true)"
    )
    parser.add_argument(
        "--language", "-l",
        choices=list(LANGUAGE_EXTENSIONS.keys()),
        help="Filter by programming language"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--output", "-o",
        help="Write output to file"
    )

    args = parser.parse_args()

    target = Path(args.path).resolve()

    if not target.exists():
        print(f"Error: Path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    if target.is_file():
        analysis = analyze_file(target)
    else:
        analysis = analyze_directory(target, args.recursive, args.language)

    if args.json:
        output = json.dumps(analysis, indent=2, default=str)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
    else:
        print_report(analysis)


if __name__ == "__main__":
    main()
