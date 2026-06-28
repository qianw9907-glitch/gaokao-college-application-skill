# 高考志愿填报辅助 Skill

`gaokao-college-application` 是一个面向 Codex 的高考志愿填报辅助 skill，用于志愿梯度设计、风险审查、官方数据核验，以及招生目录 PDF/OCR 辅助提取。

> 重要提示：本 skill 的输出仅供参考，不构成最终填报依据。最终数据务必以各省教育考试院、官方志愿填报系统、阳光高考平台、各高校招生章程、《招生考试之友》《招生专业目录》等当年官方渠道和官方材料为准。

## 适合做什么

- 根据省份、批次、科类和志愿模式，先做规则分流。
- 用位次而不是分数，设计冲、稳、保梯度。
- 检查志愿表里的常见风险：组号错误、专业组混淆、专项/中外合作混入、调剂风险等。
- 在用户提供官方 PDF、截图或复制文本时，辅助核验院校代码、专业组代码、选科要求、专业清单、计划数、学费和办学地点。
- 从官方招生目录 PDF 中定向提取目标院校/专业组片段，并可生成固定字段的 CSV 核验表。

## 不适合做什么

- 不能保证录取结果。
- 不能替代省教育考试院、志愿填报系统或官方纸质/电子材料。
- 不内置任何版权招生书、官方 PDF、截图或爬取数据。
- OCR 和结构化抽取结果必须人工回看官方原文复核。

## 目录结构

```text
gaokao-college-application/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── common-pitfalls.md
│   ├── data-sources.md
│   ├── exhaustion-guide.md
│   ├── ocr-workflow.md
│   ├── pdf-sample-testing.md
│   ├── province-config.md
│   └── province-rules.md
└── scripts/
    └── extract_admission_pdf.py
```

## 安装

在 Codex 的 skill installer 中，从本仓库安装 `gaokao-college-application` 子目录：

```bash
scripts/install-skill-from-github.py \
  --repo qianw9907-glitch/gaokao-college-application-skill \
  --path gaokao-college-application
```

安装后重启 Codex，让新 skill 生效。

## 使用示例

直接调用 skill：

```text
Use $gaokao-college-application to review my Gaokao college application plan, identify risks, and list the official data I still need to verify.
```

中文提问也可以：

```text
用 $gaokao-college-application 帮我检查这份高考志愿表，重点看冲稳保梯度、专业组风险和哪些信息还需要官方核实。
```

## PDF/OCR 辅助提取

如果你有官方《招生考试之友》《招生专业目录》PDF，可以用内置脚本做定向提取：

```bash
python gaokao-college-application/scripts/extract_admission_pdf.py /path/to/招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --output /tmp/snippets.json
```

需要生成固定字段 CSV 核验表时：

```bash
python gaokao-college-application/scripts/extract_admission_pdf.py /path/to/招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --mode rows \
  --format csv \
  --output /tmp/rows.csv
```

如果 PDF 是扫描件且没有文字层，可按 `references/ocr-workflow.md` 安装 OCR 依赖后加上 `--ocr`。OCR 结果会被标记为需要人工复核。

## 官方数据优先级

建议按以下顺序核实：

1. 各省《招生考试之友》《招生专业目录》或官方志愿填报系统
2. 各省教育考试院官网
3. 各高校当年招生章程和本科招生网
4. 阳光高考平台
5. AI 或第三方查询结果，仅作线索，必须回到官方材料核实

## 许可证与数据说明

本仓库只包含 skill 指令、参考工作流和辅助脚本，不包含任何受版权保护的招生书、官方 PDF、截图或录取数据库。

如果你使用本 skill 辅助填报，请在最终提交前逐项核对官方材料，并自行承担最终填报决策责任。
