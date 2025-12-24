#!/bin/bash

# Branch Protection Setup Script
# Usage: ./scripts/setup-branch-protection.sh [solo|team]

set -e

MODE=${1:-solo}
CONFIG_FILE=".github/branch-protection/${MODE}-development.json"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Error: Config file not found: $CONFIG_FILE"
  echo "Available modes: solo, team"
  exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

if [ -z "$REPO" ]; then
  echo "❌ Error: Could not detect GitHub repository"
  echo "Make sure you are in a Git repository with a remote origin"
  exit 1
fi

echo "🔧 Setting up branch protection for $REPO (mode: $MODE)"
echo ""

# Apply main branch protection
echo "📝 Applying protection to main branch..."
gh api "repos/$REPO/branches/main/protection" \
  --method PUT \
  --input <(jq '.main' "$CONFIG_FILE")

echo "✅ Main branch protection configured"
echo ""

# Apply develop branch protection
echo "📝 Applying protection to develop branch..."
gh api "repos/$REPO/branches/develop/protection" \
  --method PUT \
  --input <(jq '.develop' "$CONFIG_FILE")

echo "✅ Develop branch protection configured"
echo ""

# Disable squash and rebase merge at repository level
echo "📝 Disabling squash and rebase merge..."
gh api "repos/$REPO" \
  --method PATCH \
  -f allow_squash_merge=false \
  -f allow_rebase_merge=false \
  > /dev/null

echo "✅ Merge settings configured (merge commit only)"
echo ""

echo "🎉 Branch protection setup completed successfully!"
echo ""
echo "Configuration applied:"
echo "  - Mode: $MODE"
echo "  - Main branch: Protected"
echo "  - Develop branch: Protected"
echo "  - Merge method: Merge commit only (squash/rebase disabled)"
echo ""

# Display current settings
echo "Current protection settings:"
echo ""
echo "Main branch:"
gh api "repos/$REPO/branches/main/protection" | jq '{enforce_admins, required_linear_history, required_approving_review_count: .required_pull_request_reviews.required_approving_review_count}'
echo ""
echo "Develop branch:"
gh api "repos/$REPO/branches/develop/protection" | jq '{enforce_admins, required_linear_history, required_approving_review_count: .required_pull_request_reviews.required_approving_review_count}'
echo ""
echo "Repository merge settings:"
gh api "repos/$REPO" | jq '{allow_squash_merge, allow_merge_commit, allow_rebase_merge}'
