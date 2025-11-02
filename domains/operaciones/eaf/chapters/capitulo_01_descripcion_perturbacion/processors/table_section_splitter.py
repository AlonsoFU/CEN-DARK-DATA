"""
Table Section Splitter
Splits large tables into separate sections based on headers (a., b., c., etc.)
"""

from typing import List, Dict, Tuple
from smart_content_classifier import ContentBlock, ContentType


class TableSectionSplitter:
    """
    Splits tables into logical sections based on section markers.

    Section markers: a., b., c., d., 1., 2., 3., etc.
    """

    def __init__(self):
        self.section_markers = []

    def is_section_header(self, row_data: List[str]) -> bool:
        """
        Checks if a row is a section header.

        Args:
            row_data: List of cell values in the row

        Returns:
            True if row is a section header
        """
        if not row_data:
            return False

        # Check ALL cells for section markers, not just first
        for cell in row_data:
            if not cell or not cell.strip():
                continue

            cell_clean = cell.strip()

            # Check for section markers
            # a., b., c., d.
            if len(cell_clean) <= 3 and cell_clean[-1:] == ".":
                if cell_clean[0].isalpha() and cell_clean[0].islower():
                    return True

            # Check for numbered sections that are short
            # But NOT data rows like "25/02/2025"
            if len(cell_clean) <= 3 and cell_clean[-1:] == ".":
                if cell_clean[0].isdigit():
                    # Only if it's single digit followed by period
                    if len(cell_clean) == 2:  # "1.", "2."
                        return True

            # Check for subsection patterns: d.1, d.2, etc.
            if len(cell_clean) <= 4 and "." in cell_clean:
                parts = cell_clean.split(".")
                if len(parts) == 2:
                    if parts[0].isalpha() and parts[1].isdigit():
                        return True

        return False

    def split_table_into_sections(
        self,
        table_block: ContentBlock
    ) -> List[ContentBlock]:
        """
        Splits a table ContentBlock into multiple section blocks.

        Args:
            table_block: Original table block

        Returns:
            List of table blocks (one per section)
        """
        if table_block.type != ContentType.TABLE:
            return [table_block]

        table_data = table_block.content.get("data", [])
        if not table_data:
            return [table_block]

        # Find section boundaries
        section_starts = []

        for i, row in enumerate(table_data):
            if self.is_section_header(row):
                section_starts.append(i)

        # If no sections found, return original
        if len(section_starts) == 0:
            return [table_block]

        # If only one section found, also check if we should split
        if len(section_starts) == 1:
            # If section is not at start, keep original
            if section_starts[0] > 2:  # Allow some header rows
                return [table_block]

        # Split into sections
        sections = []

        for i, start_idx in enumerate(section_starts):
            # Determine end index
            if i + 1 < len(section_starts):
                end_idx = section_starts[i + 1]
            else:
                end_idx = len(table_data)

            # Extract section rows
            section_rows = table_data[start_idx:end_idx]

            if len(section_rows) == 0:
                continue

            # Calculate bbox for this section
            # Use proportional split based on row count
            total_rows = len(table_data)
            bbox = list(table_block.bbox)

            # Calculate Y coordinates
            table_height = bbox[3] - bbox[1]
            row_height = table_height / total_rows

            section_y0 = bbox[1] + (start_idx * row_height)
            section_y1 = bbox[1] + (end_idx * row_height)

            section_bbox = (bbox[0], section_y0, bbox[2], section_y1)

            # Create new ContentBlock for this section
            section_content = {
                "columns": table_block.content.get("columns", []),
                "data": section_rows,
                "bbox": section_bbox,
                "row_count": len(section_rows),
                "col_count": table_block.content.get("col_count", 0)
            }

            # Extract section marker from first row
            section_marker = ""
            if section_rows and section_rows[0]:
                for cell in section_rows[0]:
                    if cell and cell.strip():
                        cell_clean = cell.strip()
                        # Check if it's a section marker
                        if len(cell_clean) <= 4 and ("." in cell_clean):
                            section_marker = cell_clean
                            break

            section_block = ContentBlock(
                type=ContentType.TABLE,
                content=section_content,
                bbox=section_bbox,
                confidence=table_block.confidence,
                page=table_block.page,
                metadata={
                    **table_block.metadata,
                    "section_index": i,
                    "section_marker": section_marker,
                    "is_split_section": True
                }
            )

            sections.append(section_block)

        return sections if sections else [table_block]

    def split_all_tables(
        self,
        blocks: List[ContentBlock]
    ) -> List[ContentBlock]:
        """
        Splits all table blocks in a list into sections.

        Args:
            blocks: List of ContentBlocks

        Returns:
            New list with tables split into sections
        """
        result = []

        for block in blocks:
            if block.type == ContentType.TABLE:
                # Split this table
                sections = self.split_table_into_sections(block)
                result.extend(sections)
            else:
                # Keep non-table blocks as-is
                result.append(block)

        return result


# Patch function to integrate with classifier
def patch_classifier_with_splitter(classifier):
    """
    Patches a SmartContentClassifier to split tables into sections.

    Usage:
        classifier = SmartContentClassifier(pdf_path)
        patch_smart_classifier(classifier)  # Enhanced multi-line
        patch_classifier_with_splitter(classifier)  # Split sections
    """
    splitter = TableSectionSplitter()

    # Save original method
    original_classify = classifier.classify_page_content

    def classify_with_splitting(page_num: int):
        """Wrapper that splits tables into sections."""
        # Get original blocks
        blocks = original_classify(page_num)

        # Split tables into sections
        split_blocks = splitter.split_all_tables(blocks)

        return split_blocks

    # Replace method
    classifier.classify_page_content = classify_with_splitting

    return classifier


# Test function
if __name__ == "__main__":
    from pathlib import Path
    import sys

    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF not found")
        exit(1)

    from smart_content_classifier import SmartContentClassifier
    from enhanced_table_detector import patch_smart_classifier

    print("🔪 TABLE SECTION SPLITTER TEST")
    print("=" * 70)

    # Without splitting
    print("\n1️⃣  WITHOUT SPLITTING:")
    classifier1 = SmartContentClassifier(str(pdf_path))
    patch_smart_classifier(classifier1)
    blocks1 = classifier1.classify_page_content(1)

    tables1 = [b for b in blocks1 if b.type == ContentType.TABLE]
    print(f"   Tables on page 1: {len(tables1)}")

    if tables1:
        print(f"   First table rows: {tables1[0].content['row_count']}")

    # With splitting
    print("\n2️⃣  WITH SPLITTING:")
    classifier2 = SmartContentClassifier(str(pdf_path))
    patch_smart_classifier(classifier2)
    patch_classifier_with_splitter(classifier2)
    blocks2 = classifier2.classify_page_content(1)

    tables2 = [b for b in blocks2 if b.type == ContentType.TABLE]
    print(f"   Tables on page 1: {len(tables2)}")

    for i, table in enumerate(tables2, 1):
        section_marker = table.metadata.get("section_marker", "")
        rows = table.content['row_count']
        print(f"   Table {i}: Section '{section_marker}' with {rows} rows")

    print("\n✅ Done!")
