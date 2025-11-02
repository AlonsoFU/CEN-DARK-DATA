"""
Formateador Mejorado de Tablas
Convierte la tabla raw con coordenadas al formato estructurado final
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class ImprovedTableFormatter:
    """Formatea tablas extraídas con coordenadas al formato final."""

    def format_page_1_table_1(self, raw_table: List[List[str]]) -> List[Dict]:
        """
        Formatea la Tabla 1: Fecha y Hora de la falla

        Estructura esperada:
        - Columna 3: Campo (ej: "Fecha", "Hora")
        - Columna 5: Valor (ej: "25/02/2025", "15:16")
        """
        formatted_data = []
        row_id = 1

        for row in raw_table:
            # Limpiar espacios
            cleaned_row = [cell.strip() for cell in row]

            # Buscar el campo en las columnas centrales (índices 2-4)
            campo = None
            valor = None

            # Intentar encontrar campo y valor
            for i, cell in enumerate(cleaned_row):
                if cell and cell not in ["a.", "1."]:
                    # Si encontramos "Fecha" o "Hora", es un campo
                    if cell in ["Fecha", "Hora"]:
                        campo = cell
                        # El valor está más adelante en la fila
                        for j in range(i + 1, len(cleaned_row)):
                            if cleaned_row[j]:
                                valor = cleaned_row[j]
                                break
                        break
                    # También capturar otros campos importantes
                    elif any(keyword in cell.lower() for keyword in ["consumos", "demanda", "porcentaje", "calificación"]):
                        # Este es un campo completo, buscar su valor
                        campo = cell
                        for j in range(i + 1, len(cleaned_row)):
                            if cleaned_row[j]:
                                valor = cleaned_row[j]
                                break
                        break

            # Si encontramos campo y valor, agregar
            if campo and valor:
                formatted_data.append({
                    "row_id": row_id,
                    "campo": campo,
                    "valor": valor
                })
                row_id += 1

        return formatted_data

    def format_page_1_table_2(self, raw_table: List[List[str]]) -> List[Dict]:
        """
        Formatea la Tabla 2: Identificación instalación afectada

        Similar estructura: campo en columna central, valor a la derecha
        """
        formatted_data = []
        row_id = 1

        for row in raw_table:
            cleaned_row = [cell.strip() for cell in row]

            # Buscar campo y valor
            campo = None
            valor = None

            for i, cell in enumerate(cleaned_row):
                if cell and cell not in ["b."]:
                    # Si es un campo conocido
                    if any(keyword in cell.lower() for keyword in [
                        "nombre", "tipo", "tensión", "segmento", "ubicación",
                        "propietario", "coordenadas"
                    ]):
                        campo = cell
                        # Buscar valor en celdas siguientes
                        for j in range(i + 1, len(cleaned_row)):
                            if cleaned_row[j]:
                                valor = cleaned_row[j]
                                break
                        break

            if campo and valor:
                formatted_data.append({
                    "row_id": row_id,
                    "campo": campo,
                    "valor": valor
                })
                row_id += 1

        return formatted_data

    def format_page_1_table_3(self, raw_table: List[List[str]]) -> List[Dict]:
        """
        Formatea la Tabla 3: Identificación de la empresa
        """
        formatted_data = []
        row_id = 1

        for row in raw_table:
            cleaned_row = [cell.strip() for cell in row]

            campo = None
            valor = None

            for i, cell in enumerate(cleaned_row):
                if cell and cell not in ["c.", "d."]:
                    if any(keyword in cell.lower() for keyword in [
                        "razón social", "rut", "representante", "dirección",
                        "teléfono", "correo", "región"
                    ]):
                        campo = cell
                        for j in range(i + 1, len(cleaned_row)):
                            if cleaned_row[j]:
                                valor = cleaned_row[j]
                                break
                        break

            if campo and valor:
                formatted_data.append({
                    "row_id": row_id,
                    "campo": campo,
                    "valor": valor
                })
                row_id += 1

        return formatted_data

    def create_universal_schema_output(self, raw_extraction: Dict) -> Dict:
        """
        Crea la salida final en formato de esquema universal.
        """
        # Formatear cada tabla
        table_1_data = self.format_page_1_table_1(
            raw_extraction["page_1_tables"]["table_1"]["raw_table"]
        )
        table_2_data = self.format_page_1_table_2(
            raw_extraction["page_1_tables"]["table_2"]["raw_table"]
        )
        table_3_data = self.format_page_1_table_3(
            raw_extraction["page_1_tables"]["table_3"]["raw_table"]
        )

        # Construir esquema universal
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
            "extraction_method": "coordinate_based_with_improved_formatting"
        }

        # Crear entidades para cada tabla
        if table_1_data:
            result["entities"].append({
                "id": "eaf_089_2025_ch01_table_0001",
                "type": "structured_table",
                "category": "data_structure",
                "properties": {
                    "table_metadata": {
                        "title": "a. Fecha y Hora de la falla",
                        "format": "key_value_pairs",
                        "row_count": len(table_1_data),
                        "column_count": 2
                    },
                    "table_structure": {
                        "headers": ["Campo", "Valor"],
                        "rows": table_1_data,
                        "row_count": len(table_1_data),
                        "column_count": 2
                    }
                },
                "source_chapter": 1,
                "source_page": 1,
                "extraction_confidence": 0.95,
                "original_data": {
                    "section_title": "a. Fecha y Hora de la falla",
                    "extraction_method": "coordinate_based"
                }
            })

        if table_2_data:
            result["entities"].append({
                "id": "eaf_089_2025_ch01_table_0002",
                "type": "structured_table",
                "category": "data_structure",
                "properties": {
                    "table_metadata": {
                        "title": "b. Identificación instalación afectada",
                        "format": "key_value_pairs",
                        "row_count": len(table_2_data),
                        "column_count": 2
                    },
                    "table_structure": {
                        "headers": ["Campo", "Valor"],
                        "rows": table_2_data,
                        "row_count": len(table_2_data),
                        "column_count": 2
                    }
                },
                "source_chapter": 1,
                "source_page": 1,
                "extraction_confidence": 0.95,
                "original_data": {
                    "section_title": "b. Identificación instalación afectada",
                    "extraction_method": "coordinate_based"
                }
            })

        if table_3_data:
            result["entities"].append({
                "id": "eaf_089_2025_ch01_table_0003",
                "type": "structured_table",
                "category": "data_structure",
                "properties": {
                    "table_metadata": {
                        "title": "c. Identificación de la empresa",
                        "format": "key_value_pairs",
                        "row_count": len(table_3_data),
                        "column_count": 2
                    },
                    "table_structure": {
                        "headers": ["Campo", "Valor"],
                        "rows": table_3_data,
                        "row_count": len(table_3_data),
                        "column_count": 2
                    }
                },
                "source_chapter": 1,
                "source_page": 1,
                "extraction_confidence": 0.95,
                "original_data": {
                    "section_title": "c. Identificación de la empresa",
                    "extraction_method": "coordinate_based"
                }
            })

        return result


def main():
    """Demo del formateador mejorado."""
    print("🎨 FORMATEADOR MEJORADO DE TABLAS")
    print("=" * 70)

    # Leer extracción basada en coordenadas
    input_file = Path(__file__).parent.parent / "outputs" / "raw_extractions" / "capitulo_01_coordinate_based.json"

    if not input_file.exists():
        print(f"❌ Archivo no encontrado: {input_file}")
        print("💡 Ejecuta primero: python coordinate_based_table_processor.py")
        return

    print(f"📖 Leyendo: {input_file.name}")

    with open(input_file, 'r', encoding='utf-8') as f:
        raw_extraction = json.load(f)

    # Crear formateador
    formatter = ImprovedTableFormatter()

    # Generar salida formateada
    formatted_output = formatter.create_universal_schema_output(raw_extraction)

    # Mostrar resultados
    print("\n✅ FORMATEO COMPLETADO")
    print("=" * 70)

    print(f"\n📊 Entidades extraídas: {len(formatted_output['entities'])}")

    for entity in formatted_output['entities']:
        table_props = entity['properties']
        print(f"\n📋 {table_props['table_metadata']['title']}")
        print(f"   Filas: {table_props['table_metadata']['row_count']}")
        print(f"   Confianza: {entity['extraction_confidence']}")

        # Mostrar primeras 3 filas
        rows = table_props['table_structure']['rows']
        print(f"\n   Primeras filas:")
        for row in rows[:3]:
            print(f"   - {row['campo']}: {row['valor']}")

        if len(rows) > 3:
            print(f"   ... y {len(rows) - 3} filas más")

    # Guardar resultado
    output_dir = Path(__file__).parent.parent / "outputs" / "universal_json"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "capitulo_01_coordinate_based_formatted.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resultado guardado en: {output_file}")
    print()
    print("=" * 70)
    print("✅ PROCESAMIENTO COMPLETADO")
    print()
    print("💡 Verifica que 'Hora' y '15:16' estén correctamente separados!")


if __name__ == "__main__":
    main()