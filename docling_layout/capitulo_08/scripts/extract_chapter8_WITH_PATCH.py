#!/usr/bin/env python3
"""
Chapter 8 Extraction with Docling + EAF Patch
Following UNIVERSAL_DOCLING_METHODOLOGY.md
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent.parent.parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

# ============================================================================
# CONFIGURATION - Chapter 8 Specific
# ============================================================================

DOCUMENT_NAME = "Capítulo 8 - Detalle de información"
PDF_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_08/EAF-089-2025_capitulo_08_pages_348-348.pdf")
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Docling configuration
DOCLING_CONFIG = {
    "do_ocr": False,           # Native PDF text
    "do_table_structure": True, # Chapter 8 has tables
    "table_mode": "ACCURATE"    # Use ACCURATE for better table detection
}

# Patch configuration
PATCH_CONFIG = {
    "enabled": True,
    "coverage_threshold": 0.5,  # Standard 50%
    "detect_titles": True,
    "detect_custom_patterns": True
}

# ============================================================================
# EXTRACTION LOGIC (From methodology template)
# ============================================================================

print("=" * 80)
print(f"🔄 EXTRACTING: {DOCUMENT_NAME}")
print(f"📄 PDF: {PDF_PATH.name}")
print(f"📊 Configuration:")
print(f"   Docling: OCR={DOCLING_CONFIG['do_ocr']}, Tables={DOCLING_CONFIG['table_mode']}")
print(f"   Patch: Enabled={PATCH_CONFIG['enabled']}, Threshold={PATCH_CONFIG['coverage_threshold']}")
print("=" * 80)

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Apply patch if enabled
if PATCH_CONFIG['enabled']:
    print("\n🐵 Applying EAF patch...")
    apply_universal_patch_with_pdf(str(PDF_PATH))
    print("✅ Patch applied")
else:
    print("\n⚠️  Running WITHOUT patch (native Docling only)")

# Configure Docling
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = DOCLING_CONFIG['do_ocr']
pipeline_options.do_table_structure = DOCLING_CONFIG['do_table_structure']

if DOCLING_CONFIG['table_mode'] == 'ACCURATE':
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
else:
    pipeline_options.table_structure_options.mode = TableFormerMode.FAST

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# Run extraction
print("\n🔄 Running Docling extraction...")
converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(PDF_PATH))

print("✅ Extraction complete")

# Extract elements (PRESERVING FULL DOCLING LABELS)
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
            'type': str(item.label),  # PRESERVES FULL DOCLING LABEL
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
            'extractor': 'Docling + EAF Patch v2.0' if PATCH_CONFIG['enabled'] else 'Docling Native',
            'extraction_date': datetime.now().isoformat(),
            'total_elements': len(elements),
            'total_pages': len(result.document.pages),
            'config': {
                'docling': DOCLING_CONFIG,
                'patch': PATCH_CONFIG
            }
        },
        'elements': elements
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved: {output_json.name}")
print(f"📊 Total elements: {len(elements)}")

# Statistics by type
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<40}: {count:>4}")

print("=" * 80)
print(f"✅ Chapter 8 extraction complete!")
print(f"📁 Output: {OUTPUT_DIR}")
print("=" * 80)
