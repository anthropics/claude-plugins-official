---
name: hive-bootstrap
description: Use when starting a new project that needs multi-agent swarm infrastructure - detects missing setup and bootstraps everything automatically
skipPlanMode: true
---

# Hive Bootstrap

Auto-setup multi-agent swarm infrastructure for any project.

## IMPORTANT: Use Interactive UI

**You MUST use the `AskUserQuestion` tool for ALL questions.**

This provides the nice selectable chip/button interface instead of plain text prompts.

---

## Question Flow Overview (Scrutiny #93 Redesign)

```
PHASE 1: Understand the Work (shared)
  Q1: Work Type
  Q2: Scope (branches by work type)
  Q3: Scout (if existing project)

PHASE 2: Size the Team (auto-suggested from scope)
  Q4: Crew Recommendation
  Q5: Agent Mapping

PHASE 3: Execution Config (shared)
  Q6: Workflow (Quick Launch / Plan First)
  Q7: Task Mode (Auto / Manual)
  Q8: Model (Haiku / Sonnet / Opus)
  Q9: Desktop (macOS Spaces)

PHASE 4: Launch (mode-specific)
  Quick Launch → Setup → Launch → Orchestrator
  Plan First → Setup → Create Tasks → Launch
```

---

## PHASE 1: Understand the Work

### Question 1: Work Type

```
question: "What kind of work is this swarm doing?"
header: "Work Type"
options:
  - label: "Build New Software"
    description: "Create new apps, platforms, services, libraries, or APIs from scratch."

  - label: "Refactor / Migrate"
    description: "Upgrade frameworks, migrate languages, restructure architecture, or clean tech debt."

  - label: "Documentation"
    description: "Write or update technical docs, API references, user guides, or architecture docs."

  - label: "DevOps / Infrastructure"
    description: "Set up CI/CD, infrastructure as code, Kubernetes, monitoring, or cloud resources."

  - label: "Analysis / Audit"
    description: "Security review, performance audit, codebase exploration, or architecture analysis."

  - label: "Testing / QA"
    description: "Create test suites, E2E automation, test data generation, or coverage improvement."
```

Store: `work_type` for branching

---

### Question 2: Scope (branches based on Q1)

#### IF "Build New Software":

```
question: "What's the project scope?"
header: "Scope"
options:
  - label: "Full Platform"
    description: "Multiple apps + backend + dashboards (e.g., delivery platform with customer app, driver app, admin dashboard, API)."

  - label: "Single App"
    description: "One application targeting one platform (Android, iOS, or Web)."

  - label: "Backend / API"
    description: "Server-side services, APIs, or microservices only."

  - label: "Library / SDK"
    description: "Reusable package or SDK for other developers."

  - label: "CLI Tool"
    description: "Command-line application."
```

**IF "Full Platform" selected → Ask Q2b and Q2c:**

```
question: "Which platforms are you targeting?"
header: "Platforms"
multiSelect: true
options:
  - label: "Android"
    description: "Native Android app(s)"
  - label: "iOS"
    description: "Native iOS app(s)"
  - label: "Web Frontend"
    description: "Web application (SPA/SSR)"
  - label: "Backend Services"
    description: "APIs, BFF, microservices"
  - label: "Admin Dashboard"
    description: "Internal admin/management UI"
```

```
question: "What tech stacks for each platform?"
header: "Tech Stack"
(Present based on selected platforms)

Android:   ○ Kotlin + Compose (Recommended)  ○ Kotlin + XML  ○ Java
iOS:       ○ Swift + SwiftUI (Recommended)   ○ Swift + UIKit
Web:       ○ Vue + TypeScript  ○ React + TypeScript  ○ Svelte  ○ Next.js
Backend:   ○ Spring / Kotlin (Recommended)  ○ Node / TypeScript  ○ Go  ○ Python
Dashboard: ○ Vue + Shadcn (Recommended)  ○ React + Tailwind  ○ Same as Web
```

**IF "Single App" selected → Ask platform and stack:**

```
question: "Which platform?"
header: "Platform"
options:
  - label: "Android"
  - label: "iOS"
  - label: "Web"
```

Then ask tech stack for that platform.

#### IF "Refactor / Migrate":

```
question: "What type of migration?"
header: "Migration"
options:
  - label: "Framework Upgrade"
    description: "Update to newer version of same framework (e.g., React 17 → 18)."

  - label: "Language Migration"
    description: "Change primary language (e.g., Java → Kotlin, JavaScript → TypeScript)."

  - label: "Architecture Change"
    description: "Restructure (e.g., monolith → microservices, MVC → Clean Architecture)."

  - label: "Dependency Updates"
    description: "Update outdated dependencies, fix vulnerabilities."

  - label: "Tech Debt Cleanup"
    description: "Refactor messy code, improve patterns, add tests."
```

Then ask: "Describe current → target state" (open text or follow-up).

#### IF "DevOps / Infrastructure":

```
question: "What infrastructure work?"
header: "Infra Type"
options:
  - label: "CI/CD Pipelines"
    description: "Build, test, deploy automation."

  - label: "Infrastructure as Code"
    description: "Terraform, Pulumi, CloudFormation."

  - label: "Kubernetes / Containers"
    description: "K8s configs, Helm charts, Docker."

  - label: "Monitoring / Observability"
    description: "Logging, metrics, alerting, tracing."

  - label: "Cloud Setup"
    description: "AWS, GCP, or Azure resource provisioning."
```

#### IF "Documentation":

```
question: "What needs documenting?"
header: "Doc Type"
options:
  - label: "API Documentation"
    description: "OpenAPI specs, endpoint references."

  - label: "Architecture Docs"
    description: "System design, diagrams, ADRs."

  - label: "User Guides"
    description: "End-user documentation, tutorials."

  - label: "Developer Onboarding"
    description: "README, setup guides, contribution docs."
```

#### IF "Analysis / Audit":

```
question: "What to analyze?"
header: "Analysis"
options:
  - label: "Security Audit"
    description: "Vulnerability scan, security review."

  - label: "Performance Audit"
    description: "Bottleneck identification, optimization opportunities."

  - label: "Codebase Exploration"
    description: "Understand unfamiliar codebase structure."

  - label: "Architecture Review"
    description: "Evaluate current architecture, suggest improvements."
```

#### IF "Testing / QA":

```
question: "What testing work?"
header: "Testing"
options:
  - label: "Unit Test Suite"
    description: "Create comprehensive unit tests."

  - label: "Integration Tests"
    description: "API and service integration testing."

  - label: "E2E Automation"
    description: "End-to-end UI test automation."

  - label: "Test Coverage"
    description: "Improve existing test coverage."
```

---

### Question 3: Scout (CONDITIONAL)

**Only ask if existing project detected:**

```bash
.handshake/bin/hive-client has-source-files
# Returns "true" or "false"
```

**If "true":**

```
question: "This looks like an existing project. Want a scout to analyze the architecture first?"
header: "Scout"
options:
  - label: "Yes - launch scout (Recommended)"
    description: "A temporary agent analyzes the codebase and documents patterns. Takes 2-5 minutes."

  - label: "No - skip"
    description: "Skip scouting. Agents will discover patterns as they work."
```

**If "Yes":** Run `.handshake/hive scout --model haiku`, wait for completion, continue.

---

## PHASE 2: Size the Team

### Question 4: Crew Recommendation (Auto-Calculated)

Based on scope from Phase 1, calculate and present:

**Auto-suggestion logic:**

| Scope | Recommended |
|-------|-------------|
| Single app, simple | 1 crew, 2 agents |
| Single app, complex | 1 crew, 4 agents |
| Platform, 2-3 targets | 2 crews (8 agents) |
| Platform, 4+ targets | 3 crews (12 agents) |
| Backend only | 1 crew, 2-4 agents |
| Refactor (small) | 1 crew, 2 agents |
| Refactor (large) | 2 crews |
| Docs / DevOps / Analysis | 1 crew, 2 agents |

```
question: "Based on your scope, we recommend {N} crew(s) with {M} agents. Adjust?"
header: "Team Size"
options:
  - label: "Accept recommendation ({N} crews, {M} agents)"
    description: "Optimal for your scope."

  - label: "Smaller team"
    description: "Fewer agents - more cost-conscious, sequential work."

  - label: "Larger team"
    description: "More agents - aggressive parallelism, higher cost."
```

### Question 5: Agent Mapping (for Platform scope)

**Only for "Full Platform" with multiple targets:**

Present suggested mapping based on platforms selected:

```
┌─────────────────────────────────────────────────────────────────────┐
│  SUGGESTED AGENT MAPPING                                            │
├─────────────────────────────────────────────────────────────────────┤
│  HAACK Crew (Mobile)                                                │
│    kai  → Android Customer App                                      │
│    neo  → Android Courier App                                       │
│    ava  → iOS Customer App                                          │
│    lexi → iOS Courier App                                           │
│                                                                     │
│  FLUX Crew (Backend + Web)                                          │
│    jax  → BFF Services (Spring/Kotlin)                              │
│    ryn  → Core Services                                             │
│    zoe  → Admin Dashboard (Vue + Shadcn)                            │
│    max  → Merchant Dashboard                                        │
└─────────────────────────────────────────────────────────────────────┘
```

```
question: "Does this agent mapping look right?"
header: "Mapping"
options:
  - label: "Yes - use this"
    description: "Proceed with suggested mapping."

  - label: "Adjust"
    description: "Let me modify the assignments."
```

Store mapping in `.handshake/config/workstreams.json`.

---

## PHASE 3: Execution Config

### Question 6: Workflow

```
question: "How do you want to work with the swarm?"
header: "Workflow"
options:
  - label: "Quick Launch (Recommended)"
    description: "Launch agents now. Assign tasks on-the-fly as orchestrator."

  - label: "Plan First"
    description: "Create all task files before launching. Agents start with work ready."
```

### Question 7: Task Mode

```
question: "How should agents handle tasks?"
header: "Task Mode"
options:
  - label: "Auto (Recommended)"
    description: "Agents execute tasks immediately without asking."

  - label: "Manual"
    description: "Agents wait for your approval before executing."
```

Store: `--mode auto` or `--mode manual`

### Question 8: Model

```
question: "Which AI model for agents?"
header: "Model"
options:
  - label: "Sonnet (Recommended)"
    description: "Balanced capability and cost. Good for most work."

  - label: "Opus"
    description: "Most capable. Best for complex architecture work. Higher cost."

  - label: "Haiku"
    description: "Fastest and cheapest. Best for simple tasks or large swarms."
```

Store: `--model sonnet`, `--model opus`, or `--model haiku`

### Question 9: Desktop (macOS only)

```
question: "Launch crews in separate macOS Spaces?"
header: "Desktop"
options:
  - label: "Yes (Recommended)"
    description: "Each crew gets fullscreen Space. Swipe to switch."

  - label: "No"
    description: "Standard windows."
```

Store: `--desktop` flag if Yes

---

## PHASE 4: Launch

### Infrastructure Setup (Both Modes)

```bash
mkdir -p .handshake/{bin,config,status,tasks,reports,registry,analysis}
mkdir -p .claude/hooks
PLUGIN_DIR=$(ls -td ~/.claude/plugins/cache/leepick-marketplace/handshake/*/ 2>/dev/null | head -1)
cp "$PLUGIN_DIR/.handshake/"* .handshake/ 2>/dev/null || true
cp -r "$PLUGIN_DIR/.handshake/bin/"* .handshake/bin/
cp "$PLUGIN_DIR/hooks/"* .claude/hooks/ 2>/dev/null || true
chmod +x .handshake/hive .handshake/bin/* .claude/hooks/*.sh 2>/dev/null || true
.handshake/bin/generate-profiles
```

### Pre-Launch Cleanup (Both Modes)

```bash
.handshake/bin/hive-client reset
```

### Check Prerequisites (All Platforms)

**Run this FIRST before anything else.**

```bash
# Detect platform
OS=$(uname -s)
echo "Platform: $OS"

# Check Python 3.9+
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found."
    if [[ "$OS" == "Darwin" ]]; then
        echo "Install: brew install python@3.11"
    else
        echo "Install: sudo apt install python3 python3-pip"
    fi
    exit 1
fi
echo "✓ Python 3 found"

# Check tmux (required for Linux/WSL, optional for macOS)
if [[ "$OS" != "Darwin" ]]; then
    if ! command -v tmux &>/dev/null; then
        echo "ERROR: tmux not found (required for Linux/WSL)."
        echo "Install: sudo apt install tmux"
        exit 1
    fi
    echo "✓ tmux found"
elif [[ "$OS" == "Darwin" ]]; then
    # macOS: check iTerm2 or tmux
    if [[ ! -d "/Applications/iTerm.app" ]] && ! command -v tmux &>/dev/null; then
        echo "ERROR: Neither iTerm2 nor tmux found."
        echo "Install iTerm2: brew install --cask iterm2"
        echo "Or install tmux: brew install tmux"
        exit 1
    fi
    if [[ -d "/Applications/iTerm.app" ]]; then
        echo "✓ iTerm2 found"
    else
        echo "✓ tmux found (will use tmux adapter)"
    fi
fi
```

### Verify Daemon (Both Modes) - Auto-Install if Missing

**Run this after prerequisites check.**

```bash
# Check if daemon is running
if ! curl -s http://localhost:5757/health > /dev/null 2>&1; then
    echo "Daemon not running. Checking installation..."

    # Check if installed via Homebrew
    if brew list handshake &>/dev/null; then
        echo "Starting Homebrew-installed daemon..."
        brew services start handshake
        sleep 3

    # Not installed - offer to install via Homebrew (macOS)
    elif command -v brew &>/dev/null; then
        echo "Handshake not installed. Installing via Homebrew..."
        brew tap leepickdev/tap
        brew install handshake
        brew services start handshake
        sleep 3

    # Linux/WSL - no Homebrew, use plugin daemon directly
    else
        echo "Starting daemon from plugin cache..."
        PLUGIN_DIR=$(ls -td ~/.claude/plugins/cache/leepick-marketplace/handshake/*/ 2>/dev/null | head -1)
        if [[ -n "$PLUGIN_DIR" ]]; then
            cd "$PLUGIN_DIR/daemon"
            pip3 install -q -r requirements.txt 2>/dev/null
            python3 src/handshaked.py &
            sleep 3
        else
            echo "ERROR: Plugin not installed. Run: claude plugin install handshake@leepick-marketplace"
            exit 1
        fi
    fi

    # Verify daemon started
    if ! curl -s http://localhost:5757/health > /dev/null 2>&1; then
        echo "ERROR: Failed to start daemon. Check logs."
        exit 1
    fi
    echo "✓ Daemon running"
fi
```

**Flow:**
```
Check daemon health
    ↓ not running
Check brew list handshake
    ↓ not installed
Check brew available (macOS)
    ↓ yes
brew tap + install + services start
    ↓ no (Linux)
pip install + python3 daemon
```

### Mode A: Quick Launch

1. Setup infrastructure
2. Pre-launch cleanup
3. Save workstream mapping to config
4. Launch crews:
   ```bash
   .handshake/hive launch haack --mode <MODE> --model <MODEL> --agents <N> [--desktop]
   ```
5. **IMMEDIATELY invoke `handshake:hive-orchestrator`**
   - Orchestrator uses stored scope/mapping to assign tasks

### Mode B: Plan First

1. Setup infrastructure
2. Pre-launch cleanup
3. **Create task files from agent mapping:**

For each agent in mapping, create `.handshake/tasks/<agent>.md`:

```markdown
# Task: <agent> (<CREW>)

## Assignment
<From mapping: e.g., "Android Customer App">

## Tech Stack
<From scope: e.g., "Kotlin + Compose">

## Objectives
1. Set up project structure for <assignment>
2. Implement core features
3. Follow conventions in .handshake/conventions.md (if exists)
4. Commit progress regularly

## Workstream
<Platform from mapping>

## Status
pending
```

4. Launch crews:
   ```bash
   .handshake/hive launch haack --mode <MODE> --model <MODEL> --agents <N> [--desktop]
   ```
5. Agents see tasks immediately and start working

---

## Stored Configuration

After wizard completes, save to `.handshake/config/project.json`:

```json
{
  "work_type": "build_new",
  "scope": "platform",
  "platforms": ["android", "ios", "backend", "dashboard"],
  "stacks": {
    "android": "kotlin-compose",
    "ios": "swift-swiftui",
    "backend": "spring-kotlin",
    "dashboard": "vue-shadcn-ts"
  },
  "crews": 2,
  "agents_per_crew": 4,
  "agent_mapping": {
    "kai": {"platform": "android", "assignment": "Customer App"},
    "neo": {"platform": "android", "assignment": "Courier App"},
    "ava": {"platform": "ios", "assignment": "Customer App"},
    "lexi": {"platform": "ios", "assignment": "Courier App"},
    "jax": {"platform": "backend", "assignment": "BFF Services"},
    "ryn": {"platform": "backend", "assignment": "Core Services"},
    "zoe": {"platform": "dashboard", "assignment": "Admin Dashboard"},
    "max": {"platform": "dashboard", "assignment": "Merchant Dashboard"}
  },
  "workflow": "plan_first",
  "mode": "auto",
  "model": "sonnet"
}
```

---

## Default Crews

| Crew | Agents | Theme |
|------|--------|-------|
| HAACK | kai, neo, ava, lexi | Dracula (purple) |
| FLUX | jax, ryn, zoe, max | Nord (blue) |
| PULSE | ada, vex, rio, nix | Gruvbox (orange) |

---

## Quick Reference: Launch Flags

| Flag | Values | Default |
|------|--------|---------|
| `--mode` | auto, manual | auto |
| `--model` | opus, sonnet, haiku | sonnet |
| `--agents` | 1, 2, 3, 4 | 4 |
| `--desktop` | (flag) | off |

---

## Anti-Patterns

```
❌ Ask crew size before knowing scope
❌ Single-app options only for platform work
❌ Skip scout for existing codebases
❌ Agents sitting idle with no mapping
```

## Correct Pattern

```
✓ Work type first, then scope, then team size
✓ Auto-suggest crews from scope
✓ Scout existing projects for conventions
✓ Store mapping for task generation
✓ Both Quick Launch and Plan First use same Phase 1-3
```
