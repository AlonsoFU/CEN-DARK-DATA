"""
TableFormer Keeper

Keeps the original TableFormer extraction when it's good enough.
Converts to simplified structure for consistency.
"""


def keep(table, pdf_path):
    """
    Keep original TableFormer result but convert to simplified structure.

    Args:
        table: Docling table object
        pdf_path: Not used, kept for interface consistency

    Returns:
        dict: Simplified table structure
    """
    if not hasattr(table.data, 'table_cells'):
        return None

    cells = table.data.table_cells
    num_rows = table.data.num_rows if hasattr(table.data, 'num_rows') else 0
    num_cols = table.data.num_cols if hasattr(table.data, 'num_cols') else 0

    if not cells or num_rows == 0 or num_cols == 0:
        return None

    # Build grid from cells
    grid = [["" for _ in range(num_cols)] for _ in range(num_rows)]

    for cell in cells:
        row = cell.start_row_offset_idx if hasattr(cell, 'start_row_offset_idx') else 0
        col = cell.start_col_offset_idx if hasattr(cell, 'start_col_offset_idx') else 0
        text = cell.text.strip() if hasattr(cell, 'text') else ""

        if 0 <= row < num_rows and 0 <= col < num_cols:
            grid[row][col] = text

    # First row as headers
    headers = grid[0] if grid else []
    data_rows = grid[1:] if len(grid) > 1 else []

    return {
        "headers": headers,
        "rows": data_rows,
        "num_rows": len(data_rows),
        "num_cols": num_cols,
        "extractor": "tableformer"
    }
