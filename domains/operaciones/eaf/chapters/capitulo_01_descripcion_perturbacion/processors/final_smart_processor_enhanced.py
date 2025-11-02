"""
Procesador Final MEJORADO con Detección de Celdas Multi-línea (cDoubleLinea)
Captura las líneas de continuación que empiezan con "/" u otros indicadores
"""

import json
from pathlib import Path
from datetime import datetime
from smart_content_classifier import SmartContentClassifier, ContentType
from enhanced_table_detector import patch_smart_classifier


class FinalSmartProcessorEnhanced:
    """Procesador mejorado que captura celdas multi-línea (cDoubleLinea)."""

    def __init__(self, pdf_path: str):
        # Crear clasificador y aplicar mejoras
        self.classifier = SmartContentClassifier(pdf_path)
        patch_smart_classifier(self.classifier)  # 🔧 Activar detección mejorada
        self.entity_counter = 0

    def process_all_pages(self, start_page: int = 1, end_page: int = 11) -> dict:
        """Procesa todas las páginas con detección mejorada de multi-línea."""

        print("🚀 PROCESADOR MEJORADO - DETECCIÓN DE CELDAS MULTI-LÍNEA")
        print("=" * 70)
        print("📊 Detecta celdas con múltiples líneas (cDoubleLinea, cTripleLinea)")
        print("✅ Captura líneas de continuación: /, y, etc.")
        print("=" * 70)

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
                "page_range": f"{start_page}-{end_page}",
                "processing_timestamp": datetime.now().isoformat(),
                "processing_method": "smart_classification_enhanced_multiline"
            },
            "entities": [],
            "pages": {},
            "extraction_summary": {
                "total_pages": 0,
                "content_types": {
                    "tables": 0,
                    "paragraphs": 0,
                    "headings": 0,
                    "lists": 0,
                    "images": 0
                },
                "extraction_method": "smart_classification_with_multiline_cells"
            }
        }

        # Procesar cada página
        for page_num in range(start_page, end_page + 1):
            blocks = self.classifier.classify_page_content(page_num)

            page_stats = {
                "tables": 0,
                "paragraphs": 0,
                "headings": 0,
                "lists": 0,
                "images": 0
            }

            # Convertir bloques a entidades
            for block in blocks:
                self.entity_counter += 1
                entity = self._create_entity_from_block(block, self.entity_counter)
                result["entities"].append(entity)

                # Actualizar estadísticas
                type_key = block.type.value + "s" if block.type.value != "paragraph" else "paragraphs"
                if type_key in page_stats:
                    page_stats[type_key] += 1
                    result["extraction_summary"]["content_types"][type_key] += 1

            # Guardar info de página
            result["pages"][page_num] = {
                "page_number": page_num,
                **page_stats,
                "total_blocks": len(blocks)
            }

            result["extraction_summary"]["total_pages"] += 1

            # Mostrar progreso
            icons = {
                "tables": "📊",
                "paragraphs": "📝",
                "headings": "📌",
                "lists": "📋",
                "images": "🖼️"
            }

            parts = [f"{icons[k]}{v}" for k, v in page_stats.items() if v > 0]
            print(f"✅ Página {page_num:2d}: {' | '.join(parts)}")

        print("\n" + "=" * 70)
        print("📊 RESUMEN FINAL")
        print("=" * 70)

        summary = result["extraction_summary"]
        print(f"📄 Páginas: {summary['total_pages']}")
        print(f"📊 Tablas: {summary['content_types']['tables']}")
        print(f"📝 Párrafos: {summary['content_types']['paragraphs']}")
        print(f"📌 Encabezados: {summary['content_types']['headings']}")
        print(f"📋 Listas: {summary['content_types']['lists']}")
        print(f"🖼️ Imágenes: {summary['content_types']['images']}")
        print(f"🎯 Total entidades: {len(result['entities'])}")

        return result

    def _create_entity_from_block(self, block, entity_id: int) -> dict:
        """Convierte un ContentBlock en una entidad."""

        base_entity = {
            "id": f"eaf_089_2025_ch01_{block.type.value}_{entity_id:04d}",
            "type": block.type.value,
            "source_chapter": 1,
            "source_page": block.page,
            "extraction_confidence": block.confidence,
            "bbox": block.bbox,
            "original_data": {
                "extraction_method": "smart_classification_enhanced",
                **block.metadata
            }
        }

        # Contenido específico por tipo
        if block.type == ContentType.TABLE:
            base_entity["category"] = "data_structure"
            base_entity["properties"] = self._format_table_properties(block.content)

        elif block.type == ContentType.PARAGRAPH:
            base_entity["category"] = "narrative"
            base_entity["properties"] = {
                "text": block.content["text"],
                "char_count": block.metadata.get("char_count", 0),
                "line_count": block.metadata.get("line_count", 0)
            }

        elif block.type == ContentType.HEADING:
            base_entity["category"] = "structure"
            base_entity["properties"] = {
                "text": block.content["text"],
                "level": self._infer_heading_level(block.content["text"])
            }

        elif block.type == ContentType.LIST:
            base_entity["category"] = "structure"
            base_entity["properties"] = {
                "items": block.content["items"],
                "item_count": len(block.content["items"])
            }

        elif block.type == ContentType.IMAGE:
            base_entity["category"] = "media"
            base_entity["properties"] = block.content

        return base_entity

    def _format_table_properties(self, table_content: dict) -> dict:
        """Formatea propiedades de tabla en formato estructurado."""

        # Convertir matriz a formato clave-valor
        structured_rows = []
        row_id = 1

        for row_data in table_content["data"]:
            # Limpiar celdas
            cleaned = [cell.strip() for cell in row_data]
            non_empty = [c for c in cleaned if c]

            if len(non_empty) >= 2:
                campo = non_empty[0]
                valor = " ".join(non_empty[1:])

                # Filtrar encabezados y marcadores
                if campo.lower() not in ["campo", "valor"] and len(campo) > 1:
                    structured_rows.append({
                        "row_id": row_id,
                        "campo": campo,
                        "valor": valor
                    })
                    row_id += 1

        return {
            "table_metadata": {
                "row_count": len(structured_rows),
                "column_count": table_content["col_count"],
                "format": "key_value_pairs"
            },
            "table_structure": {
                "headers": ["Campo", "Valor"],
                "rows": structured_rows
            }
        }

    def _infer_heading_level(self, text: str) -> int:
        """Infiere nivel de encabezado basado en el texto."""
        text_lower = text.lower()

        if "estudio" in text_lower and "análisis" in text_lower:
            return 1  # Título del documento
        elif text.startswith(("1.", "2.", "3.")):
            return 2  # Sección principal
        elif text.startswith(("a.", "b.", "c.")):
            return 3  # Subsección
        elif text.startswith(("i.", "ii.", "iii.")):
            return 4  # Sub-subsección
        else:
            return 4  # Por defecto


# Script de ejecución
if __name__ == "__main__":
    from pathlib import Path

    # Ruta al PDF
    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        exit(1)

    # Procesar
    processor = FinalSmartProcessorEnhanced(str(pdf_path))
    result = processor.process_all_pages(start_page=1, end_page=11)

    # Guardar resultado
    output_dir = Path(__file__).parent.parent / "outputs" / "universal_json"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "capitulo_01_enhanced_multiline.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Guardado en: {output_path}")

    # Mostrar ejemplo de fila 10 (debería tener las líneas de continuación)
    print(f"\n🔍 VERIFICACIÓN: Fila 10 (Nombre de la instalación)")
    print("=" * 70)

    for entity in result["entities"]:
        if entity["type"] == "table":
            rows = entity["properties"]["table_structure"]["rows"]
            if len(rows) >= 10:
                row_10 = rows[9]  # 0-indexed
                print(f"Campo: {row_10['campo']}")
                print(f"Valor: {row_10['valor']}")

                # Verificar si tiene el código técnico
                if "LT002" in row_10['valor']:
                    print("\n✅ ¡ÉXITO! Línea de continuación capturada")
                else:
                    print("\n⚠️  Línea de continuación aún no capturada")
                break

    print("\n✨ ¡Listo!")
