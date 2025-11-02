#!/usr/bin/env python3
"""
Create annotated PDF with bounding boxes from Chapter 7 JSON
Uses EXISTING Docling extraction (layout_lightweight_FIXED.json)
"""
import json
import fitz  # PyMuPDF
from pathlib import Path

# Color scheme
COLORS = {
    "text": (0, 0, 1),
    "section_header": (1, 0, 0),
    "title": (1, 0, 0),
    "table": (0, 0.7, 0),
    "picture": (1, 0, 1),
    "formula": (1, 0.5, 0),
    "list_item": (0, 0.7, 0.7),  # Cyan
    "caption": (0.5, 0.5, 0),
    "page_header": (0.5, 0.5, 0.5),
    "page_footer": (0.5, 0.5, 0.5),
    "footnote": (0.7, 0.7, 0.7),
}

# Paths
BASE_DIR = Path(__file__).parent
json_path = BASE_DIR / "capitulo_07" / "outputs" / "layout_lightweight_FIXED.json"
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf")
output_pdf = BASE_DIR / "capitulo_07" / "outputs" / "chapter7_WITH_BBOXES.pdf"

print("\n" + "█" * 80)
print("🎨 CREATING ANNOTATED PDF FOR CHAPTER 7")
print("█" * 80)
print(f"JSON: {json_path.name}")
print(f"PDF:  {pdf_path.name}")
print(f"Output: {output_pdf}")
print()

# Load JSON
print("📊 Loading extraction data...")
with open(json_path, 'r') as f:
    data = json.load(f)

elements = data['elements']
print(f"✅ Loaded {len(elements)} elements")

# Calculate statistics
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20}: {count:>4}")
print()

# Open PDF
print("📄 Opening PDF...")
doc = fitz.open(pdf_path)
print(f"✅ PDF has {len(doc)} pages")
print()

# Draw boxes
print("🎨 Drawing bounding boxes...")
boxes_drawn = 0

for element in elements:
    page_num = element['page']

    # Calculate PDF page index
    # The PDF is pages 266-347, so page 266 in JSON = page 0 in PDF
    pdf_page_idx = page_num - 266

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

# Add legend on first page
print("📝 Adding legend...")
page = doc[0]  # First page of Chapter 7

legend_x = 450
legend_y = 700

# White background
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 150, legend_y + 100)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)

# Title
page.insert_text(fitz.Point(legend_x, legend_y), "Legend:", fontsize=10, color=(0, 0, 0))

# Element types (top 10)
sorted_types = sorted(stats.items(), key=lambda x: x[1], reverse=True)

y_offset = legend_y + 15
for elem_type, count in sorted_types[:10]:
    color = COLORS.get(elem_type, (0, 0, 1))

    # Color box
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)

    # Text
    text = f"{elem_type}: {count}"
    page.insert_text(fitz.Point(legend_x + 15, y_offset), text, fontsize=8, color=(0, 0, 0))

    y_offset += 10

print("✅ Legend added")
print()

# Save
print("💾 Saving annotated PDF...")
doc.save(output_pdf)
doc.close()

print(f"✅ Saved: {output_pdf}")
print()

print("=" * 80)
print("✅ ANNOTATED PDF CREATED")
print("=" * 80)
print()
print(f"📁 Output file:")
print(f"   {output_pdf}")
print()
print("🎨 Color legend:")
print("   🔵 Blue   = text")
print("   🔴 Red    = section_header / title")
print("   🟢 Green  = table")
print("   🔵🟢 Cyan   = list_item")
print("   🟣 Magenta = picture")
print("   🟠 Orange = formula")
print()
print("📄 Open the PDF to see all bounding boxes!")
print("=" * 80)
