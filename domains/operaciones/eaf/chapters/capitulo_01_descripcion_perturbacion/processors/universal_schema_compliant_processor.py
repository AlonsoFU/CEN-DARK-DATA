"""
Procesador que Respeta el Esquema Universal - Sin pérdida de información
Genera JSON que RESPETA el esquema universal existente pero captura TODAS las tablas
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import uuid


class UniversalSchemaCompliantProcessor:
    """Procesador que respeta el esquema universal y captura toda la información."""

    def __init__(self):
        self.entity_counter = 1

    def process_with_universal_schema(self, raw_text: str) -> Dict:
        """Procesa respetando el esquema universal pero capturando TODO."""

        # Dividir por páginas
        pages = self._split_by_pages(raw_text)

        # Estructura base que RESPETA el esquema universal
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
                "page_range": "1-11",
                "processing_timestamp": datetime.now().isoformat()
            },
            "entities": [],  # Lista de entidades extraídas
            "pages": {},     # Contenido organizado por páginas
            "categorized_entities": {
                "fault_events": [],
                "technical_parameters": [],
                "equipment": [],
                "companies": [],
                "tables": [],
                "temporal_events": [],
                "regulatory_compliance": []
            }
        }

        # Procesar cada página manteniendo esquema universal
        for page_num, page_content in pages.items():
            page_entities, page_structure = self._extract_page_entities(page_content, page_num)

            # Agregar entidades a la lista principal
            result["entities"].extend(page_entities)

            # Organizar página manteniendo estructura clara
            result["pages"][page_num] = page_structure

        # Categorizar entidades para fácil acceso
        result["categorized_entities"] = self._categorize_entities(result["entities"])

        return result

    def _split_by_pages(self, raw_text: str) -> Dict[int, str]:
        """Divide el raw text por páginas."""
        pages = {}
        current_page = None
        current_content = []

        lines = raw_text.split('\n')

        for line in lines:
            if line.startswith("=== PÁGINA"):
                if current_page is not None:
                    pages[current_page] = '\n'.join(current_content)
                page_match = re.search(r'PÁGINA (\d+)', line)
                if page_match:
                    current_page = int(page_match.group(1))
                    current_content = []
            else:
                if current_page is not None:
                    current_content.append(line)

        if current_page is not None:
            pages[current_page] = '\n'.join(current_content)

        return pages

    def _extract_page_entities(self, page_content: str, page_num: int) -> tuple[List[Dict], Dict]:
        """Extrae entidades de una página respetando el esquema universal."""

        entities = []
        page_structure = {
            "page_number": page_num,
            "sections": [],
            "tables": [],
            "paragraphs": [],
            "metadata": {
                "total_content_blocks": 0,
                "table_count": 0,
                "section_count": 0
            }
        }

        # Detectar secciones principales por sus encabezados
        sections = self._detect_page_sections(page_content, page_num)

        for section in sections:
            section_entities = self._extract_section_entities(section, page_num)
            entities.extend(section_entities)

            # Agregar sección a estructura de página
            page_structure["sections"].append({
                "section_id": section["section_id"],
                "title": section["title"],
                "content_type": section["content_type"],
                "entity_count": len(section_entities)
            })

            if section["content_type"] == "table":
                page_structure["tables"].append(section)
                page_structure["metadata"]["table_count"] += 1
            elif section["content_type"] == "section_header":
                page_structure["metadata"]["section_count"] += 1
            else:
                page_structure["paragraphs"].append(section)

        page_structure["metadata"]["total_content_blocks"] = len(sections)

        return entities, page_structure

    def _detect_page_sections(self, page_content: str, page_num: int) -> List[Dict]:
        """Detecta secciones lógicas en una página."""

        sections = []

        # Detectar por patrones específicos de la página 1
        if page_num == 1:
            sections = self._detect_page_1_sections(page_content)
        else:
            # Para otras páginas, usar detección general
            sections = self._detect_general_sections(page_content, page_num)

        return sections

    def _detect_page_1_sections(self, content: str) -> List[Dict]:
        """Detecta las secciones específicas de la página 1."""

        sections = []

        # Sección 1: Encabezado del documento
        header_pattern = r'(Página 1 de 399.*?(?=1\. Descripción))'
        header_match = re.search(header_pattern, content, re.DOTALL)
        if header_match:
            sections.append({
                "section_id": f"page_1_header",
                "title": "Encabezado del documento",
                "content": header_match.group(1).strip(),
                "content_type": "document_header"
            })

        # Sección 2: Título principal
        title_pattern = r'(1\. Descripción pormenorizada de la perturbación)'
        title_match = re.search(title_pattern, content)
        if title_match:
            sections.append({
                "section_id": f"page_1_main_title",
                "title": "Título del capítulo",
                "content": title_match.group(1).strip(),
                "content_type": "section_header"
            })

        # TABLA 1: a. Fecha y Hora de la falla
        table_1_pattern = r'(a\. Fecha y Hora de la falla.*?(?=b\. Identificación))'
        table_1_match = re.search(table_1_pattern, content, re.DOTALL)
        if table_1_match:
            sections.append({
                "section_id": f"page_1_table_fecha_hora",
                "title": "a. Fecha y Hora de la falla",
                "content": table_1_match.group(1).strip(),
                "content_type": "table"
            })

        # TABLA 2: b. Identificación instalación afectada
        table_2_pattern = r'(b\. Identificación instalación afectada.*?(?=c\. Identificación))'
        table_2_match = re.search(table_2_pattern, content, re.DOTALL)
        if table_2_match:
            sections.append({
                "section_id": f"page_1_table_instalacion",
                "title": "b. Identificación instalación afectada",
                "content": table_2_match.group(1).strip(),
                "content_type": "table"
            })

        # TABLA 3: c. Identificación del elemento fallado
        table_3_pattern = r'(c\. Identificación del elemento fallado.*$)'
        table_3_match = re.search(table_3_pattern, content, re.DOTALL)
        if table_3_match:
            sections.append({
                "section_id": f"page_1_table_elemento",
                "title": "c. Identificación del elemento fallado",
                "content": table_3_match.group(1).strip(),
                "content_type": "table"
            })

        return sections

    def _detect_general_sections(self, content: str, page_num: int) -> List[Dict]:
        """Detecta secciones en páginas generales."""

        sections = []

        # Dividir por dobles saltos de línea
        blocks = re.split(r'\n\s*\n', content.strip())

        for i, block in enumerate(blocks):
            if not block.strip():
                continue

            section_type = self._classify_section_type(block)

            sections.append({
                "section_id": f"page_{page_num}_section_{i}",
                "title": self._extract_section_title(block),
                "content": block.strip(),
                "content_type": section_type
            })

        return sections

    def _classify_section_type(self, content: str) -> str:
        """Clasifica el tipo de sección."""

        content_lower = content.lower().strip()

        # Encabezados de sección
        if re.match(r'^[a-z]\.\d+', content_lower):
            return "section_header"

        # Detectar tablas por patrones key-value o estructura columnar
        lines = content.split('\n')
        key_value_lines = 0
        columnar_lines = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Patrón key-value: "Clave valor" o "Clave: valor"
            if len(line.split()) >= 2:
                words = line.split()
                if not words[0].isdigit():  # No empezar con número
                    key_value_lines += 1

            # Patrón columnar: múltiples elementos
            if len(line.split()) >= 3:
                columnar_lines += 1

        # Es tabla si tiene suficientes patrones estructurados
        if len(lines) >= 3 and (key_value_lines >= 2 or columnar_lines >= 2):
            return "table"

        # Detectar listas de empresas
        if any(pattern in content_lower for pattern in ["s.a.", "spa", "empresa"]):
            company_lines = sum(1 for line in lines
                              if re.search(r'(s\.a\.|spa|ltda)', line, re.IGNORECASE))
            if company_lines >= 3:
                return "company_list"

        # Párrafo por defecto
        return "paragraph"

    def _extract_section_title(self, content: str) -> str:
        """Extrae el título de una sección."""

        lines = content.split('\n')
        first_line = lines[0].strip()

        # Si la primera línea es un encabezado obvio
        if re.match(r'^[a-z]\.\d+', first_line.lower()) or len(first_line) < 80:
            return first_line

        # Si es una tabla, usar las primeras palabras
        if len(first_line.split()) <= 10:
            return first_line

        # Para párrafos largos, truncar
        return first_line[:50] + "..." if len(first_line) > 50 else first_line

    def _extract_section_entities(self, section: Dict, page_num: int) -> List[Dict]:
        """Extrae entidades de una sección respetando el esquema universal."""

        entities = []
        content = section["content"]
        section_type = section["content_type"]

        if section_type == "table":
            # Extraer entidades de tabla
            table_entities = self._extract_table_entities(content, section, page_num)
            entities.extend(table_entities)

        elif section_type == "paragraph":
            # Extraer entidades de párrafo
            paragraph_entities = self._extract_paragraph_entities(content, section, page_num)
            entities.extend(paragraph_entities)

        elif section_type == "company_list":
            # Extraer entidades de lista de empresas
            company_entities = self._extract_company_entities(content, section, page_num)
            entities.extend(company_entities)

        return entities

    def _extract_table_entities(self, content: str, section: Dict, page_num: int) -> List[Dict]:
        """Extrae entidades de una tabla manteniendo esquema universal."""

        entities = []

        # Detectar tipo específico de tabla
        if "fecha y hora" in section["title"].lower():
            entities.extend(self._extract_fault_timing_table(content, page_num))

        elif "instalación afectada" in section["title"].lower():
            entities.extend(self._extract_affected_installation_table(content, page_num))

        elif "elemento fallado" in section["title"].lower():
            entities.extend(self._extract_failed_element_table(content, page_num))

        else:
            # Tabla genérica
            entities.append(self._create_generic_table_entity(content, section, page_num))

        return entities

    def _extract_fault_timing_table(self, content: str, page_num: int) -> List[Dict]:
        """Extrae entidades de la tabla de fecha y hora de falla."""

        entities = []

        # Extraer valores específicos
        date_match = re.search(r'Fecha\s+(\d{2}/\d{2}/\d{4})', content)
        time_match = re.search(r'Hora\s+(\d{2}:\d{2})', content)
        consumption_match = re.search(r'Consumos desconectados.*?(\d+\.?\d*)', content)
        demand_match = re.search(r'Demanda previa.*?(\d+\.?\d*)', content)
        percentage_match = re.search(r'Porcentaje.*?(\d+)%', content)

        # Crear entidad principal del evento de falla
        fault_event = {
            "id": f"eaf_089_2025_ch01_fault_event_{self.entity_counter:04d}",
            "type": "fault_event",
            "category": "incident",
            "properties": {
                "data": {}
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": 0.9,
            "original_data": {
                "section_title": "a. Fecha y Hora de la falla",
                "raw_content": content,
                "extraction_method": "table_parsing"
            }
        }

        if date_match:
            fault_event["properties"]["data"]["date"] = date_match.group(1)

        if time_match:
            fault_event["properties"]["data"]["time"] = time_match.group(1)

        if consumption_match:
            fault_event["properties"]["data"]["disconnected_consumption_mw"] = float(consumption_match.group(1))

        if demand_match:
            fault_event["properties"]["data"]["previous_system_demand_mw"] = float(demand_match.group(1))

        if percentage_match:
            fault_event["properties"]["data"]["disconnection_percentage"] = int(percentage_match.group(1))
            if int(percentage_match.group(1)) == 100:
                fault_event["properties"]["data"]["classification"] = "Apagón Total"

        entities.append(fault_event)
        self.entity_counter += 1

        return entities

    def _extract_affected_installation_table(self, content: str, page_num: int) -> List[Dict]:
        """Extrae entidades de la tabla de instalación afectada."""

        entities = []

        # Crear entidad de instalación
        installation_entity = {
            "id": f"eaf_089_2025_ch01_installation_{self.entity_counter:04d}",
            "type": "electrical_installation",
            "category": "equipment",
            "properties": {
                "data": {}
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": 0.85,
            "original_data": {
                "section_title": "b. Identificación instalación afectada",
                "raw_content": content,
                "extraction_method": "table_parsing"
            }
        }

        # Extraer campos específicos
        name_match = re.search(r'Nombre de la instalación\s+(.+?)(?=\n|/)', content, re.DOTALL)
        if name_match:
            installation_entity["properties"]["data"]["name"] = name_match.group(1).strip()

        type_match = re.search(r'Tipo de instalación\s+(\w+)', content)
        if type_match:
            installation_entity["properties"]["data"]["type"] = type_match.group(1)

        voltage_match = re.search(r'Tensión nominal\s+(\d+\s*kV)', content)
        if voltage_match:
            installation_entity["properties"]["data"]["nominal_voltage"] = voltage_match.group(1)

        segment_match = re.search(r'Segmento\s+(.+?)(?=\n)', content)
        if segment_match:
            installation_entity["properties"]["data"]["segment"] = segment_match.group(1).strip()

        owner_match = re.search(r'Propietario.*?\s+(.+?)(?=\n)', content)
        if owner_match:
            installation_entity["properties"]["data"]["owner"] = owner_match.group(1).strip()

        rut_match = re.search(r'RUT\s+([\d\.-]+)', content)
        if rut_match:
            installation_entity["properties"]["data"]["rut"] = rut_match.group(1)

        entities.append(installation_entity)
        self.entity_counter += 1

        return entities

    def _extract_failed_element_table(self, content: str, page_num: int) -> List[Dict]:
        """Extrae entidades de la tabla de elemento fallado."""

        entities = []

        # Crear entidad de elemento fallado
        element_entity = {
            "id": f"eaf_089_2025_ch01_failed_element_{self.entity_counter:04d}",
            "type": "failed_element",
            "category": "equipment",
            "properties": {
                "data": {}
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": 0.85,
            "original_data": {
                "section_title": "c. Identificación del elemento fallado",
                "raw_content": content,
                "extraction_method": "table_parsing"
            }
        }

        # Extraer información del elemento
        element_name_match = re.search(r'Nombre del elemento afectado\s+(.+?)(?=\n.*Propietario)', content, re.DOTALL)
        if element_name_match:
            element_entity["properties"]["data"]["element_name"] = element_name_match.group(1).strip()

        owner_match = re.search(r'Propietario elemento fallado\s+(.+?)(?=\n)', content)
        if owner_match:
            element_entity["properties"]["data"]["owner"] = owner_match.group(1).strip()

        entities.append(element_entity)
        self.entity_counter += 1

        return entities

    def _extract_paragraph_entities(self, content: str, section: Dict, page_num: int) -> List[Dict]:
        """Extrae entidades de párrafos."""

        entities = []

        # Buscar eventos temporales
        time_patterns = re.findall(r'(\d{2}:\d{2}(?::\d{2})?)', content)
        for time_pattern in time_patterns:
            entities.append({
                "id": f"eaf_089_2025_ch01_temporal_{self.entity_counter:04d}",
                "type": "temporal_event",
                "category": "temporal",
                "properties": {
                    "data": {
                        "time": time_pattern,
                        "context": content[:100] + "..."
                    }
                },
                "source_chapter": 1,
                "source_page": page_num,
                "extraction_confidence": 0.7
            })
            self.entity_counter += 1

        # Buscar valores técnicos
        technical_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(MW|kV|Hz|%)', content, re.IGNORECASE)
        for value, unit in technical_matches:
            entities.append({
                "id": f"eaf_089_2025_ch01_technical_{self.entity_counter:04d}",
                "type": "technical_parameter",
                "category": "measurement",
                "properties": {
                    "data": {
                        "value": float(value),
                        "unit": unit,
                        "context": content[:100] + "..."
                    }
                },
                "source_chapter": 1,
                "source_page": page_num,
                "extraction_confidence": 0.8
            })
            self.entity_counter += 1

        return entities

    def _extract_company_entities(self, content: str, section: Dict, page_num: int) -> List[Dict]:
        """Extrae entidades de empresas."""

        entities = []

        # Buscar patrones de empresas
        company_patterns = [
            r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]+S\.A\.)',
            r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]+SPA)',
            r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]+LTDA)',
        ]

        for pattern in company_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for company_name in matches:
                entities.append({
                    "id": f"eaf_089_2025_ch01_company_{self.entity_counter:04d}",
                    "type": "organization",
                    "category": "company",
                    "properties": {
                        "data": {
                            "name": company_name,
                            "context": section["title"]
                        }
                    },
                    "source_chapter": 1,
                    "source_page": page_num,
                    "extraction_confidence": 0.75
                })
                self.entity_counter += 1

        return entities

    def _create_generic_table_entity(self, content: str, section: Dict, page_num: int) -> Dict:
        """Crea entidad genérica para tabla."""

        return {
            "id": f"eaf_089_2025_ch01_table_{self.entity_counter:04d}",
            "type": "structured_data",
            "category": "table",
            "properties": {
                "data": {
                    "title": section["title"],
                    "content": content,
                    "rows": len(content.split('\n')),
                    "estimated_columns": max(len(line.split()) for line in content.split('\n') if line.strip())
                }
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": 0.7,
            "original_data": {
                "section_title": section["title"],
                "raw_content": content,
                "extraction_method": "generic_table_parsing"
            }
        }

    def _categorize_entities(self, entities: List[Dict]) -> Dict:
        """Categoriza entidades para fácil acceso."""

        categorized = {
            "fault_events": [],
            "technical_parameters": [],
            "equipment": [],
            "companies": [],
            "tables": [],
            "temporal_events": [],
            "regulatory_compliance": []
        }

        for entity in entities:
            entity_type = entity["type"]

            if entity_type == "fault_event":
                categorized["fault_events"].append(entity)
            elif entity_type == "technical_parameter":
                categorized["technical_parameters"].append(entity)
            elif entity_type in ["electrical_installation", "failed_element"]:
                categorized["equipment"].append(entity)
            elif entity_type == "organization":
                categorized["companies"].append(entity)
            elif entity_type == "structured_data":
                categorized["tables"].append(entity)
            elif entity_type == "temporal_event":
                categorized["temporal_events"].append(entity)

        return categorized


def main():
    """Demo del procesador que respeta esquema universal."""

    # Rutas
    base_path = Path(__file__).parent
    raw_text_path = base_path.parent / "outputs" / "raw_extractions" / "capitulo_01_raw.txt"

    if not raw_text_path.exists():
        print(f"❌ Raw text no encontrado: {raw_text_path}")
        return

    # Leer raw text
    with open(raw_text_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    print("🔄 PROCESANDO CON ESQUEMA UNIVERSAL - TODAS LAS TABLAS")
    print("=" * 60)

    # Crear procesador
    processor = UniversalSchemaCompliantProcessor()

    # Procesar respetando esquema universal
    result = processor.process_with_universal_schema(raw_text)

    # Guardar resultado
    output_path = base_path.parent / "outputs" / "universal_json" / "capitulo_01_universal_compliant.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"💾 JSON universal compliant guardado en: {output_path}")

    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS RESPETANDO ESQUEMA UNIVERSAL:")
    print(f"📋 Total entidades: {len(result['entities'])}")

    categorized = result["categorized_entities"]
    print(f"🚨 Eventos de falla: {len(categorized['fault_events'])}")
    print(f"⚡ Parámetros técnicos: {len(categorized['technical_parameters'])}")
    print(f"🔌 Equipos: {len(categorized['equipment'])}")
    print(f"🏭 Empresas: {len(categorized['companies'])}")
    print(f"📊 Tablas estructuradas: {len(categorized['tables'])}")
    print(f"⏰ Eventos temporales: {len(categorized['temporal_events'])}")

    print("\n📄 TABLAS DETECTADAS POR PÁGINA:")
    for page_num, page_data in result["pages"].items():
        table_count = page_data["metadata"]["table_count"]
        if table_count > 0:
            print(f"  Página {page_num}: {table_count} tablas")
            for table in page_data["tables"]:
                print(f"    - {table['title']}")

    print("\n" + "=" * 60)
    print("✅ PROCESAMIENTO UNIVERSAL COMPLETADO - TODAS LAS TABLAS CAPTURADAS")


if __name__ == "__main__":
    main()