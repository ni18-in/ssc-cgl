# SSC CGL Prep Data — Quality, Scope & Authoring Rules

These rules are permanently active across this repository. Every content generation, expansion, or edit must strictly comply with these guidelines.

---

## 1. Scope & Syllabus Boundaries
- **Strictly SSC CGL Pattern**: Never generate or add content outside the official SSC CGL syllabus defined in `syllabus/tier1.json`.
- **No Out-of-Scope Topics**: Do not import conventions from other competitive exams:
  - No Banking-specific floor/circular seating puzzles with complex multi-variable parameters.
  - No UPSC-specific analytical essay questions or non-objective material for Tier 1.
  - No JEE/Engineering mathematics (e.g., differential calculus, complex numbers).
- **Topic Slug Invariant**: Every question's `topic` and `subTopic` must strictly match the declared slugs in [`references/syllabus_topics.md`](.agents/skills/ssc-cgl-content/references/syllabus_topics.md).

---

## 2. Anti-Duplication & Variety
- **Pre-check Existing Content**: Before drafting questions for any topic, review the existing questions in that topic to avoid repetitive concepts, identical numerical values, or identical question templates.
- **Concept & Subtopic Diversity**:
  - Vary numerical values, ratios, geometries, and question patterns.
  - Distribute questions across multiple subtopics rather than clumping them into a single sub-category.
  - In English: Avoid repeating the same root words, idioms, or grammatical traps.
- **Option Uniqueness**: No two options in a single question may have identical English text.

---

## 3. Bilingual Quality & Explanations
- **SSC Hindi Standard**: Hindi translations must use standard SSC CGL terminology:
  - Quant: ल.स. (LCM), म.स. (HCF), क्रय मूल्य (Cost Price), विक्रय मूल्य (Selling Price), कार्यक्षमता (Efficiency).
  - Reasoning: कूटलेखन (Coding), सादृश्यता (Analogy), निष्कर्ष (Conclusion).
  - GK/Polity: अनुच्छेद (Article), संशोधन (Amendment), मूल अधिकार (Fundamental Rights).
- **Comprehensive Explanations**:
  - Explanations must be step-by-step and clear for self-study.
  - For Quant and Reasoning questions, provide shortcut formulas and mental math tricks alongside the standard method.
  - Tag questions accurately with `"shortcut_applicable"`, `"frequently_asked"`, `"conceptual"`, `"calculation_heavy"`, `"trap"`, or `"formula_based"`.
- **Unambiguous Answer Keys**: Ensure `correctIndex` points to the unequivocally correct option with 3 plausible, high-quality distractors.

---

## 4. Technical Invariants
- **Line Endings**: All files in the repository must strictly use LF (`\n`) line endings, never CRLF (`\r\n`).
- **Permanent Question IDs**: IDs follow the pattern `q_<bankId>_XXXXX` (e.g. `q_t1_quant_00201`). Never reuse, delete, or renumber existing IDs.
- **Manifest & Validation**: After any content change:
  1. `python scripts/build_manifest.py --bump --changelog "..."`
  2. `python scripts/validate.py` (must pass with 0 errors).
