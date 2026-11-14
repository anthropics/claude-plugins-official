# code-simplifier

An agent that cleans up code to make it easier to read and maintain, without changing what it does.

## What It Does

By default it only looks at code you changed in the current session. It will:

- Reduce nesting and remove redundant code
- Improve variable and function names
- Avoid nested ternaries and dense one-liners in favor of plain `if`/`else` or `switch`
- Follow the coding standards in your project's `CLAUDE.md`

It is told to keep behavior exactly the same, so outputs and features should not change.

## Installation

```
/plugin install code-simplifier@claude-plugins-official
```

## Usage

The agent is defined in [`agents/code-simplifier.md`](agents/code-simplifier.md). Claude can hand work to it on its own after you write or edit code, or you can ask for it directly:

```
"Use the code-simplifier agent on the files I just changed"
"Simplify src/utils/parse.ts"
```

To look at more than your recent changes, say so in the request, for example "simplify everything in src/".

## Notes

- The agent is set to run on the `opus` model.
- Review the diff afterwards. Simplifying is a judgment call, so check the changes before you commit them.

## License

See [LICENSE](LICENSE).
