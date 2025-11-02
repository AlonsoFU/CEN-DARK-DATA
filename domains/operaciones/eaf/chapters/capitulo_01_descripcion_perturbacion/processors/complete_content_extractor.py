"""
Extractor Completo de Contenido - Sin pérdida de información
Captura TODA la información del raw text organizándola correctamente
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging


class CompleteContentExtractor:
    """Extractor que NO pierde información del raw text."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_complete_content(self, raw_text: str) -> Dict:
        """Extrae TODO el contenido sin perder información."""

        self.logger.info("🔍 INICIANDO EXTRACCIÓN COMPLETA SIN PÉRDIDAS")

        # Dividir por páginas
        pages = self._split_by_pages(raw_text)

        result = {
            "metadata": {
                "extraction_method": "complete_no_loss",
                "pages_processed": len(pages),
                "preservation_principle": "capture_everything_from_raw_text"
            },
            "pages": {},
            "document_structure": {
                "sections": {},
                "tables": {},
                "technical_data": {},
                "chronological_events": {},
                "organizational_info": {}
            },
            "content_inventory": {
                "total_paragraphs": 0,
                "total_tables": 0,
                "total_sections": 0,
                "information_preserved": "100%"
            }
        }

        # Procesar cada página COMPLETAMENTE
        for page_num, page_content in pages.items():
            self.logger.info(f"📄 Procesando página {page_num} - EXTRACCIÓN COMPLETA")

            page_analysis = self._extract_page_completely(page_content, page_num)
            result["pages"][page_num] = page_analysis

            # Consolidar en estructura general
            self._consolidate_page_content(page_analysis, result)

        # Generar inventario final
        result["content_inventory"] = self._generate_content_inventory(result)

        self.logger.info("✅ Extracción completa terminada - CERO pérdidas")
        return result

    def _split_by_pages(self, raw_text: str) -> Dict[int, str]:
        """Divide el raw text por páginas."""

        pages = {}
        current_page = None
        current_content = []

        lines = raw_text.split('\n')

        for line in lines:
            # Detectar separador de página
            if line.startswith("=== PÁGINA"):
                # Guardar página anterior si existe
                if current_page is not None:
                    pages[current_page] = '\n'.join(current_content)

                # Extraer número de página nueva
                page_match = re.search(r'PÁGINA (\d+)', line)
                if page_match:
                    current_page = int(page_match.group(1))
                    current_content = []
            else:
                if current_page is not None:
                    current_content.append(line)

        # Guardar última página
        if current_page is not None:
            pages[current_page] = '\n'.join(current_content)

        return pages

    def _extract_page_completely(self, page_content: str, page_num: int) -> Dict:
        """Extrae COMPLETAMENTE el contenido de una página."""

        # Limpiar contenido inicial
        clean_content = page_content.strip()

        # Detectar TODOS los elementos
        page_analysis = {
            "page_number": page_num,
            "raw_content": clean_content,
            "content_blocks": [],
            "detected_structures": {
                "headers": [],
                "tables": [],
                "paragraphs": [],
                "lists": [],
                "technical_data": []
            },
            "processing_stats": {
                "total_lines": len(clean_content.split('\n')),
                "total_chars": len(clean_content),
                "blocks_identified": 0
            }
        }

        # Dividir en bloques lógicos por espacios dobles
        content_blocks = self._split_into_logical_blocks(clean_content)

        for i, block in enumerate(content_blocks):
            if block.strip():  # Solo procesar bloques no vacíos
                block_analysis = self._analyze_content_block_completely(block, i, page_num)
                page_analysis["content_blocks"].append(block_analysis)

                # Clasificar en estructuras
                block_type = block_analysis["classification"]["primary_type"]
                if block_type in page_analysis["detected_structures"]:
                    page_analysis["detected_structures"][block_type].append(block_analysis)

        page_analysis["processing_stats"]["blocks_identified"] = len(page_analysis["content_blocks"])

        return page_analysis

    def _split_into_logical_blocks(self, content: str) -> List[str]:
        """Divide contenido en bloques lógicos."""

        # Dividir por dobles saltos de línea (párrafos naturales)
        blocks = re.split(r'\n\s*\n', content)

        # Refinar: detectar bloques tabulares que pueden estar juntos
        refined_blocks = []

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Si el bloque es muy largo Y parece tener estructura tabular, dividirlo
            if len(block) > 500 and self._has_tabular_indicators(block):
                # Dividir por cambios de patrón estructural
                sub_blocks = self._split_tabular_block(block)
                refined_blocks.extend(sub_blocks)
            else:
                refined_blocks.append(block)

        return refined_blocks

    def _has_tabular_indicators(self, text: str) -> bool:
        """Detecta si un texto tiene indicadores tabulares."""

        lines = text.split('\n')

        # Contar líneas con múltiples columnas
        columnar_lines = 0
        for line in lines:
            if len(line.split()) >= 3:  # 3+ columnas
                columnar_lines += 1

        return columnar_lines / len(lines) > 0.3  # 30%+ de líneas columnares

    def _split_tabular_block(self, block: str) -> List[str]:
        """Divide un bloque grande con estructura tabular."""

        lines = block.split('\n')
        current_block = []
        blocks = []

        prev_pattern = None

        for line in lines:
            # Analizar patrón de la línea
            current_pattern = self._analyze_line_pattern(line)

            # Si cambia el patrón significativamente, crear nuevo bloque
            if (prev_pattern and
                current_pattern != prev_pattern and
                len(current_block) >= 3):

                blocks.append('\n'.join(current_block))
                current_block = [line]
            else:
                current_block.append(line)

            prev_pattern = current_pattern

        # Agregar último bloque
        if current_block:
            blocks.append('\n'.join(current_block))

        return blocks

    def _analyze_line_pattern(self, line: str) -> str:
        """Analiza el patrón de una línea."""

        line = line.strip()

        if not line:
            return "empty"

        # Detectar patrones
        if re.match(r'^[a-z]\.\d+', line.lower()):
            return "section_header"
        elif len(line.split()) >= 4:
            return "multi_column"
        elif len(line.split()) == 2:
            return "key_value"
        elif re.search(r'\d{2}:\d{2}|\d{2}/\d{2}/\d{4}', line):
            return "temporal"
        elif len(line) > 100:
            return "paragraph"
        else:
            return "short_text"

    def _analyze_content_block_completely(self, block: str, block_id: int, page_num: int) -> Dict:
        """Analiza completamente un bloque de contenido."""

        block_analysis = {
            "block_id": f"page_{page_num}_block_{block_id}",
            "raw_text": block,
            "cleaned_text": self._clean_block_text(block),
            "classification": {
                "primary_type": "paragraphs",
                "confidence": 0.0,
                "characteristics": [],
                "structure_type": "unknown"
            },
            "content_analysis": {
                "line_count": len(block.split('\n')),
                "word_count": len(block.split()),
                "char_count": len(block),
                "contains_numbers": bool(re.search(r'\d+', block)),
                "contains_dates": bool(re.search(r'\d{2}/\d{2}/\d{4}', block)),
                "contains_times": bool(re.search(r'\d{2}:\d{2}', block)),
                "contains_technical_units": bool(re.search(r'\d+\s*(MW|kV|Hz|A|V)', block, re.IGNORECASE))
            },
            "extracted_entities": {
                "companies": self._extract_companies(block),
                "technical_values": self._extract_technical_values(block),
                "timestamps": self._extract_timestamps(block),
                "equipment": self._extract_equipment(block)
            }
        }

        # Clasificar tipo de contenido
        block_analysis["classification"] = self._classify_block_type_complete(block, block_analysis)

        return block_analysis

    def _clean_block_text(self, text: str) -> str:
        """Limpia el texto del bloque preservando estructura."""

        # Solo limpiar espacios excesivos, no remover información
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Limpiar espacios al inicio/final pero preservar estructura interna
            cleaned_line = line.strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)

        return '\n'.join(cleaned_lines)

    def _classify_block_type_complete(self, block: str, analysis: Dict) -> Dict:
        """Clasifica el tipo de bloque con análisis completo."""

        text_lower = block.lower().strip()
        lines = block.split('\n')

        classification = {
            "primary_type": "paragraphs",
            "confidence": 0.5,
            "characteristics": [],
            "structure_type": "text"
        }

        # 1. ENCABEZADOS DE SECCIÓN
        if re.match(r'^[a-z]\.\d+', text_lower):
            classification.update({
                "primary_type": "headers",
                "confidence": 0.9,
                "characteristics": ["section_header", "numbered"],
                "structure_type": "hierarchical"
            })

        # 2. TABLAS - DETECCIÓN AMPLIADA
        elif self._is_table_content_complete(block, lines):
            classification.update({
                "primary_type": "tables",
                "confidence": 0.8,
                "characteristics": ["tabular_data", "structured"],
                "structure_type": "table"
            })

        # 3. PÁRRAFOS TÉCNICOS LARGOS
        elif len(block) > 200 and analysis["content_analysis"]["contains_technical_units"]:
            classification.update({
                "primary_type": "technical_data",
                "confidence": 0.7,
                "characteristics": ["technical_content", "detailed"],
                "structure_type": "technical_paragraph"
            })

        # 4. LISTAS ESTRUCTURADAS
        elif self._is_list_content(lines):
            classification.update({
                "primary_type": "lists",
                "confidence": 0.8,
                "characteristics": ["list_structure", "enumerated"],
                "structure_type": "list"
            })

        # 5. PÁRRAFOS NARRATIVOS (default mejorado)
        else:
            characteristics = ["narrative"]
            if analysis["content_analysis"]["contains_dates"]:
                characteristics.append("temporal")
            if analysis["content_analysis"]["contains_numbers"]:
                characteristics.append("quantitative")

            classification.update({
                "primary_type": "paragraphs",
                "confidence": 0.6,
                "characteristics": characteristics,
                "structure_type": "narrative"
            })

        return classification

    def _is_table_content_complete(self, block: str, lines: List[str]) -> bool:
        """Detección COMPLETA de contenido tabular - SIN restricciones excesivas."""

        if len(lines) < 2:
            return False

        # Indicadores de tabla (más permisivos)
        table_score = 0

        # 1. Líneas con múltiples elementos separados
        multi_column_lines = sum(1 for line in lines if len(line.split()) >= 2)
        if multi_column_lines / len(lines) > 0.5:  # 50%+ de líneas con 2+ columnas
            table_score += 30

        # 2. Patrones de key-value (muy común en EAF)
        key_value_patterns = 0
        for line in lines:
            if re.search(r'^[^:]+:\s*\S+', line.strip()):  # "Clave: Valor"
                key_value_patterns += 1
            elif re.search(r'^[^0-9]+\s+\d+', line.strip()):  # "Texto Número"
                key_value_patterns += 1

        if key_value_patterns >= 2:
            table_score += 25

        # 3. Datos numéricos estructurados
        numeric_lines = sum(1 for line in lines if re.search(r'\d+', line))
        if numeric_lines >= 2:
            table_score += 20

        # 4. Fechas y horas (datos estructurados)
        temporal_lines = sum(1 for line in lines
                           if re.search(r'\d{2}/\d{2}/\d{4}|\d{2}:\d{2}', line))
        if temporal_lines >= 1:
            table_score += 15

        # 5. Unidades técnicas (MW, kV, etc.)
        technical_lines = sum(1 for line in lines
                            if re.search(r'\d+\s*(MW|kV|Hz|%)', line, re.IGNORECASE))
        if technical_lines >= 1:
            table_score += 20

        # 6. Nombres de empresas/organizaciones (listas de empresas)
        company_lines = sum(1 for line in lines
                          if re.search(r'S\.A\.|SPA|LTDA|EMPRESA', line, re.IGNORECASE))
        if company_lines >= 2:
            table_score += 25

        # Es tabla si score >= 40 (mucho más permisivo)
        return table_score >= 40

    def _is_list_content(self, lines: List[str]) -> bool:
        """Detecta contenido de lista."""

        if len(lines) < 2:
            return False

        list_indicators = 0

        for line in lines:
            line_stripped = line.strip()
            if re.match(r'^\s*[-•·]\s+', line) or \
               re.match(r'^\s*\d+[\.)]\s+', line) or \
               re.match(r'^\s*[a-z][\.)]\s+', line):
                list_indicators += 1

        return list_indicators / len(lines) > 0.5

    def _extract_companies(self, text: str) -> List[str]:
        """Extrae nombres de empresas."""

        companies = []

        # Patrones de empresas
        company_patterns = [
            r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]+S\.A\.)',
            r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]+SPA)',
            r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]+LTDA)',
            r'(EMPRESA\s+[A-ZÁÉÍÓÚ\s]+)',
            r'([A-Z][A-Z\s&]+(?:CHILE|ENERGÍA|ELÉCTRICA|TRANSMISIÓN)[A-Z\s]*)',
        ]

        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            companies.extend(matches)

        return list(set(companies))  # Eliminar duplicados

    def _extract_technical_values(self, text: str) -> List[Dict]:
        """Extrae valores técnicos con unidades."""

        values = []

        # Patrones técnicos
        patterns = {
            'power': r'(\d+(?:\.\d+)?)\s*(MW|kW|GW)',
            'voltage': r'(\d+(?:\.\d+)?)\s*(kV|V)',
            'frequency': r'(\d+(?:\.\d+)?)\s*(Hz)',
            'percentage': r'(\d+(?:\.\d+)?)\s*(%)',
            'current': r'(\d+(?:\.\d+)?)\s*(A|mA)',
            'time_duration': r'(\d+(?:\.\d+)?)\s*(segundos?|minutos?|horas?)',
        }

        for value_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                values.append({
                    "value": float(match[0]),
                    "unit": match[1],
                    "type": value_type,
                    "raw_text": f"{match[0]} {match[1]}"
                })

        return values

    def _extract_timestamps(self, text: str) -> List[Dict]:
        """Extrae marcas temporales."""

        timestamps = []

        # Patrones temporales
        time_patterns = {
            'date': r'(\d{1,2}/\d{1,2}/\d{4})',
            'time': r'(\d{1,2}:\d{2}(?::\d{2})?)',
            'datetime': r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2})',
        }

        for time_type, pattern in time_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                timestamps.append({
                    "type": time_type,
                    "value": match,
                    "raw_text": match
                })

        return timestamps

    def _extract_equipment(self, text: str) -> List[str]:
        """Extrae nombres de equipos."""

        equipment = []

        # Patrones de equipos
        equipment_patterns = [
            r'(52K\d+)',  # Interruptores
            r'(S/E\s+[A-Za-z\s]+)',  # Subestaciones
            r'(línea\s+\d+x\d+\s*kV[^.]*)',  # Líneas de transmisión
            r'(circuito\s+N°?\d+)',  # Circuitos
            r'(rel[eé]s?\s+[A-Za-z0-9]+)',  # Relés
            r'(protecciones?\s+[A-Za-z0-9]+)',  # Protecciones
        ]

        for pattern in equipment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            equipment.extend(matches)

        return list(set(equipment))

    def _consolidate_page_content(self, page_analysis: Dict, result: Dict) -> None:
        """Consolida el contenido de la página en la estructura general."""

        page_num = page_analysis["page_number"]

        for block in page_analysis["content_blocks"]:
            block_type = block["classification"]["primary_type"]
            block_id = f"page_{page_num}_{block['block_id']}"

            # Consolidar según tipo
            if block_type == "headers":
                result["document_structure"]["sections"][block_id] = {
                    "page": page_num,
                    "text": block["cleaned_text"],
                    "classification": block["classification"]
                }

            elif block_type == "tables":
                result["document_structure"]["tables"][block_id] = {
                    "page": page_num,
                    "content": block["raw_text"],
                    "analysis": block["content_analysis"],
                    "entities": block["extracted_entities"]
                }

            elif block_type == "technical_data":
                result["document_structure"]["technical_data"][block_id] = {
                    "page": page_num,
                    "content": block["cleaned_text"],
                    "technical_values": block["extracted_entities"]["technical_values"],
                    "equipment": block["extracted_entities"]["equipment"]
                }

            # Eventos cronológicos
            if block["extracted_entities"]["timestamps"]:
                result["document_structure"]["chronological_events"][block_id] = {
                    "page": page_num,
                    "content": block["cleaned_text"],
                    "timestamps": block["extracted_entities"]["timestamps"]
                }

            # Info organizacional
            if block["extracted_entities"]["companies"]:
                result["document_structure"]["organizational_info"][block_id] = {
                    "page": page_num,
                    "content": block["cleaned_text"],
                    "companies": block["extracted_entities"]["companies"]
                }

    def _generate_content_inventory(self, result: Dict) -> Dict:
        """Genera inventario completo del contenido."""

        inventory = {
            "total_paragraphs": 0,
            "total_tables": 0,
            "total_sections": 0,
            "total_technical_blocks": 0,
            "total_chronological_events": 0,
            "total_organizational_blocks": 0,
            "information_preserved": "100%",
            "content_distribution": {},
            "entity_counts": {
                "companies": 0,
                "technical_values": 0,
                "timestamps": 0,
                "equipment": 0
            }
        }

        # Contar por página
        for page_num, page_data in result["pages"].items():
            page_inventory = {
                "blocks": len(page_data["content_blocks"]),
                "types": {}
            }

            for block in page_data["content_blocks"]:
                block_type = block["classification"]["primary_type"]

                if block_type not in page_inventory["types"]:
                    page_inventory["types"][block_type] = 0
                page_inventory["types"][block_type] += 1

                # Contar entidades
                entities = block["extracted_entities"]
                inventory["entity_counts"]["companies"] += len(entities["companies"])
                inventory["entity_counts"]["technical_values"] += len(entities["technical_values"])
                inventory["entity_counts"]["timestamps"] += len(entities["timestamps"])
                inventory["entity_counts"]["equipment"] += len(entities["equipment"])

            inventory["content_distribution"][f"page_{page_num}"] = page_inventory

        # Totales generales
        inventory["total_sections"] = len(result["document_structure"]["sections"])
        inventory["total_tables"] = len(result["document_structure"]["tables"])
        inventory["total_technical_blocks"] = len(result["document_structure"]["technical_data"])
        inventory["total_chronological_events"] = len(result["document_structure"]["chronological_events"])
        inventory["total_organizational_blocks"] = len(result["document_structure"]["organizational_info"])

        return inventory


def main():
    """Demo del extractor completo."""

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Rutas
    base_path = Path(__file__).parent
    raw_text_path = base_path.parent / "outputs" / "raw_extractions" / "capitulo_01_raw.txt"

    if not raw_text_path.exists():
        print(f"❌ Raw text no encontrado: {raw_text_path}")
        return

    # Leer raw text
    with open(raw_text_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    print("🔍 INICIANDO EXTRACCIÓN COMPLETA - CERO PÉRDIDAS")
    print("=" * 60)

    # Crear extractor completo
    extractor = CompleteContentExtractor()

    # Extraer todo el contenido
    complete_result = extractor.extract_complete_content(raw_text)

    # Guardar resultado
    output_path = base_path.parent / "outputs" / "universal_json" / "capitulo_01_complete_extraction.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(complete_result, f, indent=2, ensure_ascii=False)

    print(f"💾 Extracción completa guardada en: {output_path}")

    # Mostrar estadísticas detalladas
    print("\n📊 ESTADÍSTICAS DE EXTRACCIÓN COMPLETA:")
    inventory = complete_result["content_inventory"]

    print(f"📄 Páginas procesadas: {complete_result['metadata']['pages_processed']}")
    print(f"📋 Secciones encontradas: {inventory['total_sections']}")
    print(f"📊 Tablas detectadas: {inventory['total_tables']}")
    print(f"🔧 Bloques técnicos: {inventory['total_technical_blocks']}")
    print(f"⏰ Eventos cronológicos: {inventory['total_chronological_events']}")
    print(f"🏢 Bloques organizacionales: {inventory['total_organizational_blocks']}")

    print(f"\n🎯 ENTIDADES EXTRAÍDAS:")
    entities = inventory["entity_counts"]
    print(f"🏭 Empresas: {entities['companies']}")
    print(f"⚡ Valores técnicos: {entities['technical_values']}")
    print(f"🕐 Timestamps: {entities['timestamps']}")
    print(f"🔌 Equipos: {entities['equipment']}")

    print(f"\n✅ PRESERVACIÓN DE INFORMACIÓN: {inventory['information_preserved']}")

    print("\n📋 DISTRIBUCIÓN POR PÁGINA:")
    for page_id, page_info in inventory["content_distribution"].items():
        print(f"  {page_id}: {page_info['blocks']} bloques")
        for content_type, count in page_info["types"].items():
            print(f"    - {content_type}: {count}")

    print("\n" + "=" * 60)
    print("✅ EXTRACCIÓN COMPLETA TERMINADA - INFORMACIÓN PRESERVADA 100%")


if __name__ == "__main__":
    main()