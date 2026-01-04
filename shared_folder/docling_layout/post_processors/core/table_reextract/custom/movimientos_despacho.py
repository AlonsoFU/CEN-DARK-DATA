"""
Movimientos Despacho Extractor

Extractor for dispatch movement tables with pattern:
Fecha | Hora Movi. | Central-Unidad | Configuración | Despacho | Estado EO |
Consignas | Consigna | Instrucción Cmg | Motivo | Zona Desacople | Condición |
Neomante | Centro de Control

These tables track power plant dispatch changes throughout the day.
"""

import fitz
import re


EXPECTED_HEADERS = [
    "Fecha", "Hora Movi.", "Central-Unidad", "Configuración", "Despacho",
    "Estado EO", "Consignas", "Consigna", "Instrucción Cmg", "Motivo",
    "Zona Desacople", "Condición", "Neomante", "Centro de"
]


def extract(table, pdf_path):
    """
    Extract movimientos despacho table.

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
                                "width": span["bbox"][2] - span["bbox"][0]
                            })

        doc.close()

        if not text_items:
            return None

        text_items.sort(key=lambda item: (round(item["y"], 0), item["x"]))
        rows = _group_into_rows(text_items, tolerance=4)
        data = _process_movimientos_table(rows)

        if data:
            data["validation"] = validate(data)

        return data

    except Exception as e:
        print(f"      Movimientos despacho extraction error: {e}")
        return None


def validate(data):
    """Validate extracted movimientos despacho table."""
    errors = []
    warnings = []

    # These tables have variable columns (9-20)
    if data["num_cols"] < 8:
        errors.append(f"Too few columns: {data['num_cols']}")

    # Check for time pattern in first column
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    time_count = 0
    for row in data.get("rows", []):
        if row and time_pattern.search(str(row[0])):
            time_count += 1

    if time_count == 0:
        warnings.append("No time values found in Hora column")

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


def _group_into_rows(text_items, tolerance=4):
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


def _process_movimientos_table(rows):
    """Process rows for movimientos despacho format."""
    if not rows:
        return None

    data_rows = []
    detected_cols = 14  # Default

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header rows
        if _is_header_row(texts):
            continue

        # Process data row
        if texts:
            data_rows.append(texts)
            detected_cols = max(detected_cols, len(texts))

    if not data_rows:
        return None

    # Normalize column count
    normalized = []
    for row in data_rows:
        padded = row + [""] * (detected_cols - len(row))
        normalized.append(padded[:detected_cols])

    # Build headers
    headers = EXPECTED_HEADERS[:detected_cols]
    if len(headers) < detected_cols:
        headers += [f"Col{i}" for i in range(len(headers), detected_cols)]

    return {
        "headers": headers,
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": detected_cols,
        "extractor": "movimientos_despacho"
    }


def _is_header_row(texts):
    """Check if row is a header."""
    combined = " ".join(texts).lower()
    header_keywords = ["hora movi", "central-unidad", "configuración",
                       "despacho", "estado eo", "consignas"]
    matches = sum(1 for kw in header_keywords if kw in combined)
    return matches >= 2
