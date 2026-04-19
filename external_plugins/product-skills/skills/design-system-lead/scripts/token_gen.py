#!/usr/bin/env python3
"""
Design Token Generator for Design System Lead

Generates a three-tier design token system (primitive -> semantic -> component)
from a brand color input. Outputs in JSON, CSS, or SCSS format.

Uses ONLY Python standard library.

Usage:
    python token_gen.py --color "#0066CC"
    python token_gen.py --color "#0066CC" --format css --output dist/
    python token_gen.py --color "#0066CC" --format scss --tiers all --json
"""

import argparse
import colorsys
import json
import math
import os
import sys
from typing import Dict, List, Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex string."""
    return "#{:02x}{:02x}{:02x}".format(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def adjust_hue(hex_color: str, degrees: float) -> str:
    """Rotate hue of a hex color by given degrees."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360) % 1.0
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


def generate_color_scale(hex_color: str) -> Dict[str, str]:
    """Generate a 10-step color scale from a base color."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    scale = {}
    steps = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]

    for step in steps:
        if step < 500:
            new_v = 0.95 + (1.0 - 0.95) * ((500 - step) / 500)
            new_s = s * (0.2 + 0.8 * (step / 500))
        elif step == 500:
            new_v = v
            new_s = s
        else:
            factor = (step - 500) / 400
            new_v = v * (1 - factor * 0.7)
            new_s = min(1.0, s * (1 + factor * 0.3))

        nr, ng, nb = colorsys.hsv_to_rgb(h, new_s, new_v)
        scale[str(step)] = rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))

    return scale


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    def relative_luminance(hex_c: str) -> float:
        r, g, b = hex_to_rgb(hex_c)
        rs, gs, bs = r / 255, g / 255, b / 255
        rl = rs / 12.92 if rs <= 0.03928 else ((rs + 0.055) / 1.055) ** 2.4
        gl = gs / 12.92 if gs <= 0.03928 else ((gs + 0.055) / 1.055) ** 2.4
        bl = bs / 12.92 if bs <= 0.03928 else ((bs + 0.055) / 1.055) ** 2.4
        return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl

    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def generate_primitive_tokens(brand_color: str) -> Dict:
    """Generate primitive (raw value) tokens."""
    secondary = adjust_hue(brand_color, 180)
    accent = adjust_hue(brand_color, 30)

    return {
        "color": {
            "blue": generate_color_scale(brand_color),
            "secondary": generate_color_scale(secondary),
            "accent": generate_color_scale(accent),
            "gray": {
                "50": "#f9fafb", "100": "#f3f4f6", "200": "#e5e7eb",
                "300": "#d1d5db", "400": "#9ca3af", "500": "#6b7280",
                "600": "#4b5563", "700": "#374151", "800": "#1f2937", "900": "#111827",
            },
            "white": "#ffffff",
            "black": "#000000",
            "green": {"500": "#10b981", "600": "#059669", "700": "#047857"},
            "red": {"500": "#ef4444", "600": "#dc2626", "700": "#b91c1c"},
            "yellow": {"500": "#f59e0b", "600": "#d97706", "700": "#b45309"},
        },
        "spacing": {str(i): f"{i * 4}px" for i in range(0, 17)},
        "fontSize": {
            "xs": "12px", "sm": "14px", "base": "16px", "lg": "18px",
            "xl": "20px", "2xl": "24px", "3xl": "30px", "4xl": "36px", "5xl": "48px",
        },
        "fontWeight": {
            "light": "300", "normal": "400", "medium": "500",
            "semibold": "600", "bold": "700", "extrabold": "800",
        },
        "borderRadius": {
            "none": "0", "sm": "4px", "md": "8px", "lg": "12px",
            "xl": "16px", "2xl": "24px", "full": "9999px",
        },
        "lineHeight": {
            "tight": "1.25", "snug": "1.375", "normal": "1.5",
            "relaxed": "1.625", "loose": "2",
        },
    }


def generate_semantic_tokens(primitives: Dict) -> Dict:
    """Generate semantic (purpose-based alias) tokens."""
    return {
        "color": {
            "primary": "{color.blue.500}",
            "primary-hover": "{color.blue.600}",
            "primary-active": "{color.blue.700}",
            "secondary": "{color.secondary.500}",
            "secondary-hover": "{color.secondary.600}",
            "background": "{color.white}",
            "background-subtle": "{color.gray.50}",
            "background-muted": "{color.gray.100}",
            "foreground": "{color.gray.900}",
            "foreground-muted": "{color.gray.600}",
            "foreground-subtle": "{color.gray.400}",
            "border": "{color.gray.200}",
            "border-strong": "{color.gray.300}",
            "success": "{color.green.500}",
            "success-hover": "{color.green.600}",
            "error": "{color.red.500}",
            "error-hover": "{color.red.600}",
            "warning": "{color.yellow.500}",
            "warning-hover": "{color.yellow.600}",
            "info": "{color.blue.500}",
            "overlay": "rgba(0, 0, 0, 0.5)",
            "focus-ring": "{color.blue.300}",
        },
        "spacing": {
            "xs": "{spacing.1}",
            "sm": "{spacing.2}",
            "md": "{spacing.4}",
            "lg": "{spacing.6}",
            "xl": "{spacing.8}",
            "2xl": "{spacing.12}",
            "3xl": "{spacing.16}",
            "component-padding": "{spacing.4}",
            "section-gap": "{spacing.8}",
            "page-margin": "{spacing.6}",
        },
        "typography": {
            "heading": {"fontFamily": "Inter, system-ui, sans-serif", "fontWeight": "{fontWeight.bold}"},
            "body": {"fontFamily": "Inter, system-ui, sans-serif", "fontWeight": "{fontWeight.normal}"},
            "mono": {"fontFamily": "JetBrains Mono, monospace", "fontWeight": "{fontWeight.normal}"},
        },
    }


def generate_component_tokens(semantics: Dict) -> Dict:
    """Generate component-scoped tokens."""
    return {
        "button": {
            "primary": {
                "bg": "{color.primary}",
                "bg-hover": "{color.primary-hover}",
                "bg-active": "{color.primary-active}",
                "text": "{color.white}",
                "border": "transparent",
                "radius": "{borderRadius.md}",
            },
            "secondary": {
                "bg": "{color.background}",
                "bg-hover": "{color.background-subtle}",
                "text": "{color.foreground}",
                "border": "{color.border}",
                "radius": "{borderRadius.md}",
            },
            "destructive": {
                "bg": "{color.error}",
                "bg-hover": "{color.error-hover}",
                "text": "{color.white}",
                "border": "transparent",
                "radius": "{borderRadius.md}",
            },
            "size-sm": {"height": "32px", "paddingX": "12px", "fontSize": "{fontSize.sm}"},
            "size-md": {"height": "40px", "paddingX": "16px", "fontSize": "{fontSize.base}"},
            "size-lg": {"height": "48px", "paddingX": "20px", "fontSize": "{fontSize.lg}"},
        },
        "input": {
            "bg": "{color.background}",
            "bg-disabled": "{color.background-muted}",
            "border": "{color.border}",
            "border-focus": "{color.primary}",
            "border-error": "{color.error}",
            "text": "{color.foreground}",
            "placeholder": "{color.foreground-subtle}",
            "radius": "{borderRadius.md}",
            "size-sm": {"height": "32px", "paddingX": "12px", "fontSize": "{fontSize.sm}"},
            "size-md": {"height": "40px", "paddingX": "16px", "fontSize": "{fontSize.base}"},
            "size-lg": {"height": "48px", "paddingX": "20px", "fontSize": "{fontSize.lg}"},
        },
        "card": {
            "bg": "{color.background}",
            "border": "{color.border}",
            "radius": "{borderRadius.lg}",
            "padding": "{spacing.component-padding}",
            "shadow": "0 1px 3px rgba(0,0,0,0.1)",
        },
        "modal": {
            "bg": "{color.background}",
            "overlay": "{color.overlay}",
            "radius": "{borderRadius.xl}",
            "padding": "{spacing.section-gap}",
            "shadow": "0 20px 60px rgba(0,0,0,0.15)",
        },
    }


def resolve_references(tokens: Dict, primitives: Dict) -> Dict:
    """Resolve {reference} tokens to actual values for export."""
    flat_primitives = {}

    def flatten(obj, prefix=""):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flatten(v, key)
            else:
                flat_primitives[key] = v

    flatten(primitives)

    def resolve(obj):
        if isinstance(obj, str):
            if obj.startswith("{") and obj.endswith("}"):
                ref = obj[1:-1]
                return flat_primitives.get(ref, obj)
            return obj
        elif isinstance(obj, dict):
            return {k: resolve(v) for k, v in obj.items()}
        return obj

    return resolve(tokens)


def export_css(tokens: Dict, tier_name: str) -> str:
    """Export tokens as CSS custom properties."""
    lines = [f"/* {tier_name} tokens */", ":root {"]

    def flatten(obj, prefix):
        for k, v in obj.items():
            key = f"{prefix}-{k}"
            if isinstance(v, dict):
                flatten(v, key)
            else:
                lines.append(f"  --{key}: {v};")

    flatten(tokens, tier_name)
    lines.append("}")
    return "\n".join(lines)


def export_scss(tokens: Dict, tier_name: str) -> str:
    """Export tokens as SCSS variables."""
    lines = [f"// {tier_name} tokens"]

    def flatten(obj, prefix):
        for k, v in obj.items():
            key = f"{prefix}-{k}"
            if isinstance(v, dict):
                flatten(v, key)
            else:
                lines.append(f"${key}: {v};")

    flatten(tokens, tier_name)
    return "\n".join(lines)


def format_human_output(all_tokens: Dict, brand_color: str) -> str:
    """Format token summary for human-readable output."""
    lines = []
    lines.append("=" * 60)
    lines.append("DESIGN TOKEN SYSTEM")
    lines.append("=" * 60)
    lines.append(f"\n  Brand Color:  {brand_color}")
    lines.append(f"  Architecture: Three-tier (primitive -> semantic -> component)")

    for tier_name, tier_data in all_tokens.items():
        count = sum(1 for _ in _count_leaves(tier_data))
        lines.append(f"\n  {tier_name.upper()} TOKENS ({count} values)")
        lines.append("  " + "-" * 40)
        for category in tier_data:
            if isinstance(tier_data[category], dict):
                sub_count = sum(1 for _ in _count_leaves(tier_data[category]))
                lines.append(f"    {category}: {sub_count} tokens")
            else:
                lines.append(f"    {category}: {tier_data[category]}")

    # Contrast check
    primitives = all_tokens.get("primitive", {})
    blue_scale = primitives.get("color", {}).get("blue", {})
    if "500" in blue_scale and "900" in blue_scale:
        cr_white = contrast_ratio(blue_scale["500"], "#ffffff")
        cr_black = contrast_ratio(blue_scale["500"], "#000000")
        lines.append(f"\n  WCAG CONTRAST CHECK (primary-500)")
        lines.append(f"    vs white: {cr_white}:1 {'PASS AA' if cr_white >= 4.5 else 'FAIL AA'}")
        lines.append(f"    vs black: {cr_black}:1 {'PASS AA' if cr_black >= 4.5 else 'FAIL AA'}")

    return "\n".join(lines)


def _count_leaves(obj):
    """Yield leaf values from nested dict."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _count_leaves(v)
    else:
        yield obj


def main():
    parser = argparse.ArgumentParser(
        description="Generate three-tier design token system from brand color",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python token_gen.py --color "#0066CC"
  python token_gen.py --color "#0066CC" --format css --output dist/
  python token_gen.py --color "#8B4513" --tiers primitive --json
  python token_gen.py --color "#FF6B6B" --format scss
        """,
    )

    parser.add_argument("--color", "-c", default="#0066CC", help="Brand color in hex (default: #0066CC)")
    parser.add_argument("--format", "-f", choices=["json", "css", "scss", "summary"], default="summary", help="Output format (default: summary)")
    parser.add_argument("--tiers", "-t", choices=["all", "primitive", "semantic", "component"], default="all", help="Token tiers to generate (default: all)")
    parser.add_argument("--output", "-o", help="Output directory for generated files")
    parser.add_argument("--json", action="store_true", help="Shortcut for --format json")

    args = parser.parse_args()

    if args.json:
        args.format = "json"

    brand_color = args.color.strip("'\"")

    # Generate tokens
    primitives = generate_primitive_tokens(brand_color)
    semantics = generate_semantic_tokens(primitives)
    components = generate_component_tokens(semantics)

    all_tokens = {}
    if args.tiers in ("all", "primitive"):
        all_tokens["primitive"] = primitives
    if args.tiers in ("all", "semantic"):
        all_tokens["semantic"] = semantics
    if args.tiers in ("all", "component"):
        all_tokens["component"] = components

    # Output
    if args.format == "json":
        print(json.dumps(all_tokens, indent=2))
    elif args.format == "summary":
        print(format_human_output(all_tokens, brand_color))
    elif args.format in ("css", "scss"):
        export_fn = export_css if args.format == "css" else export_scss
        resolved_primitives = primitives
        resolved_semantics = resolve_references(semantics, primitives)
        resolved_components = resolve_references(components, {**primitives, **semantics})

        output_parts = []
        if args.tiers in ("all", "primitive"):
            output_parts.append(export_fn(resolved_primitives, "primitive"))
        if args.tiers in ("all", "semantic"):
            output_parts.append(export_fn(resolved_semantics, "semantic"))
        if args.tiers in ("all", "component"):
            output_parts.append(export_fn(resolved_components, "component"))

        result = "\n\n".join(output_parts)

        if args.output:
            os.makedirs(args.output, exist_ok=True)
            ext = "css" if args.format == "css" else "scss"
            filepath = os.path.join(args.output, f"tokens.{ext}")
            with open(filepath, "w") as f:
                f.write(result)
            print(f"Tokens written to {filepath}")
        else:
            print(result)


if __name__ == "__main__":
    main()
