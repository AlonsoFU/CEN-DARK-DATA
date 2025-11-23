"""
Table Classifier

Analyzes table content and structure to determine the best extraction method.
Uses PyMuPDF pre-scan to get raw text for classification before deciding extractor.
"""

import fitz  # PyMuPDF


def classify_table(table, pdf_path):
    """
    Classify a table to determine the appropriate extractor.

    Uses a two-step approach:
    1. Pre-scan with PyMuPDF to get raw text from bbox
    2. Analyze content to determine best extractor

    Args:
        table: Docling table object
        pdf_path: Path to the PDF file

    Returns:
        tuple: (table_type, confidence, reason)
    """
    # Get bounding box info
    if not table.prov:
        return ("skip", 0.0, "No provenance info")

    bbox = table.prov[0].bbox
    page_no = table.prov[0].page_no

    # Validate bbox
    if not bbox or bbox.l >= bbox.r or bbox.b >= bbox.t:
        return ("skip", 0.0, "Invalid bounding box")

    # === STEP 1: Pre-scan with PyMuPDF ===
    raw_text = _get_raw_text_from_bbox(pdf_path, page_no, bbox)

    # Handle no raw text scenarios
    if not raw_text or len(raw_text.strip()) < 10:
        # Check if TableFormer got something
        current_cells = len(table.data.table_cells) if hasattr(table.data, 'table_cells') else 0

        if current_cells > 0:
            return ("tableformer_ok", 0.5, "No raw text, using TableFormer result")
        else:
            return ("skip", 0.0, "No content found in bbox")

    # === STEP 2: Classify based on raw text content ===
    raw_lower = raw_text.lower()

    # Get TableFormer extraction info for comparison
    current_cells = len(table.data.table_cells) if hasattr(table.data, 'table_cells') else 0
    cell_texts = []
    if hasattr(table.data, 'table_cells'):
        cell_texts = [cell.text.strip() for cell in table.data.table_cells if hasattr(cell, 'text')]

    extracted_chars = sum(len(t) for t in cell_texts)
    expected_chars = len(raw_text.strip())
    ratio = extracted_chars / expected_chars if expected_chars > 0 else 0

    # === Classification Rules (in priority order) ===

    # Rule 1: Specific table types by content keywords
    if _is_costos_horarios(raw_lower):
        return ("costos_horarios", 0.9, "Detected hourly costs table")

    if _is_demanda_generacion(raw_lower):
        return ("demanda_generacion", 0.9, "Detected demand/generation table")

    if _is_hidroelectricas(raw_lower):
        return ("hidroelectricas", 0.85, "Detected hydroelectric table")

    # Rule 2: TableFormer did a good job (high extraction ratio)
    if ratio > 0.7 and current_cells > 10:
        return ("tableformer_ok", 0.8, f"Good extraction ({ratio:.0%}, {current_cells} cells)")

    # Rule 3: TableFormer partially worked
    if ratio > 0.5 and current_cells > 5:
        return ("tableformer_ok", 0.6, f"Acceptable extraction ({ratio:.0%})")

    # Rule 4: Poor extraction - needs re-extract
    if ratio < 0.3 and expected_chars > 100:
        return ("sin_lineas_generico", 0.8, f"Poor extraction ({ratio:.0%}), re-extracting")

    # Rule 5: Very few cells for lots of content
    if current_cells <= 5 and expected_chars > 500:
        return ("sin_lineas_generico", 0.85, f"Only {current_cells} cells for {expected_chars} chars")

    # Rule 6: Medium extraction - use TableFormer if reasonable
    if current_cells > 0:
        return ("tableformer_ok", 0.5, f"Using TableFormer ({current_cells} cells)")

    # Default: generic PyMuPDF extraction
    return ("default", 0.5, "Default extraction")


def _get_raw_text_from_bbox(pdf_path, page_no, bbox):
    """
    Extract raw text from PDF bounding box using PyMuPDF.

    Args:
        pdf_path: Path to PDF file
        page_no: Page number (1-indexed)
        bbox: Bounding box object with l, t, r, b

    Returns:
        str: Raw text content or empty string
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_no - 1]  # 0-indexed
        page_height = page.rect.height

        # Convert bbox to PyMuPDF coordinates (origin top-left)
        rect = fitz.Rect(
            bbox.l,
            page_height - bbox.t,
            bbox.r,
            page_height - bbox.b
        )

        text = page.get_text("text", clip=rect)
        doc.close()

        return text.strip()
    except Exception as e:
        return ""


def _is_costos_horarios(text):
    """
    Check if this is an hourly costs table (1-24 hours format).

    These tables typically contain:
    - Costos Operación, Costos Totales, Costo Marginal
    - Pérdidas, Demanda Total, Generación Total
    - 24 hour columns
    """
    keywords = [
        "costos operación", "costos totales", "costo marginal",
        "pérdidas", "demanda total", "generación total",
        "programación diaria", "coordinador eléctrico"
    ]

    matches = sum(1 for kw in keywords if kw in text)
    return matches >= 2


def _is_demanda_generacion(text):
    """Check if this is a demand/generation table."""
    keywords = ["demanda", "generación", "consumo", "mwh", "gwh"]
    matches = sum(1 for kw in keywords if kw in text)
    return matches >= 3


def _is_hidroelectricas(text):
    """Check if this is a hydroelectric plants table."""
    keywords = [
        "hidroeléctrica", "pasada", "embalse",
        "central", "potencia", "caudal"
    ]
    matches = sum(1 for kw in keywords if kw in text)
    return matches >= 2
