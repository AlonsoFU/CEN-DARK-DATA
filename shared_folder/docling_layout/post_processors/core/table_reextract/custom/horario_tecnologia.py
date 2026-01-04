"""
Horario Tecnología Extractor

Extractor for hourly generation tables by technology type:
Tecnología | Región | Comuna | Barra | 1 | 2 | ... | 24 | TOTAL

Types: TÉRMICAS, HIDRÁULICAS, EÓLICAS, CARGA DEL ALMACENAMIENTO,
       Hidroeléctricas de Pasada, etc.

These tables have 30 columns (4 location + 24 hours + Total + extra).
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract hourly technology generation table.

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

        # Detect technology type from title
        tech_type = _detect_technology_type(text_items)

        text_items.sort(key=lambda item: (round(item["y"], 0), item["x"]))
        rows = _group_into_rows(text_items, tolerance=3)
        data = _process_horario_tecnologia_table(rows, tech_type)

        if data:
            data["validation"] = validate(data)
            data["technology_type"] = tech_type

        return data

    except Exception as e:
        print(f"      Horario tecnología extraction error: {e}")
        return None


def validate(data):
    """Validate extracted horario tecnología table."""
    errors = []
    warnings = []

    # Expected ~30 columns (can vary)
    if data["num_cols"] < 26:
        warnings.append(f"Expected ~30 cols, got {data['num_cols']}")

    # Validate numeric values in hour columns
    non_numeric = 0
    for row in data.get("rows", []):
        # Check columns 5-28 (hours 1-24)
        for j in range(4, min(28, len(row))):
            if row[j] and not _is_numeric(row[j]):
                non_numeric += 1

    if non_numeric > 0:
        warnings.append(f"{non_numeric} non-numeric values in hour columns")

    # Validate row count
    if data["num_rows"] == 0:
        errors.append("No data rows extracted")

    confidence = 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.05)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "valid": len(errors) == 0,
        "confidence": round(confidence, 2),
        "errors": errors,
        "warnings": warnings
    }


def _detect_technology_type(text_items):
    """Detect technology type from title."""
    full_text = " ".join(item["text"] for item in text_items[:10]).upper()

    tech_types = {
        "TÉRMICAS": "termicas",
        "TERMICAS": "termicas",
        "HIDRÁULICAS": "hidraulicas",
        "HIDRAULICAS": "hidraulicas",
        "EÓLICAS": "eolicas",
        "EOLICAS": "eolicas",
        "SOLARES": "solares",
        "ALMACENAMIENTO": "almacenamiento",
        "CARGA": "carga_almacenamiento",
        "HIDROELÉCTRICAS DE PASADA": "pasada",
        "HIDROELECTRICAS DE PASADA": "pasada",
    }

    for key, value in tech_types.items():
        if key in full_text:
            return value

    return "general"


def _is_numeric(value):
    """Check if value is numeric."""
    if not value or value == "":
        return True
    clean = str(value).replace(" ", "").replace(",", ".").replace("-", "")
    try:
        float(clean)
        return True
    except ValueError:
        return False


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


def _process_horario_tecnologia_table(rows, tech_type):
    """Process rows for horario tecnología format."""
    if not rows:
        return None

    # Standard headers for technology hourly tables
    base_headers = ["Central", "Región", "Comuna", "Barra"]
    hour_headers = [str(i) for i in range(1, 25)]
    headers = base_headers + hour_headers + ["TOTAL"]

    data_rows = []
    detected_cols = 30

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header rows
        if _is_header_row(texts):
            continue

        if texts:
            # Process data row
            processed = _process_data_row(texts)
            if processed:
                data_rows.append(processed)
                detected_cols = max(detected_cols, len(processed))

    if not data_rows:
        return None

    # Adjust headers to detected columns
    if len(headers) < detected_cols:
        headers += [f"Extra{i}" for i in range(len(headers), detected_cols)]

    # Normalize rows
    normalized = []
    for row in data_rows:
        padded = row + [""] * (detected_cols - len(row))
        normalized.append(padded[:detected_cols])

    return {
        "headers": headers[:detected_cols],
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": detected_cols,
        "extractor": f"horario_tecnologia_{tech_type}"
    }


def _is_header_row(texts):
    """Check if row is a header."""
    combined = " ".join(texts).lower()
    header_keywords = ["región", "comuna", "barra", "total"]
    matches = sum(1 for kw in header_keywords if kw in combined)

    # Also check for hour numbers row
    if all(t.isdigit() for t in texts if t) and len(texts) >= 20:
        return True

    return matches >= 2


def _process_data_row(texts):
    """Process a data row, handling merged cells."""
    if not texts:
        return None

    # Clean numeric values
    processed = []
    for t in texts:
        clean = t.replace(" ", "") if re.match(r'^[\d\s.,\-]+$', t) else t
        processed.append(clean)

    return processed
