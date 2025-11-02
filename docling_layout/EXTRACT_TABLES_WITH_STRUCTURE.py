#!/usr/bin/env python3
"""
Extract tables WITH full structure (cells, rows, columns)
This shows how to get the COMPLETE table data from Docling
"""
import json
import sys
from pathlib import Path

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# CONFIGURATION
CHAPTER_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_01/EAF-089-2025_capitulo_01_pages_0-7.pdf")
OUTPUT_DIR = Path(__file__).parent / "capitulo_01" / "outputs"

print("=" * 80)
print("📊 EXTRACTING TABLES WITH FULL STRUCTURE")
print("=" * 80)

# Apply patch
apply_universal_patch_with_pdf(str(CHAPTER_PDF))

# Configure Docling
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True  # IMPORTANT!
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # For best results

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# Run extraction
print("\n🔄 Running Docling with table structure extraction...")
converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(CHAPTER_PDF))

print("✅ Extraction complete")

# Extract tables WITH structure
tables_with_structure = []

for item, level in result.document.iterate_items():
    if item.label == "table":
        page_num = item.prov[0].page_no if item.prov else None
        
        # Get table data
        table_data = {
            'page': page_num,
            'text': item.text if hasattr(item, 'text') else '',
            'bbox': None,
            'num_rows': 0,
            'num_cols': 0,
            'cells': []
        }
        
        # Extract bounding box
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox') and page_num in result.document.pages:
                page = result.document.pages[page_num]
                bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                table_data['bbox'] = {
                    'x0': bbox_tl.l,
                    'y0': bbox_tl.t,
                    'x1': bbox_tl.r,
                    'y1': bbox_tl.b
                }
        
        # Extract table structure (if available)
        if hasattr(item, 'data'):
            # item.data contains TableData with grid structure
            table_grid = item.data
            if hasattr(table_grid, 'grid'):
                table_data['num_rows'] = len(table_grid.grid)
                table_data['num_cols'] = len(table_grid.grid[0]) if table_grid.grid else 0
                
                # Extract cells
                for row_idx, row in enumerate(table_grid.grid):
                    for col_idx, cell in enumerate(row):
                        if cell and hasattr(cell, 'text'):
                            table_data['cells'].append({
                                'row': row_idx,
                                'col': col_idx,
                                'text': cell.text
                            })
        
        tables_with_structure.append(table_data)

# Save with structure
output_json = OUTPUT_DIR / "tables_WITH_STRUCTURE.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        'total_tables': len(tables_with_structure),
        'tables': tables_with_structure
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved: {output_json.name}")
print(f"📊 Total tables: {len(tables_with_structure)}")

# Show summary
for i, table in enumerate(tables_with_structure, 1):
    print(f"\nTable {i} (Page {table['page']}):")
    print(f"  Rows: {table['num_rows']}, Cols: {table['num_cols']}")
    print(f"  Cells: {len(table['cells'])}")
    if table['cells']:
        print(f"  Example cell: {table['cells'][0]}")

print("\n" + "=" * 80)
