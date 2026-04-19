#!/usr/bin/env python3
"""
User Journey Mapper

Creates structured user journey maps from stage definitions.
Identifies pain points, emotional curves, and opportunity areas.

Uses ONLY Python standard library.

Usage:
    python journey_mapper.py --template saas
    python journey_mapper.py --stages stages.json
    python journey_mapper.py --template ecommerce --json
"""

import argparse
import json
import sys
from typing import Dict, List


# Pre-built journey templates
JOURNEY_TEMPLATES = {
    "saas": {
        "name": "SaaS Product Journey",
        "persona": "Product Team User",
        "goal": "Successfully adopt and get value from the product",
        "stages": [
            {
                "name": "Awareness",
                "actions": ["Searches for solution online", "Reads blog post or review", "Sees ad or recommendation"],
                "touchpoints": ["Google Search", "Blog", "Social Media", "Peer referral"],
                "emotions": {"score": 3, "label": "Curious but skeptical"},
                "pain_points": ["Too many options", "Hard to tell products apart", "Unclear pricing"],
                "opportunities": ["SEO-optimized comparison content", "Clear value proposition on landing page"],
            },
            {
                "name": "Evaluation",
                "actions": ["Visits website", "Reads features page", "Compares with competitors", "Watches demo"],
                "touchpoints": ["Website", "Demo video", "Pricing page", "Competitor sites"],
                "emotions": {"score": 4, "label": "Interested, comparing options"},
                "pain_points": ["Complex pricing tiers", "No free trial visible", "Feature comparison is hard"],
                "opportunities": ["Interactive product tour", "Side-by-side comparison tool", "Social proof placement"],
            },
            {
                "name": "Signup",
                "actions": ["Creates account", "Enters payment info", "Verifies email"],
                "touchpoints": ["Registration form", "Email", "Payment processor"],
                "emotions": {"score": 3, "label": "Cautious, wants quick setup"},
                "pain_points": ["Too many form fields", "Unclear what happens after signup", "Forced credit card"],
                "opportunities": ["Single-field signup", "Show value before requiring payment", "Progress indicator"],
            },
            {
                "name": "Onboarding",
                "actions": ["Completes setup wizard", "Imports data", "Invites team members", "Completes first task"],
                "touchpoints": ["Setup wizard", "Import tool", "Email invites", "In-app tutorial"],
                "emotions": {"score": 2, "label": "Overwhelmed, needs guidance"},
                "pain_points": ["Too many steps", "Data import fails", "No clear next step", "Empty state is confusing"],
                "opportunities": ["Guided quick-start (<5 min to value)", "Pre-populated sample data", "Contextual tips"],
            },
            {
                "name": "Adoption",
                "actions": ["Uses core features daily", "Discovers advanced features", "Customizes workflow"],
                "touchpoints": ["Product UI", "Help center", "In-app notifications", "Email tips"],
                "emotions": {"score": 4, "label": "Gaining confidence, seeing value"},
                "pain_points": ["Hard to discover features", "Missing integrations", "Performance issues"],
                "opportunities": ["Feature discovery prompts", "Integration marketplace", "Workflow templates"],
            },
            {
                "name": "Advocacy",
                "actions": ["Recommends to peers", "Writes review", "Shares on social", "Expands usage"],
                "touchpoints": ["Review sites", "Social media", "Word of mouth", "Referral program"],
                "emotions": {"score": 5, "label": "Satisfied, wants to share"},
                "pain_points": ["No easy way to refer", "No recognition for loyalty", "Feature requests ignored"],
                "opportunities": ["Referral program with rewards", "Customer advisory board", "Public feature roadmap"],
            },
        ],
    },
    "ecommerce": {
        "name": "E-commerce Purchase Journey",
        "persona": "Online Shopper",
        "goal": "Find and purchase the right product at a good price",
        "stages": [
            {
                "name": "Discovery",
                "actions": ["Searches for product", "Browses categories", "Sees recommendation"],
                "touchpoints": ["Search engine", "Social media", "Email newsletter", "Marketplace"],
                "emotions": {"score": 3, "label": "Browsing, open to options"},
                "pain_points": ["Search returns irrelevant results", "Category structure is confusing"],
                "opportunities": ["Personalized recommendations", "Smart search with filters"],
            },
            {
                "name": "Consideration",
                "actions": ["Views product details", "Reads reviews", "Compares options", "Checks sizing/specs"],
                "touchpoints": ["Product page", "Reviews section", "Size guide", "Comparison tool"],
                "emotions": {"score": 4, "label": "Interested, needs reassurance"},
                "pain_points": ["Insufficient product images", "Fake or unhelpful reviews", "No size guidance"],
                "opportunities": ["360-degree product views", "Verified purchase reviews", "AR try-on"],
            },
            {
                "name": "Purchase",
                "actions": ["Adds to cart", "Applies coupon", "Enters shipping info", "Completes payment"],
                "touchpoints": ["Cart", "Checkout flow", "Payment processor", "Order confirmation"],
                "emotions": {"score": 3, "label": "Anxious about commitment"},
                "pain_points": ["Unexpected shipping costs", "Too many checkout steps", "Limited payment options"],
                "opportunities": ["One-page checkout", "Free shipping threshold", "Guest checkout option"],
            },
            {
                "name": "Delivery",
                "actions": ["Tracks order", "Receives package", "Inspects product"],
                "touchpoints": ["Tracking page", "Email updates", "SMS notifications", "Package"],
                "emotions": {"score": 4, "label": "Excited, anticipating"},
                "pain_points": ["No tracking updates", "Delayed delivery", "Damaged packaging"],
                "opportunities": ["Real-time delivery tracking", "Proactive delay notifications"],
            },
            {
                "name": "Post-Purchase",
                "actions": ["Uses product", "Writes review", "Contacts support if needed", "Considers reorder"],
                "touchpoints": ["Product", "Review prompt email", "Support chat", "Reorder email"],
                "emotions": {"score": 4, "label": "Satisfied or seeking resolution"},
                "pain_points": ["Product doesn't match description", "Difficult return process"],
                "opportunities": ["Easy self-service returns", "Post-purchase care emails", "Loyalty program"],
            },
        ],
    },
    "mobile_app": {
        "name": "Mobile App Journey",
        "persona": "Mobile-First User",
        "goal": "Download, learn, and integrate app into daily routine",
        "stages": [
            {
                "name": "Discovery",
                "actions": ["Finds app in store", "Reads description and reviews", "Views screenshots"],
                "touchpoints": ["App Store", "Google Play", "Social media", "Word of mouth"],
                "emotions": {"score": 3, "label": "Curious, evaluating quickly"},
                "pain_points": ["Too many similar apps", "Misleading screenshots", "Bad reviews"],
                "opportunities": ["App Store optimization", "Video preview", "Respond to reviews"],
            },
            {
                "name": "Install & First Open",
                "actions": ["Downloads app", "Opens for first time", "Grants permissions", "Views onboarding"],
                "touchpoints": ["App Store", "System permissions", "Onboarding screens"],
                "emotions": {"score": 3, "label": "Impatient, wants quick value"},
                "pain_points": ["Large download size", "Too many permission requests", "Long onboarding"],
                "opportunities": ["<50MB download", "Progressive permissions", "3-screen onboarding max"],
            },
            {
                "name": "First Value",
                "actions": ["Completes first core action", "Sees result", "Understands benefit"],
                "touchpoints": ["Core feature", "Success state", "Tutorial overlay"],
                "emotions": {"score": 4, "label": "Pleasantly surprised or frustrated"},
                "pain_points": ["Can't find main feature", "First action fails", "No clear path"],
                "opportunities": ["Guided first action", "Instant gratification moment", "Sample content"],
            },
            {
                "name": "Habit Formation",
                "actions": ["Returns within 24 hours", "Uses 3+ times per week", "Enables notifications"],
                "touchpoints": ["Push notifications", "App icon", "Widgets", "Email digest"],
                "emotions": {"score": 4, "label": "Building routine"},
                "pain_points": ["Annoying notifications", "App is slow", "Battery/data concerns"],
                "opportunities": ["Smart notification timing", "Offline mode", "Streaks or progress tracking"],
            },
            {
                "name": "Power Usage",
                "actions": ["Discovers advanced features", "Customizes settings", "Shares with others"],
                "touchpoints": ["Settings", "Share flow", "Advanced features", "In-app community"],
                "emotions": {"score": 5, "label": "Invested, advocates"},
                "pain_points": ["Feature bloat", "Settings are buried", "No social features"],
                "opportunities": ["Progressive disclosure", "Share rewards", "Community features"],
            },
        ],
    },
}


def calculate_journey_metrics(stages: List[Dict]) -> Dict:
    """Calculate journey health metrics."""
    emotion_scores = [s["emotions"]["score"] for s in stages]

    # Find biggest drops
    drops = []
    for i in range(1, len(emotion_scores)):
        diff = emotion_scores[i] - emotion_scores[i - 1]
        if diff < 0:
            drops.append({
                "from_stage": stages[i - 1]["name"],
                "to_stage": stages[i]["name"],
                "drop": abs(diff),
            })

    drops.sort(key=lambda x: -x["drop"])

    # Pain point severity
    all_pain_points = []
    for stage in stages:
        for pp in stage.get("pain_points", []):
            all_pain_points.append({"stage": stage["name"], "pain_point": pp})

    # Opportunity count
    total_opportunities = sum(len(s.get("opportunities", [])) for s in stages)

    return {
        "total_stages": len(stages),
        "avg_emotion_score": round(sum(emotion_scores) / len(emotion_scores), 1),
        "lowest_emotion_stage": stages[emotion_scores.index(min(emotion_scores))]["name"],
        "highest_emotion_stage": stages[emotion_scores.index(max(emotion_scores))]["name"],
        "biggest_drops": drops[:3],
        "total_pain_points": len(all_pain_points),
        "total_opportunities": total_opportunities,
        "critical_stage": stages[emotion_scores.index(min(emotion_scores))]["name"],
    }


def format_human_output(journey: Dict, metrics: Dict) -> str:
    """Format journey map as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"USER JOURNEY MAP: {journey['name']}")
    lines.append("=" * 60)
    lines.append(f"\n  Persona: {journey['persona']}")
    lines.append(f"  Goal:    {journey['goal']}")

    # Emotion curve visualization
    lines.append(f"\n  EMOTION CURVE")
    lines.append("  " + "-" * 50)
    for stage in journey["stages"]:
        score = stage["emotions"]["score"]
        bar = "*" * (score * 6)
        label = stage["emotions"]["label"]
        lines.append(f"  {stage['name']:<15} {'|' + bar:<32} {score}/5 - {label}")

    # Stage details
    for stage in journey["stages"]:
        lines.append(f"\n  STAGE: {stage['name'].upper()}")
        lines.append("  " + "-" * 40)

        lines.append(f"  Actions:")
        for action in stage["actions"]:
            lines.append(f"    - {action}")

        lines.append(f"  Touchpoints:")
        for tp in stage["touchpoints"]:
            lines.append(f"    - {tp}")

        lines.append(f"  Pain Points:")
        for pp in stage.get("pain_points", []):
            lines.append(f"    ! {pp}")

        lines.append(f"  Opportunities:")
        for opp in stage.get("opportunities", []):
            lines.append(f"    > {opp}")

    # Metrics summary
    lines.append(f"\n  JOURNEY HEALTH METRICS")
    lines.append("  " + "-" * 50)
    lines.append(f"  Avg emotion score:   {metrics['avg_emotion_score']}/5")
    lines.append(f"  Lowest point:        {metrics['lowest_emotion_stage']}")
    lines.append(f"  Highest point:       {metrics['highest_emotion_stage']}")
    lines.append(f"  Total pain points:   {metrics['total_pain_points']}")
    lines.append(f"  Total opportunities: {metrics['total_opportunities']}")

    if metrics["biggest_drops"]:
        lines.append(f"\n  BIGGEST EMOTION DROPS (prioritize these transitions)")
        for drop in metrics["biggest_drops"]:
            lines.append(f"    {drop['from_stage']} -> {drop['to_stage']} (dropped {drop['drop']} points)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Create structured user journey maps with emotion curves and opportunity analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use a pre-built template
  python journey_mapper.py --template saas
  python journey_mapper.py --template ecommerce
  python journey_mapper.py --template mobile_app

  # Load custom stages from JSON
  python journey_mapper.py --stages my_journey.json

  # JSON output
  python journey_mapper.py --template saas --json

Available templates: saas, ecommerce, mobile_app
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--template", "-t", choices=list(JOURNEY_TEMPLATES.keys()), help="Use pre-built journey template")
    group.add_argument("--stages", "-s", help="Path to custom stages JSON file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.template:
        journey = JOURNEY_TEMPLATES[args.template]
    else:
        with open(args.stages, "r") as f:
            journey = json.load(f)

    metrics = calculate_journey_metrics(journey["stages"])

    if args.json:
        output = {
            "journey": journey,
            "metrics": metrics,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_human_output(journey, metrics))


if __name__ == "__main__":
    main()
