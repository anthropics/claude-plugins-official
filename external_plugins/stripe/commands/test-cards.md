---
description: Display Stripe test card numbers for various testing scenarios
argument-hint: [scenario]
---

# Test Cards Reference

Provide a quick reference for Stripe test card numbers:

1. If a scenario argument is provided (e.g., "declined", "3dsecure", "fraud"), show relevant test cards for that scenario
2. Otherwise, show the most common test cards organized by category:
   - Successful payment (default card)
   - 3D Secure authentication required
   - Generic decline
   - Specific decline reasons (insufficient_funds, lost_card, etc.)
3. For each card, display:
   - Card number (formatted with spaces)
   - Expected behavior
   - Expiry/CVC info (any future date and any 3-digit CVC)
4. Use clear visual indicators (✓ for success, ⚠️ for auth required, ✗ for decline)
5. Mention that these only work in test mode
6. Provide link to full testing documentation: https://docs.stripe.com/testing.md

If the user is currently working on test code, offer to generate test cases using these cards.
