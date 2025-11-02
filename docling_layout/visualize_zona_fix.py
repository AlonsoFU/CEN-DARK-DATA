#!/usr/bin/env python3
"""
Create annotated PDF showing Zona items with colored bounding boxes
"""
import json
import fitz  # PyMuPDF
from pathlib import Path

# Paths
json_path = Path(__file__).parent / "capitulo_07/outputs/layout_WITH_ZONA_FIX.json"
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf")
output_path = Path(__file__).parent / "capitulo_07/outputs/capitulo_07_ZONA_FIXED.pdf"

print("=" * 80)
print("Creating Annotated PDF with Zona Items")
print("=" * 80)
print(f"\n📄 JSON: {json_path}")
print(f"📄 PDF: {pdf_path}")
print(f"📄 Output: {output_path}\n")

# Load JSON
with open(json_path, 'r') as f:
    data = json.load(f)

# Find all Zona items
zona_items = []
for item in data['elements']:
    text = item.get('text', '').strip()
    if 'Zona' in text and 'Área' in text:
        zona_items.append(item)

print(f"🔍 Found {len(zona_items)} Zona items in JSON")

# Open PDF
doc = fitz.open(pdf_path)
output_doc = fitz.open()

# Copy all pages to output
for page_num in range(len(doc)):
    output_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

# Color mapping
colors = {
    'list_item': (0, 1, 0, 0.3),      # Green with transparency
    'section_header': (1, 0, 0, 0.3),  # Red with transparency
}

# Draw boxes on Zona items
drawn_count = 0
skipped_count = 0
for item in zona_items:
    page_num = item.get('page_number')
    bbox = item.get('bbox')
    item_type = item.get('type')
    text = item.get('text', '')[:50]

    if page_num is None or bbox is None:
        skipped_count += 1
        continue

    # Check if page exists (0-indexed)
    page_index = page_num - 1
    if page_index < 0 or page_index >= len(output_doc):
        print(f"   ⚠️  Page {page_num} out of range (PDF has {len(output_doc)} pages), skipping...")
        skipped_count += 1
        continue

    # Get page (0-indexed)
    page = output_doc[page_index]

    # PyMuPDF uses (x0, y0, x1, y1) format
    # Our bbox has: x0 (left), y0 (top), x1 (right), y1 (bottom)
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

    # Get color
    color = colors.get(item_type, (0, 0, 1, 0.3))  # Default blue

    # Draw rectangle
    page.draw_rect(rect, color=color[:3], fill=color[:3], fill_opacity=color[3], width=2)

    drawn_count += 1
    print(f"   ✅ Page {page_num}: {item_type} - '{text}'...")

# Save output
output_doc.save(output_path)
output_doc.close()
doc.close()

print(f"\n✅ Created annotated PDF with {drawn_count} Zona items highlighted")
if skipped_count > 0:
    print(f"⚠️  Skipped {skipped_count} items (out of page range or missing bbox)")
print(f"📁 Saved to: {output_path}")

print("\n" + "=" * 80)
print("COLOR KEY")
print("=" * 80)
print("🟢 Green  = list_item (should be ALL Zona items)")
print("🔴 Red    = section_header (should be NONE)")
print("=" * 80)

print(f"\nℹ️  The PDF has {len(output_doc)} pages (Chapter 7 extracted pages)")
print(f"ℹ️  Page numbers in JSON are absolute (from full document)")
print(f"ℹ️  Zona items appear on pages 79-83 of Chapter 7")
