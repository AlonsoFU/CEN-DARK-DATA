"""
Indicador Compacto Extractor

Extractor for compact indicator tables with 2 columns:
Indicador | valores_en_una_celda

Types:
- Trayectoria de Cotas (reservoir levels)
- Inercia GVAs (system inertia)
- Reducción de Renovable Estimada
- Exportación Referencial SEN-SADI

Values are typically 24 numbers + summary in a single cell.
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract compact indicator table.

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

        # Detect indicator type
        indicator_type = _detect_indicator_type(text_items)

        text_items.sort(key=lambda item: (round(item["y"], 0), item["x"]))
        rows = _group_into_rows(text_items, tolerance=3)
        data = _process_indicador_table(rows, indicator_type)

        if data:
            data["validation"] = validate(data)
            data["indicator_type"] = indicator_type

        return data

    except Exception as e:
        print(f"      Indicador compacto extraction error: {e}")
        return None


def validate(data):
    """Validate extracted indicador compacto table."""
    errors = []
    warnings = []

    # Usually 2 columns, but can expand to 26 if we parse values
    if data["num_cols"] < 2:
        errors.append(f"Expected at least 2 cols, got {data['num_cols']}")

    # Check for numeric values
    numeric_count = 0
    for row in data.get("rows", []):
        for cell in row[1:]:  # Skip indicator name
            if _has_numeric(str(cell)):
                numeric_count += 1

    if numeric_count == 0 and data["num_rows"] > 0:
        warnings.append("No numeric values found")

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


def _detect_indicator_type(text_items):
    """Detect indicator type from text."""
    full_text = " ".join(item["text"] for item in text_items[:5]).lower()

    if "cotas" in full_text or "trayectoria" in full_text:
        return "cotas"
    elif "inercia" in full_text:
        return "inercia"
    elif "reducción" in full_text or "renovable" in full_text:
        return "reduccion_renovable"
    elif "exportación" in full_text or "sadi" in full_text:
        return "exportacion"

    return "general"


def _has_numeric(text):
    """Check if text contains numeric values."""
    return bool(re.search(r'\d', text))


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


def _process_indicador_table(rows, indicator_type):
    """Process rows for indicador compacto format."""
    if not rows:
        return None

    # Option 1: Keep as 2 columns (indicator | all values)
    # Option 2: Expand to 26 columns (indicator | 1-24 | Total/Promedio)

    # We'll expand to 26 columns for consistency
    headers = ["Indicador"] + [str(i) for i in range(1, 25)] + ["Total"]

    data_rows = []

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip empty rows
        if not texts or all(not t for t in texts):
            continue

        # Process row
        processed = _expand_indicator_row(texts, indicator_type)
        if processed:
            data_rows.append(processed)

    if not data_rows:
        return None

    # Normalize to 26 columns
    normalized = []
    for row in data_rows:
        padded = row + [""] * (26 - len(row))
        normalized.append(padded[:26])

    return {
        "headers": headers,
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": 26,
        "extractor": f"indicador_compacto_{indicator_type}"
    }


def _expand_indicator_row(texts, indicator_type):
    """Expand indicator row from 2 cols to 26 cols."""
    if not texts:
        return None

    # First text is usually the indicator name
    indicator_name = texts[0]

    # Rest is values (may be in one cell or multiple)
    values_text = " ".join(texts[1:])

    # Extract all numbers
    numbers = re.findall(r'[-\d.,]+', values_text)

    # Clean numbers
    cleaned = []
    for n in numbers:
        clean = n.replace(",", ".").replace(" ", "")
        cleaned.append(clean)

    # Build row: indicator + 24 hours + total/promedio
    row = [indicator_name]
    row.extend(cleaned[:25])  # Up to 25 values (24 hours + total)

    return row
