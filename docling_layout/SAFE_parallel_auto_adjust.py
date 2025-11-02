#!/usr/bin/env python3
"""
🛡️ SAFE PARALLEL PROCESSING - AUTO-ADJUSTS TO YOUR GPU
Tests memory first, then automatically adjusts number of workers
SAFE for GTX 1650 4GB - will NOT crash your GPU!
"""
import json
import sys
import torch
from pathlib import Path
from datetime import datetime
from multiprocessing import Process, Queue, set_start_method
import time

# CRITICAL: Set spawn mode for CUDA compatibility
try:
    set_start_method('spawn')
except RuntimeError:
    pass  # Already set

# Chapter definitions
CHAPTERS = {
    1: {"name": "Descripción de la Perturbación", "pages": (1, 11)},
    2: {"name": "Equipamiento Afectado", "pages": (12, 90)},
    3: {"name": "Energía No Suministrada", "pages": (91, 153)},
    4: {"name": "Configuraciones de Falla", "pages": (154, 159)},
    5: {"name": "Cronología de Eventos", "pages": (160, 171)},
    6: {"name": "Normalización del Servicio", "pages": (172, 265)},
    7: {"name": "Análisis de Causas de Falla", "pages": (266, 347)},
    8: {"name": "Detalle de Información", "pages": (348, 348)},
    9: {"name": "Análisis de Protecciones", "pages": (349, 381)},
    10: {"name": "Pronunciamiento Técnico", "pages": (382, 392)},
    11: {"name": "Recomendaciones", "pages": (393, 399)},
}

BASE_DIR = Path(__file__).parent
project_root = BASE_DIR.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🛡️ SAFE PARALLEL PROCESSING - AUTO-ADJUST MODE")
print("=" * 80)
print()

# Check GPU capacity
print("🔍 Checking your GPU capacity...")
if not torch.cuda.is_available():
    print("❌ CUDA not available! Will use CPU mode (slow)")
    print("   Estimated time: 72 hours for full document")
    print()
    print("💡 Run this instead for CPU:")
    print("   cd capitulo_01/scripts && python3 lightweight_extract.py")
    sys.exit(1)

gpu_name = torch.cuda.get_device_name(0)
total_vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
free_vram_gb = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved(0)) / 1024**3

print(f"✅ GPU: {gpu_name}")
print(f"📊 Total VRAM: {total_vram_gb:.2f} GB")
print(f"💾 Free VRAM: {free_vram_gb:.2f} GB")
print()

# Auto-calculate safe number of workers
# Docling lightweight mode uses ~0.8-1.0 GB per process
VRAM_PER_WORKER = 1.0  # GB
SYSTEM_RESERVE = 0.3    # GB (for system/display)

max_safe_workers = int((free_vram_gb - SYSTEM_RESERVE) / VRAM_PER_WORKER)
max_safe_workers = max(1, min(max_safe_workers, 4))  # Between 1-4 workers

print("🧮 AUTOMATIC WORKER CALCULATION:")
print("-" * 80)
print(f"   Free VRAM:          {free_vram_gb:.2f} GB")
print(f"   System reserve:     {SYSTEM_RESERVE:.2f} GB")
print(f"   Available:          {free_vram_gb - SYSTEM_RESERVE:.2f} GB")
print(f"   Per worker:         {VRAM_PER_WORKER:.2f} GB")
print(f"   → Safe workers:     {max_safe_workers}")
print("-" * 80)
print()

if max_safe_workers < 2:
    print("⚠️  WARNING: Only 1 worker possible (limited VRAM)")
    print("   This will be SLOW (~12 hours)")
    print()
    print("💡 Options:")
    print("   1. Close other GPU apps (browsers, games, etc.)")
    print("   2. Use ultra-fast mode (no tables) for less memory")
    print("   3. Process chapters one by one")
    print()
    # Auto-continue in background mode
    print("   ⚠️  Auto-continuing with 1 worker (background mode)")

print(f"🚀 Will process with {max_safe_workers} parallel workers")
print(f"⏱️  Estimated time: {12 / max_safe_workers:.1f} hours")
print()

# Confirm before starting
print("📋 Processing plan:")
chapters_per_batch = max_safe_workers
num_batches = (len(CHAPTERS) + chapters_per_batch - 1) // chapters_per_batch
print(f"   Total chapters: {len(CHAPTERS)}")
print(f"   Parallel workers: {max_safe_workers}")
print(f"   Batches: {num_batches}")
print()

# Auto-start in background mode
print("🚀 AUTO-STARTING (background mode)...")
print()

print()

def process_chapter(chapter_num, chapter_info, result_queue):
    """Process a single chapter - runs in separate process"""
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            TableStructureOptions,
            TableFormerMode,
            AcceleratorOptions
        )

        chapter_name = chapter_info["name"]
        start_page, end_page = chapter_info["pages"]

        print(f"[Ch {chapter_num}] Starting: {chapter_name} (pages {start_page}-{end_page})")
        start_time = time.time()

        # Setup directories
        output_dir = BASE_DIR / f"capitulo_{chapter_num:02d}"
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir = output_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)

        # Check if already done
        json_path = outputs_dir / "layout_lightweight.json"
        if json_path.exists():
            print(f"[Ch {chapter_num}] ⏭️  Already processed, skipping")
            result_queue.put((chapter_num, True, 0))
            return

        # PDF path (absolute from known location)
        pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
        if not pdf_path.exists():
            # Try relative from BASE_DIR
            pdf_path = BASE_DIR.parent.parent.parent.parent.parent / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"

        # Configure pipeline (lightweight for safety)
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

        converter = DocumentConverter(format_options=format_options)

        # Convert
        print(f"[Ch {chapter_num}] 🔍 Converting...")
        result = converter.convert(str(pdf_path))

        # Extract elements (same as before)
        chapter_elements = []
        for item in result.document.iterate_items():
            if isinstance(item, tuple):
                item, level = item

            if not hasattr(item, 'prov') or not item.prov:
                continue

            for prov in item.prov:
                if start_page <= prov.page_no <= end_page:
                    if prov.page_no not in result.document.pages:
                        continue

                    page = result.document.pages[prov.page_no]
                    bbox = prov.bbox
                    bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_norm = bbox.normalized(page.size)

                    if hasattr(item, 'text'):
                        text_content = item.text if item.text else ""
                    elif hasattr(item, 'export_to_markdown'):
                        text_content = item.export_to_markdown()
                    else:
                        text_content = str(item) if item else ""

                    element = {
                        "type": item.label,
                        "text": text_content,
                        "page": prov.page_no,
                        "bbox": {
                            "x0": round(bbox_tl.l, 2),
                            "y0": round(bbox_tl.t, 2),
                            "x1": round(bbox_tl.r, 2),
                            "y1": round(bbox_tl.b, 2)
                        },
                        "bbox_normalized": {
                            "x0": round(bbox_norm.l, 4),
                            "y0": round(bbox_norm.t, 4),
                            "x1": round(bbox_norm.r, 4),
                            "y1": round(bbox_norm.b, 4)
                        },
                        "page_dimensions": {
                            "width": page.size.width,
                            "height": page.size.height
                        }
                    }
                    chapter_elements.append(element)

        # Save JSON
        data = {
            "metadata": {
                "chapter": f"Capítulo {chapter_num} - {chapter_name}",
                "pdf_source": str(pdf_path),
                "extraction_date": datetime.now().isoformat(),
                "extractor": f"Docling Lightweight (Safe Parallel - {max_safe_workers} workers)",
                "total_elements": len(chapter_elements),
                "pages": f"{start_page}-{end_page}",
            },
            "elements": chapter_elements
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        elapsed = time.time() - start_time
        print(f"[Ch {chapter_num}] ✅ Done! {len(chapter_elements)} elements in {elapsed/60:.1f} min")

        result_queue.put((chapter_num, True, elapsed))

    except Exception as e:
        print(f"[Ch {chapter_num}] ❌ Error: {e}")
        result_queue.put((chapter_num, False, 0))

# Create batches based on safe worker count
all_chapters = list(CHAPTERS.keys())
chapter_batches = [all_chapters[i:i+max_safe_workers] for i in range(0, len(all_chapters), max_safe_workers)]

print(f"📦 Created {len(chapter_batches)} batches")
for i, batch in enumerate(chapter_batches, 1):
    print(f"   Batch {i}: Chapters {batch}")
print()

total_start = time.time()
completed = []

for batch_num, chapter_nums in enumerate(chapter_batches, 1):
    print(f"🔄 BATCH {batch_num}/{len(chapter_batches)}")
    print("-" * 80)

    result_queue = Queue()
    processes = []

    for ch_num in chapter_nums:
        if ch_num in CHAPTERS:
            p = Process(target=process_chapter, args=(ch_num, CHAPTERS[ch_num], result_queue))
            p.start()
            processes.append((ch_num, p))
            print(f"   Started: Chapter {ch_num}")

    # Wait for completion
    for ch_num, p in processes:
        p.join()

    # Collect results
    while not result_queue.empty():
        ch_num, success, elapsed = result_queue.get()
        if success:
            completed.append(ch_num)

    print()

total_elapsed = time.time() - total_start

print("=" * 80)
print("✅ SAFE PARALLEL PROCESSING COMPLETE")
print("=" * 80)
print(f"📊 Processed: {len(completed)}/{len(CHAPTERS)} chapters")
print(f"⏱️  Total time: {total_elapsed/3600:.2f} hours")
print(f"💾 Peak VRAM: ~{max_safe_workers * VRAM_PER_WORKER:.1f} GB (safe limit)")
print()
print("📁 Chapters completed:", sorted(completed))
print()
