#!/usr/bin/env python3
"""
Page Number Detector
Detects page numbers and headers/footers that Docling's AI might miss

Common patterns Docling fails to detect:
- Page numbers: "Página 172 de 399", "Page 1 of 10"
- Simple numbers at top/bottom: "1", "23", "- 5 -"
- Headers/footers with page info
"""
import re


class EAFPageDetector:
    """
    Detects page numbers and headers/footers that Docling commonly misses

    Patterns:
    - "Página X de Y" (Spanish)
    - "Page X of Y" (English)
    - Simple numbers at top/bottom margins
    - Formatted numbers: "- 5 -", "[12]", "(23)"
    """

    def __init__(self):
        # Patterns for page numbers
        self.page_patterns = [
            # Spanish: "Página 172 de 399"
            re.compile(r'Página\s+(\d+)\s+de\s+(\d+)', re.IGNORECASE),

            # English: "Page 1 of 10"
            re.compile(r'Page\s+(\d+)\s+of\s+(\d+)', re.IGNORECASE),

            # Simple number with formatting: "- 5 -", "[12]", "(23)"
            re.compile(r'^[\[\(\-\s]*(\d+)[\]\)\-\s]*$'),

            # Just a number (but must be at margin)
            re.compile(r'^\s*(\d+)\s*$'),
        ]

    def is_page_number(self, text: str, bbox: dict, page_height: float) -> dict:
        """
        Check if text matches page number patterns

        Args:
            text: Text block to check
            bbox: Bounding box dict with x0, y0, x1, y1
            page_height: Total page height (for margin detection)

        Returns:
            dict with keys:
                - is_page_number: bool
                - pattern: str (which pattern matched)
                - position: str ('header' or 'footer')
        """
        text_clean = text.strip()

        # Must be short (page numbers are usually ≤ 30 chars)
        if len(text_clean) > 30:
            return {'is_page_number': False}

        # Check position - page numbers are at top or bottom margins
        # Top margin: y0 < 100
        # Bottom margin: y0 > page_height - 100
        y0 = bbox.get('y0', 0)

        is_header = y0 < 100
        is_footer = y0 > page_height - 100

        if not (is_header or is_footer):
            return {'is_page_number': False}

        # Check each pattern
        for i, pattern in enumerate(self.page_patterns):
            match = pattern.match(text_clean)
            if match:
                position = 'header' if is_header else 'footer'

                return {
                    'is_page_number': True,
                    'pattern': pattern.pattern,
                    'position': position,
                    'text': text_clean
                }

        return {'is_page_number': False}

    def should_create_cluster(self, text: str, bbox: dict, page_height: float) -> bool:
        """
        Additional heuristics to avoid false positives

        Args:
            text: Text content
            bbox: Bounding box dict with x0, y0, x1, y1
            page_height: Total page height

        Returns:
            bool: True if we should create a page number cluster
        """
        result = self.is_page_number(text, bbox, page_height)

        if not result['is_page_number']:
            return False

        # Additional checks
        # Page numbers are usually:
        # - Centered horizontally OR at right margin
        # - Not too wide (< 300 pts for simple numbers)

        x0 = bbox.get('x0', 0)
        x1 = bbox.get('x1', 0)
        width = x1 - x0

        # Simple numbers should be narrow
        text_clean = text.strip()
        if re.match(r'^\s*\d+\s*$', text_clean):
            if width > 100:  # Too wide for a simple number
                return False

        return True


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    detector = PageNumberDetector()

    test_cases = [
        ("Página 172 de 399", {'x0': 464.6, 'y0': 728.5, 'x1': 555.9, 'y1': 739.4}, 842),
        ("Page 1 of 10", {'x0': 250, 'y0': 800, 'x1': 300, 'y1': 810}, 842),
        ("- 23 -", {'x0': 290, 'y0': 30, 'x1': 310, 'y1': 40}, 842),
        ("172", {'x0': 500, 'y0': 820, 'x1': 520, 'y1': 830}, 842),
        ("This is a paragraph", {'x0': 100, 'y0': 400, 'x1': 500, 'y1': 420}, 842),
        ("Chapter 1", {'x0': 100, 'y0': 30, 'x1': 200, 'y1': 50}, 842),
    ]

    print("=" * 80)
    print("PAGE NUMBER DETECTOR - TEST CASES")
    print("=" * 80)

    for text, bbox, page_height in test_cases:
        result = detector.is_page_number(text, bbox, page_height)
        should_create = detector.should_create_cluster(text, bbox, page_height)

        if result['is_page_number']:
            print(f"\n✅ '{text}'")
            print(f"   Pattern: {result['pattern']}")
            print(f"   Position: {result['position']}")
            print(f"   Should create cluster: {should_create}")
        else:
            print(f"\n❌ '{text}' - Not a page number")

    print("\n" + "=" * 80)
