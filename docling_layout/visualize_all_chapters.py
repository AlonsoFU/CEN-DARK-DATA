#!/usr/bin/env python3
"""
Generate annotated PDFs with Docling bounding boxes for ALL chapters (1-11)
Creates visualization files similar to capitulo_01 for each chapter
"""
import json
import fitz  # PyMuPDF
from pathlib import Path
import sys

# Chapter page ranges (from EAF-089-2025)
CHAPTERS = {
    1: {"pages": (1, 11), "name": "Descripción Perturbación"},
    2: {"pages": (12, 90), "name": "Equipamiento Afectado"},
    3: {"pages": (91, 153), "name": "Energía No Suministrada"},
    4: {"pages": (154, 159), "name": "Configuraciones de Falla"},
    5: {"pages": (160, 171), "name": "Cronología de Eventos"},
    6: {"pages": (172, 265), "name": "Normalización del Servicio"},
    7: {"pages": (266, 347), "name": "Análisis Causas Falla"},
    8: {"pages": (348, 348), "name": "Detalle Información"},
    9: {"pages": (349, 381), "name": "Análisis Protecciones"},
    10: {"pages": (382, 392), "name": "Pronunciamiento Técnico"},
    11: {"pages": (393, 399), "name": "Recomendaciones"},
}

# Color scheme (RGB 0-1 scale)
COLORS = {
    "text": (0, 0, 1),  # Blue
    "section_header": (1, 0, 0),  # Red
    "title": (1, 0, 0),  # Red
    "table": (0, 0.7, 0),  # Green
    "picture": (1, 0, 1),  # Magenta
    "formula": (1, 0.5, 0),  # Orange
    "list_item": (0, 0.7, 0.7),  # Cyan
    "caption": (0.5, 0.5, 0),  # Olive
    "page_header": (0.5, 0.5, 0.5),  # Gray
    "page_footer": (0.5, 0.5, 0.5),  # Gray
    "footnote": (0.7, 0.7, 0.7),  # Light gray
}

def visualize_chapter(chapter_num):
    """Generate annotated PDF for a single chapter"""
    print(f"\n{'=' * 80}")
    print(f"📦 CHAPTER {chapter_num}: {CHAPTERS[chapter_num]['name']}")
    print(f"{'=' * 80}")

    # Paths
    script_dir = Path(__file__).parent
    chapter_dir = script_dir / f"capitulo_{chapter_num:02d}"
    outputs_root = script_dir.parent

    json_path = chapter_dir / "outputs" / "layout_lightweight.json"
    pdf_path = outputs_root / "claude_ocr" / f"capitulo_{chapter_num:02d}" / \
               f"EAF-089-2025_capitulo_{chapter_num:02d}_pages_{CHAPTERS[chapter_num]['pages'][0]}-{CHAPTERS[chapter_num]['pages'][1]}.pdf"
    output_path = chapter_dir / "outputs" / f"annotated_capitulo_{chapter_num:02d}.pdf"

    # Check if files exist
    if not json_path.exists():
        print(f"❌ JSON not found: {json_path}")
        return False

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return False

    print(f"📄 PDF: {pdf_path.name}")
    print(f"📊 Layout: {json_path.name}")
    print(f"📁 Output: {output_path.name}")

    # Load layout data
    print("\n📖 Loading layout data...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    elements = data['elements']
    print(f"✅ Loaded {len(elements)} total elements from docling")

    # Filter only this chapter's pages
    start_page, end_page = CHAPTERS[chapter_num]['pages']
    chapter_elements = [e for e in elements if start_page <= e['page'] <= end_page]
    print(f"🔍 Filtered to {len(chapter_elements)} elements in Chapter {chapter_num} (pages {start_page}-{end_page})")

    # Open PDF
    print("\n📄 Opening PDF...")
    doc = fitz.open(pdf_path)
    print(f"✅ PDF opened: {len(doc)} pages")

    # Draw boxes
    print("\n🎨 Drawing bounding boxes...")
    boxes_drawn = 0
    for element in chapter_elements:
        # Convert absolute page number to PDF-relative (0-indexed)
        page_num_in_pdf = element['page'] - start_page

        if page_num_in_pdf < 0 or page_num_in_pdf >= len(doc):
            print(f"⚠️  Skipping page {element['page']} (out of range)")
            continue

        page = doc[page_num_in_pdf]
        bbox = element['bbox']
        elem_type = element['type']

        # Get color
        color = COLORS.get(elem_type, (0, 0, 1))

        # Create rectangle
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

        # Draw rectangle
        page.draw_rect(rect, color=color, width=2)

        # Add label
        label = f"{elem_type}"
        text_point = fitz.Point(bbox['x0'], bbox['y0'] - 2)
        page.insert_text(text_point, label, fontsize=8, color=color)

        boxes_drawn += 1

    print(f"✅ Drew {boxes_drawn} boxes")

    # Add legend on first page
    print("\n📝 Adding legend...")
    page = doc[0]
    legend_x = 450
    legend_y = 700

    # Legend background
    legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 85)
    page.draw_rect(legend_rect, color=(1, 1, 1), fill=(1, 1, 1), width=1)

    # Legend title
    page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

    # Count elements by type
    type_counts = {}
    for elem in chapter_elements:
        t = elem['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    # Sort by count
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

    # Draw legend entries
    y_offset = legend_y + 15
    for elem_type, count in sorted_types:
        color = COLORS.get(elem_type, (0, 0, 1))

        # Draw color box
        color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
        page.draw_rect(color_rect, color=color, fill=color, width=0)

        # Draw text
        text = f"{elem_type}: {count}"
        page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=8, color=(0, 0, 0))

        y_offset += 12

    print("✅ Legend added")

    # Save
    print("\n💾 Saving annotated PDF...")
    doc.save(output_path)
    doc.close()
    print(f"✅ Saved: {output_path.name}")

    # Print statistics
    print("\n📊 STATISTICS:")
    print("-" * 60)
    print(f"   Total elements: {len(chapter_elements)}")
    print(f"   Boxes drawn: {boxes_drawn}")
    print(f"   Pages: {start_page}-{end_page} ({end_page - start_page + 1} pages)")
    print("-" * 60)

    print("\n📖 ELEMENT TYPES:")
    print("-" * 60)
    for elem_type, count in sorted_types:
        color = COLORS.get(elem_type, (0, 0, 1))
        r, g, b = [int(c * 255) for c in color]
        print(f"   {elem_type:<20} RGB({r:>3}, {g:>3}, {b:>3}) - {count:>4} items")
    print("-" * 60)

    return True

def main():
    """Process all chapters or specific ones"""
    print("=" * 80)
    print("🎨 DOCLING LAYOUT VISUALIZER - ALL CHAPTERS")
    print("=" * 80)

    # Check if specific chapters requested
    if len(sys.argv) > 1:
        chapters_to_process = [int(c) for c in sys.argv[1:]]
    else:
        chapters_to_process = list(CHAPTERS.keys())

    print(f"\n📋 Will process {len(chapters_to_process)} chapters: {chapters_to_process}")

    # Process each chapter
    results = {}
    for chapter_num in chapters_to_process:
        if chapter_num not in CHAPTERS:
            print(f"\n❌ Invalid chapter number: {chapter_num}")
            results[chapter_num] = False
            continue

        success = visualize_chapter(chapter_num)
        results[chapter_num] = success

    # Summary
    print("\n" + "=" * 80)
    print("✅ PROCESSING COMPLETE")
    print("=" * 80)

    successful = [c for c, s in results.items() if s]
    failed = [c for c, s in results.items() if not s]

    print(f"\n✅ Successful: {len(successful)} chapters {successful}")
    if failed:
        print(f"❌ Failed: {len(failed)} chapters {failed}")

    print("\n📁 Output files:")
    for chapter_num in successful:
        output_path = Path(__file__).parent / f"capitulo_{chapter_num:02d}" / "outputs" / f"annotated_capitulo_{chapter_num:02d}.pdf"
        print(f"   Chapter {chapter_num:>2}: {output_path}")

    print("\n💡 TIP: Open the PDFs and zoom in to see bounding boxes clearly!")
    print()

if __name__ == "__main__":
    main()
