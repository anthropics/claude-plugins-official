---
description: Remove a specific memory item from Neutrally.
---

Help the user remove a specific memory item from Neutrally.

1. Search for the item they want to remove:
   ```
   search({ query: "<user's description of what to forget>" })
   ```

2. Show the matching results and ask the user to confirm which one(s) to delete.

3. Once confirmed, call `delete_memory` with the item ID:
   ```
   delete_memory({ id: "<memory_item_id>" })
   ```

4. Confirm deletion: "Removed from your Neutrally memory."

**Important:** Only delete after explicit user confirmation. If multiple items match, list them all and ask which ones to remove. This operation cannot be undone.

If the user wants to remove all memory related to a topic (e.g., an old project), search broadly and list everything before confirming bulk deletion.
