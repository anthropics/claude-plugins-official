# Visual Prompt Generation Guide

## Purpose

Every content piece in the Recruitin Growth Engine includes a visual prompt specification. This guide defines the format and best practices for generating prompts compatible with PiAPI, Canva, Midjourney, and DALL-E.

## Standard Visual Prompt Format

```yaml
visual_prompt:
  platform: [LinkedIn | Meta | Both]
  format: [1:1 | 4:5 | 16:9 | 9:16 | Carousel]
  dimensions: [WxH in pixels]
  style: [Photography | Illustration | Typography | Data Viz | Mixed Media]
  subject: "[Primary visual element description]"
  background: "[Background description or color]"
  brand_colors:
    primary: "[Hex code]"
    secondary: "[Hex code]"
    accent: "[Hex code]"
  text_overlay:
    headline: "[Text to display]"
    subtext: "[Supporting text]"
    position: [top-left | center | bottom-right | etc.]
  mood: "[Emotional tone]"
  style_references: "[Reference images or styles]"
  tool: [PiAPI | Canva | Midjourney | DALL-E]
  negative_prompts: "[What to avoid]"
```

## Platform-Specific Dimensions

| Platform | Format | Dimensions | Use Case |
|----------|--------|-----------|----------|
| LinkedIn | 1:1 | 1080x1080 | Feed posts |
| LinkedIn | 1.91:1 | 1200x628 | Link shares, articles |
| LinkedIn | Carousel | 1080x1080 per slide | Educational content |
| Meta Feed | 4:5 | 1080x1350 | Primary ad format |
| Meta Stories | 9:16 | 1080x1920 | Stories and Reels |
| Meta Carousel | 1:1 | 1080x1080 per card | Multi-image ads |

## Style Guidelines Per Campaign Type

### Authority Campaigns (Recruitin Brand)

```
Default Palette:
  Primary: [Recruitin brand color]
  Secondary: #1a1a2e (Dark navy)
  Accent: #e94560 (Bold accent)
  Background: #f5f5f5 (Light neutral)

Photography Style:
- Natural lighting, candid moments
- Dutch workplace environments
- Diverse professionals
- No stock photo cliches (pointing at screens, fake handshakes)

Typography:
- Clean sans-serif for headlines
- High contrast text on image
- Max 7 words on any single visual
```

### Performance Campaigns (Client Vacancies)

```
Adapt to client brand palette. If unavailable, use:
  Primary: Client's dominant brand color
  Secondary: Neutral complement
  Accent: High-visibility CTA color (orange or green)

Photography Style:
- Authentic workplace photography when available
- Role-specific environments (office, warehouse, lab, etc.)
- Show the actual team when possible
- Avoid generic corporate imagery

Typography:
- Job title prominently displayed
- Key benefit as secondary text
- Company logo in corner
- CTA button styled element
```

## Prompt Construction by Tool

### For Midjourney / PiAPI

```
[Subject description], [style], [mood], [lighting], [camera angle],
[color palette reference], [quality modifiers] --ar [aspect ratio]

Example:
"Dutch professional woman reviewing data on laptop in modern Amsterdam
office, natural window lighting, warm and focused mood, shallow depth
of field, editorial photography style, brand colors navy and coral
accents --ar 4:5 --v 6"
```

### For DALL-E

```
"Create a [format] image in [style] style showing [subject].
The mood should be [mood]. Use [color description] as the dominant
colors. The setting is [environment]. Include [specific elements].
Avoid [negative elements]."

Example:
"Create a 4:5 portrait image in modern editorial photography style
showing a diverse team of three professionals collaborating around
a standing desk in a bright, plant-filled office. The mood should
be energetic and collaborative. Use warm tones with navy blue accents.
Include natural window lighting and a laptop screen visible. Avoid
stock photo poses and artificial smiling."
```

### For Canva (Template Instructions)

```
Template Type: [Social Media Post / Ad / Carousel]
Layout: [Grid / Centered / Split / Minimal]
Background: [Solid color / Gradient / Image]
Elements:
  - Headline: "[Text]" | Font: [Style] | Size: [Large/Medium] | Color: [Hex]
  - Body: "[Text]" | Font: [Style] | Size: [Small/Medium] | Color: [Hex]
  - Logo: [Position] | Size: [Small/Medium]
  - CTA Button: "[Text]" | Color: [Hex] | Position: [Bottom center/right]
  - Image: [Description or upload reference]
Brand Kit: Apply [client name] or Recruitin brand kit
```

## Quality Checklist for Visual Prompts

- [ ] Dimensions match the target platform
- [ ] Brand colors are explicitly specified (hex codes)
- [ ] Text overlay is readable (contrast ratio > 4.5:1)
- [ ] Max 20% text coverage for Meta ads (recommendation, no longer hard rule)
- [ ] No discriminatory visual elements (age, gender, ethnicity stereotyping)
- [ ] Mood aligns with campaign phase (authority vs. urgency vs. warmth)
- [ ] Tool recommendation matches visual complexity
- [ ] Negative prompts exclude unwanted elements
