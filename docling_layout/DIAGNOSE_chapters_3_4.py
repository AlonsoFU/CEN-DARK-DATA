#!/usr/bin/env python3
"""
Diagnostic script to check Chapter 3 and 4 page alignment
"""
import json
import fitz
from pathlib import Path

print("=" * 80)
print("🔍 DIAGNOSTIC: Chapters 3 & 4 Page Alignment")
print("=" * 80)

# Paths
base_path = Path(__file__).parent
json3 = base_path / "capitulo_03/outputs/layout_WITH_PATCH.json"
json4 = base_path / "capitulo_04/outputs/layout_WITH_PATCH.json"
pdf3 = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_03/EAF-089-2025_capitulo_03_pages_91-153.pdf")
pdf4 = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_04/EAF-089-2025_capitulo_04_pages_154-159.pdf")

# Load JSONs
with open(json3) as f:
    data3 = json.load(f)

with open(json4) as f:
    data4 = json.load(f)

# Open PDFs
doc3 = fitz.open(pdf3)
doc4 = fitz.open(pdf4)

print(f"\n📄 Chapter 3:")
print(f"   PDF: {len(doc3)} pages (original pages 91-153)")
print(f"   JSON: {len(data3['elements'])} elements")
print(f"   Page range in JSON: {min(e['page'] for e in data3['elements'])} to {max(e['page'] for e in data3['elements'])}")

print(f"\n📄 Chapter 4:")
print(f"   PDF: {len(doc4)} pages (original pages 154-159)")
print(f"   JSON: {len(data4['elements'])} elements")
print(f"   Page range in JSON: {min(e['page'] for e in data4['elements'])} to {max(e['page'] for e in data4['elements'])}")

# Check Chapter 3 last page (JSON page 63)
print(f"\n" + "=" * 80)
print(f"📄 CHAPTER 3 - LAST PAGE (JSON page 63 = PDF index 62 = Original page 153)")
print("=" * 80)

page_63_elements = [e for e in data3['elements'] if e['page'] == 63]
print(f"Elements in JSON for page 63: {len(page_63_elements)}")

# Get text from actual PDF page
pdf_page_text = doc3[62].get_text()[:300]
print(f"\nActual PDF text on this page:")
print(pdf_page_text)

print(f"\nJSON elements on this page:")
for elem in page_63_elements[:5]:
    print(f"   {elem['type']:15s}: '{elem['text'][:60]}'")

# Check Chapter 4 first page (JSON page 1)
print(f"\n" + "=" * 80)
print(f"📄 CHAPTER 4 - FIRST PAGE (JSON page 1 = PDF index 0 = Original page 154)")
print("=" * 80)

page_1_elements = [e for e in data4['elements'] if e['page'] == 1]
print(f"Elements in JSON for page 1: {len(page_1_elements)}")

# Get text from actual PDF page
pdf_page_text = doc4[0].get_text()[:300]
print(f"\nActual PDF text on this page:")
print(pdf_page_text)

print(f"\nJSON elements on this page:")
for elem in page_1_elements[:5]:
    print(f"   {elem['type']:15s}: '{elem['text'][:60]}'")

# Check for overlap or misalignment
print(f"\n" + "=" * 80)
print(f"🔍 CHECKING FOR CONTENT MISALIGNMENT")
print("=" * 80)

# Check if Chapter 3 has any content mentioning "interruptores" or "52J" (which is Chapter 4 content)
ch4_keywords_in_ch3 = [e for e in data3['elements']
                        if any(keyword in e.get('text', '').lower()
                              for keyword in ['52j3', '52j6', 'don héctor operaban'])]

if ch4_keywords_in_ch3:
    print(f"❌ ISSUE FOUND: Chapter 3 JSON contains Chapter 4 content!")
    for elem in ch4_keywords_in_ch3:
        print(f"   Page {elem['page']}: {elem['text'][:70]}")
else:
    print(f"✅ No Chapter 4 content found in Chapter 3 JSON")

# Check if Chapter 4 is missing its first page
if page_1_elements:
    first_text = page_1_elements[0].get('text', '')
    if 'Los  interruptores  52J3' in first_text or '52J3' in first_text:
        print(f"✅ Chapter 4 starts with correct content (interruptores 52J3...)")
    else:
        print(f"⚠️  Chapter 4 first content: '{first_text[:70]}'")
        print(f"   Expected: Content about 'Los interruptores 52J3...'")

doc3.close()
doc4.close()

print("\n" + "=" * 80)
print("✅ Diagnostic complete")
print("=" * 80)
