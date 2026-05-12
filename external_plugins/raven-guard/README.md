# Raven Guard

> Production protection layer for Claude Code.
> Built by [Giggso Inc](https://github.com/giggsoinc). MIT License.

*The Three-Eyed Raven sees all. Nothing reaches production unchecked.*

## Requires

[Raven Core](https://github.com/giggsoinc/raven) must be installed first:

```bash
claude plugin install raven@claude-plugins-official
```

## What It Does

Hard-blocks and approval flows for destructive operations across git, database, infrastructure, firewall, and observability layers.

| | Raven Core | Raven Guard |
|---|---|---|
| **Audience** | Developers | DevOps, Architects, Security |
| **Job** | Coding discipline | Production protection |
| **Triggers** | Dev actions | System events |

## Hard Blocks (no exceptions)

- Force push to any branch
- `TRUNCATE TABLE`, `DROP TABLE`, `DROP SCHEMA`
- Terraform state file modified
- `0.0.0.0/0` firewall rule
- RDP (3389) or SSH (22) opened to public
- Kubernetes namespace deleted

## Approval Flows

- File deletion with `[GUARD:ALLOW-DELETE]` flag
- Mass deletion >100 rows
- S3 bucket deletion
- VM termination
- Network rule change

## Incident SLAs

| Level | Trigger | SLA |
|---|---|---|
| P1 | Production down / data loss | 15 min escalation |
| P2 | Degraded / potential breach | 1 hour |
| P3 | Anomaly / policy violation | 24 hours |

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/giggsoinc/raven-guard/main/install.sh | bash
cd YourProject && raven-guard-setup
```

## Source

[github.com/giggsoinc/raven-guard](https://github.com/giggsoinc/raven-guard)
