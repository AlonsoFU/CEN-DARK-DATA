# Standard Extraction Workflow for EAF Chapters

**Last Updated**: 2025-10-26
**Method**: EAF Monkey Patch (Method A)
**Status**: Production-Ready ✅

---

## Overview

This document defines the **standardized extraction workflow** for processing EAF chapters (2-11) with Docling + EAF Monkey Patch.

### What the EAF Patch Does

The EAF monkey patch intercepts Docling's extraction pipeline and applies domain-specific fixes:

1. **📋 Title Merging**: Replaces short titles like "6." with complete lines from PyMuPDF
2. **✅ Missing Title Detection**: Finds titles Docling completely missed
3. **⚡ Power Line Classification**: Classifies power system equipment as `list_item`
4. **🔄 Zona Sequential Detection**: Distinguishes isolated Zona items (headers) from sequential ones (list items)

### Why Method A (Monkey Patch) vs Method B (Post-Processing)?

| Aspect | Method A: Monkey Patch | Method B: Post-Processing |
|--------|----------------------|--------------------------|
| **When** | DURING Docling extraction | AFTER Docling completes |
| **What** | Modifies clusters + creates synthetic cells | Changes labels only |
| **Power** | Can inject missing content | Limited to relabeling |
| **Extraction** | Docling processes modified clusters | No re-extraction |
| **Used in** | Chapter 6, Chapter 7 | Initial Chapter 7 (deprecated) |

**Decision**: Use Method A (Monkey Patch) for all chapters going forward.

---

## Standard Workflow (2 Scripts per Chapter)

For each chapter, create exactly **2 scripts**:

### 1. `extract_chapter{N}_WITH_PATCH.py`

Extraction script that applies the EAF monkey patch.

**Template**:

```python
#!/usr/bin/env python3
"""
Chapter {N} Extraction with EAF Monkey Patch
"""
import sys
from pathlib import Path

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf, apply_zona_fix_to_document

# PDF path - ADJUST FOR EACH CHAPTER
pdf_path = Path("/path/to/EAF-089-2025_capitulo_{N:02d}_pages_XXX-YYY.pdf")

print("=" * 80)
print(f"Chapter {N} Extraction with EAF Monkey Patch")
print("=" * 80)
print(f"\n📄 PDF: {pdf_path}")
print(f"📄 Pages: ZZ pages (XXX-YYY)")
print(f"🐵 Method: Monkey patch (standardized)")

# STEP 1: Apply Monkey Patch BEFORE creating converter
print("\n" + "=" * 80)
print("🐵 STEP 1: Applying EAF Monkey Patch")
print("=" * 80)

apply_universal_patch_with_pdf(pdf_path)

# STEP 2: Configure Docling
print("\n" + "=" * 80)
print("⚙️  STEP 2: Configuring Docling Pipeline")
print("=" * 80)

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = True
pipeline_options.table_structure_options.mode = TableFormerMode.FAST

converter = DocumentConverter(
    format_options={
        PdfFormatOption: pipeline_options,
    }
)

print("✅ Pipeline configured (OCR=False, Tables=FAST)")

# STEP 3: Process Chapter with Patch Active
print("\n" + "=" * 80)
print(f"🔄 STEP 3: Processing Chapter {N}")
print("=" * 80)
print(f"⏱️  This will take ~X-Y minutes (ZZ pages)...")
print("🐵 Patch is ACTIVE - will intercept Docling's pipeline")
print()

result = converter.convert(str(pdf_path))

print("\n✅ Docling extraction complete (with patch applied during pipeline)")

# STEP 4: Apply Document-Level Zona Fix
print("\n" + "=" * 80)
print("🔧 STEP 4: Applying Document-Level Zona Fix")
print("=" * 80)

doc = result.document
reclassified_count = apply_zona_fix_to_document(doc)

print(f"✅ Zona fix applied ({reclassified_count} items reclassified)")

# STEP 5: Export to JSON
print("\n" + "=" * 80)
print("📄 STEP 5: Exporting to JSON")
print("=" * 80)

output_dir = Path(__file__).parent / f"capitulo_{N:02d}" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

output_json = output_dir / "layout_WITH_PATCH.json"

import json

elements = []

# Use iterate_items() with proper coordinate conversion
for item, level in doc.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None

    if page_num is not None:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                if page_num in doc.pages:
                    page = doc.pages[page_num]
                    # KEY: Proper coordinate conversion to top-left origin
                    bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_dict = {
                        'x0': bbox_tl.l,
                        'y0': bbox_tl.t,
                        'x1': bbox_tl.r,
                        'y1': bbox_tl.b
                    }

        elements.append({
            'type': item.label.value if hasattr(item, 'label') else 'unknown',
            'text': item.text if hasattr(item, 'text') else '',
            'page': page_num,
            'bbox': bbox_dict
        })

json.dump({'elements': elements, 'total_elements': len(elements)},
          open(output_json, 'w'), indent=2, ensure_ascii=False)

print(f"✅ Saved: {output_json}")
print(f"📊 Total elements: {len(elements)}")

# Stats
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20}: {count:>4}")

print("\n" + "=" * 80)
print(f"✅ CHAPTER {N} EXTRACTION COMPLETE (WITH PATCH)")
print("=" * 80)
print(f"\n📁 Output: {output_json}")
print(f"🎨 Next step: python visualize_chapter{N}_WITH_PATCH.py")
print("=" * 80)
```

### 2. `visualize_chapter{N}_WITH_PATCH.py`

Visualization script that creates annotated PDF with bounding boxes.

**Template**:

```python
#!/usr/bin/env python3
"""
Create annotated PDF with ALL bounding boxes from Chapter {N} WITH PATCH
"""
import json
import fitz  # PyMuPDF
from pathlib import Path

# Color scheme (standard across all chapters)
COLORS = {
    "text": (0, 0, 1),
    "section_header": (1, 0, 0),
    "title": (1, 0, 0),
    "table": (0, 0.7, 0),
    "picture": (1, 0, 1),
    "formula": (1, 0.5, 0),
    "list_item": (0, 0.7, 0.7),
    "caption": (0.5, 0.5, 0),
    "page_header": (0.5, 0.5, 0.5),
    "page_footer": (0.5, 0.5, 0.5),
    "footnote": (0.7, 0.7, 0.7),
}

# Paths - ADJUST FOR EACH CHAPTER
json_path = Path(__file__).parent / f"capitulo_{N:02d}/outputs/layout_WITH_PATCH.json"
pdf_path = Path("/path/to/EAF-089-2025_capitulo_{N:02d}_pages_XXX-YYY.pdf")
output_pdf = Path(__file__).parent / f"capitulo_{N:02d}/outputs/chapter{N}_WITH_PATCH.pdf"

print("\n" + "█" * 80)
print(f"🎨 CREATING COMPLETE ANNOTATED PDF FOR CHAPTER {N} (WITH PATCH)")
print("█" * 80)
print(f"JSON: {json_path}")
print(f"PDF:  {pdf_path}")
print(f"Output: {output_pdf}")
print()

# Load JSON
print("📊 Loading extraction data...")
with open(json_path, 'r') as f:
    data = json.load(f)

elements = data['elements']
print(f"✅ Loaded {len(elements)} elements")

# Calculate statistics
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20}: {count:>4}")
print()

# Open PDF
print("📄 Opening PDF...")
doc = fitz.open(pdf_path)
print(f"✅ PDF has {len(doc)} pages")
print()

# Draw boxes
print("🎨 Drawing bounding boxes...")
boxes_drawn = 0
skipped_no_bbox = 0
skipped_out_of_range = 0

for element in elements:
    page_num = element.get('page')
    bbox = element.get('bbox')
    elem_type = element.get('type', 'unknown')

    if bbox is None or page_num is None:
        skipped_no_bbox += 1
        continue

    # Convert 1-based page number to 0-based index
    pdf_page_idx = page_num - 1

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        skipped_out_of_range += 1
        continue

    page = doc[pdf_page_idx]

    # Get color
    color = COLORS.get(elem_type, (0, 0, 1))

    # Draw rectangle
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=1)

    # Add small label (only for headers, titles, tables)
    if elem_type in ['section_header', 'title', 'table', 'picture', 'formula']:
        label = f"{elem_type}"
        text_point = fitz.Point(bbox['x0'], bbox['y0'] - 2)
        page.insert_text(text_point, label, fontsize=6, color=color)

    boxes_drawn += 1

print(f"📦 Drew {boxes_drawn} bounding boxes")
if skipped_no_bbox > 0:
    print(f"⚠️  Skipped {skipped_no_bbox} elements (no bbox)")
if skipped_out_of_range > 0:
    print(f"⚠️  Skipped {skipped_out_of_range} elements (out of page range)")
print()

# Add legend on first page
print("📝 Adding legend...")
page = doc[0]

legend_x = 450
legend_y = 700

# White background
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 120)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)

# Title
page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

# Element types
sorted_types = sorted(stats.items(), key=lambda x: x[1], reverse=True)

y_offset = legend_y + 15
for elem_type, count in sorted_types[:10]:
    color = COLORS.get(elem_type, (0, 0, 1))

    # Color box
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)

    # Text
    text = f"{elem_type}: {count}"
    page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=8, color=(0, 0, 0))

    y_offset += 10

print("✅ Legend added")
print()

# Save
print("💾 Saving annotated PDF...")
doc.save(output_pdf)
doc.close()

print(f"✅ Saved: {output_pdf}")
print()

print("=" * 80)
print(f"✅ COMPLETE ANNOTATED PDF CREATED FOR CHAPTER {N}")
print("=" * 80)
print(f"\n📁 Output: {output_pdf}")
print("=" * 80)
```

---

## Step-by-Step Process for New Chapter

### Prerequisites

1. **PDF file** for the chapter in `shared_platform/utils/outputs/claude_ocr/capitulo_{N:02d}/`
2. **EAF patch** directory at `shared_platform/utils/outputs/docling_layout/eaf_patch/`
3. **GPU with ≥4GB VRAM** (or CPU mode, 10x slower)

### Steps

1. **Create chapter directory**:
   ```bash
   mkdir -p shared_platform/utils/outputs/docling_layout/capitulo_{N:02d}/outputs
   ```

2. **Copy templates**:
   ```bash
   # Adjust chapter number and page ranges
   cp extract_chapter7_WITH_PATCH.py extract_chapter{N}_WITH_PATCH.py
   cp visualize_chapter7_WITH_PATCH.py visualize_chapter{N}_WITH_PATCH.py
   ```

3. **Edit extraction script**:
   - Update `pdf_path` with correct chapter number and page range
   - Update all `{N}` placeholders
   - Adjust estimated processing time (~2 minutes per 30 pages)

4. **Edit visualization script**:
   - Update `json_path`, `pdf_path`, `output_pdf` with correct chapter number
   - Update all `{N}` placeholders

5. **Run extraction**:
   ```bash
   python3 extract_chapter{N}_WITH_PATCH.py
   ```

6. **Create visualization**:
   ```bash
   python3 visualize_chapter{N}_WITH_PATCH.py
   ```

7. **Verify outputs**:
   - `capitulo_{N:02d}/outputs/layout_WITH_PATCH.json` - Extraction data
   - `capitulo_{N:02d}/outputs/chapter{N}_WITH_PATCH.pdf` - Annotated PDF

---

## File Naming Conventions

### Extraction Scripts
- **Pattern**: `extract_chapter{N}_WITH_PATCH.py`
- **Examples**: `extract_chapter2_WITH_PATCH.py`, `extract_chapter7_WITH_PATCH.py`

### Visualization Scripts
- **Pattern**: `visualize_chapter{N}_WITH_PATCH.py`
- **Examples**: `visualize_chapter2_WITH_PATCH.py`, `visualize_chapter7_WITH_PATCH.py`

### Output Files
- **JSON**: `capitulo_{N:02d}/outputs/layout_WITH_PATCH.json`
- **PDF**: `capitulo_{N:02d}/outputs/chapter{N}_WITH_PATCH.pdf`

### Deprecated Naming
- ❌ `layout_clean.json` → Use `layout_WITH_PATCH.json`
- ❌ `layout_clean_zona_fixed.json` → Zona fix is now automatic in patch
- ❌ Post-processing scripts → Use monkey patch instead

---

## Expected Patch Behavior per Page

The patch runs **once per page** during Docling's extraction pipeline:

```
Page 1:
  📄 [PATCH] Extracted X text lines from PDF
  📊 [PATCH] Docling has Y boxes (A clusters + B cells)
  📝 [PATCH] Found N missing titles
  ⚡ [PATCH] Found M power system list items
  ✅ [PATCH] Created N SECTION_HEADER clusters
  ✅ [PATCH] Created M LIST_ITEM clusters
```

**Good signs**:
- ✅ Patch runs on every page
- ✅ Missing titles detected and replaced with complete lines from PyMuPDF
- ✅ Power lines classified as `list_item`
- ✅ Final cluster count > Docling cluster count

**Bad signs**:
- ❌ Patch doesn't run (check if `apply_universal_patch_with_pdf()` was called)
- ❌ No clusters created (check PDF path is correct)
- ❌ Errors about missing modules (check `eaf_patch` directory in path)

---

## Troubleshooting

### Problem: "No module named 'core.eaf_patch_engine'"

**Solution**: Verify `eaf_patch` directory exists and path is added:
```python
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))
```

### Problem: Patch doesn't run (no "🐵 [PATCH]" messages)

**Solution**: Call `apply_universal_patch_with_pdf(pdf_path)` BEFORE creating `DocumentConverter`

### Problem: Page number mismatch (boxes on wrong pages)

**Solution**: JSON has 1-based page numbers, PDF uses 0-based indices:
```python
pdf_page_idx = page_num - 1  # Convert 1-based to 0-based
```

### Problem: GPU out of memory

**Solutions**:
1. Use lightweight mode (disable OCR, FAST tables)
2. Process one chapter at a time
3. Use CPU mode (add `--device cpu`, expect 10x slower)

### Problem: Zona items still misclassified

**Solution**: Ensure `apply_zona_fix_to_document(doc)` is called AFTER conversion completes

---

## Performance Estimates

| Pages | GPU (4GB+) | CPU Only |
|-------|-----------|----------|
| 30    | 2 min     | 20 min   |
| 50    | 3-4 min   | 35 min   |
| 80    | 5-7 min   | 60 min   |
| 100   | 7-9 min   | 75 min   |

**Note**: Times assume:
- OCR disabled
- Tables in FAST mode
- No cell matching (adds ~20% overhead)

---

## Batch Processing All Chapters

For batch processing chapters 2-11, use the batch script:

```bash
python3 BATCH_process_chapters_2_to_11.py
```

See `BATCH_PROCESSING_GUIDE.md` for details.

---

## Quality Assurance Checklist

After processing each chapter:

- [ ] JSON file created with `layout_WITH_PATCH.json` naming
- [ ] Annotated PDF created with all bounding boxes
- [ ] Patch ran on all pages (check logs for "🐵 [PATCH]")
- [ ] Chapter title detected and merged (e.g., "7." → "7. Análisis...")
- [ ] Zona items properly classified (isolated=header, sequential=list)
- [ ] Element counts match expectations (compare with Chapter 6/7)
- [ ] No errors in extraction logs
- [ ] Visual inspection of annotated PDF confirms correct box placement

---

## References

- **EAF Patch Engine**: `eaf_patch/core/eaf_patch_engine.py`
- **Chapter 6 Reference**: `extract_chapter6_patched_only.py` (original implementation)
- **Chapter 7 Reference**: `extract_chapter7_WITH_PATCH.py` (standardized template)
- **Docling Docs**: `README_DOCLING.md`
- **Methodology**: `docs/metodologia/DATA_FLOW.md`

---

**Version**: 1.0
**Created**: 2025-10-26
**Method**: EAF Monkey Patch (Method A)
