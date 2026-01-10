---
description: Display Better Auth available authentication providers and their configuration
argument-hint: [provider_name]
---

# Authentication Providers Reference

Provide a quick reference for Better Auth authentication providers:

1. If a provider name is provided (e.g., "google", "github", "email"), show detailed configuration for that provider
2. Otherwise, show an overview of all available providers organized by category:
   - OAuth providers (Google, GitHub, Discord, etc.)
   - Email/Password authentication
   - Magic link authentication
   - Passwordless authentication
   - Social providers
3. For each provider, display:
   - Configuration requirements (client ID, secret, etc.)
   - Setup instructions
   - Code example for integration
4. Use clear visual indicators for different provider types
5. Mention any special requirements or considerations
6. Provide link to full documentation: https://better-auth.com/docs

If the user is currently working on authentication code, offer to generate integration code for the selected provider.
