# project-artifact

Generate and publish a **living status page** for a project that's too big for one update —
a migration, a launch, a research effort, anything with several workstreams tracked over
time. The page is a single self-contained tabbed HTML file (overview & success criteria,
the workstream sequence, an always-visible "Next steps" strip, plus background / plan /
risks / FAQ tabs when they earn their place), published with Claude Code's built-in
`Artifact` tool to a private `claude.ai/code/artifact/...` page that you can share with
teammates.

## Usage

- **Create one:** run `/project-artifact` (or just ask for a status page for your project)
  and point it at the project's sources — the repo and its PRs, a tracker, a design doc.
  It builds the page, publishes it, and tells you the URL.
- **Share it:** the page is private to you until you share it from the claude.ai viewer.
- **Keep it current:** say "refresh the artifact" in any later session. The plugin
  remembers the project's sources and the published URL, re-gathers live state, redeploys
  to the **same URL**, and replies with a short summary of what changed.

For software projects whose workstreams are pull requests, the page numbers the PR
sequence so the dependency order is obvious and pulls live PR/CI/review state via the
`gh` CLI.

## Requirements

- Claude Code's built-in `Artifact` tool, which requires a claude.ai login (sessions on an
  API key, Bedrock, or Vertex don't have it). Claude Code Artifacts are available in beta
  on Team and Enterprise plans.
- Optional: the `gh` CLI, for PR-driven projects.

## Notes

- Per-project state (the config and the latest render) lives in the plugin's data
  directory on your machine; the published artifact is the shareable copy.
- Artifact URLs are minted by the server. The plugin records yours after the first publish
  so refreshes land on the same address — bookmark it or add it to your team's hub so
  others can find it.
