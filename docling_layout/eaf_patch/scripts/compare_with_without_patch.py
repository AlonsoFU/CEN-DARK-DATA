#!/usr/bin/env python3
"""
Compare extraction WITH and WITHOUT monkey patch
Shows clear proof the patch works
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

def run_extraction(use_patch=False):
    """Run extraction with or without patch"""

    if use_patch:
        print("\n" + "="*80)
        print("🔧 MODE: WITH MONKEY PATCH")
        print("="*80)

        # Import and apply patch
        from docling.utils.layout_postprocessor import LayoutPostprocessor
        from docling.datamodel.base_models import BoundingBox, Cluster
        from docling.datamodel.document import DocItemLabel
        from shared_platform.utils.detailed_heading_detector import DetailedHeadingDetector

        _original = LayoutPostprocessor._process_regular_clusters

        def _patched(self, clusters, cells):
            # Convert cells to blocks
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
                    'page': self.page.page_no
                })

            # Run custom detector
            detector = DetailedHeadingDetector()
            custom_titles = detector.detect_headings(page_blocks, self.page.page_no)

            # Create custom clusters
            custom_clusters = []
            for title in custom_titles:
                bbox = title['bbox']
                custom_bbox = BoundingBox(
                    l=bbox['x0'],
                    t=bbox['y0'],
                    r=bbox['x1'],
                    b=bbox['y1'],
                    coord_origin=self.page.size.coord_origin
                )
                cluster = Cluster(
                    id=len(clusters) + len(custom_clusters),
                    label=DocItemLabel.SECTION_HEADER,
                    bbox=custom_bbox,
                    confidence=0.95,
                )
                custom_clusters.append(cluster)

            print(f"   🎯 Custom detector found {len(custom_clusters)} additional titles")

            # Merge and process
            merged = list(clusters) + custom_clusters
            return _original(self, merged, cells)

        # Apply patch
        LayoutPostprocessor._process_regular_clusters = _patched
        print("   ✅ Patch applied")
    else:
        print("\n" + "="*80)
        print("📄 MODE: WITHOUT MONKEY PATCH (vanilla Docling)")
        print("="*80)

    # Configure pipeline
    pipeline_options = PdfPipelineOptions(
        do_ocr=False,
        do_table_structure=False,
        generate_page_images=False,
    )

    format_options = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }

    # Paths
    pdf_path = project_root / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"

    # Convert
    print(f"\n🔍 Converting page 1 of {pdf_path.name}...\n")
    converter = DocumentConverter(format_options=format_options)
    result = converter.convert(str(pdf_path), max_num_pages=1)

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
            })

    # Stats
    stats = {}
    for elem in elements:
        elem_type = elem['type']
        stats[elem_type] = stats.get(elem_type, 0) + 1

    section_headers = [e for e in elements if e['type'] == 'section_header']

    print("="*80)
    print("📊 RESULTS")
    print("="*80)
    print(f"Total elements: {len(elements)}")
    print(f"\nElements by type:")
    for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {elem_type:<20} : {count:>3}")
    print(f"\n🎯 Section headers: {len(section_headers)}")
    for i, h in enumerate(section_headers[:5], 1):
        print(f"   {i}. {h['text'][:70]}")
    print("="*80)

    return {
        'total': len(elements),
        'stats': stats,
        'section_headers': section_headers
    }

# ========================================
# RUN COMPARISON
# ========================================

print("\n" + "█"*80)
print("📊 MONKEY PATCH COMPARISON TEST")
print("█"*80)

# Run without patch
results_without = run_extraction(use_patch=False)

print("\n\n")

# Run with patch (need fresh import)
results_with = run_extraction(use_patch=True)

# Compare
print("\n\n" + "█"*80)
print("🔬 COMPARISON RESULTS")
print("█"*80)

print(f"\n{'Metric':<30} | {'Without Patch':>15} | {'With Patch':>15} | {'Difference':>15}")
print("-"*80)

print(f"{'Total elements':<30} | {results_without['total']:>15} | {results_with['total']:>15} | {results_with['total'] - results_without['total']:>+15}")

print(f"{'Section headers':<30} | {len(results_without['section_headers']):>15} | {len(results_with['section_headers']):>15} | {len(results_with['section_headers']) - len(results_without['section_headers']):>+15}")

print("\n" + "█"*80)
if len(results_with['section_headers']) > len(results_without['section_headers']):
    print("✅ SUCCESS! Monkey patch detected MORE section headers")
    print(f"   Improvement: {len(results_with['section_headers']) - len(results_without['section_headers'])} additional headers")
else:
    print("⚠️  Monkey patch did not add section headers")
    print("   This might mean:")
    print("   1. DetailedHeadingDetector found no additional titles")
    print("   2. Patch didn't execute (check for patch messages above)")
print("█"*80)
