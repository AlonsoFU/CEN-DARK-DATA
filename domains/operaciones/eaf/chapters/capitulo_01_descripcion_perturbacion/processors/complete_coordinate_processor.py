"""
Procesador Completo Basado en Coordenadas
Extrae todas las páginas del Capítulo 1 usando coordenadas PDF nativas
"""

import json
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class TableCell:
    """Representa una celda de tabla con sus coordenadas."""
    text: str
    bbox: Tuple[float, float, float, float]
    row: int
    col: int


class CompleteCoordinateProcessor:
    """Procesador completo usando coordenadas para todas las páginas."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_doc = fitz.open(pdf_path)
        self.entity_counter = 0

    def process_all_pages(self, start_page: int = 1, end_page: int = 11) -> Dict:
        """
        Procesa todas las páginas del capítulo 1.

        Args:
            start_page: Página inicial (default: 1)
            end_page: Página final (default: 11)
        """
        print(f"📄 Procesando páginas {start_page} a {end_page} del Capítulo 1")
        print("=" * 70)

        result = {
            "document_metadata": {
                "eaf_number": "089/2025",
                "document_title": "Estudio para análisis de falla EAF 089/2025",
                "incident_description": "Desconexión forzada línea 2x500 kV Nueva Maitencillo - Nueva Pan de Azúcar",
                "emission_date": "18-03-2025"
            },
            "chapter": {
                "chapter_id": "eaf_089_2025_cap_01",
                "number": 1,
                "title": "Descripción pormenorizada de la perturbación",
                "content_type": "description",
                "page_range": f"{start_page}-{end_page}",
                "processing_timestamp": datetime.now().isoformat()
            },
            "entities": [],
            "pages": {},
            "extraction_summary": {
                "total_pages": 0,
                "total_tables": 0,
                "total_paragraphs": 0,
                "extraction_method": "coordinate_based"
            }
        }

        # Procesar cada página
        for page_num in range(start_page, end_page + 1):
            print(f"\n📄 Procesando página {page_num}...")

            page_data = self._process_single_page(page_num)

            # Agregar entidades de la página
            result["entities"].extend(page_data["entities"])

            # Agregar información de página
            result["pages"][page_num] = {
                "page_number": page_num,
                "tables_count": page_data["tables_count"],
                "text_blocks_count": page_data["text_blocks_count"],
                "processing_status": "completed"
            }

            # Actualizar resumen
            result["extraction_summary"]["total_pages"] += 1
            result["extraction_summary"]["total_tables"] += page_data["tables_count"]
            result["extraction_summary"]["total_paragraphs"] += page_data["text_blocks_count"]

            print(f"   ✅ Página {page_num}: {page_data['tables_count']} tablas, {page_data['text_blocks_count']} bloques de texto")

        print(f"\n✅ Procesamiento completado: {result['extraction_summary']['total_tables']} tablas extraídas")
        return result

    def _process_single_page(self, page_num: int) -> Dict:
        """Procesa una página individual."""
        page = self.pdf_doc[page_num - 1]

        # Extraer texto con coordenadas
        text_dict = page.get_text("dict")

        # Extraer items de texto
        all_items = self._extract_text_items_with_coords(text_dict["blocks"])

        # Detectar estructuras
        tables = self._detect_tables_in_page(all_items, page_num)
        text_blocks = self._extract_text_blocks(all_items, page_num)

        # Crear entidades
        entities = []

        # Agregar tablas como entidades
        for table_idx, table in enumerate(tables):
            self.entity_counter += 1
            entity = self._create_table_entity(table, page_num, self.entity_counter)
            entities.append(entity)

        # Agregar bloques de texto como entidades
        for block_idx, block in enumerate(text_blocks):
            self.entity_counter += 1
            entity = self._create_text_entity(block, page_num, self.entity_counter)
            entities.append(entity)

        return {
            "entities": entities,
            "tables_count": len(tables),
            "text_blocks_count": len(text_blocks)
        }

    def _extract_text_items_with_coords(self, blocks: List) -> List[Dict]:
        """Extrae todos los items de texto con sus coordenadas."""
        text_items = []

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    bbox = span["bbox"]
                    text = span["text"].strip()

                    if text:  # Solo agregar si tiene texto
                        text_items.append({
                            "text": text,
                            "x": bbox[0],
                            "y": bbox[1],
                            "x_end": bbox[2],
                            "y_end": bbox[3],
                            "bbox": bbox,
                            "font": span["font"],
                            "size": span["size"],
                            "flags": span["flags"],
                            "is_bold": bool(span["flags"] & 2**4)
                        })

        return text_items

    def _detect_tables_in_page(self, text_items: List[Dict], page_num: int) -> List[Dict]:
        """Detecta tablas en la página usando coordenadas."""

        # Agrupar items por filas
        rows = self._group_items_by_rows(text_items)

        tables = []

        # Buscar patrones tabulares
        i = 0
        while i < len(rows):
            # Verificar si hay al menos 3 filas consecutivas con estructura similar
            if i + 2 < len(rows):
                row1, row2, row3 = rows[i], rows[i+1], rows[i+2]

                # Detectar columnas en estas filas
                columns = self._detect_column_positions([row1, row2, row3])

                if len(columns) >= 2:  # Al menos 2 columnas = posible tabla
                    # Encontrar el final de la tabla
                    table_end = i + 3
                    while table_end < len(rows):
                        next_row = rows[table_end]
                        if self._row_fits_table_pattern(next_row, columns):
                            table_end += 1
                        else:
                            break

                    # Extraer la tabla
                    table_rows = rows[i:table_end]
                    table_data = self._build_table_from_rows(table_rows, columns)

                    # Crear objeto tabla
                    table = {
                        "start_row": i,
                        "end_row": table_end,
                        "columns": columns,
                        "data": table_data,
                        "title": self._find_table_title(table_rows)
                    }
                    tables.append(table)

                    i = table_end
                else:
                    i += 1
            else:
                i += 1

        return tables

    def _group_items_by_rows(self, text_items: List[Dict]) -> List[List[Dict]]:
        """Agrupa items de texto por filas (posición Y similar)."""
        if not text_items:
            return []

        # Ordenar por posición Y
        sorted_items = sorted(text_items, key=lambda x: x["y"])

        rows = []
        current_row = [sorted_items[0]]
        current_y = sorted_items[0]["y"]

        tolerance = 3.0  # Píxeles de tolerancia

        for item in sorted_items[1:]:
            if abs(item["y"] - current_y) <= tolerance:
                current_row.append(item)
            else:
                # Ordenar fila por posición X
                current_row.sort(key=lambda x: x["x"])
                rows.append(current_row)
                current_row = [item]
                current_y = item["y"]

        # Agregar última fila
        if current_row:
            current_row.sort(key=lambda x: x["x"])
            rows.append(current_row)

        return rows

    def _detect_column_positions(self, rows: List[List[Dict]]) -> List[float]:
        """Detecta posiciones de columnas basándose en múltiples filas."""
        all_x_positions = []

        for row in rows:
            for item in row:
                all_x_positions.append(item["x"])

        # Agrupar posiciones X similares
        columns = []
        tolerance = 5.0

        for x in sorted(set(all_x_positions)):
            is_new_column = True
            for col_x in columns:
                if abs(x - col_x) <= tolerance:
                    is_new_column = False
                    break

            if is_new_column:
                columns.append(x)

        return sorted(columns)

    def _row_fits_table_pattern(self, row: List[Dict], columns: List[float]) -> bool:
        """Verifica si una fila encaja con el patrón de columnas de la tabla."""
        tolerance = 10.0

        for item in row:
            # Verificar si la posición X del item está cerca de alguna columna
            matches_column = False
            for col_x in columns:
                if abs(item["x"] - col_x) <= tolerance:
                    matches_column = True
                    break

            if not matches_column:
                return False

        return True

    def _build_table_from_rows(self, rows: List[List[Dict]], columns: List[float]) -> List[List[str]]:
        """Construye tabla asignando items a celdas basándose en columnas."""
        table_data = []

        for row in rows:
            row_data = [""] * len(columns)

            for item in row:
                # Encontrar columna más cercana
                col_idx = self._find_closest_column(item["x"], columns)
                if col_idx is not None:
                    if row_data[col_idx]:
                        row_data[col_idx] += " " + item["text"]
                    else:
                        row_data[col_idx] = item["text"]

            table_data.append(row_data)

        return table_data

    def _find_closest_column(self, x: float, columns: List[float], tolerance: float = 10.0) -> Optional[int]:
        """Encuentra el índice de la columna más cercana."""
        for i, col_x in enumerate(columns):
            if abs(x - col_x) <= tolerance:
                return i
        return None

    def _find_table_title(self, rows: List[List[Dict]]) -> str:
        """Intenta encontrar el título de la tabla."""
        if not rows:
            return "Tabla sin título"

        # Buscar en las primeras filas
        for row in rows[:3]:
            for item in row:
                text = item["text"].lower()
                # Buscar patrones de título
                if any(pattern in text for pattern in ["a.", "b.", "c.", "d.", "tabla", "cuadro"]):
                    return item["text"]

        return "Tabla sin título"

    def _extract_text_blocks(self, text_items: List[Dict], page_num: int) -> List[Dict]:
        """Extrae bloques de texto que no son tablas."""
        # Por ahora, agrupar texto que no esté en tablas
        # Esto es una simplificación - se puede mejorar

        rows = self._group_items_by_rows(text_items)
        text_blocks = []

        for row in rows:
            # Si la fila tiene pocos elementos y mucho texto, probablemente es párrafo
            if len(row) <= 2:
                text = " ".join([item["text"] for item in row])
                if len(text) > 20:  # Mínimo 20 caracteres
                    text_blocks.append({
                        "text": text,
                        "bbox": self._calculate_bbox(row)
                    })

        return text_blocks

    def _calculate_bbox(self, items: List[Dict]) -> Tuple[float, float, float, float]:
        """Calcula bounding box de un conjunto de items."""
        if not items:
            return (0, 0, 0, 0)

        x0 = min(item["x"] for item in items)
        y0 = min(item["y"] for item in items)
        x1 = max(item["x_end"] for item in items)
        y1 = max(item["y_end"] for item in items)

        return (x0, y0, x1, y1)

    def _create_table_entity(self, table: Dict, page_num: int, entity_id: int) -> Dict:
        """Crea una entidad de tabla."""
        # Convertir a formato clave-valor
        structured_rows = self._convert_table_to_key_value(table["data"])

        return {
            "id": f"eaf_089_2025_ch01_table_{entity_id:04d}",
            "type": "structured_table",
            "category": "data_structure",
            "properties": {
                "table_metadata": {
                    "title": table["title"],
                    "format": "key_value_pairs",
                    "row_count": len(structured_rows),
                    "column_count": len(table["columns"])
                },
                "table_structure": {
                    "headers": ["Campo", "Valor"],
                    "rows": structured_rows,
                    "row_count": len(structured_rows),
                    "column_count": 2
                }
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": 0.90,
            "original_data": {
                "extraction_method": "coordinate_based",
                "column_positions": table["columns"]
            }
        }

    def _convert_table_to_key_value(self, table_data: List[List[str]]) -> List[Dict]:
        """Convierte tabla a formato clave-valor."""
        structured = []
        row_id = 1

        for row in table_data:
            # Limpiar celdas
            cleaned_row = [cell.strip() for cell in row]

            # Buscar campo y valor
            campo = None
            valor = None

            # Si hay al menos 2 columnas con contenido
            non_empty = [cell for cell in cleaned_row if cell]
            if len(non_empty) >= 2:
                campo = non_empty[0]
                valor = " ".join(non_empty[1:])
            elif len(non_empty) == 1:
                # Solo un valor, podría ser continuación
                continue

            # Filtrar encabezados y marcadores
            if campo and valor:
                if campo.lower() not in ["campo", "valor"] and len(campo) > 1:
                    structured.append({
                        "row_id": row_id,
                        "campo": campo,
                        "valor": valor
                    })
                    row_id += 1

        return structured

    def _create_text_entity(self, text_block: Dict, page_num: int, entity_id: int) -> Dict:
        """Crea una entidad de texto."""
        return {
            "id": f"eaf_089_2025_ch01_text_{entity_id:04d}",
            "type": "text_block",
            "category": "narrative",
            "properties": {
                "text": text_block["text"],
                "bbox": text_block["bbox"],
                "char_count": len(text_block["text"])
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": 0.85,
            "original_data": {
                "extraction_method": "coordinate_based"
            }
        }


def main():
    """Ejecuta el procesador completo."""
    print("🚀 PROCESADOR COMPLETO BASADO EN COORDENADAS")
    print("=" * 70)

    # Ruta al PDF
    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print(f"📄 Archivo: {pdf_path.name}")
    print()

    # Crear procesador
    processor = CompleteCoordinateProcessor(str(pdf_path))

    # Procesar todas las páginas
    result = processor.process_all_pages(start_page=1, end_page=11)

    # Mostrar resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE EXTRACCIÓN")
    print("=" * 70)
    print(f"📄 Páginas procesadas: {result['extraction_summary']['total_pages']}")
    print(f"📊 Tablas extraídas: {result['extraction_summary']['total_tables']}")
    print(f"📝 Bloques de texto: {result['extraction_summary']['total_paragraphs']}")
    print(f"🎯 Total entidades: {len(result['entities'])}")

    # Mostrar desglose por página
    print(f"\n📄 Desglose por página:")
    for page_num, page_info in sorted(result["pages"].items()):
        print(f"   Página {page_num}: {page_info['tables_count']} tablas, {page_info['text_blocks_count']} textos")

    # Guardar resultado
    output_dir = Path(__file__).parent.parent / "outputs" / "universal_json"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "capitulo_01_complete_coordinate_based.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resultado guardado en:")
    print(f"   {output_file}")

    print("\n" + "=" * 70)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()