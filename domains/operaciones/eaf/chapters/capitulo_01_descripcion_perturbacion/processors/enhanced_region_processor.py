"""
Procesador Mejorado de Regiones - EAF Capítulo 1
Versión optimizada que mejora el mapeo entre coordenadas PDF y raw text
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from difflib import SequenceMatcher

from pdf_coordinate_extractor import PDFCoordinateExtractor


class EnhancedRegionProcessor:
    """Procesador mejorado que mapea mejor las coordenadas al raw text."""

    def __init__(self, pdf_path: str, start_page: int = 1, end_page: int = 11):
        self.pdf_path = pdf_path
        self.start_page = start_page
        self.end_page = end_page
        self.coordinate_extractor = PDFCoordinateExtractor(pdf_path)
        self.logger = logging.getLogger(__name__)

    def process_with_enhanced_mapping(self, raw_text: str) -> Dict:
        """Procesa con mapeo mejorado entre coordenadas y raw text."""

        self.logger.info("🚀 INICIANDO PROCESAMIENTO MEJORADO")

        # Estructura base
        result = {
            "metadata": {
                "chapter": "Capítulo 1 - Descripción pormenorizada de la perturbación",
                "processing_method": "enhanced_region_mapping",
                "pages": f"{self.start_page}-{self.end_page}",
                "enhancement_features": [
                    "improved_text_matching",
                    "section_aware_organization",
                    "content_type_classification",
                    "hierarchical_structure"
                ]
            },
            "content_by_sections": {},
            "chronological_events": {},
            "technical_parameters": {},
            "organizational_entities": {},
            "tables_and_data": {},
            "processing_summary": {}
        }

        # Preprocesar raw text para mejor mapeo
        preprocessed_text = self._preprocess_raw_text(raw_text)

        # Procesar cada página con mapeo mejorado
        all_regions = []
        for page_num in range(self.start_page, self.end_page + 1):
            self.logger.info(f"📄 Procesando página {page_num} con mapeo mejorado")

            page_regions = self._process_page_enhanced(page_num, preprocessed_text)
            all_regions.extend(page_regions)

        # Organizar por tipo de contenido
        result = self._organize_by_content_type(all_regions, result)

        # Generar resumen del procesamiento
        result["processing_summary"] = self._generate_processing_summary(all_regions)

        self.logger.info("✅ Procesamiento mejorado completado")
        return result

    def _preprocess_raw_text(self, raw_text: str) -> Dict:
        """Preprocesa el raw text para mejorar el mapeo."""

        # Normalizar espacios y saltos de línea
        normalized_text = re.sub(r'\s+', ' ', raw_text)

        # Crear índice de palabras para búsqueda rápida
        word_index = {}
        words = normalized_text.lower().split()

        for i, word in enumerate(words):
            if word not in word_index:
                word_index[word] = []
            word_index[word].append(i)

        # Identificar secciones principales
        section_patterns = {
            'd.1': r'd\.1\s+origen\s+y\s+causa\s+de\s+la\s+falla',
            'd.2': r'd\.2\s+fenómeno\s+físico',
            'd.3': r'd\.3\s+reiteración',
            'd.4': r'd\.4\s+fenómeno\s+eléctrico'
        }

        sections = {}
        for section_id, pattern in section_patterns.items():
            match = re.search(pattern, normalized_text.lower())
            if match:
                sections[section_id] = {
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "title": match.group(0)
                }

        return {
            "original": raw_text,
            "normalized": normalized_text,
            "word_index": word_index,
            "sections": sections,
            "total_words": len(words),
            "total_chars": len(normalized_text)
        }

    def _process_page_enhanced(self, page_num: int, preprocessed_text: Dict) -> List[Dict]:
        """Procesa una página con mapeo mejorado."""

        regions = []

        try:
            # Extraer coordenadas de la página
            coord_data = self.coordinate_extractor.extract_page_with_coordinates(page_num)

            if "error" in coord_data:
                self.logger.warning(f"Error en página {page_num}: {coord_data['error']}")
                return regions

            # Procesar bloques de texto
            text_blocks = [block for block in coord_data["blocks"] if block["block_type"] == "text"]

            for i, block in enumerate(text_blocks):
                region = self._create_enhanced_region(block, i, page_num, preprocessed_text)
                if region and region["content"]["text"].strip():
                    regions.append(region)

        except Exception as e:
            self.logger.error(f"Error procesando página {page_num}: {e}")

        return regions

    def _create_enhanced_region(self, block: Dict, block_index: int, page_num: int, preprocessed_text: Dict) -> Optional[Dict]:
        """Crea una región con mapeo mejorado al raw text."""

        # Extraer texto del bloque
        block_text = self._extract_clean_text_from_block(block)

        if not block_text or len(block_text.strip()) < 5:
            return None

        # Buscar coincidencia mejorada en raw text
        text_match = self._find_enhanced_text_match(block_text, preprocessed_text)

        # Clasificar contenido con contexto
        content_classification = self._classify_content_enhanced(block_text, text_match, page_num)

        # Crear región enriquecida
        region = {
            "region_id": f"page_{page_num}_block_{block_index}",
            "page_number": page_num,
            "content_type": content_classification["type"],
            "content_subtype": content_classification["subtype"],
            "bbox": block["bbox"],
            "content": {
                "text": block_text,
                "cleaned_text": self._clean_text_for_analysis(block_text),
                "raw_text_mapping": text_match,
                "context": content_classification["context"]
            },
            "formatting": self._extract_detailed_formatting(block),
            "structure": {
                "hierarchy_level": content_classification["hierarchy_level"],
                "section_belongs_to": content_classification["section"],
                "is_header": content_classification["is_header"],
                "is_data": content_classification["is_data"]
            },
            "confidence": self._calculate_enhanced_confidence(text_match, content_classification)
        }

        return region

    def _extract_clean_text_from_block(self, block: Dict) -> str:
        """Extrae texto limpio de un bloque de coordenadas."""

        text_lines = []
        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                span_text = span.get("text", "").strip()
                if span_text:
                    line_text += span_text + " "

            clean_line = line_text.strip()
            if clean_line:
                text_lines.append(clean_line)

        return "\n".join(text_lines)

    def _find_enhanced_text_match(self, block_text: str, preprocessed_text: Dict) -> Dict:
        """Encuentra coincidencia mejorada en el raw text."""

        normalized_block = re.sub(r'\s+', ' ', block_text.strip().lower())
        normalized_raw = preprocessed_text["normalized"].lower()

        # Buscar coincidencia exacta primero
        exact_pos = normalized_raw.find(normalized_block)
        if exact_pos != -1:
            return {
                "found": True,
                "match_type": "exact",
                "start_position": exact_pos,
                "end_position": exact_pos + len(normalized_block),
                "similarity_score": 1.0,
                "matched_text": normalized_block,
                "context_before": normalized_raw[max(0, exact_pos-100):exact_pos],
                "context_after": normalized_raw[exact_pos+len(normalized_block):exact_pos+len(normalized_block)+100]
            }

        # Buscar coincidencia por palabras clave
        block_words = normalized_block.split()
        if len(block_words) >= 3:
            # Probar con las primeras 5-7 palabras
            for word_count in [7, 5, 3]:
                if len(block_words) >= word_count:
                    key_phrase = " ".join(block_words[:word_count])
                    phrase_pos = normalized_raw.find(key_phrase)
                    if phrase_pos != -1:
                        # Calcular similitud con el contexto completo
                        context_end = min(phrase_pos + len(normalized_block) + 50, len(normalized_raw))
                        context_text = normalized_raw[phrase_pos:context_end]

                        similarity = SequenceMatcher(None, normalized_block, context_text).ratio()

                        return {
                            "found": True,
                            "match_type": "partial_phrase",
                            "start_position": phrase_pos,
                            "similarity_score": similarity,
                            "matched_words": word_count,
                            "total_words": len(block_words),
                            "key_phrase": key_phrase,
                            "context_text": context_text
                        }

        # Búsqueda por similitud de fragmentos
        best_match = self._find_similarity_match(normalized_block, normalized_raw)
        if best_match:
            return best_match

        return {
            "found": False,
            "match_type": "none",
            "search_attempted": normalized_block[:100],
            "similarity_score": 0.0
        }

    def _find_similarity_match(self, block_text: str, raw_text: str) -> Optional[Dict]:
        """Encuentra coincidencia por similitud."""

        best_match = None
        best_score = 0.0
        best_position = -1

        # Dividir el raw text en chunks del tamaño aproximado del bloque
        chunk_size = max(len(block_text), 100)
        overlap = chunk_size // 4

        for i in range(0, len(raw_text) - chunk_size + 1, chunk_size - overlap):
            chunk = raw_text[i:i + chunk_size]
            similarity = SequenceMatcher(None, block_text, chunk).ratio()

            if similarity > best_score and similarity > 0.4:  # Umbral mínimo de similitud
                best_score = similarity
                best_position = i
                best_match = chunk

        if best_match:
            return {
                "found": True,
                "match_type": "similarity",
                "start_position": best_position,
                "similarity_score": best_score,
                "matched_text": best_match,
                "threshold_used": 0.4
            }

        return None

    def _classify_content_enhanced(self, text: str, text_match: Dict, page_num: int) -> Dict:
        """Clasifica contenido con análisis mejorado."""

        text_lower = text.lower().strip()

        # Detectar nivel de jerarquía
        hierarchy_level = 0
        section = "unknown"
        is_header = False
        content_type = "paragraph"
        content_subtype = "general"

        # Análisis de encabezados principales
        if re.match(r'^d\.\d+', text_lower):
            hierarchy_level = 1
            is_header = True
            content_type = "section_header"
            content_subtype = "main_section"

            # Identificar sección específica
            if "origen y causa" in text_lower:
                section = "d.1_origen_causa"
            elif "fenómeno físico" in text_lower:
                section = "d.2_fenomeno_fisico"
            elif "reiteración" in text_lower:
                section = "d.3_reiteracion"
            elif "fenómeno eléctrico" in text_lower:
                section = "d.4_fenomeno_electrico"

        # Análisis de subsecciones
        elif re.match(r'^d\.\d+\.\d+', text_lower):
            hierarchy_level = 2
            is_header = True
            content_type = "subsection_header"

        # Análisis de contenido técnico
        elif any(unit in text_lower for unit in ["mw", "mva", "kv", "hz", "°c", "amp", "var"]):
            content_type = "technical_data"
            if any(time_pattern in text for time_pattern in [r'\d{2}:\d{2}', r'\d{2}/\d{2}/\d{4}']):
                content_subtype = "temporal_technical"
            else:
                content_subtype = "measurement"

        # Análisis cronológico
        elif re.search(r'\d{2}:\d{2}|\d{1,2}\s+de\s+\w+\s+de\s+\d{4}', text):
            content_type = "chronological_event"
            if "horas" in text_lower and ("apertura" in text_lower or "desconexión" in text_lower):
                content_subtype = "fault_event"
            else:
                content_subtype = "timeline"

        # Análisis de entidades organizacionales
        elif any(org in text_lower for org in ["s/e", "empresa", "enel", "colbún", "coordinador"]):
            content_type = "organizational_info"
            if "s/e" in text_lower:
                content_subtype = "substation"
            else:
                content_subtype = "company"

        # Análisis de tablas y datos estructurados
        elif self._is_tabular_content(text):
            content_type = "table_data"
            content_subtype = "structured_data"

        # Contexto adicional basado en la página
        context = self._determine_page_context(page_num, text_lower)

        return {
            "type": content_type,
            "subtype": content_subtype,
            "hierarchy_level": hierarchy_level,
            "section": section,
            "is_header": is_header,
            "is_data": content_type in ["technical_data", "table_data"],
            "context": context
        }

    def _is_tabular_content(self, text: str) -> bool:
        """Detecta si el contenido es tabular."""
        lines = text.split('\n')

        # Verificar formato de tabla
        table_indicators = 0

        for line in lines:
            # Detectar separadores de columnas
            if len(line.split()) >= 3:  # Al menos 3 columnas
                table_indicators += 1
            # Detectar datos numéricos tabulares
            if re.search(r'\d+\.\d+|\d+,\d+', line):
                table_indicators += 1

        return table_indicators >= 2

    def _determine_page_context(self, page_num: int, text: str) -> Dict:
        """Determina el contexto basado en la página y contenido."""

        page_contexts = {
            1: "chapter_introduction",
            2: "fault_origin_analysis",
            3: "technical_phenomena",
            4: "electrical_analysis",
            5: "system_behavior",
            6: "consequences_analysis",
            7: "recovery_procedures",
            8: "detailed_measurements",
            9: "protection_analysis",
            10: "regulatory_compliance",
            11: "conclusions_summary"
        }

        base_context = page_contexts.get(page_num, "general_content")

        # Añadir contexto específico del contenido
        content_context = {
            "base_context": base_context,
            "has_timestamps": bool(re.search(r'\d{2}:\d{2}', text)),
            "has_measurements": bool(re.search(r'\d+\s*(mw|kv|hz)', text, re.IGNORECASE)),
            "has_equipment": bool(re.search(r'52k\d+|s/e|línea|circuito', text, re.IGNORECASE)),
            "importance_level": self._assess_content_importance(text)
        }

        return content_context

    def _assess_content_importance(self, text: str) -> str:
        """Evalúa la importancia del contenido."""

        high_importance_keywords = ["apertura intempestiva", "falla", "colapso", "desconexión", "islas eléctricas"]
        medium_importance_keywords = ["oscilaciones", "protecciones", "reconexión", "automatismo"]

        text_lower = text.lower()

        if any(keyword in text_lower for keyword in high_importance_keywords):
            return "high"
        elif any(keyword in text_lower for keyword in medium_importance_keywords):
            return "medium"
        else:
            return "low"

    def _extract_detailed_formatting(self, block: Dict) -> Dict:
        """Extrae información detallada de formato."""

        formatting = {
            "fonts": [],
            "sizes": [],
            "colors": [],
            "styles": {"bold": False, "italic": False, "underline": False},
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

                # Analizar flags de estilo
                flags = span.get("flags", 0)
                if flags & 16:  # Bold
                    formatting["styles"]["bold"] = True
                if flags & 2:   # Italic
                    formatting["styles"]["italic"] = True

        # Determinar estilo dominante
        if formatting["fonts"]:
            formatting["dominant_style"]["font"] = max(set(formatting["fonts"]), key=formatting["fonts"].count)
        if formatting["sizes"]:
            formatting["dominant_style"]["size"] = max(set(formatting["sizes"]), key=formatting["sizes"].count)

        return formatting

    def _clean_text_for_analysis(self, text: str) -> str:
        """Limpia texto para análisis."""
        # Normalizar espacios
        cleaned = re.sub(r'\s+', ' ', text.strip())

        # Normalizar puntuación
        cleaned = re.sub(r'([.,:;])\s*', r'\1 ', cleaned)

        return cleaned

    def _calculate_enhanced_confidence(self, text_match: Dict, classification: Dict) -> float:
        """Calcula confianza mejorada."""

        confidence = 0.0

        # Confianza del mapeo de texto
        if text_match["found"]:
            if text_match["match_type"] == "exact":
                confidence += 0.5
            elif text_match["match_type"] == "partial_phrase":
                confidence += 0.3 * text_match.get("similarity_score", 0.5)
            elif text_match["match_type"] == "similarity":
                confidence += 0.2 * text_match.get("similarity_score", 0.3)

        # Confianza de la clasificación
        if classification["is_header"]:
            confidence += 0.3
        elif classification["is_data"]:
            confidence += 0.25
        else:
            confidence += 0.15

        # Bonus por contexto
        if classification["context"]["importance_level"] == "high":
            confidence += 0.1

        return min(confidence, 1.0)

    def _organize_by_content_type(self, regions: List[Dict], result: Dict) -> Dict:
        """Organiza las regiones por tipo de contenido."""

        for region in regions:
            content_type = region["content_type"]
            region_data = {
                "page": region["page_number"],
                "text": region["content"]["text"],
                "context": region["structure"],
                "confidence": region["confidence"],
                "bbox": region["bbox"]
            }

            # Organizar por secciones
            if content_type == "section_header":
                section_id = region["structure"]["section_belongs_to"]
                if section_id not in result["content_by_sections"]:
                    result["content_by_sections"][section_id] = {
                        "header": region_data,
                        "content": [],
                        "subsections": {}
                    }
                else:
                    result["content_by_sections"][section_id]["header"] = region_data

            # Eventos cronológicos
            elif content_type == "chronological_event":
                event_id = f"event_{len(result['chronological_events'])}"
                result["chronological_events"][event_id] = region_data

            # Parámetros técnicos
            elif content_type == "technical_data":
                param_id = f"param_{len(result['technical_parameters'])}"
                result["technical_parameters"][param_id] = region_data

            # Entidades organizacionales
            elif content_type == "organizational_info":
                org_id = f"org_{len(result['organizational_entities'])}"
                result["organizational_entities"][org_id] = region_data

            # Tablas y datos
            elif content_type == "table_data":
                table_id = f"table_{len(result['tables_and_data'])}"
                result["tables_and_data"][table_id] = region_data

            # Contenido de sección (párrafos)
            elif content_type == "paragraph":
                section_belongs = region["structure"]["section_belongs_to"]
                if section_belongs in result["content_by_sections"]:
                    result["content_by_sections"][section_belongs]["content"].append(region_data)

        return result

    def _generate_processing_summary(self, regions: List[Dict]) -> Dict:
        """Genera resumen del procesamiento."""

        summary = {
            "total_regions_processed": len(regions),
            "regions_by_type": {},
            "confidence_stats": {
                "high_confidence": 0,  # > 0.8
                "medium_confidence": 0,  # 0.5 - 0.8
                "low_confidence": 0     # < 0.5
            },
            "text_matching_stats": {
                "exact_matches": 0,
                "partial_matches": 0,
                "similarity_matches": 0,
                "no_matches": 0
            },
            "content_distribution": {},
            "quality_metrics": {}
        }

        for region in regions:
            content_type = region["content_type"]
            confidence = region["confidence"]
            match_type = region["content"]["raw_text_mapping"]["match_type"]

            # Contar por tipo
            if content_type not in summary["regions_by_type"]:
                summary["regions_by_type"][content_type] = 0
            summary["regions_by_type"][content_type] += 1

            # Estadísticas de confianza
            if confidence > 0.8:
                summary["confidence_stats"]["high_confidence"] += 1
            elif confidence > 0.5:
                summary["confidence_stats"]["medium_confidence"] += 1
            else:
                summary["confidence_stats"]["low_confidence"] += 1

            # Estadísticas de matching
            if match_type == "exact":
                summary["text_matching_stats"]["exact_matches"] += 1
            elif match_type in ["partial_phrase", "partial"]:
                summary["text_matching_stats"]["partial_matches"] += 1
            elif match_type == "similarity":
                summary["text_matching_stats"]["similarity_matches"] += 1
            else:
                summary["text_matching_stats"]["no_matches"] += 1

        # Métricas de calidad
        total_regions = len(regions)
        if total_regions > 0:
            summary["quality_metrics"] = {
                "match_success_rate": (total_regions - summary["text_matching_stats"]["no_matches"]) / total_regions,
                "high_confidence_rate": summary["confidence_stats"]["high_confidence"] / total_regions,
                "exact_match_rate": summary["text_matching_stats"]["exact_matches"] / total_regions
            }

        return summary


def main():
    """Demo del procesador mejorado."""
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

    print("🚀 INICIANDO PROCESAMIENTO MEJORADO")
    print("=" * 60)

    # Crear procesador mejorado
    processor = EnhancedRegionProcessor(str(pdf_path), start_page=1, end_page=11)

    # Procesar con mapeo mejorado
    result = processor.process_with_enhanced_mapping(raw_text)

    # Guardar resultado
    output_path = base_path.parent / "outputs" / "universal_json" / "capitulo_01_enhanced_regions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"💾 Resultado guardado en: {output_path}")
    print("\n📊 RESUMEN DEL PROCESAMIENTO MEJORADO:")

    summary = result["processing_summary"]
    print(f"🎯 Total regiones procesadas: {summary['total_regions_processed']}")
    print(f"📝 Tipos de contenido encontrados: {len(summary['regions_by_type'])}")

    print("\n📈 ESTADÍSTICAS DE COINCIDENCIAS:")
    match_stats = summary["text_matching_stats"]
    print(f"✅ Coincidencias exactas: {match_stats['exact_matches']}")
    print(f"🔍 Coincidencias parciales: {match_stats['partial_matches']}")
    print(f"📊 Coincidencias por similitud: {match_stats['similarity_matches']}")
    print(f"❌ Sin coincidencias: {match_stats['no_matches']}")

    print("\n🎯 MÉTRICAS DE CALIDAD:")
    quality = summary["quality_metrics"]
    print(f"📈 Tasa de éxito en mapeo: {quality['match_success_rate']:.1%}")
    print(f"⭐ Tasa de alta confianza: {quality['high_confidence_rate']:.1%}")
    print(f"🎯 Tasa de coincidencias exactas: {quality['exact_match_rate']:.1%}")

    print(f"\n📂 ORGANIZACIÓN POR SECCIONES:")
    for section_id, section_data in result["content_by_sections"].items():
        content_count = len(section_data.get("content", []))
        print(f"📑 {section_id}: {content_count} elementos de contenido")

    print("\n" + "=" * 60)
    print("✅ PROCESAMIENTO MEJORADO COMPLETADO")


if __name__ == "__main__":
    main()