---
name: better-auth-best-practices
description: Best practices for building Better Auth integrations. Use when implementing authentication, authorization, session management, OAuth providers, or any Better Auth integration.
---

When designing an authentication integration, always prefer the documentation in [Better Auth's Documentation](https://better-auth.com/docs)

You should always default to the latest version of Better Auth unless the user specifies otherwise.

Better Auth is a TypeScript-first authentication framework that provides a secure, flexible, and developer-friendly approach to authentication. It supports multiple authentication methods including email/password, OAuth providers, magic links, and passwordless authentication.

**Core Principles:**

1. **Type Safety**: Better Auth is built with TypeScript and provides full type safety throughout the authentication flow. Always leverage TypeScript types for better developer experience and fewer runtime errors.

2. **Security First**:
   - Always use secure session management with HTTP-only cookies
   - Implement CSRF protection for all authentication endpoints
   - Use secure password hashing (bcrypt or argon2)
   - Enable rate limiting on authentication endpoints
   - Follow OWASP authentication best practices

3. **OAuth Integration**: When implementing OAuth providers:
   - Use the built-in provider configurations when available
   - Always validate OAuth tokens server-side
   - Store OAuth tokens securely
   - Handle OAuth errors gracefully
   - Implement proper redirect URI validation

4. **Session Management**:
   - Use secure, HTTP-only cookies for session tokens
   - Implement proper session expiration and refresh mechanisms
   - Store minimal data in sessions
   - Validate sessions on every protected request
   - Implement session revocation for logout

5. **Email Authentication**:
   - Implement email verification for new accounts
   - Use secure, time-limited verification tokens
   - Implement password reset with secure tokens
   - Rate limit email sending to prevent abuse

6. **Database Integration**:
   - Use the appropriate adapter for your database (Prisma, Drizzle, etc.)
   - Implement proper database indexes for performance
   - Handle database errors gracefully
   - Use transactions for critical operations

7. **Error Handling**:
   - Provide clear, user-friendly error messages
   - Never expose sensitive information in errors
   - Log authentication failures for security monitoring
   - Implement proper error boundaries

8. **Testing**:
   - Write tests for authentication flows
   - Test OAuth provider integrations
   - Test session management
   - Test error scenarios

**Common Patterns:**

- For basic email/password authentication, use the built-in email provider with secure password hashing
- For social authentication, configure OAuth providers with proper scopes and permissions
- For passwordless authentication, implement magic links with time-limited tokens
- For session management, use the built-in session adapter with your database

**Resources:**
- [Better Auth Documentation](https://better-auth.com/docs)
- [GitHub Repository](https://github.com/better-auth/better-auth)
- [Examples](https://better-auth.com/docs/examples)

Always consult the official documentation for the most up-to-date best practices and API changes.
