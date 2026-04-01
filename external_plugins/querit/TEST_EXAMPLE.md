# Querit Search Plugin - Test Example

## How to Test the Plugin

### 1. Start Claude with the plugin

```bash
cd /Users/kkkpjskey/Code/claude-querit
claude --plugin-dir .
```

### 2. Try these test prompts:

**Test 1: Basic Search**
```
Search for information about React 19 new features
```

**Test 2: Recent Information**
```
What are the latest developments in AI from the past week?
```

**Test 3: Technical Documentation**
```
Find documentation about Stripe payment integration
```

### 3. Expected Behavior

When you first make a search request, Claude will:
1. Recognize that it needs to use the Querit search skill
2. **Ask you for your Querit.ai API key** using a question prompt
3. Once you provide the key, it will execute the search
4. Return formatted results with titles, URLs, and snippets

### 4. API Key Flow

```
You: "Search for React 19 features"

Claude: "To search with Querit.ai, I need your API key.
You can get one at https://querit.ai. What is your Querit API key?"

You: [provide your API key]

Claude: [executes search and returns formatted results]
```

### 5. Sample curl command that will be executed

```bash
curl -s --compressed "https://api.querit.ai/v1/search" \
  --header "Accept: application/json" \
  --header "Authorization: Bearer YOUR_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "query": "React 19 features",
    "count": 10
  }'
```

## Verifying Plugin Installation

After starting Claude with `--plugin-dir .`, verify the plugin is loaded:

```
/help
```

You should see the skill listed as:
```
/querit-search:querit-search - Search the web using Querit.ai
```

## Troubleshooting

- If the skill doesn't trigger automatically, try using the explicit command: `/querit-search:querit-search`
- Reload plugins without restarting: `/reload-plugins`
- Check plugin status: `/plugins`

## API Response Example

When successful, the API returns:

```json
{
  "error_code": 0,
  "took": "0.5s",
  "results": {
    "result": [
      {
        "title": "React 19 Release Notes",
        "url": "https://react.dev/blog/2024/12/05/react-19",
        "snippet": "React 19 introduces Server Components, Actions, and new hooks...",
        "site_name": "react.dev",
        "page_age": "3 months ago"
      }
    ]
  }
}
```

Claude will then format this into a user-friendly presentation.
