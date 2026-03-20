# Claude Code Feishu Channel / 飞书 Channel 插件

Control Claude Code from your phone via Feishu (Lark). Send a message to your bot, Claude executes on your computer, and the result comes back in chat.

通过飞书机器人远程控制 Claude Code。在手机上发消息，Claude 在你的电脑上执行，结果直接回到飞书。

---

## Requirements / 环境要求

- [Claude Code](https://claude.ai/code) v2.1.80+，使用 **claude.ai 账号**登录（不支持 API key）
- [Bun](https://bun.sh) runtime
- 飞书**企业自建应用**

---

## Feishu App Setup / 飞书应用配置

> **Important — step order matters / 注意操作顺序：**
> Configure App ID/Secret → Save credentials → Start server → Then configure long connection in the console.
> 先配置 App ID/Secret → 保存凭证 → 启动服务 → 再到开放平台配置长连接。
> If the console still shows an error, stop and restart the server.
> 若控制台仍报错，尝试重启服务后再保存。

### Step 1 — Create a self-built app / 创建企业自建应用

Go to [Feishu Open Platform](https://open.feishu.cn/app) → **Create App** → **Self-built app**.

打开[飞书开放平台](https://open.feishu.cn/app) → 创建应用 → 企业自建应用。

### Step 2 — Get credentials / 获取凭证

Go to **Credentials & Basic Info** → copy **App ID** and **App Secret**.

进入**凭证与基础信息** → 复制 **App ID** 和 **App Secret**。

### Step 3 — Save credentials and start the server / 保存凭证并启动服务

```bash
mkdir -p ~/.claude/channels/feishu
cat > ~/.claude/channels/feishu/.env << EOF
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
```

Then start the server (keep this terminal open):

然后启动服务（保持这个终端不要关）：

```bash
cd claude-code-feishu-channel
bun server.ts
```

### Step 4 — Enable bot capability / 开启机器人能力

**App Capabilities → Add Capability → Bot** → Enable → Publish.

**应用能力 → 添加应用能力 → 机器人** → 开启 → 发布。

### Step 5 — Add permissions (batch import) / 批量导入权限

Go to **Permission Management → Bulk Import/Export** and paste the following JSON:

进入**权限管理 → 批量导入/导出权限**，粘贴以下 JSON：

```json
{
  "scopes": {
    "tenant": [
      "im:message",
      "im:message.group_msg",
      "im:message.p2p_msg:readonly",
      "im:message.reactions:read",
      "im:resource",
      "im:chat",
      "contact:user.base:readonly"
    ],
    "user": []
  }
}
```

<details>
<summary>Permission details / 权限说明</summary>

| Permission / 权限标识 | Description / 说明 |
|---|---|
| `im:message` | Send and receive messages / 收发消息 |
| `im:message.group_msg` | Read group messages / 读取群消息 |
| `im:message.p2p_msg:readonly` | Read DMs sent to bot / 读取私聊消息 |
| `im:message.reactions:read` | Read emoji reactions / 读取表情回复 |
| `im:resource` | Upload/download images and files / 上传下载图片文件 |
| `im:chat` | Get group info / 获取群组信息 |
| `contact:user.base:readonly` | Display usernames instead of IDs / 显示用户昵称而非 open_id |

</details>

### Step 6 — Subscribe to events / 订阅事件

**Events & Callbacks → Event Config → Add Event** → Search for **"接收消息"** → Select **接收消息 v2.0**.

**事件与回调 → 事件配置 → 添加事件** → 搜索**接收消息** → 选择**接收消息 v2.0**。

### Step 7 — Enable long connection / 开启长连接

Make sure the server from Step 3 is still running, then:

确保第3步的服务仍在运行，然后：

**Events & Callbacks → Subscription Method** → Select **Persistent Connection (长连接)** → Save.

**事件与回调 → 订阅方式** → 选择**使用长连接接收事件** → 保存。

### Step 8 — Publish the app / 发布应用

**Version Management & Release** → Create version → Fill in info → Save → Release.

**版本管理与发布** → 创建版本 → 填写基础信息 → 保存 → 发布。

### Step 9 — Find your bot / 找到机器人

In Feishu, go to **Workbench → Add to Favorites** → search for your bot name → Add.

在飞书中，进入**工作台 → 添加常用** → 搜索机器人名称 → 添加。

Double-click the bot to open the chat window.

双击机器人进入对话界面。

---

## Installation / 安装

### 1. Install Bun / 安装 Bun

```bash
curl -fsSL https://bun.sh/install | bash
source ~/.zshrc   # or ~/.bashrc
```

### 2. Clone and install dependencies / 克隆项目并安装依赖

```bash
git clone https://github.com/AwadYoo/claude-code-feishu-channel
cd claude-code-feishu-channel
bun install
```

### 3. Register with Claude Code / 注册到 Claude Code

Add to `~/.mcp.json` (create if it doesn't exist):

将以下内容添加到 `~/.mcp.json`（不存在则新建）：

```json
{
  "mcpServers": {
    "feishu": {
      "command": "bun",
      "args": ["/absolute/path/to/claude-code-feishu-channel/server.ts"]
    }
  }
}
```

---

## Usage / 使用方式

### Start / 启动

```bash
claude --dangerously-load-development-channels server:feishu --dangerously-skip-permissions
```

> **Note / 注意：** `--dangerously-skip-permissions` skips all confirmation prompts. Only use this on machines you trust and control.
> 此参数会跳过所有操作确认，仅在你完全信任的机器上使用。

### Pair your account / 配对账号

1. DM your bot on Feishu — it replies with a 6-character pairing code.

   在飞书中给机器人发任意消息，它会回复一个 6 位配对码。

2. In Claude Code, run:

   在 Claude Code 中运行：

   ```
   /feishu:access pair <code>
   ```

Done. Only your paired account can send messages to Claude — everyone else is silently dropped.

完成后，只有你的账号能触发 Claude，其他人的消息静默丢弃。

### Built-in commands / 内置命令

| Command / 命令 | Description / 说明 |
|---|---|
| `/ping` | Check if Claude Code is online / 检测 Claude Code 是否在线 |

---

## How it works / 工作原理

```
Feishu app (phone / 手机)
      │  DM / 私信
      ▼
Feishu Bot API — WebSocket long connection / 长连接
      │
      ▼
server.ts (Bun subprocess / 子进程)
      │  MCP notification
      ▼
Claude Code session
      │  reply tool
      ▼
Feishu app (response / 回复)
```

The channel server runs as an MCP subprocess spawned by Claude Code. Incoming messages are forwarded as `<channel>` events into the active Claude session. Claude calls the `reply` tool to send responses back — no public server or webhook URL required.

服务作为 MCP 子进程由 Claude Code 启动。飞书消息通过 WebSocket 长连接接收后，以 `<channel>` 事件注入 Claude 会话。Claude 通过 `reply` 工具回复，全程无需公网 IP 或 webhook。

---

## Security / 安全

- Only paired sender IDs can push messages into Claude. All others are silently dropped.
- The server operates within your Claude Code session scope only.
- `.env` is listed in `.gitignore` — never commit your credentials.

- 只有已配对的发送者 ID 才能向 Claude 推送消息，其他人的消息静默丢弃。
- 服务仅在你的 Claude Code 会话范围内操作。
- `.env` 已加入 `.gitignore`，凭证不会被提交。

---

## License / 许可证

Apache 2.0
