#!/usr/bin/env python3
"""
Docling Layout Extractor - Capítulo 1
======================================

Extrae layout completo con bounding boxes usando Docling (IBM Granite-258M).

Características:
- Detección automática de 11 tipos de elementos
- Bounding boxes precisos para cada elemento
- Export a JSON, Markdown, HTML
- Visualización de boxes en PDF
- Estadísticas detalladas

Modelo: Granite-Docling-258M (Sept 2025)
Precisión: 97.9% en tablas complejas, 96.4% en ecuaciones
"""

import json
import fitz  # PyMuPDF para visualización
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Agregar proyecto al path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class DoclingLayoutExtractor:
    """
    Extractor de layout usando Docling con visualización de bounding boxes.
    """

    def __init__(self, pdf_path: str):
        """
        Inicializa el extractor.

        Args:
            pdf_path: Ruta al PDF fuente
        """
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        # Lazy loading de Docling (evitar importar si no se usa)
        self.converter = None

        # Colores para visualización por tipo de elemento
        self.colors = {
            "text": (0, 0, 1),              # Azul
            "section-header": (1, 0, 0),     # Rojo
            "title": (0.8, 0, 0),            # Rojo oscuro
            "table": (0, 1, 0),              # Verde
            "picture": (1, 0, 1),            # Magenta
            "formula": (1, 0.5, 0),          # Naranja
            "list-item": (0.5, 0.5, 1),      # Azul claro
            "caption": (0.5, 1, 0.5),        # Verde claro
            "page-header": (0.7, 0.7, 0.7),  # Gris
            "page-footer": (0.7, 0.7, 0.7),  # Gris
            "footnote": (0.6, 0.3, 0),       # Café
        }

    def _init_docling(self):
        """Inicializa Docling (lazy loading)."""
        if self.converter is None:
            print("📦 Inicializando Docling Granite-258M...")
            try:
                from docling.document_converter import DocumentConverter
                self.converter = DocumentConverter()
                print("✅ Docling inicializado correctamente")
            except ImportError as e:
                print("❌ Error: Docling no está instalado")
                print("   Instalar con: pip install docling")
                raise e

    def extract_chapter_layout(
        self,
        start_page: int,
        end_page: int,
        output_dir: str,
        chapter_name: str = "Capítulo 1"
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Extrae layout completo de un capítulo con bounding boxes.

        Args:
            start_page: Página inicial (1-indexed)
            end_page: Página final (1-indexed, inclusive)
            output_dir: Directorio de salida
            chapter_name: Nombre del capítulo

        Returns:
            Tuple (elementos, estadísticas)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print("="*80)
        print(f"🚀 DOCLING LAYOUT EXTRACTOR - {chapter_name}")
        print("="*80)
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📑 Páginas: {start_page}-{end_page}")
        print(f"📁 Output: {output_dir}")
        print()

        # Inicializar Docling
        self._init_docling()

        # Convertir documento
        print(f"🔍 Analizando documento con Docling Granite-258M...")
        start_time = datetime.now()

        result = self.converter.convert(str(self.pdf_path))

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✅ Conversión completada en {elapsed:.2f}s")
        print()

        # Extraer elementos del rango de páginas
        print(f"📊 Extrayendo elementos de páginas {start_page}-{end_page}...")
        chapter_elements = []

        for item in result.document.iterate_items():
            # iterate_items() returns (element, level) tuples
            if isinstance(item, tuple):
                item, level = item

            if not hasattr(item, 'prov') or not item.prov:
                continue

            for prov in item.prov:
                if start_page <= prov.page_no <= end_page:
                    # Obtener página para conversión de coordenadas
                    page = result.document.pages[prov.page_no - 1]
                    bbox = prov.bbox

                    # Convertir a top-left origin (estándar)
                    bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)

                    # Normalizar (0-1) para independencia de resolución
                    bbox_norm = bbox.normalized(page.size)

                    element = {
                        "type": item.label,
                        "text": item.text if item.text else "",
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

        print(f"✅ Extraídos {len(chapter_elements)} elementos")
        print()

        # Guardar outputs
        self._save_json(chapter_elements, output_dir / "layout.json", chapter_name)
        self._save_markdown_export(result, output_dir / "document.md", start_page, end_page)
        self._save_html_export(result, output_dir / "document.html")

        # Generar visualización
        print("🎨 Generando visualización con bounding boxes...")
        annotated_path = output_dir / "annotated.pdf"
        self._create_annotated_pdf(chapter_elements, start_page, end_page, annotated_path)

        # Calcular estadísticas
        stats = self._calculate_stats(chapter_elements)
        self._save_stats(stats, chapter_elements, output_dir / "stats.json", chapter_name)

        # Resumen final
        print()
        print("="*80)
        print("✅ EXTRACCIÓN COMPLETADA")
        print("="*80)
        print(f"📊 Total elementos: {len(chapter_elements)}")
        print(f"\n📁 Archivos generados:")
        print(f"   - layout.json (estructura completa con bboxes)")
        print(f"   - document.md (markdown con contenido)")
        print(f"   - document.html (HTML con formato)")
        print(f"   - annotated.pdf (PDF con boxes visualizados)")
        print(f"   - stats.json (estadísticas detalladas)")
        print()

        self._print_stats(stats)

        return chapter_elements, stats

    def _save_json(self, elements: List[Dict], output_path: Path, chapter_name: str):
        """Guarda elementos en JSON."""
        data = {
            "metadata": {
                "chapter": chapter_name,
                "pdf_source": str(self.pdf_path),
                "extraction_date": datetime.now().isoformat(),
                "extractor": "Docling Granite-258M",
                "total_elements": len(elements)
            },
            "elements": elements
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON guardado: {output_path.name}")

    def _save_markdown_export(self, result, output_path: Path, start_page: int, end_page: int):
        """Exporta a Markdown."""
        # Docling ya provee export a markdown
        markdown = result.document.export_to_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Capítulo - Páginas {start_page}-{end_page}\n\n")
            f.write(markdown)

        print(f"✅ Markdown guardado: {output_path.name}")

    def _save_html_export(self, result, output_path: Path):
        """Exporta a HTML."""
        html = result.document.export_to_html()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML guardado: {output_path.name}")

    def _create_annotated_pdf(
        self,
        elements: List[Dict],
        start_page: int,
        end_page: int,
        output_path: Path
    ):
        """Crea PDF con bounding boxes dibujados."""
        doc = fitz.open(self.pdf_path)

        # Dibujar boxes en cada elemento
        for element in elements:
            page_num = element['page'] - 1  # 0-indexed para PyMuPDF

            if not (start_page - 1 <= page_num < end_page):
                continue

            page = doc[page_num]
            bbox = element['bbox']

            # Crear rectángulo
            rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])

            # Color según tipo
            color = self.colors.get(element['type'], (0.5, 0.5, 0.5))

            # Dibujar rectángulo
            page.draw_rect(rect, color=color, width=2)

            # Agregar label
            label_text = element['type']
            page.insert_text(
                (bbox['x0'], bbox['y0'] - 2),
                label_text,
                fontsize=8,
                color=color
            )

        # Guardar PDF anotado
        doc.save(output_path)
        doc.close()

        print(f"✅ PDF anotado guardado: {output_path.name}")

    def _calculate_stats(self, elements: List[Dict]) -> Dict[str, int]:
        """Calcula estadísticas de elementos por tipo."""
        stats = {}
        for element in elements:
            element_type = element['type']
            stats[element_type] = stats.get(element_type, 0) + 1

        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    def _save_stats(
        self,
        stats: Dict[str, int],
        elements: List[Dict],
        output_path: Path,
        chapter_name: str
    ):
        """Guarda estadísticas en JSON."""
        # Calcular estadísticas adicionales
        pages = sorted(set(e['page'] for e in elements))

        stats_data = {
            "chapter": chapter_name,
            "extraction_date": datetime.now().isoformat(),
            "summary": {
                "total_elements": len(elements),
                "total_pages": len(pages),
                "pages_range": f"{min(pages)}-{max(pages)}"
            },
            "elements_by_type": stats,
            "elements_per_page": {}
        }

        # Elementos por página
        for page in pages:
            page_elements = [e for e in elements if e['page'] == page]
            stats_data["elements_per_page"][str(page)] = {
                "total": len(page_elements),
                "by_type": {}
            }

            for element in page_elements:
                elem_type = element['type']
                if elem_type not in stats_data["elements_per_page"][str(page)]["by_type"]:
                    stats_data["elements_per_page"][str(page)]["by_type"][elem_type] = 0
                stats_data["elements_per_page"][str(page)]["by_type"][elem_type] += 1

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Estadísticas guardadas: {output_path.name}")

    def _print_stats(self, stats: Dict[str, int]):
        """Imprime estadísticas en consola."""
        print("📊 ESTADÍSTICAS POR TIPO DE ELEMENTO:")
        print("-" * 60)

        # Calcular ancho máximo del tipo
        max_type_len = max(len(t) for t in stats.keys()) if stats else 0

        for element_type, count in stats.items():
            # Barra visual
            bar_length = min(count, 50)
            bar = "█" * bar_length

            print(f"   {element_type:<{max_type_len}} │ {count:>3} │ {bar}")

        print("-" * 60)
        print(f"   {'TOTAL':<{max_type_len}} │ {sum(stats.values()):>3} │")
        print("="*80)


def main():
    """Función principal."""

    # Configuración
    pdf_path = Path("../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
    output_dir = Path("../outputs")

    # Capítulo 1: páginas 1-11
    CHAPTER_CONFIG = {
        "name": "Capítulo 1 - Descripción de la Perturbación",
        "start_page": 1,
        "end_page": 11
    }

    # Crear extractor
    extractor = DoclingLayoutExtractor(pdf_path)

    # Extraer layout
    elements, stats = extractor.extract_chapter_layout(
        start_page=CHAPTER_CONFIG["start_page"],
        end_page=CHAPTER_CONFIG["end_page"],
        output_dir=output_dir,
        chapter_name=CHAPTER_CONFIG["name"]
    )

    print("\n🎉 ¡Proceso completado exitosamente!")
    print(f"\n📁 Revisa los archivos en: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
