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
   
   **Note**: API credentials are required for Atlas tools and infrastructure management operations. Connection strings provide operations on a single cluster and are suitable for basic database operations. The choice depends on your use case: use connection strings for basic operations on a specific cluster, or API credentials if you need Atlas tools or infrastructure management.

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
   - If only `MDB_MCP_CONNECTION_STRING` is set: Confirm configuration is correct for basic database operations on a single cluster. Note that connection strings cannot perform Atlas infrastructure management operations.
   - If only both API credentials are set (no connection string): Confirm configuration is correct. Note that API credentials enable both basic database operations and Atlas tools/infrastructure management operations for clusters within the credential's scope.
   - If only one of the API credentials is set: Warn that both must be set together or neither
   - If both connection string and API credentials are set: Confirm configuration is correct (both options are configured). Note that API credentials enable Atlas tools and infrastructure management, while connection strings provide direct database access to a specific cluster.

6. Remind the user that:
   - Environment variables must be set before starting Claude Code (MCP servers start at launch)
   - Variables can be set in shell profile or loaded from `.env` file
   - Connection strings are suitable for basic database operations on a specific cluster
   - API credentials are required for Atlas tools and infrastructure management operations, and also enable basic database operations for clusters within the credential's scope

7. If configuration issues persist, mention that MongoDB MCP Server logs can help diagnose problems:
   - **Windows**: `%LOCALAPPDATA%\mongodb\mongodb-mcp\.app-logs`
   - **macOS and Linux**: `~/.mongodb/mongodb-mcp/.app-logs`
   - Logs can help identify connection string formatting issues, authentication problems, and other configuration errors
   - For more detailed troubleshooting guidance, refer to the [MongoDB MCP Server Troubleshooting documentation](https://www.mongodb.com/docs/mcp-server/configuration/troubleshooting/?utm_source=github-claude-plugins-official)

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

Status: Configuration valid. Full MongoDB MCP features available with API credentials, including Atlas tools and infrastructure management operations.
```

## Additional Troubleshooting Resources

If environment variables are correctly configured but issues persist:

- **Check MongoDB MCP Server logs** for detailed error messages:
  - Windows: `%LOCALAPPDATA%\mongodb\mongodb-mcp\.app-logs`
  - macOS and Linux: `~/.mongodb/mongodb-mcp/.app-logs`
- **Verify connection string format** matches MongoDB connection string requirements
- **Confirm API credentials** have appropriate permissions for the operations you're trying to perform
- **Review the official troubleshooting guide**: [MongoDB MCP Server Troubleshooting](https://www.mongodb.com/docs/mcp-server/configuration/troubleshooting/?utm_source=github-claude-plugins-official)

## Notes

- Never display the actual values of environment variables
- Only report whether each variable is set or not set
- Provide actionable guidance based on the configuration status
- Log files are the primary source for diagnosing connection and authentication issues

