#!/usr/bin/env python3
"""Validate every content file against its JSON Schema, plus cross-file rules.

    pip install jsonschema
    python scripts/validate.py

Schema validation alone cannot catch the mistakes that actually break the app —
a correctIndex pointing past the end of options, two questions sharing an id, or
a question tagged with a topic the syllabus tracker has never heard of. Those are
checked here.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ImportError:  # pragma: no cover - dependency hint
    sys.exit("Missing dependency. Run: pip install jsonschema")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas"

# Manifest 'kind' -> schema file.
SCHEMA_FOR_KIND = {
    "syllabus": "syllabus.schema.json",
    "question_bank": "question-bank.schema.json",
    "current_affairs": "current-affairs.schema.json",
    "formula_sheet": "formula-sheet.schema.json",
}

# Kinds that have no schema yet. They are still checked for valid JSON.
UNSCHEMAED_KINDS = {"mock", "pyq", "descriptive"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


def build_registry() -> Registry:
    """Register every local schema under its bare filename so that relative
    $refs like 'common.schema.json#/$defs/slug' resolve offline."""
    registry = Registry()
    for schema_path in SCHEMA_DIR.glob("*.schema.json"):
        contents = json.loads(schema_path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents, default_specification=DRAFT202012)
        registry = resource @ registry
        registry = registry.with_resource(schema_path.name, resource)
    return registry


def load_json(path: Path, report: Report) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(path.name, f"invalid JSON — {exc}")
        return None


def validate_against_schema(
    data: dict, schema_name: str, rel_path: str, registry: Registry, report: Report
) -> None:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, registry=registry)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        report.error(rel_path, f"{location} — {error.message}")


def collect_syllabus_topics(report: Report) -> dict[str, set[str]]:
    """Map subject -> set of topic slugs declared across all syllabus files."""
    topics: dict[str, set[str]] = defaultdict(set)
    syllabus_dir = REPO_ROOT / "syllabus"
    if not syllabus_dir.is_dir():
        return topics

    for path in sorted(syllabus_dir.glob("*.json")):
        data = load_json(path, report)
        if not data:
            continue
        for section in data.get("sections", []):
            subject = section.get("subject")
            for topic in section.get("topics", []):
                if subject and topic.get("slug"):
                    topics[subject].add(topic["slug"])
    return topics


def check_question_bank(
    data: dict, rel_path: str, syllabus_topics: dict[str, set[str]], seen_ids: dict[str, str], report: Report
) -> int:
    subject = data.get("subject")
    known_topics = syllabus_topics.get(subject, set())

    for index, question in enumerate(data.get("questions", [])):
        qid = question.get("id", f"<index {index}>")
        where = f"{rel_path} [{qid}]"

        options = question.get("options", [])
        correct = question.get("correctIndex")
        if isinstance(correct, int) and not (0 <= correct < len(options)):
            report.error(
                where,
                f"correctIndex {correct} is out of range for {len(options)} options",
            )

        if qid in seen_ids:
            report.error(where, f"duplicate question id, already used in {seen_ids[qid]}")
        else:
            seen_ids[qid] = rel_path

        topic = question.get("topic")
        if known_topics and topic and topic not in known_topics:
            report.error(
                where,
                f"topic '{topic}' is not declared in the {subject} syllabus — "
                "the tracker cannot attribute progress to it",
            )

        # Options that repeat make the question unanswerable even though the
        # schema is satisfied.
        english_options = [opt.get("en", "").strip().lower() for opt in options]
        if len(set(english_options)) != len(english_options):
            report.error(where, "two or more options have identical English text")

        # A question translated into Hindi should have its options translated
        # too, otherwise the Hindi reader sees a mixed-language screen.
        if question.get("question", {}).get("hi"):
            missing = [i for i, opt in enumerate(options) if not opt.get("hi")]
            if missing:
                report.warn(
                    where,
                    f"question has Hindi text but options {missing} do not — "
                    "the app will fall back to English for those",
                )

    return len(data.get("questions", []))


def main() -> int:
    report = Report()
    registry = build_registry()

    manifest_path = REPO_ROOT / "index.json"
    if not manifest_path.is_file():
        print("index.json not found. Run: python scripts/build_manifest.py --bump")
        return 1

    manifest = load_json(manifest_path, report)
    if manifest is None:
        print("\n".join(report.errors))
        return 1

    validate_against_schema(manifest, "manifest.schema.json", "index.json", registry, report)

    syllabus_topics = collect_syllabus_topics(report)
    seen_ids: dict[str, str] = {}
    question_total = 0
    files_checked = 0

    for entry in manifest.get("files", []):
        rel_path = entry["path"]
        path = REPO_ROOT / rel_path

        if not path.is_file():
            report.error(rel_path, "listed in index.json but missing on disk")
            continue

        data = load_json(path, report)
        if data is None:
            continue

        files_checked += 1
        kind = entry.get("kind")

        schema_name = SCHEMA_FOR_KIND.get(kind)
        if schema_name:
            validate_against_schema(data, schema_name, rel_path, registry, report)
        elif kind not in UNSCHEMAED_KINDS:
            report.warn(rel_path, f"unknown kind '{kind}' — parsed as JSON only")

        if kind == "question_bank":
            question_total += check_question_bank(
                data, rel_path, syllabus_topics, seen_ids, report
            )

    # latest.json must mirror an archived month, or the app's stable poll path
    # drifts away from the real content.
    latest_path = REPO_ROOT / "current_affairs" / "latest.json"
    if latest_path.is_file():
        latest = load_json(latest_path, report)
        if latest:
            month = latest.get("month", "")
            archived = REPO_ROOT / "current_affairs" / f"{month.replace('-', '_')}.json"
            if not archived.is_file():
                report.error(
                    "current_affairs/latest.json",
                    f"month '{month}' has no archived counterpart at {archived.name}",
                )
            elif json.loads(archived.read_text(encoding="utf-8")) != latest:
                report.error(
                    "current_affairs/latest.json",
                    f"content differs from {archived.name} — re-copy it",
                )

    for warning in report.warnings:
        print(f"WARN  {warning}")
    for error in report.errors:
        print(f"ERROR {error}")

    print(
        f"\n{files_checked} content files checked, {question_total} questions, "
        f"{len(report.errors)} errors, {len(report.warnings)} warnings."
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
