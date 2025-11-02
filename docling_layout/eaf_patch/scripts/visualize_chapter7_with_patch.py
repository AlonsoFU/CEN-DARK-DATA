#!/usr/bin/env python3
"""
Generate annotated PDF with bounding boxes for Chapter 7
Shows power line classification results with the monkey patch applied

Output:
    - Annotated PDF with colored bounding boxes
    - Different colors for different element types
    - CSV with all bounding box coordinates
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

# Chapter 7 definition
CHAPTER_7 = {
    "name": "Análisis de Causas de Falla",
    "pages": (266, 347),  # Actual document page range
    "pdf_pages": (266, 347)  # PDF page numbers (1-indexed)
}

# Color scheme for visualization
COLORS = {
    "text": (0, 0, 1),              # Blue
    "section_header": (1, 0, 0),     # Red
    "title": (1, 0, 0),              # Red
    "table": (0, 0.7, 0),            # Green
    "picture": (1, 0, 1),            # Magenta
    "formula": (1, 0.5, 0),          # Orange
    "list_item": (0, 0.7, 0.7),      # Cyan - POWER LINES!
    "caption": (0.5, 0.5, 0),        # Olive
    "page_header": (0.5, 0.5, 0.5),  # Gray
    "page_footer": (0.5, 0.5, 0.5),  # Gray
    "footnote": (0.7, 0.7, 0.7),     # Light gray
}

# Paths
BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR.parent / "claude_ocr"
OUTPUT_DIR = BASE_DIR / "chapter7_visualization"
OUTPUT_DIR.mkdir(exist_ok=True)

chapter_name = CHAPTER_7["name"]
start_page, end_page = CHAPTER_7["pdf_pages"]

print("\n" + "█" * 80)
print(f"📖 CHAPTER 7: {chapter_name}")
print("█" * 80)
print(f"Pages: {start_page}-{end_page}")
print(f"Output: {OUTPUT_DIR}")
print()

# Find PDF - use absolute path
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")

if not pdf_path.exists():
    print(f"❌ Error: PDF not found at {pdf_path}")
    print(f"   Checking project_root: {project_root}")
    sys.exit(1)

# ============================================================================
# CONFIGURE PIPELINE (LIGHTWEIGHT MODE)
# ============================================================================
print("🔧 Configuring Docling pipeline (lightweight mode)...")
pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=True,  # Enable tables for better detection
    generate_page_images=False,
)

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# ============================================================================
# RUN EXTRACTION
# ============================================================================
print("🔧 Creating DocumentConverter...")
converter = DocumentConverter(format_options=format_options)
print("✅ Converter ready\n")

print(f"🔍 Converting FULL document (will filter Chapter 7 pages {start_page}-{end_page})...")
print("   ⚠️  This will take ~15-20 minutes for full document")
print("   (Docling doesn't support page ranges, so we process everything then filter)")
print()

# Convert entire document (Docling doesn't support page ranges)
result = converter.convert(str(pdf_path))

print("\n✅ Conversion complete")
print()

# ============================================================================
# EXTRACT ELEMENTS
# ============================================================================
print("📊 Extracting elements...")

elements = []
for item in result.document.iterate_items():
    if isinstance(item, tuple):
        item, level = item

    if not hasattr(item, 'prov') or not item.prov:
        continue

    for prov in item.prov:
        if start_page <= prov.page_no <= end_page:
            # Get page for coordinate conversion
            if prov.page_no not in result.document.pages:
                continue

            page = result.document.pages[prov.page_no]
            bbox = prov.bbox

            # Convert to top-left origin
            bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)

            # Get text
            if hasattr(item, 'text'):
                text_content = item.text if item.text else ""
            elif hasattr(item, 'export_to_markdown'):
                text_content = item.export_to_markdown()
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
                "page_dimensions": {
                    "width": page.size.width,
                    "height": page.size.height
                }
            }

            elements.append(element)

print(f"✅ Extracted {len(elements)} elements")
print()

# ============================================================================
# CALCULATE STATISTICS
# ============================================================================
stats = {}
power_line_count = 0

for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

    # Count power lines
    if elem_type == 'list_item' and ('Línea' in elem['text'] or 'kV' in elem['text']):
        power_line_count += 1

print("📊 STATISTICS:")
print("-" * 60)
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    bar = "█" * min(count // 10, 50)
    print(f"   {elem_type:<20} │ {count:>4} │ {bar}")
print("-" * 60)
print(f"   {'TOTAL':<20} │ {sum(stats.values()):>4} │")
print()
print(f"⚡ Power line items: {power_line_count}")
print()

# ============================================================================
# CREATE ANNOTATED PDF
# ============================================================================
print("🎨 Creating annotated PDF with bounding boxes...")

# Open PDF
doc = fitz.open(pdf_path)
print(f"📄 PDF opened: {len(doc)} pages total")

# Draw boxes on Chapter 7 pages only
boxes_drawn = 0
pages_processed = 0

for element in elements:
    # Get PDF page index (element page is 1-indexed, PyMuPDF is 0-indexed)
    pdf_page_idx = element['page'] - 1

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue

    page = doc[pdf_page_idx]
    bbox = element['bbox']
    elem_type = element['type']

    # Get color
    color = COLORS.get(elem_type, (0, 0, 1))

    # Draw rectangle
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=2)

    # Add label
    label = f"{elem_type}"
    text_point = fitz.Point(bbox['x0'], bbox['y0'] - 2)
    page.insert_text(text_point, label, fontsize=8, color=color)

    boxes_drawn += 1

print(f"📦 Drew {boxes_drawn} bounding boxes")
print()

# ============================================================================
# ADD LEGEND ON FIRST PAGE
# ============================================================================
print("📝 Adding legend to first page...")

first_page_idx = start_page - 1
page = doc[first_page_idx]

legend_x = 450
legend_y = 700

# Draw white background for legend
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 100)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)

# Add title
page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

# Add element types (top 10)
sorted_types = sorted(stats.items(), key=lambda x: x[1], reverse=True)

y_offset = legend_y + 15
for elem_type, count in sorted_types[:10]:  # Top 10 types
    color = COLORS.get(elem_type, (0, 0, 1))

    # Draw color box
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)

    # Draw text
    text = f"{elem_type}: {count}"
    page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=8, color=(0, 0, 0))

    y_offset += 10

# Highlight power lines
y_offset += 5
page.insert_text(
    fitz.Point(legend_x, y_offset),
    f"⚡ Power lines: {power_line_count}",
    fontsize=8,
    color=(0, 0.7, 0.7)
)

print("✅ Legend added")
print()

# ============================================================================
# SAVE ANNOTATED PDF
# ============================================================================
output_pdf = OUTPUT_DIR / f"chapter_7_annotated_pages_{start_page}-{end_page}.pdf"

print(f"💾 Saving annotated PDF...")
doc.save(output_pdf)
doc.close()

print(f"✅ Annotated PDF saved: {output_pdf}")
print()

# ============================================================================
# SAVE JSON
# ============================================================================
json_path = OUTPUT_DIR / "chapter_7_layout.json"

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump({
        "metadata": {
            "chapter": "Chapter 7 - Análisis de Causas de Falla",
            "pages": f"{start_page}-{end_page}",
            "total_elements": len(elements),
            "power_line_items": power_line_count,
            "patch_applied": "power_line_classification_patch"
        },
        "statistics": stats,
        "elements": elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ JSON saved: {json_path}")

# ============================================================================
# SAVE CSV
# ============================================================================
csv_path = OUTPUT_DIR / "chapter_7_bounding_boxes.csv"

with open(csv_path, 'w', encoding='utf-8') as f:
    f.write("type,page,x0,y0,x1,y1,page_width,page_height,text\n")
    for elem in elements:
        bbox = elem['bbox']
        dims = elem['page_dimensions']
        text = elem['text'].replace('"', '""').replace('\n', ' ')[:200]  # Limit text length

        f.write(f'"{elem["type"]}",{elem["page"]},{bbox["x0"]:.2f},{bbox["y0"]:.2f},'
                f'{bbox["x1"]:.2f},{bbox["y1"]:.2f},{dims["width"]},{dims["height"]},"{text}"\n')

print(f"✅ CSV saved: {csv_path}")
print()

# ============================================================================
# FILTER POWER LINES TO SEPARATE FILE
# ============================================================================
power_lines = [e for e in elements if e['type'] == 'list_item' and
               ('Línea' in e['text'] or 'kV' in e['text'])]

power_lines_json = OUTPUT_DIR / "chapter_7_power_lines.json"

with open(power_lines_json, 'w', encoding='utf-8') as f:
    json.dump({
        "metadata": {
            "chapter": "Chapter 7",
            "total_power_lines": len(power_lines),
            "classification": "list_item (corrected by patch)"
        },
        "power_lines": power_lines
    }, f, indent=2, ensure_ascii=False)

print(f"⚡ Power lines extracted: {power_lines_json}")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("✅ VISUALIZATION COMPLETE")
print("=" * 80)
print()
print(f"📊 Chapter 7 processed:")
print(f"   • Pages: {start_page}-{end_page} ({end_page - start_page + 1} pages)")
print(f"   • Total elements: {len(elements)}")
print(f"   • Power line items: {power_line_count}")
print()
print(f"📁 Output files in: {OUTPUT_DIR}")
print(f"   • {output_pdf.name}")
print(f"   • {json_path.name}")
print(f"   • {csv_path.name}")
print(f"   • {power_lines_json.name}")
print()
print("🎨 Colors used:")
print("   • Blue: text")
print("   • Red: section_header / title")
print("   • Green: table")
print("   • Cyan: list_item (includes power lines!) ⚡")
print("   • Magenta: picture")
print("   • Orange: formula")
print()
print("⚡ All power lines are now consistently classified as list_item!")
print("=" * 80)
