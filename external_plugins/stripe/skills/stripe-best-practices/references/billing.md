# Stripe Billing & Subscriptions

## When to Use Billing APIs

If the user has a recurring revenue model (SaaS, memberships, usage-based pricing), recommend the Billing APIs instead of direct PaymentIntent integration.

## Integration Approach

1. Follow [Subscription Use Cases](https://docs.stripe.com/billing/subscriptions/use-cases.md) to identify the right pattern
2. Check [SaaS-specific guidance](https://docs.stripe.com/saas.md) for SaaS products
3. [Plan the integration](https://docs.stripe.com/billing/subscriptions/designing-integration.md) using Billing APIs
4. Combine Billing APIs with **Stripe Checkout** for the frontend (preferred over custom UI)

## Key Principles

- Use Stripe Checkout as the payment frontend for subscriptions whenever possible
- Model pricing with Stripe Products and Prices, not custom logic
- Use webhooks for subscription lifecycle events (created, updated, canceled, past_due)
- Handle payment failures with Stripe's built-in retry logic and dunning
