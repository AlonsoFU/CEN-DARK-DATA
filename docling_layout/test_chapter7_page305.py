#!/usr/bin/env python3
"""
Test Power Line Classification Patch on Chapter 7, Page 305

Real-world test case:
    Chapter 7 (Análisis de Causas de Falla)
    Page 305 (PDF page 305, actual page 266-347 range)

Contains lines like:
    • Línea 220 kV Cerro Dominador - Sierra Gorda
    • Línea 110 kV Diego de Almagro - Central Andes Generación

Which Docling sometimes misclassifies as section_header instead of list_item
"""
import json
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# APPLY PATCH BEFORE IMPORTING DOCLING
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
# CONFIGURATION
# ============================================================================

# Paths
pdf_path = project_root / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"
output_dir = Path(__file__).parent / "test_outputs"
output_dir.mkdir(exist_ok=True)

# Chapter 7 is pages 266-347 in the document
# We want to test page 305 specifically
# That's page index 304 (0-indexed)
TARGET_PAGE = 305

print("\n" + "█" * 80)
print(f"📄 TESTING ON CHAPTER 7, PAGE {TARGET_PAGE}")
print("█" * 80)
print(f"PDF: {pdf_path.name}")
print(f"Target page: {TARGET_PAGE}")
print()

# ============================================================================
# CONFIGURE PIPELINE (LIGHTWEIGHT MODE)
# ============================================================================
pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=False,  # Skip for speed
    generate_page_images=False,
)

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# ============================================================================
# RUN EXTRACTION
# ============================================================================
print("🔧 Creating DocumentConverter...")
converter = DocumentConverter(format_options=format_options)
print("✅ Converter ready\n")

print(f"🔍 Processing page {TARGET_PAGE} (patch will execute during processing)...\n")

# Convert single page
# Note: Docling uses 1-indexed pages internally, but we need to pass the right range
result = converter.convert(
    str(pdf_path),
    pages=[TARGET_PAGE - 1]  # 0-indexed for input
)

print("\n✅ Conversion complete\n")

# ============================================================================
# EXTRACT AND ANALYZE RESULTS
# ============================================================================
print("=" * 80)
print("📊 EXTRACTION RESULTS - PAGE 305")
print("=" * 80)
print()

# Extract elements
elements = []
for item in result.document.iterate_items():
    if isinstance(item, tuple):
        item, level = item

    if not hasattr(item, 'prov') or not item.prov:
        continue

    for prov in item.prov:
        if prov.page_no == TARGET_PAGE:
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

print(f"Total elements on page {TARGET_PAGE}: {len(elements)}\n")

print("Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<20} : {count:>3}")

# ============================================================================
# ANALYZE POWER LINE ITEMS
# ============================================================================
print("\n" + "=" * 80)
print("⚡ POWER LINE ANALYSIS")
print("=" * 80)
print()

# Filter list items that match power line pattern
power_line_items = [
    e for e in elements
    if e['type'] == 'list_item' and
    ('Línea' in e['text'] or 'kV' in e['text'])
]

print(f"🔍 Found {len(power_line_items)} power line list items:")
for i, item in enumerate(power_line_items[:20], 1):  # Show first 20
    text = item['text'][:80]
    print(f"   {i:2}. {text}")
print()

# Check for misclassified items (should be ZERO with patch!)
misclassified = [
    e for e in elements
    if e['type'] == 'section_header' and
    ('Línea' in e['text'] or 'kV' in e['text']) and
    e['text'].strip().startswith('•')
]

if misclassified:
    print("❌ MISCLASSIFIED POWER LINES (classified as section_header):")
    for item in misclassified:
        print(f"   • {item['text'][:80]}")
    print()
    print(f"⚠️  Patch failed! {len(misclassified)} power lines still misclassified")
else:
    print("✅ SUCCESS! No power lines misclassified as section_header")
    print("   All power lines correctly classified as list_item")

print()

# ============================================================================
# SAVE RESULTS
# ============================================================================
output_json = output_dir / f"chapter7_page{TARGET_PAGE}_results.json"

with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        "page": TARGET_PAGE,
        "total_elements": len(elements),
        "stats": stats,
        "power_line_items": power_line_items,
        "misclassified_items": misclassified,
        "all_elements": elements
    }, f, indent=2, ensure_ascii=False)

print(f"💾 Results saved: {output_json}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "█" * 80)
print("📊 TEST SUMMARY")
print("█" * 80)
print()
print(f"Page tested: {TARGET_PAGE}")
print(f"Total elements: {len(elements)}")
print(f"List items: {stats.get('list_item', 0)}")
print(f"Section headers: {stats.get('section_header', 0)}")
print(f"Power line items found: {len(power_line_items)}")
print(f"Misclassified power lines: {len(misclassified)}")
print()

if len(misclassified) == 0 and len(power_line_items) > 0:
    print("✅ ✅ ✅ PATCH WORKING PERFECTLY! ✅ ✅ ✅")
    print()
    print("All power transmission lines correctly classified as list_item!")
    print("No more inconsistent section_header classification!")
elif len(power_line_items) == 0:
    print("⚠️  No power lines found on this page")
    print("   Try a different page with power line listings")
else:
    print(f"❌ PATCH NOT FULLY WORKING")
    print(f"   {len(misclassified)} power lines still misclassified")
    print("   Review the patch logic")

print()
print("█" * 80)
