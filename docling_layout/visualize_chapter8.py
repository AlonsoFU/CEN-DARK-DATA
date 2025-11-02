#!/usr/bin/env python3
"""
Chapter 8 Visualization - Following METHODOLOGY color standards
"""
import json
import fitz
from pathlib import Path

# Configuration
CHAPTER_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_08/EAF-089-2025_capitulo_08_pages_348-348.pdf")
INPUT_JSON = Path(__file__).parent / "capitulo_08" / "outputs" / "layout_WITH_PATCH.json"
OUTPUT_PDF = Path(__file__).parent / "capitulo_08" / "outputs" / "capitulo_08_annotated.pdf"

# Standard Docling colors (from METHODOLOGY)
COLORS = {
    'text': (0, 0, 1),
    'section_header': (1, 0, 0),
    'title': (1, 0.5, 0),
    'list_item': (0, 0.7, 0.7),
    'table': (0, 0.7, 0),
    'picture': (1, 0, 1),
    'caption': (0.8, 0.4, 0),
    'formula': (1, 0.8, 0),
    'footnote': (0.8, 0.4, 0),
    'page_header': (0.5, 0.5, 0.5),
    'page_footer': (0.5, 0.5, 0.5),
}

print("=" * 80)
print("🎨 CHAPTER 8: Creating Annotated PDF")
print("=" * 80)

# Load JSON
with open(INPUT_JSON) as f:
    data = json.load(f)

elements = data['elements']
print(f"\n📄 Loading {len(elements)} elements...")

# Open PDF
doc = fitz.open(CHAPTER_PDF)

# Draw boxes
boxes_drawn = 0
color_counts = {}

for elem in elements:
    if not elem.get('bbox'):
        continue
    
    bbox = elem['bbox']
    page_num = elem['page']
    
    if page_num < 0 or page_num >= len(doc):
        continue
    
    page = doc[page_num]
    
    # Extract label name (handles both "text" and "DocItemLabel.TEXT")
    label = elem['type']
    if isinstance(label, str) and '.' in label:
        label = label.split('.')[-1].lower()
    else:
        label = str(label).lower()
    
    # Get color
    color = COLORS.get(label, (0.5, 0.5, 0.5))
    
    # Count
    color_counts[label] = color_counts.get(label, 0) + 1
    
    # Draw rectangle
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=2)
    
    boxes_drawn += 1

print(f"\n✅ Drew {boxes_drawn} boxes")
print("\n📊 Elements by type:")
for label, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
    color = COLORS.get(label, (0.5, 0.5, 0.5))
    color_name = {
        (1, 0, 0): "Red",
        (0, 0.7, 0.7): "Cyan",
        (0, 0.7, 0): "Green",
        (0, 0, 1): "Blue",
    }.get(color, "Gray")
    print(f"   {label:<20} ({color_name:<8}): {count:>4} boxes")

# Add legend
page = doc[0]
legend_x = 450
legend_y = 50
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 160, legend_y + 60)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
page.insert_text(fitz.Point(legend_x, legend_y), "Chapter 8 Elements:", fontsize=9, color=(0, 0, 0))

y_offset = legend_y + 15
for label in sorted(color_counts.keys()):
    color = COLORS.get(label, (0.5, 0.5, 0.5))
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)
    page.insert_text(fitz.Point(legend_x + 15, y_offset), f"{label} ({color_counts[label]})", fontsize=7, color=(0, 0, 0))
    y_offset += 10

# Save
doc.save(OUTPUT_PDF)
doc.close()

print(f"\n✅ Saved: {OUTPUT_PDF}")
print("=" * 80)
