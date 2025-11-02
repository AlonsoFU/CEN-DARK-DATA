#!/usr/bin/env python3
"""Test Docling API to understand the structure"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.document_converter import DocumentConverter

pdf_path = "../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf"

print("Testing Docling API...")
print(f"PDF: {pdf_path}")
print()

# Convert just to understand structure
converter = DocumentConverter()
print("Converting (this will take ~20 min)...")
result = converter.convert(pdf_path)
print("✅ Conversion complete")
print()

# Explore structure
print("=" * 80)
print("DOCUMENT STRUCTURE:")
print("=" * 80)
print(f"Total pages in result.document.pages: {len(result.document.pages)}")
print(f"Type of pages: {type(result.document.pages)}")
print()

# Check if it's a dict or list
if isinstance(result.document.pages, dict):
    print("Pages is a DICT")
    print(f"Keys: {list(result.document.pages.keys())[:10]}")
elif isinstance(result.document.pages, list):
    print("Pages is a LIST")
    print(f"First page: {result.document.pages[0]}")
print()

# Check iterate_items
print("=" * 80)
print("ITERATE_ITEMS STRUCTURE:")
print("=" * 80)
count = 0
for item in result.document.iterate_items():
    count += 1
    if count <= 3:
        print(f"\nItem {count}:")
        print(f"  Type: {type(item)}")
        if isinstance(item, tuple):
            print(f"  Tuple length: {len(item)}")
            elem, level = item
            print(f"  Element type: {type(elem)}")
            print(f"  Element label: {elem.label if hasattr(elem, 'label') else 'N/A'}")
            print(f"  Has prov: {hasattr(elem, 'prov')}")
            if hasattr(elem, 'prov') and elem.prov:
                print(f"  Prov length: {len(elem.prov)}")
                print(f"  First prov page_no: {elem.prov[0].page_no}")
        else:
            print(f"  Not a tuple, has label: {hasattr(item, 'label')}")
            if hasattr(item, 'label'):
                print(f"  Label: {item.label}")
    if count == 3:
        break

print(f"\nTotal items checked: {count}")
