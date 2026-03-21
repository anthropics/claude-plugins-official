# 各省部输出 JSON 格式规范

## Phase 1: 三省决策

### 中书省 (zhongshu) — 草案

```json
{
  "issue_id": "string",
  "assumptions": ["关键假设1", "关键假设2"],
  "options": [
    {
      "name": "方案名称",
      "summary": "简要描述",
      "pros": ["优势1", "优势2"],
      "cons": ["劣势1", "劣势2"],
      "rough_steps": ["步骤1", "步骤2", "步骤3"]
    }
  ]
}
```

**约束：** 至少 2 套方案，每套必须包含 summary、pros、cons、rough_steps，不得空泛。

### 门下省 (menxia) — 审议

```json
{
  "issue_id": "string",
  "risks": ["风险1", "风险2", "风险3"],
  "objections": ["反对点1"],
  "revisions": ["修订建议1", "修订建议2"]
}
```

**约束：** 至少 3 条风险，至少 2 条修订建议，不得直接定案。

### 尚书省 (shangshu) — 定稿

```json
{
  "issue_id": "string",
  "imperial_choice": {
    "name": "圣裁优先方案名称",
    "reason": "选择理由"
  },
  "alternatives": [
    {
      "name": "备选方案名称",
      "reason": "作为备选的理由"
    }
  ],
  "decision_notes": ["决策备注1", "决策备注2"]
}
```

**约束：** 必须包含 imperial_choice 且说明理由，不得忽略门下省反对意见。

## Phase 2: 六部执行

### 吏部 (libu) — 分工

```json
{
  "roles": ["角色1: 负责事项", "角色2: 负责事项"]
}
```

**约束：** 尽量使用具体角色或人员，避免抽象占位。

### 户部 (hubu) — 资源

```json
{
  "budget": "预算估算（区间）",
  "time": "时间估算（区间）",
  "gaps": ["资源缺口1", "资源缺口2"]
}
```

**约束：** 给出区间估计，明确资源缺口与风险提示。

### 礼部 (libu_ritual) — 流程

```json
{
  "process": ["流程步骤1", "流程步骤2"],
  "comms": ["沟通要点1", "沟通要点2"]
}
```

**约束：** 不得与兵部执行步骤冲突。

### 兵部 (bingbu) — 执行

```json
{
  "steps": ["执行步骤1", "执行步骤2"],
  "milestones": ["M1: 里程碑1", "M2: 里程碑2"]
}
```

**约束：** 步骤必须可操作且有顺序。

### 刑部 (xingbu) — 风险

```json
{
  "risks": ["风险1", "风险2"],
  "mitigations": ["规避措施1", "规避措施2"]
}
```

**约束：** 覆盖高概率与高影响风险。

### 工部 (gongbu) — 工具

```json
{
  "tools": ["工具1", "工具2"],
  "templates": ["模板1", "模板2"]
}
```

**约束：** 输出必须与资源、流程、执行步骤一致。

## 汇总: exec_plan.json

```json
{
  "issue_id": "string",
  "liubu": {
    "libu": { "roles": [...] },
    "hubu": { "budget": "", "time": "", "gaps": [...] },
    "libu_ritual": { "process": [...], "comms": [...] },
    "bingbu": { "steps": [...], "milestones": [...] },
    "xingbu": { "risks": [...], "mitigations": [...] },
    "gongbu": { "tools": [...], "templates": [...] }
  }
}
```

## decision.md 报告结构

最终报告按以下结构生成 Markdown：

1. `# {issue.title}`
2. `## 背景与问题` — issue.background
3. `## 中书省·草案方案` — 每个方案含优势/劣势/粗步骤
4. `## 门下省·审议意见` — 风险与修订建议
5. `## 尚书省·圣裁定稿` — 圣裁优先方案 + 备选
6. `## 吏部·分工` — 角色分配
7. `## 户部·资源` — 预算/时间/缺口
8. `## 礼部·流程` — 流程步骤与沟通要点
9. `## 兵部·执行` — 执行步骤与里程碑
10. `## 刑部·风险` — 风险与规避措施
11. `## 工部·工具` — 工具与模板
