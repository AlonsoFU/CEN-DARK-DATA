"""
Enhanced Table Detector
Handles multi-line cells (cDoubleLinea) during PDF extraction
"""

from typing import List, Dict, Tuple, Optional


class EnhancedTableDetector:
    """
    Enhanced table detector that captures multi-line cells.

    Key improvements:
    1. Detects continuation rows (lines starting with /, lowercase, etc.)
    2. Merges continuation rows into parent cells
    3. More lenient column fitting for wrapped text
    """

    def __init__(self):
        self.continuation_indicators = ["/", "y ", "-", "("]
        self.min_continuation_indent = 5  # pixels

    def is_continuation_row(
        self,
        row: List[Dict],
        prev_row: Optional[List[Dict]] = None
    ) -> bool:
        """
        Determines if a row is a continuation of the previous row.

        Args:
            row: Current row items
            prev_row: Previous row items

        Returns:
            True if row is likely a continuation
        """
        if not row:
            return False

        row_text = " ".join(item["text"] for item in row).strip()

        # Empty row - NOT a continuation
        if not row_text:
            return False

        # Section header patterns (NOT continuations)
        # 1., a., b., c., d.1, d.2, etc.
        if len(row_text) <= 4 and "." in row_text:
            if row_text[0].isalnum():
                return False

        # Field labels (NOT continuations) - these are new rows
        field_keywords = [
            "fecha", "hora", "nombre", "tipo", "tensión", "segmento",
            "propietario", "rut", "representante", "dirección", "consumos",
            "demanda", "porcentaje", "calificación", "ubicación", "elemento"
        ]

        lower_text = row_text.lower()
        if any(keyword in lower_text for keyword in field_keywords):
            # This looks like a field label, not a continuation
            return False

        # Now check for STRONG continuation indicators

        # Starts with "/" - technical ID continuation
        if row_text.startswith("/"):
            return True

        # Starts with "y " followed by technical looking text
        if row_text.startswith("y ") and len(row_text) > 10:
            return True

        # Very short with only special chars (like "/", "-")
        if len(row_text) < 5 and row_text[0] in ["(", "/", "-"]:
            return True

        # Starts with lowercase and is short (< 30 chars) - likely fragment
        if row_text[0].islower() and len(row_text) < 30:
            return True

        return False

    def merge_continuation_rows(
        self,
        rows: List[List[Dict]],
        start_idx: int,
        end_idx: int
    ) -> Tuple[List[List[Dict]], int]:
        """
        Merges continuation rows into their parent rows.

        Args:
            rows: All rows from page
            start_idx: Start of table
            end_idx: End of table

        Returns:
            (merged_rows, new_end_idx)
        """
        table_rows = rows[start_idx:end_idx]
        merged = []
        i = 0

        while i < len(table_rows):
            current_row = table_rows[i].copy()

            # Look ahead for continuation rows
            j = i + 1
            while j < len(table_rows):
                next_row = table_rows[j]

                if self.is_continuation_row(next_row, current_row):
                    # Merge next_row into current_row
                    # Add continuation items to current row
                    current_row.extend(next_row)
                    j += 1
                else:
                    # Not a continuation, stop
                    break

            merged.append(current_row)
            i = j if j > i + 1 else i + 1

        # Check if there are continuation rows after end_idx
        new_end_idx = end_idx
        if end_idx < len(rows):
            while new_end_idx < len(rows):
                if merged and self.is_continuation_row(rows[new_end_idx], merged[-1]):
                    # Extend last merged row
                    merged[-1].extend(rows[new_end_idx])
                    new_end_idx += 1
                else:
                    break

        return merged, new_end_idx

    def detect_table_with_continuations(
        self,
        rows: List[List[Dict]],
        start_idx: int,
        columns: List[float],
        base_detector_func
    ) -> Tuple[bool, Optional[Dict], int]:
        """
        Enhanced table detection that includes continuation rows.

        Args:
            rows: All rows from page
            start_idx: Starting index
            columns: Detected column positions
            base_detector_func: Original table detection function

        Returns:
            (is_table, table_data, end_idx)
        """
        # First, use base detector
        is_table, base_data, end_idx = base_detector_func(rows, start_idx, columns)

        if not is_table:
            return False, None, start_idx + 1

        # Now enhance by merging continuation rows
        merged_rows, new_end_idx = self.merge_continuation_rows(
            rows, start_idx, end_idx
        )

        # Rebuild table data with merged rows
        enhanced_data = self._build_enhanced_table_data(merged_rows, columns)

        return True, enhanced_data, new_end_idx

    def _build_enhanced_table_data(
        self,
        rows: List[List[Dict]],
        columns: List[float]
    ) -> Dict:
        """
        Builds table data from rows with merged continuations.

        Args:
            rows: Merged rows (with continuations)
            columns: Column positions

        Returns:
            Table data dict
        """
        table_matrix = []

        for row in rows:
            row_data = [""] * len(columns)

            # Sort items by X position within row
            sorted_items = sorted(row, key=lambda x: x["x"])

            for item in sorted_items:
                # Assign to closest column
                closest_col = None
                min_dist = float('inf')

                for i, col_x in enumerate(columns):
                    dist = abs(item["x"] - col_x)
                    if dist < min_dist and dist <= 15:  # Slightly more lenient
                        min_dist = dist
                        closest_col = i

                if closest_col is not None:
                    if row_data[closest_col]:
                        row_data[closest_col] += " " + item["text"]
                    else:
                        row_data[closest_col] = item["text"]

            table_matrix.append(row_data)

        # Calculate bbox
        all_items = [item for row in rows for item in row]
        bbox = self._calculate_bbox(all_items)

        return {
            "columns": columns,
            "data": table_matrix,
            "bbox": bbox,
            "row_count": len(table_matrix),
            "col_count": len(columns)
        }

    def _calculate_bbox(self, items: List[Dict]) -> Tuple[float, float, float, float]:
        """Calculates bounding box from items."""
        if not items:
            return (0, 0, 0, 0)

        x0 = min(item["x"] for item in items)
        y0 = min(item["y"] for item in items)
        x1 = max(item.get("x_end", item["x"] + item.get("width", 10)) for item in items)
        y1 = max(item.get("y_end", item["y"] + 10) for item in items)

        return (x0, y0, x1, y1)


# Example usage integration patch
def patch_smart_classifier(classifier):
    """
    Patches an existing SmartContentClassifier to use enhanced detection.

    Usage:
        classifier = SmartContentClassifier(pdf_path)
        patch_smart_classifier(classifier)
        blocks = classifier.classify_page_content(page_num)
    """
    enhancer = EnhancedTableDetector()

    # Save original method
    original_detect_table = classifier._detect_table

    def enhanced_detect_table(rows, start_idx):
        """Enhanced wrapper for _detect_table."""
        # Get initial detection
        if start_idx + 2 >= len(rows):
            return False, None, start_idx + 1

        # Analyze sample to get columns
        sample_size = min(5, len(rows) - start_idx)
        sample_rows = rows[start_idx:start_idx + sample_size]

        columns = classifier._detect_columns_smart(sample_rows)
        if len(columns) < 2:
            return False, None, start_idx + 1

        # Check if it's a table (use original heuristics)
        consistency_score = classifier._measure_column_consistency(sample_rows, columns)
        has_mixed_content = classifier._has_mixed_content(sample_rows)
        has_table_markers = classifier._has_table_markers(sample_rows)

        is_table = (
            (consistency_score > 0.7) or
            (has_table_markers) or
            (consistency_score > 0.6 and has_mixed_content)
        )

        if not is_table:
            return False, None, start_idx + 1

        # Find initial end
        end_idx = start_idx + sample_size
        while end_idx < len(rows):
            if classifier._row_fits_columns(rows[end_idx], columns, tolerance=0.7):
                end_idx += 1
            else:
                # Check if it's a continuation row
                if enhancer.is_continuation_row(rows[end_idx], rows[end_idx - 1] if end_idx > 0 else None):
                    end_idx += 1  # Include continuation
                else:
                    # Check if next row is very close (< 5px gap)
                    # Could be header followed by data rows
                    if end_idx > 0 and end_idx < len(rows):
                        prev_row = rows[end_idx - 1]
                        curr_row = rows[end_idx]

                        if prev_row and curr_row:
                            prev_y_end = max(item.get("y_end", item["y"] + 10) for item in prev_row)
                            curr_y = min(item["y"] for item in curr_row)
                            gap = curr_y - prev_y_end

                            # If gap is very small (< 5px), might be continuation of same table
                            if gap < 5:
                                end_idx += 1
                                continue

                    break

        # Merge continuation rows
        merged_rows, new_end_idx = enhancer.merge_continuation_rows(
            rows, start_idx, end_idx
        )

        # Build enhanced table data
        table_data = enhancer._build_enhanced_table_data(merged_rows, columns)

        return True, table_data, new_end_idx

    # Replace method
    classifier._detect_table = enhanced_detect_table

    return classifier
