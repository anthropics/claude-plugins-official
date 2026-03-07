# Skill: env-doctor

## 描述
环境变量健康检查工具。扫描项目代码中所有环境变量引用，对比 `.env.example` 和实际 `.env`，检测硬编码密钥，验证变量格式，自动生成 `.env.example` 模板。

## 触发条件
当用户说出以下内容时激活：
- "检查环境变量"
- "env check"
- "env doctor"
- "检查 .env"

## 支持的项目类型
- JavaScript / TypeScript（`process.env.XXX`、`import.meta.env.XXX`）
- Python（`os.environ`、`os.getenv`、`os.environ.get`）
- Go（`os.Getenv`、`os.LookupEnv`）

---

## 执行步骤

### 阶段 1：扫描代码中的环境变量引用

#### JS/TS 项目
```bash
# 扫描 process.env.XXX
grep -rn --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' --include='*.mjs' --include='*.cjs' \
  -oP 'process\.env\.([A-Z_][A-Z0-9_]*)' . 2>/dev/null | \
  sed 's/.*process\.env\.//' | sort -u

# 扫描 import.meta.env.XXX（Vite 项目）
grep -rn --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
  -oP 'import\.meta\.env\.([A-Z_][A-Z0-9_]*)' . 2>/dev/null | \
  sed 's/.*import\.meta\.env\.//' | sort -u
```

#### Python 项目
```bash
# 扫描 os.environ["XXX"]、os.environ.get("XXX")、os.getenv("XXX")
grep -rn --include='*.py' \
  -oP '(os\.environ\[[\x27"]([A-Z_][A-Z0-9_]*)[\x27"]\]|os\.environ\.get\([\x27"]([A-Z_][A-Z0-9_]*)[\x27"]|os\.getenv\([\x27"]([A-Z_][A-Z0-9_]*)[\x27"])' . 2>/dev/null | \
  grep -oP '[A-Z_][A-Z0-9_]{2,}' | sort -u
```

#### Go 项目
```bash
# 扫描 os.Getenv("XXX")、os.LookupEnv("XXX")
grep -rn --include='*.go' \
  -oP '(os\.Getenv|os\.LookupEnv)\([\x27"]([A-Z_][A-Z0-9_]*)[\x27"]\)' . 2>/dev/null | \
  grep -oP '[A-Z_][A-Z0-9_]{2,}' | sort -u
```

#### 通用（配置文件中的变量引用）
```bash
# 扫描 docker-compose.yml、Dockerfile 中的环境变量
grep -rn --include='docker-compose*.yml' --include='docker-compose*.yaml' --include='Dockerfile*' \
  -oP '\$\{([A-Z_][A-Z0-9_]*)\}' . 2>/dev/null | \
  grep -oP '[A-Z_][A-Z0-9_]{2,}' | sort -u
```

### 阶段 2：对比 .env.example 与 .env

```bash
# 提取 .env.example 中定义的变量名
ENV_EXAMPLE=".env.example"
ENV_FILE=".env"

if [ -f "$ENV_EXAMPLE" ]; then
  EXAMPLE_VARS=$(grep -v '^#' "$ENV_EXAMPLE" | grep -v '^$' | cut -d'=' -f1 | sort)
else
  echo "[WARN] .env.example 不存在，将在阶段 5 自动生成"
  EXAMPLE_VARS=""
fi

if [ -f "$ENV_FILE" ]; then
  ENV_VARS=$(grep -v '^#' "$ENV_FILE" | grep -v '^$' | cut -d'=' -f1 | sort)
else
  echo "[WARN] .env 文件不存在"
  ENV_VARS=""
fi

# 在 .env.example 中但不在 .env 中的变量（缺失）
comm -23 <(echo "$EXAMPLE_VARS") <(echo "$ENV_VARS")

# 在代码中引用但不在 .env.example 中的变量（未文档化）
comm -23 <(echo "$CODE_VARS") <(echo "$EXAMPLE_VARS")
```

### 阶段 3：检测硬编码密钥/凭据

使用以下正则模式扫描代码中的硬编码敏感信息：

```bash
# 硬编码密钥检测正则模式表
# | 模式名称           | 正则表达式                                                    |
# |-------------------|--------------------------------------------------------------|
# | API Key 赋值       | (api[_-]?key|apikey)\s*[:=]\s*["'][a-zA-Z0-9_\-]{16,}["']   |
# | Secret 赋值        | (secret|SECRET)\s*[:=]\s*["'][a-zA-Z0-9_\-]{8,}["']         |
# | Password 赋值      | (password|passwd|pwd)\s*[:=]\s*["'][^"']{4,}["']             |
# | Token 赋值         | (token|TOKEN)\s*[:=]\s*["'][a-zA-Z0-9_\-\.]{16,}["']        |
# | AWS Key            | AKIA[0-9A-Z]{16}                                             |
# | Private Key        | -----BEGIN (RSA |EC )?PRIVATE KEY-----                       |
# | JWT                | eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}                   |
# | 连接字符串          | (mongodb|postgres|mysql|redis):\/\/[^\s"']{10,}              |
# | Bearer Token       | Bearer\s+[a-zA-Z0-9_\-\.]{20,}                              |
# | GitHub Token       | gh[pousr]_[a-zA-Z0-9]{36,}                                   |
# | Slack Token        | xox[baprs]-[a-zA-Z0-9\-]{10,}                               |
# | OpenAI Key         | sk-[a-zA-Z0-9]{20,}                                          |

grep -rn \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
  --include='*.py' --include='*.go' --include='*.json' --include='*.yaml' --include='*.yml' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=vendor --exclude-dir=__pycache__ \
  --exclude-dir=dist --exclude-dir=build --exclude-dir=.next \
  --exclude='*.lock' --exclude='package-lock.json' --exclude='bun.lockb' \
  -P '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC )?PRIVATE KEY-----|eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}|(mongodb|postgres|mysql|redis):\/\/[^\s"'\'']{10,}|gh[pousr]_[a-zA-Z0-9]{36,}|xox[baprs]-[a-zA-Z0-9\-]{10,}|sk-[a-zA-Z0-9]{20,})' .

# 检测变量赋值中的硬编码
grep -rn \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
  --include='*.py' --include='*.go' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=vendor \
  -P '(api[_-]?key|secret|password|passwd|pwd|token)\s*[:=]\s*["\x27][a-zA-Z0-9_\-]{8,}["\x27]' . \
  -il 2>/dev/null
```

### 阶段 4：验证变量格式

对 `.env` 文件中的变量值进行格式验证：

```
格式验证规则表
┌──────────────────┬─────────────────────────────────────┬──────────────────────┐
│ 变量名模式        │ 期望格式                             │ 验证正则              │
├──────────────────┼─────────────────────────────────────┼──────────────────────┤
│ *_URL, *_URI     │ 合法 URL                            │ ^https?://\S+$       │
│ *_PORT           │ 1-65535 的整数                       │ ^[0-9]+$ (范围检查)   │
│ *_HOST           │ 域名或 IP                            │ ^[\w.\-]+$           │
│ *_EMAIL          │ 邮箱格式                             │ ^[^@]+@[^@]+\.[^@]+$│
│ *_ENABLED,       │ 布尔值                               │ ^(true|false|0|1)$   │
│ *_DISABLED,      │                                     │                      │
│ IS_*, ENABLE_*,  │                                     │                      │
│ USE_*, HAS_*     │                                     │                      │
│ *_TIMEOUT,       │ 正整数                               │ ^[1-9][0-9]*$        │
│ *_INTERVAL,      │                                     │                      │
│ *_TTL, *_LIMIT   │                                     │                      │
│ *_PATH, *_DIR    │ 路径格式（非空）                      │ ^[/~.][\S]+$         │
│ *_KEY, *_SECRET, │ 非占位符（不是 xxx、your-*、         │ 不匹配               │
│ *_TOKEN          │ changeme、TODO 等）                  │ ^(xxx|your-.*|       │
│                  │                                     │ changeme|TODO|       │
│                  │                                     │ REPLACE_ME|          │
│                  │                                     │ placeholder)$        │
└──────────────────┴─────────────────────────────────────┴──────────────────────┘
```

```bash
# 格式验证脚本逻辑（伪代码，实际用 bash 实现）
while IFS='=' read -r key value; do
  [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
  value=$(echo "$value" | sed 's/^["'\'']//' | sed 's/["'\'']$//')

  # URL 验证
  if [[ "$key" =~ _(URL|URI)$ ]]; then
    [[ ! "$value" =~ ^https?:// ]] && echo "[FORMAT] $key: 期望 URL 格式，实际值: $value"
  fi

  # 端口验证
  if [[ "$key" =~ _PORT$ ]]; then
    if [[ ! "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then
      echo "[FORMAT] $key: 期望 1-65535 端口号，实际值: $value"
    fi
  fi

  # 布尔值验证
  if [[ "$key" =~ ^(IS_|ENABLE_|USE_|HAS_) || "$key" =~ _(ENABLED|DISABLED)$ ]]; then
    [[ ! "$value" =~ ^(true|false|0|1|yes|no)$ ]] && echo "[FORMAT] $key: 期望布尔值，实际值: $value"
  fi

  # 占位符检测
  if [[ "$key" =~ _(KEY|SECRET|TOKEN|PASSWORD)$ ]]; then
    if [[ "$value" =~ ^(xxx|your-|changeme|TODO|REPLACE_ME|placeholder|example|test123) ]]; then
      echo "[PLACEHOLDER] $key: 疑似占位符未替换: $value"
    fi
  fi
done < .env
```

### 阶段 5：自动生成 .env.example

如果项目中不存在 `.env.example`：

```bash
# 从代码扫描结果和现有 .env 合并生成 .env.example
if [ ! -f ".env.example" ]; then
  echo "# Environment Variables Template" > .env.example
  echo "# Generated by env-doctor on $(date +%Y-%m-%d)" >> .env.example
  echo "# Copy this file to .env and fill in your values" >> .env.example
  echo "" >> .env.example

  # 按类别分组输出
  # 1. 从代码中扫描到的变量
  for var in $CODE_VARS; do
    # 根据变量名猜测类别和默认值
    case "$var" in
      *_PORT)     echo "$var=3000" ;;
      *_HOST)     echo "$var=localhost" ;;
      *_URL|*_URI) echo "$var=https://example.com" ;;
      *_ENABLED|*_DISABLED|IS_*|ENABLE_*|USE_*) echo "$var=false" ;;
      *_KEY|*_SECRET|*_TOKEN|*_PASSWORD) echo "$var=your-${var,,}-here" ;;
      *_ENV|NODE_ENV) echo "$var=development" ;;
      *_TIMEOUT|*_TTL) echo "$var=30000" ;;
      *_LIMIT) echo "$var=100" ;;
      *) echo "$var=" ;;
    esac
  done >> .env.example

  echo "[INFO] 已生成 .env.example，包含 $(wc -l < .env.example) 行"
fi
```

---

## 决策流程图

```
开始 env-doctor
      │
      ▼
┌──────────────┐
│ 检测项目类型   │ ──→ JS/TS? Python? Go? 混合?
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 扫描环境变量   │ ──→ 收集 CODE_VARS 列表
│ 引用          │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────────┐
│ .env.example │─否─→│ 阶段5: 自动生成   │
│ 存在?        │     │ .env.example     │
└──────┬───────┘     └────────┬────────┘
       │是                     │
       ▼                      ▼
┌──────────────┐
│ 对比 .env 与  │ ──→ 报告缺失变量、未文档化变量
│ .env.example │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 检测硬编码    │ ──→ 报告发现的敏感信息（文件:行号）
│ 密钥/凭据    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 格式验证      │ ──→ 报告格式不合规的变量
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 输出报告      │
└──────────────┘
```

---

## 输出报告格式

```
========================================
  env-doctor 环境变量健康检查报告
========================================

项目类型: [JS/TS | Python | Go | 混合]
扫描时间: YYYY-MM-DD HH:MM:SS

── 1. 变量引用扫描 ──────────────────
  代码中引用的环境变量: N 个
  [列出所有变量名]

── 2. .env 对比 ─────────────────────
  [MISSING]  VAR_NAME    在 .env.example 中定义但 .env 中缺失
  [UNDOC]    VAR_NAME    在代码中使用但未在 .env.example 中记录
  [UNUSED]   VAR_NAME    在 .env 中定义但代码中未使用

── 3. 硬编码密钥检测 ────────────────
  [CRITICAL] src/config.ts:42  疑似硬编码 API Key
  [CRITICAL] lib/db.py:15      疑似硬编码数据库连接字符串

── 4. 格式验证 ──────────────────────
  [FORMAT]      DATABASE_URL: 期望 URL 格式
  [PLACEHOLDER] API_SECRET: 疑似占位符未替换

── 5. 总结 ──────────────────────────
  通过: X 项 | 警告: Y 项 | 严重: Z 项

========================================
```

---

## 质量检查清单

在报告完成前，逐项验证：

- [ ] 是否扫描了所有支持的文件类型（.ts/.js/.py/.go）
- [ ] 是否排除了 node_modules、vendor、.git、dist、build 等目录
- [ ] 是否检查了 docker-compose 和 Dockerfile 中的环境变量
- [ ] .env.example 与 .env 的对比结果是否准确
- [ ] 硬编码检测是否排除了测试文件中的 mock 值
- [ ] 格式验证是否覆盖了所有规则表中的模式
- [ ] 占位符检测是否识别了常见占位符模式
- [ ] 报告格式是否清晰、分类是否正确
- [ ] 如果生成了 .env.example，是否按类别分组且有注释
- [ ] 是否向用户报告了总结统计（通过/警告/严重）

## 注意事项

- 不要读取或显示 `.env` 文件中的实际敏感值，只报告变量名
- 硬编码检测可能存在误报，标注 `[疑似]` 让用户确认
- `.env.example` 中不应包含真实密钥值，只包含格式示例
- 对于 monorepo 项目，递归检查子目录中的 `.env` 文件
