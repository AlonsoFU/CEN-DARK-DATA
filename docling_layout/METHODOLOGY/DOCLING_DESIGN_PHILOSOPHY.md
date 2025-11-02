# Docling Design Philosophy: Understanding What You Get vs What You Build

**Last Updated**: 2025-10-26
**Purpose**: Clarify Docling's capabilities and YOUR responsibilities

---

## 🎯 Core Understanding

### **Docling's Philosophy:**

> **"I give you the building blocks (layout, elements, reading order). YOU define what 'belongs together' means for YOUR documents."**

Docling is designed to provide **universal layout extraction**, not **domain-specific semantic understanding**.

---

## What Docling DOES Provide

### ✅ 1. Layout Detection (Physical Structure)

**What it does:**
- Detects WHERE elements are on the page (bounding boxes)
- Identifies element types: text, section_header, table, picture, etc.
- Determines reading order (what comes after what)
- Builds tree structure based on VISUAL NESTING

**Example:**
```
Page Layout:
┌─────────────────────────────┐
│ [Title]                     │
│   [Text paragraph]          │
│   [Text paragraph]          │
│ [Section Header]            │
│   [Table]                   │
└─────────────────────────────┘

Docling detects:
- Title at position (50, 100)
- 2 text blocks visually indented
- Section header at (50, 200)
- Table at (50, 250)
```

**Output:**
```json
{
  "body": {
    "children": [
      {"$ref": "#/texts/0"},  // Title
      {"$ref": "#/texts/1"},  // Paragraph 1
      {"$ref": "#/texts/2"},  // Paragraph 2
      {"$ref": "#/texts/3"},  // Section header
      {"$ref": "#/tables/0"}  // Table
    ]
  }
}
```

### ✅ 2. Element Classification (What Type)

**What it does:**
- Uses Granite-258M AI model to classify elements
- 11 types: text, section_header, title, list_item, table, picture, caption, formula, footnote, page_header, page_footer
- 97.9% accuracy on tables, 96.4% on formulas

**Example:**
```
Docling sees:
- "7. Análisis de causas" → Classifies as: section_header
- Large grid structure → Classifies as: table
- Numbered list → Classifies as: list_item
```

### ✅ 3. Reading Order (Sequential Flow)

**What it does:**
- Determines natural reading sequence
- Top-to-bottom, left-to-right
- Column detection in multi-column layouts

**Example:**
```
Reading order: Title → Paragraph → Section → Table → Next section
```

---

## What Docling DOESN'T Provide

### ❌ 1. Semantic Relationships (Ownership/Belonging)

**What it CAN'T do:**
- Does NOT understand "this table BELONGS to that section header"
- Does NOT group content by semantic meaning
- Does NOT know "these 3 paragraphs are all part of section 7.2"

**Example of the gap:**
```
Document:
  a. Fecha y Hora
  [Table with dates]
  b. Identificación
  [Table with IDs]

Docling output (flat list):
  [text: "a. Fecha y Hora"]
  [table: dates]
  [text: "b. Identificación"]
  [table: IDs]

What Docling DOESN'T know:
  - Table 1 belongs to section "a"
  - Table 2 belongs to section "b"
  - You need to add this yourself!
```

### ❌ 2. Domain-Specific Patterns

**What it CAN'T do:**
- Does NOT understand document-specific numbering schemes
- Does NOT know "a.1.2" is a sub-sub-section in YOUR format
- Does NOT understand YOUR document's hierarchy rules

**Why not?**
- Different documents use different patterns
- Legal docs: "Article 1", "Clause 2.a", "Paragraph (i)"
- Scientific papers: "Abstract", "1. Introduction", "2.1 Methods"
- EAF reports: "a.", "1.", "7.2"

Docling can't hardcode patterns for ALL possible document types!

### ❌ 3. Semantic Grouping

**What it CAN'T do:**
- Does NOT group "all tables in section 7"
- Does NOT understand "this figure belongs to this paragraph"
- Does NOT know "these are subsections of section 7"

---

## Your Responsibility: TWO Custom Components

### Component 1: Monkey Patch (During Extraction)

**Purpose**: Fill missing content gaps

**When Docling misses content** (because Granite didn't detect it):
- Your monkey patch uses PyMuPDF as fallback
- Detects missing lines (coverage <50%)
- Creates synthetic clusters for missing content
- Inserts into Docling's pipeline

**Example:**
```
Docling missed: "Zona Centro"
Your patch detects: "Zona Centro" pattern
Patch creates: Synthetic cluster with correct label
Result: Content appears in final output
```

**Location**: `eaf_patch/core/eaf_patch_engine.py`

**Reusability**:
- ✅ Reusable across similar documents (same patterns)
- ❌ Need customization for different document types

### Component 2: Semantic Hierarchy Builder (After Extraction)

**Purpose**: Add parent-child relationships

**What it does**:
- Reads Docling's flat output
- Detects section headers using YOUR patterns
- Groups content under headers based on reading order
- Builds semantic hierarchy

**Example:**
```python
# Input (Docling flat):
[
  {type: "section_header", text: "a. Fecha y Hora"},
  {type: "table", text: "Fecha 25/02/2025..."},
  {type: "section_header", text: "b. Identificación"},
  {type: "table", text: "..."}
]

# Output (Your hierarchy):
{
  "sections": [
    {
      "header": "a. Fecha y Hora",
      "children": [
        {type: "table", text: "Fecha 25/02/2025..."}
      ]
    },
    {
      "header": "b. Identificación",
      "children": [
        {type: "table", text: "..."}
      ]
    }
  ]
}
```

**Location**: `METHODOLOGY/build_semantic_hierarchy.py`

**Reusability**:
- ✅ Reusable across documents with same numbering scheme
- ❌ Need new patterns for different schemes

---

## Complete Workflow

### Phase 1: Extraction (Docling + Your Patch)

```bash
python extract_with_complete_json.py document.pdf outputs/
```

**What happens:**
1. Docling extracts layout (physical structure)
2. Your monkey patch fills missing content
3. Output: Flat JSON with all elements

**Output:**
- `docling_complete.json` - Flat structure, reading order preserved
- Element types classified
- Bounding boxes included
- BUT: No semantic parent-child relationships

### Phase 2: Hierarchy Building (Your Post-Processor)

```bash
python build_semantic_hierarchy.py \
    outputs/docling_complete.json \
    outputs/docling_hierarchical.json
```

**What happens:**
1. Reads Docling's flat output
2. Detects section headers (YOUR patterns)
3. Groups content under headers
4. Builds parent-child relationships

**Output:**
- Original Docling data preserved
- Added: `semantic_hierarchy` section
- Parent-child relationships captured
- Content summaries per section

---

## When to Customize

### Scenario 1: Same Document Family (EAF Reports)

**All 11 chapters use same patterns:**
- `a.`, `b.`, `c.`
- `1.`, `2.`, `3.`
- `7.1`, `7.2`, `7.3`

**Action needed:** NONE ✅
- Monkey patch: Already configured for EAF patterns
- Hierarchy builder: Already has EAF numbering schemes
- Just run the scripts!

### Scenario 2: New Document Type (Legal Contract)

**Different patterns:**
- `Article 1`, `Article 2`
- `Clause 1.1`, `Clause 1.2`
- `Paragraph (a)`, `Paragraph (b)`

**Action needed:**
1. **Update monkey patch** (if document has special patterns to detect):
   ```python
   # eaf_patch/core/custom_detector.py
   PATTERNS = [
       r'^Article\s+(\d+)',
       r'^Clause\s+(\d+\.\d+)',
       r'^Paragraph\s+\(([a-z])\)'
   ]
   ```

2. **Update hierarchy builder**:
   ```python
   # METHODOLOGY/build_semantic_hierarchy.py
   HEADER_PATTERNS = [
       r'^Article\s+(\d+)\s+(.+)',
       r'^Clause\s+(\d+\.\d+)\s+(.+)',
       r'^Paragraph\s+\(([a-z])\)\s+(.+)'
   ]
   ```

### Scenario 3: Similar Document (Minor Variations)

**Example**: EAF Anexos vs EAF Individual Reports
- Same company (Chilean power system)
- Same numbering scheme
- Slightly different sections

**Action needed:** MINIMAL
- Monkey patch: Works as-is ✅
- Hierarchy builder: Works as-is ✅
- Maybe adjust coverage threshold

---

## Key Principles

### 1. Docling is Universal, Your Components are Domain-Specific

**Docling:**
- Works on ANY PDF
- Language-agnostic
- Format-agnostic
- No document-specific logic

**Your components:**
- Tailored to YOUR document family
- Understand YOUR numbering schemes
- Know YOUR semantic rules
- Reusable within document family

### 2. Two-Phase Approach

**Phase 1 (Extraction):**
- Docling does heavy lifting (layout, classification)
- Your patch fills gaps (missing content)
- Result: Complete flat structure

**Phase 2 (Hierarchy):**
- Your post-processor adds meaning
- Builds semantic relationships
- Result: Structured data for AI/database

### 3. Separation of Concerns

**Layout Detection** (Docling's job):
- WHERE elements are
- WHAT type they are
- WHAT order to read them

**Semantic Understanding** (Your job):
- WHICH elements belong together
- WHAT relationships exist
- HOW to group content

---

## FAQ

### Q: Why doesn't Docling build semantic hierarchy automatically?

**A:** Because semantic relationships are **document-family-specific**:
- Legal docs: Articles own clauses
- Scientific papers: Sections own figures/tables
- EAF reports: Section headers own tables/paragraphs
- Each has different rules!

Docling can't hardcode ALL possible semantic rules for ALL document types.

### Q: Do I need to write patterns for EVERY document?

**A:** No! Only for **new document families**:
- All EAF chapters (1-11): ✅ Same patterns
- All EAF annexes (1-8): ✅ Same patterns
- Legal contracts: ❌ New patterns needed
- Scientific papers: ❌ New patterns needed

### Q: Can I use Docling without custom components?

**A:** Yes, but:
- ✅ You get: Layout, element types, reading order
- ❌ You lose: Missing content detection, semantic hierarchy
- Use case: Simple documents where reading order is enough

### Q: Is this a limitation of Docling?

**A:** No, it's by **design**:
- Docling focuses on universal layout extraction (does it VERY well)
- YOU add domain expertise (semantic meaning)
- This separation makes Docling flexible and powerful

---

## Summary

### Docling Provides:
✅ Layout detection (WHERE things are)
✅ Element classification (WHAT they are)
✅ Reading order (WHAT comes after WHAT)
✅ Universal, works on ANY document

### You Provide:
🔧 Monkey patch: Fill missing content (domain-specific patterns)
🔧 Hierarchy builder: Define semantic relationships (document-specific rules)
🔧 Customization: Adapt for new document families

### Result:
🎯 Universal extraction + Domain-specific intelligence
🎯 Reusable within document families
🎯 Complete structured data for AI/database consumption

---

**Bottom Line:**

> Docling gives you **physical structure** (layout, types, order).
> You add **semantic structure** (ownership, relationships, grouping).
> Together: Complete document understanding.

---

**Last Updated**: 2025-10-26
**Tested On**: EAF Chapters 1-11, Chilean power system reports
**Status**: Production-ready ✅
