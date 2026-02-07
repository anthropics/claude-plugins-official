# Leadyen Search

Search for B2B leads by company, role, industry, or other criteria.

## Usage

```
/leadyen-search [query] [--role title] [--company name] [--industry type] [--size range]
```

## What This Does

1. Searches Leadyen's B2B database
2. Returns matching contacts with verified emails
3. Shows company info, seniority, and contact details
4. Allows filtering by multiple criteria

## Example Output

```
Lead Search Results

Query: "Marketing Director" at SaaS companies, 50-200 employees
Found: 234 leads

#  Name                Title                    Company           Email Status
───────────────────────────────────────────────────────────────────────────────
1  Sarah Johnson       VP of Marketing          TechFlow Inc      ✅ Verified
2  Mike Chen           Marketing Director       CloudBase         ✅ Verified
3  Emma Williams       Head of Growth           DataSync          ✅ Verified
4  James Miller        CMO                      AppScale          ⚠️ Catch-all
5  Lisa Anderson       Director of Marketing    SaaSify           ✅ Verified

Company Insights (TechFlow Inc):
├── Industry: B2B SaaS
├── Employees: 85
├── Revenue: $8-10M
├── Tech Stack: HubSpot, Salesforce, Slack
├── Recent Funding: Series A ($5M, 6 months ago)
└── Hiring: 3 marketing roles open

Actions:
- /leadyen-enrich [email] - Get full contact details
- /leadyen-sequence - Add to outreach sequence
```
