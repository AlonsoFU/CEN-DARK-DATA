#!/usr/bin/env python3
"""
REAL test that actually modifies layout extraction results
This version ensures cells get assigned to custom clusters
"""
import json
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ========================================
# MONKEY PATCH - MUST APPLY BEFORE IMPORT
# ========================================
print("\n🔧 Applying monkey patch...")

from docling.utils.layout_postprocessor import LayoutPostprocessor
from docling.datamodel.base_models import BoundingBox, Cluster
from docling.datamodel.document import DocItemLabel
from docling_core.types.doc.page import TextCell

# Import custom detector
from shared_platform.utils.detailed_heading_detector import DetailedHeadingDetector

# Store original
_original_process_regular = LayoutPostprocessor._process_regular_clusters

def _patched_process_regular_clusters(self) -> list:
    """
    Patched version that:
    1. Runs custom detector
    2. Creates clusters with SECTION_HEADER label
    3. Assigns cells to those clusters
    4. Merges with AI clusters
    """

    print("\n" + "="*80)
    print("🔧 [PATCH] Running custom title detector")
    print("="*80)

    # Get page info
    page_num = self.page.page_no

    # Convert cells to format DetailedHeadingDetector expects
    page_blocks = []
    for cell in self.cells:
        bbox_obj = cell.rect.to_bounding_box()
        page_blocks.append({
            'bbox': {
                'x0': bbox_obj.l,
                'y0': bbox_obj.t,
                'x1': bbox_obj.r,
                'y1': bbox_obj.b
            },
            'text': cell.text,
            'page': page_num
        })

    # Run custom detector
    detector = DetailedHeadingDetector()
    custom_titles = detector.detect_headings(page_blocks, page_num)

    print(f"📊 [PATCH] Found {len(custom_titles)} custom titles")

    # Create custom clusters with cells assigned
    custom_clusters = []
    next_id = max((c.id for c in self.regular_clusters), default=0) + 1

    for i, title in enumerate(custom_titles):
        bbox_dict = title['bbox']

        # Create BoundingBox
        custom_bbox = BoundingBox(
            l=bbox_dict['x0'],
            t=bbox_dict['y0'],
            r=bbox_dict['x1'],
            b=bbox_dict['y1'],
            coord_origin=self.page.size.coord_origin
        )

        # Find cells that overlap with this bbox
        assigned_cells = []
        for cell in self.cells:
            if not cell.text.strip():
                continue

            cell_bbox = cell.rect.to_bounding_box()
            overlap = cell_bbox.intersection_over_self(custom_bbox)

            # If cell overlaps >50% with our custom bbox, assign it
            if overlap > 0.5:
                assigned_cells.append(cell)

        if assigned_cells:  # Only create cluster if it has cells
            cluster = Cluster(
                id=next_id + i,
                label=DocItemLabel.SECTION_HEADER,  # ← This is the key change!
                bbox=custom_bbox,
                confidence=0.95,
                cells=assigned_cells  # ← Cells pre-assigned!
            )
            custom_clusters.append(cluster)

    print(f"✅ [PATCH] Created {len(custom_clusters)} SECTION_HEADER clusters with cells")

    # Merge custom clusters into regular_clusters BEFORE processing
    self.regular_clusters.extend(custom_clusters)

    print(f"📊 [PATCH] Total clusters: {len(self.regular_clusters)}")
    print("="*80 + "\n")

    # Now call original method with merged clusters
    return _original_process_regular(self)

# Apply patch
LayoutPostprocessor._process_regular_clusters = _patched_process_regular_clusters
print("✅ Monkey patch applied\n")

# ========================================
# NOW IMPORT AND RUN DOCLING
# ========================================

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Paths
pdf_path = project_root / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"
output_dir = Path(__file__).parent / "test_outputs"
output_dir.mkdir(exist_ok=True)

print("="*80)
print("📄 REAL MONKEY PATCH TEST - MODIFYING LAYOUT RESULTS")
print("="*80)
print(f"PDF: {pdf_path.name}")
print(f"Testing on: Page 1 only")
print()

# Configure pipeline (lightweight mode)
pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=False,
    generate_page_images=False,
)

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# Create converter
print("🔧 Creating DocumentConverter...")
converter = DocumentConverter(format_options=format_options)
print("✅ Ready\n")

# Convert
print("🔍 Converting page 1 (patch will execute during processing)...\n")
result = converter.convert(str(pdf_path), max_num_pages=1)
print("\n✅ Conversion complete\n")

# Extract elements
elements = []
for item in result.document.iterate_items():
    if isinstance(item, tuple):
        item, level = item

    if not hasattr(item, 'prov') or not item.prov:
        continue

    for prov in item.prov:
        elements.append({
            "type": item.label,
            "text": item.text if hasattr(item, 'text') else str(item),
            "page": prov.page_no,
        })

# Stats
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

section_headers = [e for e in elements if e['type'] == 'section_header']

print("="*80)
print("📊 EXTRACTION RESULTS")
print("="*80)
print(f"Total elements: {len(elements)}\n")

print("Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20} : {count:>3}")

print(f"\n🎯 SECTION HEADERS EXTRACTED: {len(section_headers)}")
print("\nSection headers found:")
for i, header in enumerate(section_headers, 1):
    text = header['text'][:70]
    print(f"   {i:2}. {text}")

# Save results
output_json = output_dir / "real_patch_results.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        "test_type": "monkey_patch_with_cell_assignment",
        "total_elements": len(elements),
        "stats": stats,
        "section_headers": section_headers,
        "all_elements": elements
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Results saved: {output_json}")

print("\n" + "="*80)
print("🎉 TEST COMPLETE")
print("="*80)
print("\n✅ If you see custom-detected titles in the section_headers above,")
print("   the monkey patch is WORKING and modifying layout results!")
print("\n📊 Expected behavior:")
print("   - Without patch: ~5-10 section headers (AI only)")
print("   - With patch: ~15-20 section headers (AI + custom detector)")
print("="*80)
