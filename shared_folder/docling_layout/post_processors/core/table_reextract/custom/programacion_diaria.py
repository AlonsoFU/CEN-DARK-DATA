"""
Programación Diaria Extractor

Specialized extractor for daily programming tables from
COORDINADOR ELÉCTRICO NACIONAL.

These tables have:
- 26 columns: Concepto + hours 1-24 + Total
- Summary tables with date header
- Continuation tables by technology type
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract daily programming table with 24-hour column format.

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
        data = _process_hourly_table(rows)

        if data:
            # Add validation results
            data["validation"] = validate(data)

        return data

    except Exception as e:
        print(f"      Programación diaria extraction error: {e}")
        return None


def validate(data):
    """
    Validate extracted programación diaria table.

    Args:
        data: Extracted table data

    Returns:
        dict: Validation results with errors and warnings
    """
    errors = []
    warnings = []

    # Validate column count
    if data["num_cols"] != 26:
        errors.append(f"Expected 26 cols, got {data['num_cols']}")

    # Validate headers
    expected_headers = ["Concepto"] + [str(i) for i in range(1, 25)] + ["Total"]
    if data.get("headers") != expected_headers:
        warnings.append("Headers don't match expected pattern")

    # Validate numeric values in hour columns (1-24)
    non_numeric_count = 0
    for i, row in enumerate(data.get("rows", [])):
        if len(row) < 26:
            warnings.append(f"Row {i}: incomplete ({len(row)} cols)")
            continue

        for j in range(1, 25):  # columns 1-24 (indices 1-24)
            if j < len(row) and not _is_numeric(row[j]):
                non_numeric_count += 1

    if non_numeric_count > 0:
        warnings.append(f"{non_numeric_count} non-numeric values in hour columns")

    # Validate row count
    if data["num_rows"] == 0:
        errors.append("No data rows extracted")

    # Calculate confidence
    total_checks = 3  # cols, headers, rows
    passed = total_checks - len(errors)
    confidence = passed / total_checks

    return {
        "valid": len(errors) == 0,
        "confidence": round(confidence, 2),
        "errors": errors,
        "warnings": warnings
    }


def _is_numeric(value):
    """Check if value is numeric (allowing spaces, commas, dots)."""
    if not value or value == "":
        return True  # Empty is ok
    clean = str(value).replace(" ", "").replace(",", "").replace(".", "")
    return clean.isdigit() or clean == "" or clean == "-"


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
        "extractor": "programacion_diaria"
    }


def _is_header_row(texts):
    """Check if row is a header (title, date, hour numbers)."""
    combined = " ".join(texts).lower()

    # Title rows
    if "coordinador" in combined or "programación" in combined:
        return True

    # Date rows
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
              "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    if any(month in combined for month in months):
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
        if re.match(r'^[\d.\-]+$', clean):
            numeric_start = i
            break
        label_parts.append(t)

    if not label_parts:
        return None

    label = " ".join(label_parts)
    values = texts[numeric_start:]

    # Clean numeric values: remove spaces within numbers
    cleaned_values = []
    for v in values:
        # Remove spaces from numbers like "2 569" -> "2569"
        clean = v.replace(" ", "")
        cleaned_values.append(clean)

    # Build row: label + cleaned values
    return [label] + cleaned_values
