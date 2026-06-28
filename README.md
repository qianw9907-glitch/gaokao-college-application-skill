# gaokao-college-application-skill

A Codex skill for Gaokao college application planning, risk review, official-data verification, and admission PDF/OCR extraction.

> For reference only. Always verify final data with official sources such as provincial education examination authorities, official application systems, the Sunshine Gaokao platform, university admission brochures, and official admission-plan materials.

## What It Does

- Splits workflows by province, batch, and application model.
- Designs and reviews reach/match/safety application gradients.
- Checks common risks such as wrong school/group codes, mixed admission categories, and unsafe adjustment choices.
- Helps verify official admission-plan PDFs or screenshots.
- Extracts target snippets and optional CSV review rows from official PDFs.

## Skill Folder

The skill lives in:

```text
gaokao-college-application/
```

Key files:

- `SKILL.md` - main workflow and trigger instructions
- `agents/openai.yaml` - UI metadata
- `references/` - official data, province rules, OCR workflow, pitfalls, testing protocol
- `scripts/extract_admission_pdf.py` - PDF text/OCR extraction helper

## Install

Install from this repository by pointing Codex to the skill folder path:

```bash
scripts/install-skill-from-github.py --repo qianw9907-glitch/gaokao-college-application-skill --path gaokao-college-application
```

Restart Codex after installing new skills.

## Notes

This repository does not include copyrighted admission books, official PDFs, screenshots, or scraped data. Use your own official materials for verification.
