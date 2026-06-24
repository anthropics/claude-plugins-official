# 项目结构分析：claude-plugins-official

> 生成日期：2026-06-24 · 分支：`claude/condescending-golick-8f093f`

## 一、这是什么

Anthropic 官方维护的 **Claude Code 插件目录（marketplace）**。本仓库本身不是代码库，而是一个**插件清单 + 少量内置插件 + 自动化运维流水线**的组合。用户通过 Claude Code 的插件系统安装：

```
/plugin install {plugin-name}@claude-plugins-official
```

核心事实：仓库的"产品"是 `.claude-plugin/marketplace.json` 这一个清单文件。绝大多数被收录的插件**源码并不在本仓库内**，而是通过 git 引用指向外部仓库。

## 二、顶层结构

```
claude-plugins-official/
├── .claude-plugin/
│   └── marketplace.json     # ★ 核心：236 个插件条目的清单
├── plugins/                 # 37 个 Anthropic 内置插件（源码在仓库内）
├── external_plugins/        # 15 个第三方插件
├── .github/                 # CI/CD 自动化（验证 + SHA 自动更新）
│   ├── workflows/           # 8 个 GitHub Actions 工作流
│   ├── scripts/             # 校验与发现脚本
│   └── policy/              # 安全审查 prompt + schema
├── README.md
├── LICENSE
└── .gitignore               # 忽略 *.DS_Store 与 .claude/
```

## 三、核心：marketplace.json

清单中共 **236 个插件条目**。

### 分类分布

| 分类 | 数量 | | 分类 | 数量 |
|------|-----:|-|------|-----:|
| development | 101 | | deployment | 6 |
| productivity | 44 | | design | 5 |
| database | 32 | | learning | 3 |
| security | 13 | | location | 2 |
| monitoring | 13 | | migration / testing / math | 各 1 |
| (无分类) | 14 | | | |

14 个"无分类"条目正是下文的 skill-bundle 插件（`strict: false`）。

### 插件来源机制（source 字段）

| source 类型 | 数量 | 含义 |
|-------------|-----:|------|
| `url` | 122 | 指向完整外部 git 仓库 |
| `git-subdir` | 61 | 指向外部仓库的子目录 + 固定 `sha` |
| 字符串简写 | 51 | 简写形式的源引用 |
| `github` | 2 | GitHub 简写 |

关键设计：外部插件通过 **固定 commit SHA** 锁定版本（供应链安全），由 CI 每晚自动检测上游更新并逐个升级。

### skill-bundle 插件（strict: false）

14 个条目用 `strict: false` + 显式 `skills` 数组的方式，直接收录上游仓库里没有 `plugin.json` 清单、只有 `SKILL.md` 的技能集合。每个技能注册为 `<plugin-name>:<skill-name>`。

## 四、内置插件（plugins/，37 个）

源码直接维护在本仓库内。`example-plugin/` 是参考实现，展示标准结构：

```
example-plugin/
├── .claude-plugin/plugin.json   # 元数据（必需）
├── .mcp.json                    # MCP 服务器配置（可选）
├── commands/                    # 斜杠命令
├── skills/*/SKILL.md            # 技能
├── README.md
└── LICENSE
```

组件覆盖情况（37 个内置插件中）：
- 含 `commands/`：13 个
- 含 `skills/`：13 个
- 含 `agents/`：7 个
- 含 `hooks/`：5 个
- 含 `.mcp.json`：16 个（内置 + 外部合计）

代表性内置插件：各语言 LSP（`typescript-lsp` / `pyright-lsp` / `rust-analyzer-lsp` / `gopls-lsp` 等 11 个）、`code-review`、`code-simplifier`、`skill-creator`、`plugin-dev`、`mcp-server-dev`、`feature-dev`、`security-guidance`。

## 五、第三方插件（external_plugins/，15 个）

源码随仓库托管的合作方插件：`asana`、`linear`、`github`、`gitlab`、`firebase`、`discord`、`telegram`、`imessage`、`context7`、`greptile`、`playwright`、`serena`、`laravel-boost`、`terraform`、`fakechat`。

## 六、自动化与治理（.github/）

仓库的运维几乎全自动，这是它最有特点的部分。

### 工作流（8 个）

| 工作流 | 作用 |
|--------|------|
| `bump-plugin-shas.yml` | **每晚 07:23 UTC** 扫描外部插件上游 HEAD，发现新提交则校验并逐个开 PR 升级 SHA |
| `revert-failed-bumps.yml` | 升级后若失败则自动回滚 |
| `validate-plugins.yml` | PR 必需检查：`claude plugin validate` |
| `validate-frontmatter.yml` | 校验 SKILL.md / 命令的 frontmatter |
| `validate-licenses.yml` | 许可证校验 |
| `scan-plugins.yml` | 安全扫描（`scan` 必需检查） |
| `check-mcp-urls.yml` | 校验 MCP 服务器 URL（`check` 必需检查） |
| `close-external-prs.yml` | 自动关闭外部直接提交的 PR |

### 设计要点（值得注意的工程权衡）

- **绕过 `on:pull_request` 递归防护**：自动升级 PR 用默认 `GITHUB_TOKEN` 创建，不会触发 `on:pull_request` 工作流，因此必需状态检查（`validate`/`scan`/`check`）永远不会报告、PR 会永久卡住。解决办法是对每个 bump 分支 `workflow_dispatch` 这些工作流——check run 落在分支 HEAD（即 PR head）上，从而满足必需检查。这是仓库里反复出现的核心机制，多处注释都在解释它。
- **逐插件隔离**：每个外部插件单独开 PR、单独校验，失败的条目不会拖累其他升级。
- **成本控制**：`max-bumps` 限制每晚升级数量。

### 安全审查（policy/prompt.md）

收录前用 LLM 做安全/隐私审查，标准是"**是否负责任地处理用户数据**"，而不仅是"是否恶意"——即使非恶意，若观测范围超出声明用途、或安装描述未如实披露行为，也会被拒。审查覆盖 plugin.json、.mcp.json、hooks、所有 SKILL.md / agents / commands 及被引用的源文件。

## 七、贡献路径

- **内置插件**：Anthropic 团队成员开发，参照 `plugins/example-plugin`。
- **外部插件**：合作方通过[提交表单](https://clau.de/plugin-directory-submission)申请，须满足质量与安全标准。

## 八、给读者的快速判断

- 想看"目录里有什么" → 读 `.claude-plugin/marketplace.json`。
- 想加一个内置插件 → 抄 `plugins/example-plugin/` 的结构，再在 marketplace.json 加条目。
- 想理解 CI 为什么这么绕 → 读 `bump-plugin-shas.yml` 顶部那段长注释（GITHUB_TOKEN 递归防护是一切复杂度的根源）。
- 这个仓库**没有传统意义的应用代码**，没有可"运行"的程序；它的本质是清单管理 + 自动化运维。
