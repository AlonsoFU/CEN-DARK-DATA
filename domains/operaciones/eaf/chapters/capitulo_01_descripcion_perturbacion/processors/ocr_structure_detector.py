"""
Detector de Estructuras OCR - Sistema Inteligente
Detecta estructuras visuales (tablas, párrafos, encabezados) usando OCR y análisis de layout
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw
import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Optional
import re
import json
from pathlib import Path
import logging
import io


class OCRStructureDetector:
    """Detecta estructuras visuales en documentos PDF usando OCR."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_doc = fitz.open(pdf_path)
        self.logger = logging.getLogger(__name__)

        # Configuración OCR
        self.tesseract_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'

    def detect_page_structures(self, page_num: int, start_page: int = 1, end_page: int = 11) -> Dict:
        """Detecta estructuras visuales en una página específica."""
        if page_num < start_page or page_num > end_page:
            return {"error": f"Página {page_num} fuera del rango {start_page}-{end_page}"}

        try:
            page = self.pdf_doc[page_num - 1]  # fitz usa indexación 0

            # Convertir página a imagen
            mat = fitz.Matrix(2, 2)  # Zoom 2x para mejor calidad
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            # Cargar imagen con PIL
            image = Image.open(io.BytesIO(img_data))

            # Convertir a array numpy para OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Detectar estructuras
            structures = {
                "page_number": page_num,
                "image_info": {
                    "width": image.width,
                    "height": image.height,
                    "dpi": 144  # 2x zoom
                },
                "detected_structures": self._analyze_visual_layout(cv_image),
                "text_analysis": self._analyze_text_structure(cv_image),
                "table_detection": self._detect_tables(cv_image),
                "ocr_validation": self._validate_against_raw(cv_image, page_num)
            }

            return structures

        except Exception as e:
            self.logger.error(f"Error procesando página {page_num}: {str(e)}")
            return {"error": str(e)}

    def _analyze_visual_layout(self, cv_image: np.ndarray) -> Dict:
        """Analiza el layout visual de la página."""
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Detectar líneas horizontales y verticales
        horizontal_lines = self._detect_horizontal_lines(gray)
        vertical_lines = self._detect_vertical_lines(gray)

        # Detectar bloques de texto
        text_blocks = self._detect_text_blocks(gray)

        # Detectar regiones tabulares
        table_regions = self._detect_table_regions(horizontal_lines, vertical_lines)

        layout_analysis = {
            "layout_type": self._classify_layout_type(text_blocks, table_regions),
            "text_blocks": len(text_blocks),
            "table_regions": len(table_regions),
            "horizontal_lines": len(horizontal_lines),
            "vertical_lines": len(vertical_lines),
            "structure_confidence": self._calculate_structure_confidence(
                text_blocks, table_regions, horizontal_lines, vertical_lines
            )
        }

        return layout_analysis

    def _detect_horizontal_lines(self, gray_image: np.ndarray) -> List[Tuple]:
        """Detecta líneas horizontales que pueden indicar tablas."""
        # Crear kernel horizontal
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))

        # Detectar líneas horizontales
        horizontal_lines = cv2.morphologyEx(gray_image, cv2.MORPH_OPEN, horizontal_kernel)

        # Encontrar contornos
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 100 and h < 10:  # Filtrar líneas horizontales significativas
                lines.append((x, y, x + w, y + h))

        return lines

    def _detect_vertical_lines(self, gray_image: np.ndarray) -> List[Tuple]:
        """Detecta líneas verticales que pueden indicar columnas de tablas."""
        # Crear kernel vertical
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

        # Detectar líneas verticales
        vertical_lines = cv2.morphologyEx(gray_image, cv2.MORPH_OPEN, vertical_kernel)

        # Encontrar contornos
        contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > 100 and w < 10:  # Filtrar líneas verticales significativas
                lines.append((x, y, x + w, y + h))

        return lines

    def _detect_text_blocks(self, gray_image: np.ndarray) -> List[Dict]:
        """Detecta bloques de texto usando OCR."""
        try:
            # Usar pytesseract para detectar bloques de texto
            data = pytesseract.image_to_data(gray_image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)

            blocks = []
            current_block = None

            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])

                if text and conf > 30:  # Filtrar texto con confianza > 30%
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

                    block_info = {
                        "bbox": (x, y, x + w, y + h),
                        "text": text,
                        "confidence": conf,
                        "block_type": self._classify_text_block_type(text)
                    }
                    blocks.append(block_info)

            return blocks

        except Exception as e:
            self.logger.error(f"Error en detección de bloques de texto: {str(e)}")
            return []

    def _classify_text_block_type(self, text: str) -> str:
        """Clasifica el tipo de bloque de texto."""
        text_lower = text.lower()

        # Patrones para diferentes tipos
        if re.match(r'^d\.\d+', text.strip()):
            return "subsection_header"
        elif re.match(r'^\d+\.', text.strip()):
            return "numbered_header"
        elif re.match(r'^[a-z]\)', text.strip()):
            return "lettered_item"
        elif any(word in text_lower for word in ['empresa', 'informe', 'plazo']):
            return "table_header"
        elif re.search(r'\d+\s+(informes?|MW|kV)', text):
            return "table_data"
        elif len(text) > 100:
            return "paragraph"
        elif text.isupper() and len(text) > 10:
            return "heading"
        elif re.search(r':\s*$', text):
            return "field_label"
        else:
            return "regular_text"

    def _detect_table_regions(self, horizontal_lines: List, vertical_lines: List) -> List[Dict]:
        """Detecta regiones que probablemente son tablas."""
        table_regions = []

        if len(horizontal_lines) >= 2 and len(vertical_lines) >= 1:
            # Agrupar líneas para formar regiones tabulares
            for i, h_line in enumerate(horizontal_lines[:-1]):
                for j, v_line in enumerate(vertical_lines):
                    # Verificar si hay intersección que forme una región tabular
                    if self._lines_form_table_region(h_line, horizontal_lines[i+1], v_line):
                        region = {
                            "top_line": h_line,
                            "bottom_line": horizontal_lines[i+1],
                            "left_boundary": min(v_line[0], v_line[2]),
                            "right_boundary": max(v_line[0], v_line[2]),
                            "confidence": 0.8
                        }
                        table_regions.append(region)

        return table_regions

    def _lines_form_table_region(self, h_line1: Tuple, h_line2: Tuple, v_line: Tuple) -> bool:
        """Verifica si las líneas forman una región tabular válida."""
        # Verificar que las líneas horizontales estén separadas apropiadamente
        vertical_separation = abs(h_line2[1] - h_line1[1])
        if vertical_separation < 20 or vertical_separation > 200:
            return False

        # Verificar que la línea vertical intersecte ambas líneas horizontales
        v_top, v_bottom = min(v_line[1], v_line[3]), max(v_line[1], v_line[3])
        h1_y, h2_y = h_line1[1], h_line2[1]

        return v_top <= min(h1_y, h2_y) and v_bottom >= max(h1_y, h2_y)

    def _classify_layout_type(self, text_blocks: List, table_regions: List) -> str:
        """Clasifica el tipo de layout de la página."""
        if len(table_regions) >= 2:
            return "multi_table"
        elif len(table_regions) == 1:
            return "single_table"
        elif len(text_blocks) > 10:
            return "dense_text"
        elif any(block["block_type"] == "subsection_header" for block in text_blocks):
            return "structured_document"
        else:
            return "regular_text"

    def _calculate_structure_confidence(self, text_blocks: List, table_regions: List,
                                      h_lines: List, v_lines: List) -> float:
        """Calcula la confianza en la detección de estructuras."""
        confidence = 0.0

        # Confianza basada en texto detectado
        if text_blocks:
            avg_text_confidence = sum(block["confidence"] for block in text_blocks) / len(text_blocks)
            confidence += (avg_text_confidence / 100) * 0.4

        # Confianza basada en estructura de tabla
        if table_regions:
            confidence += min(len(table_regions) * 0.2, 0.3)

        # Confianza basada en líneas detectadas
        if h_lines and v_lines:
            confidence += min((len(h_lines) + len(v_lines)) * 0.05, 0.3)

        return min(confidence, 1.0)

    def _analyze_text_structure(self, cv_image: np.ndarray) -> Dict:
        """Analiza la estructura del texto usando OCR."""
        try:
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Extraer texto completo con coordenadas
            ocr_data = pytesseract.image_to_data(gray, config=self.tesseract_config, output_type=pytesseract.Output.DICT)

            # Organizar texto por líneas
            lines = self._organize_text_by_lines(ocr_data)

            # Detectar patrones
            patterns = self._detect_text_patterns(lines)

            text_analysis = {
                "total_lines": len(lines),
                "patterns_detected": patterns,
                "structure_elements": self._identify_structure_elements(lines),
                "reading_order": self._determine_reading_order(lines)
            }

            return text_analysis

        except Exception as e:
            self.logger.error(f"Error en análisis de texto: {str(e)}")
            return {"error": str(e)}

    def _organize_text_by_lines(self, ocr_data: Dict) -> List[Dict]:
        """Organiza el texto OCR por líneas."""
        lines = []
        current_line = []
        current_y = None

        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if text and int(ocr_data['conf'][i]) > 20:
                y = ocr_data['top'][i]

                # Si la diferencia en Y es mayor a 10 pixels, es una nueva línea
                if current_y is None or abs(y - current_y) > 10:
                    if current_line:
                        lines.append({
                            "text": " ".join([item["text"] for item in current_line]),
                            "bbox": self._calculate_line_bbox(current_line),
                            "words": current_line
                        })
                    current_line = []
                    current_y = y

                word_info = {
                    "text": text,
                    "bbox": (ocr_data['left'][i], ocr_data['top'][i],
                            ocr_data['left'][i] + ocr_data['width'][i],
                            ocr_data['top'][i] + ocr_data['height'][i]),
                    "confidence": int(ocr_data['conf'][i])
                }
                current_line.append(word_info)

        # Agregar la última línea
        if current_line:
            lines.append({
                "text": " ".join([item["text"] for item in current_line]),
                "bbox": self._calculate_line_bbox(current_line),
                "words": current_line
            })

        return lines

    def _calculate_line_bbox(self, words: List[Dict]) -> Tuple[int, int, int, int]:
        """Calcula el bounding box de una línea de palabras."""
        if not words:
            return (0, 0, 0, 0)

        x_coords = [word["bbox"][0] for word in words] + [word["bbox"][2] for word in words]
        y_coords = [word["bbox"][1] for word in words] + [word["bbox"][3] for word in words]

        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def _detect_text_patterns(self, lines: List[Dict]) -> Dict:
        """Detecta patrones en el texto."""
        patterns = {
            "subsection_headers": [],
            "table_headers": [],
            "company_names": [],
            "technical_data": [],
            "numbered_lists": []
        }

        for line in lines:
            text = line["text"]

            # Detectar subsecciones (d.1, d.2, etc.)
            if re.match(r'd\.\d+', text.strip()):
                patterns["subsection_headers"].append(line)

            # Detectar headers de tabla
            elif any(keyword in text.lower() for keyword in ['empresa', 'informe', 'plazo']):
                patterns["table_headers"].append(line)

            # Detectar nombres de empresa
            elif re.search(r'[A-Z][A-Z\s\.]+(?:S\.A\.|SPA|Ltda)', text):
                patterns["company_names"].append(line)

            # Detectar datos técnicos
            elif re.search(r'\d+(?:\.\d+)?\s*(MW|kV|%)', text):
                patterns["technical_data"].append(line)

            # Detectar listas numeradas
            elif re.match(r'^\d+\.', text.strip()):
                patterns["numbered_lists"].append(line)

        return patterns

    def _identify_structure_elements(self, lines: List[Dict]) -> List[Dict]:
        """Identifica elementos estructurales del documento."""
        elements = []

        for i, line in enumerate(lines):
            element = {
                "line_index": i,
                "text": line["text"],
                "type": self._classify_text_block_type(line["text"]),
                "bbox": line["bbox"],
                "context": {
                    "previous_line": lines[i-1]["text"] if i > 0 else None,
                    "next_line": lines[i+1]["text"] if i < len(lines)-1 else None
                }
            }
            elements.append(element)

        return elements

    def _determine_reading_order(self, lines: List[Dict]) -> List[int]:
        """Determina el orden de lectura de las líneas."""
        # Ordenar por posición Y primero, luego por X
        indexed_lines = [(i, line) for i, line in enumerate(lines)]
        sorted_lines = sorted(indexed_lines, key=lambda x: (x[1]["bbox"][1], x[1]["bbox"][0]))

        return [index for index, _ in sorted_lines]

    def _detect_tables(self, cv_image: np.ndarray) -> Dict:
        """Detecta tablas usando análisis combinado visual + OCR."""
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Detectar líneas de tabla
        horizontal_lines = self._detect_horizontal_lines(gray)
        vertical_lines = self._detect_vertical_lines(gray)

        # Extraer texto con coordenadas
        text_data = pytesseract.image_to_data(gray, config=self.tesseract_config, output_type=pytesseract.Output.DICT)

        # Identificar regiones tabulares
        table_regions = self._identify_tabular_regions(horizontal_lines, vertical_lines, text_data)

        table_detection = {
            "tables_found": len(table_regions),
            "table_regions": table_regions,
            "detection_method": "combined_visual_ocr",
            "confidence": self._calculate_table_detection_confidence(table_regions, horizontal_lines, vertical_lines)
        }

        return table_detection

    def _identify_tabular_regions(self, h_lines: List, v_lines: List, text_data: Dict) -> List[Dict]:
        """Identifica regiones tabulares específicas."""
        regions = []

        # Buscar patrones de empresa + datos numéricos
        company_pattern = r'[A-Z][A-Z\s\.&\-]+(?:S\.A\.|SPA|Ltda)'
        report_pattern = r'\d+\s+informes?\s+(en|fuera)'

        for i in range(len(text_data['text'])):
            text = text_data['text'][i].strip()
            if re.search(company_pattern, text):
                # Verificar si hay datos de informe en la misma línea o cercana
                region_data = self._extract_table_row_data(text_data, i)
                if region_data:
                    regions.append(region_data)

        return regions

    def _extract_table_row_data(self, text_data: Dict, start_index: int) -> Optional[Dict]:
        """Extrae datos de una fila de tabla."""
        # Esta función buscaría patrones específicos en las coordenadas
        # para reconstruir filas de tabla basándose en alineación espacial

        company_text = text_data['text'][start_index].strip()
        x_pos = text_data['left'][start_index]
        y_pos = text_data['top'][start_index]

        # Buscar texto alineado horizontalmente (misma fila)
        row_texts = []
        for j in range(len(text_data['text'])):
            if abs(text_data['top'][j] - y_pos) < 15:  # Misma línea horizontal
                row_texts.append({
                    "text": text_data['text'][j].strip(),
                    "x": text_data['left'][j],
                    "confidence": text_data['conf'][j]
                })

        if len(row_texts) >= 2:  # Al menos empresa + 1 dato
            return {
                "company": company_text,
                "row_data": sorted(row_texts, key=lambda x: x["x"]),
                "y_position": y_pos,
                "confidence": 0.7
            }

        return None

    def _calculate_table_detection_confidence(self, regions: List, h_lines: List, v_lines: List) -> float:
        """Calcula confianza en la detección de tablas."""
        if not regions:
            return 0.0

        confidence = 0.0

        # Confianza basada en número de regiones detectadas
        confidence += min(len(regions) * 0.1, 0.4)

        # Confianza basada en estructura visual
        if h_lines and v_lines:
            confidence += 0.3

        # Confianza basada en patrones de texto
        confidence += 0.3

        return min(confidence, 1.0)

    def _validate_against_raw(self, cv_image: np.ndarray, page_num: int) -> Dict:
        """Valida resultados OCR contra extracción raw existente."""
        try:
            # Extraer texto OCR
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            ocr_text = pytesseract.image_to_string(gray, config=self.tesseract_config)

            # Intentar cargar texto raw existente
            raw_file = Path(__file__).parent.parent / "outputs" / "raw_extractions" / "capitulo_01_raw.txt"

            if raw_file.exists():
                with open(raw_file, 'r', encoding='utf-8') as f:
                    raw_content = f.read()

                # Extraer contenido de esta página del raw
                page_raw = self._extract_page_from_raw(raw_content, page_num)

                # Comparar similitud
                similarity = self._calculate_text_similarity(ocr_text, page_raw)

                validation = {
                    "ocr_available": True,
                    "raw_available": True,
                    "similarity_score": similarity,
                    "validation_status": "good" if similarity > 0.7 else "needs_review",
                    "ocr_char_count": len(ocr_text),
                    "raw_char_count": len(page_raw)
                }
            else:
                validation = {
                    "ocr_available": True,
                    "raw_available": False,
                    "validation_status": "no_raw_reference"
                }

            return validation

        except Exception as e:
            return {"error": str(e)}

    def _extract_page_from_raw(self, raw_content: str, page_num: int) -> str:
        """Extrae el contenido de una página específica del raw."""
        # Buscar marcadores de página
        page_pattern = rf"=== PÁGINA {page_num} ===.*?(?==== PÁGINA {page_num + 1} ===|$)"
        match = re.search(page_pattern, raw_content, re.DOTALL)

        if match:
            return match.group(0)
        else:
            return ""

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos."""
        from difflib import SequenceMatcher

        # Normalizar textos
        norm_text1 = re.sub(r'\s+', ' ', text1.lower().strip())
        norm_text2 = re.sub(r'\s+', ' ', text2.lower().strip())

        # Calcular similitud
        matcher = SequenceMatcher(None, norm_text1, norm_text2)
        return matcher.ratio()

    def analyze_document_structure(self, start_page: int = 1, end_page: int = 11) -> Dict:
        """Analiza la estructura completa del documento."""
        document_analysis = {
            "document_info": {
                "total_pages_analyzed": end_page - start_page + 1,
                "page_range": f"{start_page}-{end_page}"
            },
            "pages": {},
            "global_patterns": {},
            "recommendations": []
        }

        # Analizar cada página
        for page_num in range(start_page, end_page + 1):
            self.logger.info(f"Analizando página {page_num}...")
            page_analysis = self.detect_page_structures(page_num, start_page, end_page)
            document_analysis["pages"][page_num] = page_analysis

        # Análisis global
        document_analysis["global_patterns"] = self._analyze_global_patterns(document_analysis["pages"])
        document_analysis["recommendations"] = self._generate_recommendations(document_analysis)

        return document_analysis

    def _analyze_global_patterns(self, pages_data: Dict) -> Dict:
        """Analiza patrones globales a través del documento."""
        patterns = {
            "layout_types": {},
            "table_pages": [],
            "text_pages": [],
            "structure_consistency": 0.0
        }

        for page_num, page_data in pages_data.items():
            if "error" not in page_data:
                layout_type = page_data["detected_structures"]["layout_type"]
                patterns["layout_types"][layout_type] = patterns["layout_types"].get(layout_type, 0) + 1

                if "table" in layout_type:
                    patterns["table_pages"].append(page_num)
                else:
                    patterns["text_pages"].append(page_num)

        return patterns

    def _generate_recommendations(self, document_analysis: Dict) -> List[str]:
        """Genera recomendaciones para mejorar la extracción."""
        recommendations = []

        global_patterns = document_analysis["global_patterns"]

        if len(global_patterns.get("table_pages", [])) > 3:
            recommendations.append("Documento contiene múltiples tablas - considerar extractor especializado de tablas")

        if "multi_table" in global_patterns.get("layout_types", {}):
            recommendations.append("Páginas con múltiples tablas detectadas - usar segmentación de regiones")

        return recommendations


def main():
    """Demo del detector OCR."""
    import io

    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print("🔍 INICIANDO ANÁLISIS OCR DE ESTRUCTURAS")
    print("=" * 60)

    # Crear detector
    detector = OCRStructureDetector(str(pdf_path))

    # Analizar algunas páginas clave
    test_pages = [1, 4, 5]  # Página 1: intro, Páginas 4-5: tablas de empresas

    for page_num in test_pages:
        print(f"\n📄 ANALIZANDO PÁGINA {page_num}")
        print("-" * 40)

        result = detector.detect_page_structures(page_num)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue

        # Mostrar resultados
        structures = result["detected_structures"]
        print(f"📋 Tipo de layout: {structures['layout_type']}")
        print(f"📝 Bloques de texto: {structures['text_blocks']}")
        print(f"📊 Regiones tabulares: {structures['table_regions']}")
        print(f"🎯 Confianza estructura: {structures['structure_confidence']:.2f}")

        # Análisis de texto
        text_analysis = result["text_analysis"]
        if "error" not in text_analysis:
            print(f"📖 Líneas de texto: {text_analysis['total_lines']}")

            patterns = text_analysis["patterns_detected"]
            for pattern_type, items in patterns.items():
                if items:
                    print(f"🔍 {pattern_type}: {len(items)} encontrados")

        # Detección de tablas
        table_detection = result["table_detection"]
        print(f"🗂️ Tablas detectadas: {table_detection['tables_found']}")
        print(f"🎯 Confianza tablas: {table_detection['confidence']:.2f}")

        # Validación OCR
        validation = result["ocr_validation"]
        if "similarity_score" in validation:
            print(f"✅ Similitud OCR-Raw: {validation['similarity_score']:.2f}")
            print(f"📊 Estado validación: {validation['validation_status']}")

    print("\n" + "=" * 60)
    print("✅ ANÁLISIS OCR COMPLETADO")


if __name__ == "__main__":
    main()