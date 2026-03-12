---
description: Lint Python source code using flake8 via Conda
allowed-tools: Bash(conda run:*), Bash(conda install:*), Bash(flake8:*), Bash(ls:*)
---

# Conda Lint

Lint the Python source code in this project using flake8 inside the Conda environment.

## Steps

1. Ensure flake8 is available by running `conda install -n base flake8 -y` (skip if already installed).
2. Run a strict check first — stop the build on any Python syntax errors or undefined names:
   `conda run -n base flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
3. If the strict check passes, run a full linting pass treating all other issues as warnings:
   `conda run -n base flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics`
4. Report the results clearly. If there are errors from step 2, list them and stop. If there are only warnings from step 3, summarize them and suggest fixes.

## Notes

- If the user passes a path or file via `$ARGUMENTS`, lint only that path instead of `.`.
- The 127-character line length limit matches the GitHub editor width standard.
