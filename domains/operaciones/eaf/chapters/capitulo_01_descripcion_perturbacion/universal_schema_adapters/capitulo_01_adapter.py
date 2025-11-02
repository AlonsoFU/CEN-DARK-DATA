"""
Adaptador de Esquema Universal - Capítulo 1
Transforma datos del capítulo 1 al esquema universal del dominio EAF
"""

from typing import Dict, List
import json
from pathlib import Path


class Capitulo01UniversalAdapter:
    """Adaptador para transformar datos del capítulo 1 al esquema universal."""

    def __init__(self):
        self.schema_version = "1.0"
        self.chapter_id = "eaf_089_2025_cap_01"

    def adapt_to_universal_schema(self, processed_data: Dict) -> Dict:
        """Adapta los datos procesados al esquema universal del dominio."""

        universal_schema = {
            "@context": {
                "@vocab": "https://dark-data-platform.cl/eaf/",
                "eaf": "https://dark-data-platform.cl/eaf/",
                "incident": "https://dark-data-platform.cl/incident/",
                "equipment": "https://dark-data-platform.cl/equipment/",
                "organization": "https://dark-data-platform.cl/organization/"
            },
            "@type": "EAFChapter",
            "schema_version": self.schema_version,
            "document": self._extract_document_info(processed_data),
            "chapter": self._extract_chapter_info(processed_data),
            "incident": self._extract_incident_info(processed_data),
            "technical_parameters": self._extract_technical_parameters(processed_data),
            "organizations": self._extract_organizations(processed_data),
            "equipment": self._extract_equipment(processed_data),
            "temporal_data": self._extract_temporal_data(processed_data),
            "relationships": self._generate_relationships(processed_data),
            "processing_metadata": self._extract_processing_metadata(processed_data)
        }

        return universal_schema

    def _extract_document_info(self, data: Dict) -> Dict:
        """Extrae información del documento."""
        return {
            "@type": "EAFDocument",
            "eaf_number": "089/2025",
            "title": "Estudio para análisis de falla EAF 089/2025",
            "incident_description": "Desconexión forzada línea 2x500 kV Nueva Maitencillo - Nueva Pan de Azúcar",
            "emission_date": "2025-03-18",
            "voltage_level": "500kV",
            "incident_type": "forced_disconnection",
            "affected_infrastructure": "transmission_line"
        }

    def _extract_chapter_info(self, data: Dict) -> Dict:
        """Extrae información del capítulo."""
        return {
            "@type": "EAFChapter",
            "chapter_id": data.get("chapter_id", self.chapter_id),
            "number": 1,
            "title": data.get("title", "Descripción pormenorizada de la perturbación"),
            "content_type": data.get("content_type", "description"),
            "page_range": "1-11",
            "pages_count": data.get("metadata", {}).get("pages_processed", 11)
        }

    def _extract_incident_info(self, data: Dict) -> Dict:
        """Extrae información específica del incidente."""
        incident_info = {
            "@type": "PowerSystemIncident",
            "incident_id": "eaf_089_2025_incident",
            "classification": "total_blackout"
        }

        # Buscar información de falla en las entidades
        for entity in data.get("entities", []):
            if entity.get("type") == "fault_event":
                fault_data = entity.get("data", {})
                incident_info.update({
                    "occurrence_date": fault_data.get("date"),
                    "occurrence_time": fault_data.get("time"),
                    "disconnected_consumption_mw": fault_data.get("disconnected_consumption_mw"),
                    "previous_system_demand_mw": fault_data.get("previous_system_demand_mw"),
                    "disconnection_percentage": fault_data.get("disconnection_percentage"),
                    "severity": "critical" if fault_data.get("disconnection_percentage", 0) == 100 else "high"
                })
                break

        return incident_info

    def _extract_technical_parameters(self, data: Dict) -> List[Dict]:
        """Extrae parámetros técnicos."""
        parameters = []

        for entity in data.get("entities", []):
            if entity.get("category") == "technical_parameter":
                param = {
                    "@type": "TechnicalParameter",
                    "parameter_type": entity.get("type"),
                    "value": entity.get("value"),
                    "unit": entity.get("unit", ""),
                    "source_chapter": 1
                }
                parameters.append(param)

        return parameters

    def _extract_organizations(self, data: Dict) -> List[Dict]:
        """Extrae organizaciones mencionadas."""
        organizations = []

        for entity in data.get("entities", []):
            if entity.get("type") == "company":
                org = {
                    "@type": "ElectricUtility",
                    "name": entity.get("name", ""),
                    "role": "utility_company",
                    "sector": "electricity",
                    "mentioned_in_chapter": 1
                }
                organizations.append(org)

        return organizations

    def _extract_equipment(self, data: Dict) -> List[Dict]:
        """Extrae equipos eléctricos."""
        equipment = []

        for entity in data.get("entities", []):
            if entity.get("category") == "equipment":
                equip = {
                    "@type": "ElectricalEquipment",
                    "equipment_type": entity.get("type"),
                    "description": entity.get("description", entity.get("name", "")),
                    "voltage_level": self._extract_voltage_from_description(
                        entity.get("description", entity.get("name", ""))
                    ),
                    "mentioned_in_chapter": 1
                }
                equipment.append(equip)

        return equipment

    def _extract_temporal_data(self, data: Dict) -> List[Dict]:
        """Extrae datos temporales."""
        temporal_data = []

        for entity in data.get("entities", []):
            if entity.get("category") == "temporal_reference":
                temporal = {
                    "@type": "TemporalReference",
                    "reference_type": entity.get("type"),
                    "value": entity.get("value"),
                    "context": "incident_timeline",
                    "source_chapter": 1
                }
                temporal_data.append(temporal)

        return temporal_data

    def _extract_voltage_from_description(self, description: str) -> str:
        """Extrae nivel de voltaje de una descripción."""
        import re
        voltage_match = re.search(r'(\d+)\s*kV', description, re.IGNORECASE)
        return f"{voltage_match.group(1)}kV" if voltage_match else "unknown"

    def _generate_relationships(self, data: Dict) -> List[Dict]:
        """Genera relaciones entre entidades."""
        relationships = []

        # Relación entre el incidente y la línea afectada
        relationships.append({
            "@type": "IncidentAffectsEquipment",
            "subject": "eaf_089_2025_incident",
            "predicate": "affects",
            "object": "line_nueva_maitencillo_nueva_pan_azucar",
            "relationship_type": "incident_equipment",
            "confidence": 1.0
        })

        # Relación temporal del incidente
        relationships.append({
            "@type": "IncidentOccursAt",
            "subject": "eaf_089_2025_incident",
            "predicate": "occurs_at",
            "object": "2025-02-25T15:16:00",
            "relationship_type": "temporal",
            "confidence": 1.0
        })

        return relationships

    def _extract_processing_metadata(self, data: Dict) -> Dict:
        """Extrae metadata del procesamiento."""
        return {
            "@type": "ProcessingMetadata",
            "processing_timestamp": data.get("processing_timestamp"),
            "extraction_method": data.get("metadata", {}).get("extraction_method", "PyPDF2"),
            "schema_version": self.schema_version,
            "confidence_score": 0.85,
            "entities_count": len(data.get("entities", [])),
            "records_count": len(data.get("records", []))
        }

    def validate_schema(self, universal_data: Dict) -> Dict:
        """Valida el esquema universal generado."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        # Validaciones básicas
        required_fields = ["@context", "@type", "document", "chapter", "incident"]
        for field in required_fields:
            if field not in universal_data:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["is_valid"] = False

        # Estadísticas
        validation_result["statistics"] = {
            "technical_parameters_count": len(universal_data.get("technical_parameters", [])),
            "organizations_count": len(universal_data.get("organizations", [])),
            "equipment_count": len(universal_data.get("equipment", [])),
            "relationships_count": len(universal_data.get("relationships", []))
        }

        return validation_result

    def export_to_file(self, universal_data: Dict, output_path: str) -> str:
        """Exporta el esquema universal a archivo."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(universal_data, f, indent=2, ensure_ascii=False)

        return str(output_file)


def main():
    """Demo del adaptador."""
    # Ejemplo de uso del adaptador
    adapter = Capitulo01UniversalAdapter()

    # Cargar datos procesados del capítulo 1
    processed_file = Path(__file__).parent.parent / "outputs" / "validated_extractions" / "capitulo_01_processed.json"

    if processed_file.exists():
        with open(processed_file, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)

        # Adaptar al esquema universal
        universal_data = adapter.adapt_to_universal_schema(processed_data)

        # Validar esquema
        validation = adapter.validate_schema(universal_data)

        # Exportar esquema universal adaptado
        output_file = adapter.export_to_file(
            universal_data,
            processed_file.parent.parent / "universal_json" / "capitulo_01_universal_adapted.json"
        )

        print("="*60)
        print("ADAPTADOR ESQUEMA UNIVERSAL - CAPÍTULO 1")
        print("="*60)
        print(f"✅ Esquema adaptado: {validation['is_valid']}")
        print(f"📊 Estadísticas:")
        for key, value in validation['statistics'].items():
            print(f"   - {key}: {value}")
        print(f"💾 Archivo generado: {output_file}")
        print("="*60)

    else:
        print(f"❌ No se encontró archivo de datos procesados: {processed_file}")


if __name__ == "__main__":
    main()