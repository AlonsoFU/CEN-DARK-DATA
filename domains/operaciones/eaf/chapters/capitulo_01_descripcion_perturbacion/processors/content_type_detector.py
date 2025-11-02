"""
Detector Específico de Tipos de Contenido - EAF
Identifica automáticamente: tablas, párrafos, imágenes, fórmulas
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import cv2
import numpy as np

from pdf_coordinate_extractor import PDFCoordinateExtractor


class ContentTypeDetector:
    """Detector especializado para identificar tipos de contenido específicos."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.coordinate_extractor = PDFCoordinateExtractor(pdf_path)

    def analyze_content_types(self, page_num: int) -> Dict:
        """Analiza y clasifica todos los tipos de contenido en una página."""

        # Extraer datos de coordenadas
        coord_data = self.coordinate_extractor.extract_page_with_coordinates(page_num)

        if "error" in coord_data:
            return {"error": coord_data["error"]}

        analysis = {
            "page_number": page_num,
            "content_types": {
                "tables": [],
                "paragraphs": [],
                "images": [],
                "formulas": [],
                "headers": [],
                "lists": []
            },
            "layout_analysis": {
                "column_detection": self._detect_columns(coord_data),
                "reading_order": [],
                "visual_hierarchy": {}
            },
            "formatting_analysis": {}
        }

        # Analizar bloques de texto
        for i, block in enumerate(coord_data.get("blocks", [])):
            if block["block_type"] == "text":
                content_analysis = self._analyze_text_block(block, i)
                content_type = content_analysis["type"]

                if content_type in analysis["content_types"]:
                    analysis["content_types"][content_type].append(content_analysis)

        # Analizar imágenes
        for i, image in enumerate(coord_data.get("images", [])):
            image_analysis = self._analyze_image_block(image, i)
            analysis["content_types"]["images"].append(image_analysis)

        # Detectar tablas por agrupación
        table_regions = self._detect_advanced_tables(coord_data)
        analysis["content_types"]["tables"].extend(table_regions)

        # Analizar orden de lectura
        analysis["layout_analysis"]["reading_order"] = self._determine_reading_order(
            analysis["content_types"]
        )

        return analysis

    def _analyze_text_block(self, block: Dict, block_id: int) -> Dict:
        """Analiza un bloque de texto específico."""

        # Extraer texto completo del bloque
        full_text = self._extract_full_text_from_block(block)

        # Análisis básico
        analysis = {
            "block_id": f"text_{block_id}",
            "bbox": block["bbox"],
            "text": full_text,
            "type": "paragraph",  # Default
            "confidence": 0.0,
            "characteristics": {},
            "formatting": self._extract_detailed_formatting(block),
            "content_metrics": self._calculate_text_metrics(full_text)
        }

        # Determinar tipo específico
        analysis["type"] = self._classify_text_content_type(full_text, block, analysis)
        analysis["confidence"] = self._calculate_type_confidence(analysis)
        analysis["characteristics"] = self._extract_content_characteristics(full_text, analysis["type"])

        return analysis

    def _classify_text_content_type(self, text: str, block: Dict, analysis: Dict) -> str:
        """Clasifica el tipo específico de contenido de texto."""

        text_lower = text.lower().strip()

        # 1. ENCABEZADOS/TÍTULOS
        if self._is_header(text, block, analysis):
            return "headers"

        # 2. FÓRMULAS MATEMÁTICAS/TÉCNICAS
        if self._is_formula(text):
            return "formulas"

        # 3. LISTAS ESTRUCTURADAS
        if self._is_list(text):
            return "lists"

        # 4. CONTENIDO TABULAR (texto que forma parte de tabla)
        if self._is_tabular_text(text, block):
            return "tables"

        # 5. PÁRRAFOS (default)
        return "paragraphs"

    def _is_header(self, text: str, block: Dict, analysis: Dict) -> bool:
        """Detecta si el texto es un encabezado."""

        # Criterios de encabezado
        criteria = {
            "short_text": len(text.split()) <= 10,
            "has_numbering": bool(re.match(r'^\d+\.|\b[a-z]\.\d+', text.lower())),
            "bold_formatting": analysis["formatting"]["styles"].get("bold", False),
            "larger_font": analysis["formatting"]["dominant_style"].get("size", 9) > 10,
            "position_top": block["bbox"][1] < 100,  # Cerca del top de página
            "standalone": text.count('\n') <= 1
        }

        # Si cumple 3+ criterios, es encabezado
        score = sum(criteria.values())
        return score >= 3

    def _is_formula(self, text: str) -> bool:
        """Detecta si el texto contiene fórmulas."""

        formula_patterns = [
            r'[=+\-*/]\s*\d+',          # Operaciones matemáticas
            r'\d+\s*[×·]\s*\d+',        # Multiplicaciones
            r'[A-Z]\s*=\s*[A-Z]',       # Variables tipo P = V × I
            r'cos\(|sin\(|tan\(',       # Funciones trigonométricas
            r'√|∑|∫|∆|π|α|β|γ|φ|θ',    # Símbolos matemáticos
            r'\d+\^\d+',                # Exponentes
            r'\([A-Za-z]+\)',           # Variables entre paréntesis
            r'\d+\s*%',                 # Porcentajes en cálculos
        ]

        return any(re.search(pattern, text) for pattern in formula_patterns)

    def _is_list(self, text: str) -> bool:
        """Detecta si el texto es una lista estructurada."""

        lines = text.split('\n')
        if len(lines) < 2:
            return False

        list_patterns = [
            r'^\s*[-•·]\s+',            # Bullet points
            r'^\s*\d+[\.)]\s+',         # Listas numeradas
            r'^\s*[a-z][\.)]\s+',       # Listas alfabéticas
            r'^\s*[IVX]+[\.)]\s+',      # Números romanos
        ]

        list_items = 0
        for line in lines:
            if any(re.match(pattern, line) for pattern in list_patterns):
                list_items += 1

        # Si más del 60% de las líneas son items de lista
        return list_items / len(lines) > 0.6

    def _is_tabular_text(self, text: str, block: Dict) -> bool:
        """Detecta si el texto forma parte de una estructura tabular."""

        lines = text.split('\n')

        # Criterios tabulares
        tabular_indicators = 0

        for line in lines:
            # Múltiples columnas separadas por espacios
            if len(line.split()) >= 3:
                tabular_indicators += 1

            # Datos numéricos alineados
            if re.search(r'\d+\.\d+|\d+,\d+', line):
                tabular_indicators += 1

            # Patrones de datos técnicos
            if re.search(r'\d+\s*(MW|kV|Hz|A|V)', line, re.IGNORECASE):
                tabular_indicators += 1

        # Verificar alineación espacial del bloque
        bbox = block["bbox"]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

        # Si es más ancho que alto y tiene indicadores tabulares
        if width > height * 2 and tabular_indicators >= 2:
            return True

        return tabular_indicators >= len(lines) * 0.5

    def _analyze_image_block(self, image: Dict, image_id: int) -> Dict:
        """Analiza un bloque de imagen."""

        return {
            "block_id": f"image_{image_id}",
            "type": "images",
            "bbox": [0, 0, image["width"], image["height"]],  # Aproximado
            "characteristics": {
                "width": image["width"],
                "height": image["height"],
                "colorspace": image.get("colorspace", "unknown"),
                "format": "embedded",
                "estimated_type": self._classify_image_type(image)
            },
            "confidence": 0.9,
            "extraction_method": "pdf_native"
        }

    def _classify_image_type(self, image: Dict) -> str:
        """Clasifica el tipo de imagen basándose en características."""

        width = image["width"]
        height = image["height"]
        aspect_ratio = width / height if height > 0 else 1

        # Clasificación por aspecto ratio y tamaño
        if aspect_ratio > 3:
            return "chart_horizontal"
        elif aspect_ratio < 0.5:
            return "chart_vertical"
        elif 0.8 <= aspect_ratio <= 1.2:
            return "diagram_square"
        else:
            return "diagram_rectangular"

    def _detect_advanced_tables(self, coord_data: Dict) -> List[Dict]:
        """Detecta tablas usando análisis avanzado de coordenadas."""

        tables = []
        text_blocks = [b for b in coord_data["blocks"] if b["block_type"] == "text"]

        # Agrupar bloques por filas (posición Y similar)
        rows = self._group_blocks_into_rows(text_blocks)

        # Detectar patrones de tabla
        table_candidates = self._find_table_patterns(rows)

        for i, candidate in enumerate(table_candidates):
            table_analysis = {
                "block_id": f"advanced_table_{i}",
                "type": "tables",
                "bbox": candidate["bbox"],
                "characteristics": {
                    "rows": candidate["rows"],
                    "columns": candidate["columns"],
                    "has_header": candidate["has_header"],
                    "data_type": candidate["data_type"],
                    "alignment": candidate["alignment"]
                },
                "confidence": candidate["confidence"],
                "detection_method": "advanced_coordinate_analysis"
            }
            tables.append(table_analysis)

        return tables

    def _group_blocks_into_rows(self, text_blocks: List[Dict]) -> List[List[Dict]]:
        """Agrupa bloques de texto en filas basándose en posición Y."""

        # Extraer información de posición de cada bloque
        block_positions = []
        for block in text_blocks:
            bbox = block["bbox"]
            y_center = (bbox[1] + bbox[3]) / 2
            block_positions.append({
                "block": block,
                "y_center": y_center,
                "x_start": bbox[0],
                "x_end": bbox[2]
            })

        # Ordenar por posición Y
        block_positions.sort(key=lambda x: x["y_center"])

        # Agrupar en filas (tolerancia de 5 píxeles)
        rows = []
        current_row = []
        current_y = None

        for block_pos in block_positions:
            if current_y is None or abs(block_pos["y_center"] - current_y) <= 5:
                current_row.append(block_pos)
                current_y = block_pos["y_center"]
            else:
                if current_row:
                    # Ordenar fila por posición X
                    current_row.sort(key=lambda x: x["x_start"])
                    rows.append(current_row)
                current_row = [block_pos]
                current_y = block_pos["y_center"]

        if current_row:
            current_row.sort(key=lambda x: x["x_start"])
            rows.append(current_row)

        return rows

    def _find_table_patterns(self, rows: List[List[Dict]]) -> List[Dict]:
        """Identifica patrones de tabla en las filas agrupadas."""

        table_candidates = []

        for i in range(len(rows) - 2):  # Necesitamos al menos 3 filas
            # Analizar 3 filas consecutivas
            row_group = rows[i:i+3]

            # Verificar si forman una tabla
            table_analysis = self._analyze_table_candidate(row_group, i)

            if table_analysis["is_table"]:
                table_candidates.append(table_analysis)

        # Fusionar tablas adyacentes
        merged_tables = self._merge_adjacent_tables(table_candidates)

        return merged_tables

    def _analyze_table_candidate(self, row_group: List[List[Dict]], start_index: int) -> Dict:
        """Analiza si un grupo de filas forma una tabla."""

        # Extraer información de columnas
        column_analysis = self._analyze_columns(row_group)

        # Calcular métricas
        alignment_score = column_analysis["alignment_score"]
        content_consistency = column_analysis["content_consistency"]
        structure_regularity = column_analysis["structure_regularity"]

        # Determinar si es tabla
        table_score = (alignment_score + content_consistency + structure_regularity) / 3
        is_table = table_score > 0.6

        # Calcular bbox total
        all_blocks = [block["block"] for row in row_group for block in row]
        table_bbox = self._calculate_group_bbox(all_blocks)

        return {
            "is_table": is_table,
            "confidence": table_score,
            "bbox": table_bbox,
            "rows": len(row_group),
            "columns": column_analysis["columns"],
            "has_header": column_analysis["has_header"],
            "data_type": column_analysis["data_type"],
            "alignment": column_analysis["alignment"],
            "start_row_index": start_index
        }

    def _analyze_columns(self, row_group: List[List[Dict]]) -> Dict:
        """Analiza la estructura de columnas en un grupo de filas."""

        # Obtener posiciones X de cada fila
        column_positions = []
        for row in row_group:
            row_x_positions = [block["x_start"] for block in row]
            column_positions.append(sorted(row_x_positions))

        # Calcular alineación promedio
        alignment_scores = []
        for i in range(len(column_positions) - 1):
            pos1, pos2 = column_positions[i], column_positions[i + 1]
            alignment = self._calculate_alignment_score(pos1, pos2)
            alignment_scores.append(alignment)

        avg_alignment = sum(alignment_scores) / len(alignment_scores) if alignment_scores else 0

        # Analizar contenido
        content_types = []
        for row in row_group:
            for block in row:
                text = self._extract_full_text_from_block(block["block"])
                content_types.append(self._classify_cell_content(text))

        # Determinar tipo de datos predominante
        data_type = max(set(content_types), key=content_types.count) if content_types else "text"

        # Detectar encabezado (primera fila diferente)
        has_header = False
        if row_group:
            first_row_content = [self._extract_full_text_from_block(block["block"]) for block in row_group[0]]
            has_header = any("empresa" in text.lower() or "nombre" in text.lower()
                           for text in first_row_content)

        return {
            "alignment_score": avg_alignment,
            "content_consistency": 0.8,  # Simplificado
            "structure_regularity": 0.7,  # Simplificado
            "columns": max(len(row) for row in row_group) if row_group else 0,
            "has_header": has_header,
            "data_type": data_type,
            "alignment": "left"  # Simplificado
        }

    def _calculate_alignment_score(self, positions1: List[float], positions2: List[float]) -> float:
        """Calcula score de alineación entre dos filas."""

        if not positions1 or not positions2:
            return 0.0

        min_len = min(len(positions1), len(positions2))
        if min_len == 0:
            return 0.0

        alignment_count = 0
        tolerance = 10  # píxeles

        for i in range(min_len):
            if abs(positions1[i] - positions2[i]) <= tolerance:
                alignment_count += 1

        return alignment_count / min_len

    def _classify_cell_content(self, text: str) -> str:
        """Clasifica el contenido de una celda de tabla."""

        text_clean = text.strip().lower()

        if re.search(r'\d+\.\d+|\d+,\d+', text):
            return "numeric"
        elif re.search(r'\d+\s*(mw|kv|hz)', text, re.IGNORECASE):
            return "technical"
        elif any(word in text_clean for word in ["empresa", "s.a.", "ltda"]):
            return "organizational"
        elif re.search(r'\d{2}:\d{2}|\d{2}/\d{2}/\d{4}', text):
            return "temporal"
        else:
            return "text"

    def _extract_full_text_from_block(self, block: Dict) -> str:
        """Extrae todo el texto de un bloque de coordenadas."""

        text_parts = []
        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                span_text = span.get("text", "").strip()
                if span_text:
                    line_text += span_text + " "
            if line_text.strip():
                text_parts.append(line_text.strip())

        return "\n".join(text_parts)

    def _extract_detailed_formatting(self, block: Dict) -> Dict:
        """Extrae información detallada de formato."""

        formatting = {
            "fonts": [],
            "sizes": [],
            "colors": [],
            "styles": {"bold": False, "italic": False},
            "dominant_style": {}
        }

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if "font" in span:
                    formatting["fonts"].append(span["font"])
                if "size" in span:
                    formatting["sizes"].append(span["size"])
                if "color" in span:
                    formatting["colors"].append(span["color"])

                flags = span.get("flags", 0)
                if flags & 16:
                    formatting["styles"]["bold"] = True
                if flags & 2:
                    formatting["styles"]["italic"] = True

        if formatting["fonts"]:
            formatting["dominant_style"]["font"] = max(set(formatting["fonts"]), key=formatting["fonts"].count)
        if formatting["sizes"]:
            formatting["dominant_style"]["size"] = max(set(formatting["sizes"]), key=formatting["sizes"].count)

        return formatting

    def _calculate_text_metrics(self, text: str) -> Dict:
        """Calcula métricas del texto."""

        return {
            "char_count": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "sentence_count": len(re.split(r'[.!?]+', text)),
            "avg_word_length": sum(len(word) for word in text.split()) / len(text.split()) if text.split() else 0
        }

    def _calculate_type_confidence(self, analysis: Dict) -> float:
        """Calcula la confianza en la clasificación de tipo."""

        base_confidence = 0.5
        content_type = analysis["type"]

        # Bonus por características específicas
        if content_type == "headers" and analysis["formatting"]["styles"]["bold"]:
            base_confidence += 0.3
        elif content_type == "formulas" and "=" in analysis["text"]:
            base_confidence += 0.3
        elif content_type == "tables" and analysis["content_metrics"]["line_count"] >= 3:
            base_confidence += 0.2

        return min(base_confidence, 1.0)

    def _extract_content_characteristics(self, text: str, content_type: str) -> Dict:
        """Extrae características específicas según el tipo de contenido."""

        characteristics = {}

        if content_type == "formulas":
            characteristics.update({
                "mathematical_symbols": re.findall(r'[=+\-*/√∑∫∆πα-ωΑ-Ω]', text),
                "variables": re.findall(r'\b[A-Z]\b', text),
                "functions": re.findall(r'(cos|sin|tan|log|ln)\(', text.lower())
            })

        elif content_type == "tables":
            lines = text.split('\n')
            characteristics.update({
                "estimated_columns": max(len(line.split()) for line in lines) if lines else 0,
                "numeric_cells": len(re.findall(r'\d+\.\d+|\d+,\d+', text)),
                "header_detected": any(word in text.lower() for word in ["empresa", "nombre", "valor"])
            })

        elif content_type == "headers":
            characteristics.update({
                "numbering_style": "decimal" if re.search(r'^\d+\.', text) else "alphabetic" if re.search(r'^[a-z]\.', text) else "none",
                "hierarchy_level": len(re.findall(r'\.', text.split()[0])) + 1 if text.split() else 1
            })

        return characteristics

    def _detect_columns(self, coord_data: Dict) -> Dict:
        """Detecta estructura de columnas en la página."""

        text_blocks = [b for b in coord_data["blocks"] if b["block_type"] == "text"]

        # Analizar distribución X
        x_positions = []
        for block in text_blocks:
            x_positions.append(block["bbox"][0])  # X start

        # Detectar clusters de posiciones X (columnas)
        x_positions.sort()
        columns = []
        current_column = [x_positions[0]] if x_positions else []

        for i in range(1, len(x_positions)):
            if x_positions[i] - x_positions[i-1] < 50:  # Misma columna
                current_column.append(x_positions[i])
            else:  # Nueva columna
                columns.append(current_column)
                current_column = [x_positions[i]]

        if current_column:
            columns.append(current_column)

        return {
            "column_count": len(columns),
            "column_positions": [sum(col)/len(col) for col in columns],
            "is_multi_column": len(columns) > 1
        }

    def _determine_reading_order(self, content_types: Dict) -> List[Dict]:
        """Determina el orden de lectura de los elementos."""

        all_elements = []
        for content_type, elements in content_types.items():
            for element in elements:
                all_elements.append({
                    "type": content_type,
                    "element": element,
                    "y_position": element["bbox"][1]  # Top Y coordinate
                })

        # Ordenar por posición Y (top to bottom)
        all_elements.sort(key=lambda x: x["y_position"])

        return [{"type": elem["type"], "id": elem["element"]["block_id"]} for elem in all_elements]

    def _merge_adjacent_tables(self, table_candidates: List[Dict]) -> List[Dict]:
        """Fusiona tablas adyacentes que probablemente son una sola tabla."""

        if len(table_candidates) <= 1:
            return table_candidates

        merged = []
        current_table = table_candidates[0]

        for i in range(1, len(table_candidates)):
            next_table = table_candidates[i]

            # Verificar si son adyacentes (diferencia de filas <= 2)
            if next_table["start_row_index"] - (current_table["start_row_index"] + current_table["rows"]) <= 2:
                # Fusionar tablas
                current_table = self._merge_two_tables(current_table, next_table)
            else:
                merged.append(current_table)
                current_table = next_table

        merged.append(current_table)
        return merged

    def _merge_two_tables(self, table1: Dict, table2: Dict) -> Dict:
        """Fusiona dos tablas adyacentes."""

        return {
            "is_table": True,
            "confidence": (table1["confidence"] + table2["confidence"]) / 2,
            "bbox": [
                min(table1["bbox"][0], table2["bbox"][0]),
                min(table1["bbox"][1], table2["bbox"][1]),
                max(table1["bbox"][2], table2["bbox"][2]),
                max(table1["bbox"][3], table2["bbox"][3])
            ],
            "rows": table1["rows"] + table2["rows"],
            "columns": max(table1["columns"], table2["columns"]),
            "has_header": table1["has_header"],
            "data_type": table1["data_type"],
            "alignment": table1["alignment"],
            "start_row_index": table1["start_row_index"]
        }

    def _calculate_group_bbox(self, blocks: List[Dict]) -> List[float]:
        """Calcula el bbox que abarca un grupo de bloques."""

        if not blocks:
            return [0, 0, 0, 0]

        all_x = []
        all_y = []

        for block in blocks:
            bbox = block["bbox"]
            all_x.extend([bbox[0], bbox[2]])
            all_y.extend([bbox[1], bbox[3]])

        return [min(all_x), min(all_y), max(all_x), max(all_y)]


def main():
    """Demo del detector de tipos de contenido."""

    # Rutas
    base_path = Path(__file__).parent
    pdf_path = base_path.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print("🔍 INICIANDO DETECCIÓN DE TIPOS DE CONTENIDO")
    print("=" * 60)

    # Crear detector
    detector = ContentTypeDetector(str(pdf_path))

    # Analizar algunas páginas
    test_pages = [2, 3, 4]

    for page_num in test_pages:
        print(f"\n📄 ANALIZANDO PÁGINA {page_num}")
        print("-" * 40)

        analysis = detector.analyze_content_types(page_num)

        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            continue

        # Mostrar resultados por tipo
        for content_type, items in analysis["content_types"].items():
            if items:
                print(f"\n📊 {content_type.upper()}: {len(items)} detectados")

                for i, item in enumerate(items[:2]):  # Mostrar primeros 2
                    print(f"  {i+1}. ID: {item['block_id']}")
                    print(f"     Texto: {item.get('text', 'N/A')[:50]}...")
                    print(f"     Confianza: {item['confidence']:.2f}")

                    if 'characteristics' in item and item['characteristics']:
                        print(f"     Características: {item['characteristics']}")

    print("\n" + "=" * 60)
    print("✅ DETECCIÓN DE TIPOS COMPLETADA")


if __name__ == "__main__":
    main()