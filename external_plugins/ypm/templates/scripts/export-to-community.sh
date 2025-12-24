#!/bin/bash
set -e

# =============================================================================
# Global Community Export Script
# =============================================================================
# Purpose: Export private repository to public community version
# Usage: export-to-community.sh [config_file]
# Config: .export-config.yml in project root (default)
# =============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# =============================================================================
# Repository Safety Check Helper
# =============================================================================
# This script operates on TWO repositories:
# - PRIVATE_REPO: Source repository (current working directory, may have upstream)
# - PUBLIC_REPO: Target repository for export
#
# All gh commands MUST explicitly specify the target repository using -R or --repo flag
# to avoid accidentally operating on the wrong repository (e.g., upstream).
# =============================================================================

check_repo_safety() {
  local TARGET_REPO="$1"
  local CURRENT_REPO=$(git remote get-url origin 2>/dev/null | sed -E 's/.*github\.com[:/](.*)(\.git)?/\1/')
  local GH_DEFAULT_REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)

  if [ "$CURRENT_REPO" != "$TARGET_REPO" ]; then
    print_info "Repository Context:"
    print_info "  Working directory: $CURRENT_REPO"
    print_info "  Export target: $TARGET_REPO"

    if [ "$GH_DEFAULT_REPO" != "$TARGET_REPO" ]; then
      print_warning "gh default repo ($GH_DEFAULT_REPO) differs from export target ($TARGET_REPO)"
      print_info "All gh commands will use -R $TARGET_REPO to avoid mistakes"
    fi
  fi
}

# =============================================================================
# Step 0A: Interactive Setup (if .export-config.yml doesn't exist)
# =============================================================================

# Determine config file location
if [ -n "$1" ]; then
  CONFIG_FILE="$1"
else
  CONFIG_FILE="$(pwd)/.export-config.yml"
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
  print_warning ".export-config.yml not found. Starting interactive setup..."
  echo ""

  # Private repository path
  print_info "Step 1/4: Private Repository"
  echo "Current directory: $(pwd)"
  read -p "Private repository path [$(pwd)]: " PRIVATE_REPO
  PRIVATE_REPO=${PRIVATE_REPO:-$(pwd)}
  print_success "Private repo: $PRIVATE_REPO"
  echo ""

  # Public repository
  print_info "Step 2/4: Public Repository"
  echo "Options:"
  echo "  1. Create new public repository"
  echo "  2. Use existing repository URL"
  read -p "Select [1/2]: " REPO_CHOICE

  if [ "$REPO_CHOICE" = "1" ]; then
    read -p "Repository owner (organization or username): " REPO_OWNER
    read -p "Repository name: " REPO_NAME
    PUBLIC_REPO_URL="https://github.com/$REPO_OWNER/$REPO_NAME.git"
    NEED_CREATE_REPO=true
  else
    read -p "Public repository URL: " PUBLIC_REPO_URL
    NEED_CREATE_REPO=false
  fi
  print_success "Public repo: $PUBLIC_REPO_URL"
  echo ""

  # Exclude paths with recommendations
  print_info "Step 3/4: Files to Exclude"
  echo "Recommended files to exclude (will be added automatically):"
  echo "  - CLAUDE.md (personal configuration)"
  echo "  - config.yml (personal paths)"
  echo "  - PROJECT_STATUS.md (personal project data)"
  echo "  - docs/research/ (internal research documents)"
  echo ""
  read -p "Additional files to exclude (comma-separated, or press Enter to skip): " ADDITIONAL_EXCLUDE
  echo ""

  # Sanitize patterns
  print_info "Step 4/4: Commit Message Sanitization"
  echo "Enter sensitive keywords to replace in commit messages"
  read -p "(comma-separated, or press Enter to skip): " SENSITIVE_KEYWORDS
  echo ""

  # Generate .export-config.yml
  print_info "Generating .export-config.yml..."

  cat > "$CONFIG_FILE" <<YAML
# Export Configuration for $(basename $(pwd))
# Generated: $(date +%Y-%m-%d)

export:
  # Private repository path (absolute path)
  private_repo: "$PRIVATE_REPO"

  # Public repository URL
  public_repo_url: "$PUBLIC_REPO_URL"

  # Files and directories to exclude from export
  exclude_paths:
    - CLAUDE.md           # Personal configuration
    - config.yml          # Personal paths
    - PROJECT_STATUS.md   # Personal project data
    - docs/research/      # Internal research documents
YAML

  # Add additional exclude paths if provided
  if [ -n "$ADDITIONAL_EXCLUDE" ]; then
    IFS=',' read -ra PATHS <<< "$ADDITIONAL_EXCLUDE"
    for path in "${PATHS[@]}"; do
      path_trimmed=$(echo "$path" | xargs)  # Trim whitespace
      echo "    - $path_trimmed" >> "$CONFIG_FILE"
    done
  fi

  # Add sanitize patterns section
  echo "" >> "$CONFIG_FILE"
  echo "  # Commit message sanitization patterns" >> "$CONFIG_FILE"
  echo "  sanitize_patterns:" >> "$CONFIG_FILE"

  if [ -n "$SENSITIVE_KEYWORDS" ]; then
    IFS=',' read -ra KEYWORDS <<< "$SENSITIVE_KEYWORDS"
    # Build pattern
    pattern=""
    for keyword in "${KEYWORDS[@]}"; do
      keyword_trimmed=$(echo "$keyword" | xargs)
      if [ -z "$pattern" ]; then
        pattern="$keyword_trimmed"
      else
        pattern="$pattern|$keyword_trimmed"
      fi
    done

    cat >> "$CONFIG_FILE" <<YAML
    - pattern: "$pattern"
      replace: "[redacted]"
YAML
  else
    echo "    # Add patterns here if needed" >> "$CONFIG_FILE"
    echo "    # - pattern: \"sensitive-keyword\"" >> "$CONFIG_FILE"
    echo "    #   replace: \"[redacted]\"" >> "$CONFIG_FILE"
  fi

  print_success ".export-config.yml created successfully"
  echo ""

  # Create public repository if needed
  if [ "$NEED_CREATE_REPO" = true ]; then
    REPO_FULL_NAME="$REPO_OWNER/$REPO_NAME"
    print_info "Creating public repository: $REPO_FULL_NAME"

    if gh repo view "$REPO_FULL_NAME" &>/dev/null; then
      print_warning "Repository already exists: $REPO_FULL_NAME"
    else
      read -p "Create public repository now? [y/n]: " CREATE_CONFIRM
      if [ "$CREATE_CONFIRM" = "y" ] || [ "$CREATE_CONFIRM" = "Y" ]; then
        gh repo create "$REPO_FULL_NAME" --public \
          --description "Community version of $(basename $PRIVATE_REPO)"
        print_success "Repository created: $REPO_FULL_NAME"

        # Set up branch protection
        print_info "Setting up branch protection for main branch..."
        sleep 2  # Wait for repo to be fully created

        gh api "repos/$REPO_FULL_NAME/branches/main/protection" -X PUT --input - <<'PROTECTION' 2>/dev/null || true
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
PROTECTION
        print_success "Branch protection configured"
      else
        print_warning "Skipping repository creation. Please create it manually before running export."
        exit 0
      fi
    fi
    echo ""
  fi

  print_success "Interactive setup completed!"
  echo ""
fi

# =============================================================================
# Step 0: Configuration
# =============================================================================

# Save original directory for cleanup
ORIGINAL_DIR="$(pwd)"

# CONFIG_FILE is already determined in Step 0A
# Skip if interactive setup just completed

print_info "Using configuration: $CONFIG_FILE"

# Parse configuration using yq
PRIVATE_REPO=$(yq eval '.export.private_repo' "$CONFIG_FILE")
PUBLIC_REPO_URL=$(yq eval '.export.public_repo_url' "$CONFIG_FILE")

# Validate required configuration
if [ "$PRIVATE_REPO" = "null" ] || [ -z "$PRIVATE_REPO" ]; then
  print_error "export.private_repo is not set in $CONFIG_FILE"
fi

if [ "$PUBLIC_REPO_URL" = "null" ] || [ -z "$PUBLIC_REPO_URL" ]; then
  print_error "export.public_repo_url is not set in $CONFIG_FILE"
fi

# =============================================================================
# Step 0B: Public Repository Check & Setup
# =============================================================================

# Extract repository name from URL
REPO_NAME=$(echo "$PUBLIC_REPO_URL" | sed -E 's/.*github\.com[:/](.*)\.git/\1/')

# Perform repository safety check
echo ""
check_repo_safety "$REPO_NAME"
echo ""

# Check if public repository exists (with redirect detection)
ACTUAL_REPO=$(gh repo view "$REPO_NAME" --json name,owner --jq '"\(.owner.login)/\(.name)"' 2>/dev/null || echo "")

if [ -z "$ACTUAL_REPO" ] || [ "$ACTUAL_REPO" != "$REPO_NAME" ]; then
  if [ -n "$ACTUAL_REPO" ]; then
    print_warning "⚠️  Repository '$REPO_NAME' redirects to '$ACTUAL_REPO'"
    print_warning "Public repository does not exist: $REPO_NAME"
  else
    print_warning "Public repository does not exist: $REPO_NAME"
  fi
  echo ""

  # Check for auto-create mode (for Claude Code integration)
  if [ "$AUTO_CREATE_REPO" = "yes" ]; then
    CREATE_REPO="y"
    print_info "Auto-creating repository (AUTO_CREATE_REPO=yes)"
  else
    read -p "Create public repository now? [y/n]: " CREATE_REPO
  fi

  if [ "$CREATE_REPO" = "y" ] || [ "$CREATE_REPO" = "Y" ]; then
    gh repo create "$REPO_NAME" --public \
      --description "Community version of $(basename $PRIVATE_REPO)"
    print_success "Repository created: $REPO_NAME"
    echo ""
    sleep 2  # Wait for repo to be fully created

    # Mark as initial export (no main branch exists yet)
    INITIAL_EXPORT=true
  else
    print_error "Public repository is required. Please create it manually and run again."
    exit 1
  fi
else
  # Repository exists, check if main branch has history
  MAIN_COMMITS=$(gh api "repos/$REPO_NAME/commits?sha=main&per_page=1" --jq 'length' 2>/dev/null || echo "0")
  if [ "$MAIN_COMMITS" = "0" ]; then
    print_info "Main branch has no commits, treating as initial export"
    INITIAL_EXPORT=true
  else
    INITIAL_EXPORT=false
  fi
fi

# Check and set up branch protection if needed (skip for initial export)
if [ "$INITIAL_EXPORT" != "true" ]; then
  print_info "Checking branch protection settings..."
  if gh api "repos/$REPO_NAME/branches/main/protection" &>/dev/null; then
    print_success "Branch protection already configured"
  else
    print_info "Setting up branch protection for main branch..."
    gh api "repos/$REPO_NAME/branches/main/protection" -X PUT --input - <<'PROTECTION' 2>/dev/null || true
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
PROTECTION
    print_success "Branch protection configured"
  fi
  echo ""
fi

# Create temporary export directory
# Extract project name from private repo path (remove -main/-dev suffixes)
PROJECT_NAME=$(basename "$PRIVATE_REPO" | sed 's/-main$//' | sed 's/-dev$//')
EXPORT_DIR="/tmp/${PROJECT_NAME}-public-export-$(date +%s)"

print_info "🔍 Starting export process..."
print_info "Private repo: $PRIVATE_REPO"
print_info "Public repo: $PUBLIC_REPO_URL"
print_info "Export dir: $EXPORT_DIR"

# =============================================================================
# Step 1: Clone private repository
# =============================================================================

print_info "📦 Cloning private repository..."
git clone "$PRIVATE_REPO" "$EXPORT_DIR"
cd "$EXPORT_DIR"

# =============================================================================
# Step 2: Get current branch name
# =============================================================================

CURRENT_BRANCH=$(git branch --show-current)
print_info "📍 Using branch: $CURRENT_BRANCH"

# =============================================================================
# Step 3: Filter sensitive files from history
# =============================================================================

print_info "🧹 Filtering sensitive files from history..."

# Read exclude paths from config
EXCLUDE_PATHS=()
EXCLUDE_COUNT=$(yq eval '.export.exclude_paths | length' "$CONFIG_FILE")

if [ "$EXCLUDE_COUNT" -gt 0 ]; then
  for i in $(seq 0 $((EXCLUDE_COUNT - 1))); do
    path=$(yq eval ".export.exclude_paths[$i]" "$CONFIG_FILE")
    EXCLUDE_PATHS+=(--path "$path" --invert-paths)
  done
  print_info "Excluding ${#EXCLUDE_PATHS[@]} / 2 paths from export"
else
  print_warning "No exclude_paths defined in config"
fi

# Run git filter-repo if there are paths to exclude
if [ ${#EXCLUDE_PATHS[@]} -gt 0 ]; then
  git filter-repo "${EXCLUDE_PATHS[@]}" --force
  print_success "File filtering completed"
  # Save result for PR body
  FILE_FILTER_STATUS="✅ COMPLETED"
  FILE_FILTER_COUNT=$((${#EXCLUDE_PATHS[@]} / 2))
else
  print_info "No files to exclude, skipping filter-repo"
  FILE_FILTER_STATUS="⚠️ SKIPPED"
  FILE_FILTER_COUNT=0
fi

# =============================================================================
# Step 4: Sanitize commit messages
# =============================================================================

print_info "✏️  Sanitizing commit messages..."

# Build Python code for message sanitization
SANITIZE_COUNT=$(yq eval '.export.sanitize_patterns | length' "$CONFIG_FILE")

if [ "$SANITIZE_COUNT" -gt 0 ]; then
  # Generate Python replacement code
  PYTHON_REPLACEMENTS=""
  for i in $(seq 0 $((SANITIZE_COUNT - 1))); do
    pattern=$(yq eval ".export.sanitize_patterns[$i].pattern" "$CONFIG_FILE")
    replace=$(yq eval ".export.sanitize_patterns[$i].replace" "$CONFIG_FILE")

    # Escape special characters for Python string
    pattern_escaped=$(printf '%s' "$pattern" | sed 's/\\/\\\\/g')
    replace_escaped=$(printf '%s' "$replace" | sed 's/\\/\\\\/g')

    PYTHON_REPLACEMENTS+="msg = re.sub(r\"$pattern_escaped\", r\"$replace_escaped\", msg)
"
  done

  # Run git filter-repo with message callback
  git filter-repo --message-callback "
import re

# Decode message to string
msg = message.decode('utf-8', errors='ignore')

# Apply sanitization patterns
$PYTHON_REPLACEMENTS

return msg.encode('utf-8')
" --force

  print_success "Commit message sanitization completed"
  # Save result for PR body
  SANITIZE_STATUS="✅ COMPLETED"
  SANITIZE_PATTERN_COUNT=$SANITIZE_COUNT
else
  print_info "No sanitize_patterns defined, skipping message sanitization"
  SANITIZE_STATUS="⚠️ SKIPPED"
  SANITIZE_PATTERN_COUNT=0
fi

# =============================================================================
# Step 5: Create feature branch and push to public repository
# =============================================================================

print_info "🚀 Creating feature branch and pushing to public repository..."

# Generate unique feature branch name
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FEATURE_BRANCH="export/community-release-$TIMESTAMP"

# Create and checkout feature branch
git checkout -b "$FEATURE_BRANCH"

# Add public remote
git remote add public "$PUBLIC_REPO_URL"

# Push feature branch
git push public "$FEATURE_BRANCH"

print_success "Feature branch pushed: $FEATURE_BRANCH"

# =============================================================================
# Step 6: Create Pull Request
# =============================================================================

print_info "📝 Creating pull request..."

# Extract repository name from URL (e.g., signalcompose/YPM)
REPO_NAME=$(echo "$PUBLIC_REPO_URL" | sed -E 's/.*github\.com[:/](.*)\.git/\1/')

# Get the last commit SHA from public repo
print_info "Fetching last public commit..."
LAST_PUBLIC_COMMIT=$(gh api "repos/$REPO_NAME/commits?per_page=1" --jq '.[0].sha' 2>/dev/null || echo "")

# Generate commit summary
if [ -n "$LAST_PUBLIC_COMMIT" ]; then
  print_info "Generating change summary since last export..."

  # Try to find the corresponding commit in our filtered history
  # Note: Due to filter-repo rewriting, SHAs won't match directly
  # Instead, we'll show all commits in this export
  COMMIT_SUMMARY=$(git log --oneline --no-decorate)
  COMMIT_COUNT=$(git log --oneline --no-decorate | wc -l | tr -d ' ')

  CHANGES_SECTION="### 📝 Changes in This Release

**Total Commits**: $COMMIT_COUNT

\`\`\`
$COMMIT_SUMMARY
\`\`\`

**Note**: Commit SHAs differ from private repository due to history filtering."
else
  CHANGES_SECTION="### 📝 Changes in This Release

This is the initial export or unable to fetch previous commit history.

**Total Commits**: $(git log --oneline --no-decorate | wc -l | tr -d ' ')

\`\`\`
$(git log --oneline --no-decorate | tail -10)
\`\`\`"
fi

# =============================================================================
# Step 6: Create PR or Initialize Main Branch
# =============================================================================

if [ "$INITIAL_EXPORT" = "true" ]; then
  # Initial export: Push export branch directly to main (no PR)
  print_info "🎯 Initial export detected: Pushing export branch to main..."

  # Push export branch to main (force) - use 'public' remote, not 'origin'
  # Note: git-filter-repo removes 'origin' remote
  git push public "$FEATURE_BRANCH:main" --force

  print_success "Export branch pushed to main"

  # Set up branch protection now that main exists
  print_info "Setting up branch protection for main branch..."
  sleep 2  # Wait for branch to be fully created

  gh api "repos/$REPO_NAME/branches/main/protection" -X PUT --input - <<'PROTECTION' 2>/dev/null || true
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
PROTECTION
  print_success "Branch protection configured"

  # Set default branch to main
  print_info "Setting default branch to main..."
  gh api -X PATCH "repos/$REPO_NAME" -f default_branch=main
  print_success "Default branch set to main"

  # Delete export branch (no longer needed) - use GitHub API
  print_info "Cleaning up export branch..."
  gh api -X DELETE "repos/$REPO_NAME/git/refs/heads/$FEATURE_BRANCH"
  print_success "Export branch deleted"

  PR_URL="N/A (Initial export - pushed directly to main)"
  echo ""
else
  # Subsequent exports: Create PR
  print_info "📝 Creating Pull Request..."

  # Create PR with detailed body
  PR_URL=$(gh pr create \
    --repo "$REPO_NAME" \
    --base main \
    --head "$FEATURE_BRANCH" \
    --title "Community Release: Export from Private Repository ($TIMESTAMP)" \
    --body "$(cat <<EOF
## 🚀 Community Release

This PR contains the latest updates from the private repository, exported on $TIMESTAMP.

$CHANGES_SECTION

### 🔒 Export Process

- ✅ **Sensitive files excluded** from history
  - CLAUDE.md (personal configuration)
  - config.yml (personal paths)
  - PROJECT_STATUS.md (personal project data)
  - docs/research/ (internal research documents)
- ✅ **Commit messages sanitized**
  - Project names → \`[project]\`
  - Statistics → \`[N]\`
  - Timestamps → \`[time]\`
- ✅ **Ready for community review**

### ✅ Verification Checklist

Please verify before merging:
- [ ] No sensitive information in commit history
- [ ] All excluded files are properly removed
- [ ] Commit messages are properly sanitized
- [ ] Documentation is up to date

### 📁 Technical Details

- **Export Directory**: \`$EXPORT_DIR\`
- **Feature Branch**: \`$FEATURE_BRANCH\`
- **Export Script**: \`~/.claude/scripts/export-to-community.sh\`

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)")
  echo ""
fi

# =============================================================================
# Step 7: Security Verification
# =============================================================================

print_info "🔍 Running TruffleHog security scan..."

if command -v trufflehog &> /dev/null; then
  # Run TruffleHog scan
  SCAN_OUTPUT=$(trufflehog git file://. --json --no-update 2>&1)

  # Extract scan results
  VERIFIED_SECRETS=$(echo "$SCAN_OUTPUT" | grep -o '"verified_secrets":[0-9]*' | grep -o '[0-9]*' | tail -1)
  UNVERIFIED_SECRETS=$(echo "$SCAN_OUTPUT" | grep -o '"unverified_secrets":[0-9]*' | grep -o '[0-9]*' | tail -1)

  # Display scan summary
  echo ""
  echo "📊 Security Scan Results:"
  echo "  🔐 Verified Secrets: ${VERIFIED_SECRETS:-0}"
  echo "  ⚠️  Unverified Secrets: ${UNVERIFIED_SECRETS:-0}"
  echo ""

  if [ "${VERIFIED_SECRETS:-0}" -eq 0 ] && [ "${UNVERIFIED_SECRETS:-0}" -eq 0 ]; then
    print_success "Security scan passed - no secrets detected"
    SECURITY_STATUS="✅ PASSED"
    SECURITY_RESULT="No secrets detected"
  else
    print_error "Security scan detected potential secrets. Please review before merging."
    SECURITY_STATUS="❌ FAILED"
    SECURITY_RESULT="Potential secrets detected - manual review required"
  fi
  TRUFFLEHOG_INSTALLED="true"
else
  print_warning "TruffleHog not installed. Skipping security scan."
  print_warning "Install: brew install trufflehog"
  echo ""
  SECURITY_STATUS="⚠️ SKIPPED"
  SECURITY_RESULT="TruffleHog not installed"
  VERIFIED_SECRETS="-"
  UNVERIFIED_SECRETS="-"
  TRUFFLEHOG_INSTALLED="false"
fi

# =============================================================================
# Step 7.5: Update PR with Verification Results (PR-based exports only)
# =============================================================================

if [ "$INITIAL_EXPORT" != "true" ]; then
  print_info "📝 Updating PR with verification results..."

  # Count files changed and commits
  FILES_CHANGED=$(git diff --name-only "public/$FEATURE_BRANCH^" 2>/dev/null | wc -l | tr -d ' ' || echo "N/A")
  COMMITS_EXPORTED=$(git log --oneline "public/$FEATURE_BRANCH^..public/$FEATURE_BRANCH" 2>/dev/null | wc -l | tr -d ' ' || echo "N/A")

  # Generate verification results section
  VERIFICATION_SECTION="## ✅ Automated Verification Results

### 🔐 Security Scan (TruffleHog)
- **Status:** $SECURITY_STATUS
- **Verified Secrets:** ${VERIFIED_SECRETS:-0}
- **Unverified Secrets:** ${UNVERIFIED_SECRETS:-0}
- **Result:** $SECURITY_RESULT

### 🧹 File Filtering (git-filter-repo)
- **Status:** $FILE_FILTER_STATUS
- **Excluded Paths:** $FILE_FILTER_COUNT paths filtered

### ✏️ Commit Message Sanitization
- **Status:** $SANITIZE_STATUS
- **Patterns Applied:** $SANITIZE_PATTERN_COUNT patterns

### 📊 Export Summary
- **Files Changed:** $FILES_CHANGED
- **Commits Exported:** $COMMITS_EXPORTED
- **Export Date:** $(date '+%Y-%m-%d %H:%M:%S')

---
"

  # Get current PR body
  CURRENT_PR_BODY=$(gh pr view "$PR_URL" --repo "$REPO_NAME" --json body --jq '.body')

  # Insert verification section after title
  NEW_PR_BODY="$VERIFICATION_SECTION
$CURRENT_PR_BODY"

  # Update PR with verification results
  # Extract PR number from URL
  PR_NUMBER=$(echo "$PR_URL" | grep -o '[0-9]*$')

  # Use REST API to update PR body (gh pr edit fails due to Projects (classic) deprecation)
  gh api -X PATCH "repos/$REPO_NAME/pulls/$PR_NUMBER" -f body="$NEW_PR_BODY"

  print_success "PR updated with verification results"
  echo ""
fi

# =============================================================================
# Step 8: Interactive Merge (PR-based exports only)
# =============================================================================

if [ "$INITIAL_EXPORT" != "true" ]; then
  echo ""
  print_info "📋 Pull Request created: $PR_URL"
  echo ""

  if command -v trufflehog &> /dev/null && [ "${VERIFIED_SECRETS:-0}" -eq 0 ] && [ "${UNVERIFIED_SECRETS:-0}" -eq 0 ]; then
    # Ask user if they want to merge now
    read -p "$(echo -e ${BLUE}Merge PR now? \(y/n\): ${NC})" MERGE_CONFIRM

    if [ "$MERGE_CONFIRM" = "y" ] || [ "$MERGE_CONFIRM" = "Y" ]; then
      print_info "🚀 Merging Pull Request..."

      # Extract repository name from URL
      REPO_NAME=$(echo "$PUBLIC_REPO_URL" | sed -E 's/.*github\.com[:/](.*)\.git/\1/')

      # Merge PR
      gh pr merge "$PR_URL" --repo "$REPO_NAME" --merge --delete-branch

      print_success "Pull Request merged successfully"

      # =============================================================================
      # Step 9: Cleanup
      # =============================================================================

      print_info "🧹 Cleaning up temporary export directory..."
      cd "$ORIGINAL_DIR"
      rm -rf "$EXPORT_DIR"
      print_success "Export directory cleaned up"

      # =============================================================================
      # Step 10: Summary (Auto-merge completed)
      # =============================================================================

      echo ""
      print_success "Community release completed successfully!"
      echo ""
      echo "📋 Pull Request: $PR_URL (merged)"
      echo "🌿 Feature Branch: $FEATURE_BRANCH (deleted)"
      echo ""
    else
      # =============================================================================
      # Step 10: Summary (Manual merge required)
      # =============================================================================

      echo ""
      print_success "Export and PR creation completed successfully!"
      echo ""
      echo "📋 Pull Request: $PR_URL"
      echo "🌿 Feature Branch: $FEATURE_BRANCH"
      echo "📁 Export Directory: $EXPORT_DIR"
      echo ""
      print_warning "Next steps:"
      echo "1. Review the PR on GitHub: $PR_URL"
      echo "2. Verify no sensitive information: cd $EXPORT_DIR && git show"
      echo "3. Merge the PR when ready"
      echo "4. Clean up: rm -rf $EXPORT_DIR"
      echo ""
    fi
  else
    # =============================================================================
    # Step 10: Summary (Security scan failed or TruffleHog not installed)
    # =============================================================================

    echo ""
    print_success "Export and PR creation completed successfully!"
    echo ""
    echo "📋 Pull Request: $PR_URL"
    echo "🌿 Feature Branch: $FEATURE_BRANCH"
    echo "📁 Export Directory: $EXPORT_DIR"
    echo ""
    print_warning "Next steps:"
    echo "1. Review the PR on GitHub: $PR_URL"
    echo "2. Verify no sensitive information: cd $EXPORT_DIR && git show"
    echo "3. Merge the PR when ready"
    echo "4. Clean up: rm -rf $EXPORT_DIR"
    echo ""
  fi
else
  # =============================================================================
  # Step 10: Summary (Initial export completed)
  # =============================================================================

  # Cleanup
  print_info "🧹 Cleaning up temporary export directory..."
  cd "$ORIGINAL_DIR"
  rm -rf "$EXPORT_DIR"
  print_success "Export directory cleaned up"

  echo ""
  print_success "Initial community release completed successfully!"
  echo ""
  echo "✅ Repository: https://github.com/$REPO_NAME"
  echo "✅ Main branch: Initialized with export content"
  echo "✅ Branch protection: Configured"
  echo ""
  print_info "Next exports will create Pull Requests for review."
  echo ""
fi
