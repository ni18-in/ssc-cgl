# ssc-cgl-prep-data

Static content backend for the **SSC CGL Prep** Android app, served free via GitHub Pages.

There is no server and no database. The app fetches versioned JSON over HTTPS, verifies it
against checksums in `index.json`, and caches it on device. After the first sync the app is
fully offline.

## Layout

```
index.json                  Master manifest — version, file list, sizes, checksums
schemas/                    JSON Schema (draft 2020-12) for every content type
syllabus/                   Topic trees that drive the in-app syllabus tracker
tier1/                      Tier 1 question banks (one file per subject)
tier2/                      Tier 2 question banks (paper1/ per subject, paper2, paper3)
mocks/                      Full-length mock tests (exact exam pattern)
pyq/                        Previous year papers, one file per year+tier
current_affairs/            Monthly chunks + latest.json pointer
formula_sheets/             Formula / shortcut cards
descriptive/                Tier 3 essay topics, letter formats, precis examples
static/images/              WebP only, ≤50 KB each
```

## Publishing

The `main` branch is served by GitHub Pages at:

```
https://<user>.github.io/ssc-cgl-prep-data/
```

Enable it under **Settings → Pages → Deploy from a branch → main / (root)**.

GitHub Pages serves gzip automatically, so JSON is committed minified-friendly but stays
human-readable in git. Uncompressed content targets ~25–30 MB; over the wire it's ~8 MB.

## Content workflow

1. Edit or add a content file under `tier1/`, `mocks/`, `current_affairs/`, etc.
2. Run the manifest builder — it recomputes sizes and SHA-256 checksums and bumps the version:

   ```bash
   python scripts/build_manifest.py --bump
   ```

3. Validate everything against the schemas before committing:

   ```bash
   python scripts/validate.py
   ```

4. Commit and push. The app picks up the new `contentVersion` on next launch and downloads
   only the files whose checksum changed.

CI runs `validate.py` and verifies the manifest is in sync on every push and pull request,
so a malformed question file cannot reach the app.

## Conventions that the app depends on

- **Question IDs are permanent.** User progress, bookmarks and notes are keyed by question
  `id` in on-device storage. Never reuse or renumber an ID — retire it instead. Changing an
  ID orphans a user's bookmark; reusing one silently reassigns it to different content.
- **`correctIndex` is 0-based** and must be a valid index into `options`.
- **Bilingual text** uses `{"en": "...", "hi": "..."}`. `en` is required, `hi` is optional —
  the app falls back to `en` when Hindi is missing, so partial translation is safe to ship.
- **Marks live on the bank**, not the question. `defaultMarks` / `defaultNegativeMarks` apply
  to every question in the file; a question may override them only when it genuinely differs.
- **Paths in `index.json` are repo-relative** and are appended to the Pages base URL as-is.

See `schemas/` for the authoritative field-by-field contract.
