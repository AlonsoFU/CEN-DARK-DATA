# Post-Processor Catalog

**Last Updated:** 2025-11-17

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

## Execution Order

Post-processors run in this order:

```python
# 1. Docling extraction (with monkey patch)
result = converter.convert(pdf_path)
doc = result.document

# 2. Apply Smart Reclassification (9 parts)
enum_count = apply_enumerated_item_fix_to_document(doc)
# Note: This runs all 9 parts internally, including Zona Fix (Part 9)

# 3. Restructure hierarchy (populate children[] arrays)
hierarchy_count = apply_hierarchy_restructure_to_document(doc)

# 4. Extract metadata dates
date_metadata = apply_date_extraction_to_document(doc)

# 5. Export to JSON and add dates
doc_dict = doc.export_to_dict()
doc_dict['origin']['fecha_emision'] = date_metadata.get('fecha_emision')
doc_dict['origin']['fecha_falla'] = date_metadata.get('fecha_falla')
doc_dict['origin']['hora_falla'] = date_metadata.get('hora_falla')
```

**Total Post-Processors:** 3
- Smart Reclassification: 9 parts (Parts 1-9, including Zona Fix)
- Hierarchy Restructure: 1 pass (populates children[] arrays)
- Metadata Date Extractor: 1 pass (extracts dates to metadata)

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
| 11 | Hierarchy Restructure | Populate children[] arrays | Numbering patterns: 1., 1.1, a), a. |
| 12 | Metadata Date Extractor | Extract dates to metadata | Fecha de Emisión, fecha/hora falla |

---

## Why Document-Level?

Post-processors run at document level (not page level) because:

1. **Text is available:** During page-level processing, `cluster.text` is empty
2. **Cross-page analysis:** Can detect sequences across page boundaries
3. **Full context:** Can count items across entire document (e.g., bullet points)

---

## Performance Impact

- **Smart Reclassification (9 parts):** ~0.3-0.5 seconds total
- **Hierarchy Restructure:** ~0.001 seconds per chapter
- **Metadata Date Extractor:** <0.1 seconds
- **Total Overhead:** <1% of total extraction time

**All post-processors combined add negligible overhead while significantly improving classification accuracy.**

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
