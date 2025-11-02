#!/usr/bin/env python3
"""
Extract Chapter 7 with the NEW Zona Classification Fix
This will verify that the patch correctly:
1. Reclassifies section-headers → list-items for Zona pattern
2. Adds missing bullets to Zona list-items
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

# Import and apply the universal patch
sys.path.insert(0, str(Path(__file__).parent))
from eaf_patch.core.eaf_patch_engine import apply_universal_patch_with_pdf, apply_zona_fix_to_document

# PDF path - use the extracted Chapter 7 PDF (absolute path)
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf")

print("=" * 80)
print("Chapter 7 Extraction with Zona Classification Fix")
print("=" * 80)
print(f"\n📄 PDF: {pdf_path}")
print(f"📄 Pages: {pdf_path.name}")

# Apply the universal patch WITH PDF extraction
print("\n🔧 Applying EAF Patch with Zona classification fix...")
apply_universal_patch_with_pdf(str(pdf_path))
print("✅ Patch applied!\n")

# Configure Docling for lightweight extraction
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

# Process Chapter 7
print("🔄 Processing Chapter 7 with Docling...")
print("⏱️  This will take ~5-7 minutes (82 pages)...\n")

result = converter.convert(str(pdf_path))

# Apply document-level Zona fix (AFTER all pages processed)
apply_zona_fix_to_document(result.document)

# Export to JSON
output_dir = Path(__file__).parent / "capitulo_07" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

output_json = output_dir / "layout_WITH_ZONA_FIX.json"

print("\n📄 Exporting to JSON...")
with open(output_json, 'w', encoding='utf-8') as f:
    import json
    doc = result.document
    elements = []
    for item, level in doc.iterate_items():
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
    json.dump({'elements': elements, 'total_elements': len(elements)}, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {output_json}")

# ============================================================================
# VERIFICATION: Check Zona items
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICATION: Zona Classification Results")
print("=" * 80)

import json
with open(output_json, 'r') as f:
    data = json.load(f)

section_headers_zona = []
list_items_zona = []
all_zona_items = []

for item in data['elements']:
    text = item.get('text', '').strip()
    item_type = item.get('type')

    if 'Zona' in text and 'Área' in text:
        all_zona_items.append({'type': item_type, 'text': text})

        if item_type == 'section_header':
            section_headers_zona.append(text)
        elif item_type == 'list_item':
            list_items_zona.append(text)

print(f"\n📊 Total Zona items found: {len(all_zona_items)}")

print(f"\n❌ SECTION HEADERS with 'Zona' (should be 0): {len(section_headers_zona)}")
if section_headers_zona:
    for text in section_headers_zona[:5]:
        print(f"   ⚠️  {text[:70]}")
    if len(section_headers_zona) > 5:
        print(f"   ... and {len(section_headers_zona) - 5} more")
else:
    print("   ✅ PERFECT! No section-headers with Zona pattern")

print(f"\n✅ LIST ITEMS with 'Zona' (should be ~18): {len(list_items_zona)}")
if list_items_zona:
    items_with_bullets = 0
    items_without_bullets = 0

    for text in list_items_zona[:10]:
        has_bullet = text.startswith(('·', '•'))
        if has_bullet:
            items_with_bullets += 1
            status = "✅"
        else:
            items_without_bullets += 1
            status = "⚠️  NO BULLET"
        print(f"   {status} {text[:70]}")

    if len(list_items_zona) > 10:
        for text in list_items_zona[10:]:
            has_bullet = text.startswith(('·', '•'))
            if has_bullet:
                items_with_bullets += 1
            else:
                items_without_bullets += 1
        print(f"   ... and {len(list_items_zona) - 10} more")

    print(f"\n   📊 With bullets: {items_with_bullets}/{len(list_items_zona)}")
    print(f"   📊 Without bullets: {items_without_bullets}/{len(list_items_zona)}")

# ============================================================================
# FINAL VERDICT
# ============================================================================
print("\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

all_have_bullets = all(t.startswith(('·', '•')) for t in list_items_zona)
no_section_headers = len(section_headers_zona) == 0
expected_count = len(list_items_zona) >= 15  # At least 15 items

if no_section_headers and all_have_bullets and expected_count:
    print("✅ FIX SUCCESSFUL!")
    print("   ✅ All Zona items are list-items (0 section-headers)")
    print("   ✅ All list-items have bullet prefixes")
    print(f"   ✅ Found {len(list_items_zona)} Zona list-items (expected ~18)")
else:
    print("⚠️  FIX INCOMPLETE:")
    if not no_section_headers:
        print(f"   ❌ Still have {len(section_headers_zona)} section-headers with Zona")
    if not all_have_bullets:
        print(f"   ❌ Some list-items missing bullets")
    if not expected_count:
        print(f"   ❌ Only found {len(list_items_zona)} items (expected ~18)")

print("=" * 80)

print(f"\n📁 Output saved to: {output_json}")
print(f"📊 Total elements extracted: {data['total_elements']}")
