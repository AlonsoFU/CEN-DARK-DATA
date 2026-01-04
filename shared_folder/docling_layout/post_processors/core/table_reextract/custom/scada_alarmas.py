"""
SCADA Alarmas Extractor

Extractor for SCADA alarm/event log tables:
History Logging Time | Station | Object Text | State Text

These tables show SCADA system events with timestamps.
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract SCADA alarmas table.

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
        data = _process_scada_table(rows)

        if data:
            data["validation"] = validate(data)

        return data

    except Exception as e:
        print(f"      SCADA alarmas extraction error: {e}")
        return None


def validate(data):
    """Validate extracted SCADA alarmas table."""
    errors = []
    warnings = []

    # Expected 4 columns
    if data["num_cols"] != 4:
        warnings.append(f"Expected 4 cols, got {data['num_cols']}")

    # Check for datetime pattern
    datetime_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4}')
    datetime_count = 0
    for row in data.get("rows", []):
        if row and datetime_pattern.search(str(row[0])):
            datetime_count += 1

    if datetime_count == 0 and data["num_rows"] > 0:
        warnings.append("No datetime values found")

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


def _process_scada_table(rows):
    """Process rows for SCADA alarmas format."""
    if not rows:
        return None

    headers = ["History Logging Time", "Station", "Object Text", "State Text"]
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

    # Normalize to 4 columns
    normalized = []
    for row in data_rows:
        padded = row + [""] * (4 - len(row))
        normalized.append(padded[:4])

    return {
        "headers": headers,
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": 4,
        "extractor": "scada_alarmas"
    }


def _is_header_row(texts):
    """Check if row is a header."""
    combined = " ".join(texts).lower()
    header_keywords = ["history", "logging", "station", "object", "state"]
    matches = sum(1 for kw in header_keywords if kw in combined)
    return matches >= 2
