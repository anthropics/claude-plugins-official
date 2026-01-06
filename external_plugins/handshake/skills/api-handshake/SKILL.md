---
name: api-handshake
description: API contract negotiation between mobile clients and BFF backends. Propose, accept, provision endpoints. Use for any "tango", "contract", "BFF", or "handshake" work.
---

# API Handshake: Cross-Team Contract Negotiation

> Mobile proposes endpoints, backend reviews and provisions.

## When To Use

Trigger on keywords: **tango**, **handshake**, **BFF**, **API contract**, **endpoint**, **propose**

## Workflow

```
IDLE ──propose──► PROPOSED ──accept──► LOCKED ──provision──► DONE
                      │
                      └──reject──► IDLE (with feedback)
```

**Frontend (Mobile):** Proposes contracts
**Backend (BFF):** Reviews, accepts, provisions

---

## Contract Location

Contracts live in the project's `.handshake/contracts/` directory:

```
.handshake/
├── contracts/
│   ├── proposals/           # Pending contracts
│   │   └── orders-v1.yaml
│   └── locked/              # Accepted contracts
│       └── auth-v1.yaml
└── ...
```

---

## Contract Schema

```yaml
contract:
  id: "feature-v1"              # Unique ID
  name: "Feature Name API"      # Display name
  version: "1.0.0"              # Semantic version
  status: proposed              # proposed | locked | provisioned
  proposed_by: android/merchant # Team path
  proposed_date: "2024-12-25"   # ISO date
  urgency: high | medium | low  # Priority
  reason: "Why this API needed" # Business justification

backend_services:
  - name: merchant-mobile-bff   # Target BFF

endpoints:
  - path: /api/v1/merchant/orders
    method: GET
    description: "Fetch merchant orders"

    request:
      headers:
        Authorization: "Bearer {token}"
      query_params:
        - name: status
          type: string
          required: false
          enum: [pending, active, completed]

    response:
      success:
        status: 200
        body:
          orders:
            type: array
            items:
              id: { type: string }
              status: { type: string }
              total_cents: { type: integer }  # Money in cents!

      errors:
        - status: 401
          code: UNAUTHORIZED
          message: "Invalid or expired token"

models:
  Order:
    fields:
      - name: id
        type: String
      - name: total_cents      # Always cents for money!
        type: Long
```

---

## Key Rules

1. **Money in cents (Long)** - NEVER use Float for currency
2. **ISO8601 for dates** - "2024-12-25T10:30:00Z"
3. **Semantic versioning** - major.minor.patch
4. **Max 3 counter-rounds** - Then escalate to human

---

## Team Mapping

```
Mobile App           →  BFF Service
─────────────────────────────────────
android/merchant     →  merchant-mobile-bff
android/consumer     →  customer-mobile-bff
android/courier      →  courier-mobile-bff
ios/merchant         →  merchant-mobile-bff
```

---

## Example: Proposing an API

**1. Create contract file:**

```yaml
# .handshake/contracts/proposals/orders-v1.yaml
contract:
  id: orders-v1
  name: Orders API
  version: "1.0.0"
  status: proposed
  proposed_by: android/merchant
  urgency: high
  reason: "Need to fetch and manage orders"

endpoints:
  - path: /api/v1/merchant/orders
    method: GET
    description: "List orders"
    response:
      success:
        status: 200
        body:
          orders: { type: array }

  - path: /api/v1/merchant/orders/{id}/accept
    method: POST
    description: "Accept an order"
    request:
      body:
        prep_time_minutes: { type: integer }
    response:
      success:
        status: 200
```

**2. Mobile agent creates the proposal file**

**3. Backend agent reviews and either:**
- Moves to `locked/` (accepted)
- Adds feedback and leaves in `proposals/` (needs revision)

**4. Once locked, backend provisions the endpoint**

---

## Tango Pattern

A "tango" is a client ↔ BFF pair. Work in batches:

```
Tango #1: android/merchant ↔ merchant-mobile-bff
Tango #2: android/consumer ↔ customer-mobile-bff
Tango #3: android/courier  ↔ courier-mobile-bff
```

For each tango:
1. Analyze client codebase for API needs
2. Draft contract YAML files
3. Place in `.handshake/contracts/proposals/`
4. Commit and push
5. Backend reviews and accepts
6. Backend provisions endpoint

---

## Integration with Velocity-X

Component contracts (vx-extraction) inform API contracts:

```
OrdersViewModel (component contract)
    └── needs: loadOrders(), acceptOrder()
        └── implies: GET /orders, POST /orders/{id}/accept
```

Extract component contracts first, then derive API contracts from dependencies.

---

## Status Checking

Agents check contract status by reading files:

```bash
# List proposals
ls .handshake/contracts/proposals/

# List locked
ls .handshake/contracts/locked/

# View a contract
cat .handshake/contracts/proposals/orders-v1.yaml
```

No special tooling needed - just files and git.
