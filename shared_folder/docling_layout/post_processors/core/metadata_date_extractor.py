"""
POST-PROCESSOR: Metadata Date Extractor
=========================================

Extracts key dates from document content and adds them to metadata:
- Fecha de Emisión (Emission Date)
- Fecha de la Falla (Failure Date)

Dates are typically found in the first section headers.
"""

import re
from datetime import datetime
from typing import Optional, Tuple


def extract_dates_to_metadata(doc) -> dict:
    """
    Extract dates from document content and return metadata dict.

    Searches for:
    1. Fecha de Emisión: DD-MM-YYYY or DD de MMMM de YYYY
    2. Fecha y Hora de la falla (in first 30 section headers)

    Returns:
        dict: {'fecha_emision': str, 'fecha_falla': str, 'hora_falla': str}
    """

    print("\n" + "=" * 80)
    print("📅 [DATE EXTRACTION] Extracting dates from document headers")
    print("=" * 80)

    metadata = {
        'fecha_emision': None,
        'fecha_falla': None,
        'hora_falla': None
    }

    # Get all section headers (first 30 should be enough)
    headers = []
    for item in doc.texts[:30]:
        if hasattr(item, 'label') and item.label.name == 'SECTION_HEADER':
            headers.append(item.text.strip())

    print(f"📊 Analyzing {len(headers)} section headers...")
    print()

    # Pattern 1: Fecha de Emisión: DD-MM-YYYY
    emission_pattern = re.compile(
        r'Fecha\s+de\s+Emisión:\s*(\d{1,2})-(\d{1,2})-(\d{4})',
        re.IGNORECASE
    )

    # Pattern 2: Fecha de Emisión: DD de MMMM de YYYY
    emission_pattern_long = re.compile(
        r'Fecha\s+de\s+Emisión:\s*(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
        re.IGNORECASE
    )

    # Pattern 3: DD de MMMM de YYYY (for failure date in text)
    date_pattern_long = re.compile(
        r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})',
        re.IGNORECASE
    )

    # Pattern 4: Time pattern HH:MM:SS
    time_pattern = re.compile(r'(\d{1,2}):(\d{2}):(\d{2})')

    # Search for emission date
    for header in headers:
        # Try DD-MM-YYYY format first
        match = emission_pattern.search(header)
        if match:
            day, month, year = match.groups()
            metadata['fecha_emision'] = f"{day}-{month}-{year}"
            print(f"✅ Fecha de Emisión encontrada: {metadata['fecha_emision']}")
            print(f"   Fuente: '{header[:80]}{'...' if len(header) > 80 else ''}'")
            print()
            break

        # Try long format
        match = emission_pattern_long.search(header)
        if match:
            day, month_name, year = match.groups()
            metadata['fecha_emision'] = f"{day} de {month_name} de {year}"
            print(f"✅ Fecha de Emisión encontrada: {metadata['fecha_emision']}")
            print(f"   Fuente: '{header[:80]}{'...' if len(header) > 80 else ''}'")
            print()
            break

    # Search for failure date and time
    # Look for headers containing "falla" or date patterns
    for header in headers:
        header_lower = header.lower()

        # Check if this header mentions "falla" or "hora"
        if 'falla' in header_lower or 'hora' in header_lower:
            # Look for date pattern
            date_match = date_pattern_long.search(header)
            if date_match and not metadata['fecha_falla']:
                day, month_name, year = date_match.groups()
                metadata['fecha_falla'] = f"{day} de {month_name} de {year}"
                print(f"✅ Fecha de la Falla encontrada: {metadata['fecha_falla']}")
                print(f"   Fuente: '{header[:80]}{'...' if len(header) > 80 else ''}'")
                print()

            # Look for time pattern
            time_match = time_pattern.search(header)
            if time_match and not metadata['hora_falla']:
                hour, minute, second = time_match.groups()
                metadata['hora_falla'] = f"{hour}:{minute}:{second}"
                print(f"✅ Hora de la Falla encontrada: {metadata['hora_falla']}")
                print(f"   Fuente: '{header[:80]}{'...' if len(header) > 80 else ''}'")
                print()

    # Also check TEXT items (not just section headers) for failure date and time
    if not metadata['fecha_falla'] or not metadata['hora_falla']:
        if not metadata['fecha_falla']:
            print("⚠️  Fecha de falla no encontrada en section_headers, buscando en textos...")
        if not metadata['hora_falla']:
            print("⚠️  Hora de falla no encontrada en section_headers, buscando en textos...")

        for item in doc.texts[:50]:
            if hasattr(item, 'label') and item.label.name == 'TEXT':
                text = item.text.strip()
                text_lower = text.lower()

                if ('falla' in text_lower or 'hora' in text_lower or 'horas' in text_lower) and len(text) < 400:
                    # Look for date
                    if not metadata['fecha_falla']:
                        date_match = date_pattern_long.search(text)
                        if date_match:
                            day, month_name, year = date_match.groups()
                            metadata['fecha_falla'] = f"{day} de {month_name} de {year}"
                            print(f"✅ Fecha de la Falla encontrada: {metadata['fecha_falla']}")
                            print(f"   Fuente: '{text[:80]}{'...' if len(text) > 80 else ''}'")
                            print()

                    # Look for time
                    if not metadata['hora_falla']:
                        time_match = time_pattern.search(text)
                        if time_match:
                            hour, minute, second = time_match.groups()
                            metadata['hora_falla'] = f"{hour}:{minute}:{second}"
                            print(f"✅ Hora de la Falla encontrada: {metadata['hora_falla']}")
                            print(f"   Fuente: '{text[:80]}{'...' if len(text) > 80 else ''}'")
                            print()

                    # If both found, stop searching
                    if metadata['fecha_falla'] and metadata['hora_falla']:
                        break

    # Summary
    print("=" * 80)
    print("📊 RESUMEN DE FECHAS EXTRAÍDAS:")
    print("=" * 80)
    for key, value in metadata.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value if value else 'No encontrada'}")
    print("=" * 80)
    print()

    return metadata


def apply_date_extraction_to_document(doc) -> dict:
    """
    Apply date extraction to document and return metadata dict.

    This function can be called from the main extraction script.

    Returns:
        dict: Extracted date metadata
    """
    return extract_dates_to_metadata(doc)
