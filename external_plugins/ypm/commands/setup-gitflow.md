---
description: "Set up Git Flow workflow with branch protection and security settings"
---

<!-- Language Handling: Check ~/.ypm/config.yml for settings.language -->
<!-- If language is not "en", translate all output to that language -->

# Git Flow Setup Command

Set up Git Flow workflow for the current project with branch protection and security settings.

## What This Command Does

1. **Repository Check** - Verify GitHub repository registration
2. **Branch Structure** - Create main (default) and develop branches
3. **Branch Protection** - Protect main/develop from direct pushes
4. **Merge Settings** - Disable squash/rebase merge (merge commit only)
5. **Security Settings** - CODEOWNERS, Secret Scanning (based on project type)

---

## Execution Steps

### STEP 0: Project Type Selection

Ask user about project type to determine security settings:

**Question**: What type of project is this?

1. **Personal Project (no forks)**
   - Solo development
   - No external contributions

2. **Small OSS (trusted contributors)**
   - Few trusted contributors
   - Accept PRs from forks

3. **Large OSS / Security Critical**
   - Many external contributors
   - CI/CD uses secrets
   - Security is important

#### Recommended Settings by Project Type

| Setting | Personal | Small OSS | Large OSS |
|---------|----------|-----------|-----------|
| **Visibility** | Private | Public | Public |
| **Secret Scanning** | Not needed | Recommended | Required |
| **CODEOWNERS** | Not needed | Recommended | Required |
| **develop protection** | Optional | Recommended | Required |
| **enforce_admins** | false | false | true/false |
| **Fork PR restriction** | Not needed | Optional | Recommended |
| **Auto-merge disabled** | Not needed | Not needed | Optional |

**Question**: What is the development style?

1. **Solo Development** - enforce_admins=false (admin bypass allowed)
2. **Team Development** - enforce_admins=true (all rules apply to everyone)

---

### STEP 1: Repository Registration Check

```bash
# Check remote repository
git remote -v

# Get GitHub repository info
gh repo view --json nameWithOwner,isPrivate,defaultBranchRef 2>/dev/null
```

**If repository exists**: Proceed to branch setup
**If not registered**: Guide user to create repository first

---

### STEP 2: Repository Creation (if not registered)

```bash
# Initialize Git repository (if not initialized)
if [ ! -d .git ]; then
  git init
  git add .
  git commit -m "Initial commit"
fi

# Create GitHub repository
gh repo create <REPO_NAME> --private --source=. --remote=origin --push
```

---

### STEP 3: Branch Structure

#### 3.1 Create develop branch

```bash
# Ensure main branch exists
git checkout -b main 2>/dev/null || git checkout main

# Initial commit (if none exists)
if [ -z "$(git log -1 2>/dev/null)" ]; then
  echo "# $(basename $(pwd))" > README.md
  git add README.md
  git commit -m "Initial commit"
  git push -u origin main
fi

# Create develop branch
git checkout -b develop
git push -u origin develop
```

#### 3.2 Verify Default Branch

```bash
# Verify main is the default branch (usually already set)
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'

# If not main, change it:
# gh repo edit --default-branch main
```

---

### STEP 4: Branch Protection Settings

#### 4.1 Create branch protection JSON

```bash
cat > /tmp/branch_protection.json <<EOF
{
  "required_status_checks": null,
  "enforce_admins": <ENFORCE_ADMINS>,
  "required_pull_request_reviews": {
    "required_approving_review_count": <REVIEWER_COUNT>,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false
}
EOF
```

**Parameters**:
- `<ENFORCE_ADMINS>`: Solo=`false`, Team=`true`
- `<REVIEWER_COUNT>`: Solo=`1` (bypass allowed), Team=`1` (required)

#### 4.2 Apply protection to main

```bash
gh api repos/:owner/:repo/branches/main/protection \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  --input /tmp/branch_protection.json
```

#### 4.3 Apply protection to develop

```bash
gh api repos/:owner/:repo/branches/develop/protection \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  --input /tmp/branch_protection.json
```

#### 4.4 Repository-level merge settings (REQUIRED)

**Important**: Disable squash and rebase merge at repository level

```bash
gh api repos/:owner/:repo \
  -X PATCH \
  -H "Accept: application/vnd.github+json" \
  -f allow_squash_merge=false \
  -f allow_rebase_merge=false \
  -f allow_merge_commit=true
```

**Why**: Git Flow requires merge commits. Squash/rebase destroys Git Flow history.

---

### STEP 5: Security Settings (based on project type)

#### 5.1 CODEOWNERS (Small OSS / Large OSS)

```bash
mkdir -p .github
cat > .github/CODEOWNERS <<'EOF'
# CODEOWNERS
# Important file changes require approval

# Global
* @<OWNER>

# GitHub config
/.github/ @<OWNER>

# CI/CD
/.github/workflows/ @<OWNER>

# Dependencies
/package.json @<OWNER>
/requirements.txt @<OWNER>

# Security
/.gitignore @<OWNER>
EOF

git add .github/CODEOWNERS
git commit -m "chore: Add CODEOWNERS for security"
git push
```

**Note**: Replace `<OWNER>` with repository owner's GitHub username.

#### 5.2 Secret Scanning (Public repositories only)

```bash
gh api repos/:owner/:repo \
  -X PATCH \
  -H "Accept: application/vnd.github+json" \
  -f security_and_analysis='{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}'
```

#### 5.3 Fork settings (OSS)

```bash
gh api repos/:owner/:repo \
  -X PATCH \
  -H "Accept: application/vnd.github+json" \
  -f allow_forking=true \
  -f allow_auto_merge=false
```

---

### STEP 6: Verification

```bash
# Check branches
git branch -a

# Check default branch
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'

# Check branch protection
gh api repos/:owner/:repo/branches/main/protection

# Check merge settings
gh api repos/:owner/:repo --jq '{allow_squash_merge, allow_merge_commit, allow_rebase_merge}'
```

---

## Completion Message

```
Git Flow Setup Complete!

【Branch Structure】
- main: Production (default, protected)
- develop: Development (protected)

【Branch Protection】
- Direct push to main/develop: Disabled
- Pull Request merge only: Enabled
- Merge commit required (squash disabled)
- Reviewers: <N>
- Admin bypass: <based on enforce_admins>
- required_linear_history: false (Git Flow compatible)

【Merge Settings】
- allow_squash_merge: false
- allow_rebase_merge: false
- allow_merge_commit: true

【Security Settings】
<List applied settings based on project type>

【Git Workflow Absolute Prohibitions】
- main -> develop reverse flow (MOST IMPORTANT)
- Direct commits to main/develop branches
- Squash merge (destroys Git Flow history)

【Next Steps】
1. New feature: `git checkout -b feature/<name>` from develop
2. Commit & push changes
3. Create Pull Request (develop <- feature)
4. After review, merge to develop (use merge commit)
5. Release: Create Pull Request (main <- develop)
6. After release, tag: `git tag v1.0.0`

【Important】
- Direct PR from develop to main is allowed ONLY for releases
- Reverse direction (main -> develop) is ABSOLUTELY PROHIBITED
- Always use "Create a merge commit" when merging
```

---

## Troubleshooting

### gh command not found

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login
```

### Branch protection failed

- Admin permission required for repository
- For organizations, check organization settings

### CODEOWNERS not working

- Enable "Require review from Code Owners" in branch protection
- Settings > Branches > Branch protection rules > main

---

## References

- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
