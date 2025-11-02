#!/usr/bin/env python3
"""
Chapter 11 Extraction WITH EAF Patch (Company Name Detector v2.1)

Features:
- Flexible scoring system for entity name detection
- No hard cutoffs - allows long company names (>120 chars)
- Universal detection (not country-specific)
"""
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
import json
import sys

# Add eaf_patch to path
sys.path.insert(0, str(Path(__file__).parent / "eaf_patch"))
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# PDF path
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_11/EAF-089-2025_capitulo_11_pages_393-399.pdf")

print("=" * 80)
print("Chapter 11 Extraction WITH EAF Patch v2.1")
print("=" * 80)
print(f"\n📄 PDF: {pdf_path.name}")
print(f"📄 Pages: 393-399 (7 pages)")
print(f"\n🔧 Patch Features:")
print("   - Flexible scoring system (no hard cutoffs)")
print("   - Entity name detection (companies, orgs, facilities)")
print("   - Supports long names (>120 chars if strong signals)")
print("   - Universal (not country-specific)")

# STEP 1: Apply patch
print("\n" + "=" * 80)
print("STEP 1: Applying EAF Patch...")
print("=" * 80)
apply_universal_patch_with_pdf(str(pdf_path))
print("\n✅ Patch applied successfully!")

# STEP 2: Configure Docling
print("\n" + "=" * 80)
print("STEP 2: Configuring Docling...")
print("=" * 80)
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

# STEP 3: Process with Docling
print("\n" + "=" * 80)
print("STEP 3: Processing Chapter 11 with Docling...")
print("=" * 80)
print("⏱️  Estimated time: ~30 seconds (7 pages)...\n")

result = converter.convert(str(pdf_path))

# STEP 3.5: Post-process - Reclassify company names
print("\n" + "=" * 80)
print("STEP 3.5: Post-processing - Reclassifying company names...")
print("=" * 80)

from eaf_patch.core.eaf_company_name_detector import EAFCompanyNameDetector
from docling.datamodel.base_models import DocItemLabel

company_detector = EAFCompanyNameDetector()
company_reclassification_log = []

doc = result.document
for item, level in doc.iterate_items():
    # Check if it's a TEXT item (potential misclassification)
    if hasattr(item, 'label') and item.label == DocItemLabel.TEXT:
        text = item.text if hasattr(item, 'text') else ''

        if text and len(text.strip()) >= 5:
            # Run company name detection
            detection = company_detector.is_company_name_header(text.strip())

            if detection.get('is_company_header'):
                # RECLASSIFY: Change label from TEXT to SECTION_HEADER
                old_label = item.label
                item.label = DocItemLabel.SECTION_HEADER

                # Log the change
                company_reclassification_log.append({
                    'text': text.strip(),
                    'old_label': old_label.value,
                    'new_label': DocItemLabel.SECTION_HEADER.value,
                    'confidence': detection.get('confidence'),
                    'score': detection.get('confidence_score'),
                    'features': detection.get('features', {})
                })

if len(company_reclassification_log) > 0:
    print(f"✅ Reclassified {len(company_reclassification_log)} company name(s) (TEXT → SECTION_HEADER)")
    for item in company_reclassification_log:
        features = item.get('features', {})
        print(f"   ✏️  '{item['text'][:60]}' "
              f"(confidence: {item['confidence']}, "
              f"score: {item['score']:.2f}, "
              f"legal_suffix: {features.get('has_legal_suffix', False)})")
else:
    print("ℹ️  No company names found for reclassification")

# STEP 4: Export to JSON
print("\n" + "=" * 80)
print("STEP 4: Exporting to JSON...")
print("=" * 80)

output_dir = Path(__file__).parent / "capitulo_11" / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

output_json = output_dir / "layout_WITH_PATCH.json"

doc = result.document
elements = []

# Extract with coordinate conversion
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

json.dump({'elements': elements, 'total_elements': len(elements)}, open(output_json, 'w'), indent=2, ensure_ascii=False)

print(f"\n✅ Saved: {output_json}")
print(f"   Total elements: {len(elements)}")

# STEP 5: Create annotated PDF
print("\n" + "=" * 80)
print("STEP 5: Creating annotated PDF...")
print("=" * 80)

import fitz  # PyMuPDF

# Standard colors
COLORS = {
    'text': (0, 0, 1),  # Blue
    'section_header': (1, 0, 0),  # Red
    'section-header': (1, 0, 0),  # Red (alternative)
    'title': (1, 0.5, 0),  # Orange
    'list_item': (0, 0.7, 0.7),  # Cyan
    'list-item': (0, 0.7, 0.7),  # Cyan (alternative)
    'table': (0, 0.7, 0),  # Green
    'picture': (1, 0, 1),  # Magenta
    'caption': (0.8, 0.4, 0),  # Brown
    'formula': (1, 0.8, 0),  # Yellow
    'footnote': (0.8, 0.4, 0),  # Brown
    'page_header': (0.5, 0.5, 0.5),  # Gray
    'page-header': (0.5, 0.5, 0.5),  # Gray (alternative)
    'page_footer': (0.5, 0.5, 0.5),  # Gray
    'page-footer': (0.5, 0.5, 0.5),  # Gray (alternative)
}

doc_pdf = fitz.open(str(pdf_path))

for elem in elements:
    if elem['bbox']:
        page_num = elem['page']
        # CRITICAL: Docling uses 1-indexed pages, PyMuPDF uses 0-indexed
        # Must subtract 1 to get correct PyMuPDF page index
        pymupdf_page_idx = page_num - 1

        if 0 <= pymupdf_page_idx < len(doc_pdf):
            page = doc_pdf[pymupdf_page_idx]

            bbox = elem['bbox']
            rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

            # Get color based on type
            elem_type = elem['type'].replace('_', '-').lower()
            color = COLORS.get(elem_type, (0.5, 0.5, 0.5))  # Gray default

            # Draw rectangle
            page.draw_rect(rect, color=color, width=1.5)

output_pdf = output_dir / "capitulo_11_annotated_PATCHED.pdf"
doc_pdf.save(str(output_pdf))
doc_pdf.close()

print(f"\n✅ Saved: {output_pdf}")

# STEP 6: Summary
print("\n" + "=" * 80)
print("EXTRACTION COMPLETE!")
print("=" * 80)

# Count by type
type_counts = {}
section_headers = []
for elem in elements:
    elem_type = elem['type']
    type_counts[elem_type] = type_counts.get(elem_type, 0) + 1

    # Collect section headers (company names)
    if elem_type in ['section_header', 'section-header']:
        section_headers.append(elem['text'])

print(f"\n📊 Elements by type:")
for elem_type, count in sorted(type_counts.items()):
    print(f"   {elem_type:20s}: {count:4d}")

print(f"\n🏢 Section headers found ({len(section_headers)}):")
for i, header in enumerate(section_headers[:20], 1):
    print(f"   {i:2d}. {header[:70]}")
if len(section_headers) > 20:
    print(f"   ... and {len(section_headers) - 20} more")

print(f"\n📁 Outputs:")
print(f"   JSON: {output_json}")
print(f"   PDF:  {output_pdf}")

print("\n✅ Done!")
