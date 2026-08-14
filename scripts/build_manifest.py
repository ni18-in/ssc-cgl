#!/usr/bin/env python3
"""Regenerate index.json from the content files on disk.

Walks the content directories, records size and SHA-256 for every JSON file, and
writes the manifest the app polls on launch. Run this after any content edit:

    python scripts/build_manifest.py --bump

Without --bump the contentVersion is left alone, which is useful for checking in
CI that the committed manifest matches the committed content.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "index.json"

SCHEMA_VERSION = "1.0.0"
DEFAULT_MIN_APP_VERSION = "1.0.0"

# Directories that hold shippable content, in the order they appear in the manifest.
CONTENT_DIRS = (
    "syllabus",
    "tier1",
    "tier2",
    "mocks",
    "pyq",
    "current_affairs",
    "formula_sheets",
    "descriptive",
)

VERSION_RE = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})\.(\d+)$")


def classify(rel_path: str) -> tuple[str, bool]:
    """Map a repo-relative path to its (kind, required) pair.

    'required' files are fetched during the first-launch sync. Everything else
    downloads lazily the first time the user opens that section, which keeps the
    initial sync small.
    """
    top = rel_path.split("/", 1)[0]

    if top == "syllabus":
        return "syllabus", True
    if top == "tier1":
        return "question_bank", True
    if top == "tier2":
        return "question_bank", False
    if top == "mocks":
        return "mock", False
    if top == "pyq":
        return "pyq", False
    if top == "current_affairs":
        # Only the stable 'latest' pointer is part of the first sync; archived
        # months are pulled on demand from the current affairs browser.
        return "current_affairs", rel_path == "current_affairs/latest.json"
    if top == "formula_sheets":
        return "formula_sheet", True
    if top == "descriptive":
        return "descriptive", False

    raise ValueError(f"No manifest 'kind' mapping for path: {rel_path}")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover() -> list[Path]:
    found: list[Path] = []
    for directory in CONTENT_DIRS:
        base = REPO_ROOT / directory
        if base.is_dir():
            found.extend(sorted(base.rglob("*.json")))
    return found


def load_previous() -> dict[str, dict]:
    """Return the previous manifest's entries keyed by path, if any."""
    if not MANIFEST_PATH.is_file():
        return {}
    try:
        previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {entry["path"]: entry for entry in previous.get("files", [])}


def next_version(previous_version: str | None, today: dt.date, bump: bool) -> str:
    today_prefix = today.strftime("%Y.%m.%d")

    if not bump:
        return previous_version or f"{today_prefix}.1"

    if previous_version:
        match = VERSION_RE.match(previous_version)
        if match and f"{match.group(1)}.{match.group(2)}.{match.group(3)}" == today_prefix:
            return f"{today_prefix}.{int(match.group(4)) + 1}"

    return f"{today_prefix}.1"


def build(bump: bool, changelog: str, min_app_version: str, force_update: bool) -> dict:
    previous_entries = load_previous()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    now_iso = now.isoformat().replace("+00:00", "Z")

    files: list[dict] = []
    total = 0

    for path in discover():
        rel = path.relative_to(REPO_ROOT).as_posix()
        kind, required = classify(rel)
        checksum = sha256_of(path)
        size = path.stat().st_size
        total += size

        # lastModified means "when this content last changed", so it is carried
        # forward untouched while the checksum is stable. Filesystem mtimes are
        # not usable here — a fresh git clone rewrites them all to clone time.
        prior = previous_entries.get(rel)
        if prior and prior.get("checksum") == checksum:
            last_modified = prior.get("lastModified", now_iso)
        else:
            last_modified = now_iso

        files.append(
            {
                "path": rel,
                "kind": kind,
                "sizeBytes": size,
                "checksum": checksum,
                "lastModified": last_modified,
                "required": required,
            }
        )

    if not files:
        raise SystemExit("No content files found — nothing to write.")

    previous_version = None
    if MANIFEST_PATH.is_file():
        try:
            previous_version = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get(
                "contentVersion"
            )
        except json.JSONDecodeError:
            previous_version = None

    return {
        "schemaVersion": SCHEMA_VERSION,
        "lastUpdated": now_iso,
        "contentVersion": next_version(previous_version, now.date(), bump),
        "minAppVersion": min_app_version,
        "files": files,
        "totalSizeBytes": total,
        "forceUpdate": force_update,
        "changelog": changelog,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bump",
        action="store_true",
        help="Advance contentVersion so installed apps see new content.",
    )
    parser.add_argument(
        "--changelog",
        default="Content update.",
        help="Short note shown in the app's update banner.",
    )
    parser.add_argument(
        "--min-app-version",
        default=DEFAULT_MIN_APP_VERSION,
        help="Oldest app build that can parse this content.",
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Block content use until the sync finishes. Reserve for corrections.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed manifest is stale, without writing.",
    )
    args = parser.parse_args()

    manifest = build(
        bump=args.bump and not args.check,
        changelog=args.changelog,
        min_app_version=args.min_app_version,
        force_update=args.force_update,
    )
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not MANIFEST_PATH.is_file():
            print("index.json is missing. Run: python scripts/build_manifest.py --bump")
            return 1

        committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        fresh_index = {entry["path"]: entry["checksum"] for entry in manifest["files"]}
        committed_index = {entry["path"]: entry["checksum"] for entry in committed.get("files", [])}

        if fresh_index != committed_index:
            added = sorted(set(fresh_index) - set(committed_index))
            removed = sorted(set(committed_index) - set(fresh_index))
            changed = sorted(
                path
                for path in set(fresh_index) & set(committed_index)
                if fresh_index[path] != committed_index[path]
            )
            print("index.json is out of sync with the content on disk.")
            for label, paths in (("added", added), ("removed", removed), ("changed", changed)):
                for path in paths:
                    print(f"  {label}: {path}")
            print("\nRun: python scripts/build_manifest.py --bump")
            return 1

        print(f"index.json is in sync ({len(fresh_index)} files).")
        return 0

    # newline="" stops Python's text mode translating "\n" to "\r\n" on Windows.
    # Everything this repo publishes must be LF on disk, because the app verifies
    # downloads against checksums of the LF blob GitHub Pages serves.
    MANIFEST_PATH.write_text(rendered, encoding="utf-8", newline="")
    size_mb = manifest["totalSizeBytes"] / (1024 * 1024)
    required_count = sum(1 for entry in manifest["files"] if entry["required"])
    print(
        f"Wrote index.json — {len(manifest['files'])} files "
        f"({required_count} required for first sync), "
        f"{size_mb:.2f} MB uncompressed, version {manifest['contentVersion']}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
