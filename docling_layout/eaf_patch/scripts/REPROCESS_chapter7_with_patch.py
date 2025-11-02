#!/usr/bin/env python3
"""
Re-process Chapter 7 with Power Line Classification Patch
Uses the separate Chapter 7 PDF file
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# APPLY PATCH FIRST!
# ============================================================================
from patch_power_lines import apply_power_line_patch

print("\n" + "█" * 80)
print("🔧 APPLYING POWER LINE CLASSIFICATION PATCH")
print("█" * 80)

apply_power_line_patch()

# ============================================================================
# NOW IMPORT DOCLING
# ============================================================================
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# ============================================================================
# PATHS
# ============================================================================
pdf_path = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf")
output_dir = Path(__file__).parent / "capitulo_07" / "outputs_WITH_PATCH"
output_dir.mkdir(parents=True, exist_ok=True)

print("\n" + "█" * 80)
print("📖 CHAPTER 7 RE-PROCESSING WITH PATCH")
print("█" * 80)
print(f"PDF: {pdf_path.name}")
print(f"Pages: 266-347 (82 pages)")
print(f"Output: {output_dir}")
print()

# ============================================================================
# CONFIGURE PIPELINE
# ============================================================================
print("🔧 Configuring lightweight pipeline...")
pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=True,
    generate_page_images=False,
)

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# ============================================================================
# CONVERT
# ============================================================================
print("🔧 Creating DocumentConverter...")
converter = DocumentConverter(format_options=format_options)
print("✅ Converter ready\n")

print("🔍 Converting Chapter 7...")
print("   ⚠️  This will take ~5-10 minutes for 82 pages")
print("   🐵 Power line patch will execute during processing")
print()

result = converter.convert(str(pdf_path))

print("\n✅ Conversion complete\n")

# ============================================================================
# EXTRACT ELEMENTS
# ============================================================================
print("📊 Extracting elements...")

chapter_elements = []
for item in result.document.iterate_items():
    if isinstance(item, tuple):
        item, level = item

    if not hasattr(item, 'prov') or not item.prov:
        continue

    for prov in item.prov:
        if prov.page_no not in result.document.pages:
            continue

        page = result.document.pages[prov.page_no]
        bbox = prov.bbox
        bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)
        bbox_norm = bbox.normalized(page.size)

        if hasattr(item, 'text'):
            text_content = item.text if item.text else ""
        else:
            text_content = str(item) if item else ""

        element = {
            "type": item.label,
            "text": text_content,
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

print(f"✅ Extracted {len(chapter_elements)} elements\n")

# ============================================================================
# ANALYZE RESULTS
# ============================================================================
stats = {}
power_line_items = []

for elem in chapter_elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

    # Find power lines
    text = elem['text']
    if 'Línea' in text and 'kV' in text:
        power_line_items.append(elem)

print("📊 STATISTICS:")
print("-" * 60)
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    bar = "█" * min(count // 20, 50)
    print(f"   {elem_type:<20} │ {count:>4} │ {bar}")
print("-" * 60)
print(f"   {'TOTAL':<20} │ {sum(stats.values()):>4} │")
print()

# ============================================================================
# POWER LINE ANALYSIS
# ============================================================================
print("⚡ POWER LINE ANALYSIS:")
print("=" * 80)

power_line_types = {}
for pl in power_line_items:
    elem_type = pl['type']
    power_line_types[elem_type] = power_line_types.get(elem_type, 0) + 1

print(f"Total power line items: {len(power_line_items)}")
print(f"\nClassification breakdown:")
for elem_type, count in sorted(power_line_types.items(), key=lambda x: x[1], reverse=True):
    icon = "✅" if elem_type == "list_item" else "❌"
    percentage = (count / len(power_line_items) * 100) if power_line_items else 0
    print(f"   {icon} {elem_type:<15}: {count:>3} ({percentage:>5.1f}%)")

# Check page 305
page_305_power = [e for e in power_line_items if e['page'] == 305]
print(f"\n📍 Page 305 power lines: {len(page_305_power)}")
for pl in page_305_power[:5]:
    icon = "✅" if pl['type'] == "list_item" else "❌"
    print(f"   {icon} [{pl['type']}] {pl['text'][:70]}")

# ============================================================================
# SAVE JSON
# ============================================================================
json_path = output_dir / "layout_WITH_PATCH.json"

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump({
        "metadata": {
            "chapter": "Capítulo 7 - Análisis de Causas de Falla",
            "pdf_source": str(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "extractor": "Docling + Power Line Classification Patch",
            "total_elements": len(chapter_elements),
            "power_line_items": len(power_line_items),
            "patch_applied": True
        },
        "elements": chapter_elements
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ JSON saved: {json_path}")

# Save power lines only
power_lines_json = output_dir / "power_lines_ONLY.json"

with open(power_lines_json, 'w', encoding='utf-8') as f:
    json.dump({
        "total": len(power_line_items),
        "classification_breakdown": power_line_types,
        "power_lines": power_line_items
    }, f, indent=2, ensure_ascii=False)

print(f"⚡ Power lines saved: {power_lines_json}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ RE-PROCESSING COMPLETE")
print("=" * 80)
print(f"Total elements: {len(chapter_elements)}")
print(f"Power line items: {len(power_line_items)}")
print()

if power_line_items:
    list_item_count = power_line_types.get('list_item', 0)
    section_header_count = power_line_types.get('section_header', 0)

    consistency = (list_item_count / len(power_line_items) * 100) if power_line_items else 0

    print(f"Consistency: {consistency:.1f}% classified as list_item")

    if consistency == 100:
        print("🎉 PERFECT! All power lines consistently classified as list_item!")
    elif consistency > 90:
        print(f"✅ GOOD! {consistency:.1f}% consistency (some edge cases remain)")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: Only {consistency:.1f}% consistency")

print("=" * 80)
