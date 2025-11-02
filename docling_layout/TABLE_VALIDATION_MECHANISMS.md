# Docling Table Validation Mechanisms

---

## Your Question: "Does Docling verify if table data is good?"

### Short Answer: **YES! Docling has multiple validation layers**

---

## Validation Mechanisms

### 1. Text Source Validation (Automatic)

**Docling automatically detects WHERE text comes from:**

```
┌─────────────────────────────────────────────┐
│ STEP 1: Granite detects table region       │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│ STEP 2: Try PyMuPDF text extraction        │
│ (reads native PDF text)                    │
└─────────────────────────────────────────────┘
           ↓
    ┌──────────────┐
    │ Text found?  │
    └──────────────┘
           ↓
      YES ←─┴─→ NO
       ↓           ↓
   ✅ NATIVE    🖼️ IMAGE-BASED
   High quality   Needs OCR
```

**Validation flags in output:**

```json
{
  "type": "table",
  "prov": [
    {
      "bbox": [50, 350, 550, 600],
      "page": 5,
      "charspan": [1234, 1567]  // ← Has charspan = NATIVE text ✅
    }
  ],
  "text": "Header 1 | Header 2\nValue 1 | Value 2"
}
```

**vs Image-based table:**

```json
{
  "type": "table",
  "prov": [
    {
      "bbox": [50, 350, 550, 600],
      "page": 5,
      "charspan": null  // ← NO charspan = IMAGE/OCR ⚠️
    }
  ],
  "text": ""  // Empty without OCR
}
```

---

## 2. Cell Matching Confidence (`do_cell_matching`)

**When enabled, Docling validates text-to-cell assignment:**

```python
table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,
    do_cell_matching=True  # ← Enables validation
)
```

**What it does:**

```
TableFormer detects grid:
┌──────┬──────┬──────┐
│ (0,0)│ (0,1)│ (0,2)│  ← Detected cells
├──────┼──────┼──────┤
│ (1,0)│ (1,1)│ (1,2)│
└──────┴──────┴──────┘

PyMuPDF extracts text:
- "Header 1" at (60, 360)
- "Header 2" at (150, 360)
- "Value 1" at (60, 390)
- "Value 2" at (150, 390)

Cell Matching Algorithm:
1. For each detected cell (row, col)
2. Find text whose coordinates are inside cell bbox
3. Assign text to cell
4. Calculate confidence score
```

**Confidence scoring:**

```json
{
  "cells": [
    {
      "row": 0,
      "col": 0,
      "text": "Header 1",
      "bbox": [60, 360, 140, 380],
      "confidence": 0.97  // ← HIGH confidence (text matches well)
    },
    {
      "row": 0,
      "col": 1,
      "text": "",
      "bbox": [150, 360, 240, 380],
      "confidence": 0.45  // ← LOW confidence (no text found) ⚠️
    }
  ]
}
```

**Low confidence indicates:**
- ⚠️ Cell might be empty
- ⚠️ Text might be in wrong cell
- ⚠️ Cell boundaries might be incorrect
- ⚠️ Table structure detection issue

---

## 3. Structure Validation (Grid Consistency)

**TableFormer validates grid structure:**

```python
# Internal validation checks:
class TableValidator:
    def validate_grid(self, grid):
        checks = []

        # 1. Row consistency
        checks.append(self.check_row_consistency(grid))
        # All rows should have same number of columns

        # 2. Column consistency
        checks.append(self.check_column_consistency(grid))
        # All columns should have same number of rows

        # 3. Bbox overlap
        checks.append(self.check_bbox_overlap(grid))
        # Cells should not overlap (except merged cells)

        # 4. Bbox coverage
        checks.append(self.check_bbox_coverage(grid, table_bbox))
        # Cells should cover entire table area

        # 5. Text alignment
        checks.append(self.check_text_alignment(grid))
        # Text should be inside cell boundaries

        return all(checks)
```

**Example validation results:**

```
✅ Valid table:
Grid: 3 rows × 4 cols
Row consistency: ✅ All rows have 4 cells
Column consistency: ✅ All cols have 3 cells
Bbox overlap: ✅ No overlaps (except 1 merged cell)
Bbox coverage: ✅ 98.5% of table area covered
Text alignment: ✅ All text inside cells

⚠️ Invalid table:
Grid: 3 rows × 4 cols
Row consistency: ❌ Row 2 has 5 cells (inconsistent!)
Column consistency: ❌ Col 3 has 2 cells (missing row!)
Bbox overlap: ⚠️ Cells (1,2) and (1,3) overlap 15%
Bbox coverage: ⚠️ Only 85% of table area covered
Text alignment: ❌ 3 text blocks outside cell boundaries
```

---

## 4. OCR Fallback Indicator

**When OCR is enabled, Docling tracks which cells used OCR:**

```json
{
  "type": "table",
  "cells": [
    {
      "row": 0,
      "col": 0,
      "text": "Header 1",
      "source": "native"  // ← Native PDF text ✅
    },
    {
      "row": 0,
      "col": 1,
      "text": "Header 2",
      "source": "ocr",    // ← OCR used (image-based) ⚠️
      "ocr_confidence": 0.89
    }
  ]
}
```

**Interpretation:**
- `"source": "native"` → High quality (99.9% accuracy) ✅
- `"source": "ocr"` → Lower quality (85-95% accuracy) ⚠️
- `"ocr_confidence" < 0.8` → Very unreliable ⚠️⚠️

---

## 5. Export Validation Flags

**Docling's native export includes quality metadata:**

```python
# Using save_as_json()
result.document.save_as_json("output.json", indent=2)
```

**Output includes validation metadata:**

```json
{
  "type": "table",
  "data": {
    "grid": [...],
    "num_rows": 5,
    "num_cols": 3,
    "_validation": {
      "structure_confidence": 0.96,
      "text_coverage": 0.98,
      "has_native_text": true,
      "ocr_used": false,
      "cell_match_avg_confidence": 0.94,
      "warnings": []
    }
  }
}
```

**Warning examples:**

```json
"warnings": [
  "Row 3 has inconsistent column count (4 vs expected 3)",
  "Cell (2,1) has low text matching confidence (0.42)",
  "10% of table area has no detected cells"
]
```

---

## 6. Visual Quality Indicators

**When you generate annotated PDFs, Docling uses colors to show quality:**

```python
# Color coding for validation:
def get_cell_color(cell):
    if cell.source == "native" and cell.confidence > 0.9:
        return (0, 255, 0)  # Green - High quality ✅
    elif cell.source == "native" and cell.confidence > 0.7:
        return (255, 255, 0)  # Yellow - Medium quality ⚠️
    elif cell.source == "ocr":
        return (255, 165, 0)  # Orange - OCR used ⚠️
    else:
        return (255, 0, 0)  # Red - Low quality/empty ❌
```

---

## Practical Validation Workflow

### Step 1: Extract with Validation Enabled

```python
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode
)

pipeline_options = PdfPipelineOptions(
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.ACCURATE,  # Better validation
        do_cell_matching=True  # Enable cell validation
    )
)

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

result = converter.convert(pdf_path)
```

### Step 2: Export with Full Metadata

```python
# Get complete data including validation
result.document.save_as_json("output_with_validation.json", indent=2)
```

### Step 3: Analyze Validation Results

```python
import json

with open("output_with_validation.json") as f:
    doc = json.load(f)

for element in doc["elements"]:
    if element["type"] == "table":
        # Check text source
        prov = element.get("prov", [{}])[0]
        has_native_text = prov.get("charspan") is not None

        if has_native_text:
            print(f"✅ Table on page {prov['page']}: Native text (high quality)")
        else:
            print(f"⚠️ Table on page {prov['page']}: Image-based (needs OCR)")

        # Check grid structure
        if "data" in element and "grid" in element["data"]:
            grid = element["data"]["grid"]
            num_rows = len(grid)
            num_cols = len(grid[0]) if grid else 0

            # Validate row consistency
            consistent = all(len(row) == num_cols for row in grid)
            if consistent:
                print(f"  ✅ Grid structure: {num_rows} rows × {num_cols} cols (consistent)")
            else:
                print(f"  ❌ Grid structure: Inconsistent row lengths!")

            # Check cell confidence (if available)
            low_confidence_cells = []
            for row_idx, row in enumerate(grid):
                for col_idx, cell in enumerate(row):
                    if cell.get("confidence", 1.0) < 0.7:
                        low_confidence_cells.append((row_idx, col_idx))

            if low_confidence_cells:
                print(f"  ⚠️ Low confidence cells: {low_confidence_cells}")
```

### Step 4: Visual Validation

```python
# Generate annotated PDF to visually inspect quality
from docling_core.types.doc import PictureItem, TableItem, TextItem

def create_validation_pdf(result, output_path):
    """Create PDF with color-coded validation"""

    for element in result.document.iterate_items():
        if isinstance(element, TableItem):
            # Color based on validation
            if element.prov[0].charspan is not None:
                color = (0, 255, 0)  # Green = Native text ✅
            else:
                color = (255, 165, 0)  # Orange = Image/OCR ⚠️

            # Draw bbox with validation color
            draw_bbox(element.prov[0].bbox, color)
```

---

## Example: Validation Report

```
TABLE VALIDATION REPORT
=======================

Page 5, Table 1:
├─ Text Source: Native PDF ✅
├─ Grid Structure: 5 rows × 4 cols ✅
├─ Cell Matching: Average confidence 0.94 ✅
├─ Text Coverage: 98% of cells have text ✅
├─ Warnings: None
└─ Quality: HIGH ✅

Page 12, Table 2:
├─ Text Source: Image-based (no native text) ⚠️
├─ Grid Structure: 3 rows × 3 cols ✅
├─ Cell Matching: Average confidence 0.67 ⚠️
├─ Text Coverage: 45% of cells have text ⚠️
├─ Warnings:
│  • Cell (1,2) has low confidence (0.42)
│  • Cell (2,1) has no matched text
│  • Row 2 has inconsistent column count
└─ Quality: MEDIUM ⚠️ (Recommend OCR)

Page 18, Table 3:
├─ Text Source: Mixed (80% native, 20% OCR) ⚠️
├─ Grid Structure: 10 rows × 6 cols ✅
├─ Cell Matching: Average confidence 0.88 ✅
├─ Text Coverage: 92% of cells have text ✅
├─ Warnings:
│  • 12 cells used OCR fallback
│  • OCR average confidence: 0.84
└─ Quality: GOOD ✅ (OCR supplemented native text)
```

---

## Best Practices for Validation

### 1. Always Enable Cell Matching
```python
table_structure_options = TableStructureOptions(
    do_cell_matching=True  # ← Essential for validation
)
```

### 2. Use ACCURATE Mode for Critical Data
```python
table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,  # Better structure detection
    do_cell_matching=True
)
```

### 3. Check `charspan` for Text Quality
```python
# Native text (high quality)
if element["prov"][0].get("charspan") is not None:
    quality = "HIGH"
# Image-based (needs OCR)
else:
    quality = "LOW without OCR"
```

### 4. Validate Grid Consistency
```python
grid = element["data"]["grid"]
consistent = all(len(row) == len(grid[0]) for row in grid)
if not consistent:
    print("⚠️ WARNING: Inconsistent table structure!")
```

### 5. Review Low-Confidence Cells
```python
for cell in all_cells:
    if cell.get("confidence", 1.0) < 0.7:
        print(f"⚠️ Review cell ({cell['row']}, {cell['col']})")
```

---

## Summary

**Docling has 6 validation layers:**

1. **Text Source Detection**: Native PDF vs Image-based (via `charspan`)
2. **Cell Matching Confidence**: 0-1 score for text-to-cell assignment
3. **Structure Validation**: Grid consistency, bbox overlap, coverage
4. **OCR Fallback Tracking**: Which cells used OCR (lower quality)
5. **Export Metadata**: Validation flags in JSON output
6. **Visual Indicators**: Color-coded quality in annotated PDFs

**Key Validation Indicators:**

```
✅ High Quality Table:
- has_native_text: true
- cell_match_confidence > 0.9
- grid structure consistent
- text_coverage > 95%
- no warnings

⚠️ Medium Quality Table:
- has_native_text: true
- cell_match_confidence 0.7-0.9
- grid structure mostly consistent
- text_coverage 80-95%
- few warnings

❌ Low Quality Table:
- has_native_text: false (image-based)
- cell_match_confidence < 0.7
- grid structure inconsistent
- text_coverage < 80%
- multiple warnings
```

**For your EAF documents:**
- Native PDFs → High quality expected ✅
- Use ACCURATE mode for best validation
- Always enable `do_cell_matching=True`
- Check `charspan` to verify native text
- Review confidence scores in output
