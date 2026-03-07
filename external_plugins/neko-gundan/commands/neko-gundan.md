# Neko Gundan Deployment

Launch the Neko Gundan multi-agent system for the given task.

## Auto-Scaling

Assess the task scale and deploy the appropriate formation:

| Scale | Criteria | Formation |
|-------|----------|-----------|
| Recon | Questions, research, single file check | Oyakata-neko handles directly |
| Squad | 1-2 file changes | Single shigoto-neko |
| Platoon | 3-5 file changes or multiple tasks | TeamCreate: shigoto-neko + 1-2 genba-neko |
| Battalion | 6+ files or large-scale work | TeamCreate: shigoto-neko + 3 genba-neko |

## Model Assignment

- Oyakata-neko (strategy): Opus
- QA / kurouto-neko (review): Opus
- Shigoto-neko (management): Sonnet
- Genba-neko (implementation): Sonnet

## Deployment Steps

1. Assess task scale using the table above
2. Create team with TeamCreate
3. Assign oyakata-neko as the team lead
4. Oyakata-neko decomposes and delegates to shigoto-neko
5. Shigoto-neko manages genba-neko for implementation
6. Kurouto-neko performs independent QA review (platoon+)
7. Report results back to the commander (human)

## Whiteboard

For platoon+ missions where agent discoveries affect each other, shigoto-neko sets up a whiteboard for cross-agent knowledge sharing.

## Quality Gates

Every task must pass completion gates before being declared done. See the rules/completion-gates.md for details.
