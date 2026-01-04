"""
Line-Based Table Extractor

Extracts table content using detected lines (drawings) from PyMuPDF.
Uses vertical and horizontal lines to determine cell boundaries.

Best for tables with visible gridlines where text-based detection fails.
"""

import fitz


def extract(table, pdf_path):
    """
    Extract table content using line-based grid detection.

    Args:
        table: Docling table object with bounding box
        pdf_path: Path to source PDF

    Returns:
        dict: Simplified table structure with headers and rows, or None if no lines found
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

        # 1. Detect lines in the table bbox
        v_lines, h_lines = _detect_lines(page, rect)

        # 2. Cluster lines to handle slight variations
        # Use smaller tolerance for horizontal lines since rows are closely spaced
        v_cols = _cluster_lines(v_lines, tolerance=3)
        h_rows = _cluster_lines(h_lines, tolerance=1)

        # 3. If not enough lines, return None (caller should use fallback)
        if len(v_cols) < 2 or len(h_rows) < 2:
            doc.close()
            return None

        # 4. Extract text items with positions
        text_items = _get_text_items(page, rect)

        if not text_items:
            doc.close()
            return None

        # 5. Create grid and assign text to cells
        num_cols = len(v_cols) - 1
        num_rows = len(h_rows) - 1
        grid = [[[] for _ in range(num_cols)] for _ in range(num_rows)]

        for item in text_items:
            col = _find_column(item["x"], v_cols)
            row = _find_row(item["y"], h_rows)
            if 0 <= row < num_rows and 0 <= col < num_cols:
                grid[row][col].append(item["text"])

        doc.close()

        # 6. Combine text in each cell and build final structure
        final_grid = []
        for row in grid:
            final_row = [" ".join(cell).strip() for cell in row]
            # Include all rows, even empty ones (preserve structure)
            final_grid.append(final_row)

        # Remove completely empty rows at end
        while final_grid and not any(cell.strip() for cell in final_grid[-1]):
            final_grid.pop()

        # Remove completely empty rows at start (but keep header row)
        while len(final_grid) > 1 and not any(cell.strip() for cell in final_grid[0]):
            final_grid.pop(0)

        if not final_grid:
            return None

        # First row with content is headers
        headers = final_grid[0] if final_grid else []
        data_rows = final_grid[1:] if len(final_grid) > 1 else []

        result = {
            "headers": headers,
            "rows": data_rows,
            "num_rows": len(data_rows),
            "num_cols": num_cols,
            "extractor": "line_based"
        }

        result["validation"] = validate(result)
        return result

    except Exception as e:
        print(f"      Line-based extraction error: {e}")
        return None


def validate(data):
    """Validate extracted table data."""
    errors = []
    warnings = []

    expected_cols = data["num_cols"]

    # Check headers
    if len(data["headers"]) != expected_cols:
        warnings.append(f"Headers: {len(data['headers'])} cols, expected {expected_cols}")

    # Check rows consistency
    for i, row in enumerate(data["rows"]):
        if len(row) != expected_cols:
            warnings.append(f"Row {i}: {len(row)} cols, expected {expected_cols}")

    # Check for empty data
    if data["num_rows"] == 0:
        errors.append("No data rows extracted")

    # Calculate confidence
    confidence = 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.05)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "valid": len(errors) == 0,
        "confidence": round(confidence, 2),
        "errors": errors,
        "warnings": warnings
    }


def _detect_lines(page, rect):
    """
    Detect vertical and horizontal lines within the given rectangle.

    Args:
        page: PyMuPDF page object
        rect: fitz.Rect bounding box

    Returns:
        tuple: (vertical_line_positions, horizontal_line_positions)
    """
    drawings = page.get_drawings()
    vertical_lines = []
    horizontal_lines = []

    margin = 5  # Allow small margin outside bbox

    for d in drawings:
        for item in d["items"]:
            if item[0] == "l":  # Line item
                p1, p2 = item[1], item[2]

                # Check if line is within or near the bbox
                x_in_range = (rect.x0 - margin <= p1.x <= rect.x1 + margin and
                              rect.x0 - margin <= p2.x <= rect.x1 + margin)
                y_in_range = (rect.y0 - margin <= p1.y <= rect.y1 + margin and
                              rect.y0 - margin <= p2.y <= rect.y1 + margin)

                if not (x_in_range and y_in_range):
                    continue

                # Vertical line: same X coordinate (within tolerance)
                if abs(p1.x - p2.x) < 2:
                    vertical_lines.append(p1.x)

                # Horizontal line: same Y coordinate (within tolerance)
                if abs(p1.y - p2.y) < 2:
                    horizontal_lines.append(p1.y)

    return vertical_lines, horizontal_lines


def _cluster_lines(positions, tolerance=3):
    """
    Cluster nearby line positions to handle slight variations.

    Args:
        positions: List of line positions
        tolerance: Maximum distance to consider lines as same

    Returns:
        list: Clustered and sorted unique positions
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

    # Return the average of each cluster
    return [sum(c) / len(c) for c in clusters]


def _get_text_items(page, rect):
    """
    Extract text items with positions from the page within the rect.

    Args:
        page: PyMuPDF page object
        rect: fitz.Rect bounding box

    Returns:
        list: Text items with text, x, y coordinates
    """
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


def _find_column(x, v_cols):
    """Find which column a text item belongs to based on X position."""
    for i in range(len(v_cols) - 1):
        if v_cols[i] <= x < v_cols[i + 1]:
            return i
    # If beyond last column, assign to last
    return len(v_cols) - 2 if len(v_cols) >= 2 else 0


def _find_row(y, h_rows, tolerance=3):
    """Find which row a text item belongs to based on Y position.

    Uses boundary-based assignment with tolerance for text that appears
    slightly before the top line of a row.

    Args:
        y: Y position of text
        h_rows: Sorted list of horizontal line positions
        tolerance: Allow text to be this many points above row top

    Returns:
        int: Row index (0-based)
    """
    if len(h_rows) < 2:
        return 0

    # Check each row boundary
    for i in range(len(h_rows) - 1):
        row_top = h_rows[i]
        row_bottom = h_rows[i + 1]

        # Text belongs to this row if it's between boundaries
        # Allow tolerance above the top boundary
        if row_top - tolerance <= y < row_bottom:
            return i

    # If beyond last row, assign to last
    return len(h_rows) - 2


def has_detectable_lines(page, rect, min_vertical=3, min_horizontal=3):
    """
    Quick check if a table has enough detectable lines for line-based extraction.

    Args:
        page: PyMuPDF page object
        rect: fitz.Rect bounding box
        min_vertical: Minimum vertical lines needed
        min_horizontal: Minimum horizontal lines needed

    Returns:
        bool: True if enough lines detected
    """
    v_lines, h_lines = _detect_lines(page, rect)
    v_cols = _cluster_lines(v_lines, tolerance=3)
    h_rows = _cluster_lines(h_lines, tolerance=3)
    return len(v_cols) >= min_vertical and len(h_rows) >= min_horizontal
