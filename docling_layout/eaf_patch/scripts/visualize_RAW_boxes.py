#!/usr/bin/env python3
"""
Visualize RAW Docling boxes (before text assembly)
This shows the actual layout detection from Docling's AI model
"""
import sys
from pathlib import Path

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent.parent
sys.path.insert(0, str(eaf_patch_path))

from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Paths
SPLIT_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
OUTPUT_PDF = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs_with_eaf_patch" / "chapter6_RAW_boxes.pdf"

print("=" * 80)
print("🎨 VISUALIZING RAW DOCLING BOXES")
print("=" * 80)
print(f"📄 PDF: {SPLIT_PDF.name}")
print(f"💾 Output: {OUTPUT_PDF.name}")
print("=" * 80)

# Apply patch
print("\n📦 Applying EAF patch...")
apply_universal_patch_with_pdf(str(SPLIT_PDF))

# Import Docling
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
import fitz

# Configure lightweight processing
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

print("\n🔍 Processing with Docling (this will show patch activity)...")
converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(SPLIT_PDF))

print("\n✅ Docling processing complete")
print("\n🎨 Now extracting RAW boxes from Docling's layout analysis...")

# Open PDF for annotation
doc = fitz.open(SPLIT_PDF)

# Color scheme
COLORS = {
    'text': (0, 0, 1),
    'section_header': (1, 0, 0),
    'title': (1, 0, 0),
    'table': (0, 1, 0),
    'picture': (1, 0, 1),
    'list_item': (0, 1, 1),
    'caption': (0.5, 0.5, 0),
    'page_header': (0.5, 0.5, 0.5),
    'page_footer': (0.5, 0.5, 0.5),
    'footnote': (0.8, 0.4, 0),
    'formula': (1, 0.5, 0),
}

boxes_drawn = 0
patch_boxes = 0

# Iterate through items and draw their RAW bounding boxes
for item, level in result.document.iterate_items():
    # Get page number
    if not hasattr(item, 'prov') or not item.prov:
        continue
    
    page_no = item.prov[0].page_no
    if page_no < 1 or page_no > len(doc):
        continue
    
    page = doc[page_no - 1]
    
    # Get bbox
    if not hasattr(item.prov[0], 'bbox'):
        continue
    
    bbox = item.prov[0].bbox
    # Fix Y-coordinate inversion: swap .t and .b for positive heights
    rect = fitz.Rect(bbox.l, bbox.b, bbox.r, bbox.t)
    
    # Get color based on label
    color = COLORS.get(item.label, (0, 0, 1))
    
    # Check if this is a patch addition (very short section_header)
    text = ""
    if hasattr(item, 'text'):
        text = item.text.strip()
    
    is_patch = False
    if item.label == 'section_header' and len(text) <= 5 and text:
        is_patch = True
        patch_boxes += 1
        # Draw thick red border for patch additions
        page.draw_rect(rect, color=(1, 0, 0), width=4)
    elif item.label == 'list_item' and ('línea' in text.lower() or 'kv' in text.lower()):
        is_patch = True
        patch_boxes += 1
        page.draw_rect(rect, color=(1, 0, 0), width=4)
    else:
        # Normal Docling box
        page.draw_rect(rect, color=color, width=2)
    
    boxes_drawn += 1

# Add legend
page = doc[0]
page.draw_rect(fitz.Rect(380, 10, 600, 140), color=(1, 1, 1), fill=(0.95, 0.95, 0.95), width=1)
page.insert_text((390, 30), "RAW DOCLING BOXES", fontsize=12, color=(0, 0, 0))
page.insert_text((390, 50), f"Total boxes: {boxes_drawn}", fontsize=9, color=(0, 0, 0))

# Color examples
y = 65
page.draw_rect(fitz.Rect(390, y, 410, y+8), color=COLORS['text'], width=2)
page.insert_text((415, y+7), "Text", fontsize=8)
y += 12
page.draw_rect(fitz.Rect(390, y, 410, y+8), color=COLORS['table'], width=2)
page.insert_text((415, y+7), "Table", fontsize=8)
y += 12
page.draw_rect(fitz.Rect(390, y, 410, y+8), color=COLORS['list_item'], width=2)
page.insert_text((415, y+7), "List", fontsize=8)
y += 12
page.draw_rect(fitz.Rect(390, y, 410, y+8), color=COLORS['section_header'], width=2)
page.insert_text((415, y+7), "Header", fontsize=8)

y += 20
page.draw_rect(fitz.Rect(390, y, 410, y+8), color=(1, 0, 0), width=4)
page.insert_text((415, y+7), f"Patch ({patch_boxes})", fontsize=8, color=(1, 0, 0))

# Save
doc.save(OUTPUT_PDF)
doc.close()

print(f"\n✅ Saved: {OUTPUT_PDF}")
print(f"\n📊 Summary:")
print(f"   📦 Total RAW boxes: {boxes_drawn}")
print(f"   🔴 Patch additions: {patch_boxes}")
print("\n" + "=" * 80)
print("✅ RAW BOXES VISUALIZATION COMPLETE")
print("=" * 80)
