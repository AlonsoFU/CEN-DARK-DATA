#!/usr/bin/env python3
"""
ANEXO 1 Enhanced Extractor - WITH OCR PER ROW
==============================================

This version adds OCR results for each metric row in the JSON output.
You can see both:
- raw_line: What PDF text extraction gives us
- ocr_line: What OCR visually sees
- comparison: Differences between raw and OCR

Usage:
    python scripts/extract_anexo1_with_ocr_per_row.py [page_number]
"""

import sys
import re
import json
import io
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Get the correct project root (go up 6 levels from the script)
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
    os.system("./venv/bin/pip install PyPDF2 pytesseract pillow PyMuPDF opencv-python")
    from PyPDF2 import PdfReader
    import pytesseract
    from PIL import Image
    import fitz
    import cv2
    import numpy as np

def extract_page_text(document_path: str, page_num: int) -> str:
    """Extract text from single page (1-indexed) using PyPDF2"""
    try:
        reader = PdfReader(document_path)
        if 1 <= page_num <= len(reader.pages):
            page = reader.pages[page_num - 1]
            return page.extract_text().strip()
        return ""
    except Exception as e:
        print(f"Error extracting page {page_num}: {e}")
        return ""

def extract_ocr_text(document_path: str, page_num: int) -> str:
    """Extract text using OCR on rendered PDF page"""
    try:
        doc = fitz.open(document_path)
        if 0 <= page_num - 1 < len(doc):
            page = doc[page_num - 1]
            
            # High DPI for better OCR accuracy
            mat = fitz.Matrix(2, 2)  # 144 DPI (72*2)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Convert to numpy array for OpenCV processing
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding for better text clarity
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL for pytesseract
            processed_pil = Image.fromarray(processed)
            
            # Run OCR with Spanish + English
            ocr_text = pytesseract.image_to_string(
                processed_pil,
                lang='spa+eng',
                config='--psm 6'  # Treat as uniform text block
            )
            
            doc.close()
            return ocr_text.strip()
        
        doc.close()
        return ""
    except Exception as e:
        print(f"⚠️  OCR extraction failed: {e}")
        return ""

def find_ocr_row_for_metric(ocr_text: str, metric_pattern: str, raw_line: str) -> Optional[Dict]:
    """Find the corresponding OCR line for a metric"""
    
    # Extract key words from raw line to match against OCR
    if "Generaci" in raw_line:
        search_terms = ["Generaci", "Total", "MWh"]
    elif "Encendido" in raw_line:
        search_terms = ["Encendido", "Detenci"]
    elif "Operaci" in raw_line:
        search_terms = ["Operaci", "Costos"]
    elif "Marginal" in raw_line:
        search_terms = ["Marginal", "Costo"]
    elif "Indisponibilidad" in raw_line:
        search_terms = ["Indisponibilidad"]
    elif "Factor" in raw_line:
        search_terms = ["Factor", "Planta"]
    elif "Horas" in raw_line:
        search_terms = ["Horas", "Servicio"]
    else:
        return None
    
    # Look for OCR lines containing these terms
    best_match = None
    best_score = 0
    
    for ocr_line in ocr_text.split('\n'):
        ocr_line = ocr_line.strip()
        if not ocr_line:
            continue
        
        # Score based on how many search terms are found
        score = sum(1 for term in search_terms if term.lower() in ocr_line.lower())
        
        # Prefer lines with numbers (likely data rows)
        if re.search(r'\d+', ocr_line):
            score += 0.5
        
        if score > best_score:
            best_score = score
            best_match = ocr_line
    
    if best_match and best_score >= 1:  # At least one search term found
        # Extract numbers from both lines
        raw_numbers = re.findall(r'\d+(?:[.,]\d+)?', raw_line)
        ocr_numbers = re.findall(r'\d+(?:[.,]\d+)?', best_match)
        
        return {
            "ocr_line": best_match,
            "ocr_numbers": ocr_numbers,
            "raw_numbers": raw_numbers,
            "ocr_count": len(ocr_numbers),
            "raw_count": len(raw_numbers),
            "match_confidence": best_score,
            "shows_more_detail": len(ocr_numbers) > len(raw_numbers)
        }
    
    return None

def smart_number_extraction_with_ocr(line_text: str, ocr_data: Optional[Dict] = None) -> Tuple[List[str], Dict]:
    """Advanced number extraction with OCR comparison"""
    
    # Apply known OCR corrections
    known_corrections = {
        '980310125': '9803 10125',
        '99210': '992 10',
        '198105': '1 98 105',  # Your validated correction
    }
    
    corrected_text = line_text
    corrections_applied = []
    
    for wrong, correct in known_corrections.items():
        if wrong in corrected_text:
            corrected_text = corrected_text.replace(wrong, correct)
            corrections_applied.append(f"'{wrong}' → '{correct}'")
    
    # Extract numbers from corrected text
    raw_numbers = re.findall(r'\d+(?:[.,]\d+)?', corrected_text)
    
    corrected_numbers = []
    
    for num in raw_numbers:
        # Fix zero-prefix merges
        if len(num) == 3 and num.startswith('0') and num != '000' and '.' not in num and ',' not in num:
            corrected_numbers.extend(['0', num[1:]])
            corrections_applied.append(f"'{num}' → ['0', '{num[1:]}']")
            continue
        
        # Fix large number merges
        if len(num) >= 6 and '.' not in num and ',' not in num:
            if num == "198105":
                corrected_numbers.extend(['1', '98', '105'])
            elif len(num) == 6:
                corrected_numbers.extend([num[:3], num[3:]])
            elif len(num) == 9:
                corrected_numbers.extend([num[:4], num[4:]])
            else:
                corrected_numbers.append(num)
            continue
        
        # Clean decimal formatting
        if ',' in num:
            num = num.replace(',', '.')
        
        corrected_numbers.append(num)
    
    # Create OCR comparison data
    ocr_comparison = {
        "raw_extraction_count": len(re.findall(r'\d+(?:[.,]\d+)?', line_text)),
        "corrected_count": len(corrected_numbers),
        "corrections_applied": corrections_applied,
        "ocr_data": ocr_data if ocr_data else {"available": False}
    }
    
    if ocr_data:
        ocr_comparison["ocr_vs_raw"] = {
            "ocr_found_more": ocr_data["shows_more_detail"],
            "ocr_count": ocr_data["ocr_count"],
            "raw_count": ocr_data["raw_count"],
            "confidence": ocr_data["match_confidence"]
        }
    
    return corrected_numbers, ocr_comparison

def validate_24_hour_data(hourly_values: List[str]) -> Dict:
    """Validate 24-hour data"""
    return {
        "is_valid": len(hourly_values) == 24,
        "total_values": len(hourly_values),
        "expected_values": 24,
        "issues": [] if len(hourly_values) == 24 else [f"Found {len(hourly_values)} values, expected 24"]
    }

def extract_enhanced_with_ocr(document_path: str, page_num: int) -> Dict:
    """Main extraction function with OCR per row"""
    
    print(f"🔍 Enhanced Extraction with OCR - Page {page_num}")
    print("=" * 60)
    
    # Extract text using both methods
    print("📄 Extracting RAW PDF text...")
    raw_text = extract_page_text(document_path, page_num)
    
    print("🔎 Extracting OCR text...")
    ocr_text = extract_ocr_text(document_path, page_num)
    
    if not raw_text:
        print(f"❌ No text extracted from page {page_num}")
        return {}
    
    print(f"📊 RAW text length: {len(raw_text)} chars")
    print(f"📊 OCR text length: {len(ocr_text)} chars")
    
    # Define system metric patterns
    metric_patterns = {
        "generacion_total": r"Generaci[óo]n\s+Total[^\n]*\[MWh\][^\n]*",
        "costos_operacion": r"Costos?\s+Operaci[óo]n[^\n]*",
        "costos_encendido_detencion": r"Costos?\s+Encendido[^\n]*Detenci[^\n]*",
        "costos_totales": r"Costos?\s+Totales[^\n]*\[kUSD\][^\n]*",
        "costo_marginal": r"Costo\s+Marginal[^\n]*",
        "indisponibilidad_forzada": r"Indisponibilidad\s+Forzada[^\n]*",
        "indisponibilidad_programada": r"Indisponibilidad\s+Programada[^\n]*",
        "factor_planta_bruto": r"Factor\s+de?\s+Planta\s+Bruto[^\n]*",
        "factor_planta_neto": r"Factor\s+de?\s+Planta\s+Neto[^\n]*",
        "horas_servicio": r"Horas?\s+de?\s+Servicio[^\n]*"
    }
    
    # Extract system metrics with OCR per row
    system_metrics = {}
    total_ocr_validations = 0
    successful_ocr_matches = 0
    
    print(f"\n🔍 Processing system metrics...")
    
    for metric_key, pattern in metric_patterns.items():
        matches = re.findall(pattern, raw_text, re.IGNORECASE)
        if matches:
            raw_line = matches[0].strip()
            
            print(f"   📊 {metric_key.replace('_', ' ').title()}")
            
            # Find corresponding OCR line
            ocr_data = None
            if ocr_text:
                total_ocr_validations += 1
                ocr_data = find_ocr_row_for_metric(ocr_text, pattern, raw_line)
                if ocr_data:
                    successful_ocr_matches += 1
                    print(f"      ✅ OCR match found (confidence: {ocr_data['match_confidence']})")
                else:
                    print(f"      ⚠️  OCR match not found")
            
            # Extract numbers with OCR comparison
            numbers, ocr_comparison = smart_number_extraction_with_ocr(raw_line, ocr_data)
            
            # Determine hourly values and total
            if len(numbers) >= 24:
                hourly_values = numbers[:24]
                total = numbers[24] if len(numbers) > 24 else "calculated"
            else:
                hourly_values = numbers
                total = "calculated"
            
            # Handle special cases
            full_title = metric_key.replace('_', ' ').title()
            location_context = None
            
            if "costo_marginal" in metric_key:
                # Extract location context like "Quillota 220 kV"
                context_match = re.search(r'([A-Za-z]+\s+\d+\s*kV)', raw_line)
                if context_match:
                    location_context = context_match.group(1)
                    full_title = f"Costo Marginal [{location_context}] [USD/MWh]"
                else:
                    full_title = "Costo Marginal [USD/MWh]"
            elif "costos_encendido" in metric_key:
                full_title = "Costos Encendido/Detención [kUSD]"
            elif "costos_operacion" in metric_key:
                full_title = "Costos Operación [kUSD]"
            elif "generacion_total" in metric_key:
                full_title = "Generación Total [MWh]"
            
            # Build hourly data with hour numbers
            hourly_data_with_hours = []
            for i, value in enumerate(hourly_values, 1):
                hourly_data_with_hours.append({
                    "hour": i,
                    "value": value
                })

            # Build metric data with OCR information
            metric_data = {
                "full_title": full_title,
                "hourly_data": hourly_data_with_hours,
                "total": total,
                "raw_line": raw_line,
                "validation": validate_24_hour_data([item['value'] for item in hourly_data_with_hours]),
                "extraction_quality": "enhanced",
                "ocr_comparison": ocr_comparison
            }
            
            if location_context:
                metric_data["location_context"] = location_context
            
            system_metrics[metric_key] = metric_data
            
            print(f"      📊 Values: {len(hourly_values)} hourly + total: {total}")
            if ocr_comparison["corrections_applied"]:
                print(f"      🔧 Corrections: {', '.join(ocr_comparison['corrections_applied'])}")
    
    # Extract date info from text
    date_match = re.search(r'(\w+),?\s*(\d+)\s*de\s*(\w+)\s*de\s*(\d{4})', raw_text)
    date_info = {}
    if date_match:
        date_info = {
            "day_name": date_match.group(1),
            "day": date_match.group(2),
            "month": date_match.group(3),
            "year": date_match.group(4),
            "formatted_date": f"{date_match.group(1)} {date_match.group(2)} de {date_match.group(3)} de {date_match.group(4)}"
        }
    
    # Build final result
    result = {
        "document_metadata": {
            "document_file": Path(document_path).name,
            "document_path": document_path,
            "page_number": page_num,
            "extraction_timestamp": datetime.now().isoformat(),
            "document_type": "ANEXO_EAF",
            "extraction_method": "enhanced_with_ocr_per_row"
        },
        "upper_table": {
            "date_info": date_info,
            "system_metrics": system_metrics
        },
        "ocr_validation_summary": {
            "ocr_available": len(ocr_text) > 0,
            "ocr_text_length": len(ocr_text),
            "total_metrics_processed": len(system_metrics),
            "ocr_validations_attempted": total_ocr_validations,
            "successful_ocr_matches": successful_ocr_matches,
            "ocr_match_rate": f"{(successful_ocr_matches/total_ocr_validations*100):.1f}%" if total_ocr_validations > 0 else "0%"
        },
        "quality_summary": {
            "system_metrics_found": len(system_metrics),
            "validation_issues": sum(1 for m in system_metrics.values() if not m["validation"]["is_valid"]),
            "overall_quality": "excellent" if all(m["validation"]["is_valid"] for m in system_metrics.values()) else "good"
        }
    }
    
    return result

def main():
    """Main extraction function"""
    
    if len(sys.argv) != 2:
        print("Usage: python scripts/extract_anexo1_with_ocr_per_row.py [page_number]")
        sys.exit(1)
    
    try:
        page_num = int(sys.argv[1])
    except ValueError:
        print("Error: Page number must be an integer")
        sys.exit(1)
    
    # Try to find the document in various locations
    possible_paths = [
        project_root / "data" / "documents" / "anexos_EAF" / "source_documents" / "Anexos-EAF-089-2025.pdf",
        project_root / "data" / "documents" / "anexos_EAF" / "samples_and_tests" / "Anexos-EAF-089-2025.pdf",
        project_root / "data" / "documents" / "power_system_reports" / "anexos_EAF" / "Anexos-EAF-089-2025.pdf",
        project_root / "data" / "documents" / "anexos_EAF" / "raw" / "Anexos-EAF-089-2025.pdf"
    ]

    document_path = None
    for path in possible_paths:
        if path.exists():
            document_path = path
            break
    
    if not document_path:
        print("Error: Document not found in any of the expected locations")
        print("Tried:")
        for path in possible_paths:
            print(f"  - {path}")
        sys.exit(1)
    
    # Extract with OCR per row
    result = extract_enhanced_with_ocr(str(document_path), page_num)
    
    if not result:
        sys.exit(1)
    
    # Save results
    output_dir = project_root / "extractions" / "anexo_01_generation_programming"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"anexo01_page_{page_num:02d}_extraction.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Print summary
    ocr_summary = result["ocr_validation_summary"]
    quality_summary = result["quality_summary"]
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"   System metrics: {quality_summary['system_metrics_found']}")
    print(f"   OCR available: {'Yes' if ocr_summary['ocr_available'] else 'No'}")
    print(f"   OCR match rate: {ocr_summary['ocr_match_rate']}")
    print(f"   Overall quality: {quality_summary['overall_quality']}")
    print(f"   Validation issues: {quality_summary['validation_issues']}")

if __name__ == "__main__":
    main()