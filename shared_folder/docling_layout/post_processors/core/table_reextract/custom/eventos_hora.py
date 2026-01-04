"""
Eventos Hora Extractor

Extractor for hourly event tables:
Hora | Centro de Control | Observación/Empresa/Instalación

These tables log events with timestamps from control centers.
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract eventos hora table.

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
        rows = _group_into_rows(text_items, tolerance=3)
        data = _process_eventos_table(rows)

        if data:
            data["validation"] = validate(data)

        return data

    except Exception as e:
        print(f"      Eventos hora extraction error: {e}")
        return None


def validate(data):
    """Validate extracted eventos hora table."""
    errors = []
    warnings = []

    # Expected 3-6 columns
    if data["num_cols"] < 2:
        errors.append(f"Expected at least 2 cols, got {data['num_cols']}")

    # Check for time pattern in Hora column
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    time_count = 0
    for row in data.get("rows", []):
        if row and time_pattern.search(str(row[0])):
            time_count += 1

    if time_count == 0 and data["num_rows"] > 0:
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


def _process_eventos_table(rows):
    """Process rows for eventos hora format."""
    if not rows:
        return None

    # Detect column count from first data row
    detected_cols = 3
    for row in rows:
        texts = [item["text"] for item in row]
        if not _is_header_row(texts) and texts:
            detected_cols = max(detected_cols, len(texts))
            break

    # Build headers based on detected columns
    base_headers = ["Hora", "Centro de Control", "Observación", "Empresa", "Instalación", "Detalle"]
    headers = base_headers[:detected_cols]
    if len(headers) < detected_cols:
        headers += [f"Col{i}" for i in range(len(headers), detected_cols)]

    data_rows = []

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header rows
        if _is_header_row(texts):
            continue

        if texts:
            data_rows.append(texts)

    if not data_rows:
        return None

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
        "extractor": "eventos_hora"
    }


def _is_header_row(texts):
    """Check if row is a header."""
    combined = " ".join(texts).lower()
    header_keywords = ["hora", "centro de control", "observación", "empresa"]
    matches = sum(1 for kw in header_keywords if kw in combined)
    return matches >= 2
