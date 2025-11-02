#!/usr/bin/env python3
"""Quick test for isolated power line fix on Chapter 7"""
import sys
sys.path.insert(0, '/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/docling_layout')

from COMPLETE_REPROCESS_ALL_CHAPTERS import extract_chapter_with_patch
import json

print("=" * 80)
print("🧪 TESTING ISOLATED POWER LINE FIX - CHAPTER 7 ONLY")
print("=" * 80)

# Extract Chapter 7
result = extract_chapter_with_patch(
    chapter_num=7,
    chapter_info={'num': 7, 'pages': '266-347', 'estimated_mins': 9}
)

print("\n" + "=" * 80)
print("✅ EXTRACTION COMPLETE")
print("=" * 80)
print(f"Elements: {result['elements']}")
print(f"Duration: {result['duration']:.2f} minutes")

# Load and check page 40
with open('capitulo_07/outputs/layout_WITH_PATCH.json', 'r') as f:
    data = json.load(f)

page40 = [e for e in data['elements'] if e['page'] == 40]
page40_sorted = sorted(page40, key=lambda x: x['bbox']['y0'])

print("\n" + "=" * 80)
print("📄 PAGE 40 - VERIFICATION")
print("=" * 80)

for elem in page40_sorted:
    if 'Calama Nueva - Lasana' in elem['text'] or 'Diego de Almagro' in elem['text']:
        status = "✅ FIXED" if elem['type'] == 'section_header' else "❌ STILL list_item"
        print(f"\n{status}")
        print(f"  Type: {elem['type']}")
        print(f"  Text: {elem['text'][:70]}")
