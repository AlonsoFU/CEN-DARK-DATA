#!/usr/bin/env python3
"""
Quick test of the title merge fix on Chapter 6 page 1
"""
import sys
from pathlib import Path

# Add eaf_patch to path
sys.path.insert(0, str(Path(__file__).parent / "eaf_patch"))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Paths
CHAPTER_PDF = "/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf"

print("="*80)
print("Testing Title Merge Fix on Chapter 6 Page 1")
print("="*80)

# Apply patch
apply_universal_patch_with_pdf(CHAPTER_PDF)

# Configure lightweight processing
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

format_options = {InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}

# Convert only first page for speed
converter = DocumentConverter(format_options=format_options)
result = converter.convert(CHAPTER_PDF)

print("\n" + "="*80)
print("EXTRACTION RESULTS - Page 1 Elements")
print("="*80)

# Extract elements from page 1 only
page1_elements = []
for item, level in result.document.iterate_items():
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None
        if page_num == 1:
            text = ""
            if hasattr(item, 'text'):
                text = item.text
            elif hasattr(item, 'export_to_markdown'):
                text = item.export_to_markdown()

            page1_elements.append({
                'type': item.label,
                'text': text
            })

print(f"\nTotal elements on page 1: {len(page1_elements)}")
print("\nSearching for title elements containing '6' or 'Normalización':")
print("-"*80)

found_title = False
for elem in page1_elements:
    text = elem['text'].strip()
    if ('6' in text[:5] or 'normalización' in text.lower()[:30]) and elem['type'] in ['section_header', 'title']:
        print(f"\n✅ [{elem['type']}]")
        print(f"   Text: '{text}'")
        found_title = True

if not found_title:
    print("\n❌ No title found with '6' or 'Normalización'")
    print("\nAll section_header and title elements on page 1:")
    for elem in page1_elements:
        if elem['type'] in ['section_header', 'title']:
            print(f"   [{elem['type']}] {elem['text'][:80]}")

print("\n" + "="*80)
print("EXPECTED RESULT:")
print("✅ [section_header] '6. Normalización del servicio'")
print("="*80)
