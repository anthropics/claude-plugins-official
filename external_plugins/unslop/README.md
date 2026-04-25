# unslop

> Strip AI writing patterns from Claude Code output before you publish.

**Author:** [Mohamed Abdallah](https://github.com/MohamedAbdallah-14)  
**Source:** [MohamedAbdallah-14/unslop](https://github.com/MohamedAbdallah-14/unslop)  
**License:** MIT

## What it does

Unslop is a Claude Code plugin that runs on session start and tracks each turn. When you're ready to publish, pipe your draft through the `unslop` CLI to strip the patterns that mark text as AI-generated: sycophantic openers, stock vocabulary, hedging stacks, em-dash pileups, and passive constructions that blunt the point.

It does not rewrite your content. It strips specific patterns and engineers burstiness (mix of short and longer sentences). Code blocks, URLs, and technical terms are preserved unchanged.

## Installation

```bash
npm install -g unslop
```

Then install the plugin in Claude Code:

```
/install-github MohamedAbdallah-14/unslop
```

## Usage

**Interactive mode** — toggle unslop on/off during a session:

```
/unslop on
/unslop off
/unslop status
```

**CLI pipe** — post-process any draft:

```bash
echo "Your AI-generated draft here..." | unslop --stdin
```

**Deterministic mode** — for scripts and CI:

```bash
cat draft.md | unslop --stdin --deterministic
```

## What gets stripped

- Sycophantic openers ("Great question!", "Certainly!", "Of course!")
- Stock AI vocabulary (utilize, leverage, delve, crucial, notable, robust)
- Hedging stacks ("it's important to note that", "it's worth mentioning")
- Em-dash overuse and comma splices
- Passive voice constructions that bury the actor

## Requirements

- Node.js 18+
- `unslop` CLI installed globally (`npm install -g unslop`)
