#!/usr/bin/env python3
"""SSC CGL Content Authoring Helper CLI.

Utilities to inspect content inventory, generate next question IDs, validate draft questions,
append questions with automatic sequential IDs, sync current affairs, and run verification.

Usage:
    python .agents/skills/ssc-cgl-content/scripts/content_helper.py stats
    python .agents/skills/ssc-cgl-content/scripts/content_helper.py next-id quant
    python .agents/skills/ssc-cgl-content/scripts/content_helper.py validate-draft draft_questions.json
    python .agents/skills/ssc-cgl-content/scripts/content_helper.py append-questions tier1/quant.json draft_questions.json
    python .agents/skills/ssc-cgl-content/scripts/content_helper.py sync-latest-ca
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Ensure UTF-8 output encoding on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Find repo root (directory containing index.json and schemas/)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3] if (SCRIPT_DIR.parents[3] / "index.json").is_file() else Path.cwd()
if not (REPO_ROOT / "index.json").is_file():
    # Try traversing up
    cur = Path(__file__).resolve()
    while cur != cur.parent:
        if (cur / "index.json").is_file():
            REPO_ROOT = cur
            break
        cur = cur.parent

SYLLABUS_DIR = REPO_ROOT / "syllabus"
SCHEMAS_DIR = REPO_ROOT / "schemas"
TIER1_DIR = REPO_ROOT / "tier1"
MOCKS_DIR = REPO_ROOT / "mocks"
PYQ_DIR = REPO_ROOT / "pyq"
FORMULA_DIR = REPO_ROOT / "formula_sheets"
CA_DIR = REPO_ROOT / "current_affairs"

VALID_TAGS = {
    "shortcut_applicable",
    "frequently_asked",
    "conceptual",
    "calculation_heavy",
    "trap",
    "formula_based",
}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_SUBJECTS = {
    "quant",
    "reasoning",
    "english",
    "gk",
    "computer",
    "statistics",
    "finance_economics",
}


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json_lf(path: Path, data: dict | list) -> None:
    """Save formatted JSON with strict LF line endings."""
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(rendered, encoding="utf-8", newline="")


def get_syllabus_topics() -> dict[str, dict[str, dict]]:
    """Returns mapping: subject -> topic_slug -> {title, weightage, subtopics}."""
    result: dict[str, dict[str, dict]] = defaultdict(dict)
    if not SYLLABUS_DIR.is_dir():
        return result
    for p in SYLLABUS_DIR.glob("*.json"):
        data = load_json(p)
        if isinstance(data, dict):
            for sec in data.get("sections", []):
                subj = sec.get("subject")
                if not subj:
                    continue
                for t in sec.get("topics", []):
                    slug = t.get("slug")
                    if slug:
                        subs = [st.get("slug") for st in t.get("subTopics", []) if st.get("slug")]
                        result[subj][slug] = {
                            "title": t.get("title", {}).get("en", slug),
                            "weightage": t.get("weightage"),
                            "subTopics": subs,
                        }
    return result


def find_bank_file(target: str) -> Path | None:
    target_clean = target.lower().strip()
    # If path provided directly
    p = Path(target)
    if p.is_file():
        return p
    rp = REPO_ROOT / target
    if rp.is_file():
        return rp

    # If subject name provided
    for dirpath in [TIER1_DIR, REPO_ROOT / "tier2"]:
        if dirpath.is_dir():
            for f in dirpath.rglob("*.json"):
                if f.stem == target_clean or f.name == target_clean:
                    return f
                # Check bankId
                try:
                    data = load_json(f)
                    if isinstance(data, dict) and data.get("bankId") == target_clean:
                        return f
                    if isinstance(data, dict) and data.get("subject") == target_clean:
                        return f
                except Exception:
                    pass
    return None


def get_bank_info(bank_file: Path) -> dict:
    data = load_json(bank_file)
    bank_id = data.get("bankId", bank_file.stem)
    subject = data.get("subject", "")
    questions = data.get("questions", [])
    max_num = 0
    pattern = re.compile(rf"^q_{re.escape(bank_id)}_(\d+)$")

    for q in questions:
        qid = q.get("id", "")
        m = pattern.match(qid)
        if m:
            max_num = max(max_num, int(m.group(1)))
        else:
            # Try generic number extraction
            m2 = re.search(r"(\d+)$", qid)
            if m2:
                max_num = max(max_num, int(m2.group(1)))

    next_num = max_num + 1
    next_id = f"q_{bank_id}_{next_num:05d}"
    return {
        "bankId": bank_id,
        "subject": subject,
        "totalQuestions": len(questions),
        "maxIndex": max_num,
        "nextId": next_id,
        "questions": questions,
        "data": data,
    }


def cmd_stats(args: argparse.Namespace) -> int:
    print("=" * 65)
    print("         SSC CGL CONTENT INVENTORY & REPOSITORY STATS")
    print("=" * 65)

    syllabus_topics = get_syllabus_topics()
    total_q_all = 0

    print("\n--- QUESTION BANKS ---")
    for f in sorted(TIER1_DIR.glob("*.json")):
        info = get_bank_info(f)
        total_q_all += info["totalQuestions"]
        print(f"  • {f.relative_to(REPO_ROOT).as_posix():<24} | Subject: {info['subject']:<10} | Questions: {info['totalQuestions']:>4} | Next ID: {info['nextId']}")

    print("\n--- TOPIC COVERAGE BREAKDOWN ---")
    for f in sorted(TIER1_DIR.glob("*.json")):
        info = get_bank_info(f)
        subj = info["subject"]
        subj_topics = syllabus_topics.get(subj, {})
        counts: dict[str, int] = defaultdict(int)
        for q in info["questions"]:
            counts[q.get("topic", "UNKNOWN")] += 1

        print(f"\n  [{subj.upper()}] - {info['totalQuestions']} questions across {len(counts)}/{len(subj_topics)} syllabus topics:")
        for slug, tinfo in sorted(subj_topics.items()):
            cnt = counts.get(slug, 0)
            wt = tinfo.get("weightage", "-")
            status = "OK" if cnt > 0 else "MISSING"
            print(f"    - {slug:<26} ({tinfo['title']:<32}) : {cnt:>3} qns (Exam Weightage: {wt}) [{status}]")

    print("\n--- MOCKS & PREVIOUS YEAR PAPERS ---")
    mock_files = list(MOCKS_DIR.rglob("*.json")) if MOCKS_DIR.is_dir() else []
    pyq_files = list(PYQ_DIR.glob("*.json")) if PYQ_DIR.is_dir() else []
    print(f"  • Full Mock Tests: {len(mock_files)} papers")
    for mf in sorted(mock_files):
        mdata = load_json(mf)
        total_q = sum(len(s.get("questionIds", [])) for s in mdata.get("sections", []))
        print(f"    - {mf.relative_to(REPO_ROOT).as_posix()}: {mdata.get('title', {}).get('en', '')} ({total_q} qns)")

    print(f"  • Official PYQs:   {len(pyq_files)} papers")
    for pf in sorted(pyq_files):
        pdata = load_json(pf)
        print(f"    - {pf.relative_to(REPO_ROOT).as_posix()}: {pdata.get('year')} {pdata.get('shift', '')}")

    print("\n--- FORMULA SHEETS & CURRENT AFFAIRS ---")
    if FORMULA_DIR.is_dir():
        for ff in sorted(FORMULA_DIR.glob("*.json")):
            fdata = load_json(ff)
            cards_cnt = sum(len(g.get("cards", [])) for g in fdata.get("groups", []))
            print(f"  • Formula Sheet: {ff.relative_to(REPO_ROOT).as_posix()} ({len(fdata.get('groups', []))} groups, {cards_cnt} cards)")

    if CA_DIR.is_dir():
        ca_files = [f for f in CA_DIR.glob("*.json") if f.name != "latest.json"]
        latest_file = CA_DIR / "latest.json"
        is_synced = "NOT FOUND"
        if latest_file.is_file() and ca_files:
            latest_data = load_json(latest_file)
            newest_ca = sorted(ca_files)[-1]
            newest_data = load_json(newest_ca)
            is_synced = "IN SYNC" if latest_data == newest_data else "OUT OF SYNC"
        print(f"  • Current Affairs: {len(ca_files)} months archived, latest.json status: {is_synced}")

    print("\n" + "=" * 65)
    print(f"TOTAL QUESTIONS IN REPO: {total_q_all}")
    print("=" * 65)
    return 0


def cmd_next_id(args: argparse.Namespace) -> int:
    bank_file = find_bank_file(args.subject)
    if not bank_file:
        print(f"Error: Question bank not found for subject/identifier '{args.subject}'", file=sys.stderr)
        return 1
    info = get_bank_info(bank_file)
    print(info["nextId"])
    return 0


def validate_question_data(
    q: dict, index: int, subject: str, syllabus_topics: dict[str, dict[str, dict]]
) -> list[str]:
    errors = []
    qid = q.get("id", f"<item #{index}>")

    # Topic check
    topic = q.get("topic")
    known_topics = syllabus_topics.get(subject, {})
    if not topic:
        errors.append(f"{qid}: missing 'topic'")
    elif known_topics and topic not in known_topics:
        errors.append(f"{qid}: topic '{topic}' is not valid for subject '{subject}'")

    # Subtopic check
    sub_topic = q.get("subTopic")
    if sub_topic and topic in known_topics:
        valid_subs = known_topics[topic].get("subTopics", [])
        if valid_subs and sub_topic not in valid_subs:
            errors.append(f"{qid}: subTopic '{sub_topic}' not in valid subtopics {valid_subs} for topic '{topic}'")

    # Question bilingual check
    q_text = q.get("question")
    if not isinstance(q_text, dict) or not q_text.get("en"):
        errors.append(f"{qid}: question text must be an object with non-empty 'en'")

    # Options check
    options = q.get("options")
    if not isinstance(options, list) or not (2 <= len(options) <= 5):
        errors.append(f"{qid}: options must be a list of 2 to 5 items")
    else:
        en_opts = []
        for opt_idx, opt in enumerate(options):
            if not isinstance(opt, dict) or not opt.get("en"):
                errors.append(f"{qid}: option #{opt_idx} missing 'en' text")
            else:
                en_opts.append(opt["en"].strip().lower())
        if len(set(en_opts)) != len(en_opts):
            errors.append(f"{qid}: duplicate option text found in English")

    # correctIndex check
    correct = q.get("correctIndex")
    if not isinstance(correct, int):
        errors.append(f"{qid}: correctIndex must be an integer")
    elif isinstance(options, list) and not (0 <= correct < len(options)):
        errors.append(f"{qid}: correctIndex {correct} is out of range for {len(options)} options")

    # Explanation check
    expl = q.get("explanation")
    if not isinstance(expl, dict) or not expl.get("en"):
        errors.append(f"{qid}: explanation must be an object with non-empty 'en'")

    # Difficulty check
    diff = q.get("difficulty")
    if diff not in VALID_DIFFICULTIES:
        errors.append(f"{qid}: difficulty '{diff}' invalid. Allowed: {sorted(VALID_DIFFICULTIES)}")

    # Tags check
    tags = q.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            errors.append(f"{qid}: tags must be a list")
        else:
            invalid_tags = set(tags) - VALID_TAGS
            if invalid_tags:
                errors.append(f"{qid}: invalid tags {list(invalid_tags)}. Allowed: {sorted(VALID_TAGS)}")

    return errors


def cmd_validate_draft(args: argparse.Namespace) -> int:
    path = Path(args.draft_file)
    if not path.is_file():
        print(f"Error: Draft file '{args.draft_file}' not found.", file=sys.stderr)
        return 1

    try:
        raw_data = load_json(path)
    except Exception as exc:
        print(f"Error parsing draft JSON: {exc}", file=sys.stderr)
        return 1

    draft_questions = raw_data if isinstance(raw_data, list) else [raw_data]
    subject = args.subject
    if not subject:
        # Try inferring from first question or argument
        if isinstance(raw_data, dict) and raw_data.get("subject"):
            subject = raw_data["subject"]

    if not subject:
        print("Note: Subject not specified, checking across all syllabus subjects...")

    syllabus_topics = get_syllabus_topics()
    all_errors = []

    for i, q in enumerate(draft_questions):
        q_subj = subject
        if not q_subj:
            # find subject that matches the question's topic
            top = q.get("topic")
            for s, tops in syllabus_topics.items():
                if top in tops:
                    q_subj = s
                    break
        if not q_subj:
            q_subj = "quant"  # fallback

        errs = validate_question_data(q, i, q_subj, syllabus_topics)
        all_errors.extend(errs)

    if all_errors:
        print(f"Validation FAILED with {len(all_errors)} error(s):")
        for e in all_errors:
            print(f"  ❌ {e}")
        return 1

    print(f"✅ Draft validation PASSED cleanly for {len(draft_questions)} question(s).")
    return 0


def cmd_append_questions(args: argparse.Namespace) -> int:
    bank_file = find_bank_file(args.bank)
    if not bank_file:
        print(f"Error: Target question bank '{args.bank}' not found.", file=sys.stderr)
        return 1

    draft_path = Path(args.draft_file)
    if not draft_path.is_file():
        print(f"Error: Draft file '{args.draft_file}' not found.", file=sys.stderr)
        return 1

    draft_data = load_json(draft_path)
    new_questions = draft_data if isinstance(draft_data, list) else [draft_data]

    bank_info = get_bank_info(bank_file)
    subject = bank_info["subject"]
    bank_id = bank_info["bankId"]
    bank_data = bank_info["data"]
    syllabus_topics = get_syllabus_topics()

    # Validate first
    all_errors = []
    for i, q in enumerate(new_questions):
        errs = validate_question_data(q, i, subject, syllabus_topics)
        all_errors.extend(errs)

    if all_errors:
        print("Cannot append: draft questions have validation errors:")
        for e in all_errors:
            print(f"  ❌ {e}")
        return 1

    # Assign sequential IDs and format
    cur_idx = bank_info["maxIndex"]
    assigned_ids = []
    for q in new_questions:
        cur_idx += 1
        new_id = f"q_{bank_id}_{cur_idx:05d}"
        q["id"] = new_id
        assigned_ids.append(new_id)
        # Ensure default field placements
        if "subTopic" not in q:
            q["subTopic"] = None
        if "year" not in q:
            q["year"] = None
        if "imageUrl" not in q:
            q["imageUrl"] = None
        if "tags" not in q:
            q["tags"] = []

    bank_data["questions"].extend(new_questions)
    save_json_lf(bank_file, bank_data)

    print(f"✅ Successfully appended {len(new_questions)} question(s) to {bank_file.relative_to(REPO_ROOT).as_posix()}.")
    print(f"   Assigned ID range: {assigned_ids[0]} -> {assigned_ids[-1]}")
    print(f"   Bank new total: {len(bank_data['questions'])} questions.")
    print("\nNext step: Run manifest build & validate:")
    print(f"   python scripts/build_manifest.py --bump --changelog \"Added {len(new_questions)} {subject.title()} questions\"")
    print("   python scripts/validate.py")
    return 0


def cmd_sync_latest_ca(args: argparse.Namespace) -> int:
    if not CA_DIR.is_dir():
        print(f"Error: {CA_DIR} not found.", file=sys.stderr)
        return 1

    month_files = sorted([f for f in CA_DIR.glob("*.json") if f.name != "latest.json"])
    if not month_files:
        print("No monthly current affairs files found in current_affairs/.", file=sys.stderr)
        return 1

    newest = month_files[-1]
    latest_path = CA_DIR / "latest.json"
    latest_path.write_text(newest.read_text(encoding="utf-8"), encoding="utf-8", newline="")
    print(f"✅ Synchronized current_affairs/latest.json with newest month: {newest.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SSC CGL Content Authoring Helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # stats
    subparsers.add_parser("stats", help="Display content inventory and repository statistics")

    # next-id
    p_next = subparsers.add_parser("next-id", help="Get next available question ID for a bank")
    p_next.add_argument("subject", help="Subject name or bankId (e.g. quant, reasoning, english, gk)")

    # validate-draft
    p_val = subparsers.add_parser("validate-draft", help="Validate draft questions before inserting")
    p_val.add_argument("draft_file", help="Path to draft JSON file")
    p_val.add_argument("--subject", help="Subject name (optional, will auto-detect if omitted)")

    # append-questions
    p_app = subparsers.add_parser("append-questions", help="Append questions to bank with auto-generated IDs")
    p_app.add_argument("bank", help="Target bank file or subject (e.g. tier1/quant.json or quant)")
    p_app.add_argument("draft_file", help="Path to draft JSON questions file")

    # sync-latest-ca
    subparsers.add_parser("sync-latest-ca", help="Sync latest.json with the newest monthly current affairs file")

    args = parser.parse_args()

    if args.command == "stats":
        return cmd_stats(args)
    elif args.command == "next-id":
        return cmd_next_id(args)
    elif args.command == "validate-draft":
        return cmd_validate_draft(args)
    elif args.command == "append-questions":
        return cmd_append_questions(args)
    elif args.command == "sync-latest-ca":
        return cmd_sync_latest_ca(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
