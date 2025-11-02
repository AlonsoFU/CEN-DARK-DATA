#!/usr/bin/env python3
"""
Test duplicate detection fix on Chapter 7
"""
import sys
sys.path.insert(0, '/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/docling_layout')

from COMPLETE_REPROCESS_ALL_CHAPTERS import extract_chapter_with_patch

print("=" * 80)
print("🧪 TESTING DUPLICATE DETECTION FIX - CHAPTER 7")
print("=" * 80)

# Extract Chapter 7
result = extract_chapter_with_patch(
    chapter_num=7,
    chapter_info={
        'num': 7,
        'pages': '266-347',
        'estimated_mins': 9
    }
)

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
print(f"Elements extracted: {result['elements']}")
print(f"Duration: {result['duration']:.2f} minutes")
print(f"\nJSON: {result['json']}")
print(f"PDF: {result['pdf']}")
