---
description: Search your Neutrally memory for past decisions, conversations, or context.
---

Search Neutrally memory using the `search` MCP tool. Call it with the user's query:

```
search({ query: "<user's search terms>" })
```

Format the results clearly:
- Show the conversation title and a concise summary for each result
- If a result is highly relevant, offer to fetch the full conversation with `fetch_conversation`
- If no results are found, say so clearly and suggest broadening the search

Example searches:
- "authentication decisions" → finds conversations about auth choices
- "react query setup" → finds when/how this was configured
- "checkout bug" → finds debugging sessions related to checkout
- "deployment config" → finds deployment-related decisions

Always search before saying "I don't know" about something that might have been discussed in a previous session.
