# MongoDB Plugin

MongoDB MCP integration for Claude Code, providing comprehensive database operations and infrastructure management capabilities.

## Installation

Install the MongoDB plugin from the Claude Code marketplace:

```bash
/plugin install mongodb@claude-plugin-directory
```

Or browse and install via:
```bash
/plugin > Discover
```

Once installed, configure your MongoDB connection (see Setup below).

## Features

### Basic Database Operations (Requires Connection String)
Requires `MDB_MCP_CONNECTION_STRING` environment variable:
- Query collections with flexible filters
- Insert, update, and delete documents
- Run aggregation pipelines
- Count documents
- List databases and collections

### Infrastructure Management (Requires API Credentials)
With MongoDB API credentials (`MDB_MCP_API_CLIENT_ID` and `MDB_MCP_API_CLIENT_SECRET`):
- Create and drop databases
- Create and drop collections
- Manage indexes (create, list, drop)
- Configure database settings
- User and role management
- Atlas cluster management

## Setup

### Required Environment Variables

**Minimum (Basic Operations):**
```bash
export MDB_MCP_CONNECTION_STRING="mongodb+srv://username:password@cluster.mongodb.net/?appName=claude-code"
```

See [MongoDB Atlas Connection String documentation](https://www.mongodb.com/docs/manual/reference/connection-string/?deployment-type=atlas&interface=atlas-ui&utm_source=github-claude-plugins-official) for details on obtaining your connection string.

**Full Access (Infrastructure Management):**
```bash
export MDB_MCP_CONNECTION_STRING="mongodb+srv://username:password@cluster.mongodb.net/?appName=claude-code"
export MDB_MCP_API_CLIENT_ID="your_client_id"
export MDB_MCP_API_CLIENT_SECRET="your_client_secret"
```

### Granting Programmatic Access to Atlas

The `MDB_MCP_API_CLIENT_ID` and `MDB_MCP_API_CLIENT_SECRET` environment variables support both service accounts and API keys for granting programmatic access to Atlas. **MongoDB recommends using service accounts** for better security and access management.

Service accounts and API keys can be created at either the **Organization** or **Project** level, depending on the scope of access you need.

See [MongoDB Atlas Configure API Access documentation](https://www.mongodb.com/docs/atlas/configure-api-access/?interface=atlas-ui&programmatic-access=service-account&utm_source=github-claude-plugins-official#grant-programmatic-access-to-service) for detailed instructions on setting up programmatic access.

## Usage

MongoDB MCP tools are invoked automatically by Claude when you describe what you want to do. Simply ask Claude in natural language, and it will use the appropriate MongoDB tools.

### Query Documents

**You say:**
```
Find all active users in the mydb.users collection, limit to 10 results
```

**Claude automatically uses:**
- `mcp__plugin_mongodb_mongodb-mcp-server__find` with appropriate parameters

**Example requests:**
- "Show me all documents in the products collection where price is greater than 100"
- "Find users with status 'active' in the mydb database"
- "Get the first 20 orders from the orders collection"

### Create Collection (Requires API Credentials)

**You say:**
```
Create a new collection called 'events' in the 'mydb' database
```

**Claude automatically uses:**
- `mcp__plugin_mongodb_mongodb-mcp-server__create-collection`

**Example requests:**
- "Create a collection named 'logs' in the analytics database"
- "Set up a new 'sessions' collection in mydb"
- "Create a capped collection 'recent_activity' with size 10MB"

### Run Aggregation

**You say:**
```
Group events by category and count them, filtering for dates after 2024-01-01
```

**Claude automatically uses:**
- `mcp__plugin_mongodb_mongodb-mcp-server__aggregate` with the aggregation pipeline

**Example requests:**
- "Calculate total sales by product category from the orders collection"
- "Find the average age of users grouped by country"
- "Show me the top 10 most active users based on login count"

### Discovering Available Tools

Use the `/mcp` command in Claude Code to see all available MongoDB tools and their schemas:

```
/mcp
```

This shows:
- All available MongoDB MCP tools
- Tool parameters and descriptions
- Full tool names (for use in custom commands)

## Permissions

- **Connection String Only**: Read/write operations on existing databases and collections, subject to the permissions of the database user
- **With API Credentials**: Full infrastructure management including creating databases, collections, indexes, and managing Atlas resources, subject to the permissions of the service account or api key

## Resources

- [MongoDB MCP Technical Documentation](https://www.mongodb.com/docs/mcp-server/get-started/?utm_source=github-claude-plugins-official)
- [MongoDB MCP Github Repo](https://github.com/mongodb-js/mongodb-mcp-server?utm_source=github-claude-plugins-official)
- [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/?utm_source=github-claude-plugins-official)

