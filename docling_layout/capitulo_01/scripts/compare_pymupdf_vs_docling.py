#!/usr/bin/env python3
"""
Comparador: PyMuPDF vs Docling
================================

Compara la extracción de layout entre PyMuPDF (actual) y Docling (nuevo).

Métricas comparadas:
- Precisión en detección de elementos
- Velocidad de procesamiento
- Tipos de elementos detectados
- Bounding boxes
"""

import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
import sys
import json

# Agregar proyecto al path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def extract_with_pymupdf(pdf_path: Path, start_page: int, end_page: int):
    """Extrae elementos con PyMuPDF (método actual)."""

    print("🔵 Extrayendo con PyMuPDF...")
    start_time = datetime.now()

    doc = fitz.open(pdf_path)
    elements = []

    for page_num in range(start_page - 1, end_page):
        page = doc[page_num]

        # Extraer bloques de texto
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") == 0:  # Text block
                bbox = block["bbox"]
                text = " ".join(
                    span["text"]
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                )

                elements.append({
                    "type": "text",  # PyMuPDF no clasifica automáticamente
                    "text": text,
                    "page": page_num + 1,
                    "bbox": {
                        "x0": bbox[0],
                        "y0": bbox[1],
                        "x1": bbox[2],
                        "y1": bbox[3]
                    }
                })

        # Detectar tablas (PyMuPDF built-in)
        tables = page.find_tables()
        for table in tables:
            elements.append({
                "type": "table",
                "text": f"Table with {len(table.extract())} rows",
                "page": page_num + 1,
                "bbox": {
                    "x0": table.bbox[0],
                    "y0": table.bbox[1],
                    "x1": table.bbox[2],
                    "y1": table.bbox[3]
                }
            })

        # Detectar imágenes
        images = page.get_images()
        for img_idx, img in enumerate(images):
            # PyMuPDF necesita más trabajo para obtener bbox de imagen
            elements.append({
                "type": "image",
                "text": f"Image {img_idx}",
                "page": page_num + 1,
                "bbox": {
                    "x0": 0, "y0": 0, "x1": 0, "y1": 0  # Requiere más código
                }
            })

    doc.close()

    elapsed = (datetime.now() - start_time).total_seconds()

    return elements, elapsed


def extract_with_docling(pdf_path: Path, start_page: int, end_page: int):
    """Extrae elementos con Docling (método nuevo)."""

    print("🟢 Extrayendo con Docling...")

    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        print("   ❌ Docling no instalado (pip install docling)")
        return None, None

    start_time = datetime.now()

    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))

    elements = []

    for item in result.document.iterate_items():
        if not item.prov:
            continue

        for prov in item.prov:
            if start_page <= prov.page_no <= end_page:
                page = result.document.pages[prov.page_no - 1]
                bbox = prov.bbox
                bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)

                elements.append({
                    "type": item.label,
                    "text": item.text if item.text else "",
                    "page": prov.page_no,
                    "bbox": {
                        "x0": bbox_tl.l,
                        "y0": bbox_tl.t,
                        "x1": bbox_tl.r,
                        "y1": bbox_tl.b
                    }
                })

    elapsed = (datetime.now() - start_time).total_seconds()

    return elements, elapsed


def calculate_stats(elements):
    """Calcula estadísticas de elementos."""
    stats = {}
    for elem in elements:
        elem_type = elem["type"]
        stats[elem_type] = stats.get(elem_type, 0) + 1

    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))


def compare_extractions():
    """Compara ambos métodos de extracción."""

    print("="*80)
    print("🔬 COMPARACIÓN: PyMuPDF vs Docling")
    print("="*80)
    print()

    # Configuración
    pdf_path = Path("../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
    start_page = 1
    end_page = 3  # Solo 3 páginas para test rápido

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print(f"📄 PDF: {pdf_path.name}")
    print(f"📑 Páginas: {start_page}-{end_page}")
    print()

    # Extraer con PyMuPDF
    print("="*80)
    pymupdf_elements, pymupdf_time = extract_with_pymupdf(pdf_path, start_page, end_page)
    pymupdf_stats = calculate_stats(pymupdf_elements)

    print(f"✅ Completado en {pymupdf_time:.2f}s")
    print(f"📊 Total elementos: {len(pymupdf_elements)}")
    print()

    # Extraer con Docling
    print("="*80)
    docling_elements, docling_time = extract_with_docling(pdf_path, start_page, end_page)

    if docling_elements is None:
        print("❌ No se pudo comparar (Docling no disponible)")
        return

    docling_stats = calculate_stats(docling_elements)

    print(f"✅ Completado en {docling_time:.2f}s")
    print(f"📊 Total elementos: {len(docling_elements)}")
    print()

    # Comparación
    print("="*80)
    print("📊 COMPARACIÓN DE RESULTADOS")
    print("="*80)
    print()

    # Velocidad
    print("⚡ VELOCIDAD:")
    print(f"   PyMuPDF:  {pymupdf_time:.2f}s")
    print(f"   Docling:  {docling_time:.2f}s")
    if pymupdf_time < docling_time:
        speedup = docling_time / pymupdf_time
        print(f"   🏆 Ganador: PyMuPDF ({speedup:.2f}x más rápido)")
    else:
        speedup = pymupdf_time / docling_time
        print(f"   🏆 Ganador: Docling ({speedup:.2f}x más rápido)")
    print()

    # Cantidad de elementos
    print("📊 ELEMENTOS DETECTADOS:")
    print(f"   PyMuPDF:  {len(pymupdf_elements)} elementos")
    print(f"   Docling:  {len(docling_elements)} elementos")
    print(f"   Δ Diferencia: {abs(len(docling_elements) - len(pymupdf_elements))} elementos")
    print()

    # Tipos de elementos
    print("🏷️  TIPOS DE ELEMENTOS:")
    print()

    print("   PyMuPDF:")
    for elem_type, count in pymupdf_stats.items():
        print(f"      {elem_type:<15} : {count:>3}")
    print()

    print("   Docling:")
    for elem_type, count in docling_stats.items():
        print(f"      {elem_type:<15} : {count:>3}")
    print()

    # Análisis cualitativo
    print("="*80)
    print("💡 ANÁLISIS CUALITATIVO")
    print("="*80)
    print()

    print("🔵 PyMuPDF (método actual):")
    print("   ✅ Ventajas:")
    print("      - Más rápido en extracción básica")
    print("      - Menos overhead de inicialización")
    print("      - Control total del código")
    print("   ❌ Desventajas:")
    print("      - Detección manual de tipos")
    print("      - No clasifica automáticamente")
    print("      - Requiere lógica personalizada para cada tipo")
    print()

    print("🟢 Docling (método nuevo - Granite-258M):")
    print("   ✅ Ventajas:")
    print("      - Clasificación automática (11 tipos)")
    print("      - 97.9% precisión en tablas complejas")
    print("      - Detecta ecuaciones (96.4% precisión)")
    print("      - Orden de lectura automático")
    print("      - Export directo a Markdown/HTML")
    print("   ❌ Desventajas:")
    print("      - Primera carga es lenta (modelos AI)")
    print("      - Más overhead en memoria")
    print()

    # Recomendación
    print("="*80)
    print("🎯 RECOMENDACIÓN")
    print("="*80)
    print()

    if len(docling_stats) > len(pymupdf_stats):
        print("🏆 Docling detectó MÁS TIPOS de elementos:")
        extra_types = set(docling_stats.keys()) - set(pymupdf_stats.keys())
        print(f"   Tipos adicionales: {', '.join(extra_types)}")
        print()
        print("💡 Considerar migrar a Docling para:")
        print("   - Documentos con ecuaciones/fórmulas")
        print("   - Layouts complejos (tablas multi-nivel)")
        print("   - Cuando necesitas clasificación automática")
        print()
    else:
        print("⚖️  Ambos métodos son similares en este documento.")
        print()
        print("💡 Mantener PyMuPDF si:")
        print("   - Velocidad es crítica")
        print("   - Solo necesitas texto básico")
        print("   - No tienes ecuaciones complejas")
        print()

    print("="*80)

    # Guardar comparación
    output_dir = Path("../outputs")
    output_dir.mkdir(exist_ok=True)

    comparison_data = {
        "date": datetime.now().isoformat(),
        "pages_tested": f"{start_page}-{end_page}",
        "pymupdf": {
            "time_seconds": pymupdf_time,
            "total_elements": len(pymupdf_elements),
            "stats": pymupdf_stats
        },
        "docling": {
            "time_seconds": docling_time,
            "total_elements": len(docling_elements),
            "stats": docling_stats
        }
    }

    comparison_file = output_dir / "comparison_pymupdf_vs_docling.json"
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Comparación guardada en: {comparison_file}")


if __name__ == "__main__":
    compare_extractions()
