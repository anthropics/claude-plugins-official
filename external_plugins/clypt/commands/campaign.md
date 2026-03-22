---
description: Create a full campaign link set across all channels (email, Twitter, LinkedIn, Google Ads)
argument-hint: "[url] [campaign-name] [--channels email,twitter,linkedin,google]"
allowed-tools: mcp__clypt__bulk_shorten, mcp__clypt__manage_tags, mcp__clypt__manage_folders
---
Create a full campaign link set using Clypt for the URL and campaign name in $ARGUMENTS.

Default channels: email, twitter, linkedin, google (unless --channels flag specifies others)

For each channel, create a link with:
- Slug: [campaign-name]-[channel-abbrev] (e.g. spring-launch-em, spring-launch-tw, spring-launch-li, spring-launch-ga)
- UTMs:
  - email → source=email, medium=newsletter
  - twitter → source=twitter, medium=social
  - linkedin → source=linkedin, medium=social
  - google → source=google, medium=cpc
  - facebook → source=facebook, medium=social
- Tag: campaign name
- Folder: campaign name

Use bulk_shorten to create all links in one call.

Present results as:
```
🚀 Campaign created: [campaign-name]

| Channel    | Short Link              |
|------------|-------------------------|
| Email      | [shortUrl for email]    |
| Twitter/X  | [shortUrl for twitter]  |
| LinkedIn   | [shortUrl for linkedin] |
| Google Ads | [shortUrl for google]   |

📁 Folder: [campaign-name]
📊 Track at clypt.io/dashboard
```
