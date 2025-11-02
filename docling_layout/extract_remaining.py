#!/usr/bin/env python3
"""
Extract remaining chapters sequentially in background with GPU memory management
"""
import json
import sys
import gc
from pathlib import Path
from datetime import datetime

# Get absolute paths
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)

# Chapters to extract
CHAPTERS = {
    2: {"name": "Equipamiento Afectado", "pages": (12, 90)},
    3: {"name": "Energía No Suministrada", "pages": (91, 153)},
    4: {"name": "Configuraciones de Falla", "pages": (154, 159)},
    6: {"name": "Normalización del Servicio", "pages": (172, 265)},
    7: {"name": "Análisis de Causas de Falla", "pages": (266, 347)},
    9: {"name": "Análisis de Protecciones", "pages": (349, 381)},
}

# PDF path
pdf_path = project_root / "domains" / "operaciones" / "eaf" / "shared" / "source" / "EAF-089-2025.pdf"

if not pdf_path.exists():
    print(f"❌ ERROR: PDF not found at {pdf_path}")
    sys.exit(1)

print("=" * 80)
print("📄 SEQUENTIAL DOCLING EXTRACTION - REMAINING CHAPTERS")
print("=" * 80)
print(f"PDF: {pdf_path}")
print(f"Chapters to extract: {list(CHAPTERS.keys())}")
print()

# Check GPU
if torch.cuda.is_available():
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
else:
    print("⚠️  No GPU available, using CPU (will be slow)")
print()

# Process each chapter
for chapter_num, chapter_info in CHAPTERS.items():
    chapter_name = chapter_info["name"]
    start_page, end_page = chapter_info["pages"]

    print(f"🔄 Chapter {chapter_num}: {chapter_name} (pages {start_page}-{end_page})")

    # Setup output directory
    output_dir = script_dir / f"capitulo_{chapter_num:02d}" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "layout_lightweight.json"

    if json_path.exists():
        print(f"   ⏭️  Already exists, skipping")
        print()
        continue

    try:
        # Clear GPU memory before each chapter
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()

        # Create fresh converter for each chapter (prevents memory buildup)
        pipeline_options = PdfPipelineOptions(
            accelerator_options=AcceleratorOptions(
                num_threads=2,
                device="cuda" if torch.cuda.is_available() else "cpu",
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
        )

        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }

        converter = DocumentConverter(format_options=format_options)

        # Convert PDF
        print(f"   🔍 Converting PDF...")
        result = converter.convert(str(pdf_path))

        # Clean up converter
        del converter
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

        # Extract elements for this chapter
        print(f"   📝 Extracting elements...")
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
        data = {
            "metadata": {
                "chapter": f"Capítulo {chapter_num} - {chapter_name}",
                "pdf_source": str(pdf_path),
                "extraction_date": datetime.now().isoformat(),
                "extractor": "Docling Lightweight (Sequential)",
                "total_elements": len(chapter_elements),
                "pages": f"{start_page}-{end_page}",
            },
            "elements": chapter_elements
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"   ✅ Done! {len(chapter_elements)} elements extracted")
        print(f"   💾 Saved to: {json_path}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

print("=" * 80)
print("✅ EXTRACTION COMPLETE")
print("=" * 80)
