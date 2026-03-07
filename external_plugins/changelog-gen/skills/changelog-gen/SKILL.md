# Changelog Gen Skill

## 概述

智能 CHANGELOG 生成器 — 从 git 历史中提取 conventional commits，按类别分组，生成人类可读的 Keep a Changelog 格式变更日志。

## 触发条件

当用户说出以下内容时激活：
- "生成 changelog"
- "generate changelog"
- "更新变更日志"
- "what changed"
- "有什么变更"
- "changelog since..."

## 执行流程

### 第一步：确定 Commit 范围

询问用户或自动推断范围：

```bash
# 方式 1：从某个 tag 到 HEAD
git log v1.0.0..HEAD --oneline

# 方式 2：最近 N 个 commit
git log -n 20 --oneline

# 方式 3：从上一个 tag 到 HEAD（自动检测）
git describe --tags --abbrev=0 2>/dev/null
# 如果有 tag，则使用 <last-tag>..HEAD
# 如果没有 tag，则使用所有 commit

# 方式 4：两个 tag 之间
git log v1.0.0..v2.0.0 --oneline

# 方式 5：基于日期
git log --after="2024-01-01" --oneline
```

### 第二步：读取 Git Log（详细格式）

使用以下命令获取结构化 commit 信息：

```bash
# 主命令 — 获取完整的 commit 信息
git log <range> --format="---COMMIT_START---%nhash: %H%nshort_hash: %h%nauthor: %an%ndate: %ai%nsubject: %s%nbody: %b%n---COMMIT_END---"

# 简化版 — 仅获取 subject 行
git log <range> --format="%h|%s|%an|%ai" --no-merges

# 获取 merge commit（单独处理）
git log <range> --merges --format="%h|%s|%an|%ai"
```

过滤掉 merge commit（除非包含有意义的信息）：

```bash
git log <range> --no-merges --format="%h|%s|%an|%ai"
```

### 第三步：按 Conventional Commits 分类

#### 分类规则表

| 前缀 | CHANGELOG 分类 | 说明 | 显示优先级 |
|------|---------------|------|-----------|
| `feat:` / `feat(scope):` | Added | 新功能 | 1 |
| `fix:` / `fix(scope):` | Fixed | Bug 修复 | 2 |
| `perf:` / `perf(scope):` | Performance | 性能优化 | 3 |
| `refactor:` / `refactor(scope):` | Changed | 重构 | 4 |
| `docs:` / `docs(scope):` | Documentation | 文档变更 | 5 |
| `test:` / `test(scope):` | Tests | 测试相关 | 6 |
| `chore:` / `chore(scope):` | Maintenance | 构建/工具/依赖 | 7 |
| `style:` / `style(scope):` | Style | 代码格式（不影响功能） | 8 |
| `ci:` / `ci(scope):` | CI/CD | 持续集成 | 9 |
| `build:` / `build(scope):` | Build | 构建系统 | 10 |
| `revert:` | Reverted | 回滚 | 3 |
| 无前缀 | Other | 未分类 | 99 |

#### 解析逻辑

```
正则匹配 subject 行：
^(feat|fix|perf|refactor|docs|test|chore|style|ci|build|revert)(\(.+\))?(!)?:\s*(.+)$

捕获组：
- group 1: type（类型）
- group 2: scope（范围，可选）
- group 3: !（breaking change 标记，可选）
- group 4: description（描述）
```

### 第四步：检测 Breaking Changes

Breaking changes 必须醒目标注。检测方式：

1. **Subject 中的 `!` 标记**：`feat!: remove legacy API`
2. **Body 中的 `BREAKING CHANGE:` 关键字**：
   ```
   feat: update auth system

   BREAKING CHANGE: JWT token format changed, all existing tokens will be invalidated.
   ```
3. **Body 中的 `BREAKING-CHANGE:` 关键字**（带连字符的变体）
4. **Footer 中的 `BREAKING CHANGE:` 或 `BREAKING-CHANGE:`**

```bash
# 快速扫描包含 breaking change 的 commit
git log <range> --format="%H %s%n%b" | grep -B1 -i "BREAKING.CHANGE\|^[a-z]*!:"
```

### 第五步：自动检测版本号

按优先级依次检查以下文件：

```bash
# 1. package.json (Node.js)
cat package.json 2>/dev/null | grep '"version"' | head -1
# 提取: "version": "1.2.3" → 1.2.3

# 2. pyproject.toml (Python)
cat pyproject.toml 2>/dev/null | grep '^version' | head -1
# 提取: version = "1.2.3" → 1.2.3

# 3. Cargo.toml (Rust)
cat Cargo.toml 2>/dev/null | grep '^version' | head -1
# 提取: version = "1.2.3" → 1.2.3

# 4. build.gradle / build.gradle.kts (Java/Kotlin)
cat build.gradle 2>/dev/null | grep 'version' | head -1

# 5. pubspec.yaml (Flutter/Dart)
cat pubspec.yaml 2>/dev/null | grep '^version:' | head -1

# 6. Git tag（最近的 tag）
git describe --tags --abbrev=0 2>/dev/null

# 7. 如果都没有，使用日期作为版本
date +"%Y.%m.%d"
```

如果检测到版本号，建议用户确认或修改。

### 第六步：生成 CHANGELOG 条目

#### 输出模板（Keep a Changelog 格式）

```markdown
## [版本号] - YYYY-MM-DD

### Breaking Changes

- **scope**: 描述 breaking change 的具体影响 ([commit-hash])
  - Migration: 迁移指引（如果 commit body 中有提供）

### Added

- **scope**: 功能描述，用人类可读的语言改写 ([commit-hash])
- 另一个新功能 ([commit-hash])

### Fixed

- **scope**: 修复了什么问题 ([commit-hash])

### Performance

- **scope**: 优化了什么 ([commit-hash])

### Changed

- **scope**: 重构/变更了什么 ([commit-hash])

### Documentation

- 更新了什么文档 ([commit-hash])

### Maintenance

- 依赖更新、构建工具变更等 ([commit-hash])
```

#### 条目改写规则

- 去掉 conventional commit 前缀（`feat:`, `fix:` 等）
- 首字母大写
- 如果有 scope，以 `**scope**:` 开头
- 用完整句子描述变更，而不是机械复制 commit message
- 合并相关的小 commit（如多次修复同一个功能的 commit）
- commit hash 使用短格式（7 位），链接到仓库（如果能检测到 remote URL）

#### 检测仓库 URL（用于生成链接）

```bash
# 获取 remote URL 并转换为 HTTPS 格式
git remote get-url origin 2>/dev/null
# git@github.com:user/repo.git → https://github.com/user/repo
# https://github.com/user/repo.git → https://github.com/user/repo
```

如果检测到仓库 URL，commit hash 生成为链接格式：
```markdown
- 功能描述 ([abc1234](https://github.com/user/repo/commit/abc1234))
```

### 第七步：追加 vs 新建 CHANGELOG

#### 判断逻辑

```bash
# 检查是否存在 CHANGELOG 文件
ls CHANGELOG.md CHANGELOG changelog.md 2>/dev/null
```

**如果 CHANGELOG.md 已存在：**
1. 读取现有内容
2. 找到第一个 `## [` 开头的行（即第一个版本条目）
3. 在该行之前插入新版本条目
4. 保留文件头部（标题、描述等）

**如果 CHANGELOG.md 不存在：**
1. 创建新文件，包含标准头部：

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [版本号] - YYYY-MM-DD

（生成的条目）
```

### 第八步：质量检查

生成完成后，执行以下检查：

- [ ] 每个 commit 都已被分类（没有遗漏）
- [ ] Breaking changes 已被单独标注并放在最前面
- [ ] 版本号格式正确（符合 semver）
- [ ] 日期格式正确（YYYY-MM-DD）
- [ ] 没有重复条目
- [ ] 没有空的分类区块（如果某个分类没有条目，则省略该区块）
- [ ] 合并了相关的小 commit（避免冗余）
- [ ] 语言风格一致（全英文或全中文，与项目现有 CHANGELOG 保持一致）
- [ ] 如果是追加模式，没有破坏现有 CHANGELOG 的格式
- [ ] Commit hash 链接正确（如果有仓库 URL）

### 特殊处理

#### Monorepo 支持

如果检测到 monorepo 结构（存在 `packages/`、`apps/`、`libs/` 等目录）：

```bash
# 按路径过滤 commit
git log <range> --no-merges --format="%h|%s" -- packages/core/
```

可以按 package 分组生成 CHANGELOG。

#### 多语言支持

- 检查现有 CHANGELOG.md 的语言
- 如果是中文项目（根据 README 或现有 CHANGELOG 判断），用中文生成条目
- 默认使用英文

## 使用示例

**用户**: 生成 changelog

**执行**:
1. 自动检测最近一个 tag 到 HEAD 的范围
2. 读取 git log
3. 分类、改写、生成
4. 追加到 CHANGELOG.md 或创建新文件

**用户**: generate changelog from v2.0.0 to v3.0.0

**执行**:
1. 使用 `v2.0.0..v3.0.0` 范围
2. 读取、分类、生成
3. 让用户确认版本号（建议 v3.0.0）

**用户**: what changed in the last 10 commits

**执行**:
1. 使用 `git log -n 10`
2. 分类展示变更摘要（不写入文件，仅展示）
