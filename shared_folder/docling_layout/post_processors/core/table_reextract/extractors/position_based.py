"""
Position-Based Table Extractor

Extracts table content by analyzing text positions to auto-detect columns.
Best for tables WITHOUT visible lines where text alignment defines structure.

Algorithm:
1. Extract all text items with X positions
2. Cluster X positions to find column starts
3. Calculate column boundaries as midpoints between clusters
4. Assign text to columns based on X position
"""

import fitz
from collections import defaultdict


def extract(table, pdf_path):
    """
    Extract table content using position-based column detection.

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

        # 1. Extract all text items with positions
        text_items = _get_text_items(page, rect)

        if not text_items:
            doc.close()
            return None

        # 2. Detect columns from X positions
        x_positions = [item["x"] for item in text_items]
        column_starts = _cluster_positions(x_positions, tolerance=8)

        if len(column_starts) < 2:
            doc.close()
            return None

        # 3. Calculate column boundaries
        boundaries = _calculate_boundaries(column_starts, bbox.l, bbox.r)
        num_cols = len(boundaries) - 1

        # 4. Group text by rows (Y position)
        rows_data = _group_into_rows(text_items, tolerance=5)

        # 5. Assign text to grid cells
        grid = []
        for row in rows_data:
            cells = [""] * num_cols
            for item in row:
                col = _find_column(item["x"], boundaries)
                if 0 <= col < num_cols:
                    if cells[col]:
                        cells[col] += " " + item["text"]
                    else:
                        cells[col] = item["text"]
            grid.append(cells)

        doc.close()

        # Remove completely empty rows
        grid = [row for row in grid if any(cell.strip() for cell in row)]

        if not grid:
            return None

        # First row is headers
        headers = grid[0] if grid else []
        data_rows = grid[1:] if len(grid) > 1 else []

        result = {
            "headers": headers,
            "rows": data_rows,
            "num_rows": len(data_rows),
            "num_cols": num_cols,
            "extractor": "position_based"
        }

        result["validation"] = validate(result)
        return result

    except Exception as e:
        print(f"      Position-based extraction error: {e}")
        return None


def validate(data):
    """Validate extracted table data."""
    errors = []
    warnings = []

    expected_cols = data["num_cols"]

    # Check headers
    if len(data["headers"]) != expected_cols:
        warnings.append(f"Headers: {len(data['headers'])} cols, expected {expected_cols}")

    # Check for empty data
    if data["num_rows"] == 0:
        errors.append("No data rows extracted")

    # Check row consistency
    empty_cells = 0
    total_cells = 0
    for row in data["rows"]:
        for cell in row:
            total_cells += 1
            if not cell.strip():
                empty_cells += 1

    if total_cells > 0:
        empty_ratio = empty_cells / total_cells
        if empty_ratio > 0.5:
            warnings.append(f"High empty cell ratio: {empty_ratio:.0%}")

    confidence = 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.1)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "valid": len(errors) == 0,
        "confidence": round(confidence, 2),
        "errors": errors,
        "warnings": warnings
    }


def _get_text_items(page, rect):
    """Extract text items with positions from page within rect."""
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
                            "y": span["bbox"][1]
                        })

    return text_items


def _cluster_positions(positions, tolerance=8):
    """
    Cluster nearby positions to find column starts.

    Args:
        positions: List of X positions
        tolerance: Maximum distance to cluster together

    Returns:
        list: Sorted list of column start positions (cluster averages)
    """
    if not positions:
        return []

    positions = sorted(positions)
    clusters = [[positions[0]]]

    for pos in positions[1:]:
        if pos - clusters[-1][-1] <= tolerance:
            clusters[-1].append(pos)
        else:
            clusters.append([pos])

    # Return average of each cluster
    return [sum(c) / len(c) for c in clusters]


def _calculate_boundaries(column_starts, left_edge, right_edge):
    """
    Calculate column boundaries as midpoints between column starts.

    Args:
        column_starts: List of detected column start X positions
        left_edge: Left edge of table bbox
        right_edge: Right edge of table bbox

    Returns:
        list: Column boundary positions
    """
    boundaries = [left_edge]

    for i in range(len(column_starts) - 1):
        mid = (column_starts[i] + column_starts[i + 1]) / 2
        boundaries.append(mid)

    boundaries.append(right_edge)
    return boundaries


def _find_column(x, boundaries):
    """Find which column an X position belongs to."""
    for i in range(len(boundaries) - 1):
        if boundaries[i] <= x < boundaries[i + 1]:
            return i
    return len(boundaries) - 2


def _group_into_rows(text_items, tolerance=5):
    """Group text items into rows based on Y position."""
    if not text_items:
        return []

    # Sort by Y then X
    text_items = sorted(text_items, key=lambda t: (round(t["y"], 0), t["x"]))

    rows = []
    current_y = None
    current_row = []

    for item in text_items:
        if current_y is None or abs(item["y"] - current_y) < tolerance:
            current_row.append(item)
            current_y = item["y"] if current_y is None else current_y
        else:
            if current_row:
                rows.append(current_row)
            current_row = [item]
            current_y = item["y"]

    if current_row:
        rows.append(current_row)

    return rows


def has_no_lines(page, rect):
    """
    Check if table bbox has no detectable lines.
    Used to determine if position-based extraction should be used.

    Args:
        page: PyMuPDF page object
        rect: fitz.Rect bounding box

    Returns:
        bool: True if no lines detected (should use position-based)
    """
    drawings = page.get_drawings()
    v_count = 0
    h_count = 0
    margin = 5

    for d in drawings:
        for item in d["items"]:
            if item[0] == "l":
                p1, p2 = item[1], item[2]

                x_in = (rect.x0 - margin <= p1.x <= rect.x1 + margin and
                        rect.x0 - margin <= p2.x <= rect.x1 + margin)
                y_in = (rect.y0 - margin <= p1.y <= rect.y1 + margin and
                        rect.y0 - margin <= p2.y <= rect.y1 + margin)

                if x_in and y_in:
                    if abs(p1.x - p2.x) < 2:
                        v_count += 1
                    if abs(p1.y - p2.y) < 2:
                        h_count += 1

    # Consider "no lines" if less than 3 vertical or 3 horizontal
    return v_count < 3 or h_count < 3
