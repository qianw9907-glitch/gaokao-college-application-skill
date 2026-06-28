# 官方 PDF 提取与 OCR 工作流

本文件用于处理用户提供的《招生专业目录》《招生考试之友》或各省考试院 PDF。目标是把官方文件中的院校代码、专业组代码、选科要求、专业清单、计划数、学费、办学地点提取出来，供志愿核验使用。

脚本和 OCR 输出仅供核验辅助。最终数据必须以各省教育考试院、官方志愿填报系统、阳光高考平台、各高校招生章程、《招生考试之友》《招生专业目录》等当年官方渠道和官方材料为准。

---

## 使用原则

1. 先提取文本，后做 OCR。很多官方 PDF 自带文字层，直接提取比 OCR 更准。
2. 只对候选院校或关键页定向提取，不默认全量 OCR 整本目录。
3. OCR 结果必须标注“需复核”，不能直接当最终事实。
4. 最终填报前，关键志愿仍要回看 PDF 原页或官方网页。
5. 用真实 PDF 验证脚本时，按 `references/pdf-sample-testing.md` 记录测试，不把版权 PDF 打包进 skill。

---

## 没有官方 PDF 怎么办

不要要求用户必须先提供 OCR 文件。若用户没有《招生专业目录》《招生考试之友》PDF，先进入轻量策略或志愿表核验模式，把以下字段标为“待官方文件确认”：

- 院校代码
- 专业组代码或专业代码
- 选科要求
- 招生类别
- 组内专业或专业名称
- 招生计划人数
- 学费
- 办学地点

提醒用户优先从官方入口获取当年材料：

| 来源 | 用途 | 入口 |
|------|------|------|
| 教育部阳光高考平台 | 查高校招生章程、院校信息、省市动态 | https://gaokao.chsi.com.cn/ |
| 阳光高考省市动态 | 查各省考试院发布的政策、志愿填报通知 | https://gaokao.chsi.com.cn/gkxx/ss/ |
| 各省教育考试院官网 | 查当年招生计划、志愿填报公告、投档录取数据 | 以本省官网为准 |
| 各高校本科招生网 | 查招生章程、专业分配规则、办学地点、特殊要求 | 搜索“学校名 本科招生网 招生章程” |
| 纸质《招生考试之友》/《招生专业目录》 | 最终核对院校代码、组号、专业、计划数 | 可拍照、截图或复制原文给 Codex 定向核验 |

常见省级入口示例：

| 省份 | 官方入口 |
|------|----------|
| 河南 | 河南省教育考试院 https://www.haeea.cn/ ；河南招生考试信息网 https://www.heao.com.cn/ |
| 山东 | 山东省教育招生考试院 https://www.sdzk.cn/ |
| 江苏 | 江苏省教育考试院 https://www.jseea.cn/ |
| 浙江 | 浙江省教育考试院 https://www.zjzs.net/ |
| 广东 | 广东省教育考试院 https://eea.gd.gov.cn/ |

检索关键词建议：

```text
[省份] 2026 普通高校招生 专业目录 PDF
[省份] 2026 招生计划 普通本科批 专业目录
[省份] 教育考试院 招生专业目录
[学校名] 2026 本科招生章程 专业分配规则
```

如果找不到 PDF，不要停下等待。先做候选方案和核验清单，并明确说明：没有官方目录时，专业组构成和代码只能作为待核实信息，不能作为最终填报依据。

---

## 依赖准备

脚本优先使用 Python PDF 文本提取库；只有 PDF 没有文字层且传入 `--ocr` 时，才需要 OCR 命令行工具。

macOS 推荐安装：

```bash
brew install poppler tesseract tesseract-lang
```

Ubuntu/Debian 推荐安装：

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-chi-sim
```

检查依赖：

```bash
which pdftoppm
which tesseract
tesseract --list-langs | rg 'chi_sim|eng'
```

如果不能安装依赖，不要编造 OCR 结果。改用 PDF 文字层、用户提供的截图/复制文本，或要求用户提供更清晰的官方文件。

---

## 推荐流程

### 轻量核验

适合用户已有候选志愿表，但还没上传官方 PDF。

- 列出每个志愿需要核实的字段。
- 生成给外部查询工具或官网检索用的精确 prompt。
- 标注哪些志愿必须等官方 PDF 才能确认。

### 定向提取

适合用户提供官方 PDF，且已经有候选院校/专业组。

运行脚本：

```bash
python scripts/extract_admission_pdf.py 招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --output snippets.json
```

不传 `--pages` 时，脚本会扫描整个 PDF。整本《招生专业目录》通常很大，首次检索建议传 `--pages` 限定页码；只有不知道页码范围、且目标数量很少时，才全文扫描。

默认输出是片段模式，适合先定位官方原文。需要固定表格 schema 时，使用结构化行模式：

```bash
python scripts/extract_admission_pdf.py 招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --mode rows \
  --format csv \
  --output rows.csv
```

结构化行模式会输出固定字段：`page,target,confidence,school_name,school_code,group_code,subject_requirement,admission_type,major_name,plan_count,tuition,campus,raw_text,needs_review`。这些字段是核验表，不是最终数据库；空字段和 `needs_review=true` 必须回看 PDF 原文。

如果脚本提示没有文字层，再尝试 OCR：

```bash
python scripts/extract_admission_pdf.py 招生目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --ocr \
  --output snippets.json
```

OCR 依赖本机已有 `pdftoppm` 和 `tesseract`。如果缺少依赖，不要编造结果，说明需要安装依赖或改用用户提供的截图/文字。

### 端到端示例

用户上传河南《招生专业目录》PDF，并要求核实南京航空航天大学 104 组：

```bash
cd /Users/wangqian/.codex/skills/gaokao-college-application

python scripts/extract_admission_pdf.py /path/to/招生专业目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --context-chars 800 \
  --output /tmp/nanhang-104-snippets.json
```

生成固定 schema 的 CSV 核验表：

```bash
python scripts/extract_admission_pdf.py /path/to/招生专业目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 120-135 \
  --mode rows \
  --line-context 3 \
  --format csv \
  --output /tmp/nanhang-104-rows.csv
```

如果输出为空，先扩大页码范围；如果片段被截断，再扩大上下文：

```bash
python scripts/extract_admission_pdf.py /path/to/招生专业目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 115-145 \
  --context-chars 1400 \
  --output /tmp/nanhang-104-snippets.json
```

若 PDF 是扫描件且无文字层：

```bash
python scripts/extract_admission_pdf.py /path/to/招生专业目录.pdf \
  --target 南京航空航天大学 \
  --target 104 \
  --pages 115-145 \
  --ocr \
  --output /tmp/nanhang-104-snippets.json
```

拿到片段后，整理为“院校代码、专业组代码、选科要求、招生类别、组内专业、计划数、学费、办学地点、页码、置信度”表格。置信度为 `ocr-review-required` 的字段必须回看 PDF 原页。

### 结构化核验

从提取片段中整理为表格：

| 字段 | 说明 |
|------|------|
| 院校名称 | 必须与官方目录一致 |
| 院校代码 | 填报系统使用的代码 |
| 专业组代码 | 院校专业组模式必填 |
| 选科要求 | 首选科目和再选科目 |
| 招生类别 | 普通/中外合作/专项/联合培养等 |
| 专业名称 | 组内全部专业逐一列出 |
| 计划人数 | 人数极少时标注波动风险 |
| 学费 | 高收费专业要单独提醒 |
| 办学地点 | 本部/分校区/异地校区 |
| 页码 | 回溯官方原文用 |
| 置信度 | embedded-text / ocr-review-required |
| raw_text | 脚本提取的原始行或片段 |
| needs_review | true 表示必须人工回看原文 |

---

## 输出要求

给用户输出时分三层：

1. **已核实**：来自官方 PDF 文字层，字段完整。
2. **需人工复核**：来自 OCR 或字段不完整。
3. **未找到**：目标院校/组号在给定页面范围内未检出。

不要只给结论，要附上页码和关键片段，方便用户回到官方文件确认。

---

## 常见失败处理

- **学校名搜不到**：尝试官方全称、简称、院校代码、拼音首字母不可靠时不用。
- **组号搜到多个**：必须结合院校名称、科目类别、招生类别判断，不能只看组号。
- **表格跨页**：扩大 `--pages` 范围，并把上一页末尾和下一页开头一起看；若同一组的专业清单被截断，增加 `--context-chars` 到 1000-2000 后重跑。
- **OCR 乱码**：降低结论强度，要求用户提供更清晰 PDF、截图或原文复制。
- **扫描件页码错位**：以 PDF 实际页码和官方印刷页码同时标注。
