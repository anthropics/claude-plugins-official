# Issue JSON 格式规范

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | Yes | 短标识符，如 `"life-002"`, `"tech-001"` |
| `domain` | string | Yes | 领域：personal, company, startup, family, career 等 |
| `title` | string | Yes | 简洁的决策问题，用用户的语言 |
| `background` | string | Yes | 2-5 句话的背景上下文 |
| `constraints` | string[] | Yes | 硬性限制（预算、时间、不可妥协的要求） |
| `goals` | string[] | Yes | 期望达成的结果 |
| `inputs` | object[] | Yes | 上下文信息或已有方案（见下） |
| `deadline` | string\|null | No | 人类可读的截止时间，如 `"本月底"`, `"2周"` |
| `priority` | string | Yes | `low` / `medium` / `high` / `critical` |

### inputs 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | `"context"`（上下文/方案描述）或 `"doc"`（文档引用） |
| `name` | string | 名称标签 |
| `summary` | string | 内容摘要 |
| `path` | string | 仅 type="doc" 时需要，文件路径 |

## 示例 1：个人生活决策

```json
{
  "id": "life-002",
  "domain": "personal",
  "title": "深圳租房：续租老房子还是搬到公司附近",
  "background": "我在深圳南山科技园上班，目前住在龙华，月租 2800 的单间，通勤地铁单程 50 分钟。最近房东要涨租到 3200。公司附近（南山）同等条件的房子要 4500-5000。我的月薪到手 15K，每月能存 4000 左右。租约下个月到期，必须做决定。",
  "constraints": [
    "月租预算上限 5000 元",
    "不接受合租（需要独立空间写代码）",
    "通勤时间希望控制在 30 分钟以内",
    "至少签一年租约"
  ],
  "goals": [
    "在预算和生活质量之间找到最优解",
    "明确下一步行动（续租/搬家/其他方案）"
  ],
  "inputs": [
    {"type": "context", "name": "方案A", "summary": "续租龙华，接受涨价到 3200，通勤 50 分钟不变"},
    {"type": "context", "name": "方案B", "summary": "搬到南山科技园附近，月租 4800，通勤 10 分钟步行"},
    {"type": "context", "name": "方案C", "summary": "搬到西丽/大学城片区，月租 3500-3800，通勤 20 分钟地铁"},
    {"type": "context", "name": "隐性成本", "summary": "搬家费用约 1500，每天通勤多出的 40 分钟折算时薪约 35 元"}
  ],
  "deadline": "本月底",
  "priority": "high"
}
```

## 示例 2：技术选型决策

```json
{
  "id": "tech-001",
  "domain": "startup",
  "title": "独立开发者做「唐朝朝廷多智能体决策系统」选什么技术栈",
  "background": "我是一个独立开发者，想做一个模拟唐朝三省六部的多智能体个人决策辅助系统。核心流程：用户输入一个待决策事项（Issue），系统通过多个 AI Agent 依次完成草案→审议→定稿→六部执行计划。目前有一个纯 Python + urllib 的 MVP 原型（约 200 行）以及基于CLI的交互原型，调用阿里云 DashScope API（qwen3-max），能跑通完整流程。现在要考虑下一步技术选型，把它做成一个可以给朋友用的产品。",
  "constraints": [
    "一个人开发，每天最多投入 3 小时",
    "预算有限，月成本控制在 500 元以内（不含 API 调用费）",
    "希望 2 周内出可用版本",
    "第二期针对用户是非技术人员，需要有简单的交互界面"
  ],
  "goals": [
    "从 MVP 命令行进化到有 Web 界面的产品",
    "选定前后端技术栈",
    "决定是否引入 LangChain/CrewAI 等 Agent 框架",
    "确定部署方案",
    "想通过这个项目跑通github actions +阿里云的完整部署流程"
  ],
  "inputs": [
    {"type": "context", "name": "当前技术栈", "summary": "Python 3.9 + urllib + DashScope API，无框架无数据库，纯脚本"},
    {"type": "context", "name": "备选方案", "summary": "A) 继续纯 Python + FastAPI 轻量路线；B) 用 LangChain + FastAPI；C) 用 Next.js 全栈 + Python API；D) 直接用 Streamlit/Gradio 快速出界面"},
    {"type": "context", "name": "开发者背景", "summary": "熟悉 Python，了解前端但不精通，没用过 LangChain,觉得langchain 太重了"}
  ],
  "deadline": "2周",
  "priority": "high"
}
```
