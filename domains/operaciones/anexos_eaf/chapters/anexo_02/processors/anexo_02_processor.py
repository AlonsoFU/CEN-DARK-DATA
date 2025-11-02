#!/usr/bin/env python3
"""
ANEXO 2 Real Generation Data Extractor
======================================

Extracts real generation data from ANEXO 2 (Pages 63-95)
Focus: Actual power generation values, real-time operational data

This script extracts:
- Real generation values by power plant
- Actual vs programmed generation comparison
- Operational performance metrics
- Time-series generation data

Usage:
    python extract_anexo2_real_generation.py [page_number]
    python extract_anexo2_real_generation.py --all  # Process all pages 63-95
"""

import sys
import re
import json
import io
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add project root to path (go up 6 levels from scripts/eaf_workflows/eaf_processing/chapters/anexo_02_real_generation/content_extraction/)
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
    """Extract comprehensive metadata from the document header"""
    # Look for date patterns like "25-02-2025" or "RESUMEN DIARIO DE OPERACION DEL SEN"
    date_patterns = [
        r'(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})',  # "25-02-2025 25-02-2025"
        r'(\d{2}-\d{2}-\d{4})',  # Single date
        r'RESUMEN DIARIO DE OPERACION DEL SEN\s*(\d{2}-\d{2}-\d{4})'  # With header
    ]

    metadata = {
        "document_tags": {
            "anexo_title": "ANEXO 2 - GENERACION REAL",
            "anexo_description": "Real Generation Data - Actual vs Programmed Generation Comparison",
            "data_source": "EAF-089-2025 Power System Report"
        },
        "plant_color_scheme": {
            "SOLAR_PV": "#FFD700",              # Gold - Large Scale Solar PV
            "DISTRIBUTED_SOLAR_PV": "#FFA500",  # Orange - Distributed Solar PV
            "DISTRIBUTED_THERMAL": "#FF6347",   # Tomato Red - Distributed Thermal
            "DISTRIBUTED_DIESEL": "#8B4513",    # Saddle Brown - Distributed Diesel
            "DISTRIBUTED_GENERATION": "#32CD32", # Lime Green - Other Distributed
            "HYDROELECTRIC": "#1E90FF",         # Dodger Blue - Hydroelectric
            "WIND": "#87CEEB",                  # Sky Blue - Wind Power
            "COAL": "#2F4F4F",                  # Dark Slate Gray - Coal
            "NATURAL_GAS": "#4169E1",           # Royal Blue - Natural Gas
            "NUCLEAR": "#FF1493",               # Deep Pink - Nuclear
            "UNKNOWN": "#808080"                # Gray - Unknown/Unclassified
        },
        "color_scheme_notes": "Colors assigned based on plant type and energy source for visual differentiation in charts and dashboards"
    }

    # Extract date information
    for pattern in date_patterns:
        match = re.search(pattern, raw_text[:200])  # Check first 200 chars
        if match:
            if len(match.groups()) == 2:  # Two dates
                metadata.update({
                    "operation_date": match.group(1),
                    "report_date": match.group(2),
                    "date_format": "DD-MM-YYYY",
                    "source": "extracted_from_header"
                })
            else:  # Single date
                metadata.update({
                    "operation_date": match.group(1),
                    "date_format": "DD-MM-YYYY",
                    "source": "extracted_from_header"
                })
            break

    # Check for document type header
    if "RESUMEN DIARIO DE OPERACION DEL SEN" in raw_text[:300]:
        metadata["document_type"] = "RESUMEN DIARIO DE OPERACION DEL SEN"
        metadata["document_type_english"] = "Daily Operation Summary of the National Electric System"
        metadata["system_operator"] = "Coordinador Eléctrico Nacional (CEN)"
    else:
        metadata["document_type"] = "daily_operation_summary"

    # Check for specific ANEXO 2 indicators
    anexo2_indicators = [
        "GENERACION REAL",
        "Real Generation",
        "Actual Generation",
        "MWh/h"  # Common unit in generation tables
    ]

    found_indicators = []
    for indicator in anexo2_indicators:
        if indicator in raw_text[:500]:  # Check first 500 chars
            found_indicators.append(indicator)

    if found_indicators:
        metadata["content_indicators"] = found_indicators
        metadata["verified_anexo"] = "ANEXO_2_REAL_GENERATION"

    return metadata

def find_pdf_file():
    """Find the EAF PDF file in the project"""
    possible_paths = [
        project_root / "data" / "documents" / "anexos_EAF" / "source_documents" / "Anexos-EAF-089-2025.pdf",
        project_root / "data" / "documents" / "anexos_EAF" / "samples_and_tests" / "Anexos-EAF-089-2025.pdf",
        project_root / "data" / "documents" / "power_system_reports" / "anexos_EAF" / "Anexos-EAF-089-2025.pdf",
        project_root / "data_real" / "Anexos-EAF-089-2025.pdf",
        project_root / "Anexos-EAF-089-2025.pdf"
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    return None

def extract_page_text(document_path: str, page_num: int) -> str:
    """Extract text from single page using PyPDF2"""
    try:
        reader = PdfReader(document_path)
        if 1 <= page_num <= len(reader.pages):
            page = reader.pages[page_num - 1]
            return page.extract_text().strip()
        return ""
    except Exception as e:
        print(f"Error extracting page {page_num}: {e}")
        return ""

def is_system_summary_page(raw_text: str) -> bool:
    """Detect if page contains actual system-wide summary data (not just header)"""
    # Key indicators that distinguish true system summary pages from regular plant pages
    # These are specific data patterns that only appear on system summary pages
    specific_system_patterns = [
        "TOTAL HORA.",  # Must have the actual TOTAL HORA data line
        "TOTAL SEN",    # Must have TOTAL SEN data
        "FLUJO CHANGOS->CUMBRES",  # Power flow data - unique to system summary
        "PERDIDAS APROX.",  # System losses data
        "DEMANDA APROX.",   # System demand data
        "DMAX"  # Daily maximum indicator at the end
    ]

    # Check if multiple specific system data patterns are present
    # (not just the common header that appears on every page)
    pattern_count = sum(1 for pattern in specific_system_patterns if pattern in raw_text)

    # Also check for the characteristic data structure pattern of system summary pages
    # Look for lines with multiple numerical values (system data rows)
    system_data_lines = 0
    lines = raw_text.split('\n')
    for line in lines:
        # Look for lines that start with system categories and have multiple numbers
        if any(pattern in line for pattern in ["TOTAL HORA.", "TOTAL SEN", "CONS. PROPIOS", "PERDIDAS APROX.", "DEMANDA APROX."]):
            # Check if line has multiple numerical values (indicating hourly data)
            numbers = len([x for x in line.split() if x.replace(',', '').replace('.', '').replace('-', '').isdigit()])
            if numbers >= 10:  # System summary lines have ~24 hourly values
                system_data_lines += 1

    # Require both: multiple system patterns AND actual system data lines
    return pattern_count >= 4 and system_data_lines >= 3

def extract_system_summary_data(raw_text: str) -> Dict:
    """Extract system-wide summary data (integrated from page 79 extractor)"""
    system_data = {}

    # System summary patterns
    patterns = {
        'total_hora': r'TOTAL HORA\.\s+([\d,\s.-]+?)\s+\d{3}\.?\d*',
        'total_hora_sing': r'TOTAL HORA\.\s+SING\s+([\d,\s.-]+?)(?:\s+TOTAL|\s+\d{2}\.?\d*\s*$)',
        'total_sen': r'TOTAL SEN\s+([\d,\s.-]+?)(?:\s+CONS\.|\s+\d{3}\.?\d*\s*$)',
        'cons_propios': r'CONS\.\s+PROPIOS\s+([\d,\s.-]+?)(?:\s+CONS\.|\s+\d\.?\d*\s*$)',
        'cons_propios_sing': r'CONS\.\s+PROPIOS\s+SING\s+([\d,\s.-]+?)(?:\s+FLUJO|\s+\d{3}\s*$)',
        'flujo_changos_cumbres': r'FLUJO\s+CHANGOS->CUMBRES\s+([\d,\s.-]+?)(?:\s+PERDIDAS|\s+-?\d\.?\d*\s*$)',
        'perdidas_aprox': r'PERDIDAS\s+APROX\.\s+([\d,\s.-]+?)(?:\s+PERDIDAS|\s+\d\.?\d*\s*$)',
        'perdidas_aprox_sing': r'PERDIDAS\s+APROX\.\s+SING\s+([\d,\s.-]+?)(?:\s+DEMANDA|\s+\d{3}\s*$)',
        'demanda_aprox': r'DEMANDA\s+APROX\.\s+([\d,\s.-]+?)(?:\s+DEMANDA|\s+\d{6}\.?\d*\s*$)',
        'demanda_aprox_sing': r'DEMANDA\s+APROX\.\s+SING\s+([\d,\s.-]+?)(?:\s+HORA|\s+\d{5}\.?\d*\s*$)',
        'dmax_total': r'DMAX\s*:\s*([\d,]+)\s+(\d+)',
        'dmed_total': r'DMAX\s*:\s*[\d,]+\s+(\d+)'
    }

    for system_type, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            values_text = match.group(1).strip()

            # Handle DMAX and DMED specially (single values)
            if system_type == 'dmax_total':
                try:
                    # Extract both DMAX and DMED from the match
                    dmax_value = float(match.group(1).replace(',', '.'))
                    dmed_value = float(match.group(2))

                    system_data[system_type] = {
                        "value": dmax_value,
                        "system_category": "Daily Maximum Total",
                        "source": "system_summary_extraction",
                        "data_type": "single_value"
                    }

                    # Also add DMED as a separate entry
                    system_data['dmed_total'] = {
                        "value": dmed_value,
                        "system_category": "Daily Average Total",
                        "source": "system_summary_extraction",
                        "data_type": "single_value"
                    }
                except ValueError:
                    continue
            elif system_type == 'dmed_total':
                # Skip DMED processing since it's handled with DMAX
                continue
            else:
                # Parse hourly values
                hourly_values = []
                value_parts = re.findall(r'-?\d+(?:,\d+)?', values_text)
                for part in value_parts[:24]:  # Only take first 24 hours
                    try:
                        clean_value = part.replace(',', '.')
                        value = float(clean_value)
                        hourly_values.append(value)
                    except ValueError:
                        continue

                if hourly_values:
                    # Build hourly data with hour numbers
                    hourly_data = []
                    for i, value in enumerate(hourly_values, 1):
                        hourly_data.append({
                            "hour": i,
                            "value": value
                        })

                    # Calculate metrics
                    daily_total = sum(hourly_values)
                    daily_max = max(hourly_values) if hourly_values else 0.0
                    daily_min = min(hourly_values) if hourly_values else 0.0
                    daily_avg = daily_total / len(hourly_values) if hourly_values else 0.0

                    system_data[system_type] = {
                        "hourly_data": hourly_data,
                        "daily_total": daily_total,
                        "daily_max": daily_max,
                        "daily_min": daily_min,
                        "daily_avg": daily_avg,
                        "operational_hours": len([v for v in hourly_values if v > 0]),
                        "system_category": system_type.replace('_', ' ').title(),
                        "data_points": len(hourly_values),
                        "source": "system_summary_extraction",
                        "data_type": "hourly_series"
                    }

    return system_data if system_data else None

def calculate_summary_metrics(generation_records: List[Dict]) -> Dict:
    """Calculate summary metrics for plant generation data"""
    if not generation_records:
        return {}

    # Calculate totals
    total_daily_mwh = sum(
        record['data'].get('daily_total_mwh', 0)
        for record in generation_records
        if isinstance(record['data'].get('daily_total_mwh'), (int, float))
    )
    max_capacity_mw = sum(
        record['data'].get('daily_max_mw', 0)
        for record in generation_records
        if isinstance(record['data'].get('daily_max_mw'), (int, float))
    )
    total_operational_hours = sum(
        record['data'].get('operational_hours', 0)
        for record in generation_records
        if isinstance(record['data'].get('operational_hours'), (int, float))
    )

    # Count by plant types
    plant_types = {}
    for record in generation_records:
        plant_type = record['data'].get('plant_type', 'UNKNOWN')
        plant_types[plant_type] = plant_types.get(plant_type, 0) + 1

    return {
        'total_plants': len(generation_records),
        'solar_pv_plants': plant_types.get('SOLAR_PV', 0),
        'distributed_solar_plants': plant_types.get('DISTRIBUTED_SOLAR_PV', 0) + plant_types.get('DISTRIBUTED_GENERATION', 0),
        'total_daily_generation_mwh': total_daily_mwh,
        'total_max_capacity_mw': max_capacity_mw,
        'avg_operational_hours': total_operational_hours / len(generation_records) if generation_records else 0,
        'system_type': 'RENEWABLE_SOLAR_FOCUSED'
    }

def extract_colors_via_text_analysis(text: str) -> Dict:
    """Extract color information from text using pattern recognition"""
    color_mapping = {}

    # Common color keywords in Spanish and English
    color_patterns = {
        'rojo|red': '#FF0000',
        'azul|blue': '#0000FF',
        'verde|green': '#00FF00',
        'amarillo|yellow': '#FFFF00',
        'naranja|orange': '#FFA500',
        'morado|purple|violeta': '#800080',
        'rosa|pink': '#FFC0CB',
        'marrón|brown|café': '#8B4513',
        'gris|gray|grey': '#808080',
        'negro|black': '#000000',
        'blanco|white': '#FFFFFF',
        'celeste|light blue|cyan': '#00FFFF',
        'dorado|gold': '#FFD700',
        'plata|silver': '#C0C0C0'
    }

    # Look for patterns like "Plant Name - Color" or "Color: Plant Name"
    lines = text.split('\n')

    for line in lines:
        line_lower = line.lower()

        # Pattern 1: "PLANT-NAME (color)" or "PLANT-NAME - color"
        for color_keyword, hex_color in color_patterns.items():
            if any(keyword in line_lower for keyword in color_keyword.split('|')):
                # Try to find plant names in the same line
                plant_patterns = [
                    r'([A-Z][A-Z\-_0-9]*[A-Z0-9])',  # Plant name pattern
                    r'(PFV-[A-ZÁÉÍÓÚÑ\-_0-9]+)',     # Solar plants
                    r'(PMGD-[A-ZÁÉÍÓÚÑ\-_0-9]+)',    # Distributed generation
                ]

                for pattern in plant_patterns:
                    matches = re.findall(pattern, line)
                    for plant_name in matches:
                        if len(plant_name) > 3:  # Avoid false matches
                            color_mapping[plant_name] = {
                                'color': hex_color,
                                'color_name': color_keyword.split('|')[0],
                                'source_line': line.strip(),
                                'detection_method': 'text_analysis'
                            }

    # Look for legend patterns like "Red = Solar Plants"
    legend_patterns = [
        r'(rojo|red|azul|blue|verde|green|amarillo|yellow|naranja|orange)\s*[=:]\s*([^,\n]+)',
        r'([^,\n]+)\s*[=:]\s*(rojo|red|azul|blue|verde|green|amarillo|yellow|naranja|orange)'
    ]

    for line in lines:
        line_lower = line.lower()
        for pattern in legend_patterns:
            matches = re.findall(pattern, line_lower)
            for match in matches:
                color_term = match[0] if match[0] in color_patterns else match[1]
                description = match[1] if match[0] in color_patterns else match[0]

                if color_term in color_patterns:
                    color_mapping[f"LEGEND_{description.upper()}"] = {
                        'color': color_patterns[color_term],
                        'color_name': color_term,
                        'description': description,
                        'source_line': line.strip(),
                        'detection_method': 'legend_analysis'
                    }

    return {
        'color_mapping': color_mapping,
        'detection_method': 'text_analysis',
        'total_colors_found': len(color_mapping)
    }

def extract_actual_pdf_colors(document_path: str, page_num: int) -> Dict:
    """Extract actual colors from PDF graphics and charts for each plant"""
    try:
        doc = fitz.open(document_path)
        if 0 <= page_num - 1 < len(doc):
            page = doc[page_num - 1]

            # Get all drawing commands and colors
            plant_colors = {}

            # Method 1: Extract from page graphics
            drawings = page.get_drawings()
            print(f"   🔍 Found {len(drawings)} drawing objects on page")

            for i, drawing in enumerate(drawings):
                if 'fill' in drawing and drawing['fill']:
                    color_info = drawing['fill']
                    if isinstance(color_info, tuple) and len(color_info) >= 3:
                        r, g, b = int(color_info[0] * 255), int(color_info[1] * 255), int(color_info[2] * 255)
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        print(f"   🎨 Drawing {i}: Color {hex_color}")

                        # Store color with drawing info
                        bbox = drawing.get('rect', None)
                        bbox_data = None
                        if bbox:
                            # Convert Rect to serializable format
                            bbox_data = [bbox.x0, bbox.y0, bbox.x1, bbox.y1]

                        plant_colors[f"drawing_{i}"] = {
                            'color': hex_color,
                            'source': 'pdf_graphics',
                            'drawing_type': drawing.get('type', 'unknown'),
                            'bbox': bbox_data
                        }

            # Method 2: Look at text formatting colors
            blocks = page.get_text("dict")
            text_colors = {}

            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            color = span.get("color", None)
                            text = span.get("text", "").strip()

                            if color and text and color != 0:  # 0 is black text
                                # Convert color integer to hex
                                hex_color = f"#{color:06x}"

                                # Check if this text might be a plant name
                                plant_patterns = [
                                    r'([A-Z][A-Z\-_0-9]*[A-Z0-9])',
                                    r'(PFV-[A-ZÁÉÍÓÚÑ\-_0-9]+)',
                                    r'(PMGD-[A-ZÁÉÍÓÚÑ\-_0-9]+)',
                                ]

                                for pattern in plant_patterns:
                                    if re.match(pattern, text):
                                        print(f"   🎨 Found colored text: '{text}' = {hex_color}")
                                        text_colors[text] = {
                                            'color': hex_color,
                                            'source': 'pdf_text_color',
                                            'font': span.get('font', ''),
                                            'size': span.get('size', 0)
                                        }

            doc.close()
            return {
                'graphic_colors': plant_colors,
                'text_colors': text_colors,
                'extraction_method': 'pdf_native_colors',
                'total_colors_found': len(plant_colors) + len(text_colors)
            }

        doc.close()
        return {}
    except Exception as e:
        print(f"⚠️  PDF color extraction failed: {e}")
        return {}

def extract_colors_from_page(document_path: str, page_num: int) -> Dict:
    """Extract dominant colors from the PDF page to identify plant color coding"""
    try:
        doc = fitz.open(document_path)
        if 0 <= page_num - 1 < len(doc):
            page = doc[page_num - 1]

            # High resolution for color detection
            mat = fitz.Matrix(3, 3)  # 216 DPI
            pix = page.get_pixmap(matrix=mat)

            # Convert to numpy array for color analysis
            # Handle both RGB and RGBA formats
            if pix.n == 4:  # RGBA
                img_data = np.frombuffer(pix.tobytes(), dtype=np.uint8).reshape(pix.height, pix.width, 4)
                # Convert RGBA to RGB by dropping alpha channel
                img_data = img_data[:, :, :3]
            elif pix.n == 3:  # RGB
                img_data = np.frombuffer(pix.tobytes(), dtype=np.uint8).reshape(pix.height, pix.width, 3)
            else:
                print(f"⚠️  Unsupported color format: {pix.n} channels")
                return {}

            # Find dominant colors (excluding white/near-white background)
            unique_colors = {}
            h, w, _ = img_data.shape

            # Sample colors from the image, focusing on non-white areas
            for y in range(0, h, 20):  # Sample every 20 pixels
                for x in range(0, w, 20):
                    r, g, b = img_data[y, x]

                    # Skip near-white colors (likely background)
                    if r > 240 and g > 240 and b > 240:
                        continue

                    # Skip near-black colors (likely text)
                    if r < 20 and g < 20 and b < 20:
                        continue

                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                    unique_colors[color_hex] = unique_colors.get(color_hex, 0) + 1

            # Get the most common non-text colors
            sorted_colors = sorted(unique_colors.items(), key=lambda x: x[1], reverse=True)
            dominant_colors = [color for color, count in sorted_colors[:10] if count > 50]

            doc.close()
            return {
                "page_colors": dominant_colors,
                "color_analysis": "extracted_from_pdf_visuals",
                "total_unique_colors": len(unique_colors)
            }

        doc.close()
        return {}
    except Exception as e:
        print(f"⚠️  Color extraction failed: {e}")
        return {}

def extract_ocr_text(document_path: str, page_num: int) -> str:
    """Extract text using OCR on rendered PDF page"""
    try:
        doc = fitz.open(document_path)
        if 0 <= page_num - 1 < len(doc):
            page = doc[page_num - 1]
            
            # High DPI for better OCR accuracy
            mat = fitz.Matrix(2, 2)  # 144 DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # OCR with Spanish + English
            ocr_text = pytesseract.image_to_string(
                pil_image,
                lang='spa+eng',
                config='--psm 6'
            )
            
            doc.close()
            return ocr_text.strip()
        
        doc.close()
        return ""
    except Exception as e:
        print(f"⚠️  OCR extraction failed: {e}")
        return ""

def extract_real_generation_data(page_text: str, ocr_text: str, page_num: int, document_path: str = None) -> Dict:
    """Extract real generation data from page text - handles both plant data and system summary"""

    # Check if this page has system summary data
    has_system_summary = is_system_summary_page(page_text)

    # Initialize extraction data structure
    extracted_data = {
        'page': page_num,
        'chapter': 'ANEXO_02_REAL_GENERATION',
        'extraction_timestamp': datetime.now().isoformat(),
        'real_generation_records': [],
        'summary_metrics': {},
        'extraction_quality': {
            'raw_text_length': len(page_text),
            'ocr_text_length': len(ocr_text),
            'has_system_data': has_system_summary,
            'patterns_found': 0
        }
    }

    # Extract system summary data if present
    if has_system_summary:
        print(f"   🔍 Detected system summary data on page {page_num}")
        system_summary = extract_system_summary_data(page_text)

        if system_summary:
            extracted_data['system_summary_data'] = system_summary
            summary_count = len([k for k, v in system_summary.items() if v.get('data_type') == 'hourly_series'])
            dmax_count = len([k for k, v in system_summary.items() if v.get('data_type') == 'single_value'])
            print(f"   ✅ Found {summary_count} system categories + {dmax_count} summary values")
            print(f"   🔧 DEBUG: System data keys = {list(system_summary.keys())[:5]}...")  # Debug line

    # ANEXO 2 specific patterns for tabular solar generation data
    patterns = {
        'solar_plant': [
            r'^(PFV-[A-ZÁÉÍÓÚÑ\-_0-9]+)',              # Solar plants: PFV-ELBOCO
            r'^(PMGD-PFV-[A-ZÁÉÍÓÚÑ\-_0-9]+)',        # Distributed solar: PMGD-PFV-QUEBRADA
            r'^(PMGD-[A-ZÁÉÍÓÚÑ\-_0-9]+)',            # Other distributed generation
        ],
        'tabular_generation': [
            # Pattern: PLANT_NAME + 24 hourly values + TOT.DIA + DMAX + DMED
            r'^([A-Z\-_0-9]+)\s+((?:\d+,\d+\s*){20,})\s*(\d+,\d+)\s+(\d+,\d+)\s+(\d+,\d+)\s*$',
            r'^([A-Z\-_0-9]+)\s+((?:\d+,\d+\s*){15,})\s*(\d+,\d+)\s+(\d+,\d+)\s+(\d+,\d+)',
        ],
        'hourly_values': [
            # Extract sequences of comma-decimal numbers
            r'(\d+,\d+)',
        ],
        'plant_name_clean': [
            # Clean extraction of plant names from start of line
            r'^([A-Z][A-Z\-_0-9]*[A-Z0-9])',
        ]
    }
    
    # Combine raw and OCR text for better coverage
    combined_text = page_text + "\n" + ocr_text
    lines = combined_text.split('\n')
    
    def convert_to_float(value_str):
        """Convert comma decimal to float"""
        try:
            return float(value_str.replace(',', '.'))
        except:
            return 0.0

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Try to extract tabular generation data (main pattern)
        for pattern in patterns['tabular_generation']:
            match = re.match(pattern, line)
            if match:
                plant_name = match.group(1)
                hourly_section = match.group(2)
                total_daily = convert_to_float(match.group(3))
                daily_max = convert_to_float(match.group(4))
                daily_avg = convert_to_float(match.group(5))
                
                # Extract hourly values
                hourly_values = []
                for hourly_match in re.finditer(r'(\d+,\d+)', hourly_section):
                    hourly_values.append(convert_to_float(hourly_match.group(1)))
                
                # Determine plant type
                plant_type = "UNKNOWN"
                if plant_name.startswith('PFV-'):
                    plant_type = "SOLAR_PV"
                elif plant_name.startswith('PMGD-PFV-'):
                    plant_type = "DISTRIBUTED_SOLAR_PV"
                elif plant_name.startswith('PMGD-TER-'):
                    plant_type = "DISTRIBUTED_THERMAL"
                elif plant_name.startswith('PMGD-DIESEL-'):
                    plant_type = "DISTRIBUTED_DIESEL"
                elif plant_name.startswith('PMGD-'):
                    plant_type = "DISTRIBUTED_GENERATION"
                elif 'HIDRO' in plant_name or 'AGUA' in plant_name:
                    plant_type = "HYDROELECTRIC"
                elif 'EOLICA' in plant_name or 'WIND' in plant_name:
                    plant_type = "WIND"
                elif 'CARBO' in plant_name or 'COAL' in plant_name:
                    plant_type = "COAL"
                elif 'GAS' in plant_name:
                    plant_type = "NATURAL_GAS"
                elif 'NUCLEAR' in plant_name:
                    plant_type = "NUCLEAR"

                # Extract colors using multiple approaches
                plant_color = "#808080"  # Default gray
                color_source = "default"

                if document_path:
                    # First priority: Actual PDF colors from graphics/text formatting
                    actual_colors = extract_actual_pdf_colors(document_path, page_num)
                    if actual_colors and actual_colors.get('text_colors'):
                        # Check if plant name appears in colored text
                        for text_key, color_info in actual_colors['text_colors'].items():
                            if plant_name in text_key or text_key in plant_name:
                                plant_color = color_info['color']
                                color_source = f"pdf_text_formatting"
                                print(f"   🎨 Found actual PDF text color {plant_color} for {plant_name}")
                                break

                    # Second priority: OCR-based color detection
                    if color_source == "default":
                        text_colors = extract_colors_via_text_analysis(page_text + "\n" + ocr_text)
                        if text_colors and text_colors.get('color_mapping'):
                            for color_key, color_info in text_colors['color_mapping'].items():
                                if plant_name in color_key or color_key in plant_name:
                                    plant_color = color_info['color']
                                    color_source = f"ocr_text_{color_info['color_name']}"
                                    print(f"   🎨 OCR detected color {color_info['color_name']} ({plant_color}) for {plant_name}")
                                    break

                    # Third priority: PDF graphic colors
                    if color_source == "default" and actual_colors and actual_colors.get('graphic_colors'):
                        graphic_colors = list(actual_colors['graphic_colors'].values())
                        if graphic_colors:
                            # Use plant index to assign different graphic colors
                            color_index = len(extracted_data['real_generation_records']) % len(graphic_colors)
                            plant_color = graphic_colors[color_index]['color']
                            color_source = "pdf_graphics"
                            print(f"   🎨 Assigned actual PDF graphic color {plant_color} to {plant_name}")

                    # Fourth priority: Fallback to PDF visual colors
                    if color_source == "default":
                        page_colors = extract_colors_from_page(document_path, page_num)
                        detected_colors = page_colors.get('page_colors', [])

                        if detected_colors:
                            # Use plant index to assign different detected colors
                            color_index = len(extracted_data['real_generation_records']) % len(detected_colors)
                            plant_color = detected_colors[color_index]
                            color_source = "pdf_visual"
                            print(f"   🎨 Assigned PDF color {plant_color} to {plant_name}")

                # Final fallback to unique colors per plant (not type-based)
                if color_source == "default":
                    # Generate unique colors for each plant using a hash-based approach
                    import hashlib

                    # Use plant name to generate a consistent unique color
                    plant_hash = hashlib.md5(plant_name.encode()).hexdigest()[:6]
                    plant_color = f"#{plant_hash}"
                    color_source = f"unique_hash_{plant_name}"

                    # Alternative: Use a predefined palette of distinct colors
                    distinct_colors = [
                        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
                        "#F8C471", "#82E0AA", "#F1948A", "#85C1E9", "#D7BDE2",
                        "#A3E4D7", "#FCF3CF", "#FADBD8", "#D5DBDB", "#AED6F1"
                    ]

                    # Use plant index to assign from distinct color palette
                    plant_index = len(extracted_data['real_generation_records'])
                    if plant_index < len(distinct_colors):
                        plant_color = distinct_colors[plant_index]
                        color_source = f"palette_index_{plant_index}"

                    print(f"   🎨 Assigned unique color {plant_color} to {plant_name} ({color_source})")
                
                # Calculate operational metrics
                operational_hours = sum(1 for v in hourly_values if v > 0.0)
                peak_hour = hourly_values.index(max(hourly_values)) + 1 if hourly_values else 0

                # Build hourly data with hour numbers
                hourly_data_with_hours = []
                for i, value in enumerate(hourly_values, 1):
                    hourly_data_with_hours.append({
                        "hour": i,
                        "value": value
                    })

                plant_data = {
                    'plant_name': plant_name,
                    'plant_type': plant_type,
                    'plant_color': plant_color,
                    'daily_total_mwh': total_daily,
                    'daily_max_mw': daily_max,
                    'daily_avg_mw': daily_avg,
                    'hourly_data': hourly_data_with_hours,
                    'operational_hours': operational_hours,
                    'peak_hour': peak_hour,
                    'source': 'tabular_extraction'
                }
                
                extracted_data['real_generation_records'].append({
                    'plant_name': plant_name,
                    'data': plant_data,
                    'source_line': i
                })
                extracted_data['extraction_quality']['patterns_found'] += 1
                break
        
        # Fallback: Try to extract just plant names for incomplete lines
        if not any(re.match(pattern, line) for pattern in patterns['tabular_generation']):
            for pattern in patterns['solar_plant']:
                match = re.match(pattern, line)
                if match:
                    plant_name = match.group(1)
                    
                    # Only add if not already found by tabular extraction
                    existing_names = [record['plant_name'] for record in extracted_data['real_generation_records']]
                    if plant_name not in existing_names:
                        # Determine plant type and assign unique color
                        basic_type = 'UNKNOWN'

                        if 'PFV' in plant_name:
                            if plant_name.startswith('PMGD-PFV-'):
                                basic_type = 'DISTRIBUTED_SOLAR_PV'
                            else:
                                basic_type = 'SOLAR_PV'
                        elif plant_name.startswith('PMGD-TER-'):
                            basic_type = 'DISTRIBUTED_THERMAL'
                        elif plant_name.startswith('PMGD-DIESEL-'):
                            basic_type = 'DISTRIBUTED_DIESEL'
                        elif plant_name.startswith('PMGD-'):
                            basic_type = 'DISTRIBUTED_GENERATION'

                        # Assign unique color using the same logic as main extraction
                        distinct_colors = [
                            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
                            "#F8C471", "#82E0AA", "#F1948A", "#85C1E9", "#D7BDE2",
                            "#A3E4D7", "#FCF3CF", "#FADBD8", "#D5DBDB", "#AED6F1"
                        ]

                        plant_index = len(extracted_data['real_generation_records'])
                        if plant_index < len(distinct_colors):
                            basic_color = distinct_colors[plant_index]
                        else:
                            # Fallback to hash-based unique color
                            import hashlib
                            plant_hash = hashlib.md5(plant_name.encode()).hexdigest()[:6]
                            basic_color = f"#{plant_hash}"

                        plant_data = {
                            'plant_name': plant_name,
                            'plant_type': basic_type,
                            'plant_color': basic_color,
                            'source': 'name_only_extraction'
                        }
                        
                        extracted_data['real_generation_records'].append({
                            'plant_name': plant_name,
                            'data': plant_data,
                            'source_line': i
                        })
                        extracted_data['extraction_quality']['patterns_found'] += 1
                    break
    
    # Calculate summary metrics for solar plant data
    if extracted_data['real_generation_records']:
        total_daily_mwh = sum(
            record['data'].get('daily_total_mwh', 0) 
            for record in extracted_data['real_generation_records']
            if isinstance(record['data'].get('daily_total_mwh'), (int, float))
        )
        max_capacity_mw = sum(
            record['data'].get('daily_max_mw', 0) 
            for record in extracted_data['real_generation_records']
            if isinstance(record['data'].get('daily_max_mw'), (int, float))
        )
        total_operational_hours = sum(
            record['data'].get('operational_hours', 0) 
            for record in extracted_data['real_generation_records']
            if isinstance(record['data'].get('operational_hours'), int)
        )
        
        # Classify plants by type
        solar_plants = [r for r in extracted_data['real_generation_records'] if r['data'].get('plant_type') == 'SOLAR_PV']
        distributed_solar = [r for r in extracted_data['real_generation_records'] if r['data'].get('plant_type') == 'DISTRIBUTED_SOLAR_PV']
        
        extracted_data['summary_metrics'] = {
            'total_plants': len(extracted_data['real_generation_records']),
            'solar_pv_plants': len(solar_plants),
            'distributed_solar_plants': len(distributed_solar),
            'total_daily_generation_mwh': total_daily_mwh,
            'total_max_capacity_mw': max_capacity_mw,
            'avg_operational_hours': total_operational_hours / len(extracted_data['real_generation_records']) if extracted_data['real_generation_records'] else 0,
            'system_type': 'RENEWABLE_SOLAR_FOCUSED'
        }
    
    # Determine data type and set summary metrics based on what was found
    has_plant_data = 'real_generation_records' in extracted_data and extracted_data['real_generation_records']
    has_system_data = 'system_summary_data' in extracted_data and extracted_data['system_summary_data']

    print(f"   🔧 DEBUG: Final check - extracted_data keys = {list(extracted_data.keys())}")  # Debug line
    print(f"   🔧 DEBUG: has_plant_data={has_plant_data}, has_system_data={has_system_data}")  # Debug line

    if has_plant_data and has_system_data:
        extracted_data['data_type'] = 'MIXED_DATA'
        print(f"   🔄 Mixed data page: {len(extracted_data['real_generation_records'])} plants + system summary")
        print(f"   🔧 DEBUG: has_system_data={has_system_data}, system_data_exists={'system_summary_data' in extracted_data}")  # Debug line
        # Add system summary metrics to existing plant metrics
        if has_system_data:
            system_metrics = {
                'system_categories': len(extracted_data['system_summary_data']),
                'has_total_sen': 'total_sen' in extracted_data['system_summary_data'],
                'has_demand_data': any('demanda' in k for k in extracted_data['system_summary_data'].keys()),
                'has_losses_data': any('perdidas' in k for k in extracted_data['system_summary_data'].keys()),
                'has_flow_data': 'flujo_changos_cumbres' in extracted_data['system_summary_data'],
                'data_completeness': 'COMPLETE' if len(extracted_data['system_summary_data']) >= 6 else 'PARTIAL'
            }
            if 'summary_metrics' in extracted_data:
                extracted_data['summary_metrics'].update(system_metrics)
            else:
                extracted_data['summary_metrics'] = system_metrics
    elif has_system_data:
        extracted_data['data_type'] = 'SYSTEM_OPERATIONAL_SUMMARY'
        extracted_data['chapter'] = 'ANEXO_02_SYSTEM_SUMMARY'
        extracted_data['summary_metrics'] = {
            'system_categories': len(extracted_data['system_summary_data']),
            'has_total_sen': 'total_sen' in extracted_data['system_summary_data'],
            'has_demand_data': any('demanda' in k for k in extracted_data['system_summary_data'].keys()),
            'has_losses_data': any('perdidas' in k for k in extracted_data['system_summary_data'].keys()),
            'has_flow_data': 'flujo_changos_cumbres' in extracted_data['system_summary_data'],
            'data_completeness': 'COMPLETE' if len(extracted_data['system_summary_data']) >= 6 else 'PARTIAL'
        }
    elif has_plant_data:
        extracted_data['data_type'] = 'PLANT_GENERATION'
    else:
        extracted_data['data_type'] = 'NO_DATA'

    # Set confidence level based on patterns found and data types
    confidence_score = extracted_data['extraction_quality']['patterns_found']
    if has_system_data:
        confidence_score += 5  # System data adds confidence

    if confidence_score >= 7:
        extracted_data['extraction_quality']['confidence'] = 'HIGH'
    elif confidence_score >= 3:
        extracted_data['extraction_quality']['confidence'] = 'MEDIUM'
    else:
        extracted_data['extraction_quality']['confidence'] = 'LOW'

    # Add comprehensive metadata including date, document type, and ANEXO title
    document_metadata = extract_date_info(page_text)
    if document_metadata:
        extracted_data['document_metadata'] = document_metadata

    return extracted_data

def process_page(page_num: int, document_path: str) -> Dict:
    """Process a single page from ANEXO 2"""
    print(f"🔍 Processing ANEXO 2 page {page_num} (Real Generation Data)")
    
    # Extract text using both methods
    raw_text = extract_page_text(document_path, page_num)
    ocr_text = extract_ocr_text(document_path, page_num)
    
    if not raw_text and not ocr_text:
        print(f"⚠️  No text extracted from page {page_num}")
        return {}
    
    # Extract actual colors from PDF graphics and text
    actual_pdf_colors = extract_actual_pdf_colors(document_path, page_num)
    page_colors = extract_colors_from_page(document_path, page_num)
    text_colors = extract_colors_via_text_analysis(raw_text + "\n" + ocr_text)

    # Extract generation data (which includes comprehensive metadata)
    extracted_data = extract_real_generation_data(raw_text, ocr_text, page_num, document_path)

    # Reorganize: Move document_metadata to top and simplify color analysis
    if 'document_metadata' in extracted_data:
        document_metadata = extracted_data.pop('document_metadata')
        # Rebuild structure with metadata first
        reordered_data = {
            'document_metadata': document_metadata,
            'page': extracted_data.get('page'),
            'chapter': extracted_data.get('chapter'),
            'extraction_timestamp': extracted_data.get('extraction_timestamp'),
            'real_generation_records': extracted_data.get('real_generation_records', []),
            'summary_metrics': extracted_data.get('summary_metrics', {}),
            'extraction_quality': extracted_data.get('extraction_quality', {}),
            'data_type': extracted_data.get('data_type')
        }
        extracted_data = reordered_data

    # Add simplified color information (only essential data)
    color_summary = {}
    if actual_pdf_colors and actual_pdf_colors.get('total_colors_found', 0) > 0:
        color_summary['colors_found'] = actual_pdf_colors['total_colors_found']
        print(f"   🎨 Found {actual_pdf_colors['total_colors_found']} actual colors in PDF graphics/text")
    if text_colors and text_colors.get('total_colors_found', 0) > 0:
        color_summary['text_color_references'] = text_colors['total_colors_found']
        print(f"   🎨 Found {text_colors['total_colors_found']} color references in text")

    if color_summary:
        extracted_data['color_summary'] = color_summary

    # Check if extraction was successful
    if not extracted_data:
        print(f"⚠️  No data extracted from page {page_num}")
        return {}
    
    # Print results based on data type
    print(f"📊 Results for page {page_num}:")

    if extracted_data.get('system_summary_data'):
        system_data = extracted_data['system_summary_data']
        summary_count = len([k for k, v in system_data.items() if v.get('data_type') == 'hourly_series'])
        dmax_count = len([k for k, v in system_data.items() if v.get('data_type') == 'single_value'])
        print(f"   📈 System Summary: {summary_count} categories + {dmax_count} summary values")

    if extracted_data.get('real_generation_records'):
        print(f"   ✅ Found {len(extracted_data['real_generation_records'])} solar generation records")
        for record in extracted_data['real_generation_records'][:10]:  # Show first 10 only
            plant = record['plant_name']
            data = record['data']
            daily_total = data.get('daily_total_mwh', 'N/A')
            daily_max = data.get('daily_max_mw', 'N/A')
            op_hours = data.get('operational_hours', 'N/A')
            plant_type = data.get('plant_type', 'Unknown')
            print(f"      - {plant} ({plant_type}): Total={daily_total}MWh, Max={daily_max}MW, OpHours={op_hours}")
        if len(extracted_data['real_generation_records']) > 10:
            print(f"      ... and {len(extracted_data['real_generation_records']) - 10} more plants")
    elif not extracted_data.get('system_summary_data'):
        print(f"   ⚠️  No generation records found")

    print(f"   📈 Confidence: {extracted_data['extraction_quality']['confidence']}")
    print(f"   🏷️  Data Type: {extracted_data.get('data_type', 'UNKNOWN')}")

    return extracted_data

def main():
    """Main extraction function"""
    print("🚀 ANEXO 2 REAL GENERATION DATA EXTRACTOR")
    print("=" * 60)
    print("📄 Target: ANEXO 2 (Pages 63-95) - Real Generation Data")
    print("🎯 Focus: Actual generation vs programmed generation")
    print("=" * 60)
    
    # Find PDF file
    document_path = find_pdf_file()
    if not document_path:
        # Try direct path
        direct_path = "/home/alonso/Documentos/Github/Proyecto Dark Data CEN/data/documents/anexos_EAF/source_documents/Anexos-EAF-089-2025.pdf"
        if Path(direct_path).exists():
            document_path = direct_path
        else:
            print("❌ EAF PDF file not found!")
            print("   Please place Anexos-EAF-089-2025.pdf in:")
            print("   - data/documents/anexos_EAF/source_documents/")
            print("   - data/documents/anexos_EAF/samples_and_tests/")
            return
    
    print(f"📁 Found PDF: {document_path}")
    
    # Process pages
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        # Process all ANEXO 2 pages (63-95)
        print("📊 Processing all ANEXO 2 pages (63-95)...")
        all_results = []
        
        for page_num in range(63, 96):  # Pages 63-95
            try:
                result = process_page(page_num, document_path)
                if result:
                    all_results.append(result)
                print()  # Empty line between pages
            except Exception as e:
                print(f"❌ Error processing page {page_num}: {e}")
        
        # Save combined results
        if all_results:
            output_file = project_root / "extractions" / "anexo_02_real_generation" / f"anexo2_real_generation_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved complete results to: {output_file}")
    
    else:
        # Process single page
        page_num = int(sys.argv[1]) if len(sys.argv) > 1 else 65  # Default to page 65
        
        if not (63 <= page_num <= 95):
            print(f"⚠️  Page {page_num} is outside ANEXO 2 range (63-95)")
            print("   Using default page 65...")
            page_num = 65
        
        result = process_page(page_num, document_path)
        
        if result:
            # Save single page result
            output_file = project_root / "extractions" / "anexo_02_real_generation" / f"anexo2_page_{page_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved results to: {output_file}")

if __name__ == "__main__":
    main()