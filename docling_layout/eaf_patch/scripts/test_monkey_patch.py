#!/usr/bin/env python3
"""
Minimal test to verify monkey patch works
Tests on Chapter 1, page 1 only (fastest test)
"""
import json
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# ========================================
# MONKEY PATCH - Apply BEFORE importing DocumentConverter
# ========================================
from docling.utils.layout_postprocessor import LayoutPostprocessor
from docling.datamodel.base_models import BoundingBox, Cluster
from docling.datamodel.document import DocItemLabel

# Import your custom detector
from shared_platform.utils.detailed_heading_detector import DetailedHeadingDetector

# Store original method
_original_process_regular_clusters = LayoutPostprocessor._process_regular_clusters

def _patched_process_regular_clusters(self, clusters, cells):
    """Patched version that runs custom detectors BEFORE Docling's logic"""

    print("\n" + "="*80)
    print("🔧 MONKEY PATCH ACTIVE - Running custom detectors")
    print("="*80)

    # Get page number and text cells
    page_num = self.page.page_no
    page_width = self.page.size.width
    page_height = self.page.size.height

    print(f"\n📄 Page {page_num} - Size: {page_width:.1f} x {page_height:.1f}")
    print(f"📊 Clusters from AI: {len(clusters)}")
    print(f"📊 Text cells: {len(cells)}")

    # Run DetailedHeadingDetector on this page's cells
    # Convert cells to format your detector expects
    page_blocks = []
    for cell in cells:
        bbox = cell.bbox
        page_blocks.append({
            'bbox': {
                'x0': bbox.l,
                'y0': bbox.t,
                'x1': bbox.r,
                'y1': bbox.b
            },
            'text': cell.text,
            'page': page_num
        })

    # Initialize detector (you may need to adjust this based on your implementation)
    detector = DetailedHeadingDetector()
    custom_titles = detector.detect_headings(page_blocks, page_num)

    print(f"\n🎯 Custom detector found {len(custom_titles)} titles:")
    for title in custom_titles[:5]:  # Show first 5
        print(f"   - Level {title.get('level', '?')}: {title['text'][:60]}...")

    # Now create custom clusters for these titles
    custom_clusters = []
    for title in custom_titles:
        bbox = title['bbox']

        # Create BoundingBox
        custom_bbox = BoundingBox(
            l=bbox['x0'],
            t=bbox['y0'],
            r=bbox['x1'],
            b=bbox['y1'],
            coord_origin=self.page.size.coord_origin
        )

        # Create Cluster with SECTION_HEADER label
        cluster = Cluster(
            id=len(clusters) + len(custom_clusters),
            label=DocItemLabel.SECTION_HEADER,
            bbox=custom_bbox,
            confidence=0.95,  # High confidence for custom detections
        )
        custom_clusters.append(cluster)

    # Merge AI clusters with custom clusters
    merged_clusters = list(clusters) + custom_clusters

    print(f"\n✅ Merged clusters: {len(clusters)} (AI) + {len(custom_clusters)} (custom) = {len(merged_clusters)} total")
    print("="*80 + "\n")

    # Call original method with merged clusters
    return _original_process_regular_clusters(self, merged_clusters, cells)

# Apply the monkey patch
print("\n🔧 Applying monkey patch to LayoutPostprocessor...")
LayoutPostprocessor._process_regular_clusters = _patched_process_regular_clusters
print("✅ Monkey patch applied successfully\n")

# ========================================
# TEST EXTRACTION
# ========================================

# Paths
pdf_path = project_root / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"
output_dir = Path(__file__).parent / "test_outputs"
output_dir.mkdir(exist_ok=True)

print("="*80)
print("📄 TESTING MONKEY PATCH ON CHAPTER 1, PAGE 1")
print("="*80)
print(f"📄 PDF: {pdf_path.name}")
print(f"📁 Output: {output_dir}")
print()

# Configure minimal pipeline (lightweight mode)
pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=False,  # Skip tables for speed
    generate_page_images=False,
)

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# Create converter
print("🔧 Creating DocumentConverter...")
converter = DocumentConverter(format_options=format_options)
print("✅ Converter ready")
print()

# Convert ONLY page 1
print("🔍 Converting page 1 (this will trigger the monkey patch)...")
print()

result = converter.convert(str(pdf_path), max_num_pages=1)

print()
print("✅ Conversion complete")
print()

# Extract elements
print("="*80)
print("📊 EXTRACTION RESULTS")
print("="*80)

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

# Count by type
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print(f"\n📊 Total elements extracted: {len(elements)}")
print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20} : {count:>3}")

# Show section headers (should include custom detected titles)
section_headers = [e for e in elements if e['type'] == 'section_header']
print(f"\n🎯 Section headers found: {len(section_headers)}")
for i, header in enumerate(section_headers[:10], 1):
    print(f"   {i}. {header['text'][:80]}")

# Save results
output_json = output_dir / "test_patch_results.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        "total_elements": len(elements),
        "stats": stats,
        "section_headers": section_headers,
        "all_elements": elements
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Results saved to: {output_json}")

print("\n" + "="*80)
print("🎉 TEST COMPLETE")
print("="*80)
print("\nIf you saw [MONKEY PATCH] messages above, the patch is working!")
print("Check the section_headers count - should be higher than without patch.")
print("="*80)
