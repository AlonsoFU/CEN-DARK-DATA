#!/usr/bin/env python3
"""
UNIVERSAL DOCLING EXTRACTION SCRIPT
Works for ANY chapter - just change the configuration section

Usage:
    python UNIVERSAL_extract_any_chapter.py

Or pass chapter number as argument:
    python UNIVERSAL_extract_any_chapter.py 5
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf, apply_zona_fix_to_document

# ============================================================================
# CONFIGURATION - ONLY CHANGE THIS SECTION!
# ============================================================================

# Get chapter number from command line or use default
if len(sys.argv) > 1:
    CHAPTER_NUM = int(sys.argv[1])
else:
    CHAPTER_NUM = 5  # Default chapter

# Chapter metadata - CORRECTED page ranges from actual PDFs
CHAPTER_INFO = {
    1: {
        'name': 'Descripción de la perturbación',
        'pages': 11,
        'page_range': '1-11'
    },
    2: {
        'name': 'Equipamiento afectado',
        'pages': 79,
        'page_range': '12-90'
    },
    3: {
        'name': 'Energía no suministrada',
        'pages': 62,
        'page_range': '91-152'
    },
    4: {
        'name': 'Configuraciones previo y posterior',
        'pages': 7,
        'page_range': '153-159'
    },
    5: {
        'name': 'Cronología de eventos',
        'pages': 12,
        'page_range': '160-171'
    },
    6: {
        'name': 'Normalización del servicio',
        'pages': 94,
        'page_range': '172-265'
    },
    7: {
        'name': 'Análisis de las causas de la falla',
        'pages': 82,
        'page_range': '266-347'
    },
    8: {
        'name': 'Detalle de información',
        'pages': 1,
        'page_range': '348-348'
    },
    9: {
        'name': 'Análisis de protecciones',
        'pages': 33,
        'page_range': '349-381'
    },
    10: {
        'name': 'Pronunciamiento técnico',
        'pages': 11,
        'page_range': '382-392'
    },
    11: {
        'name': 'Recomendaciones',
        'pages': 7,
        'page_range': '393-399'
    }
}

# Validate chapter
if CHAPTER_NUM not in CHAPTER_INFO:
    print(f"❌ Error: Chapter {CHAPTER_NUM} not found in configuration")
    print(f"Available chapters: {sorted(CHAPTER_INFO.keys())}")
    sys.exit(1)

chapter = CHAPTER_INFO[CHAPTER_NUM]

# Paths
BASE_DIR = Path(__file__).parent
PDF_PATH = BASE_DIR.parent / "claude_ocr" / f"capitulo_{CHAPTER_NUM:02d}" / f"EAF-089-2025_capitulo_{CHAPTER_NUM:02d}_pages_{chapter['page_range']}.pdf"
OUTPUT_DIR = BASE_DIR / f"capitulo_{CHAPTER_NUM:02d}" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "layout_WITH_PATCH.json"
OUTPUT_PDF = OUTPUT_DIR / f"capitulo_{CHAPTER_NUM:02d}_annotated.pdf"

# Docling configuration (same for all chapters)
DOCLING_CONFIG = {
    "do_ocr": False,                    # Native PDF text only
    "do_table_structure": True,          # Extract table structure
    "table_mode": "ACCURATE",            # ACCURATE or FAST
    "do_picture_classification": True,   # Classify images
    "do_formula_enrichment": True,       # Extract LaTeX formulas ✅
    "do_code_enrichment": False,         # Extract code blocks
    "do_picture_description": False,     # AI image descriptions (VLM)
    "generate_page_images": False,       # Generate page images
    "images_scale": 1.0                  # Image scaling factor
}

# Patch configuration (same for all chapters)
PATCH_CONFIG = {
    "enabled": True,
    "apply_zona_fix": True
}

# Import standard color scheme (ensures consistency across all chapters)
from STANDARD_COLORS import DOCLING_COLORS as COLORS

# ============================================================================
# EXTRACTION LOGIC - NO NEED TO MODIFY!
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print(f"📖 UNIVERSAL DOCLING EXTRACTION")
    print("=" * 80)
    print(f"\nChapter {CHAPTER_NUM}: {chapter['name']}")
    print(f"Pages: {chapter['pages']} (range {chapter['page_range']})")
    print(f"PDF: {PDF_PATH.name}")
    print(f"Output dir: {OUTPUT_DIR}")

    # Verify PDF exists
    if not PDF_PATH.exists():
        print(f"\n❌ Error: PDF not found at {PDF_PATH}")
        print("\nPlease check:")
        print("1. Chapter number is correct")
        print("2. PDF exists in claude_ocr directory")
        print("3. PDF filename matches expected pattern")
        sys.exit(1)

    print(f"✅ PDF found: {PDF_PATH.stat().st_size / (1024*1024):.1f} MB")

    # ========================================================================
    # STEP 1: Apply Monkey Patch
    # ========================================================================
    if PATCH_CONFIG['enabled']:
        print("\n" + "=" * 80)
        print("🐵 STEP 1: Applying EAF Monkey Patch")
        print("=" * 80)
        apply_universal_patch_with_pdf(str(PDF_PATH))
        print("✅ Patch applied successfully")
    else:
        print("\n⚠️  Patch disabled - running native Docling only")

    # ========================================================================
    # STEP 2: Configure Docling Pipeline
    # ========================================================================
    print("\n" + "=" * 80)
    print("⚙️  STEP 2: Configuring Docling Pipeline")
    print("=" * 80)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = DOCLING_CONFIG['do_ocr']
    pipeline_options.do_table_structure = DOCLING_CONFIG['do_table_structure']
    pipeline_options.do_picture_classification = DOCLING_CONFIG.get('do_picture_classification', True)
    pipeline_options.do_formula_enrichment = DOCLING_CONFIG.get('do_formula_enrichment', False)
    pipeline_options.do_code_enrichment = DOCLING_CONFIG.get('do_code_enrichment', False)
    pipeline_options.do_picture_description = DOCLING_CONFIG.get('do_picture_description', False)
    pipeline_options.generate_page_images = DOCLING_CONFIG.get('generate_page_images', False)
    pipeline_options.images_scale = DOCLING_CONFIG.get('images_scale', 1.0)

    if DOCLING_CONFIG['table_mode'] == 'ACCURATE':
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    else:
        pipeline_options.table_structure_options.mode = TableFormerMode.FAST

    print(f"✅ OCR: {pipeline_options.do_ocr}")
    print(f"✅ Tables: {DOCLING_CONFIG['table_mode']}")
    print(f"✅ Pictures: {pipeline_options.do_picture_classification}")
    print(f"✅ Formulas: {pipeline_options.do_formula_enrichment}")
    print(f"✅ Code: {pipeline_options.do_code_enrichment}")

    # ========================================================================
    # STEP 3: Run Docling Extraction
    # ========================================================================
    print("\n" + "=" * 80)
    print(f"🔄 STEP 3: Processing Chapter {CHAPTER_NUM}")
    print("=" * 80)

    estimated_time = chapter['pages'] * 3.1 / 60  # 3.1 sec/page
    print(f"⏱️  Estimated time: {estimated_time:.1f} minutes ({chapter['pages']} pages)")
    print(f"🐵 Patch is {'ACTIVE' if PATCH_CONFIG['enabled'] else 'DISABLED'}")
    print()

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(str(PDF_PATH))

    print("\n✅ Docling extraction complete")

    # ========================================================================
    # STEP 4: Apply Document-Level Zona Fix
    # ========================================================================
    if PATCH_CONFIG.get('apply_zona_fix', True):
        print("\n" + "=" * 80)
        print("🔧 STEP 4: Applying Document-Level Zona Fix")
        print("=" * 80)

        doc = result.document
        reclassified_count = apply_zona_fix_to_document(doc)

        print(f"✅ Zona fix applied ({reclassified_count} items reclassified)")

    # ========================================================================
    # STEP 5: Extract Elements to JSON (using iterate_items for clusters)
    # ========================================================================
    print("\n" + "=" * 80)
    print("📄 STEP 5: Extracting Elements to JSON")
    print("=" * 80)

    elements = []
    doc = result.document

    # Use iterate_items - each item IS a cluster with its own bounding box
    for item, level in doc.iterate_items():
        page_num = None
        if hasattr(item, 'prov') and item.prov:
            page_num = item.prov[0].page_no if item.prov else None

        if page_num is not None:
            bbox_dict = None
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0]
                if hasattr(prov, 'bbox'):
                    if page_num in doc.pages:
                        page = doc.pages[page_num]
                        # CRITICAL: Proper coordinate conversion to top-left origin
                        bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                        bbox_dict = {
                            'x0': bbox_tl.l,
                            'y0': bbox_tl.t,
                            'x1': bbox_tl.r,
                            'y1': bbox_tl.b
                        }

            elements.append({
                'type': item.label.value if hasattr(item, 'label') else 'unknown',
                'text': item.text if hasattr(item, 'text') else '',
                'page': page_num,
                'bbox': bbox_dict,
                'level': level
            })

    # Save JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'chapter': CHAPTER_NUM,
                'chapter_name': chapter['name'],
                'extractor': 'Docling + EAF Patch v2.1' if PATCH_CONFIG['enabled'] else 'Docling Native',
                'extraction_date': datetime.now().isoformat(),
                'total_elements': len(elements),
                'total_pages': chapter['pages'],
                'page_range': chapter['page_range'],
                'config': {
                    'docling': DOCLING_CONFIG,
                    'patch': PATCH_CONFIG
                }
            },
            'elements': elements
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved JSON: {OUTPUT_JSON.name}")
    print(f"📊 Total elements: {len(elements)}")

    # Statistics
    stats = {}
    for elem in elements:
        elem_type = elem['type']
        stats[elem_type] = stats.get(elem_type, 0) + 1

    print("\n📊 Elements by type:")
    for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(elements) * 100
        print(f"   {elem_type:<20}: {count:>4} ({percentage:>5.1f}%)")

    # ========================================================================
    # STEP 6: Generate Annotated PDF with Bounding Boxes
    # ========================================================================
    print("\n" + "=" * 80)
    print("🎨 STEP 6: Generating Annotated PDF")
    print("=" * 80)

    doc_pdf = fitz.open(PDF_PATH)
    boxes_drawn = 0
    skipped_no_bbox = 0
    skipped_out_of_range = 0

    for elem in elements:
        page_num = elem.get('page')
        bbox = elem.get('bbox')
        elem_type = elem.get('type', 'unknown')

        if bbox is None or page_num is None:
            skipped_no_bbox += 1
            continue

        # CRITICAL BUG FIX: Convert 1-indexed (Docling) to 0-indexed (PyMuPDF)
        pymupdf_page_idx = page_num - 1

        if pymupdf_page_idx < 0 or pymupdf_page_idx >= len(doc_pdf):
            skipped_out_of_range += 1
            continue

        page = doc_pdf[pymupdf_page_idx]

        # Get color
        color = COLORS.get(elem_type, (0.5, 0.5, 0.5))

        # Draw rectangle
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
        page.draw_rect(rect, color=color, width=1.5)

        boxes_drawn += 1

    # Save PDF
    doc_pdf.save(OUTPUT_PDF)
    doc_pdf.close()

    print(f"✅ Drew {boxes_drawn} bounding boxes")
    if skipped_no_bbox > 0:
        print(f"⚠️  Skipped {skipped_no_bbox} elements (no bbox)")
    if skipped_out_of_range > 0:
        print(f"⚠️  Skipped {skipped_out_of_range} elements (out of range)")

    print(f"✅ Saved PDF: {OUTPUT_PDF.name}")

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print(f"✅ CHAPTER {CHAPTER_NUM} EXTRACTION COMPLETE!")
    print("=" * 80)
    print(f"\n📁 Output files:")
    print(f"   JSON: {OUTPUT_JSON}")
    print(f"   PDF:  {OUTPUT_PDF}")
    print(f"\n📊 Summary:")
    print(f"   Total elements: {len(elements)}")
    print(f"   Pages processed: {chapter['pages']}")
    print(f"   Bounding boxes: {boxes_drawn}")
    print(f"   Patch applied: {'Yes ✅' if PATCH_CONFIG['enabled'] else 'No'}")
    print("\n" + "=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Extraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
