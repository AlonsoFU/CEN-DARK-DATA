# Smart Reclassification Post-Processor

**File:** `eaf_patch/core/post_processors/enumerated_item_fix.py`
**Type:** Document-level post-processing
**Runs:** AFTER Docling completes extraction (when text is available)
**Last Updated:** 2025-11-12

## Purpose

Intelligently reclassifies **8 different types** of elements that Docling often misclassifies:

1. **Company names** with legal suffixes (S.A., SpA., Ltda., etc.)
2. **Bullet point sequences** (items starting with "-")
3. **Summary captions** (Total, Totales, Suma, Resumen)
4. **Isolated power lines** (Línea XXX kV standalone items)
5. **Enumerated items** (a), b), c) or a., b., c.) - sequence-level analysis
6. **Isolated list items** (GENERAL - any isolated list_item)
7. **Title patterns** (Zona, Área, Sistema, Central, Línea, S/E)
8. **Cross-page continuations** (text flowing across pages)
9. **PAGE_HEADER to SECTION_HEADER** (chapter titles misclassified as headers)

## Why Document-Level Processing?

The original approach tried to do reclassification during page-level processing (in the monkey patch). This failed because:

```python
# During page-level processing (_process_regular_clusters):
for cluster in clusters:
    text = cluster.text  # ❌ EMPTY! Text not yet populated
    # All clusters show has_text=False
```

**Solution:** Move reclassification to document-level post-processing, after `converter.convert()` completes and text is available.

## Eight-Part Fix

### Part 1: Company Name Detection

**Pattern:** Short text (<50 chars) with legal suffixes

```python
legal_suffixes = [
    r'S\.A\.',      # Sociedad Anónima
    r'S\.p\.A\.',   # Sociedad por Acciones
    r'Ltda\.',      # Limitada
    r'SpA\.',       # Sociedad por Acciones (sin puntos)
    r'Inc\.',       # Incorporated
    r'Corp\.',      # Corporation
    r'LLC',         # Limited Liability Company
]
```

**Logic:**
```python
if item.label == TEXT and len(text) < 50 and has_legal_suffix(text):
    item.label = SECTION_HEADER
```

**Example:**
- `"Interchile S.A."` (TEXT) → SECTION_HEADER ✅

### Part 2: Bullet Point Detection

**Pattern:** Items starting with "-" (dash)

```python
bullet_pattern = re.compile(r'^-\s*\S+')
```

**Logic:**
```python
if count(bullet_items) >= 2:  # At least 2 bullet points
    for bullet_item in bullet_items:
        if item.label in [SECTION_HEADER, TEXT]:
            item.label = LIST_ITEM
```

**Why 2+ items?** A single isolated bullet point is most likely a headline, not a list item.

**Example:**
- `"-La instrucción de los siguientes planes de acción."` (SECTION_HEADER) → LIST_ITEM ✅
- `"-En PFV La Huella, se solicita..."` (SECTION_HEADER) → LIST_ITEM ✅

### Part 3: Summary Caption Reclassification

**Pattern:** Lines starting with summary keywords

```python
summary_pattern = re.compile(r'^(Total|Totales|Suma|Resumen)[:.\s]', re.IGNORECASE)
```

**Logic:**
```python
if item.label == CAPTION and summary_pattern.match(text):
    item.label = TEXT  # Summary captions are text, not captions
```

**Example:**
- `"Total: 123"` (CAPTION) → TEXT ✅
- `"Totales mensuales"` (CAPTION) → TEXT ✅

**Why?** Docling classifies table summaries as CAPTION, but they're actually TEXT content.

---

### Part 4: Isolated Power Line Detection

**Pattern:** Standalone power line items without neighbors

```python
power_line_pattern = re.compile(r'^Línea\s+\d+.*kV', re.IGNORECASE)
```

**Logic:**
```python
# Find all list_items matching power line pattern
# Check if isolated (no other list_items within ±5 positions)
if is_isolated_power_line:
    item.label = SECTION_HEADER  # Isolated power lines are headers
```

**Example:**
- `"Línea 220 kV Calama Nueva - Lasana"` (isolated LIST_ITEM) → SECTION_HEADER ✅

**Why?** A single power line reference is typically a section title, not a list item.

---

### Part 5: Enumerated Item Smart Classification

**Pattern:** Items starting with letter + delimiter

```python
enum_pattern = re.compile(r'^\s*([a-z])[\.\)]\s+', re.IGNORECASE)
# Matches: "a) ", "b) ", "c) " or "a. ", "b. ", "c. "
```

**Key Innovation: Sequence-Level Analysis**

Don't classify items individually—analyze the entire sequence's properties first.

#### Step 1: Group Items into Sequences

```python
# Example: a) → b) → c)
sequence = [item_a, item_b, item_c]

# Must be within 10 positions of each other
# Must have consecutive letters (a → b → c)
```

#### Step 2: Analyze Sequence Properties

```python
max_length = max(item.length for item in sequence)
all_short = all(item.length < 100 for item in sequence)
is_isolated = len(sequence) == 1
```

#### Step 3: Apply Decision Logic

```python
if max_length > 200:
    # ANY item >200 chars → ALL LIST_ITEM
    # Reason: Detailed list content
    desired_label = LIST_ITEM

elif not is_isolated and all_short:
    # ALL items <100 chars + in sequence → ALL SECTION_HEADER
    # Reason: Short subsection titles
    desired_label = SECTION_HEADER

elif not is_isolated:
    # Sequence with medium items (100-200 chars) → ALL LIST_ITEM
    desired_label = LIST_ITEM

elif max_length > 200:
    # Isolated + long → LIST_ITEM
    desired_label = LIST_ITEM

else:
    # Isolated + short → SECTION_HEADER
    desired_label = SECTION_HEADER
```

---

### Part 6: Isolated List Item Reclassification (GENERAL)

**Pattern:** ANY list_item appearing isolated (not pattern-specific)

**Logic:**
```python
# Different distance rules for different marker types:
# - Bullets (-, •, *, ·): distance = 1 (must be adjacent)
# - Enumerated (a), b), 1), 2)): distance ≤ 3 (can have gaps)

for list_item in all_list_items:
    has_nearby_list = check_neighbors_within_distance(list_item, max_distance)

    if not has_nearby_list:
        # EXCEPTIONS (DON'T convert):
        # 1. If previous item is SECTION_HEADER → keep LIST_ITEM
        # 2. If item is "Zona - Área" pattern → always SECTION_HEADER
        # 3. If ends with period (not company suffix) → keep LIST_ITEM
        # 4. If contains conjugated verbs → keep LIST_ITEM

        if no_exceptions_apply:
            item.label = SECTION_HEADER
```

**Examples:**

✅ **Convert to SECTION_HEADER:**
- Isolated bullet without neighbors
- Short standalone item without verb
- Item ending with colon

❌ **Keep as LIST_ITEM:**
- After a SECTION_HEADER (common pattern: header → list)
- Ends with period (sentence, not title)
- Contains verbs: "se concluye", "hay", "existe", "resulta"

**Why?** Most isolated list items are actually section titles, but we need exceptions to avoid false conversions.

---

### Part 6.5: Title Pattern Recognition

**Pattern:** Domain-specific title patterns

```python
title_pattern = re.compile(
    r'^[−•\*·\-]?\s*(Zona|Área|Sistema|Central|Línea|Subestación|S/E)\s+.+\s+-\s+',
    re.IGNORECASE
)
```

**Logic:**
```python
# Reclassify ALL list_items matching title patterns
if title_pattern.match(text):
    item.label = SECTION_HEADER
```

**Examples:**
- `"Zona Norte - Sistema Central"` (LIST_ITEM) → SECTION_HEADER ✅
- `"Línea 220 kV - Tramo Norte"` (LIST_ITEM) → SECTION_HEADER ✅
- `"S/E Maitencillo - Alimentador 12 kV"` (LIST_ITEM) → SECTION_HEADER ✅

**Why?** These patterns are geographical/infrastructure section titles, not list items.

---

### Part 7: Cross-Page Continuation Detection

**Pattern:** Text that continues from previous page to next page

**Logic:**
```python
# Check if item is first on new page
if current_page == prev_page + 1:
    # STRONG signal: Current starts with lowercase
    if current_text[0].islower():
        # Copy label from previous item
        current_item.label = prev_item.label

    # Also check: Previous doesn't end with period
    if not prev_text.endswith('.') and current_starts_lowercase:
        # This is a continuation
        current_item.label = prev_item.label
```

**Examples:**

Page 5 ends: `"La empresa debe cumplir con los siguientes requisitos de"`
Page 6 starts: `"seguridad eléctrica establecidos en la normativa"` ← Starts with lowercase!

→ Copy label from page 5 item ✅

**Why?** Text that flows across pages should maintain the same classification.

---

### Part 8: PAGE_HEADER to SECTION_HEADER Conversion

**Pattern:** Chapter titles misclassified as PAGE_HEADER

```python
chapter_title_pattern = re.compile(r'^(\d+\.\s+\w|[a-z]\.\d+\s+\w)')
# Matches: "1. Title", "6. Normalización", "d.3 Reiteración"
```

**Logic:**
```python
# Check in three places:
# 1. document.texts collection
# 2. document.furniture layer
# 3. all_items (body)

if item.label == PAGE_HEADER and chapter_title_pattern.match(text):
    item.label = SECTION_HEADER
```

**Examples:**
- `"6. Normalización del servicio"` (PAGE_HEADER) → SECTION_HEADER ✅
- `"d.3 Reiteración de fallas"` (PAGE_HEADER) → SECTION_HEADER ✅

**Why?** Docling sometimes classifies main chapter titles as page headers. These should be section headers in the document hierarchy.

---

## Decision Thresholds

| Threshold | Purpose | Justification | Used In |
|-----------|---------|---------------|---------|
| **200 chars** | Long content threshold | Items >200 chars are detailed explanations, not titles | Part 5, 6 |
| **100 chars** | Short title threshold | Subsection titles are typically <100 chars | Part 5, 6 |
| **50 chars** | Company name max | Company names are typically short | Part 1 |
| **10 positions** | Enum sequence proximity | Enumerated items must be close to form a sequence | Part 5 |
| **5 positions** | Power line isolation | Check for nearby list items | Part 4 |
| **3 positions** | Enum item proximity | Enumerated items can have small gaps | Part 6 |
| **1 position** | Bullet adjacency | Bullets must be adjacent (no gaps) | Part 6 |
| **2+ bullets** | Bullet sequence | Single bullet is likely a headline, not a list | Part 2 |

## Real-World Examples

### Part 1: Company Names (Chapter 11)

**Before:**
```
"Interchile S.A." → TEXT ❌
"CGE Distribución Ltda." → TEXT ❌
```

**After:**
```
"Interchile S.A." → SECTION_HEADER ✅
"CGE Distribución Ltda." → SECTION_HEADER ✅
```

---

### Part 2: Bullet Points (Chapter 11)

**Before:**
```
"-La instrucción de los siguientes planes de acción." → SECTION_HEADER ❌
"-En PFV La Huella, se solicita..." → SECTION_HEADER ❌
"-Informe de Falla de 5 días..." → SECTION_HEADER ❌
"-Registros oscilográficos..." → SECTION_HEADER ❌
```

**After (4+ bullets detected):**
```
"-La instrucción de los siguientes planes..." → LIST_ITEM ✅
"-En PFV La Huella, se solicita..." → LIST_ITEM ✅
"-Informe de Falla de 5 días..." → LIST_ITEM ✅
"-Registros oscilográficos..." → LIST_ITEM ✅
```

---

### Part 3: Summary Captions

**Before:**
```
"Total: 145 incidentes" → CAPTION ❌
"Totales mensuales" → CAPTION ❌
```

**After:**
```
"Total: 145 incidentes" → TEXT ✅
"Totales mensuales" → TEXT ✅
```

---

### Part 4: Isolated Power Lines (Chapter 7)

**Before:**
```
"Línea 220 kV Calama Nueva - Lasana" → LIST_ITEM ❌ (isolated, no neighbors)
```

**After:**
```
"Línea 220 kV Calama Nueva - Lasana" → SECTION_HEADER ✅ (title of section)
```

---

### Part 5: Long Enumerated Items (Chapter 10)

**Before:**
```
c) No se evidenciaron incumplimientos... (806 chars) → SECTION_HEADER ❌
d) Respecto de la aplicación... (286 chars) → SECTION_HEADER ❌
```

**Analysis:**
- Items c) and d) form a sequence
- c) has 806 chars (>200 threshold)
- Decision: Both become LIST_ITEM (detailed content)

**After:**
```
c) No se evidenciaron incumplimientos... (806 chars) → LIST_ITEM ✅
d) Respecto de la aplicación... (286 chars) → LIST_ITEM ✅
```

---

### Part 6: Isolated List Items (General)

**Before:**
```
"• Análisis de resultados" → LIST_ITEM ❌ (isolated, after section_header)
```

**After:**
```
"• Análisis de resultados" → LIST_ITEM ✅ (kept as list after header - common pattern)
```

**Before:**
```
"- Metodología aplicada" → LIST_ITEM ❌ (isolated, contains verb "aplicada")
```

**After:**
```
"- Metodología aplicada" → LIST_ITEM ✅ (kept as list - has verb)
```

**Before:**
```
"• Antecedentes generales" → LIST_ITEM ❌ (isolated, no exceptions)
```

**After:**
```
"• Antecedentes generales" → SECTION_HEADER ✅ (converted - no exceptions)
```

---

### Part 6.5: Title Patterns

**Before:**
```
"• Zona Norte - Sistema Eléctrico Central" → LIST_ITEM ❌
"Línea 220 kV - Tramo Sur" → LIST_ITEM ❌
```

**After:**
```
"• Zona Norte - Sistema Eléctrico Central" → SECTION_HEADER ✅
"Línea 220 kV - Tramo Sur" → SECTION_HEADER ✅
```

---

### Part 7: Cross-Page Continuations

**Before:**
```
Page 10: "La empresa debe cumplir con los requisitos de" → TEXT
Page 11: "seguridad establecidos en la normativa." → SECTION_HEADER ❌ (wrong!)
```

**After:**
```
Page 10: "La empresa debe cumplir con los requisitos de" → TEXT
Page 11: "seguridad establecidos en la normativa." → TEXT ✅ (continuation)
```

---

### Part 8: PAGE_HEADER Conversions

**Before:**
```
"6. Normalización del servicio" → PAGE_HEADER ❌
"d.3 Reiteración de fallas" → PAGE_HEADER ❌
```

**After:**
```
"6. Normalización del servicio" → SECTION_HEADER ✅
"d.3 Reiteración de fallas" → SECTION_HEADER ✅
```

---

### Part 5: Short Subsection Titles (Chapter 11)

**Before:**
```
a) Auditorías, planes de acción... (96 chars) → LIST_ITEM ❌
b) Medidas correctivas (22 chars) → LIST_ITEM ❌
c) Planes de acción (19 chars) → LIST_ITEM ❌
```

**Analysis:**
- Items a), b), c) form a sequence
- ALL items <100 chars (96, 22, 19)
- Decision: All become SECTION_HEADER (short subsection titles)

**After:**
```
a) Auditorías, planes de acción... (96 chars) → SECTION_HEADER ✅
b) Medidas correctivas (22 chars) → SECTION_HEADER ✅
c) Planes de acción (19 chars) → SECTION_HEADER ✅
```

### Combined Example: All Parts Working Together

**Document with multiple issues:**
```
1. "Interchile S.A." → TEXT (Part 1 fixes)
2. "6. Normalización del servicio" → PAGE_HEADER (Part 8 fixes)
3. "-Item 1" → SECTION_HEADER (Part 2 fixes - if 2+ bullets)
4. "-Item 2" → SECTION_HEADER (Part 2 fixes)
5. "Total: 145" → CAPTION (Part 3 fixes)
6. "Línea 220 kV..." (isolated) → LIST_ITEM (Part 4 fixes)
7. "a) Short title" → LIST_ITEM (Part 5 fixes - if all <100 chars)
8. "b) Another title" → LIST_ITEM (Part 5 fixes)
9. "• Isolated item" → LIST_ITEM (Part 6 fixes - if no exceptions)
10. "Zona Norte - Área 1" → LIST_ITEM (Part 6.5 fixes)
11. Page break continuation → wrong label (Part 7 fixes)
```

**After applying ALL 8 parts:**
All items correctly classified according to their context and content! ✅

## Integration with EXTRACT_ANY_CHAPTER.py

```python
from core.post_processors import (
    apply_zona_fix_to_document,
    apply_enumerated_item_fix_to_document
)

# After Docling extraction
result = converter.convert(str(pdf_path))
doc = result.document

# Apply post-processors
zona_count = apply_zona_fix_to_document(doc)
enum_count = apply_enumerated_item_fix_to_document(doc)

print(f"✅ Zona fixes: {zona_count}")
print(f"✅ Smart reclassification fixes: {enum_count}")
```

## Execution Order

```
1. Docling extraction (with monkey patch)
   ↓
2. Zona fix (post-processor #1)
   ↓
3. Smart reclassification (post-processor #2)
   ↓
4. Export to JSON
```

## Debug Output

The post-processor provides detailed logging for each of the 8 parts:

```
================================================================================
🧠 [SMART RECLASS] Smart Enumerated Item Reclassification
================================================================================
📊 [SMART RECLASS] Analyzing 147 document items...

PART 1: Company Names
   🔄 [SMART RECLASS] Company name TEXT → SECTION_HEADER: 'Interchile S.A.'
✅ [SMART RECLASS] Reclassified 1 company name(s) → SECTION_HEADER

PART 2: Bullet Points
✅ [SMART RECLASS] Reclassified 4 bullet point(s) → LIST_ITEM

PART 3: Summary Captions
✅ [SMART RECLASS] Reclassified 2 summary caption(s) → TEXT

PART 4: Isolated Power Lines
✅ [SMART RECLASS] Reclassified 1 isolated power line(s) → SECTION_HEADER

PART 5: Enumerated Items
🔍 [SMART RECLASS] Found 2 enumerated items (a), b), or a., b., ...)
   🔄 [SMART RECLASS] SECTION_HEADER → LIST_ITEM:
      Marker: 'c)' | Length: 806 chars
      Reason: sequence with long content (max 806 chars)
      Text: 'c) No se evidenciaron incumplimientos asociados...'
✅ [SMART RECLASS] Reclassified 2 item(s) → LIST_ITEM

PART 6: Isolated List Items
   🔄 [SMART RECLASS] Isolated LIST_ITEM → SECTION_HEADER (isolated bullet):
      Text: '• Antecedentes generales'
✅ [SMART RECLASS] Reclassified 1 isolated list_item(s) → SECTION_HEADER

PART 6.5: Title Patterns
✅ [SMART RECLASS] Reclassified 3 list_item(s) with title pattern → SECTION_HEADER

PART 7: Cross-Page Continuations
✅ [SMART RECLASS] Fixed 2 cross-page continuation(s)

PART 8: PAGE_HEADER Conversion
✅ [SMART RECLASS] Converted 1 chapter title PAGE_HEADER(s) to SECTION_HEADER
================================================================================
```

## Key Takeaways

### 1. Sequence-Level Analysis (Part 5)
**Always analyze sequences as a whole, not individual items.** The properties of the sequence (max length, all items' lengths, isolation) determine the correct classification for ALL items in that sequence.

This ensures consistency: if `c)` is a list item, then `d)` in the same sequence should also be a list item—even if `d)` is shorter.

### 2. Context-Aware Exceptions (Part 6)
**Not all isolated list items should become headers.** Consider context:
- After a SECTION_HEADER? Keep as LIST_ITEM (common pattern)
- Contains verbs? Keep as LIST_ITEM (content, not title)
- Ends with period? Keep as LIST_ITEM (sentence, not title)

### 3. Cross-Page Intelligence (Part 7)
**Text doesn't stop at page boundaries.** Detect continuations by:
- Lowercase start = STRONG signal of continuation
- Previous item doesn't end with period = WEAK signal
- Only apply if STRONG signal present

### 4. Comprehensive Coverage
**The post-processor handles 8 different scenarios** that Docling's AI misses. Each part solves a specific classification problem found in real-world documents.

## See Also

- [EAF Patch Architecture](./EAF_PATCH_ARCHITECTURE.md) - Overall architecture
- [Post-Processor Catalog](./POST_PROCESSOR_CATALOG.md) - All available post-processors
- [Quick Reference](./QUICK_REFERENCE.md) - Common patterns and solutions
