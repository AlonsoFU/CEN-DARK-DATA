#!/usr/bin/env python3
"""
🔬 MEMORY TEST - Find EXACT VRAM usage per Docling worker
This will run ONE Docling process and measure actual GPU memory
"""
import sys
import torch
from pathlib import Path
import time

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🔬 DOCLING MEMORY USAGE TEST")
print("=" * 80)
print()

# Check initial GPU state
if not torch.cuda.is_available():
    print("❌ CUDA not available!")
    sys.exit(1)

print("📊 GPU Status BEFORE Docling:")
print("-" * 80)
total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
initial_allocated = torch.cuda.memory_allocated(0) / 1024**3
initial_reserved = torch.cuda.memory_reserved(0) / 1024**3
print(f"   Total VRAM:     {total_vram:.2f} GB")
print(f"   Allocated:      {initial_allocated:.2f} GB")
print(f"   Reserved:       {initial_reserved:.2f} GB")
print(f"   Free (approx):  {total_vram - initial_reserved:.2f} GB")
print()

# Import Docling (this loads models)
print("📦 Loading Docling libraries...")
start_time = time.time()

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)

load_time = time.time() - start_time
print(f"✅ Loaded in {load_time:.1f} seconds")
print()

# Check memory after import
after_import_allocated = torch.cuda.memory_allocated(0) / 1024**3
after_import_reserved = torch.cuda.memory_reserved(0) / 1024**3

print("📊 GPU Status AFTER importing Docling:")
print("-" * 80)
print(f"   Allocated:      {after_import_allocated:.2f} GB (+{after_import_allocated - initial_allocated:.2f} GB)")
print(f"   Reserved:       {after_import_reserved:.2f} GB (+{after_import_reserved - initial_reserved:.2f} GB)")
print(f"   Free (approx):  {total_vram - after_import_reserved:.2f} GB")
print()

# Configure lightweight pipeline
print("🔧 Configuring lightweight pipeline...")
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(
        num_threads=2,
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

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

print("🏗️  Creating DocumentConverter...")
converter = DocumentConverter(format_options=format_options)

after_converter_allocated = torch.cuda.memory_allocated(0) / 1024**3
after_converter_reserved = torch.cuda.memory_reserved(0) / 1024**3

print()
print("📊 GPU Status AFTER creating converter:")
print("-" * 80)
print(f"   Allocated:      {after_converter_allocated:.2f} GB (+{after_converter_allocated - after_import_allocated:.2f} GB)")
print(f"   Reserved:       {after_converter_reserved:.2f} GB (+{after_converter_reserved - after_import_reserved:.2f} GB)")
print(f"   Free (approx):  {total_vram - after_converter_reserved:.2f} GB")
print()

# Process a small document (just 3 pages to test)
pdf_path = project_root / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"

print("🔍 Processing 3 pages as test...")
print("   (This simulates one worker)")
print()

start_process = time.time()
result = converter.convert(str(pdf_path))
process_time = time.time() - start_process

after_process_allocated = torch.cuda.memory_allocated(0) / 1024**3
after_process_reserved = torch.cuda.memory_reserved(0) / 1024**3
peak_allocated = torch.cuda.max_memory_allocated(0) / 1024**3
peak_reserved = torch.cuda.max_memory_reserved(0) / 1024**3

print(f"✅ Processed {len(result.document.pages)} pages in {process_time:.1f} seconds")
print()

print("=" * 80)
print("📊 FINAL MEMORY ANALYSIS")
print("=" * 80)
print()
print("Memory after processing:")
print("-" * 80)
print(f"   Current allocated:  {after_process_allocated:.2f} GB")
print(f"   Current reserved:   {after_process_reserved:.2f} GB")
print(f"   Peak allocated:     {peak_allocated:.2f} GB ⭐")
print(f"   Peak reserved:      {peak_reserved:.2f} GB ⭐")
print()
print("Memory per stage:")
print("-" * 80)
print(f"   Import Docling:     +{after_import_reserved - initial_reserved:.2f} GB")
print(f"   Create Converter:   +{after_converter_reserved - after_import_reserved:.2f} GB")
print(f"   Process Document:   +{peak_reserved - after_converter_reserved:.2f} GB")
print(f"   ─────────────────────────────────")
print(f"   TOTAL PER WORKER:   ~{peak_reserved:.2f} GB ⭐⭐⭐")
print()

# Calculate safe worker count
system_reserve = 0.2  # GB
available_vram = total_vram - system_reserve
safe_workers = int(available_vram / peak_reserved)
safe_workers = max(1, min(safe_workers, 6))  # Between 1-6

print("=" * 80)
print("🎯 RECOMMENDATION FOR YOUR GPU")
print("=" * 80)
print(f"   Total VRAM:         {total_vram:.2f} GB")
print(f"   Per worker (peak):  {peak_reserved:.2f} GB")
print(f"   System reserve:     {system_reserve:.2f} GB")
print(f"   Available:          {available_vram:.2f} GB")
print(f"   ─────────────────────────────────")
print(f"   SAFE WORKERS:       {safe_workers} ⭐")
print(f"   MAX WORKERS (risky): {int((total_vram - 0.1) / peak_reserved)}")
print()

if safe_workers >= 4:
    print("✅ Your GPU can handle 4 parallel workers safely!")
    print(f"   Estimated time: {12 / 4:.1f} hours")
elif safe_workers == 3:
    print("🟡 Your GPU can handle 3 parallel workers safely")
    print(f"   Estimated time: {12 / 3:.1f} hours")
    print("   (4 workers might work but could crash)")
elif safe_workers == 2:
    print("🟠 Your GPU can handle 2 parallel workers safely")
    print(f"   Estimated time: {12 / 2:.1f} hours")
    print("   (Not much speedup, consider sequential or ultra-fast mode)")
else:
    print("🔴 Your GPU can only handle 1 worker safely")
    print("   Parallel processing won't help much")
    print("   Consider: Ultra-fast mode or CPU processing")

print()
print("💡 To use this in parallel script:")
print(f"   Edit FAST_process_parallel.py")
print(f"   Change: chapter_batches to use {safe_workers} workers per batch")
print()
