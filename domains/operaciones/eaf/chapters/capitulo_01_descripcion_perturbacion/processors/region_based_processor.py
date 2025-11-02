"""
Procesador Basado en Regiones - EAF Capítulo 1
Combina OCR, coordenadas nativas PDF y raw text para crear JSON estructurado por regiones visuales
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from pdf_coordinate_extractor import PDFCoordinateExtractor
from ocr_structure_detector import OCRStructureDetector


class RegionBasedProcessor:
    """Procesador que estructura JSON basándose en regiones visuales detectadas."""

    def __init__(self, pdf_path: str, start_page: int = 1, end_page: int = 11):
        self.pdf_path = pdf_path
        self.start_page = start_page
        self.end_page = end_page

        # Inicializar extractores
        self.coordinate_extractor = PDFCoordinateExtractor(pdf_path)
        self.ocr_detector = OCRStructureDetector(pdf_path)

        self.logger = logging.getLogger(__name__)

    def process_chapter_by_regions(self, raw_text: str) -> Dict:
        """Procesa el capítulo completo organizando por regiones visuales."""

        self.logger.info("🎯 INICIANDO PROCESAMIENTO POR REGIONES")

        # Estructura base del resultado
        chapter_data = {
            "metadata": {
                "chapter": "Capítulo 1 - Descripción pormenorizada de la perturbación",
                "processing_method": "region_based_analysis",
                "pages": f"{self.start_page}-{self.end_page}",
                "extraction_sources": ["ocr_visual", "pdf_coordinates", "raw_text"]
            },
            "document_structure": {
                "sections": {},
                "tables": {},
                "technical_data": {},
                "chronological_events": {}
            },
            "pages": {}
        }

        # Procesar cada página
        for page_num in range(self.start_page, self.end_page + 1):
            self.logger.info(f"📄 Procesando página {page_num}")

            # Extraer contenido raw de esta página
            page_raw_text = self._extract_page_raw_text(raw_text, page_num)

            # Analizar la página con múltiples métodos
            page_analysis = self._analyze_page_multi_source(page_num, page_raw_text)

            # Estructurar por regiones
            page_regions = self._structure_page_by_regions(page_analysis, page_raw_text)

            chapter_data["pages"][page_num] = page_regions

        # Consolidar estructura general del documento
        chapter_data["document_structure"] = self._consolidate_document_structure(chapter_data["pages"])

        self.logger.info("✅ Procesamiento por regiones completado")
        return chapter_data

    def _extract_page_raw_text(self, raw_text: str, page_num: int) -> str:
        """Extrae el contenido raw text de una página específica."""
        # Buscar delimitadores de página en el raw text
        page_pattern = fr"Page {page_num}.*?(?=Page {page_num + 1}|$)"
        match = re.search(page_pattern, raw_text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(0)

        # Fallback: dividir por número estimado de caracteres
        chars_per_page = len(raw_text) // (self.end_page - self.start_page + 1)
        start_pos = (page_num - self.start_page) * chars_per_page
        end_pos = start_pos + chars_per_page

        return raw_text[start_pos:end_pos]

    def _analyze_page_multi_source(self, page_num: int, page_raw_text: str) -> Dict:
        """Analiza una página con múltiples fuentes de datos."""

        analysis = {
            "page_number": page_num,
            "coordinate_data": None,
            "ocr_data": None,
            "raw_text": page_raw_text,
            "integration_score": 0.0
        }

        try:
            # Análisis con coordenadas nativas
            self.logger.debug(f"🔍 Extrayendo coordenadas página {page_num}")
            analysis["coordinate_data"] = self.coordinate_extractor.extract_page_with_coordinates(page_num)

            # Análisis con OCR
            self.logger.debug(f"🔍 Analizando estructura OCR página {page_num}")
            analysis["ocr_data"] = self.ocr_detector.detect_page_structures(page_num, self.start_page, self.end_page)

            # Calcular puntuación de integración
            analysis["integration_score"] = self._calculate_integration_score(analysis)

        except Exception as e:
            self.logger.error(f"Error analizando página {page_num}: {e}")
            analysis["error"] = str(e)

        return analysis

    def _calculate_integration_score(self, analysis: Dict) -> float:
        """Calcula qué tan bien se integran los diferentes métodos de análisis."""
        score = 0.0

        # Verificar disponibilidad de datos
        if analysis["coordinate_data"] and "error" not in analysis["coordinate_data"]:
            score += 0.4

        if analysis["ocr_data"] and "error" not in analysis["ocr_data"]:
            score += 0.4

        if analysis["raw_text"] and len(analysis["raw_text"].strip()) > 100:
            score += 0.2

        return score

    def _structure_page_by_regions(self, page_analysis: Dict, page_raw_text: str) -> Dict:
        """Estructura el contenido de la página por regiones visuales."""

        page_regions = {
            "page_number": page_analysis["page_number"],
            "integration_score": page_analysis["integration_score"],
            "regions": [],
            "structure_summary": {
                "headers": 0,
                "paragraphs": 0,
                "tables": 0,
                "technical_data": 0,
                "chronological_events": 0
            }
        }

        # Si tenemos datos de coordenadas, usarlos como base
        if page_analysis["coordinate_data"] and "error" not in page_analysis["coordinate_data"]:
            page_regions["regions"] = self._create_regions_from_coordinates(
                page_analysis["coordinate_data"],
                page_raw_text,
                page_analysis.get("ocr_data")
            )

        # Si no, usar OCR como fallback
        elif page_analysis["ocr_data"] and "error" not in page_analysis["ocr_data"]:
            page_regions["regions"] = self._create_regions_from_ocr(
                page_analysis["ocr_data"],
                page_raw_text
            )

        # Último recurso: análisis básico del raw text
        else:
            page_regions["regions"] = self._create_regions_from_raw_text(page_raw_text)

        # Actualizar resumen de estructura
        page_regions["structure_summary"] = self._calculate_structure_summary(page_regions["regions"])

        return page_regions

    def _create_regions_from_coordinates(self, coord_data: Dict, raw_text: str, ocr_data: Optional[Dict] = None) -> List[Dict]:
        """Crea regiones basándose en coordenadas PDF nativas."""

        regions = []

        # Procesar bloques de texto
        text_blocks = [block for block in coord_data["blocks"] if block["block_type"] == "text"]

        for i, block in enumerate(text_blocks):
            # Extraer texto del bloque
            block_text = self._extract_text_from_coordinate_block(block)

            if not block_text or len(block_text.strip()) < 3:
                continue

            # Encontrar coincidencia en raw text
            raw_match = self._find_text_in_raw(block_text, raw_text)

            # Clasificar tipo de región
            region_type = self._classify_region_content(block_text, block, ocr_data)

            # Crear región
            region = {
                "region_id": f"coord_{i}",
                "type": region_type,
                "source": "pdf_coordinates",
                "bbox": block["bbox"],
                "content": {
                    "text": block_text,
                    "raw_text_match": raw_match,
                    "formatting": self._extract_formatting_from_coordinate_block(block),
                    "structure_hints": self._extract_structure_hints(block_text)
                },
                "confidence": self._calculate_region_confidence(block_text, raw_match, region_type)
            }

            # Enriquecer con datos OCR si están disponibles
            if ocr_data:
                region["ocr_enhancement"] = self._enhance_region_with_ocr(region, ocr_data)

            regions.append(region)

        # Agregar regiones de tablas detectadas
        for i, table in enumerate(coord_data.get("tables", [])):
            table_region = self._create_table_region_from_coordinates(table, raw_text, i)
            if table_region:
                regions.append(table_region)

        # Ordenar regiones por posición vertical (Y)
        regions.sort(key=lambda r: r["bbox"][1] if "bbox" in r else float('inf'))

        return regions

    def _extract_text_from_coordinate_block(self, block: Dict) -> str:
        """Extrae texto limpio de un bloque de coordenadas."""
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

    def _classify_region_content(self, text: str, block: Dict, ocr_data: Optional[Dict] = None) -> str:
        """Clasifica el tipo de contenido de una región."""

        text_lower = text.lower()

        # Detectar encabezados de sección
        if re.search(r'^[a-z]\.\d+\s', text_lower) or re.search(r'^\d+\.\s', text_lower):
            return "section_header"

        # Detectar subsecciones
        if re.search(r'^[a-z]\.\d+\.\d+', text_lower):
            return "subsection_header"

        # Detectar datos técnicos
        if any(unit in text_lower for unit in ["mw", "mva", "kv", "hz", "°c"]):
            return "technical_data"

        # Detectar información temporal/cronológica
        if re.search(r'\d{2}[:/]\d{2}[:/]\d{4}|\d{2}:\d{2}', text):
            return "chronological_event"

        # Detectar empresas/organizaciones
        if any(company in text_lower for company in ["s.a.", "ltda", "empresa", "enel", "colbún"]):
            return "organization_info"

        # Detectar tablas por formato
        if self._detect_tabular_format(text):
            return "table_content"

        # Detectar contenido de fórmula/cálculo
        if re.search(r'[=+\-*/]\s*\d+|\d+\s*[%]', text):
            return "formula_calculation"

        # Por defecto: párrafo
        return "paragraph"

    def _detect_tabular_format(self, text: str) -> bool:
        """Detecta si el texto tiene formato tabular."""
        lines = text.split('\n')

        # Verificar si hay múltiples columnas separadas por espacios
        column_separators = 0
        for line in lines:
            if len(line.split()) >= 3:  # Al menos 3 columnas
                column_separators += 1

        return column_separators >= 2  # Al menos 2 líneas con formato columnar

    def _extract_formatting_from_coordinate_block(self, block: Dict) -> Dict:
        """Extrae información de formato de un bloque de coordenadas."""

        formatting = {
            "fonts": set(),
            "sizes": set(),
            "styles": set(),
            "primary_font": None,
            "primary_size": None,
            "is_bold": False,
            "is_italic": False
        }

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if "font" in span:
                    formatting["fonts"].add(span["font"])
                if "size" in span:
                    formatting["sizes"].add(span["size"])

                # Detectar estilos basándose en flags
                flags = span.get("flags", 0)
                if flags & 16:  # Bold flag
                    formatting["is_bold"] = True
                    formatting["styles"].add("bold")
                if flags & 2:   # Italic flag
                    formatting["is_italic"] = True
                    formatting["styles"].add("italic")

        # Convertir sets a listas y encontrar valores primarios
        formatting["fonts"] = list(formatting["fonts"])
        formatting["sizes"] = list(formatting["sizes"])
        formatting["styles"] = list(formatting["styles"])

        if formatting["fonts"]:
            formatting["primary_font"] = max(formatting["fonts"], key=str)
        if formatting["sizes"]:
            formatting["primary_size"] = max(formatting["sizes"])

        return formatting

    def _extract_structure_hints(self, text: str) -> Dict:
        """Extrae pistas sobre la estructura del contenido."""

        hints = {
            "has_numbering": bool(re.search(r'^\d+\.|\b[a-z]\.\d+', text)),
            "has_subsections": bool(re.search(r'[a-z]\.\d+\.\d+', text)),
            "has_technical_units": bool(re.search(r'\d+\s*(MW|kV|Hz|MVA|°C)', text, re.IGNORECASE)),
            "has_timestamps": bool(re.search(r'\d{2}:\d{2}|\d{2}/\d{2}/\d{4}', text)),
            "has_organizations": bool(re.search(r'(S\.A\.|Ltda\.|\bEmpresa\b)', text, re.IGNORECASE)),
            "line_count": len(text.split('\n')),
            "word_count": len(text.split()),
            "char_count": len(text)
        }

        return hints

    def _find_text_in_raw(self, block_text: str, raw_text: str) -> Dict:
        """Encuentra el texto del bloque en el raw text."""

        # Limpiar textos para comparación
        clean_block = re.sub(r'\s+', ' ', block_text.strip().lower())
        clean_raw = re.sub(r'\s+', ' ', raw_text.lower())

        # Buscar coincidencia exacta
        start_pos = clean_raw.find(clean_block)
        if start_pos != -1:
            return {
                "found": True,
                "match_type": "exact",
                "start_position": start_pos,
                "end_position": start_pos + len(clean_block),
                "context_before": clean_raw[max(0, start_pos-50):start_pos],
                "context_after": clean_raw[start_pos+len(clean_block):start_pos+len(clean_block)+50]
            }

        # Buscar coincidencia parcial (primeras palabras)
        words = clean_block.split()
        if len(words) >= 2:
            partial_text = " ".join(words[:3])  # Primeras 3 palabras
            partial_pos = clean_raw.find(partial_text)
            if partial_pos != -1:
                return {
                    "found": True,
                    "match_type": "partial",
                    "start_position": partial_pos,
                    "end_position": partial_pos + len(partial_text),
                    "matched_words": 3,
                    "total_words": len(words)
                }

        return {
            "found": False,
            "match_type": "none",
            "search_attempted": clean_block[:100]  # Primeros 100 chars buscados
        }

    def _calculate_region_confidence(self, text: str, raw_match: Dict, region_type: str) -> float:
        """Calcula la confianza de la región."""

        confidence = 0.0

        # Confianza basada en coincidencia con raw text
        if raw_match["found"]:
            if raw_match["match_type"] == "exact":
                confidence += 0.5
            elif raw_match["match_type"] == "partial":
                confidence += 0.3

        # Confianza basada en contenido
        if len(text.strip()) > 10:
            confidence += 0.2

        # Confianza basada en tipo de región
        type_confidence = {
            "section_header": 0.3,
            "technical_data": 0.3,
            "table_content": 0.2,
            "paragraph": 0.1
        }
        confidence += type_confidence.get(region_type, 0.1)

        return min(confidence, 1.0)

    def _create_table_region_from_coordinates(self, table: Dict, raw_text: str, table_index: int) -> Optional[Dict]:
        """Crea una región de tabla basándose en coordenadas."""

        if table["confidence"] < 0.6:  # Solo tablas con alta confianza
            return None

        # Extraer contenido de tabla desde raw text basándose en posición
        table_content = self._extract_table_content_from_raw(table, raw_text)

        region = {
            "region_id": f"table_{table_index}",
            "type": "table",
            "source": "pdf_coordinates",
            "bbox": table["bbox"],
            "content": {
                "estimated_rows": table["estimated_rows"],
                "estimated_columns": table["estimated_columns"],
                "raw_content": table_content,
                "structure": self._analyze_table_structure(table_content)
            },
            "confidence": table["confidence"]
        }

        return region

    def _extract_table_content_from_raw(self, table: Dict, raw_text: str) -> str:
        """Extrae contenido de tabla del raw text (implementación básica)."""
        # Esta es una implementación simplificada
        # En un caso real, necesitarías mapear las coordenadas bbox a posiciones en el texto
        return f"Tabla detectada con {table['estimated_rows']} filas y {table['estimated_columns']} columnas"

    def _analyze_table_structure(self, table_content: str) -> Dict:
        """Analiza la estructura de una tabla."""
        return {
            "has_header": "empresa" in table_content.lower() or "nombre" in table_content.lower(),
            "has_numeric_data": bool(re.search(r'\d+\.?\d*', table_content)),
            "content_type": "organizational" if "empresa" in table_content.lower() else "technical"
        }

    def _enhance_region_with_ocr(self, region: Dict, ocr_data: Dict) -> Dict:
        """Enriquece una región con datos OCR."""
        # Implementación básica de enriquecimiento OCR
        return {
            "ocr_available": True,
            "visual_enhancement": "Datos OCR disponibles para validación"
        }

    def _create_regions_from_ocr(self, ocr_data: Dict, raw_text: str) -> List[Dict]:
        """Crea regiones basándose en análisis OCR (fallback)."""
        # Implementación simplificada para OCR fallback
        return [
            {
                "region_id": "ocr_fallback",
                "type": "mixed_content",
                "source": "ocr_analysis",
                "content": {
                    "text": raw_text[:500] + "...",
                    "note": "Procesamiento por OCR fallback"
                },
                "confidence": 0.7
            }
        ]

    def _create_regions_from_raw_text(self, raw_text: str) -> List[Dict]:
        """Crea regiones basándose solo en raw text (último recurso)."""

        regions = []

        # Dividir por párrafos o secciones obvias
        sections = re.split(r'\n\s*\n', raw_text)

        for i, section in enumerate(sections):
            if len(section.strip()) < 20:  # Ignorar secciones muy cortas
                continue

            region_type = self._classify_region_content(section, {}, None)

            region = {
                "region_id": f"raw_{i}",
                "type": region_type,
                "source": "raw_text_analysis",
                "content": {
                    "text": section.strip(),
                    "structure_hints": self._extract_structure_hints(section)
                },
                "confidence": 0.5
            }

            regions.append(region)

        return regions

    def _calculate_structure_summary(self, regions: List[Dict]) -> Dict:
        """Calcula resumen de estructura de las regiones."""

        summary = {
            "headers": 0,
            "paragraphs": 0,
            "tables": 0,
            "technical_data": 0,
            "chronological_events": 0,
            "total_regions": len(regions)
        }

        for region in regions:
            region_type = region["type"]

            if "header" in region_type:
                summary["headers"] += 1
            elif region_type == "paragraph":
                summary["paragraphs"] += 1
            elif region_type == "table" or "table" in region_type:
                summary["tables"] += 1
            elif region_type == "technical_data":
                summary["technical_data"] += 1
            elif region_type == "chronological_event":
                summary["chronological_events"] += 1

        return summary

    def _consolidate_document_structure(self, pages_data: Dict) -> Dict:
        """Consolida la estructura del documento desde todas las páginas."""

        consolidated = {
            "sections": {},
            "tables": {},
            "technical_data": {},
            "chronological_events": {},
            "summary": {
                "total_regions": 0,
                "regions_by_type": {},
                "confidence_distribution": {}
            }
        }

        # Recopilar información de todas las páginas
        for page_num, page_data in pages_data.items():
            page_regions = page_data.get("regions", [])

            for region in page_regions:
                region_type = region["type"]
                region_id = f"page_{page_num}_{region['region_id']}"

                # Organizar por tipo
                if "header" in region_type:
                    consolidated["sections"][region_id] = {
                        "page": page_num,
                        "content": region["content"]["text"][:200],
                        "type": region_type,
                        "confidence": region["confidence"]
                    }
                elif region_type == "table" or "table" in region_type:
                    consolidated["tables"][region_id] = {
                        "page": page_num,
                        "structure": region["content"],
                        "confidence": region["confidence"]
                    }
                elif region_type == "technical_data":
                    consolidated["technical_data"][region_id] = {
                        "page": page_num,
                        "content": region["content"]["text"],
                        "confidence": region["confidence"]
                    }
                elif region_type == "chronological_event":
                    consolidated["chronological_events"][region_id] = {
                        "page": page_num,
                        "content": region["content"]["text"],
                        "confidence": region["confidence"]
                    }

                # Actualizar estadísticas
                consolidated["summary"]["total_regions"] += 1

                if region_type not in consolidated["summary"]["regions_by_type"]:
                    consolidated["summary"]["regions_by_type"][region_type] = 0
                consolidated["summary"]["regions_by_type"][region_type] += 1

        return consolidated


def main():
    """Demo del procesador basado en regiones."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Rutas de archivos
    base_path = Path(__file__).parent
    pdf_path = base_path.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"
    raw_text_path = base_path.parent / "outputs" / "raw_extractions" / "capitulo_01_raw.txt"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    if not raw_text_path.exists():
        print(f"❌ Raw text no encontrado: {raw_text_path}")
        return

    # Leer raw text
    with open(raw_text_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    print("🎯 INICIANDO PROCESAMIENTO BASADO EN REGIONES")
    print("=" * 60)

    # Crear procesador
    processor = RegionBasedProcessor(str(pdf_path), start_page=1, end_page=11)

    # Procesar capítulo
    result = processor.process_chapter_by_regions(raw_text)

    # Guardar resultado
    output_path = base_path.parent / "outputs" / "universal_json" / "capitulo_01_region_based.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"💾 Resultado guardado en: {output_path}")
    print("\n📊 RESUMEN DEL PROCESAMIENTO:")
    print(f"📄 Páginas procesadas: {len(result['pages'])}")

    total_regions = sum(len(page.get('regions', [])) for page in result['pages'].values())
    print(f"🎯 Total regiones detectadas: {total_regions}")

    structure_summary = result['document_structure']['summary']
    print(f"📝 Regiones por tipo: {structure_summary.get('regions_by_type', {})}")

    print("\n" + "=" * 60)
    print("✅ PROCESAMIENTO POR REGIONES COMPLETADO")


if __name__ == "__main__":
    main()