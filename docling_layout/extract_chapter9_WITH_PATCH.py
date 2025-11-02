#!/usr/bin/env python3
"""
Chapter 9 Extraction - Following UNIVERSAL_DOCLING_METHODOLOGY.md
Capítulo 9: Análisis de las actuaciones de protecciones (33 pages)
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

# Configuration
DOCUMENT_NAME = "Capítulo 9 - Análisis de las actuaciones de protecciones"
CHAPTER_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_09/EAF-089-2025_capitulo_09_pages_349-381.pdf")
OUTPUT_DIR = Path(__file__).parent / "capitulo_09" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print(f"🔄 CHAPTER 9 EXTRACTION")
print("=" * 80)
print(f"Document: {DOCUMENT_NAME}")
print(f"PDF: {CHAPTER_PDF.name}")
print(f"Pages: 33 (pages 349-381 of full document)")
print("=" * 80)

# Import Docling
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Apply EAF patch
print("\n🐵 Applying EAF patch...")
apply_universal_patch_with_pdf(str(CHAPTER_PDF))
print("✅ Patch applied")

# Configure Docling (FAST mode for text-heavy chapter)
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.mode = TableFormerMode.FAST

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# Run extraction
print("\n🔄 Running Docling extraction...")
converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(CHAPTER_PDF))
print("✅ Extraction complete")

# Extract elements - PRESERVING FULL DOCLING LABELS
print("\n📊 Extracting elements...")
elements = []
for item, level in result.document.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None
    
    if page_num is not None:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                if page_num in result.document.pages:
                    page = result.document.pages[page_num]
                    bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_dict = {
                        'x0': bbox_tl.l,
                        'y0': bbox_tl.t,
                        'x1': bbox_tl.r,
                        'y1': bbox_tl.b
                    }
        
        elements.append({
            'type': str(item.label),  # ← PRESERVES FULL DOCLING LABEL
            'text': item.text if hasattr(item, 'text') else '',
            'page': page_num,
            'bbox': bbox_dict,
            'level': level
        })

# Save JSON
output_json = OUTPUT_DIR / "layout_WITH_PATCH.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'document': DOCUMENT_NAME,
            'extractor': 'Docling + EAF Patch v2.0',
            'extraction_date': datetime.now().isoformat(),
            'total_elements': len(elements),
            'total_pages': 33,
            'docling_labels_preserved': True
        },
        'elements': elements
    }, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {output_json}")

# Statistics
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print(f"\n📊 Total elements: {len(elements)}")
print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<40}: {count:>4}")

print("\n" + "=" * 80)
print("✅ Chapter 9 extraction complete!")
print(f"📁 Output: {output_json}")
print("=" * 80)
