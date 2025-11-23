"""
Costos Horarios Extractor

Specialized extractor for hourly costs tables (24-hour format).
These tables have:
- Row labels (Costos Operación, Pérdidas, Demanda, etc.)
- 24 hour columns (1-24)
- Total column
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract hourly costs table with 24-hour column format.

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

        # Convert bbox
        rect = fitz.Rect(
            bbox.l,
            page_height - bbox.t,
            bbox.r,
            page_height - bbox.b
        )

        # Get text with positions
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

        # Sort by y, then x
        text_items.sort(key=lambda item: (round(item["y"], 0), item["x"]))

        # Group into rows
        rows = _group_into_rows(text_items, tolerance=3)

        # Process for hourly format
        return _process_hourly_table(rows)

    except Exception as e:
        print(f"      Costos horarios extraction error: {e}")
        return None


def _group_into_rows(text_items, tolerance=3):
    """Group text items into rows."""
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


def _process_hourly_table(rows):
    """Process rows for hourly table format."""
    if not rows:
        return None

    # Standard headers for 24-hour tables
    headers = ["Concepto"] + [str(i) for i in range(1, 25)] + ["Total"]

    data_rows = []

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header rows (title, date, hour numbers)
        if _is_header_row(texts):
            continue

        # Process data row
        processed = _process_data_row(texts)
        if processed:
            data_rows.append(processed)

    if not data_rows:
        return None

    # Normalize to 26 columns (concept + 24 hours + total)
    normalized_rows = []
    for row in data_rows:
        padded = row + [""] * (26 - len(row))
        normalized_rows.append(padded[:26])

    return {
        "headers": headers,
        "rows": normalized_rows,
        "num_rows": len(normalized_rows),
        "num_cols": 26,
        "extractor": "costos_horarios"
    }


def _is_header_row(texts):
    """Check if row is a header (title, date, hour numbers)."""
    combined = " ".join(texts).lower()

    # Title rows
    if "coordinador" in combined or "programación" in combined:
        return True

    # Date rows
    if any(month in combined for month in ["enero", "febrero", "marzo", "abril",
                                            "mayo", "junio", "julio", "agosto",
                                            "septiembre", "octubre", "noviembre", "diciembre"]):
        return True

    # Hour number row (all numbers 1-24)
    if all(t.isdigit() for t in texts) and len(texts) >= 20:
        return True

    return False


def _process_data_row(texts):
    """Process a data row, separating label from values."""
    if not texts:
        return None

    # Find where numeric data starts
    label_parts = []
    numeric_start = 0

    for i, t in enumerate(texts):
        # Check if it's a number (with optional decimals/thousands)
        clean = t.replace(" ", "").replace(",", "")
        if re.match(r'^[\d.]+$', clean):
            numeric_start = i
            break
        label_parts.append(t)

    if not label_parts:
        return None

    label = " ".join(label_parts)
    values = texts[numeric_start:]

    # Build row: label + values
    return [label] + values
