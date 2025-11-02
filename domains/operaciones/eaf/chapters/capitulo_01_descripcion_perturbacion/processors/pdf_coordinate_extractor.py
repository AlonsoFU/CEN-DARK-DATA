"""
Extractor de Coordenadas PDF - Análisis Nativo
Extrae texto con coordenadas directamente del PDF sin OCR
"""

import fitz  # PyMuPDF
import json
from pathlib import Path
from typing import Dict, List, Tuple
import logging


class PDFCoordinateExtractor:
    """Extrae texto con coordenadas nativas del PDF."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_doc = fitz.open(pdf_path)
        self.logger = logging.getLogger(__name__)

    def extract_page_with_coordinates(self, page_num: int) -> Dict:
        """Extrae texto con coordenadas de una página específica."""
        try:
            page = self.pdf_doc[page_num - 1]  # fitz usa indexación 0

            # Extraer texto con coordenadas
            text_dict = page.get_text("dict")

            # Procesar la estructura de texto
            page_analysis = {
                "page_number": page_num,
                "page_size": {
                    "width": page.rect.width,
                    "height": page.rect.height
                },
                "blocks": self._process_text_blocks(text_dict["blocks"]),
                "images": self._extract_images(page),
                "drawings": self._extract_drawings(page),
                "tables": self._detect_table_regions(text_dict["blocks"])
            }

            return page_analysis

        except Exception as e:
            self.logger.error(f"Error extrayendo página {page_num}: {str(e)}")
            return {"error": str(e)}

    def _process_text_blocks(self, blocks: List) -> List[Dict]:
        """Procesa bloques de texto con coordenadas."""
        processed_blocks = []

        for block_num, block in enumerate(blocks):
            if "lines" in block:  # Es un bloque de texto
                block_info = {
                    "block_id": block_num,
                    "bbox": block["bbox"],  # [x0, y0, x1, y1]
                    "block_type": "text",
                    "lines": []
                }

                for line_num, line in enumerate(block["lines"]):
                    line_info = {
                        "line_id": line_num,
                        "bbox": line["bbox"],
                        "text": "",
                        "spans": []
                    }

                    for span_num, span in enumerate(line["spans"]):
                        span_info = {
                            "span_id": span_num,
                            "bbox": span["bbox"],
                            "text": span["text"],
                            "font": span["font"],
                            "size": span["size"],
                            "flags": span["flags"],  # Bold, italic, etc.
                            "color": span["color"]
                        }
                        line_info["spans"].append(span_info)
                        line_info["text"] += span["text"]

                    block_info["lines"].append(line_info)

                processed_blocks.append(block_info)

            elif "image" in block:  # Es una imagen
                block_info = {
                    "block_id": block_num,
                    "bbox": block["bbox"],
                    "block_type": "image",
                    "image_info": {
                        "width": block["width"],
                        "height": block["height"],
                        "colorspace": block.get("colorspace", "unknown")
                    }
                }
                processed_blocks.append(block_info)

        return processed_blocks

    def _extract_images(self, page) -> List[Dict]:
        """Extrae información de imágenes de la página."""
        images = []
        image_list = page.get_images()

        for img_index, img in enumerate(image_list):
            img_info = {
                "image_id": img_index,
                "xref": img[0],
                "smask": img[1],
                "width": img[2],
                "height": img[3],
                "bpc": img[4],  # bits per component
                "colorspace": img[5],
                "alt": img[6],
                "name": img[7],
                "filter": img[8]
            }
            images.append(img_info)

        return images

    def _extract_drawings(self, page) -> List[Dict]:
        """Extrae información de dibujos/líneas de la página."""
        drawings = []

        try:
            # Obtener dibujos de la página
            drawing_list = page.get_drawings()

            for draw_index, drawing in enumerate(drawing_list):
                draw_info = {
                    "drawing_id": draw_index,
                    "bbox": drawing["rect"],
                    "type": drawing.get("type", "unknown"),
                    "items": len(drawing.get("items", []))
                }
                drawings.append(draw_info)

        except Exception as e:
            self.logger.warning(f"Error extrayendo dibujos: {e}")

        return drawings

    def _detect_table_regions(self, blocks: List) -> List[Dict]:
        """Detecta regiones que parecen tablas basándose en alineación de texto."""
        tables = []

        # Agrupar bloques por posición Y (filas)
        rows = self._group_blocks_by_rows(blocks)

        # Detectar patrones tabulares
        if len(rows) >= 3:  # Al menos 3 filas
            table_candidates = self._identify_table_candidates(rows)
            tables.extend(table_candidates)

        return tables

    def _group_blocks_by_rows(self, blocks: List) -> List[List]:
        """Agrupa bloques de texto por filas (posición Y similar)."""
        text_blocks = [block for block in blocks if "lines" in block]

        # Extraer todas las líneas con sus coordenadas Y
        all_lines = []
        for block in text_blocks:
            for line in block["lines"]:
                all_lines.append({
                    "y": line["bbox"][1],  # coordenada Y
                    "bbox": line["bbox"],
                    "text": "".join(span["text"] for span in line["spans"]),
                    "block": block
                })

        # Agrupar por Y similar (tolerancia de 5 píxeles)
        rows = []
        all_lines.sort(key=lambda x: x["y"])

        current_row = []
        current_y = None

        for line in all_lines:
            if current_y is None or abs(line["y"] - current_y) <= 5:
                current_row.append(line)
                current_y = line["y"]
            else:
                if current_row:
                    rows.append(sorted(current_row, key=lambda x: x["bbox"][0]))  # Ordenar por X
                current_row = [line]
                current_y = line["y"]

        if current_row:
            rows.append(sorted(current_row, key=lambda x: x["bbox"][0]))

        return rows

    def _identify_table_candidates(self, rows: List[List]) -> List[Dict]:
        """Identifica regiones que parecen tablas."""
        table_candidates = []

        # Buscar patrones de columnas consistentes
        for i in range(len(rows) - 2):
            # Verificar si 3 filas consecutivas tienen estructura similar
            row1, row2, row3 = rows[i], rows[i+1], rows[i+2]

            if self._rows_have_similar_structure(row1, row2, row3):
                # Determinar el área de la tabla
                table_bbox = self._calculate_table_bbox(rows[i:i+3])

                table_info = {
                    "table_id": len(table_candidates),
                    "bbox": table_bbox,
                    "start_row": i,
                    "estimated_rows": 3,
                    "estimated_columns": len(row1),
                    "confidence": self._calculate_table_confidence(row1, row2, row3)
                }
                table_candidates.append(table_info)

        return table_candidates

    def _rows_have_similar_structure(self, row1: List, row2: List, row3: List) -> bool:
        """Verifica si las filas tienen estructura similar (mismo número de columnas)."""
        # Verificar número similar de elementos
        if abs(len(row1) - len(row2)) > 1 or abs(len(row2) - len(row3)) > 1:
            return False

        # Verificar alineación de columnas (posiciones X similares)
        if len(row1) >= 2 and len(row2) >= 2:
            x_positions_1 = [item["bbox"][0] for item in row1]
            x_positions_2 = [item["bbox"][0] for item in row2]

            # Verificar si las posiciones X son similares
            for i in range(min(len(x_positions_1), len(x_positions_2))):
                if abs(x_positions_1[i] - x_positions_2[i]) > 10:  # Tolerancia de 10 píxeles
                    return False

        return True

    def _calculate_table_bbox(self, rows: List[List]) -> List[float]:
        """Calcula el bounding box de una tabla."""
        all_x = []
        all_y = []

        for row in rows:
            for item in row:
                bbox = item["bbox"]
                all_x.extend([bbox[0], bbox[2]])
                all_y.extend([bbox[1], bbox[3]])

        return [min(all_x), min(all_y), max(all_x), max(all_y)]

    def _calculate_table_confidence(self, row1: List, row2: List, row3: List) -> float:
        """Calcula la confianza de que es una tabla."""
        confidence = 0.0

        # Más elementos = más probable que sea tabla
        avg_elements = (len(row1) + len(row2) + len(row3)) / 3
        confidence += min(avg_elements * 0.1, 0.5)

        # Alineación consistente
        if self._rows_have_similar_structure(row1, row2, row3):
            confidence += 0.3

        # Contenido numérico aumenta probabilidad
        numeric_content = sum(1 for row in [row1, row2, row3]
                            for item in row
                            if any(c.isdigit() for c in item["text"]))
        confidence += min(numeric_content * 0.05, 0.2)

        return min(confidence, 1.0)

    def analyze_document_structure(self, start_page: int = 1, end_page: int = 11) -> Dict:
        """Analiza la estructura completa del documento."""
        document_structure = {
            "document_info": {
                "total_pages": end_page - start_page + 1,
                "page_range": f"{start_page}-{end_page}",
                "extraction_method": "pdf_native_coordinates"
            },
            "pages": {},
            "global_analysis": {
                "total_text_blocks": 0,
                "total_images": 0,
                "total_tables": 0,
                "coordinate_system": "pdf_native"
            }
        }

        # Analizar cada página
        for page_num in range(start_page, end_page + 1):
            self.logger.info(f"Extrayendo coordenadas página {page_num}...")
            page_data = self.extract_page_with_coordinates(page_num)
            document_structure["pages"][page_num] = page_data

            # Actualizar estadísticas globales
            if "error" not in page_data:
                document_structure["global_analysis"]["total_text_blocks"] += len(page_data["blocks"])
                document_structure["global_analysis"]["total_images"] += len(page_data["images"])
                document_structure["global_analysis"]["total_tables"] += len(page_data["tables"])

        return document_structure

    def create_region_based_structure(self, page_num: int, raw_text: str) -> Dict:
        """Crea estructura basada en regiones visuales pero usando raw text."""
        # Obtener coordenadas nativas
        coordinate_data = self.extract_page_with_coordinates(page_num)

        if "error" in coordinate_data:
            return {"error": coordinate_data["error"]}

        # Clasificar regiones
        regions = {
            "page_number": page_num,
            "regions": [],
            "text_mapping": self._map_text_to_regions(raw_text, coordinate_data)
        }

        # Procesar cada bloque como una región
        for block in coordinate_data["blocks"]:
            if block["block_type"] == "text":
                region = self._classify_text_region(block, raw_text)
                regions["regions"].append(region)
            elif block["block_type"] == "image":
                region = {
                    "region_id": len(regions["regions"]),
                    "type": "image",
                    "bbox": block["bbox"],
                    "content": {"image_info": block["image_info"]}
                }
                regions["regions"].append(region)

        # Detectar tablas y reorganizar
        table_regions = coordinate_data["tables"]
        for table in table_regions:
            region = {
                "region_id": len(regions["regions"]),
                "type": "table",
                "bbox": table["bbox"],
                "confidence": table["confidence"],
                "content": self._extract_table_content_from_raw(table, raw_text)
            }
            regions["regions"].append(region)

        return regions

    def _classify_text_region(self, block: Dict, raw_text: str) -> Dict:
        """Clasifica una región de texto."""
        # Extraer texto del bloque
        block_text = ""
        for line in block["lines"]:
            block_text += line["text"] + "\n"

        block_text = block_text.strip()

        # Clasificar tipo de región
        region_type = "paragraph"
        if any(pattern in block_text.lower() for pattern in ["d.1", "d.2", "d.3"]):
            region_type = "subsection_header"
        elif any(pattern in block_text.lower() for pattern in ["empresa", "informe"]):
            region_type = "table_header"
        elif len(block_text.split()) < 5:
            region_type = "field_label"
        elif any(char.isdigit() for char in block_text) and "MW" in block_text:
            region_type = "technical_data"

        return {
            "region_id": len([]),  # Se asignará después
            "type": region_type,
            "bbox": block["bbox"],
            "content": {
                "text": block_text,
                "raw_match": self._find_text_in_raw(block_text, raw_text),
                "formatting": self._extract_formatting_info(block)
            }
        }

    def _extract_formatting_info(self, block: Dict) -> Dict:
        """Extrae información de formato del bloque."""
        formatting = {
            "fonts": [],
            "sizes": [],
            "styles": []
        }

        for line in block["lines"]:
            for span in line["spans"]:
                formatting["fonts"].append(span["font"])
                formatting["sizes"].append(span["size"])

                # Determinar estilos basándose en flags
                styles = []
                flags = span["flags"]
                if flags & 2**4:  # Bold
                    styles.append("bold")
                if flags & 2**1:  # Italic
                    styles.append("italic")
                formatting["styles"].extend(styles)

        # Eliminar duplicados y obtener más común
        formatting["primary_font"] = max(set(formatting["fonts"]), key=formatting["fonts"].count) if formatting["fonts"] else "unknown"
        formatting["primary_size"] = max(set(formatting["sizes"]), key=formatting["sizes"].count) if formatting["sizes"] else 0
        formatting["styles"] = list(set(formatting["styles"]))

        return formatting

    def _map_text_to_regions(self, raw_text: str, coordinate_data: Dict) -> Dict:
        """Mapea texto raw a regiones con coordenadas."""
        mapping = {
            "total_raw_chars": len(raw_text),
            "total_coordinate_chars": 0,
            "match_percentage": 0.0
        }

        # Calcular caracteres totales en coordenadas
        total_coord_chars = 0
        for block in coordinate_data["blocks"]:
            if block["block_type"] == "text":
                for line in block["lines"]:
                    total_coord_chars += len(line["text"])

        mapping["total_coordinate_chars"] = total_coord_chars
        if len(raw_text) > 0:
            mapping["match_percentage"] = min(total_coord_chars / len(raw_text), 1.0)

        return mapping

    def _find_text_in_raw(self, block_text: str, raw_text: str) -> Dict:
        """Encuentra el texto del bloque en el raw text."""
        # Normalizar textos para comparación
        normalized_block = block_text.strip().lower()
        normalized_raw = raw_text.lower()

        # Buscar coincidencia exacta
        start_pos = normalized_raw.find(normalized_block)

        if start_pos != -1:
            return {
                "found": True,
                "start_position": start_pos,
                "end_position": start_pos + len(normalized_block),
                "match_type": "exact"
            }

        # Buscar coincidencia parcial (primeras palabras)
        words = normalized_block.split()
        if words:
            first_words = " ".join(words[:3])  # Primeras 3 palabras
            partial_pos = normalized_raw.find(first_words)
            if partial_pos != -1:
                return {
                    "found": True,
                    "start_position": partial_pos,
                    "end_position": partial_pos + len(first_words),
                    "match_type": "partial"
                }

        return {
            "found": False,
            "match_type": "none"
        }

    def _extract_table_content_from_raw(self, table_info: Dict, raw_text: str) -> Dict:
        """Extrae contenido de tabla desde el raw text basándose en región."""
        # Esta función necesitaría lógica más compleja para mapear
        # las coordenadas de tabla al contenido raw correspondiente
        return {
            "extraction_method": "coordinate_based",
            "estimated_rows": table_info["estimated_rows"],
            "estimated_columns": table_info["estimated_columns"],
            "raw_content": "TODO: Implementar mapeo coordenadas->raw"
        }


def main():
    """Demo del extractor de coordenadas PDF."""
    logging.basicConfig(level=logging.INFO)

    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print("📄 INICIANDO EXTRACCIÓN DE COORDENADAS PDF NATIVAS")
    print("=" * 60)

    # Crear extractor
    extractor = PDFCoordinateExtractor(str(pdf_path))

    # Probar con algunas páginas
    test_pages = [1, 4, 5]

    for page_num in test_pages:
        print(f"\n📍 EXTRAYENDO COORDENADAS PÁGINA {page_num}")
        print("-" * 40)

        result = extractor.extract_page_with_coordinates(page_num)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue

        # Mostrar estadísticas
        print(f"📐 Tamaño página: {result['page_size']['width']:.1f} x {result['page_size']['height']:.1f}")
        print(f"📝 Bloques de texto: {len([b for b in result['blocks'] if b['block_type'] == 'text'])}")
        print(f"🖼️ Imágenes: {len(result['images'])}")
        print(f"✏️ Dibujos: {len(result['drawings'])}")
        print(f"📊 Tablas detectadas: {len(result['tables'])}")

        # Mostrar algunas coordenadas de ejemplo
        text_blocks = [b for b in result['blocks'] if b['block_type'] == 'text']
        if text_blocks:
            first_block = text_blocks[0]
            print(f"📍 Primer bloque bbox: {first_block['bbox']}")
            if first_block['lines']:
                first_line = first_block['lines'][0]
                print(f"📍 Primera línea: '{first_line['text'][:50]}...'")

        # Mostrar tablas detectadas
        for table in result['tables']:
            print(f"📊 Tabla detectada: bbox={table['bbox']}, confianza={table['confidence']:.2f}")

    print("\n" + "=" * 60)
    print("✅ EXTRACCIÓN DE COORDENADAS COMPLETADA")


if __name__ == "__main__":
    main()