# engineering-skills

8 flagship engineering skills for building, shipping and reviewing production code.

## Install (Claude Code)

```bash
/plugin marketplace add borghei/Claude-Skills
/plugin install engineering-skills@claude-skills
```

## Included skills

| Skill | What it does |
|---|---|
| senior-fullstack | Full-stack architecture, API design, stack decisions from first principles |
| senior-devops | CI/CD pipelines, container orchestration, infra automation |
| senior-security | AppSec review, threat modeling, OWASP-driven code review |
| docker-development | Dockerfile patterns, multi-stage builds, local dev environments |
| terraform-patterns | IaC patterns, module design, state management, provider selection |
| mcp-server-builder | Build MCP servers that Claude Code can call as native tools |
| rag-architect | Retrieval-augmented generation systems, chunking, eval, hybrid search |
| code-reviewer | Structured code review covering correctness, security, reuse, naming |

## Who this is for

Engineering teams using Claude Code that want the full stack of technical skills without manually installing each one. Lands ~3 MB of Python tooling, reference guides and templates into `.claude/skills/`.

## License

MIT + Commons Clause. See [LICENSE](https://github.com/borghei/Claude-Skills/blob/main/LICENSE).
