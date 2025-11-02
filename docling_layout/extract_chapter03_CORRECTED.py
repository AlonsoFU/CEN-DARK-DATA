#!/usr/bin/env python3
"""
Extract Chapter 3 with CORRECTED page boundaries (pages 91-152, not 91-153)

Includes EAF patch v2.1 + company name reclassification
"""
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from eaf_patch.core.eaf_patch_engine import apply_universal_patch_with_pdf
from eaf_patch.core.eaf_company_name_detector import EAFCompanyNameDetector
from docling.datamodel.base_models import DocItemLabel
import fitz
import json

print("=" * 80)
print("Chapter 3 Extraction WITH EAF Patch v2.1 (CORRECTED BOUNDARIES)")
print("=" * 80)

pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_03/EAF-089-2025_capitulo_03_pages_91-152.pdf")

print(f"\n📄 PDF: {pdf_path.name}")
print(f"📄 Pages: 91-152 (62 pages - CORRECTED)")
print("\n🔧 Patch Features:")
print("   - Missing title detection and insertion")
print("   - Power line list item detection")
print("   - Company name detection (flexible scoring)")
print("   - Company name reclassification (TEXT → SECTION_HEADER)")

# STEP 1: Apply EAF Patch
print("\n" + "=" * 80)
print("STEP 1: Applying EAF Patch...")
print("=" * 80)

apply_universal_patch_with_pdf(str(pdf_path))
print("✅ Patch applied successfully!")

# STEP 2: Configure Docling
print("\n" + "=" * 80)
print("STEP 2: Configuring Docling...")
print("=" * 80)

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# STEP 3: Process with Docling
print("\n" + "=" * 80)
print("STEP 3: Processing Chapter 3 with Docling...")
print("=" * 80)
print("⏱️  Estimated time: ~2 minutes (62 pages)...\n")

result = converter.convert(str(pdf_path))

# STEP 3.5: Post-process - Reclassify company names
print("\n" + "=" * 80)
print("STEP 3.5: Post-processing - Reclassifying company names...")
print("=" * 80)

company_detector = EAFCompanyNameDetector()
company_reclassification_log = []

doc = result.document
for item, level in doc.iterate_items():
    if hasattr(item, 'label') and item.label == DocItemLabel.TEXT:
        text = item.text if hasattr(item, 'text') else ''

        if text and len(text.strip()) >= 5:
            detection = company_detector.is_company_name_header(text.strip())

            if detection.get('is_company_header'):
                old_label = item.label
                item.label = DocItemLabel.SECTION_HEADER

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

output_dir = Path(__file__).parent / "capitulo_03" / "outputs"
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

# Save JSON
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({'elements': elements}, f, indent=2, ensure_ascii=False)

print(f"✅ Saved: {output_json}")
print(f"   Total elements: {len(elements)}")

# STEP 5: Create annotated PDF
print("\n" + "=" * 80)
print("STEP 5: Creating annotated PDF...")
print("=" * 80)

# Import standard color scheme (ensures consistency across all chapters)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from STANDARD_COLORS import DOCLING_COLORS as COLORS

doc_pdf = fitz.open(pdf_path)
output_pdf = output_dir / "capitulo_03_annotated.pdf"

for elem in elements:
    if elem['bbox']:
        page_num = elem['page']
        pymupdf_page_idx = page_num - 1

        if 0 <= pymupdf_page_idx < len(doc_pdf):
            page = doc_pdf[pymupdf_page_idx]

            bbox = elem['bbox']
            rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

            # Use consistent color scheme (same as Chapters 1 & 2)
            elem_type = elem['type']
            color = COLORS.get(elem_type, (0.5, 0.5, 0.5))

            page.draw_rect(rect, color=color, width=1.5)

doc_pdf.save(output_pdf)
doc_pdf.close()

print(f"✅ Saved: {output_pdf}")

# STEP 6: Summary
print("\n" + "=" * 80)
print("EXTRACTION COMPLETE!")
print("=" * 80)

type_counts = {}
for elem in elements:
    elem_type = elem['type']
    type_counts[elem_type] = type_counts.get(elem_type, 0) + 1

print(f"\n📊 Elements by type:")
for elem_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:20s}: {count:4d}")

print(f"\n📁 Outputs:")
print(f"   JSON: {output_json}")
print(f"   PDF:  {output_pdf}")
print("\n✅ Done!")
