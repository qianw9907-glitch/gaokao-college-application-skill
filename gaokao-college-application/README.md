# 高考志愿填报辅助 Skill

`gaokao-college-application` 是一个高考志愿填报辅助 skill，适用于 Claude Desktop / Claude Code。支持**规则分流**（院校专业组 / 专业+院校 / 传统志愿三种模式）、**多省份适配**、**特殊批次提醒**（强基/综评/专项/中外合作等），以及招生目录 PDF/OCR 定向提取核验。

> **重要提示：** 本 skill 的输出仅供参考，不构成最终填报依据。最终数据务必以各省教育考试院、官方志愿填报系统、阳光高考平台、各高校招生章程、《招生考试之友》《招生专业目录》等当年官方渠道和材料为准。

---

## 适合做什么

- 识别省份、批次、志愿模式，先做**规则分流**，再走对应流程（不同模式逻辑差异很大，不能混用）
- 用**位次而不是分数**设计冲、稳、保梯度（位次跨年可比，分数不可比）
- 检查志愿表常见风险：组号错误、跨年组号失效、专项/中外合作位次混入普通批、调剂退档风险等
- 提示特殊批次（强基/综合评价/提前批/国家专项/艺术体育）不走普通批模板，单独处理
- 在用户提供官方 PDF 时，辅助核验院校代码、专业组代码、选科要求、专业清单、计划数、学费和办学地点

## 不适合做什么

- 不能保证录取结果
- 不能替代省教育考试院、志愿填报系统或官方材料
- 不内置任何版权招生书、官方 PDF 或录取数据库
- OCR 和结构化抽取结果必须人工回看官方原文复核

---

## 目录结构

```
gaokao-college-application/
├── SKILL.md                        # 主入口：规则分流 + 7步主流程
├── agents/
│   └── openai.yaml                 # Agent 接口配置
├── references/
│   ├── common-pitfalls.md          # 8个常见坑（含真实案例）
│   ├── data-sources.md             # 数据来源优先级 + AI查询Prompt模板
│   ├── exhaustion-guide.md         # 院校穷举方法（物理类/历史类通用）
│   ├── ocr-workflow.md             # 官方PDF提取/OCR流程与输出规范
│   ├── pdf-sample-testing.md       # PDF样例测试协议
│   ├── province-config.md          # 省份志愿模式配置表 + 未知配置流程
│   └── province-rules.md           # 各省填报规则差异详解
└── scripts/
    └── extract_admission_pdf.py    # 定向提取招生目录PDF中的院校/组号片段
```

---

## 安装

### Claude Desktop / Cowork

将 `gaokao-college-application` 目录放入 Claude Desktop 的 skills 文件夹：

```bash
# macOS
cp -r gaokao-college-application ~/Library/Application\ Support/Claude/skills/

# Windows
xcopy gaokao-college-application %APPDATA%\Claude\skills\gaokao-college-application /E /I
```

重启 Claude Desktop，skill 自动加载。

### Claude Code

```bash
claude skill install https://github.com/qianw9907-glitch/gaokao-college-application-skill \
  --path gaokao-college-application
```

---

## 使用示例

直接在对话中调用：

```
用 $gaokao-college-application 帮我检查这份高考志愿表，
重点看冲稳保梯度、专业组风险和哪些信息还需要官方核实。
```

英文也可以：

```
Use $gaokao-college-application to review my Gaokao college application plan,
identify risks, and list the official data I still need to verify.
```

---

## PDF/OCR 辅助提取

如果有官方《招生考试之友》《招生专业目录》PDF，可用内置脚本定向提取：

**第一步：安装依赖（仅扫描件需要）**

```bash
# macOS
brew install poppler tesseract tesseract-lang

# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-chi-sim

# 验证安装
which pdftoppm && tesseract --version
```

**第二步：定位目标院校片段**

```bash
python gaokao-college-application/scripts/extract_admission_pdf.py /path/to/招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --context-chars 1000 \
  --output /tmp/snippets.json
```

**第三步：生成 CSV 核验表（可选）**

```bash
python gaokao-college-application/scripts/extract_admission_pdf.py /path/to/招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --mode rows \
  --format csv \
  --output /tmp/rows.csv
```

**扫描件加 `--ocr`：**

```bash
python gaokao-college-application/scripts/extract_admission_pdf.py /path/to/招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --ocr \
  --output /tmp/snippets.json
```

OCR 结果会标注 `confidence: ocr-review-required`，必须人工回看官方原文确认。

> **提示：** 不传 `--pages` 时脚本会全文扫描，速度较慢；建议先大致翻阅 PDF 确定目标院校所在页码范围再传入 `--pages`。

---

## 官方数据优先级

```
1️⃣ 各省《招生考试之友》/《招生专业目录》（最高权威）
2️⃣ 各省教育考试院官网投档数据
3️⃣ 各校官网当年招生章程
4️⃣ 阳光高考平台 gaokao.chsi.com.cn
5️⃣ AI 查询结果（仅作线索，必须回到官方材料核实）
```

---

## 许可证与数据说明

本仓库只包含 skill 指令、参考工作流和辅助脚本，不包含任何受版权保护的招生书、官方 PDF、截图或录取数据库。

使用本 skill 辅助填报，请在最终提交前逐项核对官方材料，并自行承担最终填报决策责任。
