#!/usr/bin/env python3
"""
UNIVERSAL CHAPTER EXTRACTOR - Works for ANY chapter
Only change: chapter number as argument

Usage:
    python3 EXTRACT_ANY_CHAPTER.py 6
    python3 EXTRACT_ANY_CHAPTER.py 7
    python3 EXTRACT_ANY_CHAPTER.py 1 --pages 1-11
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
from post_processors.core import apply_enumerated_item_fix_to_document, apply_hierarchy_restructure_to_document, apply_date_extraction_to_document
import json
import fitz

# Chapter definitions (page ranges)
CHAPTER_RANGES = {
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

def extract_chapter(chapter_num: int, custom_pages: str = None):
    """
    Extract a single chapter with EAF monkey patch

    Args:
        chapter_num: Chapter number (1-11)
        custom_pages: Optional custom page range like "1-50"
    """

    # Get page range
    if custom_pages:
        start, end = map(int, custom_pages.split('-'))
    else:
        if chapter_num not in CHAPTER_RANGES:
            print(f"❌ Chapter {chapter_num} not defined in CHAPTER_RANGES")
            sys.exit(1)
        start, end = CHAPTER_RANGES[chapter_num]

    # Paths
    base_pdf = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr")
    pdf_path = base_pdf / f"capitulo_{chapter_num:02d}" / f"EAF-089-2025_capitulo_{chapter_num:02d}_pages_{start}-{end}.pdf"
    output_dir = Path(f"capitulo_{chapter_num:02d}/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)

    print("=" * 80)
    print(f"📦 EXTRACTING CHAPTER {chapter_num}")
    print("=" * 80)
    print(f"📄 PDF: {pdf_path.name}")
    print(f"📄 Pages: {start}-{end} ({end - start + 1} pages)")
    print(f"📁 Output: {output_dir}")
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

    # Apply post-processors
    print("🔧 Applying post-processors...")
    enum_count = apply_enumerated_item_fix_to_document(doc)
    print(f"✅ Smart reclassification fixes (9 parts including Zona): {enum_count}")

    # Restructure by hierarchy
    hierarchy_count = apply_hierarchy_restructure_to_document(doc)
    print(f"✅ Hierarchical restructure: {hierarchy_count} numbered headers")

    # Extract dates and add to metadata
    date_metadata = apply_date_extraction_to_document(doc)
    print()

    # Export to JSON using native Docling format
    # This includes all monkey patch and post-processor modifications
    print("💾 Exporting to native Docling JSON format...")
    json_output = output_dir / "layout_WITH_PATCH.json"

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

    # Generate annotated PDF
    print("🎨 Generating annotated PDF...")
    pdf_output = output_dir / f"chapter{chapter_num:02d}_WITH_PATCH_annotated.pdf"

    pdf_doc = fitz.open(pdf_path)

    # Extract elements for PDF annotation (including furniture layer items like headers)
    all_items_to_annotate = []

    # Add body items
    for item in doc.iterate_items():
        all_items_to_annotate.append(item)

    # Add furniture items (page headers/footers) that aren't in body
    if hasattr(doc, 'texts') and doc.texts:
        for item in doc.texts:
            # Only add if it has prov and isn't already in body
            if hasattr(item, 'prov') and item.prov:
                all_items_to_annotate.append(item)

    # Track table bounding boxes to avoid drawing text inside tables
    table_boxes = []

    # First pass: collect all table bounding boxes
    for item in all_items_to_annotate:
        if isinstance(item, tuple):
            item, level = item

        if hasattr(item, 'label') and item.label.name.lower() == 'table':
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0]
                page = result.document.pages[prov.page_no]
                bbox = prov.bbox
                bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)
                table_boxes.append({
                    'page': prov.page_no,
                    'bbox': bbox_tl
                })

    # Second pass: draw annotations, skipping text inside tables
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
                'x0': bbox_tl.l,
                'y0': bbox_tl.t,
                'x1': bbox_tl.r,
                'y1': bbox_tl.b
            }
        }

        # Skip text items that are inside table bounding boxes
        if elem['type'] == 'text':
            is_inside_table = False
            for table in table_boxes:
                if table['page'] == elem['page']:
                    # Check if text bbox is inside table bbox
                    if (elem['bbox']['x0'] >= table['bbox'].l and
                        elem['bbox']['x1'] <= table['bbox'].r and
                        elem['bbox']['y0'] >= table['bbox'].t and
                        elem['bbox']['y1'] <= table['bbox'].b):
                        is_inside_table = True
                        break
            if is_inside_table:
                continue  # Skip drawing box for table cell text

        # Draw annotation on PDF
        page_num = elem['page'] - 1
        if page_num < 0 or page_num >= len(pdf_doc):
            continue

        page = pdf_doc[page_num]
        bbox = elem['bbox']
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
        color = COLORS.get(elem['type'], (0.5, 0.5, 0.5))
        page.draw_rect(rect, color=color, width=1.0)

    pdf_doc.save(pdf_output)
    pdf_doc.close()

    print(f"✅ Annotated PDF saved: {pdf_output}")
    print(f"   Size: {pdf_output.stat().st_size / (1024*1024):.1f} MB")
    print()

    # Summary
    print("=" * 80)
    print(f"✅ CHAPTER {chapter_num} EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print("📁 Output files:")
    print(f"   JSON: {json_output}")
    print(f"   PDF:  {pdf_output}")
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
    parser.add_argument('--pages', type=str, help='Custom page range (e.g., "1-50")', default=None)

    args = parser.parse_args()

    extract_chapter(args.chapter, args.pages)
