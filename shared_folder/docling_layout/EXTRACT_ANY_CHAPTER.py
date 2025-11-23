#!/usr/bin/env python3
"""
UNIVERSAL CHAPTER EXTRACTOR - Works for ANY chapter and report

Usage:
    # Basic (uses defaults for EAF-089-2025)
    python3 EXTRACT_ANY_CHAPTER.py 1

    # With report ID
    python3 EXTRACT_ANY_CHAPTER.py 1 --report EAF-089-2025

    # Custom paths
    python3 EXTRACT_ANY_CHAPTER.py 1 --report EAF-090-2026 --input ./data/inputs --output ./data/outputs

    # Custom page range
    python3 EXTRACT_ANY_CHAPTER.py 1 --pages 1-50
"""
import sys
import argparse
from pathlib import Path

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf
from post_processors.core import apply_enumerated_item_fix_to_document, apply_table_reextract_to_document, apply_hierarchy_restructure_to_document, apply_date_extraction_to_document
import json
import fitz

# Default paths (relative to project root)
DEFAULT_INPUT_DIR = Path(__file__).parent.parent.parent / "data" / "inputs"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "outputs"

# Chapter definitions per report (page ranges)
REPORT_CHAPTERS = {
    "EAF-089-2025": {
        1: (1, 11),
        2: (12, 90),
        3: (91, 152),
        4: (153, 159),
        5: (160, 171),
        6: (172, 265),
        7: (266, 347),
        8: (348, 348),
        9: (349, 381),
        10: (382, 392),
        11: (393, 399),
    },
    "EAF-477-2025": {
        1: (1, 3),
        2: (4, 4),
        3: (5, 5),
        4: (6, 6),
        5: (7, 7),
        6: (7, 7),
        7: (8, 10),
        8: (11, 11),
        9: (12, 12),
        10: (12, 12),
        11: (13, 155),
        12: (156, 156),
        13: (156, 162),
    },
}

# Color scheme for annotated PDFs
COLORS = {
    'text': (0, 0, 1),           # Blue
    'section_header': (1, 0, 0), # Red
    'title': (1, 0, 0),          # Red
    'list_item': (0, 1, 1),      # Cyan
    'table': (0, 1, 0),          # Green
    'picture': (1, 0, 1),        # Magenta
    'caption': (1, 0.5, 0),      # Orange
    'formula': (0.5, 0, 0.5),    # Purple
}


def generate_annotated_pdf(doc, result, pdf_path, output_path, label):
    """Generate an annotated PDF with bounding boxes."""
    print(f"🎨 Generating {label} annotated PDF...")

    pdf_doc = fitz.open(pdf_path)

    # Collect all items to annotate
    all_items_to_annotate = []
    for item in doc.iterate_items():
        all_items_to_annotate.append(item)

    # Add furniture items
    if hasattr(doc, 'texts') and doc.texts:
        for item in doc.texts:
            if hasattr(item, 'prov') and item.prov:
                all_items_to_annotate.append(item)

    # Track table bounding boxes
    table_boxes = []
    for item in all_items_to_annotate:
        if isinstance(item, tuple):
            item, level = item
        if hasattr(item, 'label') and item.label.name.lower() == 'table':
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0]
                page = result.document.pages[prov.page_no]
                bbox = prov.bbox
                bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)
                table_boxes.append({'page': prov.page_no, 'bbox': bbox_tl})

    # Draw annotations
    for item in all_items_to_annotate:
        if isinstance(item, tuple):
            item, level = item

        if not hasattr(item, 'prov') or not item.prov:
            continue

        prov = item.prov[0]
        page = result.document.pages[prov.page_no]
        bbox = prov.bbox
        bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)

        elem = {
            'type': item.label.name.lower(),
            'page': prov.page_no,
            'bbox': {
                'x0': bbox_tl.l, 'y0': bbox_tl.t,
                'x1': bbox_tl.r, 'y1': bbox_tl.b
            }
        }

        # Skip text inside tables
        if elem['type'] == 'text':
            is_inside_table = False
            for table in table_boxes:
                if table['page'] == elem['page']:
                    if (elem['bbox']['x0'] >= table['bbox'].l and
                        elem['bbox']['x1'] <= table['bbox'].r and
                        elem['bbox']['y0'] >= table['bbox'].t and
                        elem['bbox']['y1'] <= table['bbox'].b):
                        is_inside_table = True
                        break
            if is_inside_table:
                continue

        # Draw on PDF
        page_num = elem['page'] - 1
        if page_num < 0 or page_num >= len(pdf_doc):
            continue

        page = pdf_doc[page_num]
        bbox = elem['bbox']
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
        color = COLORS.get(elem['type'], (0.5, 0.5, 0.5))
        page.draw_rect(rect, color=color, width=1.0)

    pdf_doc.save(output_path)
    pdf_doc.close()

    print(f"✅ {label} PDF saved: {output_path}")
    print(f"   Size: {output_path.stat().st_size / (1024*1024):.1f} MB")
    return output_path

def extract_chapter(chapter_num: int, report_id: str = "EAF-089-2025",
                    input_dir: Path = None, output_dir: Path = None,
                    custom_pages: str = None):
    """
    Extract a single chapter with EAF monkey patch

    Args:
        chapter_num: Chapter number (1-11)
        report_id: Report identifier (e.g., "EAF-089-2025")
        input_dir: Directory containing input PDFs
        output_dir: Directory for output files
        custom_pages: Optional custom page range like "1-50"
    """
    # Set defaults
    if input_dir is None:
        input_dir = DEFAULT_INPUT_DIR
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    # Get page range
    if custom_pages:
        start, end = map(int, custom_pages.split('-'))
    else:
        if report_id not in REPORT_CHAPTERS:
            print(f"❌ Report {report_id} not defined in REPORT_CHAPTERS")
            print(f"   Available: {list(REPORT_CHAPTERS.keys())}")
            sys.exit(1)
        if chapter_num not in REPORT_CHAPTERS[report_id]:
            print(f"❌ Chapter {chapter_num} not defined for {report_id}")
            sys.exit(1)
        start, end = REPORT_CHAPTERS[report_id][chapter_num]

    # Paths - look in capitulos/ subfolder
    pdf_path = input_dir / report_id / "capitulos" / f"capitulo_{chapter_num:02d}.pdf"

    # Alternative: try root folder with page range in filename
    if not pdf_path.exists():
        pdf_path = input_dir / report_id / f"{report_id}_capitulo_{chapter_num:02d}_pages_{start}-{end}.pdf"

    # Alternative: try root folder without page range
    if not pdf_path.exists():
        pdf_path = input_dir / report_id / f"capitulo_{chapter_num:02d}.pdf"

    # Output directory
    chapter_output_dir = output_dir / report_id / f"capitulo_{chapter_num:02d}"
    chapter_output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        print(f"   Expected in: {input_dir / report_id}")
        sys.exit(1)

    print("=" * 80)
    print(f"📦 EXTRACTING CHAPTER {chapter_num} - {report_id}")
    print("=" * 80)
    print(f"📄 PDF: {pdf_path.name}")
    print(f"📄 Pages: {start}-{end} ({end - start + 1} pages)")
    print(f"📁 Output: {chapter_output_dir}")
    print("=" * 80)
    print()

    # Configure pipeline (optimized for accuracy with 4GB GPU)
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.force_backend_text = True  # Use PDF text layer (faster, more accurate)

    print("⚙️  Configuration:")
    print(f"   - OCR: {pipeline_options.do_ocr}")
    print(f"   - Tables: {pipeline_options.table_structure_options.mode}")
    print(f"   - Text extraction: PDF text layer (force_backend_text=True)")
    print(f"   - VRAM: ~1.0 GB peak (safe for 4GB GPU)")
    print()

    # Apply monkey patch
    print("🐵 Applying EAF monkey patch...")
    apply_universal_patch_with_pdf(str(pdf_path))
    print("✅ Monkey patch applied")
    print()

    # Extract with Docling
    print("🚀 Starting Docling extraction...")
    print(f"   (~{(end - start + 1) * 6 / 60:.1f} minutes for {end - start + 1} pages)")
    print()

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(str(pdf_path))

    print()
    print("✅ Extraction completed")
    print()

    # Check for main title
    doc = result.document
    print("🔍 Checking for main chapter title...")
    title_found = False
    for item in doc.texts[:20]:
        if hasattr(item, 'text') and f'{chapter_num}.' in item.text[:5]:
            print(f"✅ TITLE DETECTED: '{item.text}'")
            print(f"   Label: {item.label.name}")
            title_found = True
            break

    if not title_found:
        print(f"⚠️  Main title '{chapter_num}. ...' not found in first 20 elements")
    print()

    # Generate DOCLING PDF (before post-processors)
    pdf_docling = chapter_output_dir / f"chapter{chapter_num:02d}_DOCLING.pdf"
    generate_annotated_pdf(doc, result, pdf_path, pdf_docling, "DOCLING")
    print()

    # Apply post-processors
    print("🔧 Applying post-processors...")
    enum_count = apply_enumerated_item_fix_to_document(doc)
    print(f"✅ Smart reclassification fixes (10 parts): {enum_count}")

    # Re-extract tables with specialized extractors
    table_count = apply_table_reextract_to_document(doc, str(pdf_path))
    print(f"✅ Table re-extraction: {table_count} tables processed")

    # Restructure by hierarchy
    hierarchy_count = apply_hierarchy_restructure_to_document(doc)
    print(f"✅ Hierarchical restructure: {hierarchy_count} numbered headers")

    # Extract dates and add to metadata
    date_metadata = apply_date_extraction_to_document(doc)
    print()

    # Export to JSON using native Docling format
    # This includes all monkey patch and post-processor modifications
    print("💾 Exporting to native Docling JSON format...")
    json_output = chapter_output_dir / "layout_WITH_PATCH.json"

    # Use Docling's native export_to_dict() to get complete document structure
    # This preserves hierarchy, metadata, tables, pictures, and all modifications
    doc_dict = doc.export_to_dict()

    # Add extracted dates to metadata
    if 'origin' not in doc_dict:
        doc_dict['origin'] = {}
    doc_dict['origin']['fecha_emision'] = date_metadata.get('fecha_emision')
    doc_dict['origin']['fecha_falla'] = date_metadata.get('fecha_falla')
    doc_dict['origin']['hora_falla'] = date_metadata.get('hora_falla')

    with open(json_output, 'w', encoding='utf-8') as f:
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

    print(f"✅ JSON saved: {json_output}")
    print(f"   Total elements: {element_count}")
    print()

    # Generate FINAL PDF (after post-processors)
    pdf_final = chapter_output_dir / f"chapter{chapter_num:02d}_FINAL.pdf"
    generate_annotated_pdf(doc, result, pdf_path, pdf_final, "FINAL")
    print()

    # Summary
    print("=" * 80)
    print(f"✅ CHAPTER {chapter_num} EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print("📁 Output files:")
    print(f"   JSON:   {json_output}")
    print(f"   DOCLING: {pdf_docling}")
    print(f"   FINAL:   {pdf_final}")
    print()
    print("📊 Statistics:")
    type_counts = {}
    for item in doc.iterate_items():
        if isinstance(item, tuple):
            item, level = item
        if hasattr(item, 'label'):
            t = item.label.name.lower()
            type_counts[t] = type_counts.get(t, 0) + 1

    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {t:20s}: {count:4d}")
    print()
    print("🎨 Color legend:")
    print("   🔴 Red    = section_header / title")
    print("   🔵 Blue   = text")
    print("   🔵🟢 Cyan   = list_item")
    print("   🟢 Green  = table")
    print("   🟣 Magenta = picture")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract any chapter with EAF monkey patch')
    parser.add_argument('chapter', type=int, help='Chapter number (1-11)')
    parser.add_argument('--report', type=str, default='EAF-089-2025',
                        help='Report ID (e.g., "EAF-089-2025")')
    parser.add_argument('--input', type=str, default=None,
                        help='Input directory (default: data/inputs)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory (default: data/outputs)')
    parser.add_argument('--pages', type=str, default=None,
                        help='Custom page range (e.g., "1-50")')

    args = parser.parse_args()

    input_dir = Path(args.input) if args.input else None
    output_dir = Path(args.output) if args.output else None

    extract_chapter(
        chapter_num=args.chapter,
        report_id=args.report,
        input_dir=input_dir,
        output_dir=output_dir,
        custom_pages=args.pages
    )
