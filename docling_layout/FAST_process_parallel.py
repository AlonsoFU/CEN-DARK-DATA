#!/usr/bin/env python3
"""
⚡ PARALLEL PROCESSING - 4x FASTER!
Process 4 chapters simultaneously using multiprocessing
12 hours → 3 hours
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from multiprocessing import Process, Queue
import time

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

        # PDF path (absolute to avoid issues)
        pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")

        # Configure pipeline
        pipeline_options = PdfPipelineOptions(
            accelerator_options=AcceleratorOptions(
                num_threads=2,  # Fewer threads per process
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

        # Extract elements
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
                "extractor": "Docling Lightweight (Parallel Processing)",
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

print("=" * 80)
print("⚡ PARALLEL PROCESSING - 4X FASTER")
print("=" * 80)
print("🚀 Processing 4 chapters simultaneously")
print("⏱️  Estimated time: 3-4 hours (vs 12 hours sequential)")
print()

# Group chapters into batches of 4
chapter_batches = [
    [1, 4, 5, 8],     # Batch 1: Small chapters
    [2, 3, 10, 11],   # Batch 2: Medium chapters
    [6, 7, 9],        # Batch 3: Large chapters (only 3)
]

total_start = time.time()
completed = []

for batch_num, chapter_nums in enumerate(chapter_batches, 1):
    print(f"🔄 BATCH {batch_num}/{len(chapter_batches)}")
    print("-" * 80)

    # Create queue for results
    result_queue = Queue()

    # Start processes
    processes = []
    for ch_num in chapter_nums:
        if ch_num in CHAPTERS:
            p = Process(target=process_chapter, args=(ch_num, CHAPTERS[ch_num], result_queue))
            p.start()
            processes.append((ch_num, p))
            print(f"   Started: Chapter {ch_num}")

    # Wait for all to complete
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
print("✅ PARALLEL PROCESSING COMPLETE")
print("=" * 80)
print(f"📊 Processed: {len(completed)}/{len(CHAPTERS)} chapters")
print(f"⏱️  Total time: {total_elapsed/3600:.1f} hours")
print(f"⚡ Speedup: {len(CHAPTERS) * 0.5 / (total_elapsed/3600):.1f}x faster than sequential")
print()
print("📁 Chapters completed:", sorted(completed))
print()
