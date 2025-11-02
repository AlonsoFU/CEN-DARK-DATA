#!/usr/bin/env python3
"""
Clean Chapter 7 extraction using standard Docling (no patches)
Same approach as Chapter 6
"""
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

# PDF path
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf")

print("=" * 80)
print("Clean Chapter 7 Extraction (Standard Docling)")
print("=" * 80)
print(f"\n📄 PDF: {pdf_path}")
print(f"📄 Pages: 82 pages")

# Configure Docling
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
print("\n🔄 Processing Chapter 7 with Docling...")
print("⏱️  This will take ~5-7 minutes (82 pages)...\n")

result = converter.convert(str(pdf_path))

# Export to JSON (same format as Chapter 6)
output_dir = Path(__file__).parent / "capitulo_07" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

output_json = output_dir / "layout_clean.json"

print("\n📄 Exporting to JSON...")
import json

doc = result.document
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
print("✅ CLEAN EXTRACTION COMPLETE")
print("=" * 80)
