# Stripe Connect

## Choosing a Charge Type

Follow [integration recommendations](https://docs.stripe.com/connect/integration-recommendations.md):

| Scenario | Charge Type |
|----------|-------------|
| Platform wants Stripe to handle risk | Direct charges |
| Platform accepts liability for negative balances | Destination charges |

Use `on_behalf_of` parameter to control the merchant of record. **Never mix charge types** within a single integration.

## Account Types

Do NOT use the outdated terms (Standard, Express, Custom). Instead:
- [Refer to controller properties](https://docs.stripe.com/connect/migrate-to-controller-properties.md) for platform configuration
- Use [capabilities](https://docs.stripe.com/connect/account-capabilities.md) for connected accounts

## Integration Planning

If the user needs to decide on specific risk features, follow [the integration guide](https://docs.stripe.com/connect/design-an-integration.md) for a step-by-step walkthrough of platform design decisions.
