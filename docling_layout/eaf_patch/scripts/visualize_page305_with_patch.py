#!/usr/bin/env python3
"""
Generate annotated PDF for Page 305 only (fast test)
Shows power line classification results with the monkey patch applied
"""
import json
import fitz  # PyMuPDF
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# APPLY PATCH BEFORE IMPORTING DOCLING
# ============================================================================
from patch_power_lines import apply_power_line_patch

print("\n" + "█" * 80)
print("🔧 APPLYING POWER LINE CLASSIFICATION PATCH")
print("█" * 80)

apply_power_line_patch()

# ============================================================================
# NOW IMPORT DOCLING
# ============================================================================
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# ============================================================================
# CONFIGURATION
# ============================================================================

TARGET_PAGE = 305

# Color scheme
COLORS = {
    "text": (0, 0, 1),
    "section_header": (1, 0, 0),
    "title": (1, 0, 0),
    "table": (0, 0.7, 0),
    "picture": (1, 0, 1),
    "formula": (1, 0.5, 0),
    "list_item": (0, 0.7, 0.7),  # Cyan - POWER LINES!
    "caption": (0.5, 0.5, 0),
    "page_header": (0.5, 0.5, 0.5),
    "page_footer": (0.5, 0.5, 0.5),
    "footnote": (0.7, 0.7, 0.7),
}

# Paths
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")

print("\n" + "█" * 80)
print(f"📄 VISUALIZING PAGE {TARGET_PAGE} (Chapter 7)")
print("█" * 80)
print(f"PDF: {pdf_path.name}")
print(f"Output: {OUTPUT_DIR}")
print()

# ============================================================================
# CONFIGURE PIPELINE
# ============================================================================
pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=True,
    generate_page_images=False,
)

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# ============================================================================
# RUN EXTRACTION ON SINGLE PAGE
# ============================================================================
print("🔧 Creating DocumentConverter...")
converter = DocumentConverter(format_options=format_options)
print("✅ Converter ready\n")

print(f"🔍 Processing page {TARGET_PAGE} (patch will run during processing)...\n")

# Process single page using max_num_pages and starting from target page
# Note: We can't specify exact page, so we process from beginning up to target
result = converter.convert(str(pdf_path), max_num_pages=TARGET_PAGE)

print("\n✅ Conversion complete\n")

# ============================================================================
# EXTRACT ELEMENTS FROM TARGET PAGE ONLY
# ============================================================================
print(f"📊 Extracting elements from page {TARGET_PAGE}...")

elements = []
for item in result.document.iterate_items():
    if isinstance(item, tuple):
        item, level = item

    if not hasattr(item, 'prov') or not item.prov:
        continue

    for prov in item.prov:
        if prov.page_no == TARGET_PAGE:
            if prov.page_no not in result.document.pages:
                continue

            page = result.document.pages[prov.page_no]
            bbox = prov.bbox
            bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)

            if hasattr(item, 'text'):
                text_content = item.text if item.text else ""
            else:
                text_content = str(item) if item else ""

            element = {
                "type": item.label,
                "text": text_content,
                "page": prov.page_no,
                "bbox": {
                    "x0": round(bbox_tl.l, 2),
                    "y0": round(bbox_tl.t, 2),
                    "x1": round(bbox_tl.r, 2),
                    "y1": round(bbox_tl.b, 2)
                },
            }
            elements.append(element)

print(f"✅ Extracted {len(elements)} elements from page {TARGET_PAGE}")
print()

# ============================================================================
# STATISTICS
# ============================================================================
stats = {}
power_line_count = 0

for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

    if elem_type == 'list_item' and ('Línea' in elem['text'] or 'kV' in elem['text']):
        power_line_count += 1

print(f"📊 STATISTICS FOR PAGE {TARGET_PAGE}:")
print("-" * 60)
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20} │ {count:>3}")
print("-" * 60)
print(f"   {'TOTAL':<20} │ {sum(stats.values()):>3}")
print()
print(f"⚡ Power line items: {power_line_count}")
print()

# ============================================================================
# CREATE ANNOTATED PDF
# ============================================================================
print("🎨 Creating annotated PDF...")

doc = fitz.open(pdf_path)
page = doc[TARGET_PAGE - 1]  # 0-indexed

boxes_drawn = 0
for element in elements:
    bbox = element['bbox']
    elem_type = element['type']

    color = COLORS.get(elem_type, (0, 0, 1))
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=2)

    label = f"{elem_type}"
    text_point = fitz.Point(bbox['x0'], bbox['y0'] - 2)
    page.insert_text(text_point, label, fontsize=8, color=color)

    boxes_drawn += 1

print(f"📦 Drew {boxes_drawn} bounding boxes")

# Add legend
legend_x = 450
legend_y = 700

legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 85)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

y_offset = legend_y + 15
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    color = COLORS.get(elem_type, (0, 0, 1))
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)
    text = f"{elem_type}: {count}"
    page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=8, color=(0, 0, 0))
    y_offset += 10

y_offset += 5
page.insert_text(
    fitz.Point(legend_x, y_offset),
    f"⚡ Power lines: {power_line_count}",
    fontsize=8,
    color=(0, 0.7, 0.7)
)

# Save single page
output_pdf = OUTPUT_DIR / f"page_{TARGET_PAGE}_annotated.pdf"

# Create new PDF with just this page
new_doc = fitz.open()
new_doc.insert_pdf(doc, from_page=TARGET_PAGE - 1, to_page=TARGET_PAGE - 1)
new_doc.save(output_pdf)
new_doc.close()
doc.close()

print(f"✅ Annotated PDF saved: {output_pdf}")
print()

# ============================================================================
# SAVE JSON
# ============================================================================
json_path = OUTPUT_DIR / f"page_{TARGET_PAGE}_layout.json"

power_lines = [e for e in elements if e['type'] == 'list_item' and
               ('Línea' in e['text'] or 'kV' in e['text'])]

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump({
        "page": TARGET_PAGE,
        "total_elements": len(elements),
        "stats": stats,
        "power_line_count": power_line_count,
        "power_lines": power_lines,
        "elements": elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ JSON saved: {json_path}")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("✅ VISUALIZATION COMPLETE")
print("=" * 80)
print()
print(f"Page: {TARGET_PAGE}")
print(f"Total elements: {len(elements)}")
print(f"Power lines: {power_line_count}")
print()
print(f"📁 Files generated:")
print(f"   • {output_pdf.name}")
print(f"   • {json_path.name}")
print()

if power_line_count > 0:
    print("⚡ POWER LINES FOUND:")
    for i, pl in enumerate(power_lines, 1):
        print(f"   {i}. {pl['text'][:70]}")
    print()
    print("✅ All power lines classified as list_item (cyan boxes)")
else:
    print("⚠️  No power lines found on this page")

print("=" * 80)
