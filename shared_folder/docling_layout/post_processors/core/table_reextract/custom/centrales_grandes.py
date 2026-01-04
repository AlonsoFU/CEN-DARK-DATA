"""
Centrales Grandes Extractor

Extractor for large power plant availability tables:
CENTRAL (≥100 MW) | Disponibilidad (%) | Observaciones

Simple 3-column tables showing availability status of major plants.
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract centrales grandes (≥100 MW) availability table.

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
        data = _process_centrales_grandes_table(rows)

        if data:
            data["validation"] = validate(data)

        return data

    except Exception as e:
        print(f"      Centrales grandes extraction error: {e}")
        return None


def validate(data):
    """Validate extracted centrales grandes table."""
    errors = []
    warnings = []

    # Expected 3 columns
    if data["num_cols"] != 3:
        warnings.append(f"Expected 3 cols, got {data['num_cols']}")

    # Check for percentage values in disponibilidad column
    pct_count = 0
    for row in data.get("rows", []):
        if len(row) >= 2:
            disp = str(row[1])
            if re.search(r'\d+\.?\d*%?', disp):
                pct_count += 1

    if pct_count == 0 and data["num_rows"] > 0:
        warnings.append("No percentage values found in Disponibilidad column")

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


def _process_centrales_grandes_table(rows):
    """Process rows for centrales grandes format."""
    if not rows:
        return None

    headers = ["CENTRAL (≥100 MW)", "Disponibilidad (%)", "Observaciones"]
    data_rows = []

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header rows
        if _is_header_row(texts):
            continue

        # Process data row
        processed = _parse_central_row(texts)
        if processed:
            data_rows.append(processed)

    if not data_rows:
        return None

    # Normalize to 3 columns
    normalized = []
    for row in data_rows:
        padded = row + [""] * (3 - len(row))
        normalized.append(padded[:3])

    return {
        "headers": headers,
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": 3,
        "extractor": "centrales_grandes"
    }


def _is_header_row(texts):
    """Check if row is a header."""
    combined = " ".join(texts).lower()
    return "central" in combined and ("100" in combined or "disponibilidad" in combined)


def _parse_central_row(texts):
    """Parse a centrales grandes data row."""
    if not texts:
        return None

    # Combine all text
    combined = " ".join(texts)

    # Pattern: Central name, percentage, observaciones
    # Find percentage
    pct_match = re.search(r'(\d+\.?\d*)\s*%?', combined)
    if pct_match:
        pct_value = pct_match.group(1)
        pct_pos = pct_match.start()

        # Everything before is central name
        central = combined[:pct_pos].strip()
        # Everything after is observaciones
        obs = combined[pct_match.end():].strip()

        return [central, pct_value, obs]

    # If no percentage found, split by position
    if len(texts) >= 2:
        return [texts[0], texts[1] if len(texts) > 1 else "", " ".join(texts[2:]) if len(texts) > 2 else ""]

    return None
