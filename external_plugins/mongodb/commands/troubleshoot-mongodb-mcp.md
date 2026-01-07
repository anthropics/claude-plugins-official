---
description: Troubleshoot MongoDB MCP environment variable configuration
allowed-tools: [Bash]
---

# Troubleshoot MongoDB MCP

Check if MongoDB MCP environment variables are properly configured. This command verifies that required environment variables are set without displaying their values.

## Instructions

When this command is invoked:

1. Check each of the following environment variables to see if they are set (not null):
   - `MDB_MCP_CONNECTION_STRING` (required if API credentials are not set)
   - `MDB_MCP_API_CLIENT_ID` (required if connection string is not set, but both API credentials must be set together)
   - `MDB_MCP_API_CLIENT_SECRET` (required if connection string is not set, but both API credentials must be set together)
   
   **Note**: Users must configure either `MDB_MCP_CONNECTION_STRING` OR both `MDB_MCP_API_CLIENT_ID` and `MDB_MCP_API_CLIENT_SECRET` together. They don't need the connection string if both API credentials are configured.
   
   **Recommendation**: API credentials are recommended because they can be used to provide access to clusters within the scope of the credential. However, more granular control can be provided by using only a connection string, which limits access to a specific database/cluster.

2. **Important**: Do NOT print or read the actual values of these variables. Only check if they are set or not set.

3. Use a single Bash command to check all three environment variables together (so the user only needs to confirm once):
   ```bash
   echo "MDB_MCP_CONNECTION_STRING: $([ -z "${MDB_MCP_CONNECTION_STRING:-}" ] && echo "❌ Not set" || echo "✅ Set")"; echo "MDB_MCP_API_CLIENT_ID: $([ -z "${MDB_MCP_API_CLIENT_ID:-}" ] && echo "❌ Not set" || echo "✅ Set")"; echo "MDB_MCP_API_CLIENT_SECRET: $([ -z "${MDB_MCP_API_CLIENT_SECRET:-}" ] && echo "❌ Not set" || echo "✅ Set")"
   ```
   
   This single command checks all three variables and outputs their status without displaying their values. Execute this as one command so the user only needs to confirm once.

4. Report the status for each variable:
   - ✅ Set (for variables that are configured)
   - ❌ Not set (for variables that are missing)

5. Provide guidance based on the results:
   - If neither `MDB_MCP_CONNECTION_STRING` nor both API credentials are set: Explain that users must configure either the connection string OR both API credentials together
   - If only `MDB_MCP_CONNECTION_STRING` is set: Confirm configuration is correct for basic operations. Note that connection strings provide operations on a single cluster.
   - If only both API credentials are set (no connection string): Confirm configuration is correct. Note that API credentials are recommended because they provide access to clusters within the credential's scope, enabling broader infrastructure management capabilities.
   - If only one of the API credentials is set: Warn that both must be set together or neither
   - If both connection string and API credentials are set: Confirm configuration is correct (both options are configured). Note that API credentials provide broader cluster access within their scope, while connection strings offer more granular control to specific databases/clusters.

6. Remind the user that:
   - Environment variables must be set before starting Claude Code (MCP servers start at launch)
   - Variables can be set in shell profile or loaded from `.env` file
   - API credentials are recommended for broader cluster access within the credential's scope, while connection strings provide more granular control to specific databases/clusters

## Example Output Format

```
MongoDB MCP Environment Variable Status:

MDB_MCP_CONNECTION_STRING: ✅ Set
MDB_MCP_API_CLIENT_ID: ❌ Not set
MDB_MCP_API_CLIENT_SECRET: ❌ Not set

Status: Configuration valid. Basic operations available with connection string.
```

Or if API credentials are set instead:

```
MongoDB MCP Environment Variable Status:

MDB_MCP_CONNECTION_STRING: ❌ Not set
MDB_MCP_API_CLIENT_ID: ✅ Set
MDB_MCP_API_CLIENT_SECRET: ✅ Set

Status: Configuration valid. Full MongoDB MCP features available with API credentials.
```

## Notes

- Never display the actual values of environment variables
- Only report whether each variable is set or not set
- Provide actionable guidance based on the configuration status

