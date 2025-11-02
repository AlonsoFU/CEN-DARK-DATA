"""
Procesador de Tablas Basado en Coordenadas PDF
Usa las coordenadas nativas del PDF para detectar correctamente los límites de celdas
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
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    row: int
    col: int
    font_size: float = 0.0
    font_name: str = ""
    is_bold: bool = False


class CoordinateBasedTableProcessor:
    """Procesador de tablas usando coordenadas nativas del PDF."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_doc = fitz.open(pdf_path)

    def extract_table_from_page(
        self,
        page_num: int,
        y_start: float = None,
        y_end: float = None,
        column_positions: List[float] = None
    ) -> Dict:
        """
        Extrae una tabla de una página usando coordenadas.

        Args:
            page_num: Número de página (1-indexed)
            y_start: Coordenada Y inicial de la tabla (opcional)
            y_end: Coordenada Y final de la tabla (opcional)
            column_positions: Posiciones X de las columnas (opcional)
        """
        page = self.pdf_doc[page_num - 1]

        # Extraer texto con coordenadas
        text_dict = page.get_text("dict")

        # Procesar bloques de texto
        all_text_items = self._extract_text_items_with_coords(text_dict["blocks"])

        # Filtrar por rango Y si se proporciona
        if y_start is not None and y_end is not None:
            all_text_items = [
                item for item in all_text_items
                if y_start <= item["y"] <= y_end
            ]

        # Detectar columnas automáticamente si no se proporcionan
        if column_positions is None:
            column_positions = self._detect_column_positions(all_text_items)

        # Detectar filas automáticamente
        rows = self._detect_rows(all_text_items)

        # Construir tabla
        table_data = self._build_table_from_coordinates(
            all_text_items,
            rows,
            column_positions
        )

        return {
            "table_data": table_data,
            "column_positions": column_positions,
            "rows": rows,
            "page_number": page_num,
            "extraction_method": "coordinate_based"
        }

    def _extract_text_items_with_coords(self, blocks: List) -> List[Dict]:
        """Extrae todos los items de texto con sus coordenadas."""
        text_items = []

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    # Extraer información detallada del span
                    bbox = span["bbox"]
                    text_items.append({
                        "text": span["text"].strip(),
                        "x": bbox[0],
                        "y": bbox[1],
                        "x_end": bbox[2],
                        "y_end": bbox[3],
                        "bbox": bbox,
                        "font": span["font"],
                        "size": span["size"],
                        "flags": span["flags"],
                        "is_bold": bool(span["flags"] & 2**4)  # Flag de bold
                    })

        return [item for item in text_items if item["text"]]  # Filtrar vacíos

    def _detect_column_positions(self, text_items: List[Dict]) -> List[float]:
        """
        Detecta las posiciones X de las columnas basándose en los elementos de texto.

        Agrupa elementos por posición X similar.
        """
        if not text_items:
            return []

        # Recopilar todas las posiciones X de inicio
        x_positions = [item["x"] for item in text_items]

        # Agrupar posiciones X similares (tolerancia de 5 píxeles)
        column_positions = []
        tolerance = 5.0

        for x in sorted(set(x_positions)):
            # Verificar si esta posición es nueva o cerca de una existente
            is_new_column = True
            for col_x in column_positions:
                if abs(x - col_x) <= tolerance:
                    is_new_column = False
                    break

            if is_new_column:
                column_positions.append(x)

        return sorted(column_positions)

    def _detect_rows(self, text_items: List[Dict]) -> List[float]:
        """
        Detecta las posiciones Y de las filas basándose en los elementos de texto.
        """
        if not text_items:
            return []

        # Recopilar todas las posiciones Y
        y_positions = [item["y"] for item in text_items]

        # Agrupar posiciones Y similares (tolerancia de 3 píxeles)
        row_positions = []
        tolerance = 3.0

        for y in sorted(set(y_positions)):
            is_new_row = True
            for row_y in row_positions:
                if abs(y - row_y) <= tolerance:
                    is_new_row = False
                    break

            if is_new_row:
                row_positions.append(y)

        return sorted(row_positions)

    def _build_table_from_coordinates(
        self,
        text_items: List[Dict],
        rows: List[float],
        columns: List[float]
    ) -> List[List[str]]:
        """
        Construye la tabla asignando cada elemento de texto a su celda correspondiente.
        """
        # Crear matriz vacía
        table = [[" " for _ in range(len(columns))] for _ in range(len(rows))]

        # Asignar cada elemento de texto a su celda
        for item in text_items:
            # Encontrar fila (índice de la posición Y más cercana)
            row_idx = self._find_closest_index(item["y"], rows, tolerance=3.0)

            # Encontrar columna (índice de la posición X más cercana)
            col_idx = self._find_closest_index(item["x"], columns, tolerance=5.0)

            if row_idx is not None and col_idx is not None:
                # Si la celda ya tiene contenido, concatenar
                current_content = table[row_idx][col_idx]
                if current_content.strip():
                    table[row_idx][col_idx] = current_content + " " + item["text"]
                else:
                    table[row_idx][col_idx] = item["text"]

        return table

    def _find_closest_index(self, value: float, positions: List[float], tolerance: float = 5.0) -> Optional[int]:
        """Encuentra el índice de la posición más cercana dentro de la tolerancia."""
        for i, pos in enumerate(positions):
            if abs(value - pos) <= tolerance:
                return i
        return None

    def extract_page_1_tables(self) -> Dict:
        """
        Extrae las 3 tablas de la página 1 con detección automática de columnas.
        """
        page_num = 1
        page = self.pdf_doc[page_num - 1]
        page_height = page.rect.height

        # Extraer todo el texto con coordenadas
        text_dict = page.get_text("dict")
        all_items = self._extract_text_items_with_coords(text_dict["blocks"])

        # TABLA 1: Fecha y Hora de la falla (parte superior de la página)
        print("🔍 Detectando Tabla 1: Fecha y Hora de la falla...")
        table_1 = self._extract_specific_table(
            all_items,
            title_pattern="Fecha y Hora",
            y_start=80,
            y_end=250
        )

        # TABLA 2: Identificación instalación afectada (medio de la página)
        print("🔍 Detectando Tabla 2: Identificación instalación afectada...")
        table_2 = self._extract_specific_table(
            all_items,
            title_pattern="Identificación instalación",
            y_start=250,
            y_end=450
        )

        # TABLA 3: Identificación de la empresa (parte inferior)
        print("🔍 Detectando Tabla 3: Identificación de la empresa...")
        table_3 = self._extract_specific_table(
            all_items,
            title_pattern="Identificación de la empresa",
            y_start=450,
            y_end=page_height
        )

        return {
            "page_1_tables": {
                "table_1": table_1,
                "table_2": table_2,
                "table_3": table_3
            },
            "extraction_metadata": {
                "page_number": 1,
                "extraction_method": "coordinate_based",
                "timestamp": datetime.now().isoformat()
            }
        }

    def _extract_specific_table(
        self,
        all_items: List[Dict],
        title_pattern: str,
        y_start: float,
        y_end: float
    ) -> Dict:
        """Extrae una tabla específica basándose en rango Y."""

        # Filtrar items dentro del rango Y
        table_items = [
            item for item in all_items
            if y_start <= item["y"] <= y_end
        ]

        if not table_items:
            return {"error": "No se encontraron items en el rango especificado"}

        # Detectar columnas y filas
        columns = self._detect_column_positions(table_items)
        rows = self._detect_rows(table_items)

        # Construir tabla
        table_data = self._build_table_from_coordinates(table_items, rows, columns)

        # Identificar título
        title = self._find_title(table_items, title_pattern)

        # Convertir a formato estructurado
        structured_table = self._convert_to_key_value_format(table_data, title)

        return {
            "title": title,
            "raw_table": table_data,
            "structured_data": structured_table,
            "metadata": {
                "rows": len(rows),
                "columns": len(columns),
                "y_range": [y_start, y_end],
                "column_positions": columns
            }
        }

    def _find_title(self, items: List[Dict], pattern: str) -> str:
        """Encuentra el título de la tabla."""
        for item in items:
            if pattern.lower() in item["text"].lower():
                return item["text"]
        return "Título no encontrado"

    def _convert_to_key_value_format(self, table_data: List[List[str]], title: str) -> List[Dict]:
        """Convierte la tabla en formato clave-valor estructurado."""
        structured = []

        for row_idx, row in enumerate(table_data):
            if len(row) >= 2:
                # Asumiendo formato: Columna 1 = Campo, Columna 2 = Valor
                campo = row[0].strip()
                valor = row[1].strip() if len(row) > 1 else ""

                # Filtrar filas vacías o de encabezado
                if campo and campo.lower() not in ["campo", "valor", title.lower()]:
                    structured.append({
                        "row_id": row_idx + 1,
                        "campo": campo,
                        "valor": valor
                    })

        return structured


def main():
    """Demo del procesador de tablas basado en coordenadas."""
    print("📊 PROCESADOR DE TABLAS BASADO EN COORDENADAS PDF")
    print("=" * 70)

    # Ruta al PDF
    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print(f"📄 Procesando: {pdf_path.name}")
    print()

    # Crear procesador
    processor = CoordinateBasedTableProcessor(str(pdf_path))

    # Extraer tablas de página 1
    result = processor.extract_page_1_tables()

    # Mostrar resultados
    print("\n✅ EXTRACCIÓN COMPLETADA")
    print("=" * 70)

    for table_name, table_data in result["page_1_tables"].items():
        print(f"\n📊 {table_name.upper().replace('_', ' ')}")
        print("-" * 70)

        if "error" in table_data:
            print(f"❌ Error: {table_data['error']}")
            continue

        print(f"📌 Título: {table_data['title']}")
        print(f"📐 Dimensiones: {table_data['metadata']['rows']} filas x {table_data['metadata']['columns']} columnas")
        print(f"📍 Posiciones columnas: {[f'{x:.1f}' for x in table_data['metadata']['column_positions']]}")
        print()

        # Mostrar datos estructurados
        print("📋 Datos estructurados:")
        for item in table_data['structured_data'][:5]:  # Mostrar primeras 5 filas
            print(f"  {item['row_id']}. {item['campo']}: {item['valor']}")

        if len(table_data['structured_data']) > 5:
            print(f"  ... ({len(table_data['structured_data']) - 5} filas más)")

    # Guardar resultado
    output_dir = Path(__file__).parent.parent / "outputs" / "raw_extractions"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "capitulo_01_coordinate_based.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resultado guardado en: {output_file}")
    print()
    print("=" * 70)
    print("✅ PROCESAMIENTO COMPLETADO")


if __name__ == "__main__":
    main()