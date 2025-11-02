# Extraction Process Comparison: Current vs save_as_json()

---

## Process 1: YOUR CURRENT CUSTOM EXTRACTION

### Flow Diagram:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Configure Docling                                  │
├─────────────────────────────────────────────────────────────┤
│ pipeline_options = PdfPipelineOptions()                    │
│ pipeline_options.do_ocr = False                            │
│ pipeline_options.table_structure_options.mode = FAST       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Convert PDF                                        │
├─────────────────────────────────────────────────────────────┤
│ converter = DocumentConverter(...)                         │
│ result = converter.convert(pdf_path)                       │
│                                                            │
│ Docling extracts:                                          │
│ ✅ Layout (Granite AI)                                     │
│ ✅ Text (PyMuPDF)                                          │
│ ✅ Tables (TableFormer)                                    │
│ ✅ Grid structure (cells/rows/cols)                        │
│ ✅ Validation metadata                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Apply EAF Monkey Patch (Custom Logic)             │
├─────────────────────────────────────────────────────────────┤
│ from eaf_patch import apply_eaf_patch                      │
│                                                            │
│ patched_result = apply_eaf_patch(result)                   │
│                                                            │
│ Patch logic:                                               │
│ • Detect missing titles                                    │
│ • Extract power line patterns                              │
│ • Fill gaps with PyMuPDF                                   │
│ • Enhance content                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Custom JSON Building (MANUAL CODE)                │
├─────────────────────────────────────────────────────────────┤
│ elements_json = []                                         │
│                                                            │
│ for item in patched_result.document.iterate_items():      │
│     elem = {                                               │
│         "type": item.label,          # ← Basic info only  │
│         "text": item.text,           # ← Often empty!     │
│         "page": item.prov[0].page,                        │
│         "bbox": {                                          │
│             "x0": item.prov[0].bbox.l,                    │
│             "y0": item.prov[0].bbox.t,                    │
│             "x1": item.prov[0].bbox.r,                    │
│             "y1": item.prov[0].bbox.b                     │
│         }                                                  │
│     }                                                      │
│                                                            │
│     # Special handling for titles                         │
│     if isinstance(item, SectionHeaderItem):               │
│         elem["level"] = item.level                        │
│                                                            │
│     elements_json.append(elem)                            │
│                                                            │
│ ⚠️ PROBLEM: Skips table grid structure!                   │
│ ⚠️ PROBLEM: Loses validation metadata!                    │
│ ⚠️ PROBLEM: No charspan info!                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Save Custom JSON                                  │
├─────────────────────────────────────────────────────────────┤
│ output = {                                                 │
│     "elements": elements_json,                            │
│     "metadata": {                                          │
│         "total_pages": num_pages,                         │
│         "extraction_date": datetime.now()                 │
│     }                                                      │
│ }                                                          │
│                                                            │
│ with open("layout_WITH_PATCH.json", "w") as f:            │
│     json.dump(output, f, indent=2)                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: layout_WITH_PATCH.json (19 KB)                    │
├─────────────────────────────────────────────────────────────┤
│ {                                                          │
│   "elements": [                                            │
│     {                                                      │
│       "type": "table",                                     │
│       "text": "",              ← EMPTY! ❌                 │
│       "page": 1,                                           │
│       "bbox": {...}                                        │
│     }                                                      │
│   ]                                                        │
│ }                                                          │
│                                                            │
│ ❌ Missing: Table grid structure                          │
│ ❌ Missing: Cell data                                     │
│ ❌ Missing: Validation (charspan)                         │
│ ❌ Missing: Native vs image detection                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Process 2: RECOMMENDED - Using save_as_json()

### Flow Diagram:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Configure Docling (SAME)                          │
├─────────────────────────────────────────────────────────────┤
│ pipeline_options = PdfPipelineOptions()                    │
│ pipeline_options.do_ocr = False                            │
│ pipeline_options.table_structure_options.mode = ACCURATE   │
│ pipeline_options.table_structure_options.do_cell_matching = True │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Convert PDF (SAME)                                │
├─────────────────────────────────────────────────────────────┤
│ converter = DocumentConverter(...)                         │
│ result = converter.convert(pdf_path)                       │
│                                                            │
│ Docling extracts:                                          │
│ ✅ Layout (Granite AI)                                     │
│ ✅ Text (PyMuPDF)                                          │
│ ✅ Tables (TableFormer ACCURATE)                           │
│ ✅ Grid structure (cells/rows/cols)                        │
│ ✅ Validation metadata                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Apply EAF Monkey Patch (SAME - Optional)          │
├─────────────────────────────────────────────────────────────┤
│ from eaf_patch import apply_eaf_patch                      │
│                                                            │
│ patched_result = apply_eaf_patch(result)                   │
│                                                            │
│ Patch logic:                                               │
│ • Detect missing titles                                    │
│ • Extract power line patterns                              │
│ • Fill gaps with PyMuPDF                                   │
│ • Enhance content                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Use Native Export (ONE LINE!) ⭐                   │
├─────────────────────────────────────────────────────────────┤
│ # Complete export with ONE method call:                   │
│ patched_result.document.save_as_json(                      │
│     "complete_output.json",                                │
│     indent=2                                               │
│ )                                                          │
│                                                            │
│ ✅ Saves EVERYTHING automatically!                         │
│ ✅ No manual JSON building needed!                         │
│ ✅ Includes all Docling data structures!                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: complete_output.json (150+ KB)                    │
├─────────────────────────────────────────────────────────────┤
│ {                                                          │
│   "schema_name": "DoclingDocument",                       │
│   "version": "1.0.0",                                      │
│   "name": "EAF-089-2025.pdf",                             │
│   "elements": [                                            │
│     {                                                      │
│       "type": "table",                                     │
│       "text": "Header 1 | Header 2\n...",  ← HAS TEXT! ✅  │
│       "prov": [{                                           │
│         "bbox": [100, 200, 500, 400],                     │
│         "page": 5,                                         │
│         "charspan": [1234, 1567]  ← VALIDATION! ✅        │
│       }],                                                  │
│       "data": {                    ← GRID STRUCTURE! ✅    │
│         "grid": [                                          │
│           [                                                │
│             {"row": 0, "col": 0, "text": "Header 1"},     │
│             {"row": 0, "col": 1, "text": "Header 2"}      │
│           ],                                               │
│           [                                                │
│             {"row": 1, "col": 0, "text": "Value 1"},      │
│             {"row": 1, "col": 1, "text": "Value 2"}       │
│           ]                                                │
│         ],                                                 │
│         "num_rows": 2,                                     │
│         "num_cols": 2                                      │
│       }                                                    │
│     }                                                      │
│   ]                                                        │
│ }                                                          │
│                                                            │
│ ✅ Has: Complete table text                               │
│ ✅ Has: Grid structure (rows/cols/cells)                  │
│ ✅ Has: Validation (charspan)                             │
│ ✅ Has: Native vs image detection                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Process 3: HYBRID APPROACH (Best of Both Worlds)

### Flow Diagram:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Configure Docling                                  │
├─────────────────────────────────────────────────────────────┤
│ pipeline_options = PdfPipelineOptions()                    │
│ pipeline_options.do_ocr = False                            │
│ pipeline_options.table_structure_options.mode = ACCURATE   │
│ pipeline_options.table_structure_options.do_cell_matching = True │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Convert PDF                                        │
├─────────────────────────────────────────────────────────────┤
│ result = converter.convert(pdf_path)                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Apply EAF Monkey Patch                            │
├─────────────────────────────────────────────────────────────┤
│ patched_result = apply_eaf_patch(result)                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Export BOTH Formats                                │
├─────────────────────────────────────────────────────────────┤
│ # 1. Complete Docling export                              │
│ patched_result.document.save_as_json(                      │
│     "complete_docling_output.json",                        │
│     indent=2                                               │
│ )                                                          │
│                                                            │
│ # 2. Simplified custom export (for compatibility)         │
│ simplified_json = build_custom_json(patched_result)       │
│ with open("layout_WITH_PATCH.json", "w") as f:            │
│     json.dump(simplified_json, f, indent=2)               │
│                                                            │
│ # 3. Markdown export (human-readable)                     │
│ markdown = patched_result.document.export_to_markdown()    │
│ with open("document.md", "w") as f:                        │
│     f.write(markdown)                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ OUTPUTS: Multiple Formats                                  │
├─────────────────────────────────────────────────────────────┤
│ ✅ complete_docling_output.json (150+ KB)                  │
│    - Complete table data with grid structure               │
│    - Validation metadata                                   │
│    - For data processing/analysis                          │
│                                                            │
│ ✅ layout_WITH_PATCH.json (19 KB)                          │
│    - Simplified format                                     │
│    - For visualization/compatibility                       │
│                                                            │
│ ✅ document.md (50 KB)                                      │
│    - Human-readable                                        │
│    - For review/documentation                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Comparison Table

| Aspect | Current Process | save_as_json() | Hybrid |
|--------|-----------------|----------------|--------|
| **Code Lines** | ~50 lines | 1 line | ~60 lines |
| **Complexity** | High (manual) | Low (automatic) | Medium |
| **Table Text** | ❌ Often empty | ✅ Complete | ✅ Both |
| **Grid Structure** | ❌ Lost | ✅ Preserved | ✅ Both |
| **Validation** | ❌ No charspan | ✅ Has charspan | ✅ Both |
| **File Size** | Small (19 KB) | Large (150+ KB) | Both |
| **Maintainability** | Low (custom code) | High (native) | Medium |
| **Error-prone** | High (manual) | Low (tested) | Medium |
| **EAF Patch** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Visualization** | ✅ Compatible | ⚠️ Need adapter | ✅ Both |

---

## Code Examples

### Current Process (Simplified):

```python
# Your current script
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from eaf_patch import apply_eaf_patch
import json

# Configure
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False

# Convert
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
result = converter.convert(pdf_path)

# Apply patch
patched_result = apply_eaf_patch(result)

# MANUAL JSON BUILDING (50+ lines)
elements_json = []
for item in patched_result.document.iterate_items():
    elem = {
        "type": item.label,
        "text": item.text,  # Often empty for tables!
        "page": item.prov[0].page,
        "bbox": {
            "x0": item.prov[0].bbox.l,
            "y0": item.prov[0].bbox.t,
            "x1": item.prov[0].bbox.r,
            "y1": item.prov[0].bbox.b
        }
    }

    if isinstance(item, SectionHeaderItem):
        elem["level"] = item.level

    elements_json.append(elem)

output = {"elements": elements_json}
with open("layout_WITH_PATCH.json", "w") as f:
    json.dump(output, f, indent=2)
```

---

### Using save_as_json():

```python
# Much simpler!
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode
from eaf_patch import apply_eaf_patch

# Configure (with better settings)
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,
    do_cell_matching=True
)

# Convert
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
result = converter.convert(pdf_path)

# Apply patch
patched_result = apply_eaf_patch(result)

# ONE LINE EXPORT! ⭐
patched_result.document.save_as_json("complete_output.json", indent=2)
```

---

### Hybrid Approach:

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode
from eaf_patch import apply_eaf_patch
import json

# Configure
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,
    do_cell_matching=True
)

# Convert
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
result = converter.convert(pdf_path)

# Apply patch
patched_result = apply_eaf_patch(result)

# Export multiple formats:

# 1. Complete Docling format (for data processing)
patched_result.document.save_as_json("complete_docling_output.json", indent=2)

# 2. Simplified format (for visualization compatibility)
elements_json = []
for item in patched_result.document.iterate_items():
    elem = {
        "type": item.label,
        "text": item.text,
        "page": item.prov[0].page,
        "bbox": {
            "x0": item.prov[0].bbox.l,
            "y0": item.prov[0].bbox.t,
            "x1": item.prov[0].bbox.r,
            "y1": item.prov[0].bbox.b
        }
    }
    if isinstance(item, SectionHeaderItem):
        elem["level"] = item.level
    elements_json.append(elem)

with open("layout_WITH_PATCH.json", "w") as f:
    json.dump({"elements": elements_json}, f, indent=2)

# 3. Markdown format (for human review)
markdown = patched_result.document.export_to_markdown(enable_chart_tables=True)
with open("document.md", "w") as f:
    f.write(markdown)

print("✅ Exported 3 formats:")
print("  - complete_docling_output.json (complete data)")
print("  - layout_WITH_PATCH.json (simplified)")
print("  - document.md (human-readable)")
```

---

## What Data is Lost in Current Process?

### Table Example:

**Docling extracts (internally):**
```python
{
  "type": "table",
  "text": "Header 1 | Header 2 | Header 3\nValue 1 | Value 2 | Value 3",
  "prov": [{
    "bbox": [100, 200, 500, 400],
    "page": 5,
    "charspan": [1234, 1567]  # ← NATIVE text validation
  }],
  "data": {
    "grid": [  # ← Cell-by-cell structure
      [
        {"row": 0, "col": 0, "bbox": [110, 210, 200, 230], "text": "Header 1"},
        {"row": 0, "col": 1, "bbox": [210, 210, 300, 230], "text": "Header 2"},
        {"row": 0, "col": 2, "bbox": [310, 210, 400, 230], "text": "Header 3"}
      ],
      [
        {"row": 1, "col": 0, "bbox": [110, 240, 200, 260], "text": "Value 1"},
        {"row": 1, "col": 1, "bbox": [210, 240, 300, 260], "text": "Value 2"},
        {"row": 1, "col": 2, "bbox": [310, 240, 400, 260], "text": "Value 3"}
      ]
    ],
    "num_rows": 2,
    "num_cols": 3
  }
}
```

**Your custom JSON saves:**
```python
{
  "type": "table",
  "text": "",  # ← EMPTY! (item.text is empty for tables)
  "page": 5,
  "bbox": {"x0": 100, "y0": 200, "x1": 500, "y1": 400}
}
```

**What's lost:**
- ❌ Table text (`"text": ""`)
- ❌ Grid structure (`data.grid`)
- ❌ Cell data (individual cells)
- ❌ Validation (`charspan`)
- ❌ Native detection (can't verify quality)

---

## Recommendation

**Use HYBRID APPROACH:**

1. ✅ Export complete Docling format with `save_as_json()`
   - For data processing and analysis
   - Has ALL table data

2. ✅ Keep simplified format for compatibility
   - For existing visualization tools
   - Lightweight

3. ✅ Export markdown for human review
   - Easy to read
   - Quick verification

**This gives you:**
- Complete data when you need it
- Compatibility with existing tools
- Human-readable format for review
- Best of both worlds!

---

## Summary

| Process | Pros | Cons | Recommendation |
|---------|------|------|----------------|
| **Current** | • Lightweight<br>• Compatible with viz tools | • Loses table data<br>• Manual code<br>• Error-prone | ⚠️ Use for viz only |
| **save_as_json()** | • Complete data<br>• One line<br>• Validated | • Larger files<br>• Need adapter for viz | ✅ Best for data |
| **Hybrid** | • All benefits<br>• Multiple formats<br>• Flexible | • Slightly more code | ⭐ **RECOMMENDED** |

**Bottom line**: Your current process works but **loses critical table data**. Use `save_as_json()` to get complete extraction, then convert to simplified format if needed for visualization!
