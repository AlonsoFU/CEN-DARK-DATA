#!/usr/bin/env python3
"""
Complete visualization showing:
1. ALL Docling boxes (layout analysis) - Blue
2. Patch additions on top - Red (thicker)

This shows the complete Docling layout + what the patch added.
"""
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF

# Paths
SPLIT_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
JSON_WITH_PATCH = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs_with_eaf_patch" / "layout_with_eaf_patch.json"
OUTPUT_PDF = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs_with_eaf_patch" / "chapter6_COMPLETE_layout.pdf"

print("=" * 80)
print("🎨 COMPLETE LAYOUT VISUALIZATION - Chapter 6")
print("=" * 80)
print(f"📄 PDF: {SPLIT_PDF.name}")
print(f"📊 JSON: {JSON_WITH_PATCH.name}")
print(f"💾 Output: {OUTPUT_PDF.name}")
print("=" * 80)

# Load JSON
print("\n📖 Loading JSON...")
with open(JSON_WITH_PATCH, 'r', encoding='utf-8') as f:
    data = json.load(f)

elements = data['elements']
print(f"✅ Loaded {len(elements)} elements")

# Categorize elements
type_counts = {}
patch_additions = []

for elem in elements:
    elem_type = elem.get('type', 'unknown')
    type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
    
    # Identify patch additions
    text = elem.get('text', '').strip()
    if elem_type == 'section_header' and len(text) <= 5 and text:
        patch_additions.append(elem)
    elif elem_type == 'list_item' and ('línea' in text.lower() or 'kv' in text.lower()):
        patch_additions.append(elem)

print(f"\n📊 Elements by type:")
for elem_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"   {elem_type:20s}: {count:4d}")

print(f"\n🔴 Patch additions: {len(patch_additions)}")

# Open PDF
print(f"\n📂 Opening PDF...")
doc = fitz.open(SPLIT_PDF)
print(f"✅ Opened {len(doc)} pages")

# Color scheme - matching Docling style
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

print("\n🎨 Drawing ALL Docling boxes...")

boxes_drawn = 0

# Draw ALL elements with their type colors
for elem in elements:
    if 'bbox' not in elem or elem['bbox'] is None:
        continue
    
    page_num = elem.get('page')
    if not page_num:
        continue
    
    pdf_page_idx = page_num - 1
    
    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue
    
    page = doc[pdf_page_idx]
    bbox = elem['bbox']
    elem_type = elem.get('type', 'text')
    
    # Get color for this type
    color = COLORS.get(elem_type, (0, 0, 1))  # Default blue
    
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=color, width=2)
    boxes_drawn += 1

# Now draw THICK RED boxes on patch additions to highlight them
print(f"\n🔴 Highlighting patch additions with thick red boxes...")

patch_boxes_drawn = 0
for elem in patch_additions:
    if 'bbox' not in elem or elem['bbox'] is None:
        continue
    
    page_num = elem.get('page')
    if not page_num:
        continue
    
    pdf_page_idx = page_num - 1
    
    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue
    
    page = doc[pdf_page_idx]
    bbox = elem['bbox']
    
    # THICK RED border to highlight patch additions
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=(1, 0, 0), width=4)  # Thick red
    patch_boxes_drawn += 1

# Add legend
print("\n📝 Adding legend...")
page = doc[0]

# Legend background
legend_rect = fitz.Rect(380, 10, 600, 160)
page.draw_rect(legend_rect, color=(1, 1, 1), fill=(0.95, 0.95, 0.95), width=1)

# Title
page.insert_text((390, 25), "COMPLETE LAYOUT", fontsize=12, fontname="helv-bold", color=(0, 0, 0))

# Color legend
y = 40
page.draw_rect(fitz.Rect(390, y, 410, y+10), color=COLORS['text'], width=2)
page.insert_text((415, y+8), f"Text ({type_counts.get('text', 0)})", fontsize=8, color=(0, 0, 0))

y += 15
page.draw_rect(fitz.Rect(390, y, 410, y+10), color=COLORS['table'], width=2)
page.insert_text((415, y+8), f"Table ({type_counts.get('table', 0)})", fontsize=8, color=(0, 0, 0))

y += 15
page.draw_rect(fitz.Rect(390, y, 410, y+10), color=COLORS['list_item'], width=2)
page.insert_text((415, y+8), f"List ({type_counts.get('list_item', 0)})", fontsize=8, color=(0, 0, 0))

y += 15
page.draw_rect(fitz.Rect(390, y, 410, y+10), color=COLORS['section_header'], width=2)
page.insert_text((415, y+8), f"Header ({type_counts.get('section_header', 0)})", fontsize=8, color=(0, 0, 0))

y += 15
page.draw_rect(fitz.Rect(390, y, 410, y+10), color=COLORS['picture'], width=2)
page.insert_text((415, y+8), f"Picture ({type_counts.get('picture', 0)})", fontsize=8, color=(0, 0, 0))

# Patch additions highlight
y += 20
page.insert_text((390, y+8), "PATCH ADDITIONS:", fontsize=9, fontname="helv-bold", color=(0.5, 0, 0))
y += 15
page.draw_rect(fitz.Rect(390, y, 410, y+10), color=(1, 0, 0), width=4)
page.insert_text((415, y+8), f"Added by patch ({len(patch_additions)})", fontsize=8, color=(1, 0, 0))

y += 15
page.insert_text((390, y+8), "Look for THICK RED boxes!", fontsize=7, color=(0.5, 0, 0))

# Save
print(f"\n💾 Saving PDF...")
doc.save(OUTPUT_PDF)
doc.close()

print(f"✅ Saved: {OUTPUT_PDF}")
print(f"\n📊 Summary:")
print(f"   📦 Total boxes drawn: {boxes_drawn}")
print(f"   🔴 Patch additions highlighted: {patch_boxes_drawn}")
print(f"   📄 Total pages: {len(doc)}")

print("\n" + "=" * 80)
print("✅ COMPLETE LAYOUT VISUALIZATION READY")
print("=" * 80)
print(f"\nOpen the PDF to see:")
print(f"   • ALL Docling boxes (color-coded by type)")
print(f"   • THICK RED boxes = Patch additions")
print(f"   • Look for '6.' on page 1 with thick red border!")
print("=" * 80)
