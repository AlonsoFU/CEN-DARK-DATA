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

    # Rule 1: Programación Diaria (COORDINADOR ELÉCTRICO NACIONAL)
    if _is_programacion_diaria(raw_lower):
        return ("programacion_diaria", 0.9, "Detected daily programming table")

    # Rule 2: Specific table types by content keywords
    if _is_costos_horarios(raw_lower):
        return ("costos_horarios", 0.9, "Detected hourly costs table")

    # Rule 3: Movimientos de Despacho
    if _is_movimientos_despacho(raw_lower):
        return ("movimientos_despacho", 0.9, "Detected dispatch movements table")

    # Rule 4: Registro Operación SEN
    if _is_registro_operacion_sen(raw_lower):
        return ("registro_operacion_sen", 0.85, "Detected SEN operation record")

    # Rule 5: Centrales Desvío
    if _is_centrales_desvio(raw_lower):
        return ("centrales_desvio", 0.85, "Detected generation deviation table")

    # Rule 6: Centrales Grandes (≥100 MW)
    if _is_centrales_grandes(raw_lower):
        return ("centrales_grandes", 0.85, "Detected large plants availability")

    # Rule 7: Reportes Desconexión
    if _is_reporte_desconexion(raw_lower):
        return ("reporte_desconexion", 0.85, "Detected disconnection report")

    # Rule 8: Horario Tecnología (TÉRMICAS, HIDRÁULICAS, etc.)
    if _is_horario_tecnologia(raw_lower):
        return ("horario_tecnologia", 0.85, "Detected hourly technology table")

    # Rule 9: Indicadores Compactos (Cotas, Inercia, etc.)
    if _is_indicador_compacto(raw_lower):
        return ("indicador_compacto", 0.8, "Detected compact indicator table")

    # Rule 10: Eventos Hora
    if _is_eventos_hora(raw_lower):
        return ("eventos_hora", 0.8, "Detected hourly events table")

    # Rule 11: SCADA Alarmas
    if _is_scada_alarmas(raw_lower):
        return ("scada_alarmas", 0.8, "Detected SCADA alarms table")

    # Rule 12: Infraestructura SEN
    if _is_infraestructura_sen(raw_lower):
        return ("infraestructura_sen", 0.75, "Detected SEN infrastructure table")

    # Legacy rules
    if _is_demanda_generacion(raw_lower):
        return ("demanda_generacion", 0.9, "Detected demand/generation table")

    if _is_hidroelectricas(raw_lower):
        return ("hidroelectricas", 0.85, "Detected hydroelectric table")

    # Check for detectable lines before TableFormer fallbacks
    has_lines, line_info = _check_for_lines(pdf_path, page_no, bbox)
    if has_lines:
        return ("line_based", 0.9, f"Grid detected ({line_info})")

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

    Note: "programación diaria" and "coordinador eléctrico" are now
    handled by _is_programacion_diaria()
    """
    keywords = [
        "costos operación", "costos totales", "costo marginal",
        "pérdidas", "demanda total", "generación total"
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


def _is_programacion_diaria(text):
    """
    Check if this is a daily programming table from COORDINADOR ELÉCTRICO.

    These tables contain:
    - COORDINADOR ELÉCTRICO NACIONAL header
    - Programación Diaria del Sistema Eléctrico Nacional
    - Date in format "día, dd de mes de año"
    """
    keywords = [
        "coordinador eléctrico nacional",
        "programación diaria",
        "sistema eléctrico nacional"
    ]

    # Check for main keywords
    matches = sum(1 for kw in keywords if kw in text)
    if matches >= 2:
        return True

    # Also check for date pattern with day names
    import re
    days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    has_day = any(day in text for day in days)
    has_date_pattern = bool(re.search(r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}', text))

    if has_day and has_date_pattern and "coordinador" in text:
        return True

    return False


def _estimate_columns(raw_text):
    """
    Estimate number of columns in a table based on raw text.

    For hourly tables, looks for patterns like:
    - Rows with many numbers (24 hours + total)
    - Consistent number of values per line
    """
    lines = raw_text.strip().split('\n')

    # Find lines with mostly numeric content
    col_counts = []
    for line in lines:
        # Split by whitespace and count tokens
        tokens = line.split()
        if len(tokens) >= 10:  # Likely a data row
            # Count numeric-like tokens
            numeric_count = sum(1 for t in tokens if _is_numeric_token(t))
            if numeric_count >= 10:
                col_counts.append(len(tokens))

    if col_counts:
        # Return median to avoid outliers
        col_counts.sort()
        return col_counts[len(col_counts) // 2]

    return 0


def _is_numeric_token(token):
    """Check if token is numeric (allowing decimals, thousands separators)."""
    clean = token.replace(" ", "").replace(",", "").replace(".", "").replace("-", "")
    return clean.isdigit()


# === NEW DETECTION FUNCTIONS ===

def _is_movimientos_despacho(text):
    """
    Check if this is a dispatch movements table.
    Pattern: fecha | Hora Movi. | Central-Unidad | Configuración | Despacho | ...
    """
    keywords = [
        "hora movi", "central-unidad", "configuración",
        "despacho", "estado eo", "consignas", "neomante"
    ]
    matches = sum(1 for kw in keywords if kw in text)
    return matches >= 3


def _is_registro_operacion_sen(text):
    """
    Check if this is a SEN operation record table.
    """
    keywords = [
        "registro de operación",
        "sistema eléctrico nacional",
        "registro operación"
    ]
    return any(kw in text for kw in keywords)


def _is_centrales_desvio(text):
    """
    Check if this is a generation deviation table.
    Pattern: Central | Prog. | Real | Desv.% | Estado
    """
    keywords = ["prog.", "real", "desv", "estado"]
    matches = sum(1 for kw in keywords if kw in text)

    # Must also have plant names or "central" keyword
    has_central = "central" in text

    return matches >= 3 and has_central


def _is_centrales_grandes(text):
    """
    Check if this is a large plants (≥100 MW) availability table.
    """
    keywords = ["100 mw", "≥100", ">=100", "disponibilidad"]
    matches = sum(1 for kw in keywords if kw in text)
    return matches >= 1 and "central" in text


def _is_reporte_desconexion(text):
    """
    Check if this is a disconnection/intervention report.
    """
    keywords = [
        "reporte desconexión",
        "reporte fecha",
        "intervención subestacion",
        "intervención linea",
        "intervención central"
    ]
    return any(kw in text for kw in keywords)


def _is_horario_tecnologia(text):
    """
    Check if this is an hourly technology generation table.
    Types: TÉRMICAS, HIDRÁULICAS, EÓLICAS, etc.
    """
    tech_keywords = [
        "térmicas", "termicas",
        "hidráulicas", "hidraulicas",
        "eólicas", "eolicas",
        "solares", "fotovoltaicas",
        "almacenamiento"
    ]
    location_keywords = ["región", "comuna", "barra"]

    has_tech = any(kw in text for kw in tech_keywords)
    has_location = any(kw in text for kw in location_keywords)

    return has_tech and has_location


def _is_indicador_compacto(text):
    """
    Check if this is a compact indicator table.
    Types: Trayectoria de Cotas, Inercia GVAs, etc.
    """
    keywords = [
        "trayectoria de cotas",
        "inercia gva",
        "reducción de renovable",
        "exportación referencial"
    ]
    return any(kw in text for kw in keywords)


def _is_eventos_hora(text):
    """
    Check if this is an hourly events table.
    Pattern: Hora | Centro de Control | Observación
    """
    keywords = ["centro de control", "observación", "hora"]
    matches = sum(1 for kw in keywords if kw in text)

    # Avoid matching other tables that have "hora"
    not_other = "movi" not in text and "despacho" not in text

    return matches >= 2 and not_other


def _is_scada_alarmas(text):
    """
    Check if this is a SCADA alarms table.
    Pattern: History Logging Time | Station | Object Text | State Text
    """
    keywords = [
        "history logging",
        "station",
        "object text",
        "state text",
        "operado",
        "alarma"
    ]
    matches = sum(1 for kw in keywords if kw in text)
    return matches >= 2


def _is_infraestructura_sen(text):
    """
    Check if this is a SEN infrastructure table.
    Types: COMUNICACIONES, REGULACIÓN DE TENSIÓN, INDISPONIBILIDAD SCADA
    """
    keywords = [
        "comunicaciones sen",
        "regulación de tensión",
        "indisponibilidad scada"
    ]
    return any(kw in text for kw in keywords)


def _check_for_lines(pdf_path, page_no, bbox):
    """
    Check if the table bbox contains enough lines for line-based extraction.

    Args:
        pdf_path: Path to PDF file
        page_no: Page number (1-indexed)
        bbox: Bounding box object with l, t, r, b

    Returns:
        tuple: (has_lines: bool, info_string: str)
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_no - 1]
        page_height = page.rect.height

        # Convert bbox to PyMuPDF coordinates
        rect = fitz.Rect(
            bbox.l,
            page_height - bbox.t,
            bbox.r,
            page_height - bbox.b
        )

        # Detect lines in bbox
        drawings = page.get_drawings()
        vertical_lines = []
        horizontal_lines = []
        margin = 5

        for d in drawings:
            for item in d["items"]:
                if item[0] == "l":  # Line
                    p1, p2 = item[1], item[2]

                    # Check if line is within bbox
                    x_in = (rect.x0 - margin <= p1.x <= rect.x1 + margin and
                            rect.x0 - margin <= p2.x <= rect.x1 + margin)
                    y_in = (rect.y0 - margin <= p1.y <= rect.y1 + margin and
                            rect.y0 - margin <= p2.y <= rect.y1 + margin)

                    if not (x_in and y_in):
                        continue

                    # Vertical line
                    if abs(p1.x - p2.x) < 2:
                        vertical_lines.append(p1.x)

                    # Horizontal line
                    if abs(p1.y - p2.y) < 2:
                        horizontal_lines.append(p1.y)

        doc.close()

        # Cluster lines
        v_unique = _cluster_positions(vertical_lines, tolerance=3)
        h_unique = _cluster_positions(horizontal_lines, tolerance=3)

        # Need at least 3 vertical and 3 horizontal lines for a valid grid
        if len(v_unique) >= 3 and len(h_unique) >= 3:
            cols = len(v_unique) - 1
            rows = len(h_unique) - 1
            return True, f"{cols}x{rows} grid"

        return False, ""

    except Exception:
        return False, ""


def _cluster_positions(positions, tolerance=3):
    """Cluster nearby positions into unique values."""
    if not positions:
        return []

    positions = sorted(positions)
    clusters = [[positions[0]]]

    for pos in positions[1:]:
        if pos - clusters[-1][-1] <= tolerance:
            clusters[-1].append(pos)
        else:
            clusters.append([pos])

    return [sum(c) / len(c) for c in clusters]
