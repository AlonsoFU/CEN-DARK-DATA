#!/usr/bin/env python3
"""
Extract FULL TABLE STRUCTURE from Docling (cells, rows, columns)

Problem: Our simplified JSON only saves table bounding boxes, not cell data
Solution: This script extracts complete table structure from Docling's TableFormer model

Output: JSON with full table structure including all cell text
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)
from docling.datamodel.document import DocItemLabel

# Config
pdf_path = Path("../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
output_dir = Path("../outputs")
output_dir.mkdir(parents=True, exist_ok=True)

START_PAGE = 1
END_PAGE = 11

print("=" * 80)
print("📊 DOCLING TABLE STRUCTURE EXTRACTOR")
print("=" * 80)
print(f"📄 PDF: {pdf_path.name}")
print(f"📑 Pages: {START_PAGE}-{END_PAGE} (Chapter 1)")
print()

# Verify PDF exists
if not pdf_path.exists():
    print(f"❌ ERROR: PDF not found at {pdf_path}")
    print("   Please verify the path is correct.")
    sys.exit(1)

print(f"✅ PDF found: {pdf_path}")
print()
print("🔧 Configuring Docling with TableFormer (ACCURATE mode for best results)...")

# Configure pipeline with ACCURATE table mode
pipeline_options = PdfPipelineOptions()
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,  # 97.9% accuracy on tables
    do_cell_matching=True
)

# GPU acceleration
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=4,
    device="cuda"
)

# Create converter
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)

print("✅ Docling configured with ACCURATE table mode (97.9% accuracy)")
print()
print("🚀 Starting extraction...")
print()

# Convert document (entire PDF, will filter by page later)
result = converter.convert(str(pdf_path))
doc = result.document

print(f"✅ Extraction complete!")
print()
print(f"📊 Filtering tables from pages {START_PAGE}-{END_PAGE}...")
print()

# Extract all tables with FULL structure (filtered by page range)
tables_data = []
table_count = 0

for item, level in doc.iterate_items():
    # Only process table elements
    if item.label != DocItemLabel.TABLE:
        continue

    # Get page number and bbox first
    bbox = None
    page_no = None
    if hasattr(item, 'prov') and len(item.prov) > 0:
        bbox_obj = item.prov[0].bbox
        page_no = int(item.prov[0].page_no)
        bbox = {
            'x0': float(bbox_obj.l),
            'y0': float(bbox_obj.t),
            'x1': float(bbox_obj.r),
            'y1': float(bbox_obj.b),
            'page': page_no
        }

    # Filter by page range (Chapter 1 only)
    if page_no is None or page_no < START_PAGE or page_no > END_PAGE:
        continue

    table_count += 1

    # Initialize table data
    table_data = {
        'table_number': table_count,
        'type': 'table',
        'page': bbox['page'] if bbox else None,
        'bbox': bbox,
        'num_rows': 0,
        'num_cols': 0,
        'cells': [],
        'rows': [],
        'text_preview': item.text[:200] if item.text else ""
    }

    # Extract table structure from TableFormer
    if hasattr(item, 'data') and item.data is not None:
        table_grid = item.data

        # Check if we have grid structure
        if hasattr(table_grid, 'grid') and table_grid.grid:
            table_data['num_rows'] = len(table_grid.grid)
            table_data['num_cols'] = len(table_grid.grid[0]) if table_grid.grid else 0

            # Extract all cells with row/col positions
            for row_idx, row in enumerate(table_grid.grid):
                row_cells = []
                for col_idx, cell in enumerate(row):
                    cell_text = ""
                    if cell and hasattr(cell, 'text'):
                        cell_text = cell.text
                    elif cell is not None:
                        cell_text = str(cell)

                    # Add cell to flat list
                    table_data['cells'].append({
                        'row': row_idx,
                        'col': col_idx,
                        'text': cell_text
                    })

                    # Add to row structure
                    row_cells.append(cell_text)

                # Add complete row
                table_data['rows'].append(row_cells)

    tables_data.append(table_data)

    # Print progress
    print(f"📊 Table {table_count} (Page {bbox['page'] if bbox else '?'}):")
    print(f"   Size: {table_data['num_rows']} rows × {table_data['num_cols']} cols")
    print(f"   Cells: {len(table_data['cells'])} total")
    if table_data['text_preview']:
        print(f"   Preview: {table_data['text_preview'][:100]}...")
    print()

# Save complete table structure
output_file = output_dir / "tables_with_structure.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'extraction_date': datetime.now().isoformat(),
        'pdf': str(pdf_path.name),
        'pages': f"{START_PAGE}-{END_PAGE}",
        'total_tables': len(tables_data),
        'tables': tables_data
    }, f, indent=2, ensure_ascii=False)

print("=" * 80)
print("✅ EXTRACTION COMPLETE")
print("=" * 80)
print(f"📊 Total tables extracted: {len(tables_data)}")
print(f"💾 Output saved to: {output_file}")
print()
print("📋 Table Summary:")
for i, table in enumerate(tables_data, 1):
    print(f"   {i}. Page {table['page']}: {table['num_rows']}×{table['num_cols']} = {len(table['cells'])} cells")
print()
print("🎯 Each table includes:")
print("   ✓ Bounding box coordinates")
print("   ✓ Page number")
print("   ✓ Number of rows and columns")
print("   ✓ Complete cell data with positions")
print("   ✓ Row-by-row structure")
print("   ✓ Text preview")
print()
print(f"📄 Open the JSON file to see full table structure:")
print(f"   {output_file}")
print()
