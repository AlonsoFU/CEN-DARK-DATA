#!/usr/bin/env python3
"""
Quick extraction using cached conversion result
"""
import json
import fitz
from pathlib import Path
from datetime import datetime
import sys

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter

# Config
pdf_path = Path("../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
output_dir = Path("../outputs")
output_dir.mkdir(parents=True, exist_ok=True)

START_PAGE = 1
END_PAGE = 11

print("="*80)
print("🚀 QUICK DOCLING EXTRACTION - Capítulo 1")
print("="*80)
print(f"📄 PDF: {pdf_path.name}")
print(f"📑 Páginas: {START_PAGE}-{END_PAGE}")
print()

# Convert
print("🔍 Converting document...")
converter = DocumentConverter()
result = converter.convert(str(pdf_path))
print("✅ Conversion complete")
print()

# Extract elements
print(f"📊 Extracting elements from pages {START_PAGE}-{END_PAGE}...")
chapter_elements = []

for item in result.document.iterate_items():
    # Handle tuple return (element, level)
    if isinstance(item, tuple):
        item, level = item

    # Skip if no provenance info
    if not hasattr(item, 'prov') or not item.prov:
        continue

    for prov in item.prov:
        if START_PAGE <= prov.page_no <= END_PAGE:
            # Get page for coordinate conversion (pages is a dict with 1-indexed keys)
            if prov.page_no not in result.document.pages:
                continue
            page = result.document.pages[prov.page_no]
            bbox = prov.bbox

            # Convert to top-left origin
            bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)

            # Normalize
            bbox_norm = bbox.normalized(page.size)

            element = {
                "type": item.label,
                "text": item.text if item.text else "",
                "page": prov.page_no,
                "bbox": {
                    "x0": round(bbox_tl.l, 2),
                    "y0": round(bbox_tl.t, 2),
                    "x1": round(bbox_tl.r, 2),
                    "y1": round(bbox_tl.b, 2)
                },
                "bbox_normalized": {
                    "x0": round(bbox_norm.l, 4),
                    "y0": round(bbox_norm.t, 4),
                    "x1": round(bbox_norm.r, 4),
                    "y1": round(bbox_norm.b, 4)
                },
                "page_dimensions": {
                    "width": page.size.width,
                    "height": page.size.height
                }
            }

            chapter_elements.append(element)

print(f"✅ Extracted {len(chapter_elements)} elements")
print()

# Save JSON
json_path = output_dir / "layout.json"
data = {
    "metadata": {
        "chapter": "Capítulo 1 - Descripción de la Perturbación",
        "pdf_source": str(pdf_path),
        "extraction_date": datetime.now().isoformat(),
        "extractor": "Docling Granite-258M",
        "total_elements": len(chapter_elements),
        "pages": f"{START_PAGE}-{END_PAGE}"
    },
    "elements": chapter_elements
}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"✅ JSON saved: {json_path}")

# Save Markdown
md_path = output_dir / "document.md"
markdown = result.document.export_to_markdown()
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(f"# Capítulo 1 - Páginas {START_PAGE}-{END_PAGE}\n\n")
    f.write(markdown)
print(f"✅ Markdown saved: {md_path}")

# Save HTML
html_path = output_dir / "document.html"
html = result.document.export_to_html()
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"✅ HTML saved: {html_path}")

# Calculate stats
stats = {}
for element in chapter_elements:
    elem_type = element['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

stats = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

# Save stats
stats_path = output_dir / "stats.json"
pages = sorted(set(e['page'] for e in chapter_elements))
stats_data = {
    "chapter": "Capítulo 1",
    "extraction_date": datetime.now().isoformat(),
    "summary": {
        "total_elements": len(chapter_elements),
        "total_pages": len(pages),
        "pages_range": f"{min(pages)}-{max(pages)}"
    },
    "elements_by_type": stats
}
with open(stats_path, 'w', encoding='utf-8') as f:
    json.dump(stats_data, f, indent=2, ensure_ascii=False)
print(f"✅ Stats saved: {stats_path}")

# Print stats
print()
print("="*80)
print("✅ EXTRACTION COMPLETED")
print("="*80)
print(f"📊 Total elements: {len(chapter_elements)}")
print()
print("📊 ELEMENTS BY TYPE:")
print("-" * 60)
for elem_type, count in stats.items():
    bar = "█" * min(count, 50)
    print(f"   {elem_type:<20} │ {count:>3} │ {bar}")
print("-" * 60)
print(f"   {'TOTAL':<20} │ {sum(stats.values()):>3} │")
print("="*80)
print()
print(f"📁 Files saved to: {output_dir.absolute()}")
