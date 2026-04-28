#!/bin/bash
# Exit 0 if a LaTeX compiler is available, 1 otherwise.
# Used by SKILL.md to decide whether to offer PDF compilation.
command -v pdflatex >/dev/null 2>&1 || command -v xelatex >/dev/null 2>&1
