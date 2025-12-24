---
description: "Export private repository to public community version"
---

<!-- Language Handling: Check ~/.ypm/config.yml for settings.language -->
<!-- If language is not "en", translate all output to that language -->

# /ypm:export-community - Export Private Repository to Public Community Version

This command exports from a private repository to public community version.

First run performs interactive setup, subsequent runs execute export automatically.

## Your Role

Execute the following steps **strictly**:

---

### STEP 0: Language Detection

Check `~/.ypm/config.yml` for `settings.language` setting.

**Detection rules**:
- If `settings.language` is set, use that language
- If not set or config doesn't exist, detect from user's recent messages:
  - User's recent message contains Japanese keywords -> **Japanese**
  - Otherwise (English only) -> **English**
- Default: **English**

Note detected language internally for use in STEP 3 and STEP 4-2 AskUserQuestion.

---

### STEP 1: Check Current Directory and Branch

```bash
pwd
git branch --show-current
```

Check current directory and report to user.

---

### STEP 2: Check Configuration File Existence

```bash
ls -la .export-config.yml 2>/dev/null || echo "NOT_FOUND"
```

**Decision**:
- `.export-config.yml` **exists** -> **Skip to STEP 4**
- `.export-config.yml` **doesn't exist** -> **Proceed to STEP 3**

---

### STEP 3: Interactive Setup (First Run Only)

Use **AskUserQuestion tool** to collect the following information:

#### Question 1: Repository Configuration

Collect:
- Private repo path (current directory or custom path)
- Public repo URL (owner/name for new, URL for existing)

#### Question 2: Files to Exclude

Recommended exclusions:
- CLAUDE.md - Personal Claude Code configuration
- config.yml - Personal configuration with local paths
- PROJECT_STATUS.md - Personal project management data
- docs/research/ - Internal research documents

#### Question 3: Commit Message Sanitization

Collect sensitive keywords to remove from commit messages (comma-separated).

---

#### STEP 3-2: Create .export-config.yml

**Important**: Normalize data before generating YAML.

##### Data Normalization

1. **Private repo path**: Remove trailing slash if present
2. **Public repo URL**: Convert `owner/name` to `https://github.com/owner/name.git`

##### Generate YAML

Use **Write tool** to generate `.export-config.yml`:

```yaml
# Export Configuration for [Project Name]
# Generated: [Today's date]

export:
  private_repo: "[normalized path]"
  public_repo_url: "[normalized URL]"
  exclude_paths:
    - CLAUDE.md
    - config.yml
    - PROJECT_STATUS.md
    - docs/research/
  sanitize_patterns:
    # patterns if any
```

**After creation** -> **Proceed to STEP 4**

---

### STEP 4: Execute Export

#### STEP 4-1: Confirm Settings

```bash
yq eval '.export' .export-config.yml
```

Present settings to user.

#### STEP 4-2: Public Repository Existence Check

Check if repository exists and branch accordingly:

##### A. Repository doesn't exist (NEEDS_CREATE)
Ask user for confirmation to create repository.

##### B. Repository exists (EXISTS)
Confirm with user and proceed.

#### STEP 4-3: Execute Script

```bash
~/.claude/scripts/export-to-community.sh
```

**Script operations**:
1. If repository doesn't exist: Create, initialize main branch, set branch protection
2. Rewrite Git history (exclude sensitive files)
3. Auto-create PR
4. TruffleHog security scan

---

### STEP 5: Report Results

After script execution:
1. Check execution results
2. Report PR URL to user
3. Report TruffleHog scan results
4. **Always confirm with user before merging PR**
5. Only merge after user approval

---

## Important Notes

### GitHub CLI (gh) Command Safety Check (MANDATORY)

**When using gh commands during this command, always verify:**

#### Issue
Projects with upstream settings (private forks, etc.) may have gh command default to upstream repository. This could create PR/Issues in wrong repository.

#### Absolute Rule
**Before executing gh command, always verify current repository matches gh default repository.**

#### Safety Check Steps

```bash
# Current repository (from origin)
CURRENT_REPO=$(git remote get-url origin | sed -E 's/.*github\.com[:/](.*)(\.git)?/\1/')

# gh default repository
GH_DEFAULT_REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)

# Match check
if [ "$CURRENT_REPO" != "$GH_DEFAULT_REPO" ]; then
  echo "Warning: Repository mismatch detected"
  echo "  Current working repo: $CURRENT_REPO"
  echo "  gh default: $GH_DEFAULT_REPO"
  echo ""
  echo "Use -R flag to explicitly specify:"
  echo "  gh pr create -R $CURRENT_REPO --base develop --head feature/xxx"
  exit 1
fi
```

### Other Notes

- **PR merge requires user approval** (absolutely prohibited without)
- Dependencies: `git-filter-repo`, `yq`, `gh` (GitHub CLI), `trufflehog`
- GitHub permissions required (repository creation, branch protection)
- First setup is guided interactively
- Subsequent runs read config file and execute immediately
