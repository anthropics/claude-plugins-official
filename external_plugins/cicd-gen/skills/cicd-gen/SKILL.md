# Skill: CI/CD Pipeline 智能生成

自动检测项目类型和技术栈，生成 GitHub Actions workflow 及其他 CI/CD 配置。

## 触发条件

当用户请求以下操作时激活：
- "生成 ci"、"配置流水线"、"pipeline"
- "generate ci/cd"、"github actions"
- "给项目加 ci"、"setup workflow"
- 需要自动化构建、测试、部署流程

---

## 执行步骤

### 第一步：检测项目类型和技术栈

```bash
# Check for language/framework markers
ls package.json bun.lockb yarn.lock pnpm-lock.yaml pyproject.toml requirements.txt go.mod go.sum Cargo.toml Cargo.lock pom.xml build.gradle Dockerfile docker-compose.yml 2>/dev/null

# JS/TS runtime detection
if [ -f bun.lockb ]; then echo "RUNTIME=bun"
elif [ -f pnpm-lock.yaml ]; then echo "RUNTIME=pnpm"
elif [ -f yarn.lock ]; then echo "RUNTIME=yarn"
elif [ -f package.json ]; then echo "RUNTIME=npm"
fi

# Framework detection (JS/TS)
cat package.json 2>/dev/null | grep -E "(next|nuxt|remix|astro|vite|react|vue|angular|svelte|express|fastify|hono|elysia|nest)"

# Python framework detection
grep -rE "(fastapi|flask|django|streamlit)" requirements.txt pyproject.toml setup.py 2>/dev/null

# Go framework detection
grep -rE "(gin|echo|fiber|chi)" go.mod 2>/dev/null

# Rust detection
cat Cargo.toml 2>/dev/null | grep -E "(actix|axum|rocket|warp)"

# Docker detection
ls Dockerfile docker-compose.yml .dockerignore 2>/dev/null

# Monorepo detection
ls lerna.json turbo.json nx.json pnpm-workspace.yaml 2>/dev/null
ls packages/ apps/ services/ 2>/dev/null
```

根据检测结果确定：
- 语言 + 框架 + 运行时
- 包管理器（bun/pnpm/yarn/npm/pip/cargo/go）
- 是否为 monorepo
- 是否使用 Docker
- 现有 CI 配置（可能已有部分配置）

### 第二步：检查现有 CI 配置

```bash
# Check for existing CI/CD configurations
ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null
ls .gitlab-ci.yml .circleci/config.yml Jenkinsfile 2>/dev/null
ls .github/dependabot.yml renovate.json .renovaterc 2>/dev/null
```

若已有配置，读取并作为基础进行增量更新，而非从零生成。

### 第三步：确定流水线模式

根据项目类型选择合适的流水线模式：

| 项目类型 | 流水线阶段 |
|---------|-----------|
| 前端应用 (Next.js/Vite/React) | lint -> type-check -> test -> build -> deploy |
| 后端 API (Express/FastAPI/Gin) | lint -> test -> build -> docker-push -> deploy |
| 全栈 (Next.js full-stack) | lint -> type-check -> test -> build -> deploy |
| 库/SDK (npm package) | lint -> test -> build -> publish |
| CLI 工具 | lint -> test -> build -> release |
| Monorepo | 路径过滤 -> 各子项目独立流水线 |
| Docker 项目 | lint -> test -> docker-build -> docker-push -> deploy |
| 静态站点 | lint -> build -> deploy |

### 第四步：生成 GitHub Actions Workflow

在 `.github/workflows/` 目录下生成 workflow 文件。

---

## Workflow 模板

### Node.js / Bun 项目

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest

      - name: Install dependencies
        run: bun install --frozen-lockfile

      - name: Lint
        run: bun run lint

      - name: Type check
        run: bun run type-check

      - name: Test
        run: bun test

      - name: Build
        run: bun run build
```

**npm 变体（替换 bun 部分）：**
```yaml
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci
```

**pnpm 变体：**
```yaml
      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile
```

### Python 项目

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint
        run: |
          ruff check .
          ruff format --check .

      - name: Type check
        run: mypy .

      - name: Test
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

**uv 变体（替换 pip 部分）：**
```yaml
      - uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --frozen

      - name: Lint
        run: |
          uv run ruff check .
          uv run ruff format --check .
```

### Go 项目

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
          cache: true

      - name: Lint
        uses: golangci/golangci-lint-action@v6
        with:
          version: latest

      - name: Test
        run: go test -race -coverprofile=coverage.out ./...

      - name: Build
        run: go build -v ./...
```

### Rust 项目

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt

      - uses: Swatinem/rust-cache@v2

      - name: Format check
        run: cargo fmt --all -- --check

      - name: Lint
        run: cargo clippy --all-targets --all-features -- -D warnings

      - name: Test
        run: cargo test --all-features

      - name: Build
        run: cargo build --release
```

### Docker 项目

```yaml
name: Docker Build & Push

on:
  push:
    branches: [main]
    tags: ['v*']

permissions:
  contents: read
  packages: write

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## 部署目标配置

### Vercel 部署

```yaml
  deploy:
    needs: ci
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      deployments: write
    steps:
      - uses: actions/checkout@v4

      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

**所需 Secrets：**
- `VERCEL_TOKEN` — Vercel API Token
- `VERCEL_ORG_ID` — Vercel Organization ID
- `VERCEL_PROJECT_ID` — Vercel Project ID

### Netlify 部署

```yaml
  deploy:
    needs: ci
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: bun run build

      - uses: nwtgck/actions-netlify@v3
        with:
          publish-dir: './dist'
          production-branch: main
          deploy-message: 'Deploy from GitHub Actions'
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

### Docker Registry 部署（AWS ECR）

```yaml
  deploy:
    needs: ci
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-arn: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - uses: aws-actions/amazon-ecr-login@v2
        id: ecr

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.ecr.outputs.registry }}/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### npm Publish

```yaml
  publish:
    needs: ci
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: 'https://registry.npmjs.org'

      - name: Install & Build
        run: |
          npm ci
          npm run build

      - name: Publish
        run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### GitHub Pages 部署

```yaml
  deploy:
    needs: ci
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: bun run build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: './dist'

      - uses: actions/deploy-pages@v4
        id: deployment
```

---

## 缓存策略配置

### 缓存策略速查表

| 技术栈 | 缓存方式 | 缓存路径 / Key |
|-------|---------|---------------|
| Bun | 内置 `bun install --frozen-lockfile` | `~/.bun/install/cache`，key: `bun.lockb` |
| npm | `actions/setup-node` + `cache: 'npm'` | 自动管理，key: `package-lock.json` |
| pnpm | `actions/setup-node` + `cache: 'pnpm'` | 自动管理，key: `pnpm-lock.yaml` |
| yarn | `actions/setup-node` + `cache: 'yarn'` | 自动管理，key: `yarn.lock` |
| pip | `actions/setup-python` + `cache: 'pip'` | 自动管理，key: `requirements*.txt` |
| Go | `actions/setup-go` + `cache: true` | 自动管理，key: `go.sum` |
| Rust | `Swatinem/rust-cache@v2` | `target/`，key: `Cargo.lock` |
| Docker | `docker/build-push-action` + `cache-from/to: type=gha` | GitHub Actions cache |
| Gradle | `actions/setup-java` + `cache: 'gradle'` | `~/.gradle/caches` |
| Maven | `actions/setup-java` + `cache: 'maven'` | `~/.m2/repository` |

### Bun 缓存配置示例

```yaml
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest

      # bun install automatically uses lockfile-based caching
      - name: Install dependencies
        run: bun install --frozen-lockfile
```

### 自定义缓存（通用）

```yaml
      - uses: actions/cache@v4
        with:
          path: |
            ~/.cache/some-tool
            .build-cache
          key: ${{ runner.os }}-tool-${{ hashFiles('**/lockfile') }}
          restore-keys: |
            ${{ runner.os }}-tool-
```

---

## Monorepo 检测和路径过滤

### Monorepo 检测逻辑

```bash
# Turborepo
ls turbo.json 2>/dev/null && echo "MONOREPO=turborepo"

# Nx
ls nx.json 2>/dev/null && echo "MONOREPO=nx"

# Lerna
ls lerna.json 2>/dev/null && echo "MONOREPO=lerna"

# pnpm workspace
ls pnpm-workspace.yaml 2>/dev/null && echo "MONOREPO=pnpm-workspace"

# General multi-package detection
ls packages/*/package.json apps/*/package.json 2>/dev/null
```

### 路径过滤 Workflow

```yaml
name: CI - Web App

on:
  push:
    branches: [main]
    paths:
      - 'apps/web/**'
      - 'packages/shared/**'
      - 'package.json'
      - 'bun.lockb'
  pull_request:
    branches: [main]
    paths:
      - 'apps/web/**'
      - 'packages/shared/**'

jobs:
  ci-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: oven-sh/setup-bun@v2

      - run: bun install --frozen-lockfile

      - name: Lint & Test (web)
        run: |
          bun run --filter=web lint
          bun run --filter=web test

      - name: Build (web)
        run: bun run --filter=web build
```

### Turborepo Workflow

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - uses: oven-sh/setup-bun@v2

      - run: bun install --frozen-lockfile

      - name: Build affected
        run: bunx turbo run build --filter='...[HEAD^]'

      - name: Test affected
        run: bunx turbo run test --filter='...[HEAD^]'
```

---

## Dependabot / Renovate 配置

### dependabot.yml

```yaml
# .github/dependabot.yml
version: 2
updates:
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      actions:
        patterns:
          - "*"

  # npm / bun
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      production:
        dependency-type: "production"
      development:
        dependency-type: "development"
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]

  # pip
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"

  # Go modules
  - package-ecosystem: "gomod"
    directory: "/"
    schedule:
      interval: "weekly"

  # Docker
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"

  # Cargo (Rust)
  - package-ecosystem: "cargo"
    directory: "/"
    schedule:
      interval: "weekly"
```

仅生成当前项目所需的 ecosystem 条目。例如 Node.js 项目只需 `github-actions` + `npm`。

### Renovate 配置（可选替代）

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "group:allNonMajor",
    ":semanticCommits"
  ],
  "schedule": ["before 6am on Monday"],
  "automerge": true,
  "automergeType": "pr",
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    },
    {
      "matchUpdateTypes": ["major"],
      "automerge": false
    }
  ]
}
```

---

## 安全最佳实践

### Secrets 管理

1. **永远不要**在 workflow 文件中硬编码 secrets
2. 使用 `${{ secrets.XXX }}` 引用 GitHub Secrets
3. 敏感操作使用 OIDC（`id-token: write`）代替长期凭证
4. 定期轮换所有 secrets

### 权限最小化

```yaml
# Global: restrict all permissions by default
permissions:
  contents: read

# Per-job: only grant what's needed
jobs:
  deploy:
    permissions:
      contents: read
      deployments: write
      # Only add id-token for OIDC
      id-token: write
```

**权限参考表：**

| 操作 | 所需权限 |
|-----|---------|
| 读取代码 | `contents: read` |
| 推送代码/tag | `contents: write` |
| 创建 PR 评论 | `pull-requests: write` |
| 发布 Docker 到 GHCR | `packages: write` |
| 部署 GitHub Pages | `pages: write` + `id-token: write` |
| OIDC 认证（AWS/GCP） | `id-token: write` |

### 第三方 Action 安全

```yaml
# GOOD: Pin to specific commit SHA
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# ACCEPTABLE: Pin to major version
- uses: actions/checkout@v4

# BAD: Use latest or branch — vulnerable to supply chain attacks
- uses: actions/checkout@main
```

### Branch Protection 建议

生成 workflow 后，建议用户配置 Branch Protection Rules：
- Require status checks to pass before merging
- Require pull request reviews
- Require signed commits (可选)
- Do not allow bypassing the above settings

---

## 可选生成：GitLab CI

如果用户使用 GitLab，生成 `.gitlab-ci.yml`：

```yaml
stages:
  - lint
  - test
  - build
  - deploy

variables:
  BUN_INSTALL: "$CI_PROJECT_DIR/.bun"

cache:
  key: $CI_COMMIT_REF_SLUG
  paths:
    - node_modules/
    - .bun/

lint:
  stage: lint
  image: oven/bun:latest
  script:
    - bun install --frozen-lockfile
    - bun run lint

test:
  stage: test
  image: oven/bun:latest
  script:
    - bun install --frozen-lockfile
    - bun test

build:
  stage: build
  image: oven/bun:latest
  script:
    - bun install --frozen-lockfile
    - bun run build
  artifacts:
    paths:
      - dist/

deploy:
  stage: deploy
  only:
    - main
  script:
    - echo "Deploy step — customize per target"
```

---

## 可选生成：CircleCI

```yaml
version: 2.1

orbs:
  node: circleci/node@5

jobs:
  ci:
    docker:
      - image: oven/bun:latest
    steps:
      - checkout
      - run: bun install --frozen-lockfile
      - run: bun run lint
      - run: bun test
      - run: bun run build

workflows:
  main:
    jobs:
      - ci
```

---

## 质量检查清单

生成完成后，自检以下项目：

- [ ] workflow 文件语法正确（可通过 `actionlint` 验证）
- [ ] 包管理器与项目实际使用的一致（bun/npm/pnpm/yarn）
- [ ] lockfile 使用了 `--frozen-lockfile` 或 `ci` 模式
- [ ] 缓存策略已配置且 key 正确
- [ ] 全局 `permissions` 设置为 `contents: read`（最小权限）
- [ ] 使用了 `concurrency` 避免重复运行
- [ ] PR 和 push 触发条件合理
- [ ] Secrets 引用正确，无硬编码
- [ ] Action 版本已 pin 到 major version 或 SHA
- [ ] monorepo 项目配置了路径过滤
- [ ] 部署 job 有正确的条件守卫（`if: github.ref == 'refs/heads/main'`）
- [ ] dependabot.yml 仅包含项目实际使用的 ecosystem

---

## 决策流程图

```
检测项目类型和技术栈
        |
确定包管理器和运行时
        |
是否已有 CI 配置？
  是 -> 增量更新模式（补充缺失部分）
  否 -> 全量生成模式
        |
是否为 Monorepo？
  是 -> 生成路径过滤 + 各子项目 workflow
  否 -> 生成单一 workflow
        |
选择流水线模式（lint -> test -> build -> deploy）
        |
是否需要部署？
  是 -> 询问部署目标（Vercel/Netlify/Docker/npm/AWS）
  否 -> 仅生成 CI workflow
        |
生成 .github/workflows/ci.yml
        |
是否需要 dependabot？
  是 -> 生成 .github/dependabot.yml
  否 -> 跳过
        |
验证 workflow 语法（actionlint）
  失败 -> 修复后重新验证
  通过 |
        |
输出结果 + 配置说明 + 所需 Secrets 清单
```

---

## 注意事项

- **不要**生成项目不需要的步骤（如 Python 项目不需要 type-check，除非有 mypy）
- **不要**使用过时的 Action 版本，始终使用最新 stable 版本
- **不要**在 workflow 中安装全局依赖，优先使用 `bunx` / `npx`
- **不要**忽略 `--frozen-lockfile`，CI 中必须使用锁定依赖
- 优先使用 bun 作为 JS/TS 运行时（遵循用户偏好）
- 大型 monorepo 建议使用 Turborepo / Nx 的增量构建特性
- 生成后提醒用户配置所需的 GitHub Secrets
- 若项目有 Dockerfile，额外生成 Docker build workflow
