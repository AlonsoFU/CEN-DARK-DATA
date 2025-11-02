#!/usr/bin/env python3
"""
Fix Chapter 6 Visualization - Correct Coordinate System Conversion

Problem: Docling uses BOTTOM-LEFT origin, PyMuPDF uses TOP-LEFT origin
Solution: Flip Y coordinates before drawing boxes
"""
import json
import fitz
from pathlib import Path

# Paths
JSON_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/docling_layout/capitulo_06/outputs_WITH_UNIVERSAL_PATCH/layout_WITH_UNIVERSAL_PATCH.json")
PDF_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
OUTPUT_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/docling_layout/capitulo_06/outputs_WITH_UNIVERSAL_PATCH/chapter6_FIXED_COORDINATES.pdf")

print("=" * 80)
print("🔧 FIXING CHAPTER 6 VISUALIZATION - COORDINATE CONVERSION")
print("=" * 80)

# Load JSON
with open(JSON_PATH, 'r') as f:
    data = json.load(f)

elements = data['elements']
print(f"📊 Total elements: {len(elements)}")

# Open PDF
doc = fitz.open(PDF_PATH)
page_height = 792.0  # Standard page height

# Color scheme
COLORS = {
    'text': (0, 0, 1),              # Blue
    'section_header': (1, 0, 0),    # Red
    'title': (1, 0, 0),             # Red
    'table': (0, 1, 0),             # Green
    'picture': (1, 0, 1),           # Magenta
    'list_item': (0, 1, 1),         # Cyan
    'caption': (0.5, 0.5, 0),       # Olive
    'page_header': (0.5, 0.5, 0.5), # Gray
    'page_footer': (0.5, 0.5, 0.5), # Gray
    'footnote': (0.8, 0.4, 0),      # Orange
    'formula': (1, 0.5, 0),         # Orange
}

boxes_drawn = 0
coord_fixes = 0

print("\n🎨 Drawing bounding boxes with corrected coordinates...")

for element in elements:
    if 'bbox' not in element or element['bbox'] is None:
        continue

    page_num = element['page']  # 1-indexed in split PDF
    bbox = element['bbox']
    elem_type = element['type']

    # Convert to 0-indexed for PyMuPDF
    pdf_page_idx = page_num - 1

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue

    page = doc[pdf_page_idx]

    # Get color
    color = COLORS.get(elem_type, (0, 0, 1))

    # ============================================================================
    # CRITICAL FIX: Convert Docling (bottom-left) to PyMuPDF (top-left)
    # ============================================================================
    # In Docling's JSON, y0 > y1 means:
    #   y0 = top of box (higher value from bottom)
    #   y1 = bottom of box (lower value from bottom)
    # In PyMuPDF, we need:
    #   y0 = top of box (lower value from top)
    #   y1 = bottom of box (higher value from top)

    docling_x0 = bbox['x0']
    docling_y0 = bbox['y0']  # Top in Docling (larger Y)
    docling_x1 = bbox['x1']
    docling_y1 = bbox['y1']  # Bottom in Docling (smaller Y)

    # Determine which is top and which is bottom
    docling_top = max(docling_y0, docling_y1)
    docling_bottom = min(docling_y0, docling_y1)

    # Convert to PyMuPDF (flip Y axis)
    pymupdf_x0 = docling_x0
    pymupdf_y0 = page_height - docling_top     # Top: page_height - (large Y in Docling)
    pymupdf_x1 = docling_x1
    pymupdf_y1 = page_height - docling_bottom  # Bottom: page_height - (small Y in Docling)

    # Draw rectangle with CONVERTED coordinates
    rect = fitz.Rect(pymupdf_x0, pymupdf_y0, pymupdf_x1, pymupdf_y1)
    page.draw_rect(rect, color=color, width=2)

    boxes_drawn += 1
    coord_fixes += 1

print(f"✅ Drew {boxes_drawn} bounding boxes")
print(f"🔄 Converted {coord_fixes} coordinate systems (Docling → PyMuPDF)")

# Save annotated PDF
doc.save(OUTPUT_PATH)
doc.close()

print(f"\n📄 Saved: {OUTPUT_PATH}")
print("=" * 80)
print("✅ COORDINATE CONVERSION COMPLETE")
print("=" * 80)
print("\n🎯 Coordinate System Fix:")
print("   Docling:  BOTTOM-LEFT origin (y increases upward)")
print("   PyMuPDF:  TOP-LEFT origin (y increases downward)")
print(f"   Formula:  pymupdf_y = {page_height} - docling_y")
print("\n📊 Check the new PDF - boxes should now align correctly!")
