#!/usr/bin/env python3
"""
Create Chapter 6 visualization: Native (thin boxes) + Patch (thick red boxes)
"""
import json
import fitz
from pathlib import Path
from datetime import datetime

# Paths
CHAPTER_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
OUTPUT_DIR = Path(__file__).parent / "capitulo_06" / "outputs"

print("🎨 Creating Chapter 6 Comparison Visualization...")

# Load JSONs
with open(OUTPUT_DIR / "layout_native.json") as f:
    native_data = json.load(f)
    native_elements = native_data['elements']

with open(OUTPUT_DIR / "layout_patched.json") as f:
    patched_data = json.load(f)
    patched_elements = patched_data['elements']

print(f"✅ Native: {len(native_elements)} elements")
print(f"✅ Patched: {len(patched_elements)} elements")

# Find additions
native_texts = {(e['text'].strip(), e['page']) for e in native_elements if e['text']}
patched_texts = {(e['text'].strip(), e['page']) for e in patched_elements if e['text']}
added_texts = patched_texts - native_texts

patch_additions = [e for e in patched_elements if (e['text'].strip(), e['page']) in added_texts]

print(f"🔴 Patch added: {len(patch_additions)} elements")

# Open PDF
doc = fitz.open(CHAPTER_PDF)

COLORS = {
    'text': (0, 0, 1),
    'section_header': (1, 0, 0),
    'title': (1, 0, 0),
    'table': (0, 0.7, 0),
    'picture': (1, 0, 1),
    'list_item': (0, 0.7, 0.7),
    'caption': (0.5, 0.5, 0),
    'page_header': (0.5, 0.5, 0.5),
    'page_footer': (0.5, 0.5, 0.5),
    'footnote': (0.8, 0.4, 0),
    'formula': (1, 0.5, 0),
}

# Draw native boxes (thin)
for elem in native_elements:
    if not elem.get('bbox'):
        continue
    page_num = elem['page'] - 1
    if page_num < 0 or page_num >= len(doc):
        continue
    page = doc[page_num]
    bbox = elem['bbox']
    color = COLORS.get(elem['type'], (0, 0, 1))
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=1.5)

print(f"✅ Drew {len(native_elements)} native boxes (thin)")

# Draw patch additions (THICK RED)
patch_boxes = 0
for elem in patch_additions:
    if not elem.get('bbox'):
        continue
    page_num = elem['page'] - 1
    if page_num < 0 or page_num >= len(doc):
        continue
    page = doc[page_num]
    bbox = elem['bbox']
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=(1, 0, 0), width=4)  # THICK RED
    patch_boxes += 1

print(f"✅ Drew {patch_boxes} patch additions (thick red)")

# Save
output_pdf = OUTPUT_DIR / "annotated_capitulo_06_COMPLETE.pdf"
doc.save(output_pdf)
doc.close()

print(f"✅ Saved: {output_pdf}")

# Generate report
report = f"""# Chapter 6 Extraction Comparison Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Chapter**: 6 - Normalización del Servicio
**Pages**: 172-265 (94 pages)

---

## 📊 Results

| Extraction Method | Elements | Change |
|-------------------|----------|--------|
| Native Docling | {len(native_elements)} | baseline |
| Docling + EAF Patch | {len(patched_elements)} | +{len(patch_additions)} ({((len(patch_additions)/len(native_elements))*100):.1f}%) |

---

## 🔴 Patch Additions ({len(patch_additions)} elements)

"""

for i, elem in enumerate(patch_additions, 1):
    text_preview = elem['text'][:100] + "..." if len(elem['text']) > 100 else elem['text']
    report += f"{i}. **[{elem['type']}]** Page {elem['page']}\n"
    report += f"   ```\n   {text_preview}\n   ```\n\n"

report += f"""---

## 📁 Output Files

1. `layout_native.json` - Native Docling ({len(native_elements)} elements)
2. `layout_patched.json` - With EAF Patch ({len(patched_elements)} elements)
3. `annotated_capitulo_06_COMPLETE.pdf` - Visualization
   - **Thin colored boxes**: Native Docling extraction
   - **Thick RED boxes**: Elements added by EAF Patch
4. `extraction_comparison_report.md` - This report

---

## 🎯 Summary

The EAF Patch successfully detected **{len(patch_additions)} additional elements** that native Docling missed:

- Uses PyMuPDF to extract ALL text from PDF
- Compares against Docling's bounding boxes
- Detects missing titles, power lines, and other elements
- Fixes AI misclassifications

**Improvement**: +{((len(patch_additions)/len(native_elements))*100):.1f}% more elements detected

---

**Status**: ✅ Complete
"""

report_file = OUTPUT_DIR / "extraction_comparison_report.md"
with open(report_file, 'w') as f:
    f.write(report)

print(f"✅ Saved: {report_file}")
print("\n" + "="*80)
print(f"✅ COMPLETE: {len(native_elements)} native + {len(patch_additions)} patch = {len(patched_elements)} total")
print("="*80)
