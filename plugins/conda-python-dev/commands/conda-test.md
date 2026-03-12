---
description: Run the pytest test suite using the Conda environment
allowed-tools: Bash(conda run:*), Bash(conda install:*), Bash(pytest:*), Bash(ls:*)
---

# Conda Test

Run the full pytest test suite for this project inside the Conda environment.

## Steps

1. Ensure pytest is available by running `conda install -n base pytest -y` (skip if already installed).
2. Run the tests: `conda run -n base pytest`
3. Report the results:
   - If all tests pass, summarize how many passed and how long they took.
   - If any tests fail, list the failing tests with their error messages and suggest next steps for fixing them.

## Notes

- If the user passes pytest arguments via `$ARGUMENTS` (e.g. a path, `-v`, `-k test_name`), append them to the pytest command.
- If no `tests/` directory or `test_*.py` files are found, inform the user that no tests were discovered.
