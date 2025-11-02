#!/usr/bin/env python3
"""
Extract Chapter 6 - DIRECT FROM CLUSTERS (Bypass iterate_items)

Problem: iterate_items() only returns items with cells. Clusters created by patch
with empty cells=[] never appear!

Solution: Access clusters directly from DoclingPage objects instead of using
result.document.iterate_items()
"""
import json
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Apply patch BEFORE importing Docling
from universal_patch_with_pdf_extraction import apply_universal_patch_with_pdf

# PDF paths
PDF_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
OUTPUT_DIR = Path(__file__).parent.parent.parent / "capitulo_06" / "outputs_DIRECT_CLUSTERS"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("🔧 EXTRACTING FROM CLUSTERS DIRECTLY (BYPASS iterate_items)")
print("=" * 80)

# ============================================================================
# STEP 1: Apply Universal Patch
# ============================================================================
apply_universal_patch_with_pdf(str(PDF_PATH))

# ============================================================================
# STEP 2: Import Docling
# ============================================================================
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = True

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# ============================================================================
# STEP 3: Process PDF
# ============================================================================
print("\n🔍 Processing with Docling + Universal Patch...")
converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(PDF_PATH))

print("✅ Docling processing complete")

# ============================================================================
# STEP 4: Access Clusters Directly (BYPASS iterate_items!)
# ============================================================================
print("\n📊 Extracting elements DIRECTLY from clusters...")

elements = []

# Access pages from result
for page_obj in result.pages:
    page_no = page_obj.page_no + 1  # Convert to 1-indexed

    print(f"\n🔍 Page {page_no}:")

    # Access layout postprocessor clusters directly
    if hasattr(page_obj, '_layout_postprocessor'):
        postproc = page_obj._layout_postprocessor

        if hasattr(postproc, 'regular_clusters'):
            clusters = postproc.regular_clusters
            print(f"   Found {len(clusters)} clusters")

            for cluster in clusters:
                # Extract text from cluster
                text_parts = []

                # If cluster has cells, extract text from them
                if cluster.cells:
                    for cell in cluster.cells:
                        if hasattr(cell, 'text') and cell.text:
                            text_parts.append(cell.text)

                # Combine text
                text = ' '.join(text_parts).strip()

                # If no text from cells, try to extract from bbox using PyMuPDF
                if not text and cluster.bbox:
                    # Extract text at this bbox location
                    import fitz
                    doc = fitz.open(PDF_PATH)
                    page = doc[page_no - 1]

                    # Get text in bbox area
                    rect = fitz.Rect(
                        cluster.bbox.l,
                        cluster.bbox.t,
                        cluster.bbox.r,
                        cluster.bbox.b
                    )
                    text = page.get_textbox(rect).strip()
                    doc.close()

                # Create element
                element = {
                    'type': cluster.label.value if hasattr(cluster.label, 'value') else str(cluster.label),
                    'text': text,
                    'page': page_no,
                    'full_pdf_page': page_no + 171,  # Chapter 6 starts at page 172
                    'bbox': {
                        'x0': cluster.bbox.l,
                        'y0': cluster.bbox.t,
                        'x1': cluster.bbox.r,
                        'y1': cluster.bbox.b
                    } if cluster.bbox else None,
                    'confidence': cluster.confidence,
                    'num_cells': len(cluster.cells) if cluster.cells else 0,
                    'source': 'cells' if cluster.cells else 'bbox_extraction'
                }

                elements.append(element)

                # Show if it's a missing element (no cells)
                if not cluster.cells:
                    print(f"   ⭐ PATCH-ADDED: {element['type']} - '{text[:50]}...'")

print(f"\n✅ Extracted {len(elements)} elements DIRECTLY from clusters")

# Count by source
cells_count = sum(1 for e in elements if e['source'] == 'cells')
bbox_count = sum(1 for e in elements if e['source'] == 'bbox_extraction')
print(f"   - From cells: {cells_count}")
print(f"   - From bbox extraction (PATCH): {bbox_count}")

# ============================================================================
# STEP 5: Save JSON
# ============================================================================
json_output = OUTPUT_DIR / "chapter6_DIRECT_CLUSTERS.json"

output_data = {
    'metadata': {
        'extraction_method': 'Direct cluster access (bypass iterate_items)',
        'total_elements': len(elements),
        'elements_with_cells': cells_count,
        'elements_bbox_only': bbox_count,
    },
    'elements': elements
}

with open(json_output, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ JSON saved: {json_output}")

# ============================================================================
# STEP 6: Search for Title "6."
# ============================================================================
print("\n🔍 Searching for title '6.'...")

title_6_found = False
for elem in elements:
    if elem['text'].strip() == '6.':
        title_6_found = True
        print(f"✅ FOUND: Title '6.' on page {elem['page']}")
        print(f"   Type: {elem['type']}")
        print(f"   Source: {elem['source']}")
        print(f"   BBox: {elem['bbox']}")
        print(f"   Cells: {elem['num_cells']}")

if not title_6_found:
    print("❌ Title '6.' NOT found in extracted elements")

print("\n" + "=" * 80)
print("✅ EXTRACTION COMPLETE")
print("=" * 80)
