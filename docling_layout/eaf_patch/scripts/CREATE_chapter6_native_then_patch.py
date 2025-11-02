#!/usr/bin/env python3
"""
Create Chapter 6 visualization using native Docling coordinates + patch overlay
This matches the style of annotated_capitulo_01.pdf, annotated_capitulo_08.pdf, etc.

Step 1: Run Docling WITHOUT patch to get native layout_lightweight.json
Step 2: Identify patch additions from the patched JSON
Step 3: Create visualization with Docling boxes + RED patch overlays
"""
import json
import sys
from pathlib import Path

# Add eaf_patch to path (but DON'T apply patch yet!)
eaf_patch_path = Path(__file__).parent.parent
sys.path.insert(0, str(eaf_patch_path))

import fitz

# Paths
SPLIT_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
OUTPUT_DIR = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("🎨 CREATING CHAPTER 6 NATIVE DOCLING VISUALIZATION + PATCH OVERLAY")
print("=" * 80)
print(f"📄 PDF: {SPLIT_PDF.name}")
print(f"📁 Output: {OUTPUT_DIR}")
print("=" * 80)

# ============================================================================
# STEP 1: Run Docling WITHOUT Patch
# ============================================================================
print("\n🔍 Step 1: Running Docling (native, NO patch)...")

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
result = converter.convert(str(SPLIT_PDF))

print("✅ Docling processing complete (native mode)")

# ============================================================================
# STEP 2: Extract elements with Docling's NATIVE coordinates
# ============================================================================
print("\n📊 Step 2: Extracting elements with native Docling coordinates...")

elements = []
for item, level in result.document.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None

    if page_num:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                # Get page for coordinate conversion
                if page_num in result.document.pages:
                    page = result.document.pages[page_num]
                    # Use Docling's built-in conversion to top-left origin
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

        elements.append({
            'type': item.label,
            'text': text_content,
            'page': page_num,
            'bbox': bbox_dict,
            'page_dimensions': {'width': 612.0, 'height': 792.0}
        })

print(f"✅ Extracted {len(elements)} elements with native coordinates")

# Save native Docling JSON
json_output = OUTPUT_DIR / "layout_lightweight.json"
with open(json_output, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'chapter': 'Capítulo 6 - Normalización del Servicio',
            'extractor': 'Docling Native (no patch)',
            'total_elements': len(elements)
        },
        'elements': elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ Saved native Docling JSON: {json_output.name}")

# ============================================================================
# STEP 3: Load patched JSON to identify patch additions
# ============================================================================
print("\n🔴 Step 3: Loading patched JSON to identify patch additions...")

PATCHED_JSON = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs_with_eaf_patch" / "layout_with_eaf_patch.json"

if not PATCHED_JSON.exists():
    print(f"⚠️  Patched JSON not found: {PATCHED_JSON}")
    print("   Run REPROCESS_chapter6_with_universal_patch.py first!")
    sys.exit(1)

with open(PATCHED_JSON, 'r') as f:
    patched_data = json.load(f)

# Identify patch additions (short titles and power lines)
patch_additions = []
for elem in patched_data['elements']:
    text = elem.get('text', '').strip()
    elem_type = elem.get('type', '')

    is_patch = False
    if elem_type == 'section_header' and len(text) <= 5 and text:
        is_patch = True
    elif elem_type == 'list_item' and ('línea' in text.lower() or 'kv' in text.lower()):
        is_patch = True

    if is_patch:
        patch_additions.append(elem)

print(f"✅ Found {len(patch_additions)} patch additions")

# ============================================================================
# STEP 4: Create annotated PDF with native Docling + patch overlay
# ============================================================================
print("\n🎨 Step 4: Creating annotated PDF...")

doc = fitz.open(SPLIT_PDF)

# Color scheme (same as create_all_visualizations.py)
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

boxes_drawn = 0

# Draw native Docling boxes
for element in elements:
    if 'bbox' not in element or element['bbox'] is None:
        continue

    page_num = element['page']
    pdf_page_idx = page_num - 1  # Split PDF pages are 1-indexed

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue

    page = doc[pdf_page_idx]
    bbox = element['bbox']
    elem_type = element['type']

    color = COLORS.get(elem_type, (0, 0, 1))
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=2)
    boxes_drawn += 1

print(f"   🔵 Drew {boxes_drawn} native Docling boxes")

# Draw patch additions in THICK RED
# NOTE: Patch boxes also need coordinate conversion!
patch_boxes = 0
for elem in patch_additions:
    if 'bbox' not in elem or elem['bbox'] is None:
        continue

    page_num = elem['page']
    pdf_page_idx = page_num - 1

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue

    page = doc[pdf_page_idx]
    bbox = elem['bbox']

    # Convert patch bbox from bottom-left to top-left origin
    # Patch JSON uses: y0=bottom, y1=top (like Docling's raw coords)
    # PyMuPDF needs: y0=top (smaller), y1=bottom (larger)
    page_height = 792.0  # Standard US Letter
    rect = fitz.Rect(
        bbox['x0'],
        page_height - bbox['y1'],  # top: page_height - original_top
        bbox['x1'],
        page_height - bbox['y0']   # bottom: page_height - original_bottom
    )
    page.draw_rect(rect, color=(1, 0, 0), width=4)  # THICK RED
    patch_boxes += 1

print(f"   🔴 Drew {patch_boxes} patch addition overlays")

# Add legend
page = doc[0]
legend_x = 450
legend_y = 700

legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 100)
page.draw_rect(legend_rect, color=(1, 1, 1), fill=(1, 1, 1), width=1)
page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

y_offset = legend_y + 15
page.insert_text(fitz.Point(legend_x, y_offset), "Native Docling:", fontsize=8, color=(0, 0, 0))
y_offset += 12

type_counts = {}
for elem in elements:
    t = elem['type']
    type_counts[t] = type_counts.get(t, 0) + 1

sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
for elem_type, count in sorted_types[:5]:
    color = COLORS.get(elem_type, (0, 0, 1))
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)
    text = f"{elem_type}: {count}"
    page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=7, color=(0, 0, 0))
    y_offset += 10

y_offset += 5
patch_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
page.draw_rect(patch_rect, color=(1, 0, 0), width=4)
page.insert_text(fitz.Point(legend_x + 15, y_offset), f"Patch: {patch_boxes}", fontsize=7, color=(1, 0, 0))

# Save
output_pdf = OUTPUT_DIR / "annotated_capitulo_06.pdf"
doc.save(output_pdf)
doc.close()

print(f"✅ Saved: {output_pdf}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ VISUALIZATION COMPLETE")
print("=" * 80)
print(f"📊 Native Docling boxes: {boxes_drawn}")
print(f"🔴 Patch additions: {patch_boxes}")
print(f"📦 Total: {boxes_drawn + patch_boxes}")
print("\n📁 Files created:")
print(f"   1. {json_output.name} - Native Docling JSON")
print(f"   2. {output_pdf.name} - Annotated PDF with patch overlay")
print("=" * 80)
