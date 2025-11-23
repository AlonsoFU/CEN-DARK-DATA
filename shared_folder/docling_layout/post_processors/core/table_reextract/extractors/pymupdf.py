"""
PyMuPDF Generic Extractor

Extracts table content using PyMuPDF text coordinates.
Best for tables without visible lines.
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract table content using PyMuPDF coordinate-based approach.

    Args:
        table: Docling table object with bounding box
        pdf_path: Path to source PDF

    Returns:
        dict: Simplified table structure with headers and rows
    """
    if not table.prov:
        return None

    bbox = table.prov[0].bbox
    page_no = table.prov[0].page_no

    try:
        doc = fitz.open(pdf_path)
        page = doc[page_no - 1]
        page_height = page.rect.height

        # Convert bbox to PyMuPDF coordinates
        rect = fitz.Rect(
            bbox.l,
            page_height - bbox.t,
            bbox.r,
            page_height - bbox.b
        )

        # Get text blocks with positions
        blocks = page.get_text("dict", clip=rect)["blocks"]

        # Extract text spans with positions
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

        # Sort by y (row), then x (column)
        text_items.sort(key=lambda item: (round(item["y"], 0), item["x"]))

        # Group into rows by y-coordinate
        rows = _group_into_rows(text_items, tolerance=3)

        if not rows:
            return None

        # Convert to simplified structure
        return _rows_to_table_structure(rows)

    except Exception as e:
        print(f"      PyMuPDF extraction error: {e}")
        return None


def _group_into_rows(text_items, tolerance=3):
    """Group text items into rows based on y-coordinate."""
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


def _rows_to_table_structure(rows):
    """Convert grouped rows to simplified table structure."""
    if not rows:
        return None

    # Process each row
    processed_rows = []
    for row in rows:
        texts = [item["text"] for item in row]
        processed_rows.append(texts)

    # Determine headers (first row or rows with all text)
    # For now, assume first row is headers if it has fewer numbers
    headers = processed_rows[0] if processed_rows else []
    data_rows = processed_rows[1:] if len(processed_rows) > 1 else []

    # Normalize column count
    max_cols = max(len(row) for row in processed_rows) if processed_rows else 0

    # Pad rows to same length
    normalized_rows = []
    for row in data_rows:
        padded = row + [""] * (max_cols - len(row))
        normalized_rows.append(padded[:max_cols])

    # Pad headers too
    headers = headers + [""] * (max_cols - len(headers))
    headers = headers[:max_cols]

    return {
        "headers": headers,
        "rows": normalized_rows,
        "num_rows": len(normalized_rows),
        "num_cols": max_cols,
        "extractor": "pymupdf"
    }
