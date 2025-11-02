#!/usr/bin/env python3
"""
Create DUAL visualization for Chapter 6:
- BLUE boxes = Original Docling elements
- RED boxes = Patch additions (missing titles, power lines)
"""
import json
import sys
from pathlib import Path

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent.parent
sys.path.insert(0, str(eaf_patch_path))

# Import after adding to path
import fitz  # PyMuPDF

# Paths
SPLIT_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
JSON_WITH_PATCH = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs_with_eaf_patch" / "layout_with_eaf_patch.json"
OUTPUT_PDF = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs_with_eaf_patch" / "chapter6_DUAL_visualization.pdf"

print("=" * 80)
print("🎨 CREATING DUAL VISUALIZATION - Chapter 6")
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

# Separate Docling vs Patch elements
# Patch elements are identified by being very short titles or power lines
patch_elements = []
docling_elements = []

for elem in elements:
    text = elem.get('text', '').strip()
    elem_type = elem.get('type', '')
    
    # Identify patch additions:
    # 1. Missing titles (very short section_header like "6.", "a.", "b.")
    # 2. Power lines (list_item with specific patterns)
    is_patch_addition = False
    
    if elem_type == 'section_header' and len(text) <= 5 and text:
        # Short titles like "6.", "a.", "b.", "d.1", etc.
        is_patch_addition = True
    elif elem_type == 'list_item' and ('línea' in text.lower() or 'kv' in text.lower()):
        # Power lines
        is_patch_addition = True
    
    if is_patch_addition:
        patch_elements.append(elem)
    else:
        docling_elements.append(elem)

print(f"\n📊 Element breakdown:")
print(f"   🔵 Docling elements: {len(docling_elements)}")
print(f"   🔴 Patch additions: {len(patch_elements)}")

# Open PDF
print(f"\n📂 Opening PDF: {SPLIT_PDF}")
doc = fitz.open(SPLIT_PDF)
print(f"✅ Opened {len(doc)} pages")

# Draw boxes
print("\n🎨 Drawing bounding boxes...")

# Color scheme
DOCLING_COLOR = (0, 0, 1)  # Blue - original Docling
PATCH_COLOR = (1, 0, 0)     # Red - patch additions

boxes_drawn = {'docling': 0, 'patch': 0}

# Draw Docling boxes (BLUE)
for elem in docling_elements:
    if 'bbox' not in elem or elem['bbox'] is None:
        continue
    
    page_num = elem.get('page')
    if not page_num:
        continue
    
    # Page is already 1-indexed for split PDF
    pdf_page_idx = page_num - 1
    
    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue
    
    page = doc[pdf_page_idx]
    bbox = elem['bbox']
    
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=DOCLING_COLOR, width=1.5)
    boxes_drawn['docling'] += 1

# Draw Patch boxes (RED - thicker for visibility)
for elem in patch_elements:
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
    
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=PATCH_COLOR, width=3.0)  # Thicker for patch
    boxes_drawn['patch'] += 1

# Add legend on first page
print("\n📝 Adding legend to first page...")
page = doc[0]

# Legend background
legend_rect = fitz.Rect(400, 20, 590, 110)
page.draw_rect(legend_rect, color=(1, 1, 1), fill=(0.95, 0.95, 0.95), width=1)

# Legend title
page.insert_text((410, 35), "DUAL VISUALIZATION", fontsize=12, color=(0, 0, 0))

# Blue box example
page.draw_rect(fitz.Rect(410, 45, 430, 55), color=DOCLING_COLOR, width=1.5)
page.insert_text((435, 53), f"Docling ({boxes_drawn['docling']} elements)", fontsize=9, color=(0, 0, 0))

# Red box example
page.draw_rect(fitz.Rect(410, 65, 430, 75), color=PATCH_COLOR, width=3.0)
page.insert_text((435, 73), f"Patch additions ({boxes_drawn['patch']})", fontsize=9, color=(0, 0, 0))

# Note
page.insert_text((410, 90), "Red boxes = Missing titles", fontsize=8, color=(0.5, 0, 0))
page.insert_text((410, 100), "and power line corrections", fontsize=8, color=(0.5, 0, 0))

# Save
print(f"\n💾 Saving annotated PDF...")
doc.save(OUTPUT_PDF)
doc.close()

print(f"✅ Saved: {OUTPUT_PDF}")
print(f"\n📊 Boxes drawn:")
print(f"   🔵 Docling (blue): {boxes_drawn['docling']}")
print(f"   🔴 Patch (red): {boxes_drawn['patch']}")
print(f"   📦 Total: {boxes_drawn['docling'] + boxes_drawn['patch']}")

print("\n" + "=" * 80)
print("✅ DUAL VISUALIZATION COMPLETE")
print("=" * 80)
print(f"\n📖 Open the PDF to see:")
print(f"   - BLUE boxes = Original Docling elements")
print(f"   - RED boxes = Patch additions (look for '6.' on page 1!)")
print("=" * 80)
