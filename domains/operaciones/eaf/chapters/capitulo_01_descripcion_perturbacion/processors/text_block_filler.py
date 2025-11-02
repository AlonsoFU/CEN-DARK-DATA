"""
Text Block Filler
Detects text that was missed by the classifier and adds it as text/metadata blocks
"""

from typing import List, Tuple
from smart_content_classifier import ContentBlock, ContentType
import fitz


class TextBlockFiller:
    """
    Fills gaps by detecting text that wasn't classified.
    """

    def __init__(self, pdf_path: str):
        self.pdf_doc = fitz.open(pdf_path)

    def find_unclassified_text(
        self,
        page_num: int,
        existing_blocks: List[ContentBlock]
    ) -> List[ContentBlock]:
        """
        Finds text that wasn't covered by existing blocks.

        Args:
            page_num: Page number (1-indexed)
            existing_blocks: Already classified blocks

        Returns:
            List of new text blocks for uncovered text
        """
        page = self.pdf_doc[page_num - 1]

        # Get all text blocks from PDF
        text_dict = page.get_text("dict")
        all_text_items = []

        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        bbox = span["bbox"]
                        text = span["text"].strip()
                        if text:
                            all_text_items.append({
                                "bbox": bbox,
                                "text": text,
                                "size": span["size"]
                            })

        # Check which text items are NOT covered by existing blocks
        uncovered_items = []

        for item in all_text_items:
            item_bbox = item["bbox"]
            item_center_y = (item_bbox[1] + item_bbox[3]) / 2

            # Check if this item is covered by any existing block
            is_covered = False
            for block in existing_blocks:
                block_bbox = block.bbox
                # Check if item center is within block
                if (block_bbox[0] <= item_bbox[0] <= block_bbox[2] and
                    block_bbox[1] <= item_center_y <= block_bbox[3]):
                    is_covered = True
                    break

            if not is_covered:
                uncovered_items.append(item)

        # Group uncovered items into text blocks
        new_blocks = []

        if uncovered_items:
            # Sort by Y position
            uncovered_items.sort(key=lambda x: x["bbox"][1])

            # Group close items
            groups = []
            current_group = [uncovered_items[0]]

            for item in uncovered_items[1:]:
                prev_bottom = current_group[-1]["bbox"][3]
                curr_top = item["bbox"][1]

                # If close enough (within 20px), same group
                if curr_top - prev_bottom < 20:
                    current_group.append(item)
                else:
                    groups.append(current_group)
                    current_group = [item]

            if current_group:
                groups.append(current_group)

            # Create ContentBlock for each group
            for group in groups:
                # Calculate bbox for group
                x0 = min(item["bbox"][0] for item in group)
                y0 = min(item["bbox"][1] for item in group)
                x1 = max(item["bbox"][2] for item in group)
                y1 = max(item["bbox"][3] for item in group)

                bbox = (x0, y0, x1, y1)

                # Combine text
                text = " ".join(item["text"] for item in group)

                # Determine type intelligently
                text_lower = text.lower()

                # METADATA: Only page numbers and dates
                if any(keyword in text_lower for keyword in ["página", "de 399", "página 1"]):
                    block_type = ContentType.METADATA
                elif "fecha de emisión" in text_lower and len(text) < 50:
                    block_type = ContentType.METADATA
                # HEADING: Titles, subtitles, section names
                elif any(keyword in text_lower for keyword in ["estudio", "análisis", "falla", "eaf", "desconexión"]):
                    block_type = ContentType.HEADING
                elif len(text) < 150:  # Short text = likely heading
                    block_type = ContentType.HEADING
                # PARAGRAPH: Longer narrative text
                else:
                    block_type = ContentType.PARAGRAPH

                new_block = ContentBlock(
                    type=block_type,
                    content={"text": text},
                    bbox=bbox,
                    confidence=0.7,  # Lower confidence for filled blocks
                    page=page_num,
                    metadata={
                        "is_filled_block": True,
                        "item_count": len(group)
                    }
                )

                new_blocks.append(new_block)

        return new_blocks

    def fill_gaps(
        self,
        page_num: int,
        blocks: List[ContentBlock]
    ) -> List[ContentBlock]:
        """
        Adds missing text blocks to fill gaps.
        """
        new_blocks = self.find_unclassified_text(page_num, blocks)

        # Combine and sort by Y position
        all_blocks = blocks + new_blocks
        all_blocks.sort(key=lambda b: b.bbox[1])

        return all_blocks


# Patch function
def patch_classifier_with_filler(classifier, pdf_path: str):
    """
    Patches classifier to fill gaps with missing text.
    """
    filler = TextBlockFiller(pdf_path)

    original_classify = classifier.classify_page_content

    def classify_with_filling(page_num: int):
        blocks = original_classify(page_num)
        filled_blocks = filler.fill_gaps(page_num, blocks)
        return filled_blocks

    classifier.classify_page_content = classify_with_filling
    return classifier
