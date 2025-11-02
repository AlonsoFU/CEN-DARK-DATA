#!/usr/bin/env python3
"""
Chapter 6 Extraction with EAF Monkey Patch
Uses the SAME approach as Chapter 6 for consistency

Applies:
1. Title merge fix (short titles like "6." → complete lines from PyMuPDF)
2. Missing title detection
3. Power line classification
4. Zona sequential detection (document-level fix)
"""
import sys
from pathlib import Path

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

# Import patch engine
from core.eaf_patch_engine import apply_universal_patch_with_pdf, apply_zona_fix_to_document

# PDF path
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")

print("=" * 80)
print("Chapter 6 Extraction with EAF Monkey Patch")
print("=" * 80)
print(f"\n📄 PDF: {pdf_path}")
print(f"📄 Pages: 82 pages (266-347)")
print(f"🐵 Method: Monkey patch (same as Chapter 6)")

# ============================================================================
# STEP 1: Apply Monkey Patch BEFORE creating converter
# ============================================================================
print("\n" + "=" * 80)
print("🐵 STEP 1: Applying EAF Monkey Patch")
print("=" * 80)

apply_universal_patch_with_pdf(pdf_path)

# ============================================================================
# STEP 2: Configure Docling
# ============================================================================
print("\n" + "=" * 80)
print("⚙️  STEP 2: Configuring Docling Pipeline")
print("=" * 80)

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

print("✅ Pipeline configured (OCR=False, Tables=FAST)")

# ============================================================================
# STEP 3: Process Chapter 6 with Patch Active
# ============================================================================
print("\n" + "=" * 80)
print("🔄 STEP 3: Processing Chapter 6")
print("=" * 80)
print("⏱️  This will take ~5-7 minutes (82 pages)...")
print("🐵 Patch is ACTIVE - will intercept Docling's pipeline")
print()

result = converter.convert(str(pdf_path))

print("\n✅ Docling extraction complete (with patch applied during pipeline)")

# ============================================================================
# STEP 4: Apply Document-Level Zona Fix
# ============================================================================
print("\n" + "=" * 80)
print("🔧 STEP 4: Applying Document-Level Zona Fix")
print("=" * 80)

doc = result.document
reclassified_count = apply_zona_fix_to_document(doc)

print(f"✅ Zona fix applied ({reclassified_count} items reclassified)")

# ============================================================================
# STEP 5: Export to JSON
# ============================================================================
print("\n" + "=" * 80)
print("📄 STEP 5: Exporting to JSON")
print("=" * 80)

output_dir = Path(__file__).parent / "capitulo_06" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

output_json = output_dir / "layout_WITH_PATCH.json"

import json

elements = []

# Use iterate_items() with proper coordinate conversion (same as Chapter 6)
for item, level in doc.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None

    if page_num is not None:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                if page_num in doc.pages:
                    page = doc.pages[page_num]
                    # KEY: Proper coordinate conversion to top-left origin
                    bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_dict = {
                        'x0': bbox_tl.l,
                        'y0': bbox_tl.t,
                        'x1': bbox_tl.r,
                        'y1': bbox_tl.b
                    }

        elements.append({
            'type': item.label.value if hasattr(item, 'label') else 'unknown',
            'text': item.text if hasattr(item, 'text') else '',
            'page': page_num,
            'bbox': bbox_dict
        })

json.dump({'elements': elements, 'total_elements': len(elements)}, open(output_json, 'w'), indent=2, ensure_ascii=False)

print(f"✅ Saved: {output_json}")
print(f"📊 Total elements: {len(elements)}")

# Stats
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20}: {count:>4}")

print("\n" + "=" * 80)
print("✅ CHAPTER 7 EXTRACTION COMPLETE (WITH PATCH)")
print("=" * 80)
print("\n📋 What the patch did:")
print("   🔗 Merged short titles with complete PyMuPDF lines")
print("   ✅ Detected missing titles that Docling missed")
print("   ⚡ Classified power system list items")
print("   🔄 Fixed Zona sequential/isolated detection")
print("\n📁 Output:")
print(f"   {output_json}")
print("\n🎨 Next step: Create annotated PDF with bounding boxes")
print(f"   python visualize_chapter6_WITH_PATCH.py")
print("=" * 80)
