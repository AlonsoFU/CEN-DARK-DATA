#!/usr/bin/env python3
"""
Missing Title Detector
Detects chapter/section titles that Docling's AI might miss

Common patterns Docling fails to detect:
- Single digit/number titles: "6.", "7.", "a.", "b."
- Short titles without additional text
- Titles in unusual fonts/sizes
"""
import re


class EAFTitleDetector:
    """
    Detects titles that Docling's AI commonly misses

    Patterns:
    - Chapter numbers: "6.", "7.", "10."
    - Section letters: "a.", "b.", "c."
    - Subsection numbers: "6.1", "6.2.1"
    """

    def __init__(self):
        # Patterns for chapter/section titles
        self.title_patterns = [
            # Chapter numbers: "6.", "7.", "10." (optionally followed by title text)
            re.compile(r'^\s*(\d+)\.\s+.+'),       # "6. Normalización del servicio"
            re.compile(r'^\s*(\d+)\.\s*$'),        # "6." alone

            # Section letters: "a.", "b.", "c." (optionally followed by text)
            re.compile(r'^\s*([a-z])\.\s+.+', re.IGNORECASE),
            re.compile(r'^\s*([a-z])\.\s*$', re.IGNORECASE),

            # Subsections: "6.1", "6.2.1", etc. (optionally followed by text)
            re.compile(r'^\s*(\d+\.)+\d+\s+.+'),
            re.compile(r'^\s*(\d+\.)+\d+\s*$'),

            # Letter subsections: "a.1", "b.2", etc. (optionally followed by text)
            re.compile(r'^\s*[a-z]\.\d+\s+.+', re.IGNORECASE),
            re.compile(r'^\s*[a-z]\.\d+\s*$', re.IGNORECASE),

            # Roman numerals: "I.", "II.", "III." (optionally followed by text)
            re.compile(r'^\s*[IVXLCDM]+\.\s+.+', re.IGNORECASE),
            re.compile(r'^\s*[IVXLCDM]+\.\s*$', re.IGNORECASE),
        ]

        # Words that should NOT be detected as titles (table labels, etc.)
        self.excluded_words = [
            'total', 'subtotal', 'suma', 'promedio', 'average',
            'mínimo', 'máximo', 'min', 'max', 'nota', 'note',
            'fuente', 'source', 'observación', 'observation'
        ]

    def is_missing_title(self, text: str) -> dict:
        """
        Check if text matches patterns of titles that Docling commonly misses

        Args:
            text: Text block to check

        Returns:
            dict with keys:
                - is_title: bool
                - pattern: str (which pattern matched)
                - level: int (1=chapter, 2=section, 3=subsection, etc.)
        """
        text_clean = text.strip()

        # Check if text starts with an excluded word (case-insensitive)
        # Examples: "Total:", "Subtotal:", "Nota:", etc.
        first_word = text_clean.split()[0].lower().rstrip(':.,;') if text_clean.split() else ''
        if first_word in self.excluded_words:
            return {'is_title': False}

        # Titles can be longer if they include the full chapter/section name
        # "6." alone = 2 chars, "6. Normalización del servicio" = 29 chars
        # Allow up to 100 chars to capture full titles
        if len(text_clean) > 100:
            return {'is_title': False}

        # Check each pattern
        for i, pattern in enumerate(self.title_patterns):
            match = pattern.match(text_clean)
            if match:
                # Determine level based on pattern
                level = self._determine_level(text_clean)

                return {
                    'is_title': True,
                    'pattern': pattern.pattern,
                    'level': level,
                    'text': text_clean
                }

        return {'is_title': False}

    def _determine_level(self, text: str) -> int:
        """
        Determine hierarchical level of title

        Examples:
            "6." → level 1 (chapter)
            "a." → level 2 (section)
            "6.1" → level 2 (subsection)
            "6.2.1" → level 3 (sub-subsection)
        """
        text_clean = text.strip().rstrip('.')

        # Count dots to determine nesting
        dot_count = text_clean.count('.')

        # Single letter (a., b., c.)
        if re.match(r'^[a-z]$', text_clean, re.IGNORECASE):
            return 2  # Section level

        # Single digit (6., 7., 10.)
        if re.match(r'^\d+$', text_clean):
            return 1  # Chapter level

        # Nested numbers (6.1, 6.2.1, etc.)
        if '.' in text_clean:
            return dot_count + 1  # Each dot increases level

        # Roman numerals
        if re.match(r'^[IVXLCDM]+$', text_clean, re.IGNORECASE):
            return 1  # Usually chapter level

        return 1  # Default to chapter level

    def should_create_cluster(self, text: str, bbox: dict, page: int) -> bool:
        """
        Additional heuristics to avoid false positives

        Args:
            text: Text content
            bbox: Bounding box dict with x0, y0, x1, y1
            page: Page number

        Returns:
            bool: True if we should create a title cluster
        """
        result = self.is_missing_title(text)

        if not result['is_title']:
            return False

        # Check position heuristics
        # Titles are usually:
        # - Near left margin (x0 < 150)
        # - Not too small (width > 10)
        # - Width depends on whether title includes full text or just number

        x0 = bbox.get('x0', 0)
        width = bbox.get('x1', 0) - x0

        # Should be near left margin (applies to all titles)
        if x0 > 150:
            return False

        # Width validation depends on text length
        text_clean = text.strip()

        # Short titles like "6.", "a." should be small boxes
        if len(text_clean) <= 5:
            if width > 200:
                return False
        # Longer titles like "6. Normalización del servicio" can be wider
        else:
            if width > 500:  # Allow wider boxes for full titles
                return False

        return True


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    detector = MissingTitleDetector()

    test_cases = [
        "6.",
        "a.",
        "6.1",
        "6.2.1",
        "I.",
        "This is a long paragraph not a title",
        "12.",
        "a.1",
    ]

    print("=" * 80)
    print("MISSING TITLE DETECTOR - TEST CASES")
    print("=" * 80)

    for text in test_cases:
        result = detector.is_missing_title(text)
        if result['is_title']:
            print(f"\n✅ '{text}'")
            print(f"   Pattern: {result['pattern']}")
            print(f"   Level: {result['level']}")
        else:
            print(f"\n❌ '{text}' - Not a title")

    print("\n" + "=" * 80)
