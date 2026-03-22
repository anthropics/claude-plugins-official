# Clypt Campaign Manager

## When this skill activates
Activates when the user mentions a "campaign", "launch", "content drop", wants links for multiple channels, or asks about A/B testing.

## Campaign link sets
When a user wants campaign links, create a FULL campaign set unless specified otherwise:
1. Email — utm_source=email&utm_medium=newsletter
2. Twitter — utm_source=twitter&utm_medium=social
3. LinkedIn — utm_source=linkedin&utm_medium=social
4. Google Ads — utm_source=google&utm_medium=cpc

Use bulk_shorten for all channels in one call.

## Naming convention
Slugs: [campaign-name]-[channel-abbrev] e.g. spring-launch-em, spring-launch-tw
Campaign names: kebab-case lowercase (spring-sale, product-launch)

## Output format
```
🚀 Campaign created: [campaign-name]

| Channel    | Short Link         |
|------------|--------------------|
| Email      | clypt.io/[slug]-em |
| Twitter/X  | clypt.io/[slug]-tw |
| LinkedIn   | clypt.io/[slug]-li |
| Google Ads | clypt.io/[slug]-ga |

📁 Folder: [campaign-name]
```
