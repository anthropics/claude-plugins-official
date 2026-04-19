#!/usr/bin/env python3
"""
Component Scaffolder for Design System Lead

Generates component documentation scaffolds including props table,
variants, states, accessibility requirements, and usage examples.

Uses ONLY Python standard library.

Usage:
    python component_scaffold.py --name Button --category primitive
    python component_scaffold.py --name DataTable --category pattern --variants "default,compact,striped"
    python component_scaffold.py --name Modal --category composite --json
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List


# Component category templates
CATEGORY_TEMPLATES = {
    "primitive": {
        "description": "A foundational UI element used as a building block for more complex components.",
        "default_variants": ["primary", "secondary", "tertiary"],
        "default_sizes": ["sm", "md", "lg"],
        "default_states": ["default", "hover", "active", "focus", "disabled"],
        "complexity": "low",
        "examples": ["Button", "Input", "Icon", "Badge", "Label", "Checkbox", "Radio"],
    },
    "composite": {
        "description": "A component composed of multiple primitives working together.",
        "default_variants": ["default", "bordered", "elevated"],
        "default_sizes": ["sm", "md", "lg"],
        "default_states": ["default", "loading", "empty", "error"],
        "complexity": "medium",
        "examples": ["Card", "Modal", "Dropdown", "Accordion", "Tabs", "Toast"],
    },
    "pattern": {
        "description": "A complex, reusable UI pattern solving a specific user interaction need.",
        "default_variants": ["default"],
        "default_sizes": ["default", "compact", "expanded"],
        "default_states": ["default", "loading", "empty", "error", "success"],
        "complexity": "high",
        "examples": ["DataTable", "Form", "Navigation", "SearchBar", "Pagination", "FileUpload"],
    },
}

# Common accessibility requirements by category
A11Y_REQUIREMENTS = {
    "primitive": [
        "Minimum touch target: 44x44px",
        "Visible focus ring on keyboard navigation (2px offset, high contrast)",
        "Color contrast meets WCAG AA (4.5:1 normal text, 3:1 large text)",
        "Supports keyboard interaction (Enter/Space for activation)",
    ],
    "composite": [
        "Focus trapping for overlays (modal, dropdown)",
        "Escape key closes/dismisses component",
        "aria-expanded for collapsible sections",
        "Screen reader announcements for state changes",
        "Visible focus ring on all interactive elements",
    ],
    "pattern": [
        "Full keyboard navigation for all interactive elements",
        "ARIA landmarks and roles for complex layouts",
        "Screen reader-friendly table headers and captions",
        "Loading states announced to assistive technology",
        "Error messages associated with inputs via aria-describedby",
    ],
}


def generate_props(name: str, category: str, variants: List[str], sizes: List[str]) -> List[Dict]:
    """Generate standard props table for a component."""
    props = [
        {"name": "variant", "type": f"'{\"' | '\".join(variants)}'", "default": f"'{variants[0]}'", "required": False, "description": f"Visual style variant"},
        {"name": "size", "type": f"'{\"' | '\".join(sizes)}'", "default": "'md'", "required": False, "description": "Component size"},
        {"name": "disabled", "type": "boolean", "default": "false", "required": False, "description": "Disables interaction"},
        {"name": "className", "type": "string", "default": "''", "required": False, "description": "Additional CSS class names"},
    ]

    # Category-specific props
    if category == "primitive":
        props.extend([
            {"name": "onClick", "type": "function", "default": "-", "required": False, "description": "Click event handler"},
            {"name": "aria-label", "type": "string", "default": "-", "required": False, "description": "Accessible label (required for icon-only)"},
        ])
    elif category == "composite":
        props.extend([
            {"name": "open", "type": "boolean", "default": "false", "required": False, "description": "Controls open/visible state"},
            {"name": "onClose", "type": "function", "default": "-", "required": False, "description": "Close event handler"},
            {"name": "children", "type": "ReactNode", "default": "-", "required": True, "description": "Component content"},
        ])
    elif category == "pattern":
        props.extend([
            {"name": "data", "type": "array", "default": "[]", "required": True, "description": "Data source"},
            {"name": "loading", "type": "boolean", "default": "false", "required": False, "description": "Loading state"},
            {"name": "onAction", "type": "function", "default": "-", "required": False, "description": "Primary action handler"},
            {"name": "emptyState", "type": "ReactNode", "default": "-", "required": False, "description": "Empty state content"},
        ])

    return props


def generate_tokens_map(name: str, category: str) -> Dict:
    """Generate design token mapping for the component."""
    base = {
        "background": f"{{component.{name.lower()}.bg}}",
        "text": f"{{color.foreground}}",
        "border": f"{{component.{name.lower()}.border}}",
        "borderRadius": f"{{component.{name.lower()}.radius}}",
        "padding": f"{{spacing.component-padding}}",
    }

    if category == "composite":
        base["shadow"] = f"{{component.{name.lower()}.shadow}}"
        base["overlay"] = "{color.overlay}"

    return base


def generate_scaffold(args) -> Dict:
    """Generate complete component scaffold."""
    category_template = CATEGORY_TEMPLATES.get(args.category, CATEGORY_TEMPLATES["primitive"])

    variants = args.variants.split(",") if args.variants else category_template["default_variants"]
    sizes = args.sizes.split(",") if args.sizes else category_template["default_sizes"]
    states = category_template["default_states"]

    props = generate_props(args.name, args.category, variants, sizes)
    tokens = generate_tokens_map(args.name, args.category)
    a11y = A11Y_REQUIREMENTS.get(args.category, A11Y_REQUIREMENTS["primitive"])

    scaffold = {
        "component": {
            "name": args.name,
            "category": args.category,
            "description": category_template["description"],
            "version": "0.1.0",
            "status": "draft",
            "created": datetime.now().strftime("%Y-%m-%d"),
        },
        "anatomy": {
            "slots": _generate_anatomy_slots(args.name, args.category),
        },
        "variants": [{"name": v, "description": f"{v.title()} visual style"} for v in variants],
        "sizes": [{"name": s, "description": f"{s.upper()} size variant"} for s in sizes],
        "states": [{"name": s, "description": f"{s.title()} interaction state"} for s in states],
        "props": props,
        "design_tokens": tokens,
        "accessibility": a11y,
        "usage_guidelines": {
            "do": _generate_do_guidelines(args.name, args.category),
            "dont": _generate_dont_guidelines(args.name, args.category),
        },
        "code_example": _generate_code_example(args.name, variants[0], sizes),
        "testing_checklist": [
            f"All {len(variants)} variants render correctly",
            f"All {len(sizes)} sizes render correctly",
            "All states visually distinct",
            "Keyboard navigation works",
            "Screen reader announces correctly",
            "Responsive behavior verified at all breakpoints",
            "Visual regression snapshot captured",
        ],
        "file_structure": {
            "component": f"components/{args.category}s/{args.name}/{args.name}.tsx",
            "styles": f"components/{args.category}s/{args.name}/{args.name}.styles.ts",
            "tests": f"components/{args.category}s/{args.name}/{args.name}.test.tsx",
            "stories": f"components/{args.category}s/{args.name}/{args.name}.stories.tsx",
            "docs": f"components/{args.category}s/{args.name}/README.md",
        },
    }

    return scaffold


def _generate_anatomy_slots(name: str, category: str) -> List[Dict]:
    """Generate component anatomy slots."""
    base_slots = [
        {"name": "root", "element": "div", "description": "Outermost wrapper"},
    ]

    if category == "primitive":
        base_slots.extend([
            {"name": "leadingIcon", "element": "span", "description": "Optional leading icon"},
            {"name": "label", "element": "span", "description": "Text content"},
            {"name": "trailingIcon", "element": "span", "description": "Optional trailing icon"},
        ])
    elif category == "composite":
        base_slots.extend([
            {"name": "header", "element": "div", "description": "Component header area"},
            {"name": "body", "element": "div", "description": "Main content area"},
            {"name": "footer", "element": "div", "description": "Actions or metadata area"},
        ])
    elif category == "pattern":
        base_slots.extend([
            {"name": "toolbar", "element": "div", "description": "Controls and filters"},
            {"name": "content", "element": "div", "description": "Primary content region"},
            {"name": "pagination", "element": "nav", "description": "Navigation controls"},
        ])

    return base_slots


def _generate_do_guidelines(name: str, category: str) -> List[str]:
    """Generate 'do' usage guidelines."""
    return [
        f"Use {name} for its intended purpose within the design system",
        "Apply design tokens instead of hardcoded values",
        "Include appropriate ARIA attributes for accessibility",
        "Test across all supported breakpoints and browsers",
        "Follow established naming conventions for variants",
    ]


def _generate_dont_guidelines(name: str, category: str) -> List[str]:
    """Generate 'don't' usage guidelines."""
    return [
        f"Don't use {name} as a substitute for a different component",
        "Don't override design tokens with inline styles",
        "Don't nest interactive elements inside interactive elements",
        "Don't remove focus indicators for keyboard users",
        "Don't create new variants without RFC approval",
    ]


def _generate_code_example(name: str, default_variant: str, sizes: List[str]) -> str:
    """Generate a code usage example."""
    return f"""import {{ {name} }} from '@design-system/components';

// Basic usage
<{name} variant="{default_variant}">{name} Content</{name}>

// With size
<{name} variant="{default_variant}" size="{sizes[1] if len(sizes) > 1 else sizes[0]}">{name}</{name}>

// Disabled
<{name} variant="{default_variant}" disabled>{name}</{name}>"""


def format_human_output(scaffold: Dict) -> str:
    """Format scaffold as human-readable markdown-style output."""
    c = scaffold["component"]
    lines = []
    lines.append("=" * 60)
    lines.append(f"COMPONENT SCAFFOLD: {c['name']}")
    lines.append("=" * 60)
    lines.append(f"\n  Category:    {c['category']}")
    lines.append(f"  Status:      {c['status']}")
    lines.append(f"  Description: {c['description']}")

    lines.append(f"\n  ANATOMY")
    for slot in scaffold["anatomy"]["slots"]:
        lines.append(f"    <{slot['element']}> {slot['name']} - {slot['description']}")

    lines.append(f"\n  VARIANTS: {', '.join(v['name'] for v in scaffold['variants'])}")
    lines.append(f"  SIZES:    {', '.join(s['name'] for s in scaffold['sizes'])}")
    lines.append(f"  STATES:   {', '.join(s['name'] for s in scaffold['states'])}")

    lines.append(f"\n  PROPS TABLE")
    lines.append(f"  {'Name':<15} {'Type':<25} {'Default':<12} {'Required':<10} Description")
    lines.append(f"  {'-'*15} {'-'*25} {'-'*12} {'-'*10} {'-'*20}")
    for p in scaffold["props"]:
        req = "Yes" if p["required"] else "No"
        ptype = str(p["type"])[:24]
        lines.append(f"  {p['name']:<15} {ptype:<25} {str(p['default']):<12} {req:<10} {p['description']}")

    lines.append(f"\n  DESIGN TOKENS")
    for k, v in scaffold["design_tokens"].items():
        lines.append(f"    {k}: {v}")

    lines.append(f"\n  ACCESSIBILITY")
    for req in scaffold["accessibility"]:
        lines.append(f"    - {req}")

    lines.append(f"\n  USAGE GUIDELINES")
    lines.append(f"  Do:")
    for item in scaffold["usage_guidelines"]["do"]:
        lines.append(f"    + {item}")
    lines.append(f"  Don't:")
    for item in scaffold["usage_guidelines"]["dont"]:
        lines.append(f"    - {item}")

    lines.append(f"\n  CODE EXAMPLE")
    lines.append(f"  ```")
    lines.append(scaffold["code_example"])
    lines.append(f"  ```")

    lines.append(f"\n  FILE STRUCTURE")
    for key, path in scaffold["file_structure"].items():
        lines.append(f"    {key}: {path}")

    lines.append(f"\n  TESTING CHECKLIST")
    for item in scaffold["testing_checklist"]:
        lines.append(f"    [ ] {item}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate design system component scaffold with docs, props, and a11y requirements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python component_scaffold.py --name Button --category primitive
  python component_scaffold.py --name Card --category composite --variants "default,bordered,elevated"
  python component_scaffold.py --name DataTable --category pattern --json
  python component_scaffold.py --name Modal --category composite --sizes "sm,md,lg,xl"
        """,
    )

    parser.add_argument("--name", "-n", required=True, help="Component name (PascalCase)")
    parser.add_argument("--category", "-c", choices=["primitive", "composite", "pattern"], required=True, help="Component category")
    parser.add_argument("--variants", "-v", help="Comma-separated variant names")
    parser.add_argument("--sizes", "-s", help="Comma-separated size names")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    scaffold = generate_scaffold(args)

    if args.json:
        print(json.dumps(scaffold, indent=2))
    else:
        print(format_human_output(scaffold))


if __name__ == "__main__":
    main()
