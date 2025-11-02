#!/usr/bin/env python3
"""
Create annotated PDFs and CSV exports for all chapters
Processes all existing docling outputs
"""
import json
import fitz  # PyMuPDF
from pathlib import Path

# Chapter definitions
CHAPTERS = {
    1: {"name": "Descripción de la Perturbación", "pages": (1, 11)},
    2: {"name": "Equipamiento Afectado", "pages": (12, 90)},
    3: {"name": "Energía No Suministrada", "pages": (91, 153)},
    4: {"name": "Configuraciones de Falla", "pages": (154, 159)},
    5: {"name": "Cronología de Eventos", "pages": (160, 171)},
    6: {"name": "Normalización del Servicio", "pages": (172, 265)},
    7: {"name": "Análisis de Causas de Falla", "pages": (266, 347)},
    8: {"name": "Detalle de Información", "pages": (348, 348)},
    9: {"name": "Análisis de Protecciones", "pages": (349, 381)},
    10: {"name": "Pronunciamiento Técnico", "pages": (382, 392)},
    11: {"name": "Recomendaciones", "pages": (393, 399)},
}

# Color scheme
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

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR.parent / "claude_ocr"

print("=" * 80)
print("🎨 BATCH VISUALIZATION GENERATOR")
print("=" * 80)
print()

def create_annotated_pdf(chapter_num, chapter_info):
    """Create annotated PDF for a single chapter"""
    chapter_name = chapter_info["name"]
    start_page, end_page = chapter_info["pages"]

    print(f"📖 Chapter {chapter_num}: {chapter_name}")

    # Paths
    chapter_dir = BASE_DIR / f"capitulo_{chapter_num:02d}"
    outputs_dir = chapter_dir / "outputs"
    json_path = outputs_dir / "layout_lightweight.json"
    pdf_path = PDF_DIR / f"capitulo_{chapter_num:02d}" / f"EAF-089-2025_capitulo_{chapter_num:02d}_pages_{start_page}-{end_page}.pdf"
    output_pdf = outputs_dir / f"annotated_capitulo_{chapter_num:02d}.pdf"
    output_csv = outputs_dir / "bounding_boxes.csv"

    # Check if JSON exists
    if not json_path.exists():
        print(f"   ⚠️  No docling output found: {json_path.name}")
        print()
        return False

    # Check if PDF exists
    if not pdf_path.exists():
        print(f"   ⚠️  PDF not found: {pdf_path.name}")
        print()
        return False

    # Load layout data
    with open(json_path, 'r') as f:
        data = json.load(f)

    elements = data['elements']
    print(f"   📊 Loaded {len(elements)} elements")

    # Open PDF
    doc = fitz.open(pdf_path)
    print(f"   📄 PDF opened: {len(doc)} pages")

    # Draw boxes
    boxes_drawn = 0
    for element in elements:
        # PDF pages are 1-indexed in element, 0-indexed in PyMuPDF
        # Chapter PDF starts at page 1, so page N in element = page (N - start_page) in PDF
        pdf_page_idx = element['page'] - start_page

        if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
            continue

        page = doc[pdf_page_idx]
        bbox = element['bbox']
        elem_type = element['type']

        color = COLORS.get(elem_type, (0, 0, 1))
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
        page.draw_rect(rect, color=color, width=2)

        label = f"{elem_type}"
        text_point = fitz.Point(bbox['x0'], bbox['y0'] - 2)
        page.insert_text(text_point, label, fontsize=8, color=color)

        boxes_drawn += 1

    # Add legend on first page
    page = doc[0]
    legend_x = 450
    legend_y = 700

    legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 85)
    page.draw_rect(legend_rect, color=(1, 1, 1), fill=(1, 1, 1), width=1)
    page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

    type_counts = {}
    for elem in elements:
        t = elem['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

    y_offset = legend_y + 15
    for elem_type, count in sorted_types[:8]:  # Top 8 types only
        color = COLORS.get(elem_type, (0, 0, 1))
        color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
        page.draw_rect(color_rect, color=color, fill=color, width=0)
        text = f"{elem_type}: {count}"
        page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=8, color=(0, 0, 0))
        y_offset += 12

    # Save PDF
    doc.save(output_pdf)
    doc.close()
    print(f"   ✅ Annotated PDF: {output_pdf.name}")

    # Export to CSV
    with open(output_csv, 'w') as f:
        f.write("type,page,x0,y0,x1,y1,x0_norm,y0_norm,x1_norm,y1_norm,page_width,page_height,text\n")
        for elem in elements:
            bbox = elem['bbox']
            bbox_norm = elem['bbox_normalized']
            dims = elem['page_dimensions']
            text = elem['text'].replace('"', '""').replace('\n', ' ')

            f.write(f'"{elem["type"]}",{elem["page"]},{bbox["x0"]:.2f},{bbox["y0"]:.2f},{bbox["x1"]:.2f},{bbox["y1"]:.2f},'
                    f'{bbox_norm["x0"]:.6f},{bbox_norm["y0"]:.6f},{bbox_norm["x1"]:.6f},{bbox_norm["y1"]:.6f},'
                    f'{dims["width"]},{dims["height"]},"{text}"\n')

    print(f"   ✅ CSV export: {output_csv.name}")
    print(f"   📦 Drew {boxes_drawn} bounding boxes")
    print()

    return True

# Process all chapters
print("🔄 Processing all chapters...")
print()

success_count = 0
for chapter_num, chapter_info in CHAPTERS.items():
    try:
        if create_annotated_pdf(chapter_num, chapter_info):
            success_count += 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
        continue

print("=" * 80)
print("✅ VISUALIZATION COMPLETE")
print("=" * 80)
print(f"📊 Processed: {success_count}/{len(CHAPTERS)} chapters")
print()
print("📁 Output files (per chapter):")
print("   • annotated_capitulo_XX.pdf - Visual bounding boxes")
print("   • bounding_boxes.csv - Coordinate data")
print()
