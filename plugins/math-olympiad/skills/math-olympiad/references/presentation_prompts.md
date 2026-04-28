# Presentation Pass — Prompts and Templates

**Premise**: Aletheia's PDFs are beautiful; raw IMO output is not. The
difference is a _presentation pass_: after a proof is **verified correct**, a
fresh agent — one who didn't sweat through the discovery — finds the cleanest
way to say it. The discoverer is too attached to the scaffolding.

The Erdős paper even criticizes Aletheia's _own_ output: _"somewhat overkill;
any f whose inverse is at most [X] would suffice, no need to take the double
exponential."_ The presentation pass is where overkill goes to die.

---

## 1. The Presentation Pass Prompt

Paste this to a **fresh subagent** along with the verified proof. The agent must
not have discovery-context; that's the point.

> You are given a **verified, correct proof**. Your job is not to check it — it
> is correct. Your job is to find the **cleanest presentation**. The order it
> was discovered in is almost never the order it should be read in.
>
> Work through these questions in order:
>
> **Hindsight shortcuts.** Now that you know the answer, is there a 3-line
> argument? The discoverer built machinery to _find_ the key step; you already
> _have_ the key step. Can the machinery be discarded? (Classic: a long
> case-bash that, in hindsight, collapses once you spot the invariant.)
>
> **Overkill.** Is any bound stronger than needed? Any construction more general
> than the problem requires? If a double exponential works but a linear function
> also works, use the linear one — the reader will wonder what the double
> exponential is hiding. Match the strength of each tool to the strength of what
> it's proving.
>
> **What to cut.** Which steps _verify_ without _illuminating_? Discovery leaves
> a debris field: sanity checks, dead ends backed out of, "note that X (we won't
> use this)". Delete them. If a paragraph can be removed and the proof still
> compiles in the reader's head, remove it.
>
> **Lemma granularity.** Inline a lemma if it's used once and the proof is ≤3
> lines. Keep it standalone if it's used twice, or if its _statement alone_
> clarifies the structure (even with a 1-line proof). Name standalone lemmas
> descriptively — "Combinatorial dimension bound", not "Lemma 2".
>
> **Order.** Lead with the main statement. Then the one idea that makes it work.
> Then the details. Isolate the one genuinely clever step — there's almost
> always exactly one — and let everything else be obviously routine _by
> contrast_.
>
> **Step names.** Number steps _and_ name them: "**Step 3: Fourier inversion and
> translation invariance.**" The name is a promise to the reader about what this
> block accomplishes. Signpost reductions explicitly: "We are reduced to showing
> that…"
>
> Output clean LaTeX using the template below. Aim for: a strong grad student
> could reconstruct every suppressed detail, a professor could skim the step
> names alone and nod.

---

## 2. LaTeX Output Template

Minimal preamble — Aletheia's environments, none of its ornament. No
`tcolorbox`, no custom colors.

```latex
\documentclass[11pt]{article}
\usepackage[margin=1.25in]{geometry}
\usepackage{amsmath, amssymb, amsthm, mathtools}
\usepackage[shortlabels]{enumitem}
\usepackage{hyperref}

\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{claim}{Claim}
\newtheorem{proposition}[theorem]{Proposition}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem*{remark}{Remark}

\begin{document}

\section*{Problem}
% Restate the problem exactly. No paraphrase.

\section*{Solution}

\begin{theorem}
% State what you will prove, in full. If the answer is "yes" or "no"
% or a specific value, state it here so the reader isn't kept in suspense.
\end{theorem}

% If a lemma is reused or structurally load-bearing, state it before
% the main proof. One-shot verifications get inlined below.
% \begin{lemma}\label{lem:key}
%   ...
% \end{lemma}
% \begin{proof} ... \end{proof}

\begin{proof}[Proof of Theorem]
\textbf{Step 1: [Descriptive name — what this step accomplishes].}
% e.g. "Reduction to the compact case." / "The key invariant."

% Display important equations; inline routine ones.
% End a reduction step with: "We are reduced to showing that ..."

\textbf{Step 2: [Name].}
% ...

\textbf{Step $n$: Conclusion.}
% One or two sentences. Make the contradiction / induction close / final
% computation land visibly.
\end{proof}

\end{document}
```

**Style conventions lifted from the Aletheia samples:**

- Display math for the equation a step _produces_; inline math for the algebra
  getting there.
- Cite precisely when invoking a named result:
  _(Jacquet–Piatetski-Shapiro–Shalika, 1981)_ — not "by a well-known theorem".
- In contradiction proofs: state the false assumption plainly ("Suppose, for
  contradiction, that…"), and flag the collision plainly ("We are led to the
  contradiction $0 > 0$.").
- Integer bounds earn the ceiling: if $d \ge n/k$ and $d \in \mathbb{Z}$, write
  $d \ge \lceil n/k \rceil$. Free sharpness.

---

## 3. Anti-Patterns to Catch

The presentation agent should flag and fix these:

- **Discovery-order exposition.** "First I tried X, which led me to notice Y…" —
  the reader doesn't care. State Y.
- **Overkill constructions.** The tell: the bound you prove is parametrically
  stronger than what the next line consumes. Weaken it until it's tight.
- **Proof by intimidation.** _"It is trivial to see that…"_, _"Obviously…"_, _"A
  standard argument shows…"_ — if it's trivial, one sentence suffices. Write the
  sentence.
- **Unnecessary generality.** Proving it for all $n$ when the problem asks about
  $n=3$ and the general case adds no insight, only indices.
- **Orphan lemmas.** Stated, proved, cited once, three lines long. Inline it.
- **Unlabeled case splits.** Five cases, no indication of why five or what
  distinguishes them. Name the cases; say upfront which one carries the content.
- **Missing signposts.** A page of computation with no "we are reduced to" / "it
  suffices to show" markers. The reader shouldn't have to reverse-engineer your
  strategy.
