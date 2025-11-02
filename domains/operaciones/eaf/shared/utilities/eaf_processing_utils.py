"""
EAF Processing Utilities
Common utilities for processing EAF documents across all chapters
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class EAFIdentifier:
    """EAF document identifier components"""
    number: str
    year: str
    full_id: str


class EAFPatterns:
    """Common regex patterns for EAF document processing"""

    # EAF number patterns
    EAF_NUMBER = re.compile(r'EAF\s*(\d+)/(\d{4})', re.IGNORECASE)

    # Date patterns
    DATE_PATTERNS = [
        re.compile(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'),  # DD/MM/YYYY or DD-MM-YYYY
        re.compile(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})'),  # YYYY/MM/DD or YYYY-MM-DD
        re.compile(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'),  # DD de MM de YYYY (Spanish)
    ]

    # Equipment patterns
    EQUIPMENT_PATTERNS = {
        'transformer': re.compile(r'transformador\s+(?:N°\s*)?(\d+|\w+)', re.IGNORECASE),
        'line': re.compile(r'línea\s+(?:de\s+)?(\d+\s*kV)', re.IGNORECASE),
        'substation': re.compile(r'S/E\s+([A-Za-z\s]+)', re.IGNORECASE),
        'interruptor': re.compile(r'interruptor\s+(\w+)', re.IGNORECASE),
    }

    # Company patterns (Chilean companies)
    COMPANY_PATTERNS = [
        re.compile(r'Enel\s+(?:Chile|Generación|Distribución)', re.IGNORECASE),
        re.compile(r'Colbún\s+S\.A\.?', re.IGNORECASE),
        re.compile(r'AES\s+Gener', re.IGNORECASE),
        re.compile(r'ENGIE\s+(?:Chile|Energía)', re.IGNORECASE),
        re.compile(r'Statkraft', re.IGNORECASE),
    ]

    # Voltage levels
    VOLTAGE_PATTERN = re.compile(r'(\d+)\s*kV', re.IGNORECASE)

    # Chilean RUT pattern
    RUT_PATTERN = re.compile(r'(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])')


class EAFParser:
    """Parser utilities for EAF documents"""

    @staticmethod
    def extract_eaf_number(text: str) -> Optional[EAFIdentifier]:
        """
        Extract EAF number from text

        Args:
            text: Text to search for EAF number

        Returns:
            EAFIdentifier or None if not found
        """
        match = EAFPatterns.EAF_NUMBER.search(text)
        if match:
            number, year = match.groups()
            full_id = f"EAF {number}/{year}"
            return EAFIdentifier(number=number, year=year, full_id=full_id)
        return None

    @staticmethod
    def extract_dates(text: str) -> List[datetime]:
        """
        Extract dates from text using multiple patterns

        Args:
            text: Text to search for dates

        Returns:
            List of datetime objects
        """
        dates = []

        for pattern in EAFPatterns.DATE_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    if len(match) == 3:
                        # Handle different date formats
                        if pattern == EAFPatterns.DATE_PATTERNS[0]:  # DD/MM/YYYY
                            day, month, year = match
                            date = datetime(int(year), int(month), int(day))
                        elif pattern == EAFPatterns.DATE_PATTERNS[1]:  # YYYY/MM/DD
                            year, month, day = match
                            date = datetime(int(year), int(month), int(day))
                        else:  # Spanish format
                            day, month_name, year = match
                            month = EAFParser._spanish_month_to_number(month_name)
                            if month:
                                date = datetime(int(year), month, int(day))
                            else:
                                continue
                        dates.append(date)
                except ValueError:
                    continue

        return list(set(dates))  # Remove duplicates

    @staticmethod
    def _spanish_month_to_number(month_name: str) -> Optional[int]:
        """Convert Spanish month name to number"""
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        return months.get(month_name.lower())

    @staticmethod
    def extract_equipment(text: str) -> Dict[str, List[str]]:
        """
        Extract equipment mentions from text

        Args:
            text: Text to search for equipment

        Returns:
            Dictionary with equipment types and found instances
        """
        equipment = {}

        for eq_type, pattern in EAFPatterns.EQUIPMENT_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                equipment[eq_type] = matches

        return equipment

    @staticmethod
    def extract_companies(text: str) -> List[str]:
        """
        Extract company names from text

        Args:
            text: Text to search for companies

        Returns:
            List of company names found
        """
        companies = []

        for pattern in EAFPatterns.COMPANY_PATTERNS:
            matches = pattern.findall(text)
            companies.extend(matches)

        return list(set(companies))  # Remove duplicates

    @staticmethod
    def extract_voltage_levels(text: str) -> List[str]:
        """
        Extract voltage levels from text

        Args:
            text: Text to search for voltage levels

        Returns:
            List of voltage levels (e.g., ['220 kV', '66 kV'])
        """
        matches = EAFPatterns.VOLTAGE_PATTERN.findall(text)
        return [f"{voltage} kV" for voltage in matches]

    @staticmethod
    def extract_ruts(text: str) -> List[str]:
        """
        Extract Chilean RUTs from text

        Args:
            text: Text to search for RUTs

        Returns:
            List of RUT strings
        """
        matches = EAFPatterns.RUT_PATTERN.findall(text)
        return matches


class EAFValidator:
    """Validation utilities for EAF data"""

    @staticmethod
    def validate_eaf_number(eaf_number: str) -> bool:
        """Validate EAF number format"""
        return bool(EAFPatterns.EAF_NUMBER.match(eaf_number))

    @staticmethod
    def validate_rut(rut: str) -> bool:
        """Validate Chilean RUT format and check digit"""
        if not EAFPatterns.RUT_PATTERN.match(rut):
            return False

        # Remove dots and extract numbers and check digit
        clean_rut = rut.replace('.', '').replace('-', '')
        if len(clean_rut) < 2:
            return False

        numbers = clean_rut[:-1]
        check_digit = clean_rut[-1].upper()

        # Calculate check digit
        multipliers = [2, 3, 4, 5, 6, 7, 2, 3, 4, 5, 6, 7]
        total = 0

        for i, digit in enumerate(reversed(numbers)):
            total += int(digit) * multipliers[i % 12]

        remainder = 11 - (total % 11)
        if remainder == 11:
            expected = '0'
        elif remainder == 10:
            expected = 'K'
        else:
            expected = str(remainder)

        return check_digit == expected

    @staticmethod
    def validate_date_range(date: datetime, min_year: int = 2020, max_year: int = None) -> bool:
        """Validate if date is within expected range for EAF reports"""
        if max_year is None:
            max_year = datetime.now().year + 1

        return min_year <= date.year <= max_year


class EAFFileManager:
    """File management utilities for EAF processing"""

    @staticmethod
    def get_eaf_output_path(base_path: Path, eaf_number: str, output_type: str) -> Path:
        """
        Generate output file path for EAF processing results

        Args:
            base_path: Base directory path
            eaf_number: EAF number (e.g., "EAF 299/2025")
            output_type: Type of output (raw_extractions, validated_extractions, universal_json)

        Returns:
            Path object for output file
        """
        safe_name = eaf_number.replace('/', '_').replace(' ', '_').lower()
        output_dir = base_path / "outputs" / output_type
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{safe_name}.json"

    @staticmethod
    def save_extraction_results(data: Dict[str, Any], output_path: Path) -> None:
        """Save extraction results to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def load_extraction_results(input_path: Path) -> Dict[str, Any]:
        """Load extraction results from JSON file"""
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)


# Common EAF processing constants
EAF_CONSTANTS = {
    'VOLTAGE_LEVELS': ['500 kV', '220 kV', '154 kV', '110 kV', '66 kV', '23 kV', '13.2 kV'],
    'INCIDENT_TYPES': [
        'Desconexión forzada',
        'Apertura intempestiva',
        'Falla de equipo',
        'Sobrecarga',
        'Cortocircuito',
        'Falla de aislación',
        'Operación indebida'
    ],
    'SEVERITY_LEVELS': ['Crítica', 'Alta', 'Media', 'Baja'],
    'EQUIPMENT_TYPES': [
        'Transformador',
        'Línea de transmisión',
        'Interruptor',
        'Seccionador',
        'Generador',
        'Reactor',
        'Condensador'
    ]
}