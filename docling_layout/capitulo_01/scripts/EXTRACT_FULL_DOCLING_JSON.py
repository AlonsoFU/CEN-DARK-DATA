#!/usr/bin/env python3
"""
Extract COMPLETE Docling JSON using built-in save_as_json() method

This uses Docling's native export which includes ALL data:
- Complete table structure (cells, rows, columns)
- All element types and text
- Bounding boxes and coordinates
- Provenance information
- Everything Docling extracts

Much simpler than custom extraction!
"""
import sys
from pathlib import Path

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

# Config
pdf_path = Path("../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
output_dir = Path("../outputs")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("📚 DOCLING COMPLETE JSON EXPORT (Built-in method)")
print("=" * 80)
print(f"📄 PDF: {pdf_path.name}")
print(f"📑 Pages: 1-11 (Chapter 1 - will filter after extraction)")
print()
print("✨ Using Docling's native save_as_json() method")
print("   This includes ALL extracted data automatically!")
print()

# Configure pipeline with ACCURATE table mode
pipeline_options = PdfPipelineOptions()
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,  # 97.9% accuracy
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

print("🚀 Starting Docling extraction...")
print("   (This will take ~15-30 minutes for 399 pages)")
print()

# Convert entire document
result = converter.convert(str(pdf_path))
doc = result.document

print("✅ Docling extraction complete!")
print()

# Save complete JSON using Docling's built-in method
output_json = output_dir / "docling_complete_export.json"
print(f"💾 Saving complete Docling JSON...")

doc.save_as_json(
    filename=output_json,
    indent=2  # Pretty formatting
)

print(f"✅ Complete JSON saved to: {output_json}")
print()

# Also save markdown export for human reading
output_md = output_dir / "docling_complete_export.md"
print(f"📝 Saving Markdown export (includes table data as markdown)...")

markdown_text = doc.export_to_markdown(
    page_no=None,  # All pages
    enable_chart_tables=True  # Include tables
)

with open(output_md, 'w', encoding='utf-8') as f:
    f.write(markdown_text)

print(f"✅ Markdown saved to: {output_md}")
print()

# Get statistics
from docling.datamodel.document import DocItemLabel

stats = {}
for item, level in doc.iterate_items():
    label = str(item.label)
    stats[label] = stats.get(label, 0) + 1

print("=" * 80)
print("📊 EXTRACTION STATISTICS")
print("=" * 80)
for label, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {label}: {count}")
print()
print(f"📁 Output files:")
print(f"   1. {output_json.name} - Complete JSON with all data")
print(f"   2. {output_md.name} - Human-readable Markdown")
print()
print("🎯 The JSON file contains EVERYTHING Docling extracted:")
print("   ✓ All element types and text")
print("   ✓ Complete table structure (cells, rows, cols)")
print("   ✓ Bounding boxes and coordinates")
print("   ✓ Provenance and metadata")
print("   ✓ All 11 Docling element types preserved")
print()
print("💡 To extract Chapter 1 only (pages 1-11), filter the JSON after loading")
print()
