---
name: Train_Prep
description: This skill should be used when the user asks to "prepare training materials", "create training for [industry/client]", "制作培训材料", "准备培训", "给客户做培训方案", "Train_Prep", or wants to generate a consulting deliverable package (Word report + interactive HTML slides) for a specific industry/client. Involves multi-agent parallel research, pain point analysis, AI solution mapping, Word report generation, and interactive HTML presentation creation.
version: 0.1.0
---

# Train_Prep：AI 赋能行业培训材料制作工作流

## 技能概述

Train_Prep 封装了一套完整的 AI 咨询培训材料制作流程，从行业痛点调研到最终交付，涵盖：
- 多 Agent 并行调研（行业痛点 × AI 解决方案匹配）
- Word 方案报告生成（Markdown → pandoc → .docx）
- 交互式 HTML 培训幻灯片（多 Agent 并行开发 → 组装）

适用场景：为客户/行业高管准备 AI 赋能解决方案培训，需要同时输出 Word 报告和 HTML 演示材料。

---

## 快速启动检查

执行以下检查，确认环境就绪：
```bash
which pdftotext   # poppler，PDF 文本提取
which pandoc      # Markdown → Word 转换
```

若缺失（macOS）：`brew install poppler pandoc`

Linux：`sudo apt-get install poppler-utils pandoc`

---

## 工作流总览（三阶段）

```
阶段一：研究调研（多 Agent 并行）
  ├── PDF 参考资料提取（pdftotext）
  ├── Agent A：第一业务阶段痛点调研
  ├── Agent B：第二业务阶段痛点调研
  └── Agent C：第三业务阶段痛点调研 + 落地计划

阶段二：Word 报告
  ├── 组装 Markdown 章节
  ├── pandoc 转换为 .docx
  └── 用户确认质量

阶段三：HTML 交互培训材料（多 Agent 并行）
  ├── Agent A：HTML 框架 + CSS + JS + 封面/目录幻灯片
  ├── Agent B：第一业务阶段幻灯片
  ├── Agent C：第二业务阶段幻灯片
  ├── Agent D：第三业务阶段 + 落地计划 + 结束幻灯片
  └── 主进程：macOS 兼容组装脚本
```

---

## 阶段一：多 Agent 并行研究

### 第 1 步：提取 PDF 参考资料

将客户行业资料和己方能力介绍 PDF 转为文本：
```bash
pdftotext "己方能力介绍.pdf" /tmp/capability.txt
pdftotext "解决方案案例.pdf" /tmp/solutions.txt
```

**注意**：优先使用 pdftotext 而非 Read 工具读取 PDF，稳定性更好。

### 第 2 步：规划业务阶段分工

根据行业特点，将客户业务划分为 3 个阶段（每个 Agent 负责一个），示例：

| 行业 | Agent A | Agent B | Agent C |
|------|---------|---------|---------|
| 轨道交通 | 建设阶段 | 运维阶段 | 运营阶段 |
| 制造业 | 研发设计 | 生产制造 | 供应链/销售 |
| 医疗 | 临床诊断 | 医院运营 | 患者服务 |
| 政务 | 政策制定 | 行政审批 | 公共服务 |

### 第 3 步：并行启动 3 个研究 Agent

在同一条消息中同时发送 3 个 Agent 调用（最大化并行度），每个 Agent 收到：
- 行业背景和客户信息
- 己方 AI 能力描述（/tmp/capability.txt 内容）
- 该阶段的调研范围

**每个痛点的输出格式要求**：
```markdown
## 痛点 N：[名称]
**现状**：[当前存在的问题和挑战]
**AI 解决方案**：[具体方案组件列表]
**预期价值**：效率提升 X%，节省 Y 人力/年
**对应产品/技术**：[匹配的 AI 产品或技术栈]
```

**中间文件约定**（可自定义）：
- `/tmp/train_phase1.md` - 第一阶段
- `/tmp/train_phase2.md` - 第二阶段
- `/tmp/train_phase3.md` - 第三阶段（含落地计划）

---

## 阶段二：Word 报告生成

### 组装 Markdown 报告

撰写执行摘要和己方能力介绍，然后组装：
```bash
cat /tmp/train_header.md \
    /tmp/train_phase1.md \
    /tmp/train_phase2.md \
    /tmp/train_phase3.md \
    > /tmp/train_report.md
```

**报告结构**：执行摘要 → 己方能力介绍 → 各阶段方案 → 落地建议计划

### 转换为 Word
```bash
pandoc /tmp/train_report.md \
    -o "AI赋能[客户简称]_解决方案_v1.0.docx" \
    --from markdown --to docx
```

**等待用户确认 Word 报告质量后**，再进入阶段三。

---

## 阶段三：HTML 交互培训材料

### 核心架构约束（多 Agent 接口契约）

HTML 内容分 4 部分并行开发，需严格遵守：

| 部分 | 负责内容 | HTML 结构要求 |
|------|----------|--------------|
| Part 1 | 框架+CSS+JS+封面/目录幻灯片 | 完整 `<html><head>...</head><body><div id="slide-container">` + 幻灯片，**不写** `</body></html>`，`slide-container` **不关闭** |
| Part 2 | 第一阶段幻灯片 | 只有 `<div class="slide">...</div>` 片段，无 HTML 头尾 |
| Part 3 | 第二阶段幻灯片 | 只有 `<div class="slide">...</div>` 片段，可含 `<style>` 块 |
| Part 4 | 第三阶段+落地+结束幻灯片 | `<div class="slide">` 片段，以 `</div><!-- end #slide-container --></body></html>` 结尾 |

### Part 1 必须包含的 JS 功能
```javascript
// 键盘导航（← →箭头、空格键）
// 触摸滑动（移动端）
// 底部进度条
// MutationObserver 动态幻灯片计数（避免硬编码总数）
const observer = new MutationObserver(() => {
  totalSlides = document.querySelectorAll('.slide').length;
});
observer.observe(container, { childList: true });
```

### macOS 兼容组装脚本（⚠️ 关键）

**禁止**使用 `head -n -2`（macOS 的 `head` 不支持负数行数，会报错）：
```bash
# 正确做法：先计算行数，再用正数截断
lines=$(wc -l < /tmp/train_slide_part1.html)
head -n $((lines - 2)) /tmp/train_slide_part1.html > /tmp/train_final.html

# 追加其余部分
cat /tmp/train_slide_part2.html >> /tmp/train_final.html
cat /tmp/train_slide_part3.html >> /tmp/train_final.html
cat /tmp/train_slide_part4.html >> /tmp/train_final.html
```

### 验证
```bash
grep -c 'class="slide"' /tmp/train_final.html   # 核验幻灯片总数
wc -l /tmp/train_final.html                      # 核验总行数

# 复制到输出目录
cp /tmp/train_final.html "AI赋能[客户简称]_培训材料_v1.0.html"
```

---

## 视觉设计规范

推荐色系（可按客户品牌替换 CSS 变量）：
```css
:root {
  --primary: #1a3a6b;   /* 主色（深蓝） */
  --accent: #e8a020;    /* 强调色（金） */
  --success: #27ae60;
  --warning: #f39c12;
  --text-dark: #1a1a2e;
  --text-light: #ffffff;
}
```

**推荐幻灯片序列**：封面 → 目录 → 己方能力介绍（2-3张）→ 客户概况（1张）→ 各阶段痛点/方案（3-4张/阶段）→ 落地计划（2-3张）→ 结束致谢页

---

## 输出文件命名规范

```
AI赋能[客户简称]_[场景描述]_解决方案_v1.0.docx
AI赋能[客户简称]_[场景描述]_培训材料_v1.0.html
```

---

## 附加资源

- **`references/workflow-guide.md`** — 完整代码示例、质量检查清单、HTML 幻灯片组件规范
