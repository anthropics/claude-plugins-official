---
description: Generate a QR code for any Clypt link
argument-hint: "[short-code] [--size px] [--color hex] [--bg hex] [--format png|svg]"
allowed-tools: mcp__clypt__generate_qr_code
---
Generate a QR code using Clypt for the link in $ARGUMENTS.

Parse options:
- --size → size in pixels (default 512)
- --color → foreground hex colour (default #000000)
- --bg → background hex colour (default #ffffff)
- --format → png or svg (default png)

Call generate_qr_code with the parsed options.

Return the QR code URL and note: "This QR code is dynamic — you can update the destination anytime without reprinting."
