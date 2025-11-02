#!/usr/bin/env python3
"""
Extract and display bounding box information from docling output
Useful for analyzing box coordinates and element types
"""
import json
from pathlib import Path

# Paths
script_dir = Path(__file__).parent
cap1_dir = script_dir.parent
json_path = cap1_dir / "outputs" / "layout_lightweight.json"
csv_output = cap1_dir / "outputs" / "bounding_boxes.csv"

print("=" * 80)
print("📦 BOUNDING BOX EXTRACTOR")
print("=" * 80)
print(f"📊 Input: {json_path.name}")
print(f"📁 Output: {csv_output.name}")
print()

# Load layout data
print("📖 Loading layout data...")
with open(json_path, 'r') as f:
    data = json.load(f)

metadata = data['metadata']
elements = data['elements']

print(f"✅ Loaded {len(elements)} elements")
print()

# Print metadata
print("📋 METADATA:")
print("-" * 80)
print(f"   Chapter: {metadata['chapter']}")
print(f"   Pages: {metadata['pages']}")
print(f"   Extractor: {metadata['extractor']}")
print(f"   Total elements: {metadata['total_elements']}")
print(f"   Extraction date: {metadata['extraction_date']}")
print("-" * 80)
print()

# Group by type
type_counts = {}
for elem in elements:
    t = elem['type']
    type_counts[t] = type_counts.get(t, 0) + 1

print("📊 ELEMENT TYPES:")
print("-" * 80)
for elem_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<25} {count:>3} items")
print("-" * 80)
print()

# Show sample elements (first 5)
print("📄 SAMPLE ELEMENTS (first 5):")
print("-" * 80)
for i, elem in enumerate(elements[:5], 1):
    print(f"\n   [{i}] Type: {elem['type']}")
    print(f"       Page: {elem['page']}")
    print(f"       Text: {elem['text'][:80]}{'...' if len(elem['text']) > 80 else ''}")
    print(f"       Bbox (absolute): ({elem['bbox']['x0']:.2f}, {elem['bbox']['y0']:.2f}) → ({elem['bbox']['x1']:.2f}, {elem['bbox']['y1']:.2f})")
    print(f"       Bbox (normalized): ({elem['bbox_normalized']['x0']:.4f}, {elem['bbox_normalized']['y0']:.4f}) → ({elem['bbox_normalized']['x1']:.4f}, {elem['bbox_normalized']['y1']:.4f})")
    print(f"       Dimensions: {elem['page_dimensions']['width']} x {elem['page_dimensions']['height']} pts")
print("-" * 80)
print()

# Export to CSV
print("💾 Exporting to CSV...")
with open(csv_output, 'w') as f:
    # Header
    f.write("type,page,x0,y0,x1,y1,x0_norm,y0_norm,x1_norm,y1_norm,page_width,page_height,text\n")

    # Data
    for elem in elements:
        bbox = elem['bbox']
        bbox_norm = elem['bbox_normalized']
        dims = elem['page_dimensions']
        text = elem['text'].replace('"', '""').replace('\n', ' ')  # CSV escape

        f.write(f'"{elem["type"]}",{elem["page"]},{bbox["x0"]:.2f},{bbox["y0"]:.2f},{bbox["x1"]:.2f},{bbox["y1"]:.2f},'
                f'{bbox_norm["x0"]:.6f},{bbox_norm["y0"]:.6f},{bbox_norm["x1"]:.6f},{bbox_norm["y1"]:.6f},'
                f'{dims["width"]},{dims["height"]},"{text}"\n')

print(f"✅ Exported {len(elements)} elements to CSV")
print()

print("=" * 80)
print("✅ EXTRACTION COMPLETE")
print("=" * 80)
print()
print("📁 Files created:")
print(f"   • {csv_output}")
print()
print("💡 You can now:")
print("   • Open the CSV in Excel/LibreOffice for analysis")
print("   • Use the annotated PDF to visualize the boxes")
print("   • Import the CSV into Python/R for further processing")
print()
