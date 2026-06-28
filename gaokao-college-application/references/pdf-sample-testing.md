# 真实 PDF 样例测试协议

不要把《招生考试之友》《招生专业目录》等受版权保护的 PDF 打包进 skill。测试时只记录文件来源、页码范围、目标院校/组号、脚本命令和抽样核验结果。

---

## 测试目标

验证 `scripts/extract_admission_pdf.py` 在真实官方 PDF 上能否稳定完成三件事：

1. 定位目标院校或专业组片段。
2. 输出固定 schema 的 CSV 核验表。
3. 对 OCR、空字段、跨页表格标注 `needs_review=true` 或保留 `raw_text` 供人工复核。

---

## 最小测试集

每个年度至少覆盖：

| 类型 | 样例要求 | 验收重点 |
|------|----------|----------|
| 文字层 PDF | 官方目录 PDF 可复制文本 | 默认模式能输出 snippets，`confidence=embedded-text` |
| 扫描 PDF | 图片扫描或拍照转 PDF | `--ocr` 能运行；结果标注 `ocr-review-required` |
| 跨页表格 | 同一院校/组号专业清单跨页 | 扩大 `--pages` 和 `--context-chars` 后能取到上下文 |
| 院校专业组省份 | 如河南、江苏、广东等 | 能核验 group_code、subject_requirement、raw_text |
| 专业+院校省份 | 如山东、浙江等 | 不套专业组调剂；重点看专业代码、计划数、选科要求 |

---

## 测试记录模板

```text
测试日期：
省份/年份：
官方材料名称：
材料来源：
PDF 类型：文字层 / 扫描 / 混合
目标院校/专业组/专业：
页码范围：
命令：
输出文件：
抽样核验：
- 页码是否正确：
- 院校代码是否正确：
- 专业组/专业代码是否正确：
- 选科要求是否正确：
- 计划数是否正确：
- 学费/办学地点是否正确：
结论：通过 / 部分通过 / 不通过
问题：
后续修正：
```

---

## 推荐命令

先定位片段：

```bash
python scripts/extract_admission_pdf.py /path/to/招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --context-chars 1000 \
  --output /tmp/snippets.json
```

再生成固定 schema CSV：

```bash
python scripts/extract_admission_pdf.py /path/to/招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --mode rows \
  --line-context 3 \
  --format csv \
  --output /tmp/rows.csv
```

扫描件再加 `--ocr`，但 OCR 结果必须人工抽样核对。

---

## 验收标准

- 不允许脚本凭空补齐缺失字段。
- `raw_text` 必须保留，方便回看原文。
- 空字段可以接受，但必须由 agent 在最终回答中标为“待核实”。
- OCR 结果不能标为最终事实。
- 跨页表格不能只看命中的一页，必须扩大页码范围。
