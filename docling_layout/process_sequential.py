#!/usr/bin/env python3
"""
Sequential Docling processing - ONE chapter at a time
SAFE and RELIABLE for 4GB GPU
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import time

# Chapter definitions with page counts for time estimates
CHAPTERS = {
    1: {"name": "Descripción de la Perturbación", "pages": (1, 11), "page_count": 11},
    2: {"name": "Equipamiento Afectado", "pages": (12, 90), "page_count": 79},
    3: {"name": "Energía No Suministrada", "pages": (91, 153), "page_count": 63},
    4: {"name": "Configuraciones de Falla", "pages": (154, 159), "page_count": 6},
    5: {"name": "Cronología de Eventos", "pages": (160, 171), "page_count": 12},
    6: {"name": "Normalización del Servicio", "pages": (172, 265), "page_count": 94},
    7: {"name": "Análisis de Causas de Falla", "pages": (266, 347), "page_count": 82},
    8: {"name": "Detalle de Información", "pages": (348, 348), "page_count": 1},
    9: {"name": "Análisis de Protecciones", "pages": (349, 381), "page_count": 33},
    10: {"name": "Pronunciamiento Técnico", "pages": (382, 392), "page_count": 11},
    11: {"name": "Recomendaciones", "pages": (393, 399), "page_count": 7},
}

BASE_DIR = Path(__file__).parent
PDF_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")

# Estimate ~1.5 minutes per page in lightweight mode
MINUTES_PER_PAGE = 1.5

print("=" * 80)
print("📄 SEQUENTIAL DOCLING PROCESSING")
print("=" * 80)
print()

# Check which chapters are already done
completed = []
remaining = []

for ch_num, ch_info in CHAPTERS.items():
    output_dir = BASE_DIR / f"capitulo_{ch_num:02d}" / "outputs"
    json_path = output_dir / "layout_lightweight.json"
    if json_path.exists():
        completed.append(ch_num)
    else:
        remaining.append(ch_num)

print(f"✅ Already completed: {len(completed)} chapters {completed}")
print(f"⏳ Remaining: {len(remaining)} chapters {remaining}")
print()

if not remaining:
    print("🎉 All chapters already processed!")
    sys.exit(0)

# Calculate total estimated time
total_pages = sum(CHAPTERS[ch]["page_count"] for ch in remaining)
total_minutes = total_pages * MINUTES_PER_PAGE
total_hours = total_minutes / 60

print("⏱️  TIME ESTIMATES FOR REMAINING CHAPTERS:")
print("-" * 80)
for ch_num in remaining:
    ch = CHAPTERS[ch_num]
    est_min = ch["page_count"] * MINUTES_PER_PAGE
    print(f"   Chapter {ch_num:2d}: {ch['page_count']:3d} pages → ~{est_min:5.1f} minutes ({est_min/60:.1f}h)")
print("-" * 80)
print(f"   TOTAL:      {total_pages:3d} pages → ~{total_minutes:5.1f} minutes ({total_hours:.1f}h)")
print()

print("💡 TIP: This will process ONE chapter at a time (sequential)")
print("   Safe for 4GB GPU, uses ~1.3 GB VRAM per chapter")
print()

# Auto-start in background mode (no user input required)
print("🚀 AUTO-STARTING sequential processing...")
print("   (You can monitor progress with: tail -f docling_sequential.log)")
print()

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)

# Configure once
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(num_threads=2, device="cuda"),
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

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

total_start = time.time()
results = []

for i, ch_num in enumerate(remaining, 1):
    ch_info = CHAPTERS[ch_num]
    print(f"[{i}/{len(remaining)}] Chapter {ch_num}: {ch_info['name']}")
    print(f"         Pages {ch_info['pages'][0]}-{ch_info['pages'][1]} ({ch_info['page_count']} pages)")
    
    start_time = time.time()
    
    try:
        # Setup output directory
        output_dir = BASE_DIR / f"capitulo_{ch_num:02d}" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert
        print(f"         🔍 Converting...")
        result = converter.convert(str(PDF_PATH))
        
        # Extract elements
        chapter_elements = []
        for item in result.document.iterate_items():
            if isinstance(item, tuple):
                item, level = item
            if not hasattr(item, 'prov') or not item.prov:
                continue
            
            for prov in item.prov:
                if ch_info['pages'][0] <= prov.page_no <= ch_info['pages'][1]:
                    if prov.page_no not in result.document.pages:
                        continue
                    page = result.document.pages[prov.page_no]
                    bbox = prov.bbox
                    bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_norm = bbox.normalized(page.size)
                    
                    # Extract text content based on item type
                    if hasattr(item, 'text'):
                        text_content = item.text if item.text else ""
                    elif hasattr(item, 'export_to_markdown'):
                        # Some items require 'doc' argument for export_to_markdown
                        try:
                            text_content = item.export_to_markdown(result.document)
                        except TypeError:
                            # Fallback if it doesn't accept doc argument
                            try:
                                text_content = item.export_to_markdown()
                            except:
                                text_content = str(item) if item else ""
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
        
        # Save
        json_path = output_dir / "layout_lightweight.json"
        data = {
            "metadata": {
                "chapter": f"Capítulo {ch_num} - {ch_info['name']}",
                "pdf_source": str(PDF_PATH),
                "extraction_date": datetime.now().isoformat(),
                "extractor": "Docling Lightweight (Sequential)",
                "total_elements": len(chapter_elements),
                "pages": f"{ch_info['pages'][0]}-{ch_info['pages'][1]}",
            },
            "elements": chapter_elements
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        elapsed = time.time() - start_time
        print(f"         ✅ Done! {len(chapter_elements)} elements in {elapsed/60:.1f} min")
        results.append((ch_num, True, elapsed))
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"         ❌ Error: {e}")
        results.append((ch_num, False, elapsed))
    
    print()

total_elapsed = time.time() - total_start

print("=" * 80)
print("✅ PROCESSING COMPLETE")
print("=" * 80)
successful = [r[0] for r in results if r[1]]
failed = [r[0] for r in results if not r[1]]
print(f"✅ Successful: {len(successful)} chapters {successful}")
print(f"❌ Failed: {len(failed)} chapters {failed}")
print(f"⏱️  Total time: {total_elapsed/3600:.2f} hours")
print()
