# ssc-cgl-prep-data

Static content backend for the **SSC CGL Prep** Android app, served free via GitHub Pages.

There is no server and no database. The app fetches versioned JSON over HTTPS, verifies it
against checksums in `index.json`, and caches it on device. After the first sync the app is
fully offline.

| | |
|---|---|
| **Live site** | https://ni18-in.github.io/ssc-cgl/ |
| **Repository** | https://github.com/ni18-in/ssc-cgl |
| **Manifest** | https://ni18-in.github.io/ssc-cgl/index.json |
| **CI** | [validate.yml](.github/workflows/validate.yml) — schema + manifest checks on every push |
| **Consumer** | [`../android-project`](../android-project/README.md) |

## Live content

Every file below is public and directly fetchable. `required` files are pulled during the
app's first-launch sync; the rest download lazily when the user opens that section.

| Path | Kind | Required | Live URL |
|---|---|:---:|---|
| [`index.json`](index.json) | manifest | — | [open](https://ni18-in.github.io/ssc-cgl/index.json) |
| [`syllabus/tier1.json`](syllabus/tier1.json) | syllabus | yes | [open](https://ni18-in.github.io/ssc-cgl/syllabus/tier1.json) |
| [`tier1/quant.json`](tier1/quant.json) | question_bank | yes | [open](https://ni18-in.github.io/ssc-cgl/tier1/quant.json) |
| [`tier1/reasoning.json`](tier1/reasoning.json) | question_bank | yes | [open](https://ni18-in.github.io/ssc-cgl/tier1/reasoning.json) |
| [`tier1/english.json`](tier1/english.json) | question_bank | yes | [open](https://ni18-in.github.io/ssc-cgl/tier1/english.json) |
| [`tier1/gk.json`](tier1/gk.json) | question_bank | yes | [open](https://ni18-in.github.io/ssc-cgl/tier1/gk.json) |
| [`formula_sheets/quant_formulas.json`](formula_sheets/quant_formulas.json) | formula_sheet | yes | [open](https://ni18-in.github.io/ssc-cgl/formula_sheets/quant_formulas.json) |
| [`current_affairs/latest.json`](current_affairs/latest.json) | current_affairs | yes | [open](https://ni18-in.github.io/ssc-cgl/current_affairs/latest.json) |
| [`current_affairs/2026_08.json`](current_affairs/2026_08.json) | current_affairs | no | [open](https://ni18-in.github.io/ssc-cgl/current_affairs/2026_08.json) |
| [`mocks/tier1/t1_mock_001.json`](mocks/tier1/t1_mock_001.json) | mock | no | *not yet published* |
| [`pyq/2024_tier1.json`](pyq/2024_tier1.json) | pyq | no | *not yet published* |

> **The PYQ set is a placeholder too.** `pyq/2024_tier1.json` reuses practice-bank questions
> so the interface can be exercised end to end. Replace it with questions transcribed from an
> official SSC paper and answer key, then clear `isDemo` and fill in the exam date and shift.

> **Current affairs are placeholders.** The entries in `2026_08.json` are structurally valid
> samples with `SAMPLE —` headlines, not real news. Replace them with curated, verified items
> before any release.

Measured transfer for the current seed set: **74 KB uncompressed → 21 KB over the wire**
(≈28%, GitHub Pages gzips automatically). At that ratio the projected 25–30 MB full content
set should cost roughly 8 MB of download.

## Layout

```
index.json                  Master manifest — version, file list, sizes, checksums
schemas/                    JSON Schema (draft 2020-12) for every content type
syllabus/                   Topic trees that drive the in-app syllabus tracker
tier1/                      Tier 1 question banks (one file per subject)
tier2/                      Tier 2 banks (paper1/ per subject, paper2, paper3)   [empty]
mocks/                      Full-length mock tests (tier1/ has one demo paper)
pyq/                        Previous year papers, one file per year+tier
current_affairs/            Monthly chunks + latest.json pointer
formula_sheets/             Formula / shortcut cards
descriptive/                Tier 3 essay topics, letter formats, precis examples [empty]
static/images/              WebP only, ≤50 KB each                               [empty]
scripts/                    Manifest builder and validator
```

Directories marked `[empty]` are part of the schema and manifest routing but have no content
yet — they fill in during Weeks 5–6.

## Schemas

All draft 2020-12, cross-referencing [`common.schema.json`](schemas/common.schema.json) for
shared definitions (`localizedText`, `difficulty`, `tier`, `subject`, `sha256`, `slug`).

| Schema | Governs |
|---|---|
| [`common.schema.json`](schemas/common.schema.json) | Shared `$defs` used by every other schema |
| [`manifest.schema.json`](schemas/manifest.schema.json) | `index.json` |
| [`question-bank.schema.json`](schemas/question-bank.schema.json) | `tier1/*.json`, `tier2/**/*.json` |
| [`syllabus.schema.json`](schemas/syllabus.schema.json) | `syllabus/*.json` |
| [`current-affairs.schema.json`](schemas/current-affairs.schema.json) | `current_affairs/*.json` |
| [`formula-sheet.schema.json`](schemas/formula-sheet.schema.json) | `formula_sheets/*.json` |
| [`mock.schema.json`](schemas/mock.schema.json) | `mocks/**/*.json` and `pyq/*.json` |

Previous year papers share `mock.schema.json`: a past paper is a mock that really happened,
plus provenance (`year`, `examDate`, `shift`, `source`). Publishing one under the `pyq` kind
additionally requires `year` and `source` — a paper without provenance is indistinguishable
from an invented one, which is precisely the trust a candidate places in it.

Descriptive content has no schema yet and is validated as well-formed JSON only.

## Content workflow

1. Edit or add a content file under `tier1/`, `mocks/`, `current_affairs/`, etc.
2. Rebuild the manifest — recomputes sizes and SHA-256 checksums and bumps the version:

   ```bash
   python scripts/build_manifest.py --bump --changelog "Added 150 Quant questions"
   ```

3. Validate against the schemas and cross-file rules:

   ```bash
   python scripts/validate.py
   ```

4. Commit and push. The app picks up the new `contentVersion` on next launch and downloads
   only the files whose checksum changed.

Install the one dependency once: `pip install jsonschema`.

### Script reference

**[`scripts/build_manifest.py`](scripts/build_manifest.py)**

| Flag | Effect |
|---|---|
| `--bump` | Advance `contentVersion` (`YYYY.MM.DD.N`) so installed apps see new content |
| `--changelog "..."` | Text shown in the app's update banner |
| `--min-app-version X.Y.Z` | Oldest app build that can parse this content |
| `--force-update` | Block content use until the sync finishes — reserve for corrections |
| `--check` | Exit non-zero if the committed manifest is stale; writes nothing. Used by CI |

**[`scripts/validate.py`](scripts/validate.py)** — takes no arguments. Beyond schema
validation it enforces what schemas cannot express:

- `correctIndex` within the bounds of `options`
- question IDs unique across *every* bank
- each question's `topic` declared in that subject's syllabus section
- no two options with identical English text
- every mock's `questionIds` resolving to a real question **of that section's subject**
- mock sectional timing agreeing with per-section durations, and section durations summing to
  the paper duration
- a Tier 1 mock claiming the real pattern actually having 100 questions in 60 minutes, or
  being flagged `isDemo`
- a previous year paper recording both its `year` and its `source`
- `latest.json` matching its archived month exactly
- files listed in the manifest actually present on disk

It also warns (without failing) when a question has Hindi text but untranslated options,
since the reader would see a mixed-language screen.

Exit codes: `0` clean, `1` errors found. Warnings alone do not fail the build.

## Conventions the app depends on

- **Question IDs are permanent.** User progress, bookmarks and notes are keyed by question
  `id` in on-device storage. Never reuse or renumber an ID — retire it instead. Changing an
  ID orphans a user's bookmark; reusing one silently reassigns it to different content.
- **`correctIndex` is 0-based** and must be a valid index into `options`.
- **Bilingual text** uses `{"en": "...", "hi": "..."}`. `en` is required, `hi` is optional —
  the app falls back to `en` when Hindi is missing, so partial translation is safe to ship.
- **Marks live on the bank**, not the question. `defaultMarks` / `defaultNegativeMarks` apply
  to every question in the file; a question overrides them only when it genuinely differs.
- **Topic slugs must match the syllabus.** The tracker attributes progress by slug, so a
  question tagged with an undeclared topic is invisible to it. `validate.py` rejects this.
- **Paths in `index.json` are repo-relative** and are appended to the Pages base URL as-is.
- **A new `kind` is safe to add.** Older apps map unrecognised kinds to `unknown` and skip
  them rather than failing the whole sync.

## Publishing

Served by GitHub Pages from `main`, configured under
**Settings → Pages → Deploy from a branch → main / (root)**.

The app has the base URL baked in as `AppConfig.contentBaseUrl`
([app_constants.dart](../android-project/lib/core/constants/app_constants.dart)).
Republishing needs no app change unless `minAppVersion` is raised.

## Reference

- [JSON Schema draft 2020-12](https://json-schema.org/draft/2020-12/release-notes) ·
  [python-jsonschema](https://python-jsonschema.readthedocs.io/)
- [SSC official site](https://ssc.gov.in/) — exam pattern, syllabus, previous papers
- [GitHub Pages docs](https://docs.github.com/en/pages)
