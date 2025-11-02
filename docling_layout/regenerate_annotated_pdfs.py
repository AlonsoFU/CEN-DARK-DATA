#!/usr/bin/env python3
"""
Regenerate annotated PDFs with Docling Native Colors
(No re-extraction needed - just re-visualize existing JSONs)
"""
import json
import fitz
from pathlib import Path

# Docling Native Colors
COLORS = {
    'text': (1.0, 1.0, 0.6),                    # Yellow
    'section_header': (1.0, 0.6, 0.6),          # Light red
    'title': (1.0, 0.6, 0.6),                   # Light red
    'list_item': (0.6, 0.6, 1.0),               # Light blue
    'table': (1.0, 0.8, 0.8),                   # Light pink
    'picture': (1.0, 0.8, 0.64),                # Peach
    'caption': (1.0, 0.8, 0.6),                 # Light orange
    'formula': (0.75, 0.75, 0.75),              # Gray
    'footnote': (0.78, 0.78, 1.0),              # Light purple
    'page_header': (0.8, 1.0, 0.8),             # Light green
    'page_footer': (0.8, 1.0, 0.8),             # Light green
}

def create_annotated_pdf(chapter_num, source_pdf_path, json_path, output_pdf_path):
    """Create annotated PDF with Docling colors"""

    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    elements = data['elements']

    # Open PDF
    doc_pdf = fitz.open(source_pdf_path)

    # Draw boxes
    for elem in elements:
        if elem['bbox']:
            page_num = elem['page']
            pymupdf_page_idx = page_num - 1  # Docling 1-indexed → PyMuPDF 0-indexed

            if 0 <= pymupdf_page_idx < len(doc_pdf):
                page = doc_pdf[pymupdf_page_idx]

                bbox = elem['bbox']
                rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

                elem_type = elem['type'].replace('_', '-').lower()
                color = COLORS.get(elem_type, (0.5, 0.5, 0.5))

                page.draw_rect(rect, color=color, width=1.5)

    # Save
    doc_pdf.save(output_pdf_path)
    doc_pdf.close()

    print(f"✅ Chapter {chapter_num}: {output_pdf_path.name}")

print("=" * 80)
print("🎨 Regenerating Annotated PDFs with Docling Native Colors")
print("=" * 80)

base_path = Path(__file__).parent
pdf_base = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr")

# Chapter 3
print("\nChapter 3...")
create_annotated_pdf(
    chapter_num=3,
    source_pdf_path=pdf_base / "capitulo_03" / "EAF-089-2025_capitulo_03_pages_91-152.pdf",
    json_path=base_path / "capitulo_03" / "outputs" / "layout_WITH_PATCH.json",
    output_pdf_path=base_path / "capitulo_03" / "outputs" / "capitulo_03_annotated.pdf"
)

# Chapter 4
print("\nChapter 4...")
create_annotated_pdf(
    chapter_num=4,
    source_pdf_path=pdf_base / "capitulo_04" / "EAF-089-2025_capitulo_04_pages_153-159.pdf",
    json_path=base_path / "capitulo_04" / "outputs" / "layout_WITH_PATCH.json",
    output_pdf_path=base_path / "capitulo_04" / "outputs" / "capitulo_04_annotated.pdf"
)

print("\n" + "=" * 80)
print("✅ Done! Annotated PDFs now use Docling native colors")
print("=" * 80)
print("\nColor scheme:")
print("  🟡 Yellow       - text")
print("  🔴 Light red    - section_header / title")
print("  🔵 Light blue   - list_item")
print("  🌸 Light pink   - table")
print("  🍑 Peach        - picture")
print("  🟠 Light orange - caption")
print("  ⚪ Gray         - formula")
