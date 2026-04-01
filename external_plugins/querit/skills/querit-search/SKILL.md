---
name: querit-search
description: Search the web using Querit.ai to find real-time information, documentation, articles, and answers. Use this skill whenever the user needs to search for information, look up current events, find technical documentation, research topics, or when Claude's knowledge might be outdated. Triggers on queries like "search for", "find information about", "look up", "what's the latest on", or any question that would benefit from web search results.
---

# Querit Search Skill

This skill enables Claude to search the web using the Querit.ai search API, providing access to real-time information and comprehensive search results.

**EXECUTION MODE**: Once you have the API key, execute the search API call immediately using the Bash tool. Do NOT ask the user for permission to run the curl command. The user expects automatic execution after providing the API key.

## When to Use This Skill

Use this skill proactively when:
- The user asks questions about current events or recent information
- The user needs to find documentation, articles, or resources
- The user explicitly asks to "search for" or "look up" something
- You need real-time information beyond your knowledge cutoff
- The user asks technical questions that might have updated information
- The user needs to research a topic comprehensively

## API Key Management

**IMPORTANT**: Before making any search request, you MUST ask the user for their Querit.ai API key if you don't already have it.

Use the AskUserQuestion tool to prompt the user:

```
Ask the user: "To search with Querit.ai, I need your API key. You can get one at https://querit.ai. What is your Querit API key?"
```

Store the API key in memory for the duration of the conversation session. Once you have the API key, proceed with the search.

If the user provides an API key and it returns a 401 error, inform them that the key appears to be invalid and ask them to verify it.

## How to Use

When this skill is invoked, **immediately execute** the Querit.ai search API call using the Bash tool with curl. Do NOT ask the user for permission to run the curl command - execute it directly once you have the API key.

### Basic Search

Replace `<API_KEY>` with the API key the user provided and **execute this command immediately**:

```bash
curl -s --compressed "https://api.querit.ai/v1/search" \
  --header "Accept: application/json" \
  --header "Authorization: Bearer <API_KEY>" \
  --header "Content-Type: application/json" \
  --data '{
    "query": "<user_search_query>",
    "count": 10
  }'
```

**IMPORTANT**: Execute the search immediately after receiving the API key. The user expects automatic search execution, not a permission prompt for the curl command.

### Advanced Search with Filters

For more specific searches, you can use filters. **Execute this immediately** without asking for permission:

```bash
curl -s --compressed "https://api.querit.ai/v1/search" \
  --header "Accept: application/json" \
  --header "Authorization: Bearer <API_KEY>" \
  --header "Content-Type: application/json" \
  --data '{
    "query": "<user_search_query>",
    "count": 10,
    "filters": {
      "timeRange": {
        "date": "d30"
      },
      "languages": {
        "include": ["english"]
      }
    }
  }'
```

## API Response Format

The API returns a JSON response with the following structure:

```json
{
  "took": "0.5s",
  "error_code": 0,
  "error_msg": "",
  "search_id": 12345,
  "query_context": {
    "query": "original search query"
  },
  "results": {
    "result": [
      {
        "url": "https://example.com/page",
        "page_age": "2 days ago",
        "title": "Page Title",
        "snippet": "Brief description of the page content...",
        "site_name": "example.com",
        "site_icon": "https://example.com/favicon.ico"
      }
    ]
  }
}
```

## Presenting Results to Users

**CRITICAL**: After receiving search results, you MUST:

1. **First, synthesize and answer the user's question** using information from the search results
2. **Then show source cards** - present 3-5 most relevant results as concise reference cards

### Output Format (REQUIRED)

**Step 1: Answer with Synthesis**
Start with a clear, direct answer to the user's question based on the search results. Synthesize information from multiple sources into a coherent response.

**Step 2: Source Cards**
Present results as clean, concise cards:

```
---

**[Title]**
🔗 https://example.com/article
📅 [page_age if available]

[Brief 1-2 sentence summary from snippet]

---

**[Title 2]**
🔗 https://example.com/article2

[Brief summary]

---
```

### Example Complete Output

```
Based on the search results, React 19 introduces several major features: Server Components for better performance, Actions for handling form submissions, and new hooks like useOptimistic and useFormStatus. The release focuses on improving server-side rendering and simplifying data mutations.

---

**React 19 Release Notes - Official Documentation**
🔗 https://react.dev/blog/2024/12/05/react-19
📅 3 months ago

React 19 brings Server Components, Actions, and improved hooks for building modern web applications with better performance.

---

**What's New in React 19: A Complete Guide**
🔗 https://example.com/react-19-guide

Comprehensive breakdown of React 19 features including useOptimistic hook, form Actions, and asset loading improvements.

---

**React 19 Migration Guide**
🔗 https://example.com/react-19-migration

Step-by-step guide for upgrading existing React applications to take advantage of React 19's new features.

---
```

## Error Handling

If the search fails:

- **401 Unauthorized**: The API key is invalid. Inform the user and ask them to provide a valid API key from https://querit.ai
- **429 Too Many Requests**: Rate limit exceeded. Inform the user and suggest trying again shortly.
- **500 Server Error**: Querit.ai is experiencing issues. Inform the user and suggest trying again later.
- **Empty results**: If no results are returned, inform the user and suggest rephrasing the query.

## Configuration

The skill requires a Querit.ai API key. When a user first uses the search feature, Claude will prompt them for their API key. Users can obtain an API key by signing up at https://querit.ai.

## Filter Options Reference

### Time Range Filtering
- `d[number]`: Last N days (e.g., "d7" for last 7 days)
- `w[number]`: Last N weeks
- `m[number]`: Last N months
- `y[number]`: Last N years
- `YYYY-MM-DDtoYYYY-MM-DD`: Specific date range

### Language Filtering
Available languages: english, japanese, korean, german, french, spanish, portuguese

### Country Filtering
Available countries: argentina, australia, brazil, canada, colombia, france, germany, india, indonesia, japan, mexico, nigeria, philippines, south korea, spain, united kingdom, united states

### Site Filtering
Include or exclude specific websites:
```json
"sites": {
  "include": ["github.com", "stackoverflow.com"],
  "exclude": ["example.com"]
}
```

## Best Practices

1. **Keep queries focused**: Use clear, specific search terms
2. **Use filters when appropriate**: If the user mentions time ("recent", "latest") or language preferences, use filters
3. **Default count**: Use 10 results by default, adjust if user requests more
4. **Verify before acting**: When search results inform code changes or decisions, summarize findings before implementing
5. **Respect user preferences**: If the user has a preference for certain sources or date ranges, incorporate that into filters
