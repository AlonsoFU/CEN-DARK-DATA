#!/usr/bin/env python3
"""
Process all chapters with Docling and create annotated PDFs
Runs lightweight extraction on chapters 2-11
"""
import json
import sys
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime

# Chapter definitions with page ranges
CHAPTERS = {
    1: {"name": "Descripción de la Perturbación", "pages": (1, 11)},
    2: {"name": "Equipamiento Afectado", "pages": (12, 90)},
    3: {"name": "Energía No Suministrada", "pages": (91, 153)},
    4: {"name": "Configuraciones de Falla", "pages": (154, 159)},
    5: {"name": "Cronología de Eventos", "pages": (160, 171)},
    6: {"name": "Normalización del Servicio", "pages": (172, 265)},
    7: {"name": "Análisis de Causas de Falla", "pages": (266, 347)},
    8: {"name": "Detalle de Información", "pages": (348, 348)},
    9: {"name": "Análisis de Protecciones", "pages": (349, 381)},
    10: {"name": "Pronunciamiento Técnico", "pages": (382, 392)},
    11: {"name": "Recomendaciones", "pages": (393, 399)},
}

# Paths
BASE_DIR = Path(__file__).parent
FULL_PDF = BASE_DIR.parent.parent / "claude_ocr"
OUTPUT_ROOT = BASE_DIR

# Add project to path for docling
project_root = BASE_DIR.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🚀 BATCH DOCLING PROCESSING - All Chapters")
print("=" * 80)
print()

def extract_chapter_with_docling(chapter_num, chapter_info):
    """Extract layout from a single chapter using docling"""
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        TableStructureOptions,
        TableFormerMode,
        AcceleratorOptions
    )

    chapter_name = chapter_info["name"]
    start_page, end_page = chapter_info["pages"]

    print(f"📖 Chapter {chapter_num}: {chapter_name} (pages {start_page}-{end_page})")

    # Setup output directory
    output_dir = OUTPUT_ROOT / f"capitulo_{chapter_num:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = output_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    scripts_dir = output_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # PDF path
    pdf_path = BASE_DIR.parent.parent.parent / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"   ⚠️  PDF not found: {pdf_path}")
        return False

    # Configure lightweight pipeline
    print(f"   🔧 Configuring lightweight extractor...")
    pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(
            num_threads=2,
            device="cuda",
        ),
        do_ocr=False,
        do_picture_classification=False,
        do_picture_description=False,
        do_code_enrichment=False,
        do_formula_enrichment=False,
        do_table_structure=True,
        table_structure_options=TableStructureOptions(
            mode=TableFormerMode.FAST,
            do_cell_matching=True,
        ),
        generate_page_images=False,
        generate_picture_images=False,
        generate_table_images=False,
        images_scale=0.5,
    )

    format_options = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }

    converter = DocumentConverter(format_options=format_options)

    # Convert
    print(f"   🔍 Converting pages {start_page}-{end_page}...")
    result = converter.convert(str(pdf_path))

    # Extract elements
    print(f"   📊 Extracting elements...")
    chapter_elements = []

    for item in result.document.iterate_items():
        if isinstance(item, tuple):
            item, level = item

        if not hasattr(item, 'prov') or not item.prov:
            continue

        for prov in item.prov:
            if start_page <= prov.page_no <= end_page:
                if prov.page_no not in result.document.pages:
                    continue

                page = result.document.pages[prov.page_no]
                bbox = prov.bbox
                bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)
                bbox_norm = bbox.normalized(page.size)

                if hasattr(item, 'text'):
                    text_content = item.text if item.text else ""
                elif hasattr(item, 'export_to_markdown'):
                    text_content = item.export_to_markdown()
                else:
                    text_content = str(item) if item else ""

                element = {
                    "type": item.label,
                    "text": text_content,
                    "page": prov.page_no,
                    "bbox": {
                        "x0": round(bbox_tl.l, 2),
                        "y0": round(bbox_tl.t, 2),
                        "x1": round(bbox_tl.r, 2),
                        "y1": round(bbox_tl.b, 2)
                    },
                    "bbox_normalized": {
                        "x0": round(bbox_norm.l, 4),
                        "y0": round(bbox_norm.t, 4),
                        "x1": round(bbox_norm.r, 4),
                        "y1": round(bbox_norm.b, 4)
                    },
                    "page_dimensions": {
                        "width": page.size.width,
                        "height": page.size.height
                    }
                }

                chapter_elements.append(element)

    # Save JSON
    json_path = outputs_dir / "layout_lightweight.json"
    data = {
        "metadata": {
            "chapter": f"Capítulo {chapter_num} - {chapter_name}",
            "pdf_source": str(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "extractor": "Docling Lightweight (4GB GPU optimized)",
            "total_elements": len(chapter_elements),
            "pages": f"{start_page}-{end_page}",
            "optimizations": [
                "OCR disabled",
                "Table mode: FAST",
                "No image generation",
                "No enrichment models",
                "Memory footprint: ~1.3 GB"
            ]
        },
        "elements": chapter_elements
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Extracted {len(chapter_elements)} elements")
    print(f"   💾 Saved: {json_path.name}")
    print()

    return True

# Process each chapter
print("🔄 Starting batch processing...")
print()

success_count = 0
for chapter_num, chapter_info in CHAPTERS.items():
    try:
        if extract_chapter_with_docling(chapter_num, chapter_info):
            success_count += 1
    except Exception as e:
        print(f"   ❌ Error processing chapter {chapter_num}: {e}")
        print()
        continue

print("=" * 80)
print("✅ BATCH PROCESSING COMPLETE")
print("=" * 80)
print(f"📊 Processed: {success_count}/{len(CHAPTERS)} chapters")
print()
print("📁 Output directories:")
for chapter_num in CHAPTERS.keys():
    output_dir = OUTPUT_ROOT / f"capitulo_{chapter_num:02d}"
    if output_dir.exists():
        print(f"   • {output_dir}")
print()
