#!/usr/bin/env python3
"""
Chapter 7: Show what the PATCH gives TO Docling
Logs the intermediate state - the modified clusters before Docling processes them
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

# Paths
CHAPTER_PDF = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf")
OUTPUT_DIR = Path(__file__).parent / "capitulo_07" / "outputs"

print("=" * 80)
print("🔍 CHAPTER 7: Show PATCH INPUT to Docling")
print("=" * 80)
print("\nThis will show you what the patch GIVES TO Docling:")
print("  1. Modified clusters (e.g., '7.' → 'complete title')")
print("  2. New synthetic clusters (missing titles, power lines)")
print("  3. What Docling receives as input for processing")
print()

# ============================================================================
# Modify the patch to LOG what it returns to Docling
# ============================================================================

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# MONKEY PATCH THE MONKEY PATCH to intercept return value
from core import eaf_patch_engine
from docling.utils.layout_postprocessor import LayoutPostprocessor

original_patched_method = eaf_patch_engine._patched_process_regular_clusters

# Storage for what patch returns to Docling
patch_outputs = []

def _logging_patched_process_regular_clusters(self):
    """
    Wrapper around the patch that logs what it returns to Docling
    """
    # Call the actual patch
    final_clusters = original_patched_method(self)

    # Log what we're returning to Docling
    page_num = self.page.page_no

    page_info = {
        'page': page_num,
        'total_clusters': len(final_clusters),
        'clusters': []
    }

    for cluster in final_clusters:
        cluster_info = {
            'id': cluster.id,
            'label': str(cluster.label),
            'text': cluster.text if hasattr(cluster, 'text') and cluster.text else '',
            'bbox': {
                'x0': cluster.bbox.l,
                'y0': cluster.bbox.t,
                'x1': cluster.bbox.r,
                'y1': cluster.bbox.b
            } if cluster.bbox else None,
            'num_cells': len(cluster.cells) if hasattr(cluster, 'cells') and cluster.cells else 0
        }
        page_info['clusters'].append(cluster_info)

    patch_outputs.append(page_info)

    # Print summary for this page
    print(f"\n📄 Page {page_num}:")
    print(f"   Total clusters going to Docling: {len(final_clusters)}")

    # Show section headers and list items
    headers = [c for c in final_clusters if 'SECTION_HEADER' in str(c.label)]
    lists = [c for c in final_clusters if 'LIST_ITEM' in str(c.label)]

    if headers:
        print(f"   🔴 Section headers: {len(headers)}")
        for h in headers[:3]:
            text = h.text[:60] + "..." if len(h.text) > 60 else h.text if hasattr(h, 'text') else ''
            print(f"      - {text}")

    if lists:
        print(f"   🔵 List items: {len(lists)}")
        for l in lists[:3]:
            text = l.text[:60] + "..." if len(l.text) > 60 else l.text if hasattr(l, 'text') else ''
            print(f"      - {text}")

    return final_clusters

# Replace the patch with our logging version
eaf_patch_engine._patched_process_regular_clusters = _logging_patched_process_regular_clusters

# ============================================================================
# Apply Patch and Run Docling
# ============================================================================
print("🐵 Applying patch...\n")
apply_universal_patch_with_pdf(str(CHAPTER_PDF))

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

print("=" * 80)
print("🔄 Processing with patch (logging input to Docling)...")
print("=" * 80)

converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(CHAPTER_PDF))

print("\n" + "=" * 80)
print("✅ Processing Complete")
print("=" * 80)

# ============================================================================
# Save what the patch gave to Docling
# ============================================================================
output_json = OUTPUT_DIR / "patch_input_to_docling.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'description': 'What the EAF patch gives TO Docling (before final processing)',
            'chapter': 'Capítulo 7',
            'total_pages': len(patch_outputs),
            'extraction_date': datetime.now().isoformat()
        },
        'pages': patch_outputs
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved patch input: {output_json.name}")

# ============================================================================
# Summary Statistics
# ============================================================================
print("\n" + "=" * 80)
print("📊 SUMMARY: What Patch Gave to Docling")
print("=" * 80)

total_clusters = sum(p['total_clusters'] for p in patch_outputs)
print(f"\nTotal clusters sent to Docling: {total_clusters}")

# Count by type
type_counts = {}
for page in patch_outputs:
    for cluster in page['clusters']:
        label = cluster['label']
        type_counts[label] = type_counts.get(label, 0) + 1

print("\nClusters by type:")
for label, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {label:<30}: {count:>4}")

# Show examples of patch-created clusters
print("\n🔴 Examples of complete titles (patch merged):")
example_count = 0
for page in patch_outputs:
    for cluster in page['clusters']:
        if 'SECTION_HEADER' in cluster['label'] and len(cluster['text']) > 50:
            print(f"  Page {page['page']}: {cluster['text'][:80]}...")
            example_count += 1
            if example_count >= 5:
                break
    if example_count >= 5:
        break

print("\n📁 JSON Output:")
print(f"  {output_json}")

# ============================================================================
# Create PDF Visualization of Patch Input
# ============================================================================
print("\n🎨 Creating PDF visualization of patch input...")

import fitz

doc = fitz.open(CHAPTER_PDF)

COLORS = {
    'section_header': (1, 0, 0),      # Red - Section headers
    'list_item': (0, 0.7, 0.7),       # Cyan - List items
    'table': (0, 0.7, 0),              # Green - Tables
    'text': (0, 0, 1),                 # Blue - Text blocks
    'picture': (1, 0, 1),              # Magenta - Pictures
    'title': (1, 0.5, 0),              # Orange - Titles
    'caption': (0.8, 0.4, 0),          # Brown - Captions
    'page_header': (0.5, 0.5, 0.5),    # Gray - Page headers
    'page_footer': (0.5, 0.5, 0.5),    # Gray - Page footers
    'footnote': (0.8, 0.4, 0),         # Brown - Footnotes
    'formula': (1, 0.8, 0),            # Yellow - Formulas
}

boxes_drawn = 0
for page_data in patch_outputs:
    page_num = page_data['page']
    pdf_page_idx = page_num

    if pdf_page_idx < 0 or pdf_page_idx >= len(doc):
        continue

    page = doc[pdf_page_idx]

    for cluster in page_data['clusters']:
        if not cluster['bbox']:
            continue

        bbox = cluster['bbox']
        label = cluster['label'].split('.')[-1]  # Get label name without enum prefix
        color = COLORS.get(label, (0.5, 0.5, 0.5))

        # Draw rectangle
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
        page.draw_rect(rect, color=color, width=2)

        # Add label for section headers and list items
        if label in ['SECTION_HEADER', 'LIST_ITEM']:
            text_point = fitz.Point(bbox['x0'], bbox['y0'] - 2)
            page.insert_text(text_point, f"{label[:8]}", fontsize=6, color=color)

        boxes_drawn += 1

# Add legend
page = doc[0]
legend_x = 450
legend_y = 600
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 160, legend_y + 90)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
page.insert_text(fitz.Point(legend_x, legend_y), "Patch Input to Docling:", fontsize=9, color=(0, 0, 0))

y_offset = legend_y + 15
legend_items = [
    ('text', 'Blue - Text'),
    ('section_header', 'Red - Headers'),
    ('list_item', 'Cyan - Lists'),
    ('caption', 'Brown - Captions'),
    ('page_footer', 'Gray - Footers'),
]

for label, description in legend_items:
    color = COLORS.get(label, (0, 0, 0))
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)
    page.insert_text(fitz.Point(legend_x + 15, y_offset), description, fontsize=7, color=(0, 0, 0))
    y_offset += 10

output_pdf = OUTPUT_DIR / "patch_input_to_docling.pdf"
doc.save(output_pdf)
doc.close()

print(f"✅ Drew {boxes_drawn} cluster boxes")
print(f"✅ Saved PDF: {output_pdf.name}")

print("\n📁 Output files:")
print(f"  - {output_json.name} (JSON with all cluster data)")
print(f"  - {output_pdf.name} (PDF visualization)")
print("\nThis shows the EXACT clusters the patch gives to Docling,")
print("including modified clusters and new synthetic clusters.")
print("=" * 80)
