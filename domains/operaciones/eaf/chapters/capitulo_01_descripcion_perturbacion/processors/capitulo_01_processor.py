"""
Procesador del Capítulo 1: Descripción pormenorizada de la perturbación
EAF-089/2025

Procesa páginas 1-11 del documento EAF siguiendo el dataflow:
PDF → JSON → SQLite → MCP → AI Access
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List
import PyPDF2
import re
from datetime import datetime
import sys

# Importar OCR detector
try:
    from ocr_structure_detector import OCRStructureDetector
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    print(f"⚠️ OCR no disponible: {e}")

# Add shared path
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.append(str(shared_path))


class Capitulo01Processor:
    """Procesador específico para Capítulo 1 - Descripción de la perturbación."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.chapter_dir = Path(__file__).parent.parent
        self.outputs_dir = self.chapter_dir / "outputs"

        # Chapter specific info
        self.chapter_info = {
            "number": 1,
            "title": "Descripción pormenorizada de la perturbación",
            "start_page": 0,  # PDF page index
            "end_page": 10,   # PDF page index
            "content_type": "description"
        }

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Inicializar OCR si está disponible
        self.ocr_detector = None
        if OCR_AVAILABLE:
            try:
                self.ocr_detector = OCRStructureDetector(str(pdf_path))
                self.logger.info("✅ OCR detector inicializado correctamente")
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo inicializar OCR: {e}")
        else:
            self.logger.warning("⚠️ OCR no disponible - continuando sin análisis visual")

    def process_chapter(self) -> Dict:
        """Procesa el capítulo 1 completo siguiendo el dataflow."""
        self.logger.info("Iniciando procesamiento Capítulo 1: Descripción de la perturbación")

        # Paso 1: Extraer texto del PDF
        raw_text = self._extract_pdf_text()

        # Paso 2: Procesar y estructurar datos
        processed_data = self._process_chapter_content(raw_text)

        # Paso 3: Guardar extracción raw
        raw_file = self._save_raw_extraction(raw_text)

        # Paso 4: Guardar datos procesados
        processed_file = self._save_processed_data(processed_data)

        # Paso 5: Transformar a JSON universal
        universal_data = self._transform_to_universal_json(processed_data)
        universal_file = self._save_universal_json(universal_data)

        # Paso 6: Ingerir a base de datos (simulado)
        db_result = self._ingest_to_database(universal_data)

        results = {
            "chapter": self.chapter_info,
            "files": {
                "raw_extraction": str(raw_file),
                "processed_data": str(processed_file),
                "universal_json": str(universal_file)
            },
            "stats": {
                "raw_text_size": len(raw_text),
                "entities_extracted": len(processed_data.get("entities", [])),
                "records_count": len(processed_data.get("records", []))
            },
            "database_ingestion": db_result,
            "status": "completed"
        }

        self.logger.info(f"Capítulo 1 procesado exitosamente: {results['stats']}")
        return results

    def _extract_pdf_text(self) -> str:
        """Extrae texto de las páginas 1-11 del PDF."""
        text_parts = []

        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            for page_num in range(self.chapter_info["start_page"], self.chapter_info["end_page"] + 1):
                if page_num < len(reader.pages):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    text_parts.append(f"=== PÁGINA {page_num + 1} ===\n{text}\n")

        return "\n".join(text_parts)

    def _process_chapter_content(self, text: str) -> Dict:
        """Procesa el contenido específico del capítulo 1."""
        entities = []
        records = []
        technical_data = {}

        # Extraer información de la falla
        fault_info = self._extract_fault_information(text)
        if fault_info:
            entities.append({
                "type": "fault_event",
                "category": "incident",
                "data": fault_info
            })

        # Extraer datos técnicos (fechas, horas, MW, etc.)
        tech_data = self._extract_technical_data(text)
        entities.extend(tech_data)

        # Extraer empresas y equipos mencionados
        companies = self._extract_companies(text)
        entities.extend(companies)

        # Extraer información de voltajes y líneas
        electrical_data = self._extract_electrical_data(text)
        entities.extend(electrical_data)

        # Extraer secuencia temporal de eventos (nuevo)
        temporal_sequence = self._extract_temporal_sequence(text)
        entities.extend(temporal_sequence)

        # Procesar cada página como un registro
        pages = text.split("=== PÁGINA")
        for page_text in pages[1:]:  # Skip first empty split
            page_record = self._process_page_content(page_text)
            if page_record:
                records.append(page_record)

        return {
            "chapter_id": "eaf_089_2025_cap_01",
            "title": self.chapter_info["title"],
            "content_type": self.chapter_info["content_type"],
            "entities": entities,
            "records": records,
            "technical_data": technical_data,
            "processing_timestamp": datetime.now().isoformat(),
            "metadata": {
                "pages_processed": self.chapter_info["end_page"] - self.chapter_info["start_page"] + 1,
                "extraction_method": "PyPDF2"
            }
        }

    def _extract_fault_information(self, text: str) -> Dict:
        """Extrae información específica de la falla incluyendo detalles técnicos."""
        fault_info = {}

        # Buscar fecha y hora de la falla (básica)
        date_pattern = r'Fecha\s+(\d{2}/\d{2}/\d{4})'
        time_pattern = r'Hora\s+(\d{1,2}:\d{2})'

        date_match = re.search(date_pattern, text)
        time_match = re.search(time_pattern, text)

        if date_match:
            fault_info["date"] = date_match.group(1)
        if time_match:
            fault_info["time"] = time_match.group(1)

        # Buscar hora exacta del origen de la falla (más específica)
        exact_time_pattern = r'A las (\d{1,2}:\d{2}:\d{2}) horas\s+del día (\d{1,2} de \w+ de \d{4})'
        exact_time_match = re.search(exact_time_pattern, text)
        if exact_time_match:
            fault_info["exact_fault_time"] = exact_time_match.group(1)
            fault_info["exact_fault_date"] = exact_time_match.group(2)

        # Buscar interruptores específicos operados
        breakers_pattern = r'interruptores\s+((?:\d+\w+[,\s]*)+)'
        breakers_matches = re.findall(breakers_pattern, text)
        if breakers_matches:
            fault_info["operated_breakers"] = [match.strip() for match in breakers_matches]

        # Buscar potencia transitada
        power_transit_pattern = r'transitaban del orden de (\d+)\s*MW'
        power_match = re.search(power_transit_pattern, text)
        if power_match:
            fault_info["power_transit_mw"] = int(power_match.group(1))

        # Buscar tiempo de oscilaciones
        oscillation_pattern = r'durante aproximadamente (\d+)\s*segundo'
        oscillation_match = re.search(oscillation_pattern, text)
        if oscillation_match:
            fault_info["oscillation_duration_seconds"] = int(oscillation_match.group(1))

        # Buscar tiempo de reconexión automática
        reconnection_pattern = r'(\d+\.?\d*)\s*segundos más tarde se produjo la reconexión automática'
        reconnection_match = re.search(reconnection_pattern, text)
        if reconnection_match:
            fault_info["automatic_reconnection_time_seconds"] = float(reconnection_match.group(1))

        # Buscar causa raíz (función diferencial)
        cause_pattern = r'función diferencial de línea \((\w+)\)'
        cause_match = re.search(cause_pattern, text)
        if cause_match:
            fault_info["root_cause_function"] = cause_match.group(1)

        # Buscar sistema de protección afectado
        protection_system_pattern = r'relés (\w+\s+\w+)'
        protection_matches = re.findall(protection_system_pattern, text)
        if protection_matches:
            fault_info["protection_systems"] = list(set(protection_matches))

        # Buscar fenómeno físico
        physical_phenomenon_pattern = r'Fenómeno Físico:\s*([^:]+)'
        physical_match = re.search(physical_phenomenon_pattern, text)
        if physical_match:
            fault_info["physical_phenomenon"] = physical_match.group(1).strip()

        # Buscar código de operación
        operation_code_pattern = r'(OPE\d+):'
        operation_match = re.search(operation_code_pattern, text)
        if operation_match:
            fault_info["operation_code"] = operation_match.group(1)

        # Buscar empresa propietaria
        owner_pattern = r'empresa ([^,]+), propietaria'
        owner_match = re.search(owner_pattern, text)
        if owner_match:
            fault_info["equipment_owner"] = owner_match.group(1).strip()

        # Información básica (mantener compatibilidad)
        consumption_pattern = r'Consumos desconectados \(MW\)\s+([0-9.]+)'
        consumption_match = re.search(consumption_pattern, text)
        if consumption_match:
            fault_info["disconnected_consumption_mw"] = float(consumption_match.group(1))

        demand_pattern = r'Demanda previa del sistema \(MW\)\s+([0-9.]+)'
        demand_match = re.search(demand_pattern, text)
        if demand_match:
            fault_info["previous_system_demand_mw"] = float(demand_match.group(1))

        percentage_pattern = r'Porcentaje de desconexión\s+(\d+)%'
        percentage_match = re.search(percentage_pattern, text)
        if percentage_match:
            fault_info["disconnection_percentage"] = int(percentage_match.group(1))

        qualification_pattern = r'Calificación\s+([^\n]+)'
        qualification_match = re.search(qualification_pattern, text)
        if qualification_match:
            fault_info["classification"] = qualification_match.group(1).strip()

        return fault_info

    def _extract_technical_data(self, text: str) -> List[Dict]:
        """Extrae datos técnicos del texto."""
        entities = []

        # Extraer voltajes
        voltage_pattern = r'(\d+(?:\.\d+)?)\s*k?V'
        voltages = re.findall(voltage_pattern, text, re.IGNORECASE)
        for voltage in set(voltages):  # Remove duplicates
            entities.append({
                "type": "voltage",
                "category": "technical_parameter",
                "value": voltage,
                "unit": "kV"
            })

        # Extraer potencias en MW
        power_pattern = r'(\d+(?:\.\d+)?)\s*MW'
        powers = re.findall(power_pattern, text, re.IGNORECASE)
        for power in set(powers):
            entities.append({
                "type": "power",
                "category": "technical_parameter",
                "value": power,
                "unit": "MW"
            })

        # Extraer fechas
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        dates = re.findall(date_pattern, text)
        for date in set(dates):
            entities.append({
                "type": "date",
                "category": "temporal_reference",
                "value": date
            })

        # Extraer horas
        time_pattern = r'(\d{1,2}:\d{2})'
        times = re.findall(time_pattern, text)
        for time in set(times):
            entities.append({
                "type": "time",
                "category": "temporal_reference",
                "value": time
            })

        return entities

    def _extract_companies(self, text: str) -> List[Dict]:
        """Extrae nombres de empresas del texto."""
        entities = []

        # Patrones de empresas típicas del sector eléctrico chileno
        company_patterns = [
            r'([A-Z][A-Z\s&\.]+(?:S\.A\.|SPA|LTDA))',
            r'(Enel\s+\w+)',
            r'(Colbún\s+\w*)',
            r'(AES\s+\w+)',
            r'(ENGIE\s+\w*)',
            r'(Coordinador\s+Eléctrico\s+Nacional)'
        ]

        for pattern in company_patterns:
            companies = re.findall(pattern, text, re.IGNORECASE)
            for company in set(companies):
                if len(company.strip()) > 3:  # Filter noise
                    entities.append({
                        "type": "company",
                        "category": "organization",
                        "name": company.strip()
                    })

        return entities

    def _extract_electrical_data(self, text: str) -> List[Dict]:
        """Extrae datos de equipos eléctricos incluyendo interruptores específicos."""
        entities = []

        # Extraer interruptores específicos (crítico para análisis de fallas)
        breaker_pattern = r'(\d+[A-Z]+\d*)'
        breakers = re.findall(breaker_pattern, text)
        for breaker in set(breakers):
            if len(breaker) >= 3:  # Filtrar códigos válidos
                entities.append({
                    "type": "circuit_breaker",
                    "category": "equipment",
                    "identifier": breaker.strip(),
                    "equipment_class": "protection_device"
                })

        # Extraer líneas de transmisión con más detalle
        line_patterns = [
            r'línea\s+de\s+transmisión\s+([0-9x]+\s*kV\s+[A-Za-z\s\-]+)',
            r'línea\s+([0-9x]+\s*kV\s+[A-Za-z\s\-]+)',
            r'circuitos?\s+de\s+la\s+línea\s+([0-9x]+\s*kV\s+[A-Za-z\s\-]+)'
        ]
        for pattern in line_patterns:
            lines = re.findall(pattern, text, re.IGNORECASE)
            for line in set(lines):
                entities.append({
                    "type": "transmission_line",
                    "category": "equipment",
                    "description": line.strip(),
                    "equipment_class": "transmission"
                })

        # Extraer subestaciones con más contexto
        substation_patterns = [
            r'S/E\s+([A-Za-z\s]+)',
            r'SS/EE\s+([A-Za-z\s,\-]+)',
            r'subestación\s+([A-Za-z\s]+)'
        ]
        for pattern in substation_patterns:
            substations = re.findall(pattern, text, re.IGNORECASE)
            for substation in set(substations):
                if len(substation.strip()) > 2:  # Filtrar nombres válidos
                    entities.append({
                        "type": "substation",
                        "category": "equipment",
                        "name": substation.strip(),
                        "equipment_class": "substation"
                    })

        # Extraer sistemas de protección específicos
        protection_patterns = [
            r'relés\s+(\w+\s+\w+)',
            r'función\s+([^)]+)\s+\((\w+)\)',
            r'protecciones\s+([^,]+)'
        ]
        for pattern in protection_patterns:
            protections = re.findall(pattern, text, re.IGNORECASE)
            for protection in protections:
                if isinstance(protection, tuple):
                    entities.append({
                        "type": "protection_function",
                        "category": "equipment",
                        "function_name": protection[0].strip(),
                        "function_code": protection[1].strip() if len(protection) > 1 else "",
                        "equipment_class": "protection_system"
                    })
                else:
                    entities.append({
                        "type": "protection_system",
                        "category": "equipment",
                        "name": protection.strip(),
                        "equipment_class": "protection_system"
                    })

        # Extraer circuitos específicos
        circuit_pattern = r'circuito\s+N°(\d+)'
        circuits = re.findall(circuit_pattern, text, re.IGNORECASE)
        for circuit in set(circuits):
            entities.append({
                "type": "circuit",
                "category": "equipment",
                "circuit_number": circuit,
                "equipment_class": "circuit"
            })

        return entities

    def _extract_temporal_sequence(self, text: str) -> List[Dict]:
        """Extrae la secuencia temporal detallada de eventos de la falla."""
        entities = []

        # Eventos temporales específicos
        temporal_events = [
            # Evento inicial
            (r'A las (\d{1,2}:\d{2}:\d{2}) horas.*?ocurre.*?apertura intempestiva', 'fault_initiation'),
            # Reconexión automática
            (r'(\d+\.?\d*) segundos más tarde.*?reconexión automática', 'automatic_reconnection'),
            # Oscilaciones de potencia
            (r'durante aproximadamente (\d+) segundo.*?oscilaciones de potencia', 'power_oscillations'),
            # Colapso de islas
            (r'(\d+) minutos.*?colapsó', 'north_island_collapse'),
            (r'(\d+) segundos.*?isla sur colapsó', 'south_island_collapse'),
        ]

        for pattern, event_type in temporal_events:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                entities.append({
                    "type": "temporal_event",
                    "category": "temporal_reference",
                    "event_type": event_type,
                    "timing": match if isinstance(match, str) else match[0],
                    "context": "fault_sequence"
                })

        # Extraer descripciones de causas específicas
        cause_patterns = [
            (r'actuación no esperada e imprevista.*?función diferencial de línea', 'unexpected_differential_operation'),
            (r'falla del módulo de comunicaciones principal', 'communication_module_failure'),
            (r'intento de recuperación del canal.*?resincronización', 'channel_recovery_attempt'),
        ]

        for pattern, cause_type in cause_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                entities.append({
                    "type": "fault_cause",
                    "category": "analysis",
                    "cause_type": cause_type,
                    "description": pattern.replace('.*?', ' ')
                })

        # Extraer efectos del sistema
        system_effects = [
            (r'conformación de dos islas eléctricas', 'electrical_island_formation'),
            (r'isla excedentaria al norte', 'north_surplus_island'),
            (r'isla deficitaria al sur', 'south_deficit_island'),
            (r'desconexión de unidades generadoras', 'generator_disconnection'),
            (r'elevadas tensiones.*?desconexión sucesiva', 'high_voltage_cascade'),
            (r'no ser posible controlar la caída de la frecuencia', 'frequency_control_loss'),
        ]

        for pattern, effect_type in system_effects:
            if re.search(pattern, text, re.IGNORECASE):
                entities.append({
                    "type": "system_effect",
                    "category": "analysis",
                    "effect_type": effect_type,
                    "description": effect_type.replace('_', ' ')
                })

        return entities

    def _process_page_content(self, page_text: str) -> Dict:
        """Procesa el contenido de una página con análisis estructurado e inteligente."""
        lines = page_text.split('\n')
        page_num = None

        # Extraer número de página
        if lines:
            first_line = lines[0].strip()
            page_match = re.search(r'(\d+)\s+===', first_line)
            if page_match:
                page_num = int(page_match.group(1))

        # Obtener contenido completo (sin el header de página)
        content_lines = [line.strip() for line in lines[1:] if len(line.strip()) > 0]
        full_content = '\n'.join(content_lines)

        # Procesamiento inteligente del contenido
        processed_content = self._analyze_page_content(full_content)

        return {
            "page_number": page_num,
            "content_analysis": processed_content,  # Análisis estructurado
            "raw_content": full_content,  # Mantener también el raw por si acaso
            "character_count": len(full_content),
            "processing_metadata": {
                "content_lines_count": len(content_lines),
                "contains_technical_detail": len(full_content) > 500,
                "analysis_confidence": processed_content.get("confidence_score", 0.0)
            }
        }

    def _analyze_page_content(self, content: str) -> Dict:
        """Analiza y estructura inteligentemente el contenido de una página."""
        analysis = {
            "content_type": "unknown",
            "hierarchical_structure": {},
            "subsections": {},
            "tabular_data": {},
            "confidence_score": 0.0
        }

        # Detectar tipo de contenido con mejor precisión
        content_type = self._detect_content_type(content)
        analysis["content_type"] = content_type["type"]
        analysis["confidence_score"] = content_type["confidence"]

        # Filtrar ruido antes del procesamiento
        clean_content = self._filter_noise(content)

        # Extraer estructura jerárquica organizada por subsecciones
        analysis["hierarchical_structure"] = self._extract_hierarchical_structure(clean_content)

        # Extraer subsecciones organizadas (d.1, d.2, d.3, etc.)
        analysis["subsections"] = self._extract_organized_subsections(clean_content)

        # Extraer datos tabulares específicos para EAF
        if analysis["content_type"] == "company_reports":
            analysis["tabular_data"] = self._extract_company_reports_table(clean_content)
        elif analysis["content_type"] == "technical_data":
            analysis["tabular_data"] = self._extract_technical_data_table(clean_content)
        elif analysis["content_type"] == "fault_data":
            analysis["tabular_data"] = self._extract_fault_data_table(clean_content)

        # Enriquecer con análisis OCR si está disponible
        if self.ocr_detector:
            analysis["ocr_enhancement"] = self._enhance_with_ocr_analysis(content, analysis)

        return analysis

    def _enhance_with_ocr_analysis(self, original_content: str, current_analysis: Dict) -> Dict:
        """Enriquece el análisis con información del OCR."""
        try:
            # Intentar determinar el número de página del contenido
            page_num = self._extract_page_number_from_content(original_content)

            if page_num is None:
                return {"status": "no_page_detected"}

            # Obtener análisis OCR de la página
            ocr_result = self.ocr_detector.detect_page_structures(page_num)

            if "error" in ocr_result:
                return {"status": "ocr_error", "error": ocr_result["error"]}

            enhancement = {
                "page_number": page_num,
                "visual_layout": ocr_result["detected_structures"]["layout_type"],
                "ocr_confidence": ocr_result["detected_structures"]["structure_confidence"],
                "table_detection": {
                    "tables_detected": ocr_result["table_detection"]["tables_found"],
                    "table_confidence": ocr_result["table_detection"]["confidence"]
                },
                "text_structure_validation": ocr_result["text_analysis"],
                "recommendations": []
            }

            # Generar recomendaciones basadas en OCR
            enhancement["recommendations"] = self._generate_ocr_recommendations(
                current_analysis, ocr_result
            )

            return enhancement

        except Exception as e:
            self.logger.warning(f"Error en análisis OCR: {e}")
            return {"status": "error", "error": str(e)}

    def _extract_page_number_from_content(self, content: str) -> int:
        """Extrae el número de página del contenido."""
        # Buscar patrón "Página X de Y"
        page_match = re.search(r'Página (\d+) de \d+', content)
        if page_match:
            return int(page_match.group(1))

        # Buscar patrón en primera línea
        lines = content.split('\n')
        for line in lines[:3]:  # Revisar primeras 3 líneas
            if re.search(r'Página \d+', line):
                num_match = re.search(r'(\d+)', line)
                if num_match:
                    return int(num_match.group(1))

        return None

    def _generate_ocr_recommendations(self, text_analysis: Dict, ocr_result: Dict) -> List[str]:
        """Genera recomendaciones basadas en comparación OCR vs texto."""
        recommendations = []

        # Comparar detección de tablas
        text_detected_tables = "company_reports" in text_analysis.get("content_type", "")
        ocr_detected_tables = ocr_result["table_detection"]["tables_found"] > 0

        if ocr_detected_tables and not text_detected_tables:
            recommendations.append("OCR detectó tablas que el análisis de texto no capturó - considerar revisión manual")

        if text_detected_tables and not ocr_detected_tables:
            recommendations.append("Análisis de texto detectó tablas que OCR no confirmó - verificar estructura visual")

        # Comparar confianza de estructura
        ocr_confidence = ocr_result["detected_structures"]["structure_confidence"]
        if ocr_confidence < 0.5:
            recommendations.append("Baja confianza en estructura visual - contenido puede estar mal escaneado")

        # Validar tipo de layout detectado
        layout_type = ocr_result["detected_structures"]["layout_type"]
        if layout_type == "multi_table" and text_analysis.get("content_type") != "company_reports":
            recommendations.append("OCR detectó múltiples tablas - considerar procesamiento especializado")

        return recommendations

    def _detect_content_type(self, content: str) -> Dict:
        """Detecta el tipo de contenido con mayor precisión."""
        # Patrones específicos para tipos de contenido
        patterns = {
            "fault_analysis": {
                "keywords": ['origen y causa', 'falla', 'apertura intempestiva', 'interruptor'],
                "patterns": [r'd\.\d+\s+Origen y causa', r'apertura intempestiva', r'52K\d+'],
                "confidence": 0.95
            },
            "company_reports": {
                "keywords": ['empresa', 'informe', 'plazo', 'informes en plazo', 'informes fuera de plazo'],
                "patterns": [r'\d+\s+informes?\s+(en|fuera de)\s+plazo', r'S\.A\.\s+\d+\s+informe'],
                "confidence": 0.9
            },
            "technical_data": {
                "keywords": ['tensión nominal', 'propietario', 'instalación afectada', 'elemento fallado'],
                "patterns": [r'Tensión nominal\s+\d+\s*kV', r'Propietario.*S\.A\.', r'RUT\s+\d+'],
                "confidence": 0.85
            },
            "fault_data": {
                "keywords": ['consumos desconectados', 'demanda previa', 'porcentaje', 'calificación'],
                "patterns": [r'Consumos desconectados.*MW', r'Porcentaje de desconexión.*%'],
                "confidence": 0.88
            },
            "reiterations": {
                "keywords": ['reiteración', 'fenómeno físico', 'últimos 24 meses'],
                "patterns": [r'd\.\d+\s+Reiteración', r'últimos 24 meses móviles'],
                "confidence": 0.8
            }
        }

        scores = {}
        for content_type, criteria in patterns.items():
            score = 0

            # Puntaje por keywords
            keyword_matches = sum(1 for keyword in criteria["keywords"] if keyword in content.lower())
            score += keyword_matches * 0.3

            # Puntaje por patrones regex
            pattern_matches = sum(1 for pattern in criteria["patterns"] if re.search(pattern, content, re.IGNORECASE))
            score += pattern_matches * 0.5

            scores[content_type] = score * criteria["confidence"]

        # Determinar el tipo con mayor puntaje
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] > 0.3:  # Umbral mínimo
                return {"type": best_type, "confidence": min(scores[best_type], 0.95)}

        return {"type": "unknown", "confidence": 0.1}

    def _filter_noise(self, content: str) -> str:
        """Filtra ruido y contenido irrelevante."""
        lines = content.split('\n')
        clean_lines = []

        # Filtros de ruido
        noise_patterns = [
            r'^Página \d+ de \d+$',           # Números de página
            r'^\s*=== PÁGINA \d+ ===$',      # Separadores de página
            r'^\s*$',                        # Líneas vacías
            r'^[-\s]+$',                     # Líneas con solo guiones o espacios
            r'^\s*\.\s*$'                    # Líneas con solo puntos
        ]

        for line in lines:
            # Saltar líneas que coinciden con patrones de ruido
            if any(re.match(pattern, line.strip()) for pattern in noise_patterns):
                continue

            # Limpiar espacios excesivos
            clean_line = re.sub(r'\s+', ' ', line.strip())

            if clean_line:  # Solo agregar líneas no vacías
                clean_lines.append(clean_line)

        return '\n'.join(clean_lines)

    def _extract_company_reports_table(self, content: str) -> Dict:
        """Extrae tablas estructuradas de informes de empresas."""
        company_data = {
            "table_type": "company_reports",
            "headers": ["Empresa", "Informe 48h", "Informe 5 días"],
            "companies": [],
            "summary": {"total_companies": 0, "reports_48h": {}, "reports_5d": {}}
        }

        # Patrón para detectar filas de empresas con informes
        company_pattern = r'([A-ZÁÉÍÓÚ][A-ZÁÉÍÓÚ\s\.\-&]+(?:S\.A\.|SPA|Ltda\.?|SCM|S\.C\.M\.|Limited))\s+(.+?)\s+(.+?)(?=\n|$)'

        matches = re.findall(company_pattern, content, re.MULTILINE | re.DOTALL)

        for company_name, report_48h, report_5d in matches:
            # Limpiar nombres de empresa
            clean_company = re.sub(r'\s+', ' ', company_name.strip())

            # Parsear informes de 48 horas
            reports_48h_parsed = self._parse_report_status(report_48h)

            # Parsear informes de 5 días
            reports_5d_parsed = self._parse_report_status(report_5d)

            company_entry = {
                "company_name": clean_company,
                "reports_48h": reports_48h_parsed,
                "reports_5d": reports_5d_parsed,
                "company_type": self._classify_company_type(clean_company)
            }

            company_data["companies"].append(company_entry)

        # Generar resumen
        company_data["summary"]["total_companies"] = len(company_data["companies"])

        # Estadísticas de informes
        for company in company_data["companies"]:
            # Contar estados de informes de 48h
            status_48h = company["reports_48h"]["status"]
            company_data["summary"]["reports_48h"][status_48h] = company_data["summary"]["reports_48h"].get(status_48h, 0) + 1

        return company_data

    def _parse_report_status(self, report_text: str) -> Dict:
        """Parsea el estado de los informes de una empresa."""
        report_info = {
            "raw_text": report_text.strip(),
            "count_on_time": 0,
            "count_late": 0,
            "count_not_received": 0,
            "status": "unknown",
            "details": []
        }

        # Patrones para diferentes estados
        patterns = {
            "on_time": r'(\d+)\s+informes?\s+en\s+plazo',
            "late": r'(\d+)\s+informes?\s+fuera\s+de\s+plazo',
            "not_received": r'(\d+)\s+informes?\s+no\s+recibido'
        }

        for status, pattern in patterns.items():
            matches = re.findall(pattern, report_text, re.IGNORECASE)
            if matches:
                count = sum(int(match) for match in matches)
                if status == "on_time":
                    report_info["count_on_time"] = count
                elif status == "late":
                    report_info["count_late"] = count
                elif status == "not_received":
                    report_info["count_not_received"] = count

        # Determinar estado general
        if report_info["count_late"] > 0 or report_info["count_not_received"] > 0:
            report_info["status"] = "issues"
        elif report_info["count_on_time"] > 0:
            report_info["status"] = "compliant"
        else:
            report_info["status"] = "unknown"

        return report_info

    def _classify_company_type(self, company_name: str) -> str:
        """Clasifica el tipo de empresa basado en su nombre."""
        name_lower = company_name.lower()

        if any(word in name_lower for word in ['generación', 'generadora', 'eólica', 'solar', 'hidro']):
            return "generation"
        elif any(word in name_lower for word in ['transmisión', 'transmisora', 'eléctrica']):
            return "transmission"
        elif any(word in name_lower for word in ['distribución', 'distribuidora']):
            return "distribution"
        elif any(word in name_lower for word in ['minera', 'mining', 'codelco']):
            return "mining"
        elif any(word in name_lower for word in ['cooperativa']):
            return "cooperative"
        else:
            return "other"

    def _extract_technical_data_table(self, content: str) -> Dict:
        """Extrae tablas de datos técnicos."""
        technical_data = {
            "table_type": "technical_specifications",
            "sections": {},
            "summary": {}
        }

        # Secciones de datos técnicos comunes
        sections = {
            "installation_data": {
                "patterns": [
                    (r'Nombre de la instalación\s+(.+)', 'installation_name'),
                    (r'Tipo de instalación\s+(.+)', 'installation_type'),
                    (r'Tensión nominal\s+(.+)', 'nominal_voltage'),
                    (r'Segmento\s+(.+)', 'segment'),
                    (r'Propietario instalación afectada\s+(.+)', 'owner')
                ]
            },
            "fault_element": {
                "patterns": [
                    (r'Nombre del elemento afectado\s+(.+)', 'element_name'),
                    (r'Propietario elemento fallado\s+(.+)', 'element_owner')
                ]
            },
            "legal_data": {
                "patterns": [
                    (r'RUT\s+([\d\.\-]+)', 'rut'),
                    (r'Representante Legal\s+(.+)', 'legal_representative'),
                    (r'Dirección\s+(.+)', 'address')
                ]
            }
        }

        for section_name, section_config in sections.items():
            section_data = {}
            for pattern, field_name in section_config["patterns"]:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    section_data[field_name] = match.group(1).strip()

            if section_data:  # Solo agregar si se encontró data
                technical_data["sections"][section_name] = section_data

        return technical_data

    def _extract_fault_data_table(self, content: str) -> Dict:
        """Extrae tabla de datos de falla."""
        fault_data = {
            "table_type": "fault_metrics",
            "fault_info": {},
            "timing": {},
            "classification": {}
        }

        # Patrones para datos de falla
        fault_patterns = [
            (r'Fecha\s+(\d{2}/\d{2}/\d{4})', 'fault_date', 'timing'),
            (r'Hora\s+(\d{1,2}:\d{2})', 'fault_time', 'timing'),
            (r'Consumos desconectados \(MW\)\s+([\d\.]+)', 'disconnected_consumption_mw', 'fault_info'),
            (r'Demanda previa del sistema \(MW\)\s+([\d\.]+)', 'previous_demand_mw', 'fault_info'),
            (r'Porcentaje de desconexión\s+(\d+)%', 'disconnection_percentage', 'fault_info'),
            (r'Calificación\s+(.+)', 'classification_text', 'classification')
        ]

        for pattern, field_name, category in fault_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()

                # Convertir valores numéricos
                if field_name in ['disconnected_consumption_mw', 'previous_demand_mw']:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                elif field_name == 'disconnection_percentage':
                    try:
                        value = int(value)
                    except ValueError:
                        pass

                fault_data[category][field_name] = value

        return fault_data

    def _extract_hierarchical_structure(self, content: str) -> Dict:
        """Extrae estructura jerárquica organizada por subsecciones."""
        structure = {
            "document_sections": {},
            "subsection_order": [],
            "content_organization": "hierarchical"
        }

        # Buscar subsecciones principales (d.1, d.2, d.3, etc.)
        subsection_pattern = r'd\.(\d+)\s+([^\n]+)'
        subsections = re.findall(subsection_pattern, content, re.MULTILINE)

        for subsection_num, subsection_title in subsections:
            subsection_key = f"d.{subsection_num}"
            structure["subsection_order"].append(subsection_key)

            # Extraer contenido de esta subsección específica
            subsection_content = self._extract_subsection_content(content, subsection_key)

            structure["document_sections"][subsection_key] = {
                "title": subsection_title.strip(),
                "subsection_number": subsection_num,
                "content_analysis": self._analyze_subsection_content(subsection_content),
                "sub_points": self._extract_sub_points(subsection_content),
                "technical_data": self._extract_technical_from_subsection(subsection_content)
            }

        return structure

    def _extract_organized_subsections(self, content: str) -> Dict:
        """Extrae subsecciones de manera organizada y limpia."""
        organized = {}

        # Patrones para diferentes niveles de organización
        patterns = {
            "main_subsections": r'd\.(\d+)\s+([^\n]+)',
            "sub_points": r'([a-z])\)\s+([^\n]+)',
            "numbered_points": r'(\d+)\.\s+([A-Z][^\n]{10,})',
            "bullet_points": r'[-•]\s+([^\n]+)'
        }

        # Extraer subsecciones principales
        main_subsections = re.findall(patterns["main_subsections"], content, re.MULTILINE)

        for subsection_num, title in main_subsections:
            subsection_key = f"d.{subsection_num}"
            subsection_content = self._extract_subsection_content(content, subsection_key)

            organized[subsection_key] = {
                "title": title.strip(),
                "content": subsection_content,
                "sub_structure": {
                    "sub_points": self._extract_sub_points_organized(subsection_content),
                    "technical_elements": self._extract_technical_elements_clean(subsection_content),
                    "key_information": self._extract_key_info_organized(subsection_content)
                }
            }

        return organized

    def _extract_subsection_content(self, full_content: str, subsection_id: str) -> str:
        """Extrae el contenido específico de una subsección."""
        # Buscar desde la subsección actual hasta la siguiente
        pattern = rf'{re.escape(subsection_id)}\s+[^\n]+\n(.*?)(?=d\.\d+|$)'
        match = re.search(pattern, full_content, re.DOTALL)

        if match:
            return match.group(1).strip()
        else:
            # Si no encuentra el patrón, buscar de manera más flexible
            lines = full_content.split('\n')
            start_idx = None

            for i, line in enumerate(lines):
                if subsection_id in line:
                    start_idx = i
                    break

            if start_idx is not None:
                # Buscar hasta la siguiente subsección o final
                end_idx = len(lines)
                for i in range(start_idx + 1, len(lines)):
                    if re.match(r'd\.\d+', lines[i]):
                        end_idx = i
                        break

                return '\n'.join(lines[start_idx + 1:end_idx]).strip()

        return ""

    def _analyze_subsection_content(self, subsection_content: str) -> Dict:
        """Analiza el contenido específico de una subsección."""
        analysis = {
            "content_type": "subsection_detail",
            "key_topics": [],
            "temporal_references": [],
            "equipment_mentions": [],
            "causes_and_effects": {}
        }

        # Identificar temas clave
        if "origen" in subsection_content.lower() and "causa" in subsection_content.lower():
            analysis["key_topics"].append("fault_origin_analysis")
        if "apertura" in subsection_content.lower() and "interruptor" in subsection_content.lower():
            analysis["key_topics"].append("breaker_operation")
        if "protección" in subsection_content.lower():
            analysis["key_topics"].append("protection_system")

        # Extraer referencias temporales
        time_patterns = [
            r'(\d{1,2}:\d{2}:\d{2})',
            r'(\d+\.?\d*)\s*segundos?',
            r'(\d+)\s*minutos?'
        ]

        for pattern in time_patterns:
            matches = re.findall(pattern, subsection_content)
            for match in matches:
                analysis["temporal_references"].append({
                    "value": match,
                    "context": self._extract_context(subsection_content, match)
                })

        return analysis

    def _extract_sub_points(self, subsection_content: str) -> List[Dict]:
        """Extrae sub-puntos dentro de una subsección."""
        sub_points = []

        # Patrones para diferentes tipos de sub-puntos
        patterns = [
            (r'([a-z])\)\s+([^\n]+)', 'lettered_point'),
            (r'(\d+)\.\s+([A-Z][^\n]{15,})', 'numbered_point'),
            (r'[-•]\s+([^\n]+)', 'bullet_point'),
            (r'(OPE\d+):\s*([^\n]+)', 'operation_code')
        ]

        for pattern, point_type in patterns:
            matches = re.findall(pattern, subsection_content, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    sub_points.append({
                        "type": point_type,
                        "identifier": match[0],
                        "content": match[1].strip(),
                        "technical_data": self._extract_technical_from_text(match[1])
                    })

        return sub_points

    def _extract_sub_points_organized(self, content: str) -> Dict:
        """Extrae sub-puntos de manera organizada."""
        organized_points = {
            "lettered_points": {},
            "numbered_points": {},
            "bullet_points": [],
            "operation_codes": {}
        }

        # Puntos con letras (a), b), c))
        lettered = re.findall(r'([a-z])\)\s+([^\n]+)', content, re.MULTILINE)
        for letter, text in lettered:
            organized_points["lettered_points"][letter] = {
                "content": text.strip(),
                "technical_elements": self._extract_technical_from_text(text)
            }

        # Puntos numerados
        numbered = re.findall(r'(\d+)\.\s+([A-Z][^\n]{15,})', content, re.MULTILINE)
        for number, text in numbered:
            organized_points["numbered_points"][number] = {
                "content": text.strip(),
                "technical_elements": self._extract_technical_from_text(text)
            }

        # Códigos de operación
        op_codes = re.findall(r'(OPE\d+):\s*([^\n]+)', content, re.MULTILINE)
        for code, description in op_codes:
            organized_points["operation_codes"][code] = description.strip()

        return organized_points

    def _extract_technical_from_subsection(self, content: str) -> Dict:
        """Extrae datos técnicos específicos de una subsección."""
        technical_data = {
            "voltages": [],
            "powers": [],
            "times": [],
            "equipment_codes": [],
            "protection_functions": []
        }

        # Extraer voltajes
        voltages = re.findall(r'(\d+(?:\.\d+)?)\s*kV', content, re.IGNORECASE)
        technical_data["voltages"] = [{"value": v, "unit": "kV"} for v in set(voltages)]

        # Extraer potencias
        powers = re.findall(r'(\d+(?:\.\d+)?)\s*MW', content, re.IGNORECASE)
        technical_data["powers"] = [{"value": p, "unit": "MW"} for p in set(powers)]

        # Extraer tiempos específicos
        times = re.findall(r'(\d{1,2}:\d{2}:\d{2})', content)
        technical_data["times"] = [{"value": t, "type": "exact_time"} for t in set(times)]

        # Extraer códigos de equipos (interruptores)
        equipment = re.findall(r'(52K\d+)', content)
        technical_data["equipment_codes"] = [{"code": eq, "type": "breaker"} for eq in set(equipment)]

        # Extraer funciones de protección
        protection = re.findall(r'(\d+[A-Z]+)', content)
        technical_data["protection_functions"] = [{"function": prot} for prot in set(protection)]

        return technical_data

    def _extract_technical_elements_clean(self, content: str) -> List[Dict]:
        """Extrae elementos técnicos de manera limpia y organizada."""
        elements = []

        # Patrones técnicos organizados
        tech_patterns = [
            (r'(\d+(?:\.\d+)?)\s*kV', 'voltage', 'kV'),
            (r'(\d+(?:\.\d+)?)\s*MW', 'power', 'MW'),
            (r'(\d{1,2}:\d{2}:\d{2})', 'exact_time', 'time'),
            (r'(\d+\.?\d*)\s*segundos?', 'duration', 'seconds'),
            (r'(\d+)\s*minutos?', 'duration', 'minutes'),
            (r'(52K\d+)', 'breaker_code', 'equipment'),
            (r'(\d+[A-Z]+)', 'protection_function', 'protection'),
            (r'(OPE\d+)', 'operation_code', 'operation')
        ]

        for pattern, element_type, category in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in set(matches):  # Remove duplicates
                elements.append({
                    "type": element_type,
                    "value": match,
                    "category": category,
                    "context": self._extract_context(content, match)[:100] + "..." if len(self._extract_context(content, match)) > 100 else self._extract_context(content, match)
                })

        return elements

    def _extract_key_info_organized(self, content: str) -> Dict:
        """Extrae información clave de manera organizada."""
        key_info = {
            "fault_details": {},
            "timeline": {},
            "equipment_involved": {},
            "causes": {},
            "effects": {}
        }

        # Información de falla
        if "apertura intempestiva" in content.lower():
            key_info["fault_details"]["type"] = "apertura intempestiva"

        # Línea de tiempo
        time_matches = re.findall(r'(\d{1,2}:\d{2}:\d{2})', content)
        if time_matches:
            key_info["timeline"]["fault_time"] = time_matches[0]

        # Equipos involucrados
        breakers = re.findall(r'(52K\d+)', content)
        if breakers:
            key_info["equipment_involved"]["breakers"] = list(set(breakers))

        return key_info

    def _extract_context(self, text: str, target: str) -> str:
        """Extrae contexto alrededor de un texto objetivo."""
        target_pos = text.find(target)
        if target_pos == -1:
            return ""

        start = max(0, target_pos - 50)
        end = min(len(text), target_pos + len(target) + 50)
        return text[start:end].strip()

    def _extract_technical_from_text(self, text: str) -> List[Dict]:
        """Extrae elementos técnicos de un texto específico."""
        elements = []

        # Patrones técnicos básicos
        patterns = [
            (r'(\d+(?:\.\d+)?)\s*kV', 'voltage'),
            (r'(\d+(?:\.\d+)?)\s*MW', 'power'),
            (r'(52K\d+)', 'breaker'),
            (r'(\d+[A-Z]+)', 'protection_function')
        ]

        for pattern, element_type in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                elements.append({
                    "type": element_type,
                    "value": match
                })

        return elements

    def _extract_structured_sections(self, content: str) -> List[Dict]:
        """Extrae secciones del contenido de manera estructurada."""
        sections = []

        # Patrones para diferentes tipos de secciones
        section_patterns = [
            (r'd\.(\d+)\s+([^.\n]+)', 'subsection'),
            (r'(\d+)\.\s+([A-Z][^.\n]{20,})', 'main_section'),
            (r'([A-Z][^:\n]{15,}):', 'titled_section'),
            (r'(OPE\d+):\s*([^.\n]+)', 'operation_code')
        ]

        for pattern, section_type in section_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    sections.append({
                        "type": section_type,
                        "identifier": match[0].strip(),
                        "title": match[1].strip(),
                        "full_match": f"{match[0]} {match[1]}".strip()
                    })

        return sections

    def _extract_fault_analysis_info(self, content: str) -> Dict:
        """Extrae información específica de análisis de fallas."""
        fault_info = {}

        # Extraer información temporal estructurada
        temporal_data = {}
        time_patterns = [
            (r'A las (\d{1,2}:\d{2}:\d{2}) horas.*?del día (\d{1,2} de \w+ de \d{4})', 'exact_fault_time'),
            (r'(\d+\.?\d*) segundos.*?reconexión automática', 'reconnection_delay'),
            (r'durante aproximadamente (\d+) segundo.*?oscilaciones', 'oscillation_duration'),
            (r'(\d+) minutos.*?colapsó', 'collapse_time_north'),
            (r'(\d+) segundos.*?isla sur colapsó', 'collapse_time_south')
        ]

        for pattern, info_type in time_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                temporal_data[info_type] = {
                    "value": match.group(1),
                    "context": match.group(0)[:100] + "..." if len(match.group(0)) > 100 else match.group(0)
                }

        fault_info["temporal_sequence"] = temporal_data

        # Extraer equipos involucrados de forma estructurada
        equipment_data = {}

        # Interruptores específicos
        breaker_pattern = r'interruptores\s+((?:\d+\w+[,\s]*)+)'
        breaker_matches = re.findall(breaker_pattern, content)
        if breaker_matches:
            equipment_data["circuit_breakers"] = [
                {"identifiers": match.strip(), "action": "opened"}
                for match in breaker_matches
            ]

        # Subestaciones
        substation_pattern = r'S/E\s+([A-Za-z\s]+)'
        substations = re.findall(substation_pattern, content)
        if substations:
            equipment_data["substations"] = [
                {"name": sub.strip(), "role": "affected"}
                for sub in set(substations)
            ]

        fault_info["equipment_involved"] = equipment_data

        # Extraer análisis de causas
        cause_analysis = {}

        # Función de protección
        protection_pattern = r'función ([^)]+)\s+\((\w+)\)'
        protection_match = re.search(protection_pattern, content)
        if protection_match:
            cause_analysis["protection_function"] = {
                "name": protection_match.group(1).strip(),
                "code": protection_match.group(2).strip(),
                "description": "función diferencial de línea"
            }

        # Sistema de relés
        relay_pattern = r'relés\s+(\w+\s+\w+)'
        relay_matches = re.findall(relay_pattern, content)
        if relay_matches:
            cause_analysis["relay_systems"] = [
                {"model": relay.strip(), "status": "affected"}
                for relay in set(relay_matches)
            ]

        # Empresa responsable
        owner_pattern = r'empresa ([^,]+),\s*propietari?a'
        owner_match = re.search(owner_pattern, content, re.IGNORECASE)
        if owner_match:
            cause_analysis["equipment_owner"] = {
                "company": owner_match.group(1).strip(),
                "responsibility": "protection_systems"
            }

        fault_info["cause_analysis"] = cause_analysis

        # Extraer efectos del sistema
        system_effects = {}

        if "islas eléctricas" in content:
            system_effects["electrical_islands"] = {
                "formation": True,
                "north_island": {
                    "type": "surplus",
                    "stability": "temporary",
                    "collapse_time": temporal_data.get("collapse_time_north", {}).get("value")
                },
                "south_island": {
                    "type": "deficit",
                    "stability": "immediate_collapse",
                    "collapse_time": temporal_data.get("collapse_time_south", {}).get("value")
                }
            }

        fault_info["system_effects"] = system_effects

        return fault_info

    def _extract_company_info(self, content: str) -> Dict:
        """Extrae información estructurada de empresas."""
        company_info = {}

        # Buscar patrones de empresas y sus estados
        company_patterns = [
            (r'([A-Z][A-Z\s&\.]+(?:S\.A\.|SPA|LTDA))\s+(\d+)\s*informes?\s+(en plazo|fuera de plazo|no recibido)', 'report_status'),
            (r'([A-Z][A-Z\s&\.]+(?:S\.A\.|SPA|LTDA))\s+S/E\s+([A-Za-z\s]+)', 'substation_association')
        ]

        for pattern, info_type in company_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                company_info[info_type] = [
                    {"company": match[0].strip(), "details": match[1:]}
                    for match in matches
                ]

        return company_info

    def _extract_table_info(self, content: str) -> Dict:
        """Extrae información estructurada de tablas."""
        table_info = {}

        # Detectar filas de tabla (líneas con múltiples campos separados)
        lines = content.split('\n')
        table_rows = []

        for line in lines:
            # Buscar líneas que parecen filas de tabla
            if '\t' in line or (line.count('  ') >= 2 and any(c.isdigit() for c in line)):
                parts = re.split(r'\s{2,}|\t', line.strip())
                if len(parts) >= 3:  # Al menos 3 columnas
                    table_rows.append([part.strip() for part in parts if part.strip()])

        if table_rows:
            table_info["detected_table"] = {
                "row_count": len(table_rows),
                "sample_rows": table_rows[:3],  # Primeras 3 filas como muestra
                "column_count": max(len(row) for row in table_rows) if table_rows else 0
            }

        return table_info

    def _extract_technical_elements(self, content: str) -> List[Dict]:
        """Extrae elementos técnicos específicos del contenido."""
        technical_elements = []

        # Patrones técnicos específicos
        tech_patterns = [
            (r'(\d+(?:\.\d+)?)\s*MW', 'power', 'MW'),
            (r'(\d+(?:\.\d+)?)\s*kV', 'voltage', 'kV'),
            (r'(\d+(?:\.\d+)?)\s*segundos?', 'time_duration', 'seconds'),
            (r'(\d+(?:\.\d+)?)\s*minutos?', 'time_duration', 'minutes'),
            (r'(\d+(?:\.\d+)?)\s*%', 'percentage', '%'),
            (r'(OPE\d+)', 'operation_code', 'code'),
            (r'(\d+[A-Z]+\d*)', 'equipment_code', 'breaker_id')
        ]

        for pattern, element_type, unit in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                technical_elements.append({
                    "type": element_type,
                    "value": match,
                    "unit": unit,
                    "context": "extracted_from_content"
                })

        return technical_elements

    def _save_raw_extraction(self, text: str) -> Path:
        """Guarda la extracción raw del texto."""
        raw_file = self.outputs_dir / "raw_extractions" / "capitulo_01_raw.txt"
        raw_file.parent.mkdir(parents=True, exist_ok=True)

        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(text)

        return raw_file

    def _save_processed_data(self, data: Dict) -> Path:
        """Guarda los datos procesados."""
        processed_file = self.outputs_dir / "validated_extractions" / "capitulo_01_processed.json"
        processed_file.parent.mkdir(parents=True, exist_ok=True)

        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return processed_file

    def _transform_to_universal_json(self, processed_data: Dict) -> Dict:
        """Transforma a esquema JSON universal preservando toda la información."""
        universal_data = {
            "document_metadata": {
                "eaf_number": "089/2025",
                "document_title": "Estudio para análisis de falla EAF 089/2025",
                "incident_description": "Desconexión forzada línea 2x500 kV Nueva Maitencillo - Nueva Pan de Azúcar",
                "emission_date": "18-03-2025"
            },
            "chapter": {
                "chapter_id": processed_data["chapter_id"],
                "number": 1,
                "title": processed_data["title"],
                "content_type": processed_data["content_type"],
                "page_range": "1-11",
                "processing_timestamp": processed_data["processing_timestamp"]
            },
            "entities": [],
            "records": processed_data.get("records", []),  # Preserve all records
            "technical_data": processed_data.get("technical_data", {}),  # Preserve technical data
            "relationships": [],
            "metadata": processed_data["metadata"]
        }

        # Transform ALL entities to universal format (preserving complete information)
        for i, entity in enumerate(processed_data["entities"]):
            universal_entity = {
                "id": f"eaf_089_2025_ch01_{entity['type']}_{i+1:04d}",  # Sequential ID
                "type": entity["type"],
                "category": entity["category"],
                "properties": {k: v for k, v in entity.items() if k not in ["type", "category"]},
                "source_chapter": 1,
                "extraction_confidence": 0.85,
                "original_data": entity  # Keep original data for reference
            }
            universal_data["entities"].append(universal_entity)

        # Add categorized entities for easier access
        universal_data["categorized_entities"] = self._categorize_entities(processed_data["entities"])

        # Add processing statistics
        universal_data["processing_statistics"] = {
            "total_entities": len(processed_data["entities"]),
            "total_records": len(processed_data.get("records", [])),
            "entities_by_type": self._count_entities_by_type(processed_data["entities"]),
            "entities_by_category": self._count_entities_by_category(processed_data["entities"])
        }

        return universal_data

    def _categorize_entities(self, entities: List[Dict]) -> Dict:
        """Categoriza entidades por tipo para fácil acceso."""
        categorized = {
            "companies": [],
            "technical_parameters": [],
            "equipment": [],
            "temporal_references": [],
            "incidents": [],
            "others": []
        }

        for entity in entities:
            entity_type = entity.get("type", "unknown")
            category = entity.get("category", "unknown")

            if entity_type == "company" or category == "organization":
                categorized["companies"].append(entity)
            elif category == "technical_parameter":
                categorized["technical_parameters"].append(entity)
            elif category == "equipment":
                categorized["equipment"].append(entity)
            elif category == "temporal_reference":
                categorized["temporal_references"].append(entity)
            elif entity_type == "fault_event" or category == "incident":
                categorized["incidents"].append(entity)
            else:
                categorized["others"].append(entity)

        return categorized

    def _count_entities_by_type(self, entities: List[Dict]) -> Dict:
        """Cuenta entidades por tipo."""
        counts = {}
        for entity in entities:
            entity_type = entity.get("type", "unknown")
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts

    def _count_entities_by_category(self, entities: List[Dict]) -> Dict:
        """Cuenta entidades por categoría."""
        counts = {}
        for entity in entities:
            category = entity.get("category", "unknown")
            counts[category] = counts.get(category, 0) + 1
        return counts

    def _save_universal_json(self, universal_data: Dict) -> Path:
        """Guarda el JSON universal."""
        universal_file = self.outputs_dir / "universal_json" / "capitulo_01_universal.json"
        universal_file.parent.mkdir(parents=True, exist_ok=True)

        with open(universal_file, 'w', encoding='utf-8') as f:
            json.dump(universal_data, f, indent=2, ensure_ascii=False)

        return universal_file

    def _ingest_to_database(self, universal_data: Dict) -> Dict:
        """Simula la ingesta a base de datos (solo dominio)."""
        # En implementación real, conectaría a shared/database/eaf_data.db
        self.logger.info(f"Simulando ingesta a BD para capítulo 1: {len(universal_data['entities'])} entidades")

        return {
            "status": "simulated",
            "entities_to_ingest": len(universal_data["entities"]),
            "target_database": "shared/database/eaf_data.db",
            "chapter_id": universal_data["chapter"]["chapter_id"]
        }


def main():
    """Ejecuta el procesador del capítulo 1."""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python capitulo_01_processor.py <pdf_path>")
        return

    pdf_path = sys.argv[1]
    processor = Capitulo01Processor(pdf_path)

    print("="*60)
    print("PROCESADOR CAPÍTULO 1 - DESCRIPCIÓN DE LA PERTURBACIÓN")
    print("="*60)

    results = processor.process_chapter()

    print(f"✅ Procesamiento completado")
    print(f"📄 Páginas procesadas: {results['chapter']['title']}")
    print(f"📊 Entidades extraídas: {results['stats']['entities_extracted']}")
    print(f"📝 Registros procesados: {results['stats']['records_count']}")
    print(f"💾 Archivos generados:")
    for file_type, file_path in results['files'].items():
        print(f"   - {file_type}: {file_path}")

    print("="*60)


if __name__ == "__main__":
    main()