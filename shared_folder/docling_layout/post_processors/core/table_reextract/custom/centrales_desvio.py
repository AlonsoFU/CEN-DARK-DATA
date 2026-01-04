"""
Centrales Desvío Extractor

Extractor for generation deviation tables showing:
Central | Prog. | Real | Desv.% | Estado

These tables compare programmed vs actual generation for power plants.
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract centrales desvío table.

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
        data = _process_desvio_table(rows)

        if data:
            data["validation"] = validate(data)

        return data

    except Exception as e:
        print(f"      Centrales desvío extraction error: {e}")
        return None


def validate(data):
    """Validate extracted centrales desvío table."""
    errors = []
    warnings = []

    # Validate column count (5 or 10 for dual tables)
    if data["num_cols"] not in [5, 10]:
        warnings.append(f"Expected 5 or 10 cols, got {data['num_cols']}")

    # Validate headers
    expected = ["Central", "Prog.", "Real", "Desv.%", "Estado"]
    headers = data.get("headers", [])[:5]
    if headers != expected:
        warnings.append("Headers don't match expected pattern")

    # Validate numeric values in Prog., Real, Desv.% columns
    for i, row in enumerate(data.get("rows", [])):
        if len(row) >= 4:
            for j in [1, 2, 3]:  # Prog., Real, Desv.%
                if j < len(row) and row[j] and not _is_numeric(row[j]):
                    warnings.append(f"Row {i}: non-numeric in col {j}")
                    break

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


def _is_numeric(value):
    """Check if value is numeric."""
    if not value or value == "":
        return True
    clean = str(value).replace(" ", "").replace(",", ".").replace("%", "")
    try:
        float(clean)
        return True
    except ValueError:
        return clean == "-" or clean == ""


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


def _process_desvio_table(rows):
    """Process rows for desvío table format."""
    if not rows:
        return None

    headers = ["Central", "Prog.", "Real", "Desv.%", "Estado"]
    data_rows = []

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header rows
        if _is_header_row(texts):
            continue

        # Process data row
        processed = _parse_desvio_row(texts)
        if processed:
            data_rows.append(processed)

    if not data_rows:
        return None

    # Normalize to 5 columns
    normalized = []
    for row in data_rows:
        padded = row + [""] * (5 - len(row))
        normalized.append(padded[:5])

    return {
        "headers": headers,
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": 5,
        "extractor": "centrales_desvio"
    }


def _is_header_row(texts):
    """Check if row is a header."""
    combined = " ".join(texts).lower()
    header_keywords = ["central", "prog", "real", "desv", "estado"]
    matches = sum(1 for kw in header_keywords if kw in combined)
    return matches >= 3


def _parse_desvio_row(texts):
    """Parse a desvío data row."""
    if not texts:
        return None

    # Combine all text
    combined = " ".join(texts)

    # Pattern: Central name, numbers, estado
    # Example: "NEWEN-2 50.0 49.8 -0.4% OK"

    # Find estado at the end
    estado_match = re.search(r'(OK|FALLA|PARADA|N/A|-)$', combined, re.IGNORECASE)
    if estado_match:
        estado = estado_match.group(1)
        rest = combined[:estado_match.start()].strip()
    else:
        estado = ""
        rest = combined

    # Find numeric values
    numbers = re.findall(r'[-\d.,]+%?', rest)

    if len(numbers) >= 3:
        # Last 3 numbers are Prog, Real, Desv%
        prog = numbers[-3]
        real = numbers[-2]
        desv = numbers[-1]

        # Everything before is the central name
        central = rest
        for n in numbers[-3:]:
            central = central.replace(n, "", 1)
        central = central.strip()

        return [central, prog, real, desv, estado]

    return None
