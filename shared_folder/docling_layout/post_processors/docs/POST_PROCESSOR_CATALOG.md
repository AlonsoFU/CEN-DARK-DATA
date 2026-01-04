# Post-Processor Catalog

**Last Updated:** 2025-11-25

Post-processors run AFTER Docling completes extraction, at the document level. They have access to all pages and full text content.

## Available Post-Processors

### 1. Smart Reclassification (`enumerated_item_fix.py`)

**Purpose:** Intelligently reclassifies **9 different types** of elements

This post-processor has **9 PARTS** that run sequentially:

#### **PART 1: Company Names**
```python
"Interchile S.A." (TEXT) → SECTION_HEADER
"CGE Distribución Ltda." (TEXT) → SECTION_HEADER
```
**Condition:** <50 chars + legal suffix (S.A., SpA., Ltda., Inc., Corp., LLC)

#### **PART 2: Bullet Point Sequences**
```python
"-Item 1" → LIST_ITEM (if 2+ bullets exist)
"-Item 2" → LIST_ITEM
```
**Condition:** 2+ items starting with "-"

#### **PART 3: Summary Captions**
```python
"Total: 145 incidentes" (CAPTION) → TEXT
"Totales mensuales" (CAPTION) → TEXT
```
**Pattern:** Total, Totales, Suma, Resumen + colon/period/space

#### **PART 4: Isolated Power Lines**
```python
"Línea 220 kV Calama Nueva" (isolated LIST_ITEM) → SECTION_HEADER
```
**Condition:** No other list_items within ±5 positions

#### **PART 5: Enumerated Items (Sequence-Level Analysis)**
```python
# Short sequence (all <100 chars)
"a) Short title" → SECTION_HEADER
"b) Another title" → SECTION_HEADER

# Long sequence (any >200 chars)
"c) Long explanation..." (806 chars) → LIST_ITEM
"d) More details..." → LIST_ITEM
```
**Logic:** Analyzes ENTIRE sequence, not individual items

#### **PART 6: Isolated List Items (GENERAL)**
```python
"• Antecedentes generales" (isolated) → SECTION_HEADER
```
**Condition:** No neighbors within distance (bullets=1, enumerated=3)

**Exceptions (keep as LIST_ITEM):**
- After SECTION_HEADER
- Ends with period (not company suffix)
- Contains conjugated verbs
- "Zona - Área" pattern (always SECTION_HEADER)

#### **PART 6.5: Title Pattern Recognition**
```python
"Zona Norte - Sistema Central" (LIST_ITEM) → SECTION_HEADER
"Línea 220 kV - Tramo Sur" (LIST_ITEM) → SECTION_HEADER
"S/E Maitencillo - Alimentador 12 kV" (LIST_ITEM) → SECTION_HEADER
```
**Patterns:** Zona, Área, Sistema, Central, Línea, Subestación, S/E + " - "

#### **PART 7: Cross-Page Continuations**
```python
Page 10: "La empresa debe cumplir con los requisitos de" → TEXT
Page 11: "seguridad establecidos en la normativa." → TEXT (copies from page 10)
```
**Signal:** Next page starts with lowercase = STRONG continuation signal

#### **PART 8: PAGE_HEADER to SECTION_HEADER**
```python
"6. Normalización del servicio" (PAGE_HEADER) → SECTION_HEADER
"d.3 Reiteración de fallas" (PAGE_HEADER) → SECTION_HEADER
```
**Pattern:** Chapter titles (^\d+\.\s+ or ^[a-z]\.\d+\s+)

#### **PART 9: Zona Classification Fix**
```python
# Sequential Zona items (within ±3 positions)
"Zona Norte - Área 1" → LIST_ITEM (adds bullet: "• Zona Norte - Área 1")
"Zona Sur - Área 2" → LIST_ITEM

# Isolated Zona item
"Zona Centro - Área 5" (isolated) → SECTION_HEADER
```
**Pattern:** `^[·•]?\s*Zona\s+.+?\s+-\s+Área\s+.+`

**Logic:**
- Sequential items (2+ within ±3 positions) → `LIST_ITEM` + add bullet
- Isolated items → `SECTION_HEADER`

**File:** `post_processors/core/enumerated_item_fix.py`

**See:** [Smart Reclassification Post-Processor](./SMART_RECLASSIFICATION_POST_PROCESSOR.md) (detailed documentation with examples)

---

### 2. Metadata Date Extractor (`metadata_date_extractor.py`)

**Purpose:** Extracts key dates from document headers and adds them to JSON metadata

**Extracted Fields:**
- `fecha_emision` - Document emission date
- `fecha_falla` - Failure event date
- `hora_falla` - Failure event time

**Patterns:**
```python
# Fecha de Emisión
"Fecha de Emisión: 18-03-2025" → metadata['fecha_emision'] = "18-03-2025"

# Fecha de la Falla (in text)
"A las 15:15:41 horas del día 25 de febrero de 2025..."
  → metadata['fecha_falla'] = "25 de febrero de 2025"
  → metadata['hora_falla'] = "15:15:41"
```

**Search Strategy:**
1. Analyzes first 30 SECTION_HEADERs for emission date
2. If not found, searches first 50 TEXT items containing "falla", "hora", "horas"
3. Uses regex patterns to extract DD-MM-YYYY, DD de MMMM de YYYY, and HH:MM:SS
4. Adds extracted dates to `doc_dict['origin']` before JSON export

**Regex Patterns:**
```python
emission_pattern = r'Fecha\s+de\s+Emisión:\s*(\d{1,2})-(\d{1,2})-(\d{4})'
date_pattern_long = r'(\d{1,2})\s+de\s+(enero|febrero|...|diciembre)\s+de\s+(\d{4})'
time_pattern = r'(\d{1,2}):(\d{2}):(\d{2})'
```

**Output Location:** `origin.fecha_emision`, `origin.fecha_falla`, `origin.hora_falla` in JSON

**File:** `post_processors/core/metadata_date_extractor.py`

**Performance:** <0.1 seconds (searches limited to first 30-50 items)

---

### 3. Hierarchy Restructure (`hierarchy_restructure.py`)

**Purpose:** Populates `children[]` arrays in section headers to reflect semantic parent-child hierarchy

**What it does:**
- Detects numbering patterns in SECTION_HEADERs
- Populates `children[]` arrays with `$ref` pointers
- Does NOT move items or modify `body.children`
- Only ADDS references to existing empty `children[]` arrays

**Supported patterns:**
```python
1., 2., 3.           → Level 1 (main chapters)
1.1, 1.2, 2.1        → Level 2 (subsections)
a), b), c)           → Level 3 (enumerated)
a., b., c.           → Level 4 (sub-enumerated)
i., ii., iii.        → Level 5 (roman numerals)
```

**Example output:**
```json
{
  "text": "1. Descripción",
  "children": [
    {"$ref": "#/texts/3"},   // → "a. Fecha y Hora"
    {"$ref": "#/texts/4"},   // → "b. Identificación"
    {"$ref": "#/texts/5"}    // → "c. Elemento"
  ]
}
```

**Benefits:**
- LLM can navigate hierarchy: `item → children → grandchildren`
- Faster semantic search
- Better document understanding

**File:** `post_processors/core/hierarchy_restructure.py`

**Performance:** ~0.001 seconds per chapter (instantaneous)

---

### 4. Table Re-extraction (`table_reextract/`)

**Purpose:** Re-extracts tables that TableFormer failed to process correctly, using specialized extractors based on table type.

**Architecture:**
```
table_reextract/
├── __init__.py           # Entry point: apply_table_reextract_to_document()
├── classifier.py         # Classifies table type using PyMuPDF pre-scan
├── extractors/
│   ├── pymupdf.py        # Generic extractor for tables without lines
│   └── tableformer.py    # Keeps original Docling result
└── custom/
    ├── costos_horarios.py     # 24-hour cost tables (26 cols)
    └── programacion_diaria.py # Daily programming tables (26 cols) ⭐ NEW
```

**Classification Process:**
1. Pre-scan bbox with PyMuPDF to get raw text
2. Analyze content for domain-specific keywords
3. Compare TableFormer extraction ratio (extracted/expected chars)
4. Select appropriate extractor

**Table Types Detected:**

| Type | Keywords | Extractor |
|------|----------|-----------|
| `programacion_diaria` | COORDINADOR ELÉCTRICO, Programación Diaria | `custom/programacion_diaria.py` |
| `costos_horarios` | Costos Operación, Costo Marginal, Pérdidas | `custom/costos_horarios.py` |
| `demanda_generacion` | Demanda, Generación, MWh, GWh | `costos_horarios.py` |
| `hidroelectricas` | Hidroeléctrica, Pasada, Embalse | `pymupdf.py` |
| `sin_lineas_generico` | Poor extraction ratio (<30%) | `pymupdf.py` |
| `tableformer_ok` | Good extraction ratio (>70%) | `tableformer.py` |

**Validation System:** ⭐ NEW

Each custom extractor includes a `validate()` function that runs after extraction.

#### Programación Diaria Validator (`programacion_diaria.py`)

**Checks performed:**

| Check | Type | Condition |
|-------|------|-----------|
| Column count | ERROR | Must be exactly 26 columns |
| Headers | WARNING | Must match `["Concepto", "1", "2", ..., "24", "Total"]` |
| Row completeness | WARNING | Each row must have 26 cells |
| Numeric values | WARNING | Columns 1-24 must be numeric (allows empty, `-`, decimals) |
| Row count | ERROR | Must have at least 1 data row |

**Confidence calculation:**
```python
total_checks = 3  # cols, headers, rows
passed = total_checks - len(errors)
confidence = passed / total_checks  # 0.0 to 1.0
```

**Example validation output:**
```json
{
  "valid": true,
  "confidence": 1.0,
  "errors": [],
  "warnings": ["Headers don't match expected pattern"]
}
```

```json
{
  "valid": false,
  "confidence": 0.67,
  "errors": ["Expected 26 cols, got 24"],
  "warnings": ["5 non-numeric values in hour columns"]
}
```

**Output Structure:**
```json
{
  "extractor": "programacion_diaria",
  "headers": ["Concepto", "1", "2", ..., "24", "Total"],
  "rows": [["Central X", "100", "105", ...]],
  "num_rows": 15,
  "num_cols": 26,
  "validation": {
    "valid": true,
    "confidence": 0.9,
    "errors": [],
    "warnings": ["2 non-numeric values in hour columns"]
  }
}
```

**Usage:**
```python
from post_processors.core import apply_table_reextract_to_document

# Standard mode (smart classification)
count = apply_table_reextract_to_document(doc, pdf_path)

# Force PyMuPDF for all tables (skip TableFormer results)
count = apply_table_reextract_to_document(doc, pdf_path, force_pymupdf=True)
```

**Error Storage:**

Validation results are stored directly in each table's `data` field:
```json
{
  "data": {
    "extractor": "programacion_diaria",
    "headers": [...],
    "rows": [...],
    "validation": {
      "valid": false,
      "confidence": 0.67,
      "errors": ["Expected 26 cols, got 24"],
      "warnings": ["Row 3 has non-numeric value"]
    }
  }
}
```

**Console Output:**
```
📊 [TABLE REEXTRACT] Re-extracting tables (Smart classification)
================================================================================
📋 [TABLE REEXTRACT] Processing 45 tables...
   Table 0 (p.1): ↻ Re-extracted (15x26) - Detected daily programming table
   Table 1 (p.2): ✓ Kept TableFormer (120 cells) - Good extraction (85%)
   Table 2 (p.3): ↻ Re-extracted (8x26) - Poor extraction (12%), re-extracting
...
✅ [TABLE REEXTRACT] Re-extracted: 32, Kept: 13
⏱️  [TABLE REEXTRACT] Processing time: 0.145 seconds
================================================================================
```

**File:** `post_processors/core/table_reextract/`

**Performance:** ~0.003 seconds per table

**See also:** [Future Improvements](../core/table_reextract/FUTURE_IMPROVEMENTS.md) - Roadmap for optimization

---

### 5. Table Continuation Merger (`table_continuation_merger.py`) ⭐ NEW

**Purpose:** Merges tables that span multiple pages into single consolidated tables.

**Problem Solved:**
In EAF reports, detailed tables (DETALLE) often continue across pages:
- Table N: Technology header (e.g., "Hidroeléctricas de Pasada")
- Table N+1: Continuation with "Concepto" header (same columns)
- Table N+2: Another continuation (same columns)

**Detection Criteria:**
```python
def _is_continuation(candidate, base_table):
    # Must have same number of columns
    # Must have matching headers
    # Must be on same or consecutive pages (page_diff <= 1)
    # Must use same extractor
    # First header must be "Concepto" or match base table
```

**What it Does:**
1. Detects continuation patterns
2. Merges rows from continuation tables into base table
3. Marks continuation tables with `"is_continuation": true` flag
4. Filters out metadata/header rows during merge
5. Updates validation with merge notes

**Metadata Rows Filtered During Merge:**

The merger skips these rows when merging continuations:
```python
metadata_patterns = [
    "periodo desde:",
    "fecha:",
    "coordinador eléctrico",
    "programación diaria",
    "sistema eléctrico",
]
```
Also skips rows with empty first cell.

**Output:**
```json
// Base table (merged)
{
  "headers": ["Concepto", "1", "2", ...],
  "rows": [...],  // Combined rows from all continuations
  "num_rows": 45,  // Updated count
  "validation": {
    "warnings": ["Merged 2 continuation tables"]
  }
}

// Continuation table (marked)
{
  "is_continuation": true,
  "merged_into_table": "#/tables/5"
}
```

**Usage:**
```python
from post_processors.core import apply_table_continuation_merger_to_document

merge_count = apply_table_continuation_merger_to_document(doc)
print(f"✅ Merged {merge_count} continuation tables")
```

**Console Output:**
```
================================================================================
🔧 [TABLE CONTINUATION MERGER] Starting...
================================================================================

  Table 5:
    Base: 'Hidroeléctricas de Pasada' (page 12, 8 rows, programacion_diaria)
    + Continuation: 'Concepto' (page 13, 12 rows) (12 rows)
    + Continuation: 'Concepto' (page 14, 6 rows) (6 rows)
    → Merged table: 26 total rows

✅ [TABLE CONTINUATION MERGER] Merged 2 continuation tables
================================================================================
```

**File:** `post_processors/core/table_continuation_merger.py`

**Performance:** ~0.001 seconds per table

---

## Execution Order

Post-processors run in this order:

```python
# 1. Docling extraction (with monkey patch)
result = converter.convert(pdf_path)
doc = result.document

# 2. Apply Smart Reclassification (10 parts)
enum_count = apply_enumerated_item_fix_to_document(doc)

# 3. Re-extract tables with specialized extractors
table_count = apply_table_reextract_to_document(doc, pdf_path, force_pymupdf=True)

# 4. Merge table continuations across pages
merge_count = apply_table_continuation_merger_to_document(doc)

# 5. Restructure hierarchy (populate children[] arrays)
hierarchy_count = apply_hierarchy_restructure_to_document(doc)

# 6. Extract metadata dates
date_metadata = apply_date_extraction_to_document(doc)

# 7. Export to JSON and add dates
doc_dict = doc.export_to_dict()
doc_dict['origin']['fecha_emision'] = date_metadata.get('fecha_emision')
doc_dict['origin']['fecha_falla'] = date_metadata.get('fecha_falla')
doc_dict['origin']['hora_falla'] = date_metadata.get('hora_falla')
```

**Total Post-Processors:** 5
- Smart Reclassification: 10 parts (Parts 1-10)
- Table Re-extraction: Classifies and re-extracts tables with PyMuPDF
- Table Continuation Merger: Merges multi-page tables
- Hierarchy Restructure: Populates children[] arrays
- Metadata Date Extractor: Extracts dates to metadata

---

## Summary Table

| # | Post-Processor | What it Does | Pattern/Condition |
|---|----------------|--------------|-------------------|
| 1 | Smart (Part 1) | Company names → SECTION_HEADER | <50 chars + legal suffix |
| 2 | Smart (Part 2) | Bullet sequences → LIST_ITEM | 2+ items with "-" |
| 3 | Smart (Part 3) | Summary captions → TEXT | Total, Totales, Suma, Resumen |
| 4 | Smart (Part 4) | Isolated power lines → SECTION_HEADER | "Línea XXX kV" standalone |
| 5 | Smart (Part 5) | Enumerated sequences | a), b), c) - sequence analysis |
| 6 | Smart (Part 6) | Isolated lists → SECTION_HEADER | Any isolated list_item + exceptions |
| 7 | Smart (Part 6.5) | Title patterns → SECTION_HEADER | Zona, Área, Sistema, Línea, S/E + " - " |
| 8 | Smart (Part 7) | Cross-page continuations | Next page starts lowercase |
| 9 | Smart (Part 8) | PAGE_HEADER → SECTION_HEADER | Chapter titles misclassified |
| 10 | Smart (Part 9) | Zona classification fix | "Zona X - Área Y" sequential/isolated |
| 11 | Smart (Part 10) | Similar header normalization | Normalize similar headers |
| 12 | **Table Re-extract** | Re-extract failed tables | PyMuPDF pre-scan + classification |
| 13 | **Table Continuation** | Merge multi-page tables | Same headers + consecutive pages |
| 14 | Hierarchy Restructure | Populate children[] arrays | Numbering patterns: 1., 1.1, a), a. |
| 15 | Metadata Date Extractor | Extract dates to metadata | Fecha de Emisión, fecha/hora falla |

---

## Why Document-Level?

Post-processors run at document level (not page level) because:

1. **Text is available:** During page-level processing, `cluster.text` is empty
2. **Cross-page analysis:** Can detect sequences across page boundaries
3. **Full context:** Can count items across entire document (e.g., bullet points)

---

## Performance Impact

- **Smart Reclassification (10 parts):** ~0.3-0.5 seconds total
- **Table Re-extraction:** ~0.003 seconds per table
- **Table Continuation Merger:** ~0.001 seconds per table
- **Hierarchy Restructure:** ~0.001 seconds per chapter
- **Metadata Date Extractor:** <0.1 seconds
- **Total Overhead:** <2% of total extraction time

**All post-processors combined add negligible overhead while significantly improving extraction quality.**

---

## Adding a New Post-Processor

1. Create file in `post_processors/core/`
2. Implement function: `apply_XXX_fix_to_document(document)`
3. Add to `post_processors/core/__init__.py`:
   ```python
   from .xxx_fix import apply_xxx_fix_to_document
   __all__ = [..., 'apply_xxx_fix_to_document']
   ```
4. Call in `EXTRACT_ANY_CHAPTER.py`:
   ```python
   xxx_count = apply_xxx_fix_to_document(doc)
   print(f"✅ XXX fixes: {xxx_count}")
   ```

---

## See Also

- [Smart Reclassification Details](./SMART_RECLASSIFICATION_POST_PROCESSOR.md) - Detailed documentation with examples
- [EAF Patch Documentation](../../eaf_patch/docs/) - Monkey patch architecture
- [Main Project README](../../README.md) - Project overview
