---
name: Create Auth Skill
description: A skill to create auth service for new applications.
---

# Create an auth layer for your TypeScript/JavaScript applications

## Overview

A user could ask you to create authentication and authorization layers for their TypeScript/JavaScript applications.

## Decision Tree: Choosing Your Approach

```
User task -> Do we start from a empty project?
    ├─ Yes → Create a new project with authentication scaffolding
    │         ├─ Choose web framework: React, Next.js, Express, etc.
    │         ├─ Select database: PostgreSQL, MongoDB, etc.
    │         ├─ Set up auth using @better-auth/cli
    │         └─ Customize auth flows as per user requirements, like OAuth, JWT, Organization, Admin...
    │
    └─ No → Is the existing project already have authentication?
              ├─ Yes → Review existing auth implementation
              │         ├─ Identify gaps or improvements needed
              │         ├─ Read document for missing features from `better-auth`
              │         └─ Test and validate the updated auth flows
              │
              └─ No → Analyze the existing project structure
                        ├─ Choose appropriate auth strategy
                        ├─ Integrate `better-auth` into the existing codebase
                        └─ Implement and test the new authentication flows
```

## Example: Next.js app with Better Auth

You can read [templates/nextjs](https://github.com/better-auth/examples/tree/main/nextjs-mcp)
to see a complete example of a Next.js app integrated with Better Auth.

In this example, you can see the most two essential files, auth.ts and auth-client.ts.

```ts
import { betterAuth } from 'better-auth'
import Database from 'better-sqlite3'

export const auth = betterAuth({
  database: new Database('./auth.db'),
  baseURL: 'http://localhost:3000',
  plugins: [],
  emailAndPassword: {
    enabled: true
  }
})
```

```ts
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient();
```

In this example, it doesn't include any plugins, but you can easily add plugins by importing them from
`better-auth/plugins` and adding them to the `plugins` array in the `betterAuth` configuration.

Also you will need to update auth client to make sure client-side plugins are included.

You can refer to the [plugins](https://www.better-auth.com/docs/concepts/plugins) for more details on how
to set up and customize your authentication flows.

## Dependencies

To use better-auth, install these dependencies only if they aren't already present in package.json:

```bash
npm install better-auth
```

## Advanced features

**@better-auth/cli**: See [cli](https://www.better-auth.com/docs/concepts/cli) for details on how to use the CLI tool.
**Examples**: See [examples](https://github.com/better-auth/examples) for complete example projects using better-auth,
including astro, browser-extension, next.js, nuxt, svelte and tanstack.
