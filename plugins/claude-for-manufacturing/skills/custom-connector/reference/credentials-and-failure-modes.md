# Handling credentials, and saying how it will break

---

## Credentials

**Narrowest scope that does the job.** Read-only unless a write is
genuinely required and has been approved — not "might be useful later,"
approved for a stated, current need.

**A dedicated integration user, never someone's personal login.** Access
tied to a person breaks the day they change roles or leave, usually at the
worst possible moment, and it can't be revoked without locking that person
out of everything else they use the same login for.

**Tokens and OAuth only. Never a password.** A password is a standing
secret with no expiry and no scope; a token can be scoped, rotated, and
revoked without touching anything else the account can do.

**Say plainly what the connector will be able to reach before it's
created.** Not after — the customer's admin is granting access based on
what they're told, and finding out afterward that the scope was broader
than expected is how a plant stops trusting the next connector request.

**Never accept a credential in conversation.** Not pasted, not typed, not
read back to confirm it was copied correctly. If someone pastes one
anyway, say plainly that it should be rotated — a credential that has
touched a chat transcript is not clean again just because nobody used it.

---

## Registering what was built

Once a connector is working, record — concretely, not as a general
capability claim:

- **What it reaches.** The specific entities and fields, not "NetSuite
  data."
- **What it cannot do.** The boundary is as important as the capability;
  a downstream skill needs to know what to ask for elsewhere.
- **How it refreshes.** Real-time, polled at an interval, or on an export
  cadence — and what that means for anything time-sensitive that reads it.
- **Which skills it now unblocks.** Named specifically, so the person who
  requested it can see the actual payoff.

---

## Say how it will break, while the customer is still listening

**A connector that fails silently is worse than no connector.** No
connector produces an obvious gap; a silently failing one produces
confident, wrong output that looks exactly like a working connection.

State the specific failure mode for the tier that was built, before
handing it over:

| Tier | How it fails |
|---|---|
| 1, 2, 3 | Token expiry — name the renewal path. Vendor API version changes arrive with no warning; the surface needs re-testing when they do |
| 3 | Rate limits, hit under real load rather than in testing |
| 4 | Schema drift — a vendor upgrade changes the underlying table with no error, and the view returns the wrong thing or nothing |
| 5 | Task limits on the plan tier, and per-task cost that scales with volume nobody budgeted for |
| 7 | An export that stops landing, silently, with no error anywhere — this is exactly why `data-consolidate`'s freshness check exists |

**Name who fixes it, too.** A failure mode with no owner is a failure mode
nobody responds to until a downstream skill reports something wrong and
someone traces it back here.
