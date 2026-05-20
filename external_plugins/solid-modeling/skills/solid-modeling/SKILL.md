---
name: solid-modeling
description: Use when designing or reviewing shared Solid Pod, RDF, Linked Data, drizzle-solid, or @undefineds.co/models schemas; especially for URI vs id fields, default id functions, inverse links, chat/thread/message/task/run modeling, Pod persistence boundaries, and cross-app data semantics.
---

# Solid Modeling

Use this skill when changing or reviewing shared Pod data models, RDF vocab
mappings, drizzle-solid schemas, repositories, or tests that assert durable
cross-app semantics.

## Core Stance

Model the Pod as a Linked Data graph, not as a relational database with foreign
keys.

- Use RDF/Pod relation fields for URI references.
- Use local ids only for UI state, runtime protocol keys, function parameters,
  or the random key passed into an id default function.
- Treat durable `id` values as base-relative resource ids. If the storage path
  or fragment is part of identity, the `id` must include it.
- Do not let a field named `xxxId` secretly behave like an RDF link.
- Prefer semantic relation names: `chat`, `thread`, `message`, `maker`,
  `replyTo`, `workspace`, `task`, `run`, `agent`.
- UI-only state stays outside the Pod. Durable shared state belongs in the Pod.

## Package Ownership

`@undefineds.co/models` owns durable shared model semantics. `drizzle-solid`
owns the ORM/resource machinery. Product shells such as Xpod, LinX desktop,
CLI, mobile, or workers should not duplicate shared schemas.

- If a resource/schema/repository already exists in `models`, consume it.
- If a product needs a missing shared query, mutation, or id helper, add it to
  `models` first with tests, then call it from the product shell.
- Keep product shells focused on interaction and adapter code: routing,
  rendering, runtime protocol projection, local cache plumbing, and mapping
  native runtime events into shared DTOs.
- Do not copy shared predicates, subject/id defaults, Turtle serializers, URI
  builders, or resource lifecycle state machines into shells.

## ORM-First Pod Access

Do not hand-parse shared business TTL when a resource schema exists.

- Use `db.select().from(resource).where(...)` for list/subset reads.
- Use `db.findById`, `db.updateById`, and `db.deleteById` when callers hold a
  canonical base-relative resource id.
- Use `db.findByIri`, `db.updateByIri`, and `db.deleteByIri` when the concrete
  resource IRI is known.
- Use `db.findByResource`, `db.updateByResource`, and `db.deleteByResource`
  only at adapter boundaries that intentionally accept mixed exact targets.
- Do not expose locator-shaped inputs in business APIs. `findByLocator`,
  `updateByLocator`, and `deleteByLocator` are legacy compatibility surfaces.
- Raw Solid client or `fetch` access is acceptable only for protocol-level
  adapters where no shared business resource exists yet.

## Ids, Defaults, and Subject Templates

The durable `id` is base-relative. It is not a fragment id.

Use an `id.default((key, row) => ...)` function when the id shape depends on
related resources, dates, command kind, workspace, or other row values. The
function should return the full base-relative resource id.

Examples:

```ts
chatResourceId('default') === 'default/index.ttl#this'
messageResourceId('msg_1', row) === 'chat/default/2026/05/18/messages.ttl#msg_1'
runResourceId('run_1', row) === 'task/secretary/2026/05/18/runs.ttl#run_1'
```

Do not combine a full id default with a `subjectTemplate` that reparses or
wraps the same id. Exact ids should resolve directly against `base`.

Keep `subjectTemplate` only for simple resources where the id field is the
stable storage key and the template has no hidden dependency on another
resource. Prefer a default id function once the template needs parent paths,
date buckets, fragments, or associated resource ids.

If a user passes an explicit id, treat it as exact. Do not reinterpret it as a
random key or fragment id.

## URI Fields and Query Ergonomics

Schema storage semantics and app ergonomics are different layers.

### Pod Schema Layer

Use full URI relation fields:

```ts
message.chat
message.thread
message.replyTo
thread.chat
run.thread
run.task
```

Avoid persisted relation fields such as:

```ts
message.chatId
message.threadId
thread.chatId
```

unless they are intentionally opaque literal protocol fields, not RDF links.

### Repository/API Layer

Short-id helpers are fine at API boundaries:

```ts
messageRepository.listByThreadId(db, { chatId, threadId })
threadRepository.listByChatId(db, { chatId })
```

These helpers should derive canonical Pod IRIs or base-relative ids internally.
Do not force UI/CLI callers to manually construct Pod IRIs in every query.

## Chat, Task, Thread, Message, Run, Step

Use these concepts consistently across products:

- `Chat`: interactive command surface/counterpart. It answers who or what the
  user is talking with.
- `Task`: task-style command surface, parallel to Chat. It describes recurring,
  triggered, or one-off task intent.
- `Thread`: concrete timeline/place under a Chat or Task.
- `Message`: human/runtime communication item in a Thread, linked to the Chat
  or Task surface when useful.
- `Run`: one concrete execution attempt by an Agent Runtime.
- `RunStep`: append-only execution facts for a Run.

Chat and Task are command surfaces. Run is the state center for execution.
RunStep is not a separate event store elsewhere; store it with Run when the
storage layout is date-bucketed.

## Solid Chat Relationship Guidance

Align with graph semantics:

| Concept | Preferred RDF direction | Typical predicate |
|---|---|---|
| chat contains message | `chat -> message` | `wf:message` / project vocabulary |
| thread contains message | `thread -> message` | `sioc:has_member` or equivalent |
| reply points to original | `replyMessage -> originalMessage` | `sioc:has_reply` / project predicate |
| author/maker | `message -> maker` | `foaf:maker` |

When inverse predicates are supported, use them for read/write symmetry. If the
ORM cannot safely express the inverse write, put the relation writer in the
repository and cover it with integration tests.

## Resource Naming

Use `Resource` names for shared models.

- Export `chatResource`, `messageResource`, `taskResource`, `runResource`.
- Keep `chatTable`-style aliases only for compatibility while downstream code
  migrates.
- New shared-model code should prefer `solidResources` over table registries.

## Testing Expectations

For shared schema changes, verify both ergonomics and graph semantics:

1. Unit tests for id/default helpers and URI builders.
2. Resource tests that assert exact-id mode or the intended `subjectTemplate`.
3. Repository or Pod integration tests for relation read/write behavior.
4. Assertions that produced IRIs contain no unresolved template placeholders.

Do not preserve obsolete tests that encode abandoned storage paths. Rewrite
them around current Pod semantics.

## Product Boundary

Product-specific domain rules do not belong in this skill.

- Put product data semantics in owning schemas, repositories, and shared docs.
- Keep this skill limited to reusable Solid/RDF modeling guidance.
- If product terms such as `chat`, `task`, `run`, or `agent` become shared,
  encode the durable semantics in `models`.
