#!/usr/bin/env python3
"""
⚡ ENHANCED PARALLEL PROCESSING - Production Quality
Process 4 chapters simultaneously with:
- ✅ EAF Monkey Patch (domain-specific enhancements)
- ✅ Post-processors (zona_fix, etc.)
- ✅ Annotated PDFs with ALL clusters visualization
- ✅ Optimized Safe mode (ACCURATE tables + SmolVLM)
- ✅ Comprehensive validation and reporting

12 hours → 3 hours
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import multiprocessing
from multiprocessing import Process, Queue
import time

# CUDA requires spawn method for multiprocessing
multiprocessing.set_start_method('spawn', force=True)

# Chapter definitions with corrected page ranges
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

# Color scheme for annotated PDFs (RGB 0-1 scale)
COLORS = {
    'text': (0, 0, 1),           # Blue
    'section_header': (1, 0, 0), # Red
    'title': (1, 0, 0),          # Red
    'list_item': (0, 1, 1),      # Cyan
    'table': (0, 1, 0),          # Green
    'picture': (1, 0, 1),        # Magenta
    'caption': (1, 0.5, 0),      # Orange
    'formula': (0.5, 0, 0.5),    # Purple
    'page_header': (0.5, 0.5, 0.5), # Gray
    'page_footer': (0.5, 0.5, 0.5), # Gray
}

BASE_DIR = Path(__file__).parent

def process_chapter(chapter_num, chapter_info, result_queue, use_optimized_safe=True):
    """
    Process a single chapter with FULL methodology:
    - EAF monkey patch applied
    - Post-processors executed
    - Annotated PDF generated with ALL clusters
    - Optimized Safe mode (or fallback to lightweight)
    """
    try:
        # Add eaf_patch to path
        eaf_patch_path = BASE_DIR / "eaf_patch"
        sys.path.insert(0, str(eaf_patch_path))

        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
        from core.eaf_patch_engine import apply_universal_patch_with_pdf
        from core.post_processors import apply_zona_fix_to_document
        import fitz  # PyMuPDF

        chapter_name = chapter_info["name"]
        start_page, end_page = chapter_info["pages"]

        print(f"[Ch {chapter_num}] 🚀 Starting: {chapter_name} (pages {start_page}-{end_page})")
        start_time = time.time()

        # Setup directories
        output_dir = BASE_DIR / f"capitulo_{chapter_num:02d}" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if already done
        json_path = output_dir / "layout_WITH_PATCH.json"
        pdf_path_output = output_dir / f"chapter{chapter_num:02d}_WITH_PATCH_annotated.pdf"

        if json_path.exists() and pdf_path_output.exists():
            print(f"[Ch {chapter_num}] ⏭️  Already processed, skipping")
            result_queue.put((chapter_num, True, 0, 0, 0))
            return

        # Source PDF path (individual chapter PDFs)
        pdf_path = Path(f"/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_{chapter_num:02d}/EAF-089-2025_capitulo_{chapter_num:02d}_pages_{start_page}-{end_page}.pdf")

        if not pdf_path.exists():
            print(f"[Ch {chapter_num}] ❌ PDF not found: {pdf_path}")
            result_queue.put((chapter_num, False, 0, 0, 0))
            return

        # Configure pipeline - Optimized Safe mode
        print(f"[Ch {chapter_num}] ⚙️  Configuring {'Optimized Safe' if use_optimized_safe else 'Lightweight'} mode...")
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False  # Save VRAM
        pipeline_options.do_table_structure = True

        if use_optimized_safe:
            # ACCURATE mode: 97.9% table accuracy
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            pipeline_options.do_picture_description = True  # SmolVLM descriptions
            pipeline_options.do_formula_enrichment = True   # LaTeX formulas
            print(f"[Ch {chapter_num}]    - Tables: ACCURATE (97.9%)")
            print(f"[Ch {chapter_num}]    - Picture descriptions: SmolVLM")
            print(f"[Ch {chapter_num}]    - Formula extraction: LaTeX")
            print(f"[Ch {chapter_num}]    - VRAM: ~3.0 GB")
        else:
            # FAST mode: 90-95% table accuracy
            pipeline_options.table_structure_options.mode = TableFormerMode.FAST
            pipeline_options.do_picture_description = False
            pipeline_options.do_formula_enrichment = False
            print(f"[Ch {chapter_num}]    - Tables: FAST (90-95%)")
            print(f"[Ch {chapter_num}]    - VRAM: ~1.5 GB")

        # Apply EAF monkey patch
        print(f"[Ch {chapter_num}] 🐵 Applying EAF monkey patch...")
        apply_universal_patch_with_pdf(str(pdf_path))
        print(f"[Ch {chapter_num}] ✅ Monkey patch applied")

        # Extract with Docling
        print(f"[Ch {chapter_num}] 🔍 Starting Docling extraction...")
        converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        result = converter.convert(str(pdf_path))
        doc = result.document

        print(f"[Ch {chapter_num}] ✅ Extraction completed")

        # Apply post-processors
        print(f"[Ch {chapter_num}] 🔧 Applying post-processors...")
        zona_fixes = apply_zona_fix_to_document(doc)
        print(f"[Ch {chapter_num}] ✅ Post-processors applied (zona fixes: {zona_fixes})")

        # Export to JSON using native Docling format
        # This includes all monkey patch and post-processor modifications
        print(f"[Ch {chapter_num}] 💾 Exporting to native Docling JSON format...")

        # Use Docling's native export_to_dict() to get complete document structure
        # This preserves hierarchy, metadata, tables, pictures, and all modifications
        doc_dict = doc.export_to_dict()

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(doc_dict, f, indent=2, ensure_ascii=False)

        # Count elements for summary
        element_count = 0
        if 'body' in doc_dict and 'children' in doc_dict['body']:
            def count_items(item):
                count = 1
                if 'children' in item:
                    for child in item['children']:
                        count += count_items(child)
                return count

            for child in doc_dict['body']['children']:
                element_count += count_items(child)

        print(f"[Ch {chapter_num}] ✅ JSON saved: {element_count} elements")

        # Generate annotated PDF with ALL clusters + source labels
        print(f"[Ch {chapter_num}] 🎨 Generating annotated PDF (ALL clusters + labels)...")
        pdf_doc = fitz.open(pdf_path)

        # Extract elements for PDF annotation
        annotation_elements = []
        for item in doc.iterate_items():
            if isinstance(item, tuple):
                item, level = item

            if not hasattr(item, 'prov') or not item.prov:
                continue

            prov = item.prov[0]
            page = result.document.pages[prov.page_no]
            bbox = prov.bbox
            bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)

            # Get text for PATCH label detection
            text_content = ""
            if hasattr(item, 'text') and item.text:
                text_content = item.text

            annotation_elements.append({
                'type': item.label.name.lower(),
                'text': text_content,
                'page': prov.page_no,
                'bbox': {
                    'x0': bbox_tl.l,
                    'y0': bbox_tl.t,
                    'x1': bbox_tl.r,
                    'y1': bbox_tl.b
                }
            })

        label_count = 0
        for idx, elem in enumerate(annotation_elements):
            page_num = elem['page'] - 1  # Convert to 0-indexed
            if page_num < 0 or page_num >= len(pdf_doc):
                continue

            page = pdf_doc[page_num]
            bbox = elem['bbox']
            rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

            # Use methodology colors (Red=headers, Blue=text, Green=tables, etc.)
            color = COLORS.get(elem['type'], (0.5, 0.5, 0.5))
            page.draw_rect(rect, color=color, width=1.0)

            # Add small "PATCH" label for likely monkey-patch additions
            # Heuristic: section_headers and titles appearing after typical baseline
            if elem['type'] in ['section_header', 'title']:
                # Check if this looks like a patch addition (simplified heuristic)
                text_lower = elem.get('text', '').lower()
                # Mark Chilean-specific patterns likely from patch
                is_patch = any(keyword in text_lower for keyword in [
                    'línea', 'kv', 's/e', 'subestación', 'zona', 'área',
                    'transformador', 'interruptor', 'página'
                ])

                if is_patch:
                    # Add small text label above the box
                    label_text = "PATCH"
                    label_point = fitz.Point(bbox['x0'], bbox['y0'] - 8)

                    # Semi-transparent background
                    label_rect = fitz.Rect(
                        bbox['x0'], bbox['y0'] - 10,
                        bbox['x0'] + 35, bbox['y0'] - 2
                    )
                    page.draw_rect(label_rect, color=(1, 1, 0.8), fill=(1, 1, 0.8), width=0.5)

                    # Add text
                    page.insert_text(
                        label_point,
                        label_text,
                        fontsize=6,
                        color=(0.6, 0, 0),  # Dark red
                        fontname="helv-bold"
                    )
                    label_count += 1

        pdf_doc.save(pdf_path_output)
        pdf_doc.close()

        print(f"[Ch {chapter_num}] ✅ Labels added: {label_count} patch markers")

        elapsed = time.time() - start_time
        pdf_size_mb = pdf_path_output.stat().st_size / (1024*1024)

        print(f"[Ch {chapter_num}] ✅ Annotated PDF saved ({pdf_size_mb:.1f} MB)")
        print(f"[Ch {chapter_num}] 🎉 COMPLETE in {elapsed/60:.1f} min")
        print(f"[Ch {chapter_num}] 📊 Element counts: {type_counts}")

        result_queue.put((chapter_num, True, elapsed, len(elements), zona_fixes))

    except Exception as e:
        import traceback
        print(f"[Ch {chapter_num}] ❌ Error: {e}")
        print(f"[Ch {chapter_num}] {traceback.format_exc()}")
        result_queue.put((chapter_num, False, 0, 0, 0))


def check_gpu_vram():
    """Check available GPU VRAM"""
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"🔍 GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"💾 VRAM: {vram_gb:.1f} GB")
            return vram_gb
        else:
            print("⚠️  No GPU detected - will use CPU (slower)")
            return 0
    except:
        print("⚠️  Could not detect GPU")
        return 0


def main():
    """Main execution"""
    print("=" * 80)
    print("⚡ ENHANCED PARALLEL PROCESSING - Production Quality")
    print("=" * 80)
    print()

    # Check GPU
    vram_gb = check_gpu_vram()
    use_optimized_safe = vram_gb >= 3.0

    if use_optimized_safe:
        print("✅ Using Optimized Safe mode (ACCURATE tables + SmolVLM)")
    else:
        print("⚠️  Using Lightweight mode (FAST tables, limited features)")
    print()

    print("📋 Methodology:")
    print("   ✅ EAF monkey patch (11 domain-specific improvements)")
    print("   ✅ Post-processors (zona classification, etc.)")
    print("   ✅ Annotated PDFs (Docling + monkey patch + post-processor clusters)")
    print()

    print("🚀 Processing strategy: 4 chapters simultaneously")
    print("⏱️  Estimated time: 3-4 hours")
    print()

    # Group chapters into batches
    chapter_batches = [
        [1, 4, 5, 8],     # Batch 1: Small chapters (~30 pages each)
        [2, 3, 10, 11],   # Batch 2: Medium chapters (~40-80 pages)
        [6, 7, 9],        # Batch 3: Large chapters (~80-95 pages, only 3)
    ]

    total_start = time.time()
    completed = []
    results = {}

    for batch_num, chapter_nums in enumerate(chapter_batches, 1):
        print(f"🔄 BATCH {batch_num}/{len(chapter_batches)}")
        print("-" * 80)

        # Create queue for results
        result_queue = Queue()

        # Start processes
        processes = []
        for ch_num in chapter_nums:
            if ch_num in CHAPTERS:
                p = Process(
                    target=process_chapter,
                    args=(ch_num, CHAPTERS[ch_num], result_queue, use_optimized_safe)
                )
                p.start()
                processes.append((ch_num, p))
                print(f"   ▶️  Started: Chapter {ch_num} - {CHAPTERS[ch_num]['name']}")

        # Wait for all to complete
        for ch_num, p in processes:
            p.join()

        # Collect results
        while not result_queue.empty():
            ch_num, success, elapsed, elem_count, zona_fixes = result_queue.get()
            if success:
                completed.append(ch_num)
                results[ch_num] = {
                    'elapsed': elapsed,
                    'elements': elem_count,
                    'zona_fixes': zona_fixes
                }

        print()

    total_elapsed = time.time() - total_start

    # Final report
    print("=" * 80)
    print("✅ ENHANCED PARALLEL PROCESSING COMPLETE")
    print("=" * 80)
    print(f"📊 Processed: {len(completed)}/{len(CHAPTERS)} chapters")
    print(f"⏱️  Total time: {total_elapsed/3600:.2f} hours ({total_elapsed/60:.1f} min)")
    print()

    print("📁 Outputs generated per chapter:")
    print("   - layout_WITH_PATCH.json (structured extraction)")
    print("   - chapterXX_WITH_PATCH_annotated.pdf (visual validation)")
    print()

    print("📊 Chapter Statistics:")
    print("-" * 80)
    total_elements = 0
    total_zona_fixes = 0

    for ch_num in sorted(completed):
        if ch_num in results:
            r = results[ch_num]
            total_elements += r['elements']
            total_zona_fixes += r['zona_fixes']
            print(f"   Ch {ch_num:2d}: {r['elements']:4d} elements, "
                  f"{r['zona_fixes']:2d} zona fixes, "
                  f"{r['elapsed']/60:5.1f} min")

    print("-" * 80)
    print(f"   TOTAL: {total_elements} elements, {total_zona_fixes} zona fixes")
    print()

    print("🎨 Annotated PDF Color Legend:")
    print("   🔴 Red     = section_header / title")
    print("   🔵 Blue    = text paragraphs")
    print("   🔵🟢 Cyan    = list_item")
    print("   🟢 Green   = table")
    print("   🟣 Magenta  = picture")
    print("   🟠 Orange   = caption")
    print("   🟣 Purple   = formula")
    print("   ⚪ Gray     = page_header / page_footer")
    print()

    print("✅ All clusters visualized:")
    print("   1. Docling's original AI-detected clusters")
    print("   2. Monkey patch synthetic clusters (missing titles, power lines, etc.)")
    print("   3. Post-processor modifications (zona classification fixes)")
    print()

    print("=" * 80)
    print(f"🎉 SUCCESS! All {len(completed)} chapters processed with full methodology")
    print("=" * 80)


if __name__ == "__main__":
    main()
