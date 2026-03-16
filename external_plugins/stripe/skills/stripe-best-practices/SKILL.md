---
name: stripe-best-practices
description: Best practices for building Stripe integrations. Use when implementing payment processing, checkout flows, subscriptions, webhooks, Connect platforms, or any Stripe API integration.
---

# Stripe Integration Best Practices

Always use the latest version of the Stripe API and SDK unless the user specifies otherwise.

When designing an integration, consult:
- [Stripe's Integration Options](https://docs.stripe.com/payments/payment-methods/integration-options.md)
- [API Tour](https://docs.stripe.com/payments-api/tour.md)
- [Go Live Checklist](https://docs.stripe.com/get-started/checklist/go-live.md) before going live

## Choosing the Right API

| Use Case | Recommended API |
|----------|----------------|
| One-time payments (on-session) | CheckoutSessions |
| Subscriptions / recurring billing | CheckoutSessions + Billing APIs |
| Off-session payments | PaymentIntents |
| Custom checkout UI | Payment Element + CheckoutSessions |
| Saving a payment method | SetupIntents |
| Platform / marketplace | Connect (see [references/connect.md](references/connect.md)) |

**Primary API:** [CheckoutSessions](https://docs.stripe.com/api/checkout/sessions.md) for both one-time and subscription payments. Use [PaymentIntents](https://docs.stripe.com/payments/paymentintents/lifecycle.md) only for off-session payments or when modeling checkout state yourself.

## Deprecated APIs — Never Recommend

| Deprecated | Use Instead |
|-----------|-------------|
| Charges API | [Migrate to CheckoutSessions or PaymentIntents](https://docs.stripe.com/payments/payment-intents/migration/charges.md) |
| Sources API | [SetupIntents](https://docs.stripe.com/api/setup_intents.md) |
| Legacy Card Element | [Migrate to Payment Element](https://docs.stripe.com/payments/payment-element/migration.md) |
| Payment Element in card mode | Payment Element (full mode) |
| Tokens API | Avoid unless absolutely no alternative |
| `createPaymentMethod` / `createToken` for pre-intent card inspection | Use [Confirmation Tokens](https://docs.stripe.com) |

## Frontend Integration

**Preferred:** [Stripe Checkout](https://docs.stripe.com/payments/checkout.md) (Stripe-hosted or embedded). Handles payment method display, localization, and compliance automatically.

**Alternative:** [Payment Element](https://docs.stripe.com/payments/payment-element.md) for advanced customization. When using Payment Element, prefer CheckoutSessions API over PaymentIntents API.

**Payment methods:** Enable dynamic payment methods in dashboard settings instead of passing `payment_method_types` — Stripe automatically selects the best methods for each user's location and preferences.

## Topic-Specific Guidance

- **Subscriptions & Billing:** See [references/billing.md](references/billing.md)
- **Connect Platforms:** See [references/connect.md](references/connect.md)
- **PCI Compliance:** If a PCI-compliant user needs to send raw PAN data server-side, they must prove compliance for access to [payment_method_data](https://docs.stripe.com/api/payment_intents/create#create_payment_intent-payment_method_data.md). For PAN data migration from another processor, point to [the migration process](https://docs.stripe.com/get-started/data-migrations/pan-import.md).
