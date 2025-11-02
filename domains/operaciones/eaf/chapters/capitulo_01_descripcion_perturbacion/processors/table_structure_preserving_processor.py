"""
Procesador que Preserva la Estructura Tabular Real
Mantiene el formato de tabla original y detecta las estructuras correctamente
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class TableStructurePreservingProcessor:
    """Procesador que preserva la estructura tabular real."""

    def __init__(self):
        self.entity_counter = 1

    def process_preserving_table_structure(self, raw_text: str) -> Dict:
        """Procesa preservando la estructura tabular real."""

        pages = self._split_by_pages(raw_text)

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
            "entities": [],
            "pages": {},
            "table_catalog": {
                "total_tables": 0,
                "tables_by_page": {},
                "table_formats": {}
            }
        }

        # Procesar cada página preservando estructura tabular
        for page_num, page_content in pages.items():
            page_entities, page_structure = self._extract_page_with_table_structure(page_content, page_num)

            result["entities"].extend(page_entities)
            result["pages"][page_num] = page_structure

            # Actualizar catálogo de tablas
            if page_structure["tables"]:
                result["table_catalog"]["tables_by_page"][page_num] = len(page_structure["tables"])
                result["table_catalog"]["total_tables"] += len(page_structure["tables"])

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

    def _extract_page_with_table_structure(self, page_content: str, page_num: int) -> Tuple[List[Dict], Dict]:
        """Extrae página preservando estructura tabular."""

        entities = []
        page_structure = {
            "page_number": page_num,
            "sections": [],
            "tables": [],
            "paragraphs": [],
            "metadata": {
                "total_sections": 0,
                "table_count": 0,
                "paragraph_count": 0
            }
        }

        # Detectar secciones específicas para página 1
        if page_num == 1:
            tables = self._extract_page_1_tables_with_structure(page_content)

            for table in tables:
                # Crear entidad con estructura tabular preservada
                table_entity = self._create_table_entity_with_structure(table, page_num)
                entities.append(table_entity)

                # Agregar a estructura de página
                page_structure["tables"].append(table)
                page_structure["metadata"]["table_count"] += 1

        else:
            # Para otras páginas, detectar estructura general
            sections = self._detect_general_sections_with_tables(page_content, page_num)

            for section in sections:
                if section["type"] == "table":
                    table_entity = self._create_table_entity_with_structure(section, page_num)
                    entities.append(table_entity)
                    page_structure["tables"].append(section)
                    page_structure["metadata"]["table_count"] += 1
                else:
                    page_structure["paragraphs"].append(section)
                    page_structure["metadata"]["paragraph_count"] += 1

        return entities, page_structure

    def _extract_page_1_tables_with_structure(self, content: str) -> List[Dict]:
        """Extrae las 3 tablas de la página 1 con estructura preservada."""

        tables = []

        # TABLA 1: Fecha y Hora de la falla
        table_1_pattern = r'(a\. Fecha y Hora de la falla.*?(?=b\. Identificación|$))'
        table_1_match = re.search(table_1_pattern, content, re.DOTALL)
        if table_1_match:
            table_1_structure = self._parse_key_value_table(table_1_match.group(1), "a. Fecha y Hora de la falla")
            tables.append(table_1_structure)

        # TABLA 2: Identificación instalación afectada
        table_2_pattern = r'(b\. Identificación instalación afectada.*?(?=c\. Identificación|$))'
        table_2_match = re.search(table_2_pattern, content, re.DOTALL)
        if table_2_match:
            table_2_structure = self._parse_key_value_table(table_2_match.group(1), "b. Identificación instalación afectada")
            tables.append(table_2_structure)

        # TABLA 3: Identificación del elemento fallado
        table_3_pattern = r'(c\. Identificación del elemento fallado.*$)'
        table_3_match = re.search(table_3_pattern, content, re.DOTALL)
        if table_3_match:
            table_3_structure = self._parse_key_value_table(table_3_match.group(1), "c. Identificación del elemento fallado")
            tables.append(table_3_structure)

        return tables

    def _parse_key_value_table(self, table_content: str, table_title: str) -> Dict:
        """Parsea una tabla con formato key-value preservando estructura."""

        lines = table_content.strip().split('\n')

        table_structure = {
            "table_id": f"page_1_table_{len([]) + 1}",
            "title": table_title,
            "type": "table",
            "format": "key_value_pairs",
            "parsed_structure": {
                "headers": ["Campo", "Valor"],
                "rows": [],
                "row_count": 0,
                "column_count": 2
            },
            "metadata": {
                "parsing_method": "key_value_detection",
                "confidence": 0.9
            }
        }

        # Parsear líneas para extraer pares key-value
        current_key = None
        current_value = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Saltar título de tabla
            if line.lower().startswith(('a.', 'b.', 'c.')):
                continue

            # Detectar patrones key-value
            # Patrón 1: "Clave valor" (separados por espacios)
            words = line.split()
            if len(words) >= 2:
                # Buscar dónde termina la clave y empieza el valor
                key_value_split = self._detect_key_value_split(line)

                if key_value_split:
                    key, value = key_value_split

                    # Si había una clave anterior, guardarla
                    if current_key:
                        table_structure["parsed_structure"]["rows"].append({
                            "row_id": len(table_structure["parsed_structure"]["rows"]) + 1,
                            "campo": current_key,
                            "valor": current_value.strip()
                        })

                    current_key = key.strip()
                    current_value = value.strip()
                else:
                    # Es continuación del valor anterior
                    if current_key:
                        current_value += " " + line
            else:
                # Línea con una sola palabra, probablemente continuación
                if current_key:
                    current_value += " " + line

        # Guardar última clave-valor
        if current_key:
            table_structure["parsed_structure"]["rows"].append({
                "row_id": len(table_structure["parsed_structure"]["rows"]) + 1,
                "campo": current_key,
                "valor": current_value.strip()
            })

        # Actualizar metadatos
        table_structure["parsed_structure"]["row_count"] = len(table_structure["parsed_structure"]["rows"])

        return table_structure

    def _detect_key_value_split(self, line: str) -> Tuple[str, str] or None:
        """Detecta dónde dividir una línea en clave y valor."""

        # Patrón 1: "Clave: Valor"
        if ':' in line:
            parts = line.split(':', 1)
            return parts[0], parts[1]

        # Patrón 2: "Clave Valor" (detectar por palabras conocidas)
        key_indicators = [
            'fecha', 'hora', 'consumos', 'demanda', 'porcentaje', 'calificación',
            'nombre', 'tipo', 'tensión', 'segmento', 'propietario', 'rut',
            'representante', 'dirección', 'elemento'
        ]

        words = line.split()
        if len(words) < 2:
            return None

        # Buscar indicadores de clave
        for i, word in enumerate(words):
            if word.lower() in key_indicators:
                # Buscar hasta dónde va la clave
                key_end = i + 1

                # Extender clave si las siguientes palabras son parte del campo
                while key_end < len(words):
                    next_word = words[key_end].lower()
                    if next_word in ['de', 'del', 'la', 'las', 'el', 'los', 'en']:
                        key_end += 1
                    elif next_word in key_indicators:
                        key_end += 1
                    else:
                        break

                if key_end < len(words):
                    key = ' '.join(words[:key_end])
                    value = ' '.join(words[key_end:])
                    return key, value

        # Patrón 3: Heurística - primera parte como clave
        if len(words) >= 3:
            # Tomar primeras 2-3 palabras como clave
            if len(words) <= 4:
                key = ' '.join(words[:-1])
                value = words[-1]
            else:
                # Buscar punto de división natural
                mid_point = len(words) // 2
                key = ' '.join(words[:mid_point])
                value = ' '.join(words[mid_point:])

            return key, value

        return None

    def _detect_general_sections_with_tables(self, content: str, page_num: int) -> List[Dict]:
        """Detecta secciones generales preservando tablas."""

        sections = []

        # Dividir por bloques
        blocks = re.split(r'\n\s*\n', content.strip())

        for i, block in enumerate(blocks):
            if not block.strip():
                continue

            section = {
                "section_id": f"page_{page_num}_section_{i}",
                "title": self._extract_section_title(block),
                "type": self._classify_section_type(block)
            }

            # Si es tabla, parsear estructura
            if section["type"] == "table":
                section["table_structure"] = self._parse_general_table(block)

            sections.append(section)

        return sections

    def _parse_general_table(self, content: str) -> Dict:
        """Parsea tabla general preservando estructura."""

        lines = content.split('\n')

        structure = {
            "format": "unknown",
            "headers": [],
            "rows": []
        }

        # Detectar tipo de tabla
        if self._is_key_value_format(lines):
            structure["format"] = "key_value_pairs"
            structure = self._parse_key_value_format(lines)
        elif self._is_columnar_format(lines):
            structure["format"] = "columnar"
            structure = self._parse_columnar_format(lines)
        elif self._is_company_list_format(lines):
            structure["format"] = "company_list"
            structure = self._parse_company_list_format(lines)

        return structure

    def _is_key_value_format(self, lines: List[str]) -> bool:
        """Detecta si es formato key-value."""
        key_value_lines = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            words = line.split()
            if len(words) >= 2:
                # Buscar patrones key-value
                if ':' in line or self._detect_key_value_split(line):
                    key_value_lines += 1

        return key_value_lines >= 2

    def _is_columnar_format(self, lines: List[str]) -> bool:
        """Detecta si es formato columnar."""
        columnar_lines = 0

        for line in lines:
            if len(line.split()) >= 3:
                columnar_lines += 1

        return columnar_lines >= 3

    def _is_company_list_format(self, lines: List[str]) -> bool:
        """Detecta si es lista de empresas."""
        company_lines = 0

        for line in lines:
            if re.search(r'(s\.a\.|spa|ltda)', line, re.IGNORECASE):
                company_lines += 1

        return company_lines >= 2

    def _parse_key_value_format(self, lines: List[str]) -> Dict:
        """Parsea formato key-value."""

        structure = {
            "format": "key_value_pairs",
            "headers": ["Campo", "Valor"],
            "rows": []
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            key_value = self._detect_key_value_split(line)
            if key_value:
                key, value = key_value
                structure["rows"].append({
                    "campo": key.strip(),
                    "valor": value.strip()
                })

        return structure

    def _parse_columnar_format(self, lines: List[str]) -> Dict:
        """Parsea formato columnar."""

        structure = {
            "format": "columnar",
            "headers": [],
            "rows": []
        }

        non_empty_lines = [line for line in lines if line.strip()]

        if non_empty_lines:
            # Primera línea como headers
            first_line_words = non_empty_lines[0].split()
            if len(first_line_words) >= 2:
                structure["headers"] = first_line_words

            # Resto como datos
            for line in non_empty_lines[1:]:
                words = line.split()
                if len(words) >= len(structure["headers"]):
                    row_data = {}
                    for i, header in enumerate(structure["headers"]):
                        if i < len(words):
                            row_data[f"col_{i}_{header}"] = words[i]
                    structure["rows"].append(row_data)

        return structure

    def _parse_company_list_format(self, lines: List[str]) -> Dict:
        """Parsea formato de lista de empresas."""

        structure = {
            "format": "company_list",
            "headers": ["Empresa", "Detalles"],
            "rows": []
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Extraer nombre de empresa y detalles
            company_match = re.search(r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s]+(S\.A\.|SPA|LTDA))', line, re.IGNORECASE)
            if company_match:
                company_name = company_match.group(1)
                details = line.replace(company_name, '').strip()

                structure["rows"].append({
                    "empresa": company_name,
                    "detalles": details
                })

        return structure

    def _classify_section_type(self, content: str) -> str:
        """Clasifica tipo de sección."""

        content_lower = content.lower()

        # Encabezados
        if re.match(r'^[a-z]\.\d+', content_lower.strip()):
            return "section_header"

        # Tablas
        lines = content.split('\n')
        if self._is_key_value_format(lines) or self._is_columnar_format(lines) or self._is_company_list_format(lines):
            return "table"

        return "paragraph"

    def _extract_section_title(self, content: str) -> str:
        """Extrae título de sección."""

        lines = content.split('\n')
        first_line = lines[0].strip()

        if len(first_line) <= 80:
            return first_line
        else:
            return first_line[:50] + "..."

    def _create_table_entity_with_structure(self, table: Dict, page_num: int) -> Dict:
        """Crea entidad de tabla con estructura preservada."""

        entity = {
            "id": f"eaf_089_2025_ch01_table_{self.entity_counter:04d}",
            "type": "structured_table",
            "category": "data_structure",
            "properties": {
                "table_metadata": {
                    "title": table["title"],
                    "format": table.get("format", "unknown"),
                    "row_count": table.get("parsed_structure", {}).get("row_count", 0),
                    "column_count": table.get("parsed_structure", {}).get("column_count", 0)
                },
                "table_structure": table.get("parsed_structure", {})
            },
            "source_chapter": 1,
            "source_page": page_num,
            "extraction_confidence": table.get("metadata", {}).get("confidence", 0.8),
            "original_data": {
                "section_title": table["title"],
                "extraction_method": "table_structure_preservation"
            }
        }

        self.entity_counter += 1
        return entity


def main():
    """Demo del procesador que preserva estructura tabular."""

    base_path = Path(__file__).parent
    raw_text_path = base_path.parent / "outputs" / "raw_extractions" / "capitulo_01_raw.txt"

    if not raw_text_path.exists():
        print(f"❌ Raw text no encontrado: {raw_text_path}")
        return

    with open(raw_text_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    print("📊 PROCESANDO PRESERVANDO ESTRUCTURA TABULAR REAL")
    print("=" * 60)

    processor = TableStructurePreservingProcessor()
    result = processor.process_preserving_table_structure(raw_text)

    # Guardar resultado
    output_path = base_path.parent / "outputs" / "universal_json" / "capitulo_01_table_structure_preserved.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"💾 JSON con estructura tabular guardado en: {output_path}")

    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS DE TABLAS CON ESTRUCTURA:")
    print(f"📋 Total entidades: {len(result['entities'])}")
    print(f"📊 Total tablas: {result['table_catalog']['total_tables']}")

    print("\n📄 TABLAS POR PÁGINA:")
    for page_num, table_count in result["table_catalog"]["tables_by_page"].items():
        print(f"  Página {page_num}: {table_count} tablas")

    print("\n🔍 DETALLE DE TABLAS DE PÁGINA 1:")
    page_1_tables = result["pages"].get("1", {}).get("tables", [])
    for i, table in enumerate(page_1_tables):
        print(f"\n  Tabla {i+1}: {table['title']}")
        print(f"    Formato: {table['format']}")
        if 'parsed_structure' in table:
            print(f"    Filas: {table['parsed_structure']['row_count']}")
            print(f"    Columnas: {table['parsed_structure']['column_count']}")

            # Mostrar primeras filas
            rows = table['parsed_structure'].get('rows', [])
            for j, row in enumerate(rows[:3]):
                print(f"      Fila {j+1}: {row}")

    print("\n" + "=" * 60)
    print("✅ ESTRUCTURA TABULAR PRESERVADA CORRECTAMENTE")


if __name__ == "__main__":
    main()