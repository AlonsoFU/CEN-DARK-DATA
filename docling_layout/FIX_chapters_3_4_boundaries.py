#!/usr/bin/env python3
"""
Fix Chapter 3 and 4 PDF boundaries

ISSUE: Page 153 contains Chapter 4 title but was included in Chapter 3 PDF
SOLUTION: Re-split with corrected boundaries
  - Chapter 3: pages 91-152 (was 91-153)
  - Chapter 4: pages 153-159 (was 154-159)
"""
import fitz
from pathlib import Path

print("=" * 80)
print("🔧 FIXING CHAPTER 3 & 4 BOUNDARIES")
print("=" * 80)

# Paths
source_pdf = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
output_dir = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr")

# Open source PDF
doc = fitz.open(source_pdf)
print(f"\n📄 Source PDF: {len(doc)} pages")

# Create Chapter 3: pages 91-152 (indices 90-151)
print("\n" + "=" * 80)
print("📝 Creating Chapter 3 (pages 91-152)")
print("=" * 80)

ch3_output = output_dir / "capitulo_03" / "EAF-089-2025_capitulo_03_pages_91-152.pdf"
ch3_output.parent.mkdir(parents=True, exist_ok=True)

ch3_doc = fitz.open()
for page_num in range(90, 152):  # Pages 91-152 (0-indexed: 90-151)
    ch3_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

ch3_doc.save(ch3_output)
ch3_doc.close()

print(f"✅ Saved: {ch3_output}")
print(f"   Pages: 91-152 (62 pages)")

# Create Chapter 4: pages 153-159 (indices 152-158)
print("\n" + "=" * 80)
print("📝 Creating Chapter 4 (pages 153-159)")
print("=" * 80)

ch4_output = output_dir / "capitulo_04" / "EAF-089-2025_capitulo_04_pages_153-159.pdf"
ch4_output.parent.mkdir(parents=True, exist_ok=True)

ch4_doc = fitz.open()
for page_num in range(152, 159):  # Pages 153-159 (0-indexed: 152-158)
    ch4_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

ch4_doc.save(ch4_output)
ch4_doc.close()

print(f"✅ Saved: {ch4_output}")
print(f"   Pages: 153-159 (7 pages)")

doc.close()

# Verify content
print("\n" + "=" * 80)
print("🔍 VERIFYING CORRECTED PDFs")
print("=" * 80)

# Check Chapter 3 last page
ch3_verify = fitz.open(ch3_output)
last_page_ch3 = ch3_verify[len(ch3_verify)-1]
last_text = last_page_ch3.get_text()

print(f"\nChapter 3 last page ({len(ch3_verify)} total):")
if "Estado y configuración previo a la falla" in last_text:
    print("✅ Ends with 'Estado y configuración previo a la falla' - CORRECT")
else:
    print(f"⚠️  Ends with: {last_text[:100]}")

# Check Chapter 4 first page
ch4_verify = fitz.open(ch4_output)
first_page_ch4 = ch4_verify[0]
first_text = first_page_ch4.get_text()

print(f"\nChapter 4 first page ({len(ch4_verify)} total):")
if "4. Descripción de las configuraciones" in first_text:
    print("✅ Starts with '4. Descripción de las configuraciones' - CORRECT")
else:
    print(f"⚠️  Starts with: {first_text[:100]}")

ch3_verify.close()
ch4_verify.close()

print("\n" + "=" * 80)
print("✅ PDF boundaries corrected!")
print("=" * 80)
print("\nNext steps:")
print("1. Re-extract Chapter 3 with new PDF (pages 91-152)")
print("2. Re-extract Chapter 4 with new PDF (pages 153-159)")
print("3. Re-visualize both chapters")
