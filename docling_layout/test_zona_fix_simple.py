#!/usr/bin/env python3
"""
Simple test: Reprocess existing Chapter 7 PDF with the Zona fix
Uses PyMuPDF to extract just the pages we need first
"""
import sys
import fitz
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

# Import and apply the universal patch
sys.path.insert(0, str(Path(__file__).parent))
from eaf_patch.core.eaf_patch_engine import apply_universal_patch_with_pdf

# PDF paths
full_pdf_path = project_root / "domains/operaciones/eaf/chapters/eaf_089_2025.pdf"
temp_chapter7_pdf = Path(__file__).parent / "temp_chapter7.pdf"

print("=" * 80)
print("Testing Zona Classification Fix on Chapter 7")
print("=" * 80)
print(f"\n📄 Full PDF: {full_pdf_path}")

# Step 1: Extract just Chapter 7 pages to a temporary PDF
print("\n📄 Step 1: Extracting Chapter 7 pages (256-308)...")
doc = fitz.open(full_pdf_path)
chapter7_doc = fitz.open()

for page_num in range(255, 308):  # 0-indexed (pages 256-308)
    chapter7_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

chapter7_doc.save(temp_chapter7_pdf)
chapter7_doc.close()
doc.close()
print(f"✅ Saved temporary PDF: {temp_chapter7_pdf}")

# Step 2: Apply the universal patch WITH PDF extraction
print("\n📄 Step 2: Applying patch...")
apply_universal_patch_with_pdf(str(temp_chapter7_pdf))

# Step 3: Process with Docling
print("\n📄 Step 3: Processing with Docling...")
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = True
pipeline_options.table_structure_options.mode = TableFormerMode.FAST

converter = DocumentConverter(
    format_options={
        PdfFormatOption: pipeline_options,
    }
)

result = converter.convert(str(temp_chapter7_pdf))

# Step 4: Export to JSON
print("\n📄 Step 4: Exporting to JSON...")
output_dir = Path(__file__).parent / "capitulo_07" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

output_json = output_dir / "layout_patched_zona_fix.json"
with open(output_json, 'w', encoding='utf-8') as f:
    import json
    doc_obj = result.document
    elements = []
    for item, level in doc_obj.iterate_items():
        elements.append({
            'type': item.label.value if hasattr(item, 'label') else 'unknown',
            'text': item.text if hasattr(item, 'text') else '',
            'page_number': item.prov[0].page_no + 1 if hasattr(item, 'prov') and item.prov else None,
            'bbox': {
                'x0': item.prov[0].bbox.l,
                'y0': item.prov[0].bbox.t,
                'x1': item.prov[0].bbox.r,
                'y1': item.prov[0].bbox.b
            } if hasattr(item, 'prov') and item.prov and hasattr(item.prov[0], 'bbox') else None
        })
    json.dump({'elements': elements}, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {output_json}")

# Step 5: Analyze results
print("\n📄 Step 5: Analyzing results...")
import json
with open(output_json, 'r') as f:
    data = json.load(f)

print("\n" + "=" * 80)
print("VERIFICATION: Zona items by type")
print("=" * 80)

section_headers = []
list_items = []

for item in data['elements']:
    text = item.get('text', '').strip()
    item_type = item.get('type')

    if 'Zona' in text and 'Área' in text:
        if item_type == 'section_header':
            section_headers.append(text[:80])
        elif item_type == 'list_item':
            list_items.append(text[:80])

print(f"\n📊 SECTION HEADERS with 'Zona' (should be 0): {len(section_headers)}")
for text in section_headers:
    print(f"   ❌ {text}")

print(f"\n📊 LIST ITEMS with 'Zona' (should be ALL ~18): {len(list_items)}")
for text in list_items[:10]:  # Show first 10
    has_bullet = text.startswith(('·', '•'))
    status = "✅" if has_bullet else "⚠️  NO BULLET"
    print(f"   {status} {text}")

if len(list_items) > 10:
    print(f"   ... and {len(list_items) - 10} more")

print("\n" + "=" * 80)
if len(section_headers) == 0 and len(list_items) >= 18:
    print("✅ FIX SUCCESSFUL! All Zona items are list-items with bullets")
else:
    print(f"⚠️  FIX INCOMPLETE: {len(section_headers)} still section-headers, {len(list_items)} list-items")
print("=" * 80)

# Cleanup
temp_chapter7_pdf.unlink()
print(f"\n🧹 Cleaned up temporary PDF")
