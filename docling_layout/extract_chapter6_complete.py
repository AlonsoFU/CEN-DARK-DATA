#!/usr/bin/env python3
"""
Complete Chapter 6 Extraction with Native Docling + EAF Patch
Generates visualization showing base Docling boxes + RED patch overlays

Output:
1. layout_native.json - Native Docling extraction
2. layout_patched.json - With EAF patch applied
3. annotated_capitulo_06_COMPLETE.pdf - Visual comparison
4. extraction_comparison_report.md - Detailed analysis
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

import fitz

# Paths
CHAPTER_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
OUTPUT_DIR = Path(__file__).parent / "capitulo_06" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("🎯 CHAPTER 6 COMPLETE EXTRACTION: Native Docling + EAF Patch")
print("=" * 80)
print(f"📄 PDF: {CHAPTER_PDF.name}")
print(f"📁 Output: {OUTPUT_DIR}")
print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# ============================================================================
# STEP 1: Run Native Docling (NO PATCH)
# ============================================================================
print("\n🔵 STEP 1: Running Native Docling (no patch)...")
print("-" * 80)

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Configure lightweight processing
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(CHAPTER_PDF))

print("✅ Native Docling processing complete")

# Extract elements with native coordinates
native_elements = []
for item, level in result.document.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None

    if page_num:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                if page_num in result.document.pages:
                    page = result.document.pages[page_num]
                    bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_dict = {
                        'x0': bbox_tl.l,
                        'y0': bbox_tl.t,
                        'x1': bbox_tl.r,
                        'y1': bbox_tl.b
                    }

        text_content = ""
        if hasattr(item, 'text'):
            text_content = item.text
        elif hasattr(item, 'export_to_markdown'):
            text_content = item.export_to_markdown()
        else:
            text_content = str(item)

        native_elements.append({
            'type': item.label,
            'text': text_content,
            'page': page_num,
            'bbox': bbox_dict
        })

print(f"✅ Native extraction: {len(native_elements)} elements")

# Count by type
native_counts = {}
for elem in native_elements:
    t = elem['type']
    native_counts[t] = native_counts.get(t, 0) + 1

print("\nNative element breakdown:")
for elem_type, count in sorted(native_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:20s}: {count:4d}")

# Save native JSON
native_json = OUTPUT_DIR / "layout_native.json"
with open(native_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'chapter': 'Capítulo 6 - Normalización del Servicio',
            'extractor': 'Docling Native (no patch)',
            'extraction_date': datetime.now().isoformat(),
            'total_elements': len(native_elements)
        },
        'elements': native_elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {native_json.name}")

# ============================================================================
# STEP 2: Run Docling WITH EAF Patch
# ============================================================================
print("\n🔴 STEP 2: Running Docling WITH EAF Patch...")
print("-" * 80)

# Import and apply patch
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Apply patch (also sets PDF path internally)
apply_universal_patch_with_pdf(str(CHAPTER_PDF))

# Create new converter (patch is now active)
converter_patched = DocumentConverter(format_options=format_options)
result_patched = converter_patched.convert(str(CHAPTER_PDF))

print("✅ Patched Docling processing complete")

# Extract elements from patched result
patched_elements = []
for item, level in result_patched.document.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None

    if page_num:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                if page_num in result_patched.document.pages:
                    page = result_patched.document.pages[page_num]
                    bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_dict = {
                        'x0': bbox_tl.l,
                        'y0': bbox_tl.t,
                        'x1': bbox_tl.r,
                        'y1': bbox_tl.b
                    }

        text_content = ""
        if hasattr(item, 'text'):
            text_content = item.text
        elif hasattr(item, 'export_to_markdown'):
            text_content = item.export_to_markdown()
        else:
            text_content = str(item)

        patched_elements.append({
            'type': item.label,
            'text': text_content,
            'page': page_num,
            'bbox': bbox_dict
        })

print(f"✅ Patched extraction: {len(patched_elements)} elements")

# Count by type
patched_counts = {}
for elem in patched_elements:
    t = elem['type']
    patched_counts[t] = patched_counts.get(t, 0) + 1

print("\nPatched element breakdown:")
for elem_type, count in sorted(patched_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:20s}: {count:4d}")

# Save patched JSON
patched_json = OUTPUT_DIR / "layout_patched.json"
with open(patched_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'chapter': 'Capítulo 6 - Normalización del Servicio',
            'extractor': 'Docling + EAF Patch v2.0',
            'extraction_date': datetime.now().isoformat(),
            'total_elements': len(patched_elements)
        },
        'elements': patched_elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {patched_json.name}")

# ============================================================================
# STEP 3: Identify Patch Additions
# ============================================================================
print("\n🔍 STEP 3: Analyzing patch additions...")
print("-" * 80)

# Compare native vs patched to find additions
native_texts = {(e['text'].strip(), e['page']) for e in native_elements if e['text']}
patched_texts = {(e['text'].strip(), e['page']) for e in patched_elements if e['text']}

added_texts = patched_texts - native_texts

# Find added elements
patch_additions = []
for elem in patched_elements:
    text = elem['text'].strip()
    page = elem['page']
    if (text, page) in added_texts:
        patch_additions.append(elem)

print(f"✅ Patch added {len(patch_additions)} new elements")

if patch_additions:
    print("\nPatch additions:")
    for i, elem in enumerate(patch_additions[:10], 1):  # Show first 10
        text_preview = elem['text'][:60] + "..." if len(elem['text']) > 60 else elem['text']
        print(f"   {i}. [{elem['type']}] Page {elem['page']}: {text_preview}")
    if len(patch_additions) > 10:
        print(f"   ... and {len(patch_additions) - 10} more")

# ============================================================================
# STEP 4: Create Visualization
# ============================================================================
print("\n🎨 STEP 4: Creating annotated PDF...")
print("-" * 80)

doc = fitz.open(CHAPTER_PDF)

# Color scheme
COLORS = {
    'text': (0, 0, 1),              # Blue
    'section_header': (1, 0, 0),    # Red
    'title': (1, 0, 0),             # Red
    'table': (0, 0.7, 0),           # Green
    'picture': (1, 0, 1),           # Magenta
    'list_item': (0, 0.7, 0.7),     # Cyan
    'caption': (0.5, 0.5, 0),       # Olive
    'page_header': (0.5, 0.5, 0.5), # Gray
    'page_footer': (0.5, 0.5, 0.5), # Gray
    'footnote': (0.8, 0.4, 0),      # Orange
    'formula': (1, 0.5, 0),         # Light orange
}

# Draw native Docling boxes (thin lines)
native_boxes = 0
for element in native_elements:
    if not element.get('bbox'):
        continue

    page_num = element['page']
    pdf_page_idx = page_num - 1

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue

    page = doc[pdf_page_idx]
    bbox = element['bbox']
    elem_type = element['type']

    color = COLORS.get(elem_type, (0, 0, 1))
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=1.5)  # Thin lines
    native_boxes += 1

print(f"   🔵 Drew {native_boxes} native Docling boxes (thin)")

# Draw patch additions (THICK RED)
patch_boxes = 0
for elem in patch_additions:
    if not elem.get('bbox'):
        continue

    page_num = elem['page']
    pdf_page_idx = page_num - 1

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue

    page = doc[pdf_page_idx]
    bbox = elem['bbox']

    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=(1, 0, 0), width=4)  # THICK RED
    patch_boxes += 1

print(f"   🔴 Drew {patch_boxes} patch additions (thick red)")

# Add legend on first page
page = doc[0]
legend_x = 450
legend_y = 650

# White background
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 120)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)

# Title
page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0), fontname="helv-bold")

# Native boxes
y_offset = legend_y + 15
page.insert_text(fitz.Point(legend_x, y_offset), "Native Docling (thin):", fontsize=8, color=(0, 0, 0))
y_offset += 12

for elem_type, count in sorted(native_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
    color = COLORS.get(elem_type, (0, 0, 1))
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)
    text = f"{elem_type}: {count}"
    page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=7, color=(0, 0, 0))
    y_offset += 10

# Patch additions
y_offset += 5
page.insert_text(fitz.Point(legend_x, y_offset), "Patch Additions (thick):", fontsize=8, color=(0, 0, 0))
y_offset += 12

patch_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
page.draw_rect(patch_rect, color=(1, 0, 0), width=4)
page.insert_text(fitz.Point(legend_x + 15, y_offset), f"Added: {patch_boxes}", fontsize=7, color=(1, 0, 0))

# Save PDF
output_pdf = OUTPUT_DIR / "annotated_capitulo_06_COMPLETE.pdf"
doc.save(output_pdf)
doc.close()

print(f"✅ Saved: {output_pdf.name}")

# ============================================================================
# STEP 5: Generate Comparison Report
# ============================================================================
print("\n📊 STEP 5: Generating comparison report...")
print("-" * 80)

report = f"""# Chapter 6 Extraction Comparison Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Chapter**: 6 - Normalización del Servicio
**PDF**: {CHAPTER_PDF.name}
**Pages**: 172-265 (94 pages)

---

## 📊 Extraction Statistics

### Native Docling (No Patch)
**Total Elements**: {len(native_elements)}

| Element Type | Count | Percentage |
|-------------|-------|------------|
"""

for elem_type, count in sorted(native_counts.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(native_elements)) * 100
    report += f"| {elem_type} | {count} | {pct:.1f}% |\n"

report += f"""
### Docling + EAF Patch
**Total Elements**: {len(patched_elements)}

| Element Type | Count | Percentage |
|-------------|-------|------------|
"""

for elem_type, count in sorted(patched_counts.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(patched_elements)) * 100
    report += f"| {elem_type} | {count} | {pct:.1f}% |\n"

report += f"""
---

## 🔴 Patch Additions

**Elements Added by Patch**: {len(patch_additions)}

"""

if patch_additions:
    report += "### Details\n\n"
    for i, elem in enumerate(patch_additions, 1):
        text_preview = elem['text'][:80] + "..." if len(elem['text']) > 80 else elem['text']
        report += f"{i}. **[{elem['type']}]** Page {elem['page']}\n"
        report += f"   ```\n   {text_preview}\n   ```\n"
        if elem.get('bbox'):
            bbox = elem['bbox']
            report += f"   BBox: ({bbox['x0']:.1f}, {bbox['y0']:.1f}) → ({bbox['x1']:.1f}, {bbox['y1']:.1f})\n\n"

report += f"""
---

## 📈 Comparison Summary

| Metric | Native | Patched | Difference |
|--------|--------|---------|------------|
| Total Elements | {len(native_elements)} | {len(patched_elements)} | +{len(patched_elements) - len(native_elements)} |
| Boxes Drawn | {native_boxes} | {native_boxes + patch_boxes} | +{patch_boxes} |

---

## 📁 Output Files

1. **`layout_native.json`** - Native Docling extraction ({len(native_elements)} elements)
2. **`layout_patched.json`** - With EAF patch ({len(patched_elements)} elements)
3. **`annotated_capitulo_06_COMPLETE.pdf`** - Visual comparison
   - Thin colored boxes: Native Docling
   - Thick red boxes: Patch additions
4. **`extraction_comparison_report.md`** - This report

---

## 🎯 Key Findings

- Native Docling extracted **{len(native_elements)}** elements
- EAF Patch added **{len(patch_additions)}** missing elements
- Total improvement: **{((len(patch_additions) / len(native_elements)) * 100):.1f}%** more elements detected

### What the Patch Fixed

The EAF Patch uses PyMuPDF to extract ALL text from PDF and compares against
Docling's bounding boxes to identify missing elements. It specifically detects:

1. **Short titles** (e.g., "6.", "a.") that Docling filters out
2. **Power system elements** (e.g., "Línea 220 kV") that AI misclassifies
3. **Page numbers and headers/footers** that Docling ignores
4. **Complete text lines** instead of fragmented spans

---

**Processing Status**: ✅ Complete
**Methodology**: Hybrid (AI Layout Analysis + Direct PDF Extraction + Domain Rules)
**Accuracy**: Native baseline + {len(patch_additions)} additional elements = Enhanced coverage
"""

report_file = OUTPUT_DIR / "extraction_comparison_report.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"✅ Saved: {report_file.name}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ CHAPTER 6 EXTRACTION COMPLETE")
print("=" * 80)
print(f"🔵 Native Docling: {len(native_elements)} elements")
print(f"🔴 EAF Patch Added: {len(patch_additions)} elements")
print(f"📦 Total: {len(patched_elements)} elements")
print(f"📈 Improvement: +{((len(patch_additions) / len(native_elements)) * 100):.1f}%")
print("\n📁 Files created in: {OUTPUT_DIR}")
print(f"   1. {native_json.name}")
print(f"   2. {patched_json.name}")
print(f"   3. {output_pdf.name}")
print(f"   4. {report_file.name}")
print("=" * 80)
print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
