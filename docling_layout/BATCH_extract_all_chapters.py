#!/usr/bin/env python3
"""
Batch Extract All Chapters (1-6, 10-11)
Following UNIVERSAL_DOCLING_METHODOLOGY.md
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

# Import Docling
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Chapter definitions (chapters to extract)
# CORRECTED: Chapter 3 = 91-152, Chapter 4 = 153-159 (page 153 is Chapter 4 title!)
CHAPTERS = [
    {"num": 1, "name": "Descripción de la perturbación", "pages": "1-11", "total_pages": 11},
    {"num": 2, "name": "Equipamiento afectado", "pages": "12-90", "total_pages": 79},
    {"num": 3, "name": "Energía no suministrada", "pages": "91-152", "total_pages": 62},  # CORRECTED
    {"num": 4, "name": "Configuraciones previo y posterior", "pages": "153-159", "total_pages": 7},  # CORRECTED
    {"num": 5, "name": "Cronología de eventos", "pages": "160-171", "total_pages": 12},
    {"num": 6, "name": "Normalización del servicio", "pages": "172-265", "total_pages": 94},
    {"num": 10, "name": "Pronunciamiento técnico", "pages": "382-392", "total_pages": 11},
    {"num": 11, "name": "Recomendaciones", "pages": "393-399", "total_pages": 7},
]

BASE_PDF_DIR = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr")
OUTPUT_BASE = Path(__file__).parent

print("=" * 80)
print("🔄 BATCH EXTRACTION: Chapters 1-6, 10-11")
print("=" * 80)
print(f"Total chapters to process: {len(CHAPTERS)}")
print("=" * 80)

results = []

for chapter in CHAPTERS:
    num = chapter["num"]
    name = chapter["name"]
    total_pages = chapter["total_pages"]
    
    # Paths
    chapter_dir = f"capitulo_{num:02d}"
    pdf_path = BASE_PDF_DIR / chapter_dir / f"EAF-089-2025_capitulo_{num:02d}_pages_{chapter['pages']}.pdf"
    output_dir = OUTPUT_BASE / chapter_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"📄 CHAPTER {num}: {name}")
    print(f"{'='*80}")
    print(f"Pages: {total_pages}")
    print(f"PDF: {pdf_path.name}")
    
    start_time = time.time()
    
    try:
        # Apply patch
        print("🐵 Applying EAF patch...")
        apply_universal_patch_with_pdf(str(pdf_path))
        
        # Configure Docling
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = TableFormerMode.FAST
        
        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
        
        # Run extraction
        print("🔄 Running Docling extraction...")
        converter = DocumentConverter(format_options=format_options)
        result = converter.convert(str(pdf_path))
        
        # Extract elements
        elements = []
        for item, level in result.document.iterate_items():
            page_num = None
            if hasattr(item, 'prov') and item.prov:
                page_num = item.prov[0].page_no if item.prov else None
            
            if page_num is not None:
                bbox_dict = None
                if hasattr(item, 'prov') and item.prov:
                    prov = item.prov[0]
                    if hasattr(prov, 'bbox'):
                        if page_num in result.document.pages:
                            page = result.document.pages[page_num]
                            bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                            bbox_dict = {
                                'x0': bbox_tl.l,
                                'y0': bbox_tl.t,
                                'x1': bbox_tl.r,
                                'y1': bbox_tl.b
                            }
                
                elements.append({
                    'type': str(item.label),
                    'text': item.text if hasattr(item, 'text') else '',
                    'page': page_num,
                    'bbox': bbox_dict,
                    'level': level
                })
        
        # Save JSON
        output_json = output_dir / "layout_WITH_PATCH.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'document': f"Capítulo {num} - {name}",
                    'extractor': 'Docling + EAF Patch v2.0',
                    'extraction_date': datetime.now().isoformat(),
                    'total_elements': len(elements),
                    'total_pages': total_pages,
                    'docling_labels_preserved': True
                },
                'elements': elements
            }, f, indent=2, ensure_ascii=False)
        
        elapsed = time.time() - start_time
        
        # Statistics
        stats = {}
        for elem in elements:
            elem_type = elem['type']
            stats[elem_type] = stats.get(elem_type, 0) + 1
        
        print(f"✅ Extracted {len(elements)} elements in {elapsed:.1f}s")
        print(f"📊 Top types: {', '.join([f'{k}:{v}' for k,v in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:3]])}")
        
        results.append({
            'chapter': num,
            'name': name,
            'elements': len(elements),
            'time': elapsed,
            'status': 'SUCCESS'
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        results.append({
            'chapter': num,
            'name': name,
            'elements': 0,
            'time': 0,
            'status': f'FAILED: {str(e)[:50]}'
        })

# Summary
print("\n" + "=" * 80)
print("📊 BATCH EXTRACTION SUMMARY")
print("=" * 80)
for r in results:
    status_icon = "✅" if r['status'] == 'SUCCESS' else "❌"
    print(f"{status_icon} Chapter {r['chapter']:2d}: {r['elements']:4d} elements in {r['time']:5.1f}s - {r['status']}")

total_elements = sum(r['elements'] for r in results)
total_time = sum(r['time'] for r in results)
success_count = sum(1 for r in results if r['status'] == 'SUCCESS')

print("\n" + "=" * 80)
print(f"✅ Completed: {success_count}/{len(CHAPTERS)} chapters")
print(f"📊 Total elements: {total_elements}")
print(f"⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
print("=" * 80)
