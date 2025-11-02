#!/usr/bin/env python3
"""
INFORME DIARIO Day 1 Extractor
==============================

Extracts daily operational information from INFORME DIARIO Day 1 (Pages 101-134)
Date: Tuesday, February 25, 2025
Focus: Daily operational summary, system performance, incidents, and key metrics

This script extracts:
- Daily operational summary
- System performance metrics
- Incidents and events
- Load and generation balance
- Transmission system status
- Weather conditions impact
- Operational alerts and notifications

Usage:
    python extract_informe_diario_day1.py [page_number]
    python extract_informe_diario_day1.py --all  # Process all pages 101-134
"""

import sys
import re
import json
import io
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add project root to path (go up 6 levels from scripts/eaf_workflows/eaf_processing/chapters/informe_diario_day1/content_extraction/)
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from PyPDF2 import PdfReader
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Installing required packages: {e}")
    import os
    os.system("pip install PyPDF2 pytesseract pillow PyMuPDF opencv-python")
    from PyPDF2 import PdfReader
    import pytesseract
    from PIL import Image
    import fitz
    import cv2
    import numpy as np

def extract_date_info(raw_text: str) -> Dict:
    """Extract date and time information from the daily report"""
    date_info = {
        "report_date": "2025-02-25",  # Tuesday, February 25, 2025
        "day_name": "Tuesday",
        "extraction_timestamp": datetime.now().isoformat(),
        "page_range": "101-134"
    }

    # Look for specific date patterns in the text
    date_patterns = [
        r"(\d{1,2})\s+de\s+(febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+del?\s+(\d{4})",
        r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s+(\d{1,2})",
        r"(\d{1,2})/(\d{1,2})/(\d{4})"
    ]

    for pattern in date_patterns:
        match = re.search(pattern, raw_text.lower())
        if match:
            date_info["found_date_pattern"] = match.group(0)
            break

    return date_info

def extract_operational_summary(raw_text: str) -> Dict:
    """Extract operational summary information"""
    summary = {
        "system_status": "operational",
        "total_demand_mw": None,
        "peak_demand_mw": None,
        "peak_demand_time": None,
        "generation_sources": [],
        "transmission_status": "normal",
        "incidents_count": 0,
        "weather_conditions": "normal"
    }

    # Extract demand information
    demand_patterns = [
        r"demanda\s+máxima.*?(\d+(?:\.\d+)?)\s*mw",
        r"demanda\s+pico.*?(\d+(?:\.\d+)?)\s*mw",
        r"consumo.*?(\d+(?:\.\d+)?)\s*mw"
    ]

    for pattern in demand_patterns:
        match = re.search(pattern, raw_text.lower())
        if match:
            summary["peak_demand_mw"] = float(match.group(1))
            break

    # Extract time information
    time_patterns = [
        r"(\d{1,2}):(\d{2})\s*hrs?",
        r"(\d{1,2}):(\d{2})\s*horas?"
    ]

    for pattern in time_patterns:
        match = re.search(pattern, raw_text.lower())
        if match:
            summary["peak_demand_time"] = f"{match.group(1)}:{match.group(2)}"
            break

    return summary

def detect_abbreviations(raw_text: str) -> Dict:
    """Extract abbreviation definitions from the text"""
    abbreviations = {
        "abbreviations_found": [],
        "pmgd_plants": [],
        "is_abbreviations_page": False
    }

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    # Check if this is an abbreviations page
    abbreviation_indicators = ['abreviatura', 'abreviaciones', 'significado', 'definiciones', 'nomenclatura']
    has_abbreviation_section = any(indicator in raw_text.lower() for indicator in abbreviation_indicators)

    if has_abbreviation_section:
        abbreviations["is_abbreviations_page"] = True

        # Find the "Abreviaturas:" line
        abbrev_line_index = -1
        for i, line in enumerate(lines):
            if 'abreviatura' in line.lower():
                abbrev_line_index = i
                break

        # Extract abbreviation definitions from lines BEFORE "Abreviaturas:"
        if abbrev_line_index >= 0:
            # Look at lines before "Abreviaturas:" for definitions
            for i in range(max(0, abbrev_line_index - 20), abbrev_line_index):
                line = lines[i]
                # Pattern: ABC:Definition (with colon) - allow single character codes too
                abbrev_match = re.match(r'^([A-Z]{1,4}):(.+)$', line)
                if abbrev_match:
                    abbrev_code = abbrev_match.group(1)
                    definition = abbrev_match.group(2).strip()
                    abbreviations["abbreviations_found"].append({
                        "code": abbrev_code,
                        "definition": definition,
                        "raw_line": line
                    })

        # Also try general abbreviation extraction for any page
        for line in lines:
            # Pattern: ABC:Definition (with colon) - allow single character codes too
            abbrev_match = re.match(r'^([A-Z]{1,4}):(.+)$', line)
            if abbrev_match:
                abbrev_code = abbrev_match.group(1)
                definition = abbrev_match.group(2).strip()
                # Avoid duplicates
                existing_codes = [a["code"] for a in abbreviations["abbreviations_found"]]
                if abbrev_code not in existing_codes:
                    abbreviations["abbreviations_found"].append({
                        "code": abbrev_code,
                        "definition": definition,
                        "raw_line": line
                    })

    # Look for PMGD plants specifically
    for line in lines:
        if 'pmgd' in line.lower():
            # Extract PMGD plant information
            pmgd_match = re.match(r'^(PMGD\s+[A-Z]+)\s+(.+)$', line, re.IGNORECASE)
            if pmgd_match:
                pmgd_type = pmgd_match.group(1).upper()
                pmgd_name = pmgd_match.group(2).strip()
                abbreviations["pmgd_plants"].append({
                    "type": pmgd_type,
                    "name": pmgd_name,
                    "raw_line": line
                })

    return abbreviations

def detect_table_structure(raw_text: str) -> Dict:
    """Detect and parse tabular data structure with Estado column and multiple tables"""
    tables = {
        "power_plants": [],
        "left_table": [],
        "right_table": [],
        "generation_summary": [],
        "detected_tables": [],
        "abbreviations": None
    }

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    # Process multi-line power plant data structure
    i = 0
    current_table_side = "left"  # Track which table we're processing
    plant_count = 0  # Count plants to help detect table switch

    while i < len(lines):
        line = lines[i]

        # Look for plant name pattern - flexible approach with PMGD support
        # First try known prefixes (for better classification)
        known_prefix_match = re.match(r'^(PE|PFV|PEO|CTM|CTH|CTA|TER|U)\s+(.+)$', line)

        # Try PMGD pattern (Pequeños Medios de Generación Distribuida)
        pmgd_match = re.match(r'^(PMGD\s+[A-Z]+)\s+(.+)$', line, re.IGNORECASE)

        # Also try general plant name pattern (any capitalized name followed by data)
        general_plant_match = None
        if not known_prefix_match and not pmgd_match:
            # Look for potential plant names: starts with capital, not just a code, has substance
            if (re.match(r'^[A-Z]', line) and
                len(line) > 4 and
                not re.match(r'^[A-Z]{1,3}$', line) and  # Not estado codes like RO, GNP
                not line in ['Centrales', 'Prog.', 'Desv %', 'Estado', 'Real'] and  # Not headers
                not re.match(r'^\(\*\)', line) and  # Not markers
                not re.match(r'^[\+\-]?\d+\.?\d*\s*%?$', line)):  # Not percentages

                # Check if followed by numerical data (indicates it's a plant)
                if i + 1 < len(lines) and re.match(r'^\d+\.?\d*$', lines[i + 1]):
                    general_plant_match = re.match(r'^(.+)$', line)

        plant_match = known_prefix_match or pmgd_match or general_plant_match
        if plant_match:
            if known_prefix_match:
                # Extract type and name from known prefix pattern
                plant_type = known_prefix_match.group(1)
                plant_name = known_prefix_match.group(2).strip()
            elif pmgd_match:
                # Extract PMGD type and name
                pmgd_full_type = pmgd_match.group(1).upper()  # e.g., "PMGD PFV"
                plant_name = pmgd_match.group(2).strip()

                # Extract the actual plant type from PMGD designation
                if 'PFV' in pmgd_full_type:
                    plant_type = "PFV"  # Solar
                elif 'PE' in pmgd_full_type or 'PEO' in pmgd_full_type:
                    plant_type = "PEO"  # Wind
                elif 'HID' in pmgd_full_type:
                    plant_type = "HID"  # Hydro
                else:
                    plant_type = "PMGD"  # Generic PMGD

                # Add PMGD designation to name for clarity
                plant_name = f"PMGD {plant_name}"
            else:
                # General plant - try to extract type from name or use "UNKNOWN"
                full_name = general_plant_match.group(1).strip()
                # Try to infer type from name patterns
                if any(word in full_name.upper() for word in ['SOLAR', 'FOTOVOLTAICA', 'PV']):
                    plant_type = "PFV"
                    plant_name = full_name
                elif any(word in full_name.upper() for word in ['EOLICA', 'WIND', 'VIENTO']):
                    plant_type = "PEO"
                    plant_name = full_name
                elif any(word in full_name.upper() for word in ['TERMICA', 'THERMAL', 'GAS', 'DIESEL', 'CARBON']):
                    plant_type = "TER"
                    plant_name = full_name
                elif any(word in full_name.upper() for word in ['HIDRO', 'HYDRO']):
                    plant_type = "HID"
                    plant_name = full_name
                else:
                    plant_type = "UNKNOWN"
                    plant_name = full_name

            plant_count += 1

            # Detect table side based on plant type and position
            # TER plants typically appear in the right table
            # Also use plant count as heuristic (after ~25 plants, likely right table)
            if plant_type == "TER" or plant_count > 25:
                current_table_side = "right"

            # Initialize plant data
            plant_data = {
                "plant_type": plant_type,
                "plant_name": plant_name,
                "programmed_mwh": None,
                "real_mwh": None,
                "percentage_diff": None,
                "estado": None,
                "table_side": current_table_side,
                "special_markers": [],
                "comments": [],
                "raw_lines": [line]
            }

            # Look ahead for the data values (programmed, real, percentage, estado)
            j = i + 1
            values_found = []

            while j < len(lines) and j < i + 6:  # Look at next 5 lines max
                next_line = lines[j]

                # Check if this is another plant (stop processing current plant)
                if (re.match(r'^(PE|PFV|PEO|CTM|CTH|CTA|TER|U)\s+(.+)$', next_line) or
                    re.match(r'^(PMGD\s+[A-Z]+)\s+(.+)$', next_line, re.IGNORECASE)):
                    break

                # Check for programmed value (number with possible markers)
                number_with_marker = re.match(r'^(\d+\.?\d*)([*†‡§¶#@]+)?$', next_line)
                if number_with_marker:
                    value = float(number_with_marker.group(1))
                    marker = number_with_marker.group(2)
                    if marker:
                        plant_data["special_markers"].append({
                            "type": "programmed_value",
                            "marker": marker,
                            "position": "after_number"
                        })
                        plant_data["comments"].append(f"Programmed value has marker: {marker}")

                    values_found.append(('number', value, next_line))
                    plant_data["raw_lines"].append(next_line)

                # Check for percentage with possible markers - including (*) format
                elif re.match(r'^(\(\*\))?\s*([\+\-]?\d+\.?\d*)\s*%?([*†‡§¶#@]+)?$', next_line):
                    percentage_match = re.match(r'^(\(\*\))?\s*([\+\-]?\d+\.?\d*)\s*%?([*†‡§¶#@]+)?$', next_line)
                    prefix_marker = percentage_match.group(1)  # (*) at beginning
                    percentage = float(re.sub(r'[%\s*†‡§¶#@()]', '', percentage_match.group(2)))
                    suffix_marker = percentage_match.group(3)  # markers after percentage

                    if prefix_marker:
                        plant_data["special_markers"].append({
                            "type": "percentage",
                            "marker": prefix_marker,
                            "position": "before_percentage"
                        })
                        plant_data["comments"].append(f"Percentage has prefix marker: {prefix_marker}")

                    if suffix_marker:
                        plant_data["special_markers"].append({
                            "type": "percentage",
                            "marker": suffix_marker,
                            "position": "after_percentage"
                        })
                        plant_data["comments"].append(f"Percentage has suffix marker: {suffix_marker}")

                    values_found.append(('percentage', percentage, next_line))
                    plant_data["raw_lines"].append(next_line)

                # Check for standard percentage without special markers
                elif re.match(r'^([\+\-]?\d+\.?\d*)\s*%?$', next_line):
                    percentage = float(re.sub(r'[%\s]', '', next_line))
                    values_found.append(('percentage', percentage, next_line))
                    plant_data["raw_lines"].append(next_line)

                # Check for special marker lines (just symbols)
                elif re.match(r'^[*†‡§¶#@]+$', next_line):
                    plant_data["special_markers"].append({
                        "type": "standalone_marker",
                        "marker": next_line,
                        "position": "separate_line"
                    })
                    plant_data["comments"].append(f"Has special marker: {next_line}")
                    plant_data["raw_lines"].append(next_line)

                # Check for Estado (state codes like RO, FU, etc.)
                elif re.match(r'^[A-Z]{2,3}$', next_line) and len(next_line) <= 3:
                    plant_data["estado"] = next_line
                    plant_data["raw_lines"].append(next_line)

                # Check for blank/empty lines or dashes (missing data)
                elif next_line in ['-', '--', '', 'N/A', 'n/a', '*']:
                    if next_line == '*':
                        plant_data["special_markers"].append({
                            "type": "missing_data",
                            "marker": "*",
                            "position": "replacement"
                        })
                        plant_data["comments"].append("Data replaced with * (missing/unavailable)")
                    elif next_line == '-':
                        plant_data["comments"].append("Data marked as unavailable with -")

                    values_found.append(('blank', None, next_line))
                    plant_data["raw_lines"].append(next_line)

                j += 1

            # Process the found values
            numbers = [v for v in values_found if v[0] == 'number']
            percentages = [v for v in values_found if v[0] == 'percentage']
            blanks = [v for v in values_found if v[0] == 'blank']

            # Assign values based on what we found
            if len(numbers) >= 2:
                plant_data["programmed_mwh"] = numbers[0][1]
                plant_data["real_mwh"] = numbers[1][1]
            elif len(numbers) == 1:
                # Only one number found, could be programmed or real
                plant_data["programmed_mwh"] = numbers[0][1]
                # Check if there's a blank indicating missing real value
                if blanks:
                    plant_data["real_mwh"] = None

            if percentages:
                plant_data["percentage_diff"] = percentages[0][1]

            # Calculate efficiency ratio if we have both values
            if plant_data["programmed_mwh"] and plant_data["real_mwh"]:
                plant_data["efficiency_ratio"] = plant_data["real_mwh"] / plant_data["programmed_mwh"]
            else:
                plant_data["efficiency_ratio"] = None

            # Add source_type classification to plant_data
            plant_data["source_type"] = (
                "solar" if plant_type == "PFV" else
                "wind" if plant_type in ["PE", "PEO"] else
                "hydro" if plant_type == "HID" else
                "thermal" if plant_type in ["CTM", "CTH", "CTA", "TER"] else
                "distributed" if plant_type == "PMGD" else
                "unknown"
            )

            # Add to appropriate table
            tables["power_plants"].append(plant_data)
            if current_table_side == "left":
                tables["left_table"].append(plant_data)
            else:
                tables["right_table"].append(plant_data)

            # Skip the processed lines
            i = j
            continue

        # Check for table boundary indicators (might help detect left vs right)
        elif line in ['TABLA IZQUIERDA', 'TABLA DERECHA', '|', '||'] or len(line) > 50:
            current_table_side = "right" if "derecha" in line.lower() or current_table_side == "left" else "left"

        i += 1

    # Extract abbreviations information
    abbreviations_data = detect_abbreviations(raw_text)
    tables["abbreviations"] = abbreviations_data

    # Look for table headers and summary sections
    potential_headers = []
    for i, line in enumerate(lines):
        # Detect potential table headers
        if any(keyword in line.lower() for keyword in
               ['programado', 'real', 'diferencia', 'porcentaje', '%', 'mwh', 'mw', 'total', 'subtotal']):

            # Check if it's not just a percentage value
            if not re.match(r'^[\+\-]?\d+\.?\d*\s*%?$', line.strip()):
                potential_headers.append({
                    "line_number": i,
                    "header_text": line,
                    "columns": line.split()
                })

    tables["detected_headers"] = potential_headers

    # Calculate summary statistics
    if tables["power_plants"]:
        # Handle None values in calculations
        total_programmed = sum(p["programmed_mwh"] for p in tables["power_plants"] if p["programmed_mwh"] is not None)
        total_real = sum(p["real_mwh"] for p in tables["power_plants"] if p["real_mwh"] is not None)

        tables["generation_summary"] = {
            "total_plants": len(tables["power_plants"]),
            "plants_with_data": len([p for p in tables["power_plants"] if p["programmed_mwh"] is not None]),
            "total_programmed_mwh": round(total_programmed, 2),
            "total_real_mwh": round(total_real, 2),
            "overall_efficiency": round((total_real / total_programmed * 100) if total_programmed > 0 else 0, 2),
            "left_table_count": len(tables["left_table"]),
            "right_table_count": len(tables["right_table"]),
            "plants_by_type": {}
        }

        # Group by plant type
        for plant in tables["power_plants"]:
            plant_type = plant["plant_type"]
            if plant_type not in tables["generation_summary"]["plants_by_type"]:
                tables["generation_summary"]["plants_by_type"][plant_type] = {
                    "count": 0,
                    "total_programmed": 0,
                    "total_real": 0
                }

            tables["generation_summary"]["plants_by_type"][plant_type]["count"] += 1

            # Handle None values
            programmed = plant["programmed_mwh"] if plant["programmed_mwh"] is not None else 0
            real = plant["real_mwh"] if plant["real_mwh"] is not None else 0

            tables["generation_summary"]["plants_by_type"][plant_type]["total_programmed"] += programmed
            tables["generation_summary"]["plants_by_type"][plant_type]["total_real"] += real

    return tables

def extract_generation_data(raw_text: str) -> List[Dict]:
    """Extract generation data from different sources including tabular data"""
    generation_data = []

    # First try to extract structured table data
    table_data = detect_table_structure(raw_text)

    # Add power plant data from tables
    for plant in table_data["power_plants"]:
        # Prepare comments summary
        comments_summary = None
        if plant.get("comments"):
            comments_summary = "; ".join(plant["comments"])

        # Prepare special markers summary
        markers_summary = None
        if plant.get("special_markers"):
            markers = [f"{m['marker']} ({m['type']})" for m in plant["special_markers"]]
            markers_summary = "; ".join(markers)

        generation_data.append({
            "source_type": "solar" if plant["plant_type"] == "PFV" else
                          "wind" if plant["plant_type"] in ["PE", "PEO"] else
                          "hydro" if plant["plant_type"] == "HID" else
                          "thermal" if plant["plant_type"] in ["CTM", "CTH", "CTA", "TER"] else
                          "unknown",
            "plant_type_code": plant["plant_type"],
            "plant_name": plant["plant_name"],
            "programmed_mwh": plant["programmed_mwh"],
            "real_mwh": plant["real_mwh"],
            "deviation_percentage": plant["percentage_diff"],
            "efficiency_ratio": plant.get("efficiency_ratio"),
            "estado": plant.get("estado"),
            "table_side": plant.get("table_side"),
            "special_markers": plant.get("special_markers", []),
            "comments": comments_summary,
            "markers_summary": markers_summary,
            "data_source": "table_extraction"
        })

    # Fallback to pattern-based extraction if no table data found
    if not generation_data:
        sources = [
            "hidro", "hidroeléctrica", "térmica", "termoelectrica",
            "solar", "fotovoltaica", "eólica", "biomasa", "geotérmica"
        ]

        for source in sources:
            pattern = rf"{source}.*?(\d+(?:\.\d+)?)\s*mw"
            matches = re.finditer(pattern, raw_text.lower())

            for match in matches:
                generation_data.append({
                    "source_type": source,
                    "capacity_mw": float(match.group(1)),
                    "text_context": match.group(0),
                    "data_source": "pattern_extraction"
                })

    return generation_data

def extract_incidents_and_events(raw_text: str) -> List[Dict]:
    """Extract incidents, alerts, and significant events"""
    incidents = []

    # Check if this is an abbreviations page - don't extract incidents from these
    abbreviation_indicators = ['abreviaciones', 'significado', 'definiciones', 'nomenclatura']
    is_abbreviations_page = any(indicator in raw_text.lower() for indicator in abbreviation_indicators)

    if is_abbreviations_page:
        # Don't extract incidents from abbreviation pages
        return incidents

    # Incident keywords
    incident_keywords = [
        "falla", "incidente", "emergencia", "alerta", "desconexión",
        "reconexión", "mantenimiento", "indisponibilidad", "salida"
    ]

    lines = raw_text.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()

        # Skip lines that look like abbreviation definitions
        if re.match(r'^[A-Z]{2,}:?\s*[^:]+$', line.strip()):
            continue

        for keyword in incident_keywords:
            if keyword in line_lower and len(line.strip()) > 10:
                # Extract time if present
                time_match = re.search(r'(\d{1,2}):(\d{2})', line)
                time_str = f"{time_match.group(1)}:{time_match.group(2)}" if time_match else None

                incidents.append({
                    "type": keyword,
                    "description": line.strip(),
                    "time": time_str,
                    "line_number": i + 1
                })
                break

    return incidents

def extract_system_metrics(raw_text: str) -> Dict:
    """Extract system performance metrics"""
    metrics = {
        "frequency_hz": None,
        "voltage_levels": [],
        "reserve_margin_mw": None,
        "transmission_losses_percent": None,
        "interconnection_flows": []
    }

    # Extract frequency
    freq_patterns = [
        r"frecuencia.*?(\d+(?:\.\d+)?)\s*hz",
        r"(\d+(?:\.\d+)?)\s*hz"
    ]

    for pattern in freq_patterns:
        match = re.search(pattern, raw_text.lower())
        if match:
            freq = float(match.group(1))
            if 49.5 <= freq <= 50.5:  # Reasonable frequency range
                metrics["frequency_hz"] = freq
                break

    # Extract voltage levels
    voltage_patterns = [
        r"(\d+)\s*kv",
        r"tensión.*?(\d+)\s*kv"
    ]

    for pattern in voltage_patterns:
        matches = re.finditer(pattern, raw_text.lower())
        for match in matches:
            voltage = int(match.group(1))
            if voltage not in metrics["voltage_levels"] and voltage > 10:
                metrics["voltage_levels"].append(voltage)

    return metrics

def detect_section_info(raw_text: str, page_number: int) -> Dict:
    """Detect section titles and subsections from the text"""
    section_info = {
        "section_number": None,
        "section_title": None,
        "subsection_number": None,
        "subsection_title": None,
        "page_type": "content"
    }

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    for line in lines[:20]:  # Check first 20 lines for section headers
        # Main sections: "1TITLE", "2TITLE", etc. - allow uppercase letters and symbols
        main_section_match = re.match(r'^([0-9]+)([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\(\)\*]+)$', line)
        if main_section_match:
            section_info["section_number"] = main_section_match.group(1)
            section_info["section_title"] = main_section_match.group(2).strip()
            section_info["page_type"] = "section_start"
            break

        # Subsections: "1.1. Title", "3.2. Title", etc.
        sub_section_match = re.match(r'^([0-9]+\.[0-9]+\.)\s*([A-Za-záéíóúñ\s]+)$', line)
        if sub_section_match:
            section_info["subsection_number"] = sub_section_match.group(1)
            section_info["subsection_title"] = sub_section_match.group(2).strip()
            section_info["page_type"] = "subsection_start"
            # Extract main section number from subsection (e.g., "3" from "3.1.")
            main_section = section_info["subsection_number"].split('.')[0]
            section_info["section_number"] = main_section
            break

    # Special case for abbreviations
    if 'abreviatura' in raw_text.lower():
        section_info["subsection_title"] = "Abreviaturas"
        section_info["page_type"] = "abbreviations"
        section_info["section_number"] = "1"  # Part of section 1

    return section_info

def extract_section_1_tables(raw_text: str) -> Dict:
    """Extract Section 1: DESVIACIONES DE LA PROGRAMACION tables"""
    # Use the existing detect_table_structure function
    return detect_table_structure(raw_text)

def extract_section_2_justifications(raw_text: str) -> Dict:
    """Extract Section 2: JUSTIFICACIÓN DE PRINCIPALES DESVIACIONES"""
    justifications = {
        "justifications_found": [],
        "total_justifications": 0
    }

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for plant names (patterns like "HE Plant", "PE Plant", "PFV Plant", "TER Plant")
        plant_match = re.match(r'^(HE|HP|PE|PEO|PFV|TER|CTM|CTH|CTA)\s+(.+)$', line)
        if plant_match:
            plant_type = plant_match.group(1)
            plant_name = plant_match.group(2).strip()

            # Look for justification in next line
            if i + 1 < len(lines):
                justification = lines[i + 1].strip()

                justifications["justifications_found"].append({
                    "plant_type": plant_type,
                    "plant_name": plant_name,
                    "justification": justification,
                    "source_type": (
                        "hydro" if plant_type in ["HE", "HP"] else
                        "wind" if plant_type in ["PE", "PEO"] else
                        "solar" if plant_type == "PFV" else
                        "thermal" if plant_type in ["TER", "CTM", "CTH", "CTA"] else
                        "unknown"
                    )
                })
                i += 2  # Skip both plant name and justification lines
            else:
                i += 1
        else:
            i += 1

    justifications["total_justifications"] = len(justifications["justifications_found"])
    return justifications

def extract_section_3_status(raw_text: str) -> Dict:
    """Extract Section 3: ESTADO DE LAS CENTRALES"""
    status_data = {
        "plant_status_found": [],
        "subsection": None,
        "total_plants": 0
    }

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    # Detect subsection
    for line in lines[:10]:
        if re.match(r'^3\.[0-9]+\.', line):
            status_data["subsection"] = line
            break

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for plant names
        plant_match = re.match(r'^(HE|HP|PE|PEO|PFV|TER|CTM|CTH|CTA|PMGD)\s+(.+)$', line)
        if plant_match:
            plant_type = plant_match.group(1)
            plant_name = plant_match.group(2).strip()

            # Look for availability percentage and observations in next lines
            availability = None
            observations = []

            j = i + 1
            while j < len(lines) and j < i + 10:  # Look ahead max 10 lines
                next_line = lines[j]

                # Stop if we hit another plant
                if re.match(r'^(HE|HP|PE|PEO|PFV|TER|CTM|CTH|CTA|PMGD)\s+', next_line):
                    break

                # Look for availability percentage (e.g., "100.0", "85.0")
                if re.match(r'^[0-9]+\.[0-9]+$', next_line) and availability is None:
                    availability = float(next_line)

                # Collect observation text (longer descriptive lines)
                elif len(next_line) > 20:  # Observations are typically longer
                    observations.append(next_line)

                j += 1

            status_data["plant_status_found"].append({
                "plant_type": plant_type,
                "plant_name": plant_name,
                "availability_percent": availability,
                "observations": " ".join(observations) if observations else None,
                "source_type": (
                    "hydro" if plant_type in ["HE", "HP"] else
                    "wind" if plant_type in ["PE", "PEO"] else
                    "solar" if plant_type == "PFV" else
                    "thermal" if plant_type in ["TER", "CTM", "CTH", "CTA"] else
                    "distributed" if plant_type == "PMGD" else
                    "unknown"
                )
            })
            i = j
        else:
            i += 1

    status_data["total_plants"] = len(status_data["plant_status_found"])
    return status_data

def extract_section_4_operations(raw_text: str) -> Dict:
    """Extract Section 4: ANTECEDENTES DE LA OPERACIÓN DIARIA SEN"""
    operations_data = {
        "observations_found": [],
        "subsection": None,
        "total_observations": 0
    }

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    # Detect subsection
    for line in lines[:10]:
        if re.match(r'^4\.[0-9]+\.', line):
            operations_data["subsection"] = line
            break

    i = 0
    current_time = None
    current_control_center = None

    while i < len(lines):
        line = lines[i]

        # Look for time patterns (HH:MM)
        time_match = re.match(r'^([0-9]{1,2}:[0-9]{2})$', line)
        if time_match:
            current_time = time_match.group(1)
            i += 1
            continue

        # Look for control center names (short lines that could be centers)
        if len(line) <= 30 and not re.match(r'^[0-9]', line) and current_time:
            current_control_center = line
            i += 1
            continue

        # Look for observation text (longer descriptive lines)
        if len(line) > 30 and current_time and current_control_center:
            operations_data["observations_found"].append({
                "time": current_time,
                "control_center": current_control_center,
                "observation": line
            })
            # Reset for next observation
            current_time = None
            current_control_center = None

        i += 1

    operations_data["total_observations"] = len(operations_data["observations_found"])
    return operations_data

def extract_section_5_8_system_tables(raw_text: str, section_number: str) -> Dict:
    """Extract Sections 5-8: System status tables (SCADA, Communications, etc.)"""
    system_data = {
        "system_entries_found": [],
        "section_number": section_number,
        "total_entries": 0
    }

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for control center names (typically company names)
        if (len(line) > 5 and len(line) < 50 and
            not re.match(r'^[0-9]', line) and
            not line in ['Centro de Control', 'Instalación', 'Fecha F/S', 'Hora F/S', 'Fecha E/S', 'Hora E/S']):

            control_center = line
            installation = None
            fecha_fs = None
            hora_fs = None
            fecha_es = None
            hora_es = None
            description = None

            # Look ahead for associated data
            j = i + 1
            while j < len(lines) and j < i + 10:
                next_line = lines[j]

                # Stop if we hit another control center
                if (len(next_line) > 5 and len(next_line) < 50 and
                    not re.match(r'^[0-9]', next_line) and j > i + 3):
                    break

                # Look for installation description (longer text)
                if len(next_line) > 20 and installation is None:
                    installation = next_line

                # Look for dates (DD/MM/YYYY format)
                elif re.match(r'^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$', next_line):
                    if fecha_fs is None:
                        fecha_fs = next_line
                    elif fecha_es is None:
                        fecha_es = next_line

                # Look for times (HH:MM format)
                elif re.match(r'^[0-9]{1,2}:[0-9]{2}$', next_line):
                    if hora_fs is None:
                        hora_fs = next_line
                    elif hora_es is None:
                        hora_es = next_line

                j += 1

            if installation:  # Only add if we found meaningful data
                system_data["system_entries_found"].append({
                    "control_center": control_center,
                    "installation": installation,
                    "fecha_fs": fecha_fs,
                    "hora_fs": hora_fs,
                    "fecha_es": fecha_es,
                    "hora_es": hora_es
                })

            i = j
        else:
            i += 1

    system_data["total_entries"] = len(system_data["system_entries_found"])
    return system_data

def process_pdf_page(pdf_path: str, page_number: int) -> Dict:
    """Process a single page from the PDF and extract daily report information"""

    try:
        # Open PDF with PyMuPDF for better text extraction
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number - 1)  # 0-indexed

        # Extract text
        raw_text = page.get_text()

        # Extract images for OCR if text is insufficient
        image_list = page.get_images()

        if len(raw_text.strip()) < 100 and image_list:
            # Use OCR for image-heavy pages
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)

            # Preprocess image for better OCR
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Apply threshold to get better contrast
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Use pytesseract for OCR
            raw_text = pytesseract.image_to_string(thresh, lang='spa')

        doc.close()

        if len(raw_text.strip()) < 50:
            return {
                "page": page_number,
                "chapter": "INFORME_DIARIO_DAY1",
                "extraction_timestamp": datetime.now().isoformat(),
                "error": "Insufficient text extracted",
                "raw_text_length": len(raw_text)
            }

        # Detect section information
        section_info = detect_section_info(raw_text, page_number)

        # Extract basic information
        date_info = extract_date_info(raw_text)
        incidents = extract_incidents_and_events(raw_text)

        # Initialize result structure
        result = {
            "page": page_number,
            "chapter": "INFORME_DIARIO_DAY1",
            "extraction_timestamp": datetime.now().isoformat(),
            "date_info": date_info,
            "section_info": section_info,
            "sections": {},
            "incidents_and_events": incidents,
            "raw_text_sample": raw_text[:500],
            "text_length": len(raw_text),
            "status": "extracted"
        }

        # Extract section-specific data based on detected section
        section_number = section_info.get("section_number")

        if section_number == "1":
            # Section 1: DESVIACIONES DE LA PROGRAMACION
            section_1_data = extract_section_1_tables(raw_text)
            result["sections"]["section_1"] = {
                "title": "DESVIACIONES DE LA PROGRAMACION",
                "subsections": {},
                "data": section_1_data
            }

            # Check for specific subsections
            if section_info.get("subsection_title") == "Abreviaturas":
                result["sections"]["section_1"]["subsections"]["abreviaturas"] = {
                    "title": "Abreviaturas",
                    "data": section_1_data.get("abbreviations", {})
                }
            elif "1.1" in raw_text or "Centrales" in raw_text:
                result["sections"]["section_1"]["subsections"]["1_1_centrales"] = {
                    "title": "1.1. Centrales",
                    "data": {
                        "power_plants": section_1_data.get("power_plants", []),
                        "generation_summary": section_1_data.get("generation_summary", {})
                    }
                }
            elif "1.2" in raw_text or "PMGD" in raw_text:
                result["sections"]["section_1"]["subsections"]["1_2_pmgd"] = {
                    "title": "1.2. PMGD",
                    "data": {
                        "pmgd_plants": section_1_data.get("pmgd_plants", []),
                        "abbreviations": section_1_data.get("abbreviations", {})
                    }
                }

        elif section_number == "2":
            # Section 2: JUSTIFICACIÓN DE PRINCIPALES DESVIACIONES
            section_2_data = extract_section_2_justifications(raw_text)
            result["sections"]["section_2"] = {
                "title": "JUSTIFICACIÓN DE PRINCIPALES DESVIACIONES (*)",
                "data": section_2_data
            }

        elif section_number == "3":
            # Section 3: ESTADO DE LAS CENTRALES
            section_3_data = extract_section_3_status(raw_text)
            result["sections"]["section_3"] = {
                "title": "ESTADO DE LAS CENTRALES",
                "subsection": section_3_data.get("subsection"),
                "data": section_3_data
            }

        elif section_number == "4":
            # Section 4: ANTECEDENTES DE LA OPERACIÓN DIARIA SEN
            section_4_data = extract_section_4_operations(raw_text)
            result["sections"]["section_4"] = {
                "title": "ANTECEDENTES DE LA OPERACIÓN DIARIA SEN",
                "subsection": section_4_data.get("subsection"),
                "data": section_4_data
            }

        elif section_number in ["5", "6", "7", "8"]:
            # Sections 5-8: System tables
            section_titles = {
                "5": "INDISPONIBILIDAD SCADA SEN",
                "6": "COMUNICACIONES SEN",
                "7": "CAMBIOS TOPOLÓGICOS RELEVANTES SEN",
                "8": "REGULACIÓN DE TENSIÓN SEN"
            }

            section_data = extract_section_5_8_system_tables(raw_text, section_number)
            result["sections"][f"section_{section_number}"] = {
                "title": section_titles[section_number],
                "data": section_data
            }

        else:
            # Fallback: use legacy extraction for unknown sections
            operational_summary = extract_operational_summary(raw_text)
            generation_data = extract_generation_data(raw_text)
            system_metrics = extract_system_metrics(raw_text)
            table_structure = detect_table_structure(raw_text)

            result["fallback_data"] = {
                "operational_summary": operational_summary,
                "generation_data": generation_data,
                "system_metrics": system_metrics,
                "table_structure": table_structure
            }

        return result

    except Exception as e:
        return {
            "page": page_number,
            "chapter": "INFORME_DIARIO_DAY1",
            "extraction_timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "failed"
        }

def save_extraction_result(result: Dict, output_dir: Path):
    """Save extraction result to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"informe_diario_day1_page_{result['page']}_{timestamp}.json"

    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {output_path}")
    return output_path

def main():
    """Main execution function"""
    # Setup paths
    project_root = Path(__file__).parent.parent.parent.parent.parent
    pdf_path = project_root / "data" / "documents" / "anexos_EAF" / "raw" / "Anexos-EAF-089-2025.pdf"
    output_dir = project_root / "extractions" / "informe_diario_day1"

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        # Try alternative path
        pdf_path = project_root / "data" / "documents" / "power_system_reports" / "anexos_EAF" / "Anexos-EAF-089-2025.pdf"
        if not pdf_path.exists():
            print(f"❌ PDF file not found in alternative path: {pdf_path}")
            return

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            # Process all pages 101-134
            pages_to_process = list(range(101, 135))
        else:
            try:
                page_num = int(sys.argv[1])
                if 101 <= page_num <= 134:
                    pages_to_process = [page_num]
                else:
                    print(f"❌ Page number must be between 101 and 134. Got: {page_num}")
                    return
            except ValueError:
                print(f"❌ Invalid page number: {sys.argv[1]}")
                return
    else:
        # Default: process page 101 (first page of daily report)
        pages_to_process = [101]

    print(f"🚀 Starting INFORME DIARIO Day 1 extraction")
    print(f"📄 PDF: {pdf_path}")
    print(f"📊 Pages to process: {pages_to_process}")
    print(f"💾 Output directory: {output_dir}")
    print("-" * 60)

    successful_extractions = 0
    failed_extractions = 0

    for page_num in pages_to_process:
        print(f"\n📖 Processing page {page_num}...")

        result = process_pdf_page(str(pdf_path), page_num)

        if result.get("status") == "extracted":
            save_extraction_result(result, output_dir)
            successful_extractions += 1

            # Print summary of what was extracted
            summary = result.get("operational_summary", {})
            incidents = result.get("incidents_and_events", [])
            generation = result.get("generation_data", [])

            print(f"   📈 Peak demand: {summary.get('peak_demand_mw', 'N/A')} MW")
            print(f"   🔄 Generation sources found: {len(generation)}")
            print(f"   ⚠️  Incidents/events: {len(incidents)}")

        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            failed_extractions += 1

    print("-" * 60)
    print(f"✅ Successful extractions: {successful_extractions}")
    print(f"❌ Failed extractions: {failed_extractions}")
    print(f"📁 Output saved to: {output_dir}")

if __name__ == "__main__":
    main()