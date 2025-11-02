"""
Procesador Híbrido de Granularidad Optimizado
- Tablas: Granularidad fina (campo-valor preciso)
- Texto: Párrafos completos agrupados (contexto para AI)
"""

import json
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class HybridGranularityProcessor:
    """
    Procesador que combina lo mejor de ambos mundos:
    - Tablas con granularidad fina para búsquedas precisas
    - Párrafos completos para comprensión contextual
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_doc = fitz.open(pdf_path)
        self.entity_counter = 0

    def process_all_pages(self, start_page: int = 1, end_page: int = 11) -> Dict:
        """Procesa todas las páginas con granularidad híbrida."""
        print(f"📄 Procesando páginas {start_page} a {end_page} con GRANULARIDAD HÍBRIDA")
        print("=" * 70)
        print("📊 Tablas: Granularidad fina (campo-valor)")
        print("📝 Texto: Párrafos completos agrupados")
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
                "processing_timestamp": datetime.now().isoformat(),
                "granularity_strategy": "hybrid"
            },
            "entities": [],
            "pages": {},
            "extraction_summary": {
                "total_pages": 0,
                "total_tables": 0,
                "total_paragraphs": 0,
                "granularity": {
                    "tables": "fine",
                    "text": "paragraph"
                },
                "extraction_method": "coordinate_based_hybrid"
            }
        }

        # Procesar cada página
        for page_num in range(start_page, end_page + 1):
            print(f"\n📄 Página {page_num}...", end=" ")

            page_data = self._process_single_page(page_num)

            result["entities"].extend(page_data["entities"])

            result["pages"][page_num] = {
                "page_number": page_num,
                "tables_count": page_data["tables_count"],
                "paragraphs_count": page_data["paragraphs_count"],
                "processing_status": "completed"
            }

            result["extraction_summary"]["total_pages"] += 1
            result["extraction_summary"]["total_tables"] += page_data["tables_count"]
            result["extraction_summary"]["total_paragraphs"] += page_data["paragraphs_count"]

            print(f"✅ {page_data['tables_count']} tablas, {page_data['paragraphs_count']} párrafos")

        print(f"\n{'=' * 70}")
        print(f"✅ COMPLETADO: {result['extraction_summary']['total_tables']} tablas + {result['extraction_summary']['total_paragraphs']} párrafos")
        return result

    def _process_single_page(self, page_num: int) -> Dict:
        """Procesa una página con estrategia híbrida."""
        page = self.pdf_doc[page_num - 1]
        text_dict = page.get_text("dict")

        all_items = self._extract_text_items_with_coords(text_dict["blocks"])
        rows = self._group_items_by_rows(all_items)

        # PASO 1: Detectar tablas (granularidad fina)
        tables = self._detect_tables_smart(rows, page_num)

        # PASO 2: Identificar qué filas pertenecen a tablas
        table_row_indices = set()
        for table in tables:
            table_row_indices.update(range(table["start_row"], table["end_row"]))

        # PASO 3: Extraer párrafos de filas NO tabulares
        non_table_rows = [rows[i] for i in range(len(rows)) if i not in table_row_indices]
        paragraphs = self._group_rows_into_paragraphs(non_table_rows, page_num)

        # PASO 4: Crear entidades
        entities = []

        # Agregar tablas
        for table in tables:
            self.entity_counter += 1
            entity = self._create_table_entity(table, page_num, self.entity_counter)
            entities.append(entity)

        # Agregar párrafos
        for paragraph in paragraphs:
            self.entity_counter += 1
            entity = self._create_paragraph_entity(paragraph, page_num, self.entity_counter)
            entities.append(entity)

        return {
            "entities": entities,
            "tables_count": len(tables),
            "paragraphs_count": len(paragraphs)
        }

    def _extract_text_items_with_coords(self, blocks: List) -> List[Dict]:
        """Extrae items de texto con coordenadas."""
        text_items = []

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    bbox = span["bbox"]
                    text = span["text"].strip()

                    if text:
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

    def _group_items_by_rows(self, text_items: List[Dict]) -> List[List[Dict]]:
        """Agrupa items por filas (posición Y similar)."""
        if not text_items:
            return []

        sorted_items = sorted(text_items, key=lambda x: x["y"])
        rows = []
        current_row = [sorted_items[0]]
        current_y = sorted_items[0]["y"]
        tolerance = 3.0

        for item in sorted_items[1:]:
            if abs(item["y"] - current_y) <= tolerance:
                current_row.append(item)
            else:
                current_row.sort(key=lambda x: x["x"])
                rows.append(current_row)
                current_row = [item]
                current_y = item["y"]

        if current_row:
            current_row.sort(key=lambda x: x["x"])
            rows.append(current_row)

        return rows

    def _detect_tables_smart(self, rows: List[List[Dict]], page_num: int) -> List[Dict]:
        """
        Detecta tablas de forma inteligente:
        - Mínimo 2 columnas
        - Al menos 3 filas consecutivas con estructura similar
        """
        tables = []
        i = 0

        while i < len(rows):
            # Buscar inicio de tabla
            if i + 2 < len(rows):
                # Analizar 3 filas consecutivas
                sample_rows = rows[i:i+3]
                columns = self._detect_column_positions(sample_rows)

                # Si hay al menos 2 columnas, podría ser tabla
                if len(columns) >= 2:
                    # Encontrar final de la tabla
                    table_end = i + 3

                    # Extender mientras las filas sigan el patrón
                    while table_end < len(rows):
                        if self._row_fits_table_pattern(rows[table_end], columns):
                            table_end += 1
                        else:
                            break

                    # Crear tabla
                    table_rows = rows[i:table_end]
                    table_data = self._build_table_from_rows(table_rows, columns)

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

    def _detect_column_positions(self, rows: List[List[Dict]]) -> List[float]:
        """Detecta posiciones X de columnas."""
        all_x_positions = []
        for row in rows:
            for item in row:
                all_x_positions.append(item["x"])

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
        """Verifica si una fila sigue el patrón de columnas."""
        tolerance = 10.0

        # La fila debe tener items alineados con las columnas
        matches = 0
        for item in row:
            for col_x in columns:
                if abs(item["x"] - col_x) <= tolerance:
                    matches += 1
                    break

        # Al menos 50% de items deben coincidir con columnas
        return matches >= len(row) * 0.5 if row else False

    def _build_table_from_rows(self, rows: List[List[Dict]], columns: List[float]) -> List[List[str]]:
        """Construye tabla asignando items a celdas."""
        table_data = []

        for row in rows:
            row_data = [""] * len(columns)

            for item in row:
                col_idx = self._find_closest_column(item["x"], columns)
                if col_idx is not None:
                    if row_data[col_idx]:
                        row_data[col_idx] += " " + item["text"]
                    else:
                        row_data[col_idx] = item["text"]

            table_data.append(row_data)

        return table_data

    def _find_closest_column(self, x: float, columns: List[float], tolerance: float = 10.0) -> Optional[int]:
        """Encuentra columna más cercana."""
        for i, col_x in enumerate(columns):
            if abs(x - col_x) <= tolerance:
                return i
        return None

    def _find_table_title(self, rows: List[List[Dict]]) -> str:
        """Busca título de tabla."""
        for row in rows[:3]:
            for item in row:
                text = item["text"].lower()
                if any(p in text for p in ["a.", "b.", "c.", "d.", "tabla", "cuadro"]):
                    return item["text"]
        return "Tabla sin título"

    def _group_rows_into_paragraphs(self, rows: List[List[Dict]], page_num: int) -> List[Dict]:
        """
        Agrupa filas en párrafos completos.

        Criterios de agrupación:
        1. Margen izquierdo similar (±10px)
        2. Distancia vertical pequeña (< 15px entre líneas)
        3. No son líneas muy cortas (> 30 caracteres acumulados)
        """
        paragraphs = []
        current_para_rows = []
        prev_x = None
        prev_y_end = None

        for row in rows:
            if not row:
                continue

            # Características de la fila
            row_x = min(item["x"] for item in row)
            row_y = min(item["y"] for item in row)
            row_y_end = max(item["y_end"] for item in row)
            row_text = " ".join(item["text"] for item in row)

            # Filtrar líneas muy cortas o marcadores
            if len(row_text) < 10 or row_text.strip() in ["a.", "b.", "c.", "d.", "1.", "2.", "3.", "4."]:
                # Si hay párrafo acumulado, finalizarlo
                if current_para_rows:
                    para = self._finalize_paragraph(current_para_rows)
                    if para:
                        paragraphs.append(para)
                    current_para_rows = []
                prev_x = None
                prev_y_end = None
                continue

            # Decidir si agregar a párrafo actual
            should_group = False

            if current_para_rows and prev_x is not None and prev_y_end is not None:
                x_diff = abs(row_x - prev_x)
                y_gap = row_y - prev_y_end

                # Agrupar si: mismo margen (±10px) y gap pequeño (< 15px)
                if x_diff <= 10 and 0 <= y_gap < 15:
                    should_group = True

            if should_group:
                current_para_rows.append(row)
            else:
                # Finalizar párrafo actual
                if current_para_rows:
                    para = self._finalize_paragraph(current_para_rows)
                    if para:
                        paragraphs.append(para)

                # Iniciar nuevo párrafo
                current_para_rows = [row]

            prev_x = row_x
            prev_y_end = row_y_end

        # Finalizar último párrafo
        if current_para_rows:
            para = self._finalize_paragraph(current_para_rows)
            if para:
                paragraphs.append(para)

        return paragraphs

    def _finalize_paragraph(self, rows: List[List[Dict]]) -> Optional[Dict]:
        """Crea un párrafo a partir de filas acumuladas."""
        if not rows:
            return None

        # Concatenar todo el texto
        all_items = []
        texts = []

        for row in rows:
            row_text = " ".join(item["text"] for item in row)
            texts.append(row_text)
            all_items.extend(row)

        full_text = " ".join(texts)

        # Filtrar párrafos muy cortos
        if len(full_text) < 50:  # Mínimo 50 caracteres
            return None

        # Calcular bounding box completo
        bbox = self._calculate_bbox(all_items)

        return {
            "text": full_text,
            "bbox": bbox,
            "line_count": len(rows),
            "char_count": len(full_text)
        }

    def _calculate_bbox(self, items: List[Dict]) -> Tuple[float, float, float, float]:
        """Calcula bounding box."""
        if not items:
            return (0, 0, 0, 0)

        x0 = min(item["x"] for item in items)
        y0 = min(item["y"] for item in items)
        x1 = max(item["x_end"] for item in items)
        y1 = max(item["y_end"] for item in items)

        return (x0, y0, x1, y1)

    def _create_table_entity(self, table: Dict, page_num: int, entity_id: int) -> Dict:
        """Crea entidad de tabla con granularidad fina."""
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
                    "column_count": len(table["columns"]),
                    "granularity": "fine"
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
                "extraction_method": "coordinate_based_hybrid",
                "granularity": "fine"
            }
        }

    def _convert_table_to_key_value(self, table_data: List[List[str]]) -> List[Dict]:
        """Convierte tabla a formato clave-valor."""
        structured = []
        row_id = 1

        for row in table_data:
            cleaned = [cell.strip() for cell in row]
            non_empty = [c for c in cleaned if c]

            if len(non_empty) >= 2:
                campo = non_empty[0]
                valor = " ".join(non_empty[1:])

                if campo.lower() not in ["campo", "valor"] and len(campo) > 1:
                    structured.append({
                        "row_id": row_id,
                        "campo": campo,
                        "valor": valor
                    })
                    row_id += 1

        return structured

    def _create_paragraph_entity(self, paragraph: Dict, page_num: int, entity_id: int) -> Dict:
        """Crea entidad de párrafo completo."""
        return {
            "id": f"eaf_089_2025_ch01_paragraph_{entity_id:04d}",
            "type": "paragraph",
            "category": "narrative",
            "properties": {
                "text": paragraph["text"],
                "bbox": paragraph["bbox"],
                "line_count": paragraph["line_count"],
                "char_count": paragraph["char_count"],
                "granularity": "paragraph"
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": 0.90,
            "original_data": {
                "extraction_method": "coordinate_based_hybrid",
                "granularity": "paragraph"
            }
        }


def main():
    """Ejecuta el procesador híbrido."""
    print("🚀 PROCESADOR HÍBRIDO DE GRANULARIDAD")
    print("=" * 70)

    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print(f"📄 Archivo: {pdf_path.name}\n")

    processor = HybridGranularityProcessor(str(pdf_path))
    result = processor.process_all_pages(start_page=1, end_page=11)

    print("\n" + "=" * 70)
    print("📊 RESUMEN DE EXTRACCIÓN HÍBRIDA")
    print("=" * 70)
    print(f"📄 Páginas: {result['extraction_summary']['total_pages']}")
    print(f"📊 Tablas (granularidad fina): {result['extraction_summary']['total_tables']}")
    print(f"📝 Párrafos (completos): {result['extraction_summary']['total_paragraphs']}")
    print(f"🎯 Total entidades: {len(result['entities'])}")

    print(f"\n📄 Desglose por página:")
    for page_num, page_info in sorted(result["pages"].items()):
        print(f"   Pág {page_num}: {page_info['tables_count']} tablas + {page_info['paragraphs_count']} párrafos")

    output_dir = Path(__file__).parent.parent / "outputs" / "universal_json"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "capitulo_01_hybrid_granularity.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resultado guardado en:")
    print(f"   {output_file}")

    print("\n" + "=" * 70)
    print("✅ PROCESAMIENTO HÍBRIDO COMPLETADO")
    print("=" * 70)
    print("\n💡 Ahora tienes:")
    print("   📊 Tablas con granularidad fina (búsquedas precisas)")
    print("   📝 Párrafos completos (contexto para AI)")


if __name__ == "__main__":
    main()