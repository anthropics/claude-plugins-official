---
description: Set up a Conda Python development environment from an environment.yml file
allowed-tools: Bash(conda env update:*), Bash(conda info:*), Bash(conda env list:*), Bash(cat:*), Bash(ls:*)
---

# Conda Environment Setup

Set up the Python development environment using Conda for the current project.

## Steps

1. Check if `environment.yml` exists in the project root. If it does not exist, inform the user and stop.
2. Run `conda env update --file environment.yml --name base --prune` to install or update all dependencies.
3. Verify the environment was set up correctly by running `conda info` and listing installed packages with `conda env list`.
4. Report success with a summary of what was installed, or report any errors clearly so the user can act on them.

## Notes

- Use `--prune` to remove packages that are no longer in `environment.yml`.
- If the user passes a custom environment name via `$ARGUMENTS`, use that name instead of `base`.
