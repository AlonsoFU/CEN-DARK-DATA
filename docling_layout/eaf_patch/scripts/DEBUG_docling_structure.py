#!/usr/bin/env python3
"""
Debug Docling Structure - Find where clusters are stored
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from universal_patch_with_pdf_extraction import apply_universal_patch_with_pdf
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

PDF_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")

apply_universal_patch_with_pdf(str(PDF_PATH))

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(PDF_PATH))

print("\n" + "=" * 80)
print("DOCLING RESULT STRUCTURE")
print("=" * 80)

print("\n📦 result object attributes:")
for attr in dir(result):
    if not attr.startswith('_'):
        print(f"   - {attr}")

print("\n📦 result.pages:")
print(f"   Type: {type(result.pages)}")
print(f"   Length: {len(result.pages) if hasattr(result.pages, '__len__') else 'N/A'}")

if result.pages:
    print("\n📄 First page object attributes:")
    page = result.pages[0]
    for attr in dir(page):
        if not attr.startswith('_'):
            val = getattr(page, attr, None)
            if not callable(val):
                print(f"   - {attr}: {type(val).__name__}")

print("\n📖 result.document:")
print(f"   Type: {type(result.document)}")

print("\n📖 result.document attributes:")
for attr in dir(result.document):
    if not attr.startswith('_'):
        val = getattr(result.document, attr, None)
        if not callable(val):
            print(f"   - {attr}: {type(val).__name__}")

# Try to access internal structure
print("\n🔍 Searching for clusters...")

if hasattr(result, '_backend'):
    print(f"   result._backend: {type(result._backend)}")

if hasattr(result, 'pages'):
    for i, page in enumerate(result.pages[:2]):  # Check first 2 pages
        print(f"\n📄 Page {i} private attributes:")
        for attr in dir(page):
            if attr.startswith('_') and not attr.startswith('__'):
                try:
                    val = getattr(page, attr, None)
                    print(f"   - {attr}: {type(val).__name__}")

                    # Check for clusters
                    if hasattr(val, 'regular_clusters'):
                        clusters = val.regular_clusters
                        print(f"     ✅ FOUND regular_clusters: {len(clusters)} clusters")
                        if clusters:
                            c = clusters[0]
                            print(f"     First cluster: label={c.label}, bbox={c.bbox}, cells={len(c.cells) if c.cells else 0}")
                except:
                    pass

print("\n" + "=" * 80)
