---
name: ssc-cgl-content
description: >-
  Comprehensive guide and workflow runbook for authoring, expanding, and validating SSC CGL exam preparation content (Question Banks, Mock Tests, Previous Year Papers/PYQs, Formula Sheets, Current Affairs, and Syllabus Trees) adhering to project schemas, strict ID conventions, and manifest synchronization. Use whenever adding or editing SSC CGL questions, mocks, tests, formulas, current affairs, or syllabus data.
---

# SSC CGL Content Authoring Skill

This skill guides the agent and contributors through authoring, expanding, structuring, and verifying high-quality exam preparation content for the **SSC CGL Prep** application.

---

## Content Inventory & Schemas Reference

All content is organized into versioned JSON files governed by JSON Schema (draft 2020-12) under [`schemas/`](../../../schemas/).

| Content Type | Location | Schema File | Required on 1st Launch |
| :--- | :--- | :--- | :---: |
| **Syllabus Trees** | `syllabus/*.json` | [`schemas/syllabus.schema.json`](../../../schemas/syllabus.schema.json) | Yes |
| **Question Banks** | `tier1/*.json`, `tier2/**/*.json` | [`schemas/question-bank.schema.json`](../../../schemas/question-bank.schema.json) | Tier 1: Yes |
| **Formula Sheets** | `formula_sheets/*.json` | [`schemas/formula-sheet.schema.json`](../../../schemas/formula-sheet.schema.json) | Yes |
| **Current Affairs** | `current_affairs/*.json` | [`schemas/current-affairs.schema.json`](../../../schemas/current-affairs.schema.json) | `latest.json`: Yes |
| **Mock Tests** | `mocks/tier1/*.json` | [`schemas/mock.schema.json`](../../../schemas/mock.schema.json) | No (Lazy) |
| **PYQ Papers** | `pyq/*.json` | [`schemas/mock.schema.json`](../../../schemas/mock.schema.json) | No (Lazy) |
| **Master Manifest**| `index.json` | [`schemas/manifest.schema.json`](../../../schemas/manifest.schema.json) | Manifest |

> [!TIP]
> For quick access to valid topic slugs, see the [Syllabus Topics Reference](references/syllabus_topics.md).
> For schema details, see the [Schemas Cheat Sheet](references/schemas_cheat_sheet.md).

---

## Helper Tool: `content_helper.py`

Use the included helper tool to inspect inventory, get next available IDs, validate drafts, and append questions:

```bash
# View content stats, topic coverage, and next available IDs:
python .agents/skills/ssc-cgl-content/scripts/content_helper.py stats

# Get next sequential ID for a subject:
python .agents/skills/ssc-cgl-content/scripts/content_helper.py next-id quant

# Validate draft question(s) before appending:
python .agents/skills/ssc-cgl-content/scripts/content_helper.py validate-draft <draft_file.json>

# Safely append questions to a bank (auto-assigns sequential IDs + LF line endings):
python .agents/skills/ssc-cgl-content/scripts/content_helper.py append-questions tier1/quant.json <draft_file.json>

# Sync current_affairs/latest.json with latest monthly archive:
python .agents/skills/ssc-cgl-content/scripts/content_helper.py sync-latest-ca
```

---

## Authoring Workflows

### 1. Adding Questions to Question Banks (`tier1/*.json`)

1. **Check Topic & Weightage**:
   Consult [references/syllabus_topics.md](references/syllabus_topics.md) to choose the valid `topic` and optional `subTopic`.
2. **Draft the Question**:
   Follow the format in [examples/question_sample.json](examples/question_sample.json):
   - `id`: Format `q_<bankId>_XXXXX` (e.g. `q_t1_quant_00201`). Question IDs are permanent and must never be reused or renumbered.
   - `question`: Bilingual object `{"en": "...", "hi": "..."}`. (`en` mandatory, `hi` strongly recommended).
   - `options`: 2 to 5 bilingual objects. **Every option must have distinct English text.**
   - `correctIndex`: 0-based integer index into `options` (`0` to `len(options)-1`).
   - `explanation`: Bilingual object explaining the solution step-by-step, including shortcuts / key formulas where applicable.
   - `difficulty`: `"easy"`, `"medium"`, or `"hard"`.
   - `year`: Integer (e.g. `2024`) if from an official SSC exam, else `null`.
   - `tags`: Subset of `["shortcut_applicable", "frequently_asked", "conceptual", "calculation_heavy", "trap", "formula_based"]`.
3. **Append to Bank**:
   Use `content_helper.py append-questions <bank> <draft_file>` or edit the bank directly.

---

### 2. Creating Full Mock Tests (`mocks/tier1/`) & PYQs (`pyq/`)

1. **Tier 1 Mock Requirements**:
   - Total 100 questions (25 Reasoning, 25 GK, 25 Quant, 25 English).
   - `durationMinutes`: 60.
   - `sectionalTiming`: `false`.
   - `isDemo`: `false` for full mocks (or `true` if creating a demo/sample).
   - Each section lists `questionIds` referencing existing question IDs of that subject.
2. **Previous Year Paper (PYQ) Requirements**:
   - Stored under `pyq/YYYY_tier1.json`.
   - Must include provenance fields:
     - `year`: integer (e.g. `2024`).
     - `examDate`: `"YYYY-MM-DD"`.
     - `shift`: e.g. `"Shift 1 (09:00 AM - 10:00 AM)"`.
     - `source`: e.g. `"SSC Official Question Paper and Answer Key..."`.
3. Reference template: [examples/mock_sample.json](examples/mock_sample.json).

---

### 3. Adding Formula & Shortcut Cards (`formula_sheets/`)

1. Cards are grouped by syllabus topic under `formula_sheets/{subject}_formulas.json`.
2. Each card requires:
   - `id`: `f_<topic>_XXXX` (e.g. `f_algebra_0001`).
   - `label`: `{"en": "...", "hi": "..."}`.
   - `latex`: TeX equation without delimiters (`null` if prose-only).
   - `plain`: Plain-text expression for clipboard copy and search indexing.
   - `note`: `{"en": "...", "hi": "..."}` or `null`.
   - `kind`: `"formula"`, `"shortcut"`, `"identity"`, or `"conversion"`.
3. Reference template: [examples/formula_card_sample.json](examples/formula_card_sample.json).

---

### 4. Adding Current Affairs (`current_affairs/`)

1. Monthly files: `current_affairs/YYYY_MM.json` with items having:
   - `id`: `ca_YYYY_MM_XXX` (e.g. `ca_2026_09_001`).
   - `date`: `"YYYY-MM-DD"`.
   - `category`: `"polity"`, `"economy"`, `"international"`, `"science_tech"`, `"environment"`, `"sports"`, `"awards"`, `"defence"`, `"schemes"`, `"appointments"`, `"obituary"`, or `"art_culture"`.
   - `headline` & `summary`: Bilingual objects with in-house written summaries.
   - `examRelevance`: `"high"`, `"medium"`, or `"low"`.
   - `source`: Attribution string (e.g. `"PIB India"`, `"The Hindu"`).
2. **Keep `latest.json` in sync**: Run `python .agents/skills/ssc-cgl-content/scripts/content_helper.py sync-latest-ca`.
3. Reference template: [examples/current_affairs_sample.json](examples/current_affairs_sample.json).

---

## Verification & Publishing Checklist

After adding or editing any content:

1. **Rebuild Manifest**:
   ```bash
   python scripts/build_manifest.py --bump --changelog "Added X questions / updated Y content"
   ```
2. **Run Validation**:
   ```bash
   python scripts/validate.py
   ```
   Ensure:
   - 0 errors.
   - All question IDs are unique and resolve properly.
   - No duplicate options.
   - All topics exist in the syllabus tree.
   - All line endings are strictly LF (`\n`).

3. **Check Manifest Status**:
   ```bash
   python scripts/build_manifest.py --check
   ```
