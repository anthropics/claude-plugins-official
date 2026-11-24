# Attack surface analysis: the details

An attack surface analysis follows the method in Anthropic's research post [Using Claude to reduce the attack surface of code](https://www.anthropic.com/research/attack-surface-reduction), by reading your code: it leaves out that method's checks that build and run the code. It does not hunt for vulnerabilities, so it does not replace a scan.

## Confirmation

The analysis can take one to two and a half hours and uses many tokens, so it asks you to confirm before it starts anything. A request that accepts the cost answers in advance: "run an attack surface analysis; I understand it takes long and uses a lot of tokens".

- Leave Claude Code open until the analysis has finished.
- Leave the checkout as it is while the analysis runs. A change normally stops the analysis after the stage that is running, and makes the report read `unverified`.
- Run the analysis in auto mode.

## Getting started

Type `/claude-security:attack-surface-analysis`, or ask in plain words ("run an attack surface analysis of this repository"). Open Claude Code at the repository's root: the analysis covers the whole checkout, and refuses to start in a subfolder.

## The stages

The analysis runs these stages in order. You can ask for one or two of them alone.

| Stage | What it looks for | What you get |
| --- | --- | --- |
| **Default attack surface reduction** | Code that the default configuration reaches but default functionality never uses | Patch files that close that code off, and a regression suite to test them with |
| **Early reachability audit** | Sensitive code that an attacker can reach before login, or without the victim doing anything | A ranked inventory that separates what must run early from what does so by accident |
| **Configuration interaction audit** | Combinations of options that silently switch off a security feature | Findings with the exact options and values, and proposed fixes as patch files |

## How a finding earns its place

Each finding needs a recorded trace through the code. A second agent, which is not given that trace, then tries to prove it wrong. Only findings that it confirms are reported as findings. Refuted and unresolved ones are listed apart.

## What the agents may do

The agents are told to read your code, to build, install and run none of it, and to make no network call. These are instructions, not an enforced boundary: the analysis runs in your session, under the same trust model as a scan (see [Where it runs](README.md#where-it-runs)). The skill pre-approves reads of any file. It pre-approves no write and no command.

## Where the results go

The analysis writes the same report files as a scan, into `CLAUDE-SECURITY-<timestamp>/` in the folder where you started Claude Code. `CLAUDE-SECURITY-RESULTS.md` is the one to read. It reads `verified` or `unverified`; an `unverified` one says why. Its Coverage section says what each stage left out. Each stage has its own folder, with its report, full lists and evidence. Patches are in `attack-surface-patches/`, with `PATCHES.md` as its index.

- A finding's id (`claudeSecurityPluginFindingId`) changes when its line moves.
- "Suggest patches" does not take this folder: an analysis writes its own patches.

## Patches

Each proposed change is a patch file that you apply when you choose. `PATCHES.md` says which patches are ready, which are set aside and why, and which may clash. No patch has been tested. Read each one before you apply it. Apply the regression suite's patch first, and run the suite before and after you apply the patches that it tests.

## Disclosure

The agents are told to publish and report nothing; disclosure is yours to do.
