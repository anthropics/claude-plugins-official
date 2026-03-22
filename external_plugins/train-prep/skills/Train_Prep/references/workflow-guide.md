# Train_Prep 完整工作流指南

## 一、环境准备

### 目录结构
```
工作目录/
├── refs/              # 放置参考资料 PDF
├── output/            # 生成的 Word 报告和 HTML
└── /tmp/              # 中间产物（Markdown 章节文件）
```

### 依赖工具检查
```bash
which pdftotext    # poppler，用于 PDF 文本提取
which pandoc       # 用于 Markdown → Word 转换
```

安装（macOS）：
```bash
brew install poppler pandoc
```

---

## 二、第一阶段：研究调研（多 Agent 并行）

### PDF 资料提取
```bash
# 提取 PDF 文本为可检索的文本文件
pdftotext "参考资料1.pdf" /tmp/ref1.txt
pdftotext "参考资料2.pdf" /tmp/ref2.txt
```

**注意**：Read 工具的 PDF 渲染能力在某些 PDF 上不可靠，pdftotext 是更稳定的选择。

### 行业痛点研究（3 个并行 Agent）

每个 Agent 负责一个业务阶段，给定以下信息：
- 行业背景和客户信息
- AIEC/我方能力的文本内容（/tmp/ref*.txt）
- 该阶段的调研范围

**Agent 分工模板**：
```
Agent A（建设阶段）：
- 调研痛点：勘察设计、施工建造、竣工验收
- 输出：/tmp/train_construction.md

Agent B（运维阶段）：
- 调研痛点：设备维保、安全巡检、知识管理、能耗资产
- 输出：/tmp/train_maintenance.md

Agent C（运营阶段）：
- 调研痛点：客运服务、调度指挥、安全管理、行政支撑
- 输出：/tmp/train_operations.md（含落地建议计划）
```

**每个 Agent 的输出格式**：
```markdown
## 痛点 N：[名称]

**现状描述**：...

**AI 解决方案**：
- 方案组件1
- 方案组件2

**预期价值**：效率提升 X%，节省 Y 人力/年

**对应产品**：[平云智语/智能问数/智能体/无人机等]
```

---

## 三、第二阶段：Word 报告生成

### 章节组装
```bash
# 组装完整 Markdown 报告
cat /tmp/train_header.md \
    /tmp/train_construction.md \
    /tmp/train_maintenance.md \
    /tmp/train_operations.md \
    > /tmp/train_report.md
```

### 报告结构模板
```markdown
# [项目名称] AI 赋能解决方案

## 执行摘要
（3-5 段，覆盖：痛点概览、解决方案价值主张、投资回报、建议行动）

## 一、我方 AI 能力介绍
（简介 + 核心产品矩阵表格）

## 二、建设阶段 AI 赋能方案
（X 个痛点，每个包含：现状-方案-价值）

## 三、运维阶段 AI 赋能方案

## 四、运营阶段 AI 赋能方案

## 五、落地建议计划
（3 阶段路线图 + 责任分工 + ROI 预测表）
```

### Word 转换
```bash
pandoc /tmp/train_report.md \
    -o "output/AI赋能[客户]_解决方案_v1.0.docx" \
    --from markdown \
    --to docx
```

---

## 四、第三阶段：HTML 交互培训材料

### 多 Agent 并行架构（4 个 Agent）

**关键设计原则**：
- Agent A（框架层）：提供完整 HTML 头部、CSS 变量、JS 导航系统，最后一个 `</div>` 为 slide-container 打开标签（不关闭），**不写 `</body></html>`**
- Agent B/C/D（内容层）：只输出 `<div class="slide">...</div>` 片段，无 HTML 头尾
- 最终组装：拼接 4 个部分，使用 macOS 兼容语法

**Agent A 输出结构**：
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    /* CSS 变量和布局 */
    :root { --primary: #1a3a6b; ... }
    .slide { ... }
    /* 完整 CSS */
  </style>
</head>
<body>
  <div id="slide-container">
    <!-- Slide 1: 封面 -->
    <div class="slide active">...</div>
    <!-- Slide 2: 目录 -->
    <div class="slide">...</div>
    <!-- ... Slide 6 -->
    <!-- 注意：slide-container 故意不关闭，由 part4 关闭 -->

  <script>
    // 完整导航 JS（包含 MutationObserver 动态计数）
  </script>
  <!-- 注意：不写 </body></html> -->
```

**Agent D 输出结构（最后一部分）**：
```html
    <!-- 最后几张 Slide -->
    <div class="slide">...</div>
  </div><!-- end #slide-container -->
</body>
</html>
```

### macOS 兼容的组装脚本

**⚠️ 重要**：macOS 的 `head` 不支持 `head -n -N`（负数行数），需用以下方式：
```bash
# 去除 part1 末尾 2 行（</body></html>）
lines=$(wc -l < /tmp/train_slide_part1.html)
head -n $((lines - 2)) /tmp/train_slide_part1.html > /tmp/train_final.html

# 追加其他部分
cat /tmp/train_slide_part2.html >> /tmp/train_final.html
cat /tmp/train_slide_part3.html >> /tmp/train_final.html
cat /tmp/train_slide_part4.html >> /tmp/train_final.html

# 验证
grep -c 'class="slide"' /tmp/train_final.html
wc -l /tmp/train_final.html

# 复制到输出目录
cp /tmp/train_final.html "output/培训材料_v1.0.html"
```

### HTML 幻灯片设计规范

**视觉风格**：
```css
:root {
  --primary: #1a3a6b;      /* 深蓝主色 */
  --accent: #e8a020;       /* 金色强调 */
  --text-dark: #1a1a2e;
  --text-light: #ffffff;
  --success: #27ae60;
  --warning: #f39c12;
}
```

**导航 JS 核心功能**：
- 键盘：左右箭头键、空格键翻页
- 触摸：swipe 手势支持（移动端）
- 进度条：底部进度指示
- 动态计数：MutationObserver 监听 DOM，获取准确幻灯片总数（避免硬编码）

**推荐幻灯片布局类型**：
- `layout-split`：左右分栏（文字 + 图表）
- `layout-grid`：网格卡片
- `layout-timeline`：时间线/路线图
- `layout-comparison`：对比表格（Before/After）
- `layout-cover`：封面/章节页

**内容层级**（每张幻灯片）：
```html
<div class="slide">
  <div class="slide-header">
    <h2 class="slide-title">标题</h2>
    <span class="slide-subtitle">副标题</span>
  </div>
  <div class="slide-body">
    <!-- 内容区 -->
  </div>
  <div class="slide-footer">
    <span class="slide-number">X / TOTAL</span>
  </div>
</div>
```

---

## 五、质量检查清单

### Word 报告检查
- [ ] 执行摘要覆盖全部阶段和关键 ROI 数据
- [ ] 痛点数量准确（建设/运维/运营各阶段完整）
- [ ] 解决方案与我方实际产品能力匹配
- [ ] 落地计划包含阶段划分、责任矩阵、投资估算

### HTML 培训材料检查
- [ ] 幻灯片总数与实际内容匹配（grep 验证）
- [ ] 导航功能正常（键盘、触摸）
- [ ] 章节封面页标识清晰
- [ ] 视觉层次合理，重点突出
- [ ] 移动端响应式布局

---

## 六、文件命名规范

```
AI赋能[客户简称]_[业务场景]_解决方案_v1.0.docx
AI赋能[客户简称]_[业务场景]_培训材料_v1.0.html
```

示例：
```
AI赋能珠三角城际轨道_建设运维运营全场景解决方案_v1.0.docx
AI赋能珠三角城际轨道_培训材料_v1.0.html
```
