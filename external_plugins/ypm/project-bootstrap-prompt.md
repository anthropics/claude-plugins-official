# Project Startup Support Prompt

## ⚠️ Important: Purpose of This Prompt

**The sole purpose of this prompt (the `/ypm:new` command) is to strictly follow the bootstrap flow and complete project implementation preparation safely and quickly.**

### Absolute Principles to Follow

1. **Strictly Follow the Bootstrap Flow**
   - Execute Phases 1-8 in order
   - Do not skip or omit phases
   - Always confirm when user interaction is required

2. **Never Perform Implementation**
   - YPM is for preparation only. Implementation and test code creation are prohibited
   - After preparation is complete, guide users to work in a separate session

3. **Visualize Progress**
   - Clearly indicate current position in each phase
   ```
   ## [Project Name] - Bootstrap Progress

   ✅ Phase 1: Project Planning
   ✅ Phase 2: Project Directory Creation
   🔄 Phase 3: Documentation Setup ← Currently here
   ⏳ Phase 4: GitHub Integration
   ⏳ Phase 5: Git Workflow Configuration
   ⏳ Phase 6: Environment Configuration Files
   ⏳ Phase 7: Documentation Management Rules
   ⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
   ```

4. **Ensure Safety**
   - Avoid destructive operations
   - Always ask for confirmation when user input is required

5. **Speed**
   - Efficient requirements gathering
   - Utilize templates
   - Skip unnecessary dialogue

---

We will guide you through the planning and initial setup of a new project step by step.

## Phase 1: Project Planning

**Progress Display**:
```
🔄 Phase 1: Project Planning ← Currently here
⏳ Phase 2: Project Directory Creation
⏳ Phase 3: Documentation Setup
⏳ Phase 4: GitHub Integration
⏳ Phase 5: Git Workflow Configuration
⏳ Phase 6: Environment Configuration Files
⏳ Phase 7: Documentation Management Rules
⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
```

First, we will gather requirements through dialogue:

1. **Project Overview Hearing**
   - What kind of project do you want to create? (purpose, features, tech stack)
   - Target users and use cases

2. **Requirements Definition Creation**
   - Functional requirements (essential features, priorities)
   - Non-functional requirements (performance, security, scalability)
   - Technology selection rationale

3. **Basic Project Information Decisions**
   - Project name
   - Overview description (short and long)
   - Programming languages and frameworks

Once requirements are defined, we will create necessary documents such as system specifications and architecture diagrams.

### ✅ Phase 1 Completion Confirmation

**YPM will verify:**
- Is the project overview clear?
- Are requirements defined?
- Are project name and tech stack decided?

**After confirming all items are complete, report to user:**

"✅ Phase 1 (Project Planning) is complete.

Confirmed details:
- Project name: [Project name]
- Tech stack: [Tech stack]
- Requirements: [Requirements summary]

May I proceed to Phase 2 (Project Directory Creation)?"

**After receiving user approval:**
1. Re-read Phase 2 of the bootstrap prompt (internal operation)
2. Review Phase 2 content (internal operation)
3. Start Phase 2

## Phase 2: Project Directory Creation

**Progress Display**:
```
✅ Phase 1: Project Planning
🔄 Phase 2: Project Directory Creation ← Currently here
⏳ Phase 3: Documentation Setup
⏳ Phase 4: GitHub Integration
⏳ Phase 5: Git Workflow Configuration
⏳ Phase 6: Environment Configuration Files
⏳ Phase 7: Documentation Management Rules
⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
```

1. **Local Directory Verification**
   - Please provide the path for your project git directory
   - If the directory doesn't exist, we will create it

2. **Git Initialization**
   - Run `git init`
   - Create initial README.md for the first commit

### ✅ Phase 2 Completion Confirmation

**YPM will verify:**
- Has the project directory been created?
- Has the Git repository been initialized? (Does `.git/` directory exist?)
- Has README.md been created?

**After confirming all items are complete, report to user:**

"✅ Phase 2 (Project Directory Creation) is complete.

Created deliverables:
- Project directory: [Path]
- Git repository initialization complete
- README.md creation complete

May I proceed to Phase 3 (Documentation Setup)?"

**After receiving user approval:**
1. Re-read Phase 3 of the bootstrap prompt (internal operation)
2. Review Phase 3 content (internal operation)
3. Start Phase 3

## Phase 3: Documentation Setup

**Progress Display**:
```
✅ Phase 1: Project Planning
✅ Phase 2: Project Directory Creation
🔄 Phase 3: Documentation Setup ← Currently here
⏳ Phase 4: GitHub Integration
⏳ Phase 5: Git Workflow Configuration
⏳ Phase 6: Environment Configuration Files
⏳ Phase 7: Documentation Management Rules
⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
```

### 🎯 Core Principle: DDD (Documentation Driven Development)

**All development starts with documentation.**

- **DDD = Documentation Driven Development**
  - Not to be confused with Domain-Driven Design
  - Development flow: **Specification creation → Implementation → Testing → Documentation update**
  - **Documentation is the Single Source of Truth**
  - No tolerance for divergence between code and documentation

This principle ensures:
✅ Requirements are clear before implementation
✅ Teams (or your future self) won't get lost
✅ Easy onboarding for new members
✅ Design consistency is maintained

### 1. **Create docs/ Directory**
   - Create the following under `docs/`:
     - **INDEX.md** (documentation index and management)
     - Requirements specification (requirements.md)
     - System specifications (specifications.md)
     - Architecture design (architecture.md)
     - Development guidelines (development-guide.md)

### 2. **Introduce Development Rules**

   - **TDD (Test Driven Development)**
     - Follow Red → Green → Refactor cycle
     - Write tests before implementation
     - Set test coverage targets

   - **DRY (Don't Repeat Yourself)**
     - Avoid code duplication
     - Extract common logic
     - Design reusable components

### 3. **Prepare Research Directory**
   - Create `docs/research/`
   - Include the following in README.md:
     - "Planned for future sub-repository conversion"
     - "Location for documenting research conducted with gemini commands or WebFetch"

### ✅ Phase 3 Completion Confirmation

**YPM will verify:**
- Has docs/INDEX.md been created?
- Have the 4 basic documents (requirements.md, specifications.md, architecture.md, development-guide.md) been created under docs/?
- Have docs/research/ directory and README.md been created?
- Are development principles (DDD, TDD, DRY) documented?

**After confirming all items are complete, report to user:**

"✅ Phase 3 (Documentation Setup) is complete.

Created deliverables:
- docs/INDEX.md (documentation index)
- docs/requirements.md (requirements specification)
- docs/specifications.md (system specifications)
- docs/architecture.md (architecture design)
- docs/development-guide.md (development guidelines)
- docs/research/ (directory for storing research)

May I proceed to Phase 4 (GitHub Integration)?"

**After receiving user approval:**
1. Re-read Phase 4 of the bootstrap prompt (internal operation)
2. Review Phase 4 content (internal operation)
3. Start Phase 4

## Phase 4: GitHub Integration

**Progress Display**:
```
✅ Phase 1: Project Planning
✅ Phase 2: Project Directory Creation
✅ Phase 3: Documentation Setup
🔄 Phase 4: GitHub Integration ← Currently here
⏳ Phase 5: Git Workflow Configuration
⏳ Phase 6: Environment Configuration Files
⏳ Phase 7: Documentation Management Rules
⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
```

1. **Obtain GitHub Account Information**
   - Please provide your GitHub account name
   - Get and display organizations with `gh api user/orgs`
   - Select personal account or organization

2. **Repository Creation**
   - **"We will create a Private repository. Is this acceptable?" - Confirm with user**
   - After user approval, create repository with `gh repo create --private`
   - Perform initial push
   - *Note: If you want to make it public, you can manually change to Public once ready

### ✅ Phase 4 Completion Confirmation

**YPM will verify:**
- Has the GitHub repository been created?
- Has the local repository been pushed to GitHub?

**After confirming all items are complete, report to user:**

"✅ Phase 4 (GitHub Integration) is complete.

Created deliverables:
- GitHub repository: [Repository URL]
- Initial push complete

May I proceed to Phase 5 (Git Workflow Configuration)?"

**After receiving user approval:**
1. Re-read Phase 5 of the bootstrap prompt (internal operation)
2. Review Phase 5 content (internal operation)
3. Start Phase 5

## Phase 5: Git Workflow Configuration

**Progress Display**:
```
✅ Phase 1: Project Planning
✅ Phase 2: Project Directory Creation
✅ Phase 3: Documentation Setup
✅ Phase 4: GitHub Integration
🔄 Phase 5: Git Workflow Configuration ← Currently here
⏳ Phase 6: Environment Configuration Files
⏳ Phase 7: Documentation Management Rules
⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
```

1. **Confirm Workflow Necessity**
   - Do you want to introduce Git Flow? (Recommended for multi-developer projects)

2. **Configuration for Introduction**
   - **Set default branch to `develop`** (Important)
     ```bash
     gh api repos/:owner/:repo -X PATCH -f default_branch=develop
     ```
   - Reason:
     - `main` is the release branch (production environment)
     - `develop` is the development branch (for development work)
     - Development is done on `develop`, so `develop` is the default

   - **Select Development Style** (newly added)
     - Confirm with user:
       ```
       Please select the development style for this project:

       1️⃣ Solo Development (Recommended)
          - You develop alone
          - Admin bypass enabled
          - Review recommended (not enforced)

       2️⃣ Team Development
          - Multiple developers
          - Protection rules apply to admins too
          - Review required

       Choice: [1/2]
       ```

   - **Branch Protection Rules Configuration**

     **⚠️ Important Design Principle**:
     - **Git Flow requires merge commits**
     - Set `required_linear_history: false` (prohibit squash merge)
     - Squash merge destroys history and causes main/develop history to diverge

     **For Solo Development**:
     ```bash
     # main branch
     gh api repos/:owner/:repo/branches/main/protection -X PUT --input - <<'EOF'
     {
       "required_status_checks": null,
       "enforce_admins": false,
       "required_pull_request_reviews": {
         "dismiss_stale_reviews": true,
         "require_code_owner_reviews": false,
         "required_approving_review_count": 1
       },
       "restrictions": null,
       "allow_force_pushes": false,
       "allow_deletions": false,
       "required_linear_history": false
     }
     EOF

     # develop branch (with review settings)
     gh api repos/:owner/:repo/branches/develop/protection -X PUT --input - <<'EOF'
     {
       "required_status_checks": null,
       "enforce_admins": false,
       "required_pull_request_reviews": {
         "dismiss_stale_reviews": true,
         "require_code_owner_reviews": false,
         "required_approving_review_count": 1
       },
       "restrictions": null,
       "allow_force_pushes": false,
       "allow_deletions": false,
       "required_linear_history": false
     }
     EOF
     ```

     **Note**: Even in solo development, review settings are added, but Admins can bypass with `enforce_admins: false`. This allows:
     - Present: Self-review recommended but can be skipped when necessary
     - Future: When transitioning to team development, reviews automatically become mandatory

     **For Team Development**:
     ```bash
     # main branch
     gh api repos/:owner/:repo/branches/main/protection -X PUT --input - <<'EOF'
     {
       "required_status_checks": null,
       "enforce_admins": true,
       "required_pull_request_reviews": {
         "dismiss_stale_reviews": true,
         "require_code_owner_reviews": false,
         "required_approving_review_count": 1
       },
       "restrictions": null,
       "allow_force_pushes": false,
       "allow_deletions": false,
       "required_linear_history": false
       }
     EOF

     # develop branch
     gh api repos/:owner/:repo/branches/develop/protection -X PUT --input - <<'EOF'
     {
       "required_status_checks": null,
       "enforce_admins": true,
       "required_pull_request_reviews": {
         "required_approving_review_count": 1
       },
       "restrictions": null,
       "allow_force_pushes": false,
       "allow_deletions": false,
       "required_linear_history": false
     }
     EOF
     ```

     **Configuration Details**:
     - `required_linear_history: false` - **Allow merge commits** (essential for maintaining Git Flow)
     - `enforce_admins` - Solo: false (can bypass), Team: true
     - `required_approving_review_count` - Both: 1 (solo can bypass, team required)
     - `allow_force_pushes: false` - Prohibit force push
     - `dismiss_stale_reviews: true` - Stale reviews are invalidated by new commits

     **Gradual Transition Approach**:
     1. **Solo Development Phase**: Review settings exist but Admin can bypass for flexible work
     2. **Team Join**: New members automatically require reviews (non-Admins)
     3. **Full Transition**: Change to `enforce_admins: true` for mandatory reviews for all

   - **Repository-Level Merge Settings** (Required)

     **⚠️ Important**: Disable squash merge at repository level as well as branch protection

     ```bash
     # Disable squash merge and rebase merge
     gh api repos/:owner/:repo -X PATCH -f allow_squash_merge=false -f allow_rebase_merge=false
     ```

     **Reason**:
     - Branch protection sets "whether to make history linear"
     - Repository settings control "which merge methods are allowed"
     - Without both settings, squash can still be selected during PR merge
     - **Git Flow must only allow merge commits**

3. **Git Worktree Introduction Confirmation**
   - Do you want to introduce Git Worktree?
   - **Configuration when introducing**:
     - **Main (develop)**: Use project directory as-is
     - **main worktree**: `[ProjectName]_main/` (for releases, read-only)

   **Setup Procedure**:
   ```bash
   # Run in project directory
   cd /path/to/project

   # Create main worktree (ProjectName_main directory)
   git worktree add ../[ProjectName]_main main
   ```

   **Directory Structure Example** (for my-project):
   ```
   ~/Projects/proj_my-project/
   ├── my-project/         # develop worktree (for development work, this is main)
   └── my-project_main/    # main worktree (for releases, read-only)
   ```

   - **If not introducing**:
     - Operate with normal branch switching
   - **Note**: Even if not introduced initially, can be introduced later when needed

4. **Workflow Rules Formalization**
   - Always create an ISSUE when working
   - Basically branch from `develop`
   - If already on a working branch, confirm where to branch from

5. **Commit/PR/ISSUE Naming Conventions**
   - Title: English
   - Body: Japanese or English (which do you prefer?)

### ✅ Phase 5 Configuration Completion Confirmation

**YPM will execute the following to verify settings and present to user:**

1. **Verify Default Branch**
   ```bash
   gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
   ```
   Show result to user and confirm "Is the default branch set to `develop`?"

2. **Verify Branch Protection Settings**
   ```bash
   gh api repos/:owner/:repo/branches/main/protection
   gh api repos/:owner/:repo/branches/develop/protection
   ```
   Show results to user and confirm "Are the branch protection settings correct?"

3. **Verify Git Worktree** (if introduced)
   ```bash
   git worktree list
   ```
   Show results to user and confirm "Is the Worktree configuration correct?"

**Proceed to next step only after receiving user approval**

### ✅ Phase 5 Completion Confirmation

**YPM will verify:**
- Has default branch been set to `develop`? (verified)
- Has main/develop branch protection been configured? (verified)
- Has Git Worktree setup been completed? (if introduced, verified)
- Have workflow rules been established?

**After confirming all items are complete, report to user:**

"✅ Phase 5 (Git Workflow Configuration) is complete.

Configured settings:
- Default branch: develop
- Branch protection: main/develop
- Git Worktree: [If introduced, describe configuration]
- Commit/PR/ISSUE naming conventions: [Title in English/Body in Japanese, etc.]

May I proceed to Phase 6 (Environment Configuration Files)?"

**After receiving user approval:**
1. Re-read Phase 6 of the bootstrap prompt (internal operation)
2. Review Phase 6 content (internal operation)
3. Start Phase 6

## Phase 6: Environment Configuration Files

**Progress Display**:
```
✅ Phase 1: Project Planning
✅ Phase 2: Project Directory Creation
✅ Phase 3: Documentation Setup
✅ Phase 4: GitHub Integration
✅ Phase 5: Git Workflow Configuration
🔄 Phase 6: Environment Configuration Files ← Currently here
⏳ Phase 7: Documentation Management Rules
⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
```

1. **.gitignore Configuration**
   - Add `.serena` (required for development projects)
   - Add language/framework-specific settings

2. **.claude/settings.json Configuration**

   **Official Documentation Reference** (for format verification):
   - [Claude Code Settings - Anthropic Docs](https://docs.anthropic.com/en/docs/claude-code/settings)

   **Basic Template**:

   > **Design Philosophy**: Minimize `allow`. Each user can add permissions in `.claude/settings.local.json`.
   > Shared `settings.json` is centered on `ask` and `deny`.

   ```json
   {
     "permissions": {
       "allow": [
         "Read(*)",
         "Glob(*)",
         "Grep(*)"
       ],
       "ask": [
         "Write(*)",
         "Edit(*)",
         "Bash(git :*)",
         "Bash(gh :*)",
         "Bash(npm :*)",
         "Bash(pnpm :*)",
         "Bash(yarn :*)",
         "Bash(python :*)",
         "Bash(pip :*)",
         "Bash(cargo :*)",
         "Bash(go :*)",
         "Bash(docker :*)",
         "Bash(curl :*)",
         "Bash(wget :*)"
       ],
       "deny": [
         "Read(./.env)",
         "Read(./.env.*)",
         "Read(./secrets/**)",
         "Read(./**/credentials.json)",
         "Read(./**/*.pem)",
         "Read(./**/*.key)",
         "Bash(rm -rf :*)",
         "Bash(rm -r :*)",
         "Bash(git push --force :*)",
         "Bash(git push -f :*)",
         "Bash(git reset --hard :*)",
         "Bash(git clean -f :*)",
         "Bash(gh repo delete :*)",
         "Bash(gh secret :*)",
         "Bash(sudo :*)",
         "Bash(chmod 777 :*)"
       ]
     },
     "cleanupPeriodDays": 30
   }
   ```

   **Default Strategy**:
   - `allow`: **Minimal** (read-only) - Users can add via `settings.local.json`
   - `ask`: Write operations, Git, build tools, network operations, etc. (ask for confirmation)
   - `deny`: Sensitive files, destructive operations

3. **Destructive Change Prohibition Rules**
   - Prohibit changes to system files (/etc, /usr, etc.)
   - Prohibit file changes outside project directory
   - Document these in settings.json and README.md

### ⚠️ Important Warning

**Alert to User:**

"`.claude/settings.json` is created based on official documentation and best practices, but requirements may differ for each project.

When starting a Claude Code session in each project, please always verify that the settings.json configuration is appropriate. Pay special attention to:
- Permissions for project-specific tools and commands
- Handling special directory structures
- Security requirements

Please adjust manually as needed."

### ✅ Phase 6 Completion Confirmation

**YPM will verify:**
- Has `.serena` been added to .gitignore?
- Has .claude/settings.json been created?
- Are official best practices reflected in settings.json?
- Are destructive change prohibition rules documented in settings.json and README.md?

**After confirming all items are complete, report to user:**

"✅ Phase 6 (Environment Configuration Files) is complete.

Created deliverables:
- .gitignore (.serena added)
- .claude/settings.json (permission settings configured)

⚠️ Note: settings.json needs to be verified and adjusted for each project

May I proceed to Phase 7 (Documentation Management Rules)?"

**After receiving user approval:**
1. Re-read Phase 7 of the bootstrap prompt (internal operation)
2. Review Phase 7 content (internal operation)
3. Start Phase 7

## Phase 7: Documentation Management Rules

**Progress Display**:
```
✅ Phase 1: Project Planning
✅ Phase 2: Project Directory Creation
✅ Phase 3: Documentation Setup
✅ Phase 4: GitHub Integration
✅ Phase 5: Git Workflow Configuration
✅ Phase 6: Environment Configuration Files
🔄 Phase 7: Documentation Management Rules ← Currently here
⏳ Phase 8: CLAUDE.md Creation and Final Confirmation
```

1. **Documentation Update Principles**
   - **Maintain Synchronization Between Implementation and Documentation**
     - Update related documentation when adding/changing features
     - Verify documentation updates during PR reviews

   - **When Updates Are Needed**
     - When new feature implementation is complete
     - When architecture changes
     - When API specifications change
     - When environment settings change
     - When major dependency package updates occur

   - **Target Documents**
     - README.md (setup procedures, usage)
     - docs/specifications.md (system specifications)
     - docs/architecture.md (design diagrams)
     - docs/development-guide.md (development guidelines)
     - API specifications (if they exist)

2. **Onboarding Support**
   - Include the following in README.md:
     - Quick start guide
     - Development environment setup procedures
     - FAQ (frequently asked questions and solutions)
     - Contribution guidelines

   - Create `docs/onboarding.md`:
     - Explanation of project structure
     - Coding conventions
     - How to write and run tests
     - Deployment process

3. **Documentation Update Checklist**
   - Add "Documentation update status" to PR template
   - Check for broken documentation links in CI/CD (if possible)

### ✅ Phase 7 Completion Confirmation

**YPM will verify:**
- Are documentation management principles established?
- Does README.md include onboarding information?
- Has docs/onboarding.md been created?
- Has PR template been created?

**After confirming all items are complete, report to user:**

"✅ Phase 7 (Documentation Management Rules) is complete.

Created deliverables:
- README.md (onboarding information added)
- docs/onboarding.md
- PR template (.github/pull_request_template.md)

May I proceed to Phase 8 (CLAUDE.md Creation and Final Confirmation)?"

**After receiving user approval:**
1. Re-read Phase 8 of the bootstrap prompt (internal operation)
2. Review Phase 8 content (internal operation)
3. Start Phase 8

## Phase 8: CLAUDE.md Creation and Final Confirmation

**Progress Display**:
```
✅ Phase 1: Project Planning
✅ Phase 2: Project Directory Creation
✅ Phase 3: Documentation Setup
✅ Phase 4: GitHub Integration
✅ Phase 5: Git Workflow Configuration
✅ Phase 6: Environment Configuration Files
✅ Phase 7: Documentation Management Rules
🔄 Phase 8: CLAUDE.md Creation and Final Confirmation ← Currently here
```

1. **Create CLAUDE.md**
   - Create project-specific CLAUDE.md
   - Include the following content:
     - Project overview
     - Tech stack
     - Development principles (DDD, TDD, DRY)
     - Session startup procedures
     - **Git Workflow (detailed procedure manual)**
     - **Commit/PR/ISSUE conventions (emphasize language rules)**
     - Directory structure
     - Implementation approach
     - Troubleshooting
     - Reference resources

   **Important Sections That Must Be Included in CLAUDE.md**:

   ### A. Git Workflow Enforcement Rules

   ```markdown
   ## Development Flow

   ### ⚠️ Important: Git Workflow Enforcement Rules

   **This section cannot be omitted under any circumstances. If violated, stop immediately and report to user.**

   #### New Feature Development Flow

   **STEP 1**: Create ISSUE on GitHub (required)
   **STEP 2**: Verify current branch (confirm it's `develop` with `git branch --show-current`)
   **STEP 3**: Create feature branch (`git checkout -b feature/<issue-number>-<feature-name>`)
   **STEP 4**: Implement and commit
   **STEP 5**: Create PR (`feature/<...>` → `develop`)
   **STEP 6**: Merge (use merge commit)

   #### Release Flow

   **STEP 1**: Create ISSUE on GitHub (e.g., `Release v1.0.1`)
   **STEP 2**: Make final adjustments and version updates on develop branch (if needed)
   **STEP 3**: Create PR (`develop` → `main`)  ← **Direct PR is OK**
   **STEP 4**: Merge (use merge commit)
   **STEP 5**: Tag (`git tag v1.0.1`)

   **Important**: Direct PR from develop to main is **only allowed for releases**.
   Reverse direction (main → develop) is **absolutely prohibited**.

   #### 🚨 Absolute Prohibitions

   - ❌ **main → develop backflow** (this is most critical)
   - ❌ **Direct commits to main/develop branches**
   - ❌ Squash merge (destroys Git Flow history)
   - ❌ Branch names without ISSUE numbers

   #### 🚨 Response to Violations

   If the following situations are detected, **stop work immediately** and report to user:

   1. **Attempted to create main → develop backflow PR**
      → Stop immediately, report "Backflow is absolutely prohibited"

   2. **Attempted to commit directly to main/develop branches**
      → Stop immediately, report "Please work on feature branch or bugfix/hotfix branch"

   3. **Attempted to select squash merge**
      → Stop immediately, report "Must use merge commit"
   ```

   ### B. Commit/PR Language Rules

   ```markdown
   ## Commit Message Conventions

   ### 🚨 Absolute Language Rules to Follow (CRITICAL)

   **Commit/PR/ISSUE Language**:
   - ✅ **Title (1st line)**: **Must be in English** (Conventional Commits)
   - ✅ **Body (2nd line onwards)**: **Must be in Japanese**

   ### Format

   ```
   <type>(<scope>): <subject>  ← English

   <body>  ← Japanese

   <footer>
   ```

   **✅ Correct Example**:
   ```bash
   feat(tickets): implement issue search functionality

   チケット検索機能を実装
   - search_issuesツールを追加
   - 複数のフィルターパラメータに対応

   Closes #123
   ```

   **❌ Wrong Example (Absolutely Do Not Do This)**:
   ```bash
   # NG: Body in English
   feat(tickets): implement issue search functionality

   - Add search_issues tool  ← English is NG!
   - Support multiple filter parameters  ← English is NG!

   Closes #123
   ```

   ### 🚨 Response to Violations

   4. **Commit/PR body is in English**
      → **Absolutely unacceptable violation**
      → Report to user immediately and suggest correction method
   ```

2. **Review CLAUDE.md**
   - Present created CLAUDE.md content to user
   - Confirm "Is this CLAUDE.md content acceptable?"
   - ⚠️ **Communicate important notice to user:**

     "Changes to CLAUDE.md should be made while confirming with Claude Code in each project, or edited manually. Adjustments are necessary according to project-specific requirements."

3. **Confirm Additional Rules**
   - Ask user "Are there any other rules or settings you'd like to introduce?"

4. **Final Commit and Push**
   - Commit all changes
   - Push to GitHub

5. **Setup Completion Confirmation**
   - Verify project is ready for development
   - Guide next steps:

     ```
     🎉 [Project Name] preparation is complete!

     ⚠️ Important: YPM work ends here

     YPM only performs "preparation". It does not create implementation or test code.

     Next steps:
     1. Navigate to project directory: cd [path]
     2. Start new Claude Code session
     3. Start development following CLAUDE.md instructions:
        - DDD principle: Start with documentation
        - TDD principle: Write tests first
        - Create first ISSUE
        - Branch from develop branch

     Please perform implementation in each project.
     ```

### ✅ Phase 8 Completion Confirmation

**YPM will verify:**
- Has CLAUDE.md been created and reviewed by user?
- Have all changes been committed?
- Has it been pushed to GitHub?
- Is the project ready for development?

**After confirming all items are complete, make final report to user:**

"🎉 All 8 phases of bootstrap are complete!

[Project Name] is ready for development.

Main deliverables created:
- Project directory and Git repository
- Basic documents under docs/
- GitHub repository (Private)
- Git Workflow configuration (develop/main, branch protection)
- Environment configuration files (.gitignore, .claude/settings.json)
- Documentation management rules (PR template, etc.)
- CLAUDE.md

⚠️ Important: YPM work ends here.
Please perform implementation in each project.

Next steps:
1. Navigate to project directory: cd [path]
2. Start new Claude Code session
3. Start development following CLAUDE.md instructions"

---

## Continuous Practice During Development

### TDD Practice Rules
1. **Red**: Write failing test
2. **Green**: Write minimal code to pass test
3. **Refactor**: Refactor based on DRY principle

### Documentation Update Triggers
- Just before merging PR after feature implementation is complete
- When milestones are achieved (v0.1.0, v0.2.0, etc.)
- Monthly or bi-weekly regular reviews

---

## Usage

Paste this prompt into Claude Code to start the dialogue. We will guide you through project setup step by step, asking for necessary information at each phase.

---

**Main Additions:**

1. Added explicit mention of TDD/DRY principles in **Phase 3**
2. Created new **Phase 7** as "Documentation Management Rules"
   - Clarified update timing
   - Onboarding support mechanisms
   - Introduced checklists
3. Added development startup guidelines to **Phase 8**
4. Documented implementation rules in **Continuous Practice During Development** section

This ensures documentation stays current not only at project start but throughout development, creating an environment where new members can smoothly join at any time.
