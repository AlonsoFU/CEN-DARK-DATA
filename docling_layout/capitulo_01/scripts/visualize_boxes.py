#!/usr/bin/env python3
"""
Visualize Docling layout boxes on PDF
Creates an annotated PDF with colored bounding boxes
"""
import json
import fitz  # PyMuPDF
from pathlib import Path

# Paths
json_path = Path("../outputs/layout_lightweight.json")
pdf_path = Path("../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
output_path = Path("../outputs/annotated_layout.pdf")

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

print("=" * 80)
print("📦 DOCLING LAYOUT VISUALIZER")
print("=" * 80)
print(f"📄 PDF: {pdf_path.name}")
print(f"📊 Layout: {json_path.name}")
print(f"📁 Output: {output_path.name}")
print()

# Load layout data
print("📖 Loading layout data...")
with open(json_path, 'r') as f:
    data = json.load(f)

elements = data['elements']
print(f"✅ Loaded {len(elements)} elements")
print()

# Open PDF
print("📄 Opening PDF...")
doc = fitz.open(pdf_path)
print(f"✅ PDF opened: {len(doc)} pages")
print()

# Draw boxes
print("🎨 Drawing bounding boxes...")
for element in elements:
    page_num = element['page'] - 1  # PyMuPDF uses 0-indexed pages

    if page_num >= len(doc):
        continue

    page = doc[page_num]
    bbox = element['bbox']
    elem_type = element['type']

    # Get color (default to blue if type not in mapping)
    color = COLORS.get(elem_type, (0, 0, 1))

    # Create rectangle (PyMuPDF uses: x0, y0, x1, y1)
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

    # Draw rectangle with semi-transparent fill
    page.draw_rect(rect, color=color, width=2)

    # Add label
    label = f"{elem_type}"
    text_point = fitz.Point(bbox['x0'], bbox['y0'] - 2)
    page.insert_text(text_point, label, fontsize=8, color=color)

print(f"✅ Drew {len(elements)} boxes")
print()

# Add legend on first page
print("📝 Adding legend...")
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
for elem in elements:
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
print()

# Save
print("💾 Saving annotated PDF...")
doc.save(output_path)
doc.close()
print(f"✅ Saved: {output_path.absolute()}")
print()

print("=" * 80)
print("✅ VISUALIZATION COMPLETE")
print("=" * 80)
print()
print("📖 COLOR LEGEND:")
print("-" * 60)
for elem_type, color in COLORS.items():
    r, g, b = [int(c * 255) for c in color]
    print(f"   {elem_type:<20} RGB({r:>3}, {g:>3}, {b:>3})")
print("-" * 60)
print()
print(f"📁 Open the file: {output_path.absolute()}")
print()
print("💡 TIP: Zoom in to see bounding boxes clearly!")
