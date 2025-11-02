#!/usr/bin/env python3
"""
COMPLETE REPROCESSING: Extract ALL 11 Chapters with Docling + EAF Patch
AND Generate Annotated PDFs with Cluster Bounding Boxes

This script:
1. Extracts each chapter using Docling with EAF monkey patch
2. Generates layout_WITH_PATCH.json with all elements and bounding boxes
3. Creates annotated PDFs with colored bounding boxes for visual inspection
4. Provides detailed progress tracking and statistics

Memory-optimized for 4GB GPU (GTX 1650) with lightweight configuration
Expected total time: ~60-90 minutes for all 11 chapters
"""
import sys
import json
import time
import fitz
from pathlib import Path
from datetime import datetime

# Chapter definitions with correct page ranges
CHAPTERS = [
    {"num": 1, "pages": "1-11", "estimated_mins": 2},
    {"num": 2, "pages": "12-90", "estimated_mins": 8},
    {"num": 3, "pages": "91-152", "estimated_mins": 7},
    {"num": 4, "pages": "153-159", "estimated_mins": 2},
    {"num": 5, "pages": "160-171", "estimated_mins": 3},
    {"num": 6, "pages": "172-265", "estimated_mins": 10},
    {"num": 7, "pages": "266-347", "estimated_mins": 9},
    {"num": 8, "pages": "348-348", "estimated_mins": 1},
    {"num": 9, "pages": "349-381", "estimated_mins": 4},
    {"num": 10, "pages": "382-392", "estimated_mins": 3},
    {"num": 11, "pages": "393-399", "estimated_mins": 2},
]

# Standard Docling colors (from METHODOLOGY)
COLORS = {
    'text': (0, 0, 1),           # Blue
    'section_header': (1, 0, 0),  # Red
    'title': (1, 0.5, 0),         # Orange
    'list_item': (0, 0.7, 0.7),   # Cyan
    'table': (0, 0.7, 0),         # Green
    'picture': (1, 0, 1),         # Magenta
    'caption': (0.8, 0.4, 0),     # Brown
    'formula': (1, 0.8, 0),       # Yellow
    'footnote': (0.8, 0.4, 0),    # Brown
    'page_header': (0.5, 0.5, 0.5),  # Gray
    'page_footer': (0.5, 0.5, 0.5),  # Gray
}

COLOR_NAMES = {
    (1, 0, 0): "Red",
    (0, 0.7, 0.7): "Cyan",
    (0, 0.7, 0): "Green",
    (0, 0, 1): "Blue",
    (0.8, 0.4, 0): "Brown",
    (1, 0.5, 0): "Orange",
    (1, 0, 1): "Magenta",
    (1, 0.8, 0): "Yellow",
    (0.5, 0.5, 0.5): "Gray"
}

BASE_PATH = Path(__file__).parent
PDF_BASE = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr")


def extract_chapter_with_patch(chapter_num, chapter_info):
    """Extract a chapter using Docling + EAF patch"""
    print("\n" + "=" * 80)
    print(f"📦 EXTRACTING CHAPTER {chapter_num}")
    print("=" * 80)

    pages = chapter_info['pages']

    # Import Docling modules
    eaf_patch_path = BASE_PATH / "eaf_patch"
    sys.path.insert(0, str(eaf_patch_path))

    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from core.eaf_patch_engine import apply_universal_patch_with_pdf
    from core.post_processors import apply_zona_fix_to_document

    # PDF path
    pdf_path = PDF_BASE / f"capitulo_{chapter_num:02d}" / f"EAF-089-2025_capitulo_{chapter_num:02d}_pages_{pages}.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return None

    print(f"📄 PDF: {pdf_path.name}")
    print(f"📄 Pages: {pages}")
    print(f"⏱️  Estimated time: ~{chapter_info['estimated_mins']} minutes")

    # Apply EAF monkey patch
    print("\n🔧 Applying EAF monkey patch...")
    apply_universal_patch_with_pdf(pdf_path)

    # Configure Docling (lightweight mode for 4GB GPU)
    print("⚙️  Configuring Docling (lightweight mode)...")
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False  # Disable OCR (-1.5 GB VRAM)
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.table_structure_options.mode = TableFormerMode.FAST  # Fast tables (-400 MB vs ACCURATE)

    converter = DocumentConverter(
        format_options={
            PdfFormatOption: pipeline_options,
        }
    )

    # Extract with patch
    start_time = datetime.now()
    print(f"🔄 Starting extraction at {start_time.strftime('%H:%M:%S')}...")

    try:
        result = converter.convert(str(pdf_path))
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    print(f"✅ Extraction complete in {duration:.1f} minutes")

    # Apply Zona fix (document-level post-processor)
    print("🔧 Applying Zona classification fix...")
    doc = result.document
    reclassified_count = apply_zona_fix_to_document(doc)
    print(f"✅ Reclassified {reclassified_count} elements")

    # Note: Isolated list-item fix now runs in monkey patch (page-level)

    # Export to JSON
    output_dir = BASE_PATH / f"capitulo_{chapter_num:02d}" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "layout_WITH_PATCH.json"

    print("\n📝 Exporting to JSON...")
    elements = []

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
                        # Convert from bottom-left to top-left origin
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

    # Save JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'elements': elements,
            'total_elements': len(elements),
            'chapter': chapter_num,
            'pages': pages,
            'extracted_at': datetime.now().isoformat(),
            'extraction_time_minutes': duration
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {output_json}")
    print(f"📊 Total elements: {len(elements)}")

    # Element statistics
    stats = {}
    for elem in elements:
        elem_type = elem['type']
        stats[elem_type] = stats.get(elem_type, 0) + 1

    print("\n📊 Elements by type:")
    for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {elem_type:<20}: {count:>4}")

    return {
        'json_path': output_json,
        'pdf_path': pdf_path,
        'elements': elements,
        'stats': stats,
        'duration_minutes': duration
    }


def create_annotated_pdf(chapter_num, extraction_result):
    """Create annotated PDF with colored bounding boxes"""
    print("\n" + "=" * 80)
    print(f"🎨 CREATING ANNOTATED PDF FOR CHAPTER {chapter_num}")
    print("=" * 80)

    json_path = extraction_result['json_path']
    pdf_path = extraction_result['pdf_path']
    elements = extraction_result['elements']

    output_pdf = json_path.parent / f"capitulo_{chapter_num:02d}_annotated_WITH_PATCH.pdf"

    print(f"📄 Source PDF: {pdf_path.name}")
    print(f"📊 Drawing {len(elements)} bounding boxes...")

    # Open PDF
    doc = fitz.open(pdf_path)

    # Draw boxes
    boxes_drawn = 0
    color_counts = {}

    for elem in elements:
        if not elem.get('bbox'):
            continue

        bbox = elem['bbox']
        page_num_json = elem['page']

        # JSON uses 1-indexed pages, PyMuPDF uses 0-indexed
        page_idx = page_num_json - 1

        if 0 <= page_idx < len(doc):
            page = doc[page_idx]

            # Extract label name
            label = elem['type']
            if isinstance(label, str) and '.' in label:
                label = label.split('.')[-1].lower()
            else:
                label = str(label).lower()

            # Get color
            color = COLORS.get(label, (0.5, 0.5, 0.5))

            # Count
            color_counts[label] = color_counts.get(label, 0) + 1

            # Draw rectangle
            rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
            page.draw_rect(rect, color=color, width=2)

            boxes_drawn += 1

    print(f"✅ Drew {boxes_drawn} boxes")

    # Add legend on first page
    page = doc[0]
    legend_x = 420
    legend_y = 30
    legend_height = min(15 + len(color_counts) * 12, 120)
    legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 160, legend_y + legend_height)
    page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
    page.insert_text(fitz.Point(legend_x, legend_y), f"Chapter {chapter_num} - Docling+Patch", fontsize=9, color=(0, 0, 0))

    y_offset = legend_y + 15
    for label in sorted(color_counts.keys(), key=lambda x: color_counts[x], reverse=True)[:7]:
        color = COLORS.get(label, (0.5, 0.5, 0.5))
        color_name = COLOR_NAMES.get(color, "Unknown")
        color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
        page.draw_rect(color_rect, color=color, fill=color, width=0)
        page.insert_text(fitz.Point(legend_x + 15, y_offset), f"{label} ({color_counts[label]})", fontsize=7, color=(0, 0, 0))
        y_offset += 12

    # Save
    doc.save(output_pdf)
    doc.close()

    print(f"✅ Saved: {output_pdf}")
    print("\n📊 Bounding boxes by type:")
    for label, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
        color = COLORS.get(label, (0.5, 0.5, 0.5))
        color_name = COLOR_NAMES.get(color, "Unknown")
        print(f"   {label:<20} ({color_name:<8}): {count:>4} boxes")

    return output_pdf


def main():
    """Main batch processing function"""
    print("=" * 80)
    print("🔄 COMPLETE REPROCESSING: ALL 11 CHAPTERS WITH DOCLING + EAF PATCH")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Extract all 11 chapters using Docling + EAF monkey patch")
    print("  2. Generate layout_WITH_PATCH.json with all elements and bounding boxes")
    print("  3. Create annotated PDFs with colored bounding boxes")
    print("\n⚙️  Configuration:")
    print("  - Memory-optimized for 4GB GPU (GTX 1650)")
    print("  - Lightweight mode: OCR disabled, FAST table detection")
    print("  - Expected VRAM usage: ~2.0 GB (safe for 3.9 GB available)")
    print("\n📊 Processing plan:")

    total_estimated_time = sum(ch['estimated_mins'] for ch in CHAPTERS)

    for ch in CHAPTERS:
        print(f"  Chapter {ch['num']:2d} (pages {ch['pages']:>8}): ~{ch['estimated_mins']} min")

    print(f"\n⏱️  Total estimated time: ~{total_estimated_time} minutes ({total_estimated_time/60:.1f} hours)")
    print("\n⚠️  IMPORTANT:")
    print("  - Do NOT run other GPU processes during batch extraction")
    print("  - Monitor GPU usage: watch -n 1 nvidia-smi")
    print("  - Safe to cancel anytime (Ctrl+C)")
    print("\n🚀 Starting batch processing in 3 seconds...\n")

    time.sleep(3)

    batch_start = datetime.now()
    results = []
    successful = []
    failed = []

    for chapter_info in CHAPTERS:
        chapter_num = chapter_info['num']

        try:
            # Extract chapter
            extraction_result = extract_chapter_with_patch(chapter_num, chapter_info)

            if extraction_result is None:
                failed.append(chapter_num)
                results.append({
                    'chapter': chapter_num,
                    'status': 'FAILED',
                    'reason': 'Extraction failed'
                })
                continue

            # Create annotated PDF
            try:
                output_pdf = create_annotated_pdf(chapter_num, extraction_result)
                successful.append(chapter_num)
                results.append({
                    'chapter': chapter_num,
                    'status': 'SUCCESS',
                    'elements': len(extraction_result['elements']),
                    'duration': f"{extraction_result['duration_minutes']:.1f} min",
                    'json': str(extraction_result['json_path']),
                    'pdf': str(output_pdf)
                })
            except Exception as e:
                print(f"\n❌ Visualization failed: {e}")
                failed.append(chapter_num)
                results.append({
                    'chapter': chapter_num,
                    'status': 'PARTIAL',
                    'reason': f'JSON created but PDF visualization failed: {e}'
                })

        except KeyboardInterrupt:
            print("\n\n⚠️  Batch processing cancelled by user")
            break

        except Exception as e:
            print(f"\n❌ ERROR processing chapter {chapter_num}:")
            print(f"   {e}")
            failed.append(chapter_num)
            results.append({
                'chapter': chapter_num,
                'status': 'FAILED',
                'reason': str(e)
            })
            import traceback
            traceback.print_exc()

    batch_end = datetime.now()
    total_duration = (batch_end - batch_start).total_seconds() / 60

    # Final summary
    print("\n" + "=" * 80)
    print("📊 BATCH PROCESSING COMPLETE")
    print("=" * 80)

    print("\n📋 Results:")
    for result in results:
        ch = result['chapter']
        if result['status'] == 'SUCCESS':
            print(f"✅ Chapter {ch:2d}: {result['elements']:4d} elements in {result['duration']:>8s}")
        elif result['status'] == 'PARTIAL':
            print(f"⚠️  Chapter {ch:2d}: {result['reason']}")
        else:
            print(f"❌ Chapter {ch:2d}: {result['reason']}")

    print("\n" + "=" * 80)
    print(f"⏱️  Total time: {total_duration:.1f} minutes ({total_duration/60:.1f} hours)")
    print(f"✅ Successful: {len(successful)}/{len(CHAPTERS)} chapters - {successful}")

    if failed:
        print(f"❌ Failed: {len(failed)}/{len(CHAPTERS)} chapters - {failed}")
    else:
        print("🎉 All chapters processed successfully!")

    print("\n📁 Output locations:")
    print("  JSON files: shared_platform/utils/outputs/docling_layout/capitulo_{N:02d}/outputs/layout_WITH_PATCH.json")
    print("  Annotated PDFs: shared_platform/utils/outputs/docling_layout/capitulo_{N:02d}/outputs/capitulo_{N:02d}_annotated_WITH_PATCH.pdf")

    # Save summary report
    summary_path = BASE_PATH / "COMPLETE_REPROCESS_SUMMARY.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'batch_start': batch_start.isoformat(),
            'batch_end': batch_end.isoformat(),
            'total_duration_minutes': total_duration,
            'total_chapters': len(CHAPTERS),
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Summary saved: {summary_path}")
    print("=" * 80)


if __name__ == '__main__':
    main()
