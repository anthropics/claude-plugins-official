#!/bin/bash
# Compile a LaTeX proof body into a standalone PDF.
# Usage: compile_pdf.sh <body.tex> <output_dir>
# The body.tex should contain just the \begin{document}...\end{document} contents
# (theorem, proof, lemmas). This script wraps it in a minimal preamble.

set -euo pipefail

BODY="$1"
OUTDIR="${2:-.}"
BASENAME=$(basename "$BODY" .tex)
FULL="$OUTDIR/${BASENAME}_full.tex"

cat > "$FULL" <<'PREAMBLE'
\documentclass[11pt]{article}
\usepackage[margin=1.25in]{geometry}
\usepackage{amsmath, amssymb, amsthm, mathtools}
\usepackage[shortlabels]{enumitem}
\usepackage{enumitem}
\usepackage[colorlinks=true, linkcolor=blue, citecolor=blue]{hyperref}

\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{claim}[theorem]{Claim}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{remark}[theorem]{Remark}

\begin{document}
PREAMBLE

cat "$BODY" >> "$FULL"

cat >> "$FULL" <<'CLOSE'
\end{document}
CLOSE

if command -v pdflatex >/dev/null 2>&1; then
    COMPILER=pdflatex
elif command -v xelatex >/dev/null 2>&1; then
    COMPILER=xelatex
else
    echo "No LaTeX compiler found" >&2
    exit 1
fi

cd "$OUTDIR"
$COMPILER -interaction=nonstopmode -halt-on-error "${BASENAME}_full.tex" >/dev/null
$COMPILER -interaction=nonstopmode -halt-on-error "${BASENAME}_full.tex" >/dev/null
echo "$OUTDIR/${BASENAME}_full.pdf"
