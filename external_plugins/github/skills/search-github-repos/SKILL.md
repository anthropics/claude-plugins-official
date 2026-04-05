---
name: search-github-repos
description: Use this skill when the user wants to search for GitHub repositories, discover open-source projects, or find code examples. Trigger phrases include "search for repositories about", "find repos for", "look for GitHub projects on", "show me repos tagged with", "find popular [language] repos for [topic]".
---

# Search GitHub Repositories

Use the GitHub MCP server to search for repositories matching the user's criteria.

## Steps

1. **Clarify the search intent** — extract the key parameters from the user's request:
   - **Topic or keyword**: what the repository should be about
   - **Language** (optional): e.g. Python, TypeScript, Rust
   - **Sort** (optional): stars, forks, updated (default: best match)
   - **Filters** (optional): `is:archived` exclusion, minimum stars, organisation scope
2. **Run the search** using the GitHub MCP `search_repositories` tool with the appropriate query string.
3. **Present the results** in a clear, scannable format for each repository:
   - **Name** (with link): `owner/repo`
   - **Description**: what the project does
   - **Stars / Forks**: popularity indicators
   - **Language**: primary programming language
   - **Last updated**: recency signal
   - **Topics / tags**: relevant labels
4. **Offer to refine** — if the results are too broad or too narrow, suggest adjusting the search query.

## Search Query Tips

- Combine topic and language: `machine learning language:python`
- Exclude archived repos: `machine learning language:python NOT is:archived`
- Minimum star count: `machine learning stars:>1000`
- Organisation scope: `machine learning org:google`

## Example Interaction

> User: "Search for repositories about machine learning"

1. Build query: `machine learning sort:stars`
2. Return top 10 results with name, description, stars, language, and link.
3. Offer: "Would you like to filter by language or minimum star count?"

## Notes

- Default to returning 10 results unless the user asks for more or fewer.
- Highlight the top 3 by stars if the list is long.
- If the search returns no results, suggest broadening the query (remove language filter, use synonyms).
