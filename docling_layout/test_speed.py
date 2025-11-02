#!/usr/bin/env python3
"""
Quick speed test for Docling with GPU
Tests on just 3 pages to measure pages/second
"""
import time
from pathlib import Path
import sys

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)

pdf_path = Path(__file__).parent.parent.parent.parent.parent / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"

print("=" * 80)
print("🚀 DOCLING SPEED TEST")
print("=" * 80)
print(f"📄 PDF: {pdf_path.name}")
print(f"📑 Testing: Pages 1-3 (3 pages)")
print()

# Test 1: Lightweight GPU mode (your current config)
print("🔬 TEST 1: Lightweight GPU Mode")
print("-" * 80)

pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(
        num_threads=4,  # More threads
        device="cuda",
    ),
    do_ocr=False,
    do_picture_classification=False,
    do_picture_description=False,
    do_code_enrichment=False,
    do_formula_enrichment=False,
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,
        do_cell_matching=True,
    ),
    generate_page_images=False,
    generate_picture_images=False,
    generate_table_images=False,
)

format_options = {InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
converter = DocumentConverter(format_options=format_options)

print("⏱️  Starting conversion...")
start_time = time.time()

result = converter.convert(str(pdf_path))

end_time = time.time()
elapsed = end_time - start_time

print(f"✅ Conversion complete")
print(f"⏱️  Total time: {elapsed:.2f} seconds")
print(f"📊 Speed: {len(result.document.pages) / elapsed:.2f} pages/second")
print()

# Count elements
elements = []
for item in result.document.iterate_items():
    if isinstance(item, tuple):
        item, level = item
    if hasattr(item, 'prov') and item.prov:
        for prov in item.prov:
            if 1 <= prov.page_no <= 3:
                elements.append(item)

print(f"📦 Elements extracted: {len(elements)}")
print()

# Estimate for full document
full_pages = 399
estimated_time = full_pages / (len(result.document.pages) / elapsed)
estimated_hours = estimated_time / 3600

print("=" * 80)
print("📈 PROJECTIONS FOR FULL DOCUMENT (399 pages)")
print("=" * 80)
print(f"Estimated time: {estimated_time:.0f} seconds = {estimated_hours:.1f} hours")
print()

# Per chapter estimates
chapters = [
    ("Chapter 1", 11),
    ("Chapter 2", 79),
    ("Chapter 3", 63),
    ("Chapter 4", 6),
    ("Chapter 5", 12),
    ("Chapter 6", 94),
    ("Chapter 7", 82),
    ("Chapter 8", 1),
    ("Chapter 9", 33),
    ("Chapter 10", 11),
    ("Chapter 11", 7),
]

print("Per chapter estimates:")
print("-" * 60)
for name, pages in chapters:
    chapter_time = pages / (len(result.document.pages) / elapsed)
    chapter_mins = chapter_time / 60
    print(f"{name:12} ({pages:3} pages) → {chapter_mins:5.1f} minutes")
print("-" * 60)
total_estimate = sum(p[1] for p in chapters) / (len(result.document.pages) / elapsed) / 3600
print(f"{'TOTAL':12} ({sum(p[1] for p in chapters):3} pages) → {total_estimate:5.1f} hours")
print()

print("💡 Ways to speed up:")
print("   1. Process chapters in parallel (4 at once = 4x faster)")
print("   2. Use faster GPU (RTX 3060 = 2-3x faster)")
print("   3. Disable table detection (saves ~30%)")
print("   4. Process only the chapters you actually need")
print()
