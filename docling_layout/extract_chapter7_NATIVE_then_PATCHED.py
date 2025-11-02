#!/usr/bin/env python3
"""
Chapter 7: Extract BOTH native + patched, then visualize the difference
EXACTLY like Chapter 6 methodology
"""
import json
import sys
from pathlib import Path
from datetime import datetime

import fitz

# Paths
CHAPTER_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf")
OUTPUT_DIR = Path(__file__).parent / "capitulo_07" / "outputs"

print("=" * 80)
print("🎯 CHAPTER 7: Native + Patched Extraction (Like Chapter 6)")
print("=" * 80)

# ============================================================================
# STEP 1: Run Native Docling (NO PATCH)
# ============================================================================
print("\n🔵 Step 1: Running NATIVE Docling (no patch)...")
print("-" * 80)

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

converter_native = DocumentConverter(format_options=format_options)
result_native = converter_native.convert(str(CHAPTER_PDF))

print("✅ Native Docling complete")

# Extract native elements
native_elements = []
for item, level in result_native.document.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None

    if page_num:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                if page_num in result_native.document.pages:
                    page = result_native.document.pages[page_num]
                    bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_dict = {
                        'x0': bbox_tl.l,
                        'y0': bbox_tl.t,
                        'x1': bbox_tl.r,
                        'y1': bbox_tl.b
                    }

        native_elements.append({
            'type': item.label,
            'text': item.text if hasattr(item, 'text') else str(item),
            'page': page_num,
            'bbox': bbox_dict
        })

print(f"✅ Native extraction: {len(native_elements)} elements")

# Save native JSON
native_json = OUTPUT_DIR / "layout_native.json"
with open(native_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'chapter': 'Capítulo 7 - Análisis de las causas de la falla',
            'extractor': 'Docling Native',
            'extraction_date': datetime.now().isoformat(),
            'total_elements': len(native_elements)
        },
        'elements': native_elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {native_json.name}")

# ============================================================================
# STEP 2: Run Patched Docling
# ============================================================================
print("\n🔴 Step 2: Running PATCHED Docling...")
print("-" * 80)

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Apply patch
apply_universal_patch_with_pdf(str(CHAPTER_PDF))

# Run patched extraction
converter_patched = DocumentConverter(format_options=format_options)
result_patched = converter_patched.convert(str(CHAPTER_PDF))

print("✅ Patched Docling complete")

# Extract patched elements
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

        patched_elements.append({
            'type': item.label,
            'text': item.text if hasattr(item, 'text') else str(item),
            'page': page_num,
            'bbox': bbox_dict
        })

print(f"✅ Patched extraction: {len(patched_elements)} elements")

# Save patched JSON
patched_json = OUTPUT_DIR / "layout_patched.json"
with open(patched_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'chapter': 'Capítulo 7 - Análisis de las causas de la falla',
            'extractor': 'Docling + EAF Patch v2.0',
            'extraction_date': datetime.now().isoformat(),
            'total_elements': len(patched_elements)
        },
        'elements': patched_elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {patched_json.name}")

# ============================================================================
# STEP 3: Identify What Patch Added
# ============================================================================
print("\n🔍 Step 3: Analyzing patch additions...")
print("-" * 80)

native_texts = {(e['text'].strip(), e['page']) for e in native_elements if e['text']}
patched_texts = {(e['text'].strip(), e['page']) for e in patched_elements if e['text']}
added_texts = patched_texts - native_texts

patch_additions = []
for elem in patched_elements:
    text = elem['text'].strip()
    page = elem['page']
    if (text, page) in added_texts:
        patch_additions.append(elem)

print(f"✅ Native: {len(native_elements)} elements")
print(f"✅ Patched: {len(patched_elements)} elements")
print(f"🔴 Patch added: {len(patch_additions)} NEW elements")

# Show first 10 additions
if patch_additions:
    print("\n📋 First 10 patch additions:")
    for i, elem in enumerate(patch_additions[:10], 1):
        text_preview = elem['text'][:60] + "..." if len(elem['text']) > 60 else elem['text']
        print(f"   {i}. [{elem['type']}] Page {elem['page']}: {text_preview}")

# ============================================================================
# STEP 4: Create Layered Visualization
# ============================================================================
print("\n🎨 Step 4: Creating layered visualization...")
print("-" * 80)

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

# Layer 1: Draw NATIVE boxes (THIN lines)
print("   📦 Drawing native boxes (thin)...")
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
    color = COLORS.get(element['type'], (0, 0, 1))
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=1.5)
    native_boxes += 1

print(f"   ✅ Drew {native_boxes} native boxes (thin)")

# Layer 2: Draw PATCH ADDITIONS ONLY (THICK RED)
print("   🔴 Drawing patch additions (thick red)...")
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

print(f"   ✅ Drew {patch_boxes} patch additions (thick red)")

# Add legend
page = doc[0]
legend_x = 450
legend_y = 650
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 100)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

y_offset = legend_y + 15
page.insert_text(fitz.Point(legend_x, y_offset), "Native (thin):", fontsize=8, color=(0, 0, 0))
y_offset += 12

native_counts = {}
for e in native_elements:
    t = e['type']
    native_counts[t] = native_counts.get(t, 0) + 1

for elem_type, count in sorted(native_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
    color = COLORS.get(elem_type, (0, 0, 1))
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)
    page.insert_text(fitz.Point(legend_x + 15, y_offset), f"{elem_type}: {count}", fontsize=7, color=(0, 0, 0))
    y_offset += 10

y_offset += 5
page.insert_text(fitz.Point(legend_x, y_offset), "Patch (thick):", fontsize=8, color=(0, 0, 0))
y_offset += 12
patch_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
page.draw_rect(patch_rect, color=(1, 0, 0), width=4)
page.insert_text(fitz.Point(legend_x + 15, y_offset), f"Added: {patch_boxes}", fontsize=7, color=(1, 0, 0))

output_pdf = OUTPUT_DIR / "annotated_capitulo_07_COMPLETE.pdf"
doc.save(output_pdf)
doc.close()

print(f"✅ Saved: {output_pdf.name}")

print("\n" + "=" * 80)
print("✅ CHAPTER 7 COMPLETE (Like Chapter 6)")
print("=" * 80)
print(f"🔵 Native: {len(native_elements)} elements")
print(f"🔴 Patch added: {len(patch_additions)} elements")
print(f"📦 Total: {len(patched_elements)} elements")
print("\n📁 Files:")
print(f"   - layout_native.json")
print(f"   - layout_patched.json")
print(f"   - annotated_capitulo_07_COMPLETE.pdf (layered visualization)")
print("=" * 80)
