#!/usr/bin/env python3
"""
Batch Process Chapters 2-11 with EAF Monkey Patch

Processes all remaining EAF chapters sequentially using the standardized workflow.

Note: Sequential processing is safer for 4GB GPU (avoids OOM errors)
Expected total time: ~60-90 minutes for all chapters
"""
import sys
from pathlib import Path
from datetime import datetime

# Chapter configuration (adjust page ranges as needed)
CHAPTERS = {
    2: {"pages": "XX-YY", "estimated_mins": 3},
    3: {"pages": "XX-YY", "estimated_mins": 4},
    4: {"pages": "XX-YY", "estimated_mins": 5},
    5: {"pages": "XX-YY", "estimated_mins": 4},
    6: {"pages": "XX-YY", "estimated_mins": 6},
    # Chapter 7 already done
    8: {"pages": "XX-YY", "estimated_mins": 5},
    9: {"pages": "XX-YY", "estimated_mins": 4},
    10: {"pages": "XX-YY", "estimated_mins": 5},
    11: {"pages": "XX-YY", "estimated_mins": 6},
}

def process_chapter(chapter_num):
    """Process a single chapter with EAF patch"""
    print("\n" + "=" * 80)
    print(f"📦 PROCESSING CHAPTER {chapter_num}")
    print("=" * 80)

    chapter_info = CHAPTERS[chapter_num]

    # Import here to avoid loading all modules at once
    eaf_patch_path = Path(__file__).parent / "eaf_patch"
    sys.path.insert(0, str(eaf_patch_path))

    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from core.eaf_patch_engine import apply_universal_patch_with_pdf, apply_zona_fix_to_document

    # PDF path (adjust base path as needed)
    pdf_path = Path(f"/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_{chapter_num:02d}/EAF-089-2025_capitulo_{chapter_num:02d}_pages_{chapter_info['pages']}.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return False

    print(f"📄 PDF: {pdf_path}")
    print(f"⏱️  Estimated time: ~{chapter_info['estimated_mins']} minutes")

    # Apply patch
    apply_universal_patch_with_pdf(pdf_path)

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

    # Process with patch
    start_time = datetime.now()
    print(f"🔄 Starting extraction at {start_time.strftime('%H:%M:%S')}...")

    result = converter.convert(str(pdf_path))

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    print(f"✅ Extraction complete in {duration:.1f} minutes")

    # Apply Zona fix
    doc = result.document
    reclassified_count = apply_zona_fix_to_document(doc)

    # Export to JSON
    output_dir = Path(__file__).parent / f"capitulo_{chapter_num:02d}" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "layout_WITH_PATCH.json"

    import json

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

    json.dump({'elements': elements, 'total_elements': len(elements)},
              open(output_json, 'w'), indent=2, ensure_ascii=False)

    print(f"✅ Saved: {output_json}")
    print(f"📊 Total elements: {len(elements)}")

    # Stats
    stats = {}
    for elem in elements:
        elem_type = elem['type']
        stats[elem_type] = stats.get(elem_type, 0) + 1

    print("\n📊 Elements by type:")
    for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {elem_type:<20}: {count:>4}")

    return True

def main():
    """Batch process all chapters"""
    print("=" * 80)
    print("🔄 BATCH PROCESSING CHAPTERS 2-11 WITH EAF PATCH")
    print("=" * 80)
    print(f"\nTotal chapters: {len(CHAPTERS)}")

    total_estimated_time = sum(ch['estimated_mins'] for ch in CHAPTERS.values())
    print(f"Estimated total time: ~{total_estimated_time} minutes ({total_estimated_time/60:.1f} hours)")
    print("\n⚠️  Processing sequentially (safer for 4GB GPU)")
    print("⚠️  Do NOT run other GPU processes during batch!")
    print()

    input("Press Enter to start batch processing...")

    batch_start = datetime.now()
    successful = []
    failed = []

    for chapter_num in sorted(CHAPTERS.keys()):
        try:
            success = process_chapter(chapter_num)
            if success:
                successful.append(chapter_num)
            else:
                failed.append(chapter_num)
        except Exception as e:
            print(f"\n❌ ERROR processing chapter {chapter_num}:")
            print(f"   {e}")
            failed.append(chapter_num)
            import traceback
            traceback.print_exc()

    batch_end = datetime.now()
    total_duration = (batch_end - batch_start).total_seconds() / 60

    print("\n" + "=" * 80)
    print("📊 BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"\n⏱️  Total time: {total_duration:.1f} minutes ({total_duration/60:.1f} hours)")
    print(f"✅ Successful: {len(successful)} chapters - {successful}")
    if failed:
        print(f"❌ Failed: {len(failed)} chapters - {failed}")
    else:
        print("🎉 All chapters processed successfully!")

    print("\n📁 Output location:")
    print("   shared_platform/utils/outputs/docling_layout/capitulo_{N:02d}/outputs/layout_WITH_PATCH.json")

    print("\n🎨 Next step: Create visualizations")
    print("   for i in 2 3 4 5 6 8 9 10 11; do")
    print("       python3 visualize_chapter${i}_WITH_PATCH.py")
    print("   done")
    print("=" * 80)

if __name__ == '__main__':
    main()
