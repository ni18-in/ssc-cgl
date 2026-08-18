# SSC CGL Content Schemas Cheat Sheet

Quick reference for all 6 content types and schema definitions in the repository.

---

## 1. Common Types & Enums (`schemas/common.schema.json`)

### Bilingual Text (`localizedText`)
```json
{
  "en": "Mandatory English string",
  "hi": "Optional Hindi translation (falls back to en if missing)"
}
```

### Enums
- **`tier`**: `"tier1"` | `"tier2_paper1"` | `"tier2_paper2"` | `"tier2_paper3"` | `"tier3"`
- **`subject`**: `"quant"` | `"reasoning"` | `"english"` | `"gk"` | `"computer"` | `"statistics"` | `"finance_economics"`
- **`difficulty`**: `"easy"` | `"medium"` | `"hard"`
- **Question `tags`**:
  `"shortcut_applicable"`, `"frequently_asked"`, `"conceptual"`, `"calculation_heavy"`, `"trap"`, `"formula_based"`
- **Current Affairs `category`**:
  `"polity"`, `"economy"`, `"international"`, `"science_tech"`, `"environment"`, `"sports"`, `"awards"`, `"defence"`, `"schemes"`, `"appointments"`, `"obituary"`, `"art_culture"`
- **Current Affairs `examRelevance`**: `"high"` | `"medium"` | `"low"`
- **Formula Card `kind`**: `"formula"` | `"shortcut"` | `"identity"` | `"conversion"`

---

## 2. Question Bank Schema (`schemas/question-bank.schema.json`)

File location: `tier1/{subject}.json` or `tier2/{paper}/{subject}.json`

```json
{
  "schemaVersion": "1.0.0",
  "bankId": "t1_quant",
  "tier": "tier1",
  "subject": "quant",
  "title": { "en": "Quantitative Aptitude — Tier 1", "hi": "मात्रात्मक अभियोग्यता — टियर 1" },
  "defaultMarks": 2,
  "defaultNegativeMarks": 0.5,
  "questions": [
    {
      "id": "q_t1_quant_00201",
      "topic": "time_and_work",
      "subTopic": "pipes_and_cisterns",
      "question": {
        "en": "Pipe A can fill a cistern in 8 hours...",
        "hi": "नल A एक हौज को 8 घंटे में भर सकता है..."
      },
      "options": [
        { "en": "4.8 hours", "hi": "4.8 घंटे" },
        { "en": "5 hours", "hi": "5 घंटे" },
        { "en": "3.5 hours", "hi": "3.5 घंटे" },
        { "en": "6 hours", "hi": "6 घंटे" }
      ],
      "correctIndex": 0,
      "explanation": {
        "en": "LCM of 8 and 12 is 24 units. A's rate = 3, B's rate = 2. Combined = 5. Time = 24/5 = 4.8 hours.",
        "hi": "8 और 12 का ल.स. 24 इकाई है। A की दर = 3, B की दर = 2। कुल दर = 5। समय = 24/5 = 4.8 घंटे।"
      },
      "difficulty": "easy",
      "year": 2024,
      "imageUrl": null,
      "tags": ["shortcut_applicable", "frequently_asked"]
    }
  ]
}
```

---

## 3. Mock Test & PYQ Schema (`schemas/mock.schema.json`)

File location: `mocks/tier1/t1_mock_XXX.json` or `pyq/YYYY_tier1.json`

```json
{
  "schemaVersion": "1.0.0",
  "mockId": "t1_mock_004",
  "tier": "tier1",
  "title": { "en": "SSC CGL Tier 1 — Full Mock Test 4", "hi": "एसएससी सीजीएल टियर 1 — फुल मॉक टेस्ट 4" },
  "durationMinutes": 60,
  "sectionalTiming": false,
  "isDemo": false,
  "year": null,
  "examDate": null,
  "shift": null,
  "source": null,
  "instructions": {
    "en": "Official Tier 1 Pattern: 100 Questions...",
    "hi": "आधिकारिक टियर 1 पैटर्न: 100 प्रश्न..."
  },
  "sections": [
    {
      "subject": "reasoning",
      "title": { "en": "General Intelligence & Reasoning", "hi": "सामान्य बुद्धि एवं तर्कशक्ति" },
      "durationMinutes": null,
      "marksPerQuestion": 2,
      "negativeMarks": 0.5,
      "questionIds": ["q_t1_reasoning_00001", "...25 question IDs total..."]
    },
    {
      "subject": "gk",
      "title": { "en": "General Awareness", "hi": "सामान्य जागरूकता" },
      "durationMinutes": null,
      "marksPerQuestion": 2,
      "negativeMarks": 0.5,
      "questionIds": ["q_t1_gk_00001", "...25 question IDs total..."]
    },
    {
      "subject": "quant",
      "title": { "en": "Quantitative Aptitude", "hi": "मात्रात्मक अभियोग्यता" },
      "durationMinutes": null,
      "marksPerQuestion": 2,
      "negativeMarks": 0.5,
      "questionIds": ["q_t1_quant_00001", "...25 question IDs total..."]
    },
    {
      "subject": "english",
      "title": { "en": "English Comprehension", "hi": "अंग्रेजी समझ" },
      "durationMinutes": null,
      "marksPerQuestion": 2,
      "negativeMarks": 0.5,
      "questionIds": ["q_t1_english_00001", "...25 question IDs total..."]
    }
  ]
}
```

*Note for PYQ*: `year` (e.g. `2024`), `examDate` (`"2024-09-12"`), `shift` (`"Shift 1 (09:00 AM - 10:00 AM)"`), and `source` (`"SSC Official Question Paper..."`) are mandatory.

---

## 4. Formula Sheet Schema (`schemas/formula-sheet.schema.json`)

File location: `formula_sheets/{subject}_formulas.json`

```json
{
  "schemaVersion": "1.0.0",
  "sheetId": "quant_formulas",
  "subject": "quant",
  "title": { "en": "Quantitative Aptitude Formulas", "hi": "मात्रात्मक अभियोग्यता सूत्र" },
  "groups": [
    {
      "topic": "number_system",
      "title": { "en": "Number System", "hi": "संख्या पद्धति" },
      "cards": [
        {
          "id": "f_numsys_0001",
          "label": { "en": "Sum of first n natural numbers", "hi": "प्रथम n प्राकृतिक संख्याओं का योग" },
          "latex": "\\sum n = \\frac{n(n + 1)}{2}",
          "plain": "Sum = n(n + 1) / 2",
          "note": { "en": "Valid for positive integers starting from 1.", "hi": "1 से शुरू होने वाले धनात्मक पूर्णांकों के लिए वैध।" },
          "kind": "formula"
        }
      ]
    }
  ]
}
```

---

## 5. Current Affairs Schema (`schemas/current-affairs.schema.json`)

File location: `current_affairs/YYYY_MM.json` (and duplicate to `current_affairs/latest.json`)

```json
{
  "schemaVersion": "1.0.0",
  "month": "2026-08",
  "items": [
    {
      "id": "ca_2026_08_001",
      "date": "2026-08-01",
      "category": "schemes",
      "headline": {
        "en": "PM Surya Ghar: Muft Bijli Yojana installs 1.5 million rooftop solar systems",
        "hi": "पीएम सूर्य घर: मुफ्त बिजली योजना के तहत 15 लाख रूफटॉप सोलर सिस्टम स्थापित"
      },
      "summary": {
        "en": "The PM Surya Ghar Muft Bijli Yojana provides free electricity up to 300 units per month to 1 crore households.",
        "hi": "पीएम सूर्य घर मुफ्त बिजली योजना 1 करोड़ परिवारों को प्रति माह 300 यूनिट तक मुफ्त बिजली उपलब्ध कराती है।"
      },
      "examRelevance": "high",
      "source": "PIB India",
      "sourceUrl": null
    }
  ]
}
```
