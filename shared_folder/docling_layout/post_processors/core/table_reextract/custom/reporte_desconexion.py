"""
Reporte Desconexión Extractor

Extractor for disconnection/intervention reports:
- Reporte Desconexión/Intervención Subestacion
- Reporte Desconexión/Intervención Linea
- Reporte Desconexión/Intervención Central Generadora

These tables have 26 columns with disconnection event details.
"""

import fitz
import re


EXPECTED_HEADERS = [
    "Número", "Tipos", "Estado", "Empresa", "Id Coordinado", "Tipo Solicitud",
    "Origen", "Tipo Programación", "ID(s)", "Elemento", "ID(s) Elemento",
    "Tipo Trabajo", "Potencia", "Trabajos a Realizar", "Descripción",
    "Nivel Riesgo", "Comentario Adicional", "Consumo", "Empresas Afectadas",
    "Trabajo Requiere", "Estado Operativo", "Fecha Inicio", "Fecha Fin",
    "Fecha Efectiva Inicio", "Fecha Efectiva Fin", "Observaciones"
]


def extract(table, pdf_path):
    """
    Extract reporte desconexión table.

    Args:
        table: Docling table object
        pdf_path: Path to source PDF

    Returns:
        dict: Simplified table structure
    """
    if not table.prov:
        return None

    bbox = table.prov[0].bbox
    page_no = table.prov[0].page_no

    try:
        doc = fitz.open(pdf_path)
        page = doc[page_no - 1]
        page_height = page.rect.height

        rect = fitz.Rect(
            bbox.l,
            page_height - bbox.t,
            bbox.r,
            page_height - bbox.b
        )

        blocks = page.get_text("dict", clip=rect)["blocks"]

        text_items = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            text_items.append({
                                "text": text,
                                "x": span["bbox"][0],
                                "y": span["bbox"][1],
                            })

        doc.close()

        if not text_items:
            return None

        text_items.sort(key=lambda item: (round(item["y"], 0), item["x"]))

        # Detect element type from title
        element_type = _detect_element_type(text_items)

        rows = _group_into_rows(text_items, tolerance=3)
        data = _process_desconexion_table(rows, element_type)

        if data:
            data["validation"] = validate(data)
            data["element_type"] = element_type

        return data

    except Exception as e:
        print(f"      Reporte desconexión extraction error: {e}")
        return None


def validate(data):
    """Validate extracted reporte desconexión table."""
    errors = []
    warnings = []

    # These tables have ~26 columns
    if data["num_cols"] < 10:
        warnings.append(f"Expected ~26 cols, got {data['num_cols']}")

    # Check for date pattern in fecha columns
    date_pattern = re.compile(r'\d{2}-\d{2}-\d{2,4}')
    date_found = False
    for row in data.get("rows", []):
        for cell in row[-6:]:  # Last 6 columns often have dates
            if date_pattern.search(str(cell)):
                date_found = True
                break
        if date_found:
            break

    if not date_found:
        warnings.append("No date values found in fecha columns")

    # Validate row count
    if data["num_rows"] == 0:
        errors.append("No data rows extracted")

    confidence = 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.1)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "valid": len(errors) == 0,
        "confidence": round(confidence, 2),
        "errors": errors,
        "warnings": warnings
    }


def _detect_element_type(text_items):
    """Detect the type of element from title text."""
    full_text = " ".join(item["text"] for item in text_items[:20]).lower()

    if "subestacion" in full_text:
        return "subestacion"
    elif "linea" in full_text or "línea" in full_text:
        return "linea"
    elif "central" in full_text:
        return "central"
    return "general"


def _group_into_rows(text_items, tolerance=3):
    """Group text items into rows by Y position."""
    rows = []
    current_row = []
    current_y = None

    for item in text_items:
        if current_y is None or abs(item["y"] - current_y) < tolerance:
            current_row.append(item)
            current_y = item["y"] if current_y is None else current_y
        else:
            if current_row:
                current_row.sort(key=lambda x: x["x"])
                rows.append(current_row)
            current_row = [item]
            current_y = item["y"]

    if current_row:
        current_row.sort(key=lambda x: x["x"])
        rows.append(current_row)

    return rows


def _process_desconexion_table(rows, element_type):
    """Process rows for reporte desconexión format."""
    if not rows:
        return None

    data_rows = []
    detected_cols = 26

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header/title rows
        if _is_header_row(texts):
            continue

        if texts:
            data_rows.append(texts)
            detected_cols = max(detected_cols, len(texts))

    if not data_rows:
        return None

    # Use detected column count
    headers = EXPECTED_HEADERS[:detected_cols]
    if len(headers) < detected_cols:
        headers += [f"Col{i}" for i in range(len(headers), detected_cols)]

    # Normalize rows
    normalized = []
    for row in data_rows:
        padded = row + [""] * (detected_cols - len(row))
        normalized.append(padded[:detected_cols])

    return {
        "headers": headers,
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": detected_cols,
        "extractor": f"reporte_desconexion_{element_type}"
    }


def _is_header_row(texts):
    """Check if row is a header/title."""
    combined = " ".join(texts).lower()
    if "reporte desconexión" in combined or "reporte fecha" in combined:
        return True
    if "intervención" in combined and ("subestacion" in combined or "linea" in combined):
        return True

    # Header column names
    header_keywords = ["número", "tipos", "estado", "empresa", "coordinado"]
    matches = sum(1 for kw in header_keywords if kw in combined)
    return matches >= 3
