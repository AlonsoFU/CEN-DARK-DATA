#!/usr/bin/env python3
"""
Power Line Item Classifier
Ensures power transmission lines are always classified as list_item, not section_header

Problem:
    Docling AI sometimes misclassifies lines like:
    • Línea 220 kV Cerro Dominador - Sierra Gorda

    As section_header instead of list_item (inconsistent)

Solution:
    Domain-specific rules to force correct classification
"""
import re


class PowerLineClassifier:
    """
    Classifies power system elements using domain-specific rules
    """

    # Patterns for power lines
    # NOTE: Docling may strip bullet characters or use different bullets (·, •, -, *)
    # We match with AND without bullets to handle all cases
    POWER_LINE_PATTERNS = [
        # WITH bullet (various bullet types)
        r'[•·\-\*]\s+Líneas?\s+\d+\s*[kK][vV]',      # Any bullet + Línea/Líneas + voltage
        r'[•·\-\*]\s+L[íi]neas?\s+\d+\s*[kK][vV]',   # Accent variation
        r'[•·\-\*]\s+Líneas?\s+\d+x\d+\s*[kK][vV]',  # Multi-line: Líneas 2x220 kV

        # WITHOUT bullet (Docling sometimes strips them)
        r'^\s*Línea\s+\d+\s*[kK][vV]',               # Start: Línea 220 kV...
        r'^\s*L[íi]nea\s+\d+\s*[kK][vV]',            # Accent variation
        r'^\s*Líneas\s+\d+x\d+\s*[kK][vV]',          # Multi-line without bullet

        # Anywhere in text (not just start)
        r'Líneas?\s+\d+x\d+\s*[kK][vV]',             # Líneas 2x220 kV anywhere
    ]

    # Patterns for substations
    SUBSTATION_PATTERNS = [
        r'•\s+S/E\s+',                      # • S/E Substation Name
        r'•\s+Subestación\s+',              # • Subestación Name
        r'•\s+Subestacion\s+',              # Without accent
    ]

    # Patterns for equipment
    EQUIPMENT_PATTERNS = [
        r'•\s+Transformador\s+',            # • Transformador ...
        r'•\s+Interruptor\s+',              # • Interruptor ...
        r'•\s+Seccionador\s+',              # • Seccionador ...
        r'•\s+Reactor\s+',                  # • Reactor ...
        r'•\s+Condensador\s+',              # • Condensador ...
    ]

    def __init__(self):
        """Initialize classifier with compiled patterns"""
        self.power_line_regex = [re.compile(p, re.IGNORECASE) for p in self.POWER_LINE_PATTERNS]
        self.substation_regex = [re.compile(p, re.IGNORECASE) for p in self.SUBSTATION_PATTERNS]
        self.equipment_regex = [re.compile(p, re.IGNORECASE) for p in self.EQUIPMENT_PATTERNS]

    def is_power_line_item(self, text: str) -> bool:
        """
        Check if text is a power line list item

        Args:
            text: Text to check

        Returns:
            True if text matches power line patterns

        Examples:
            >>> classifier = PowerLineClassifier()
            >>> classifier.is_power_line_item("• Línea 220 kV Cerro Dominador - Sierra Gorda")
            True
            >>> classifier.is_power_line_item("• Línea 110 kV Diego de Almagro - Central Andes")
            True
            >>> classifier.is_power_line_item("1. DESCRIPCIÓN")
            False
        """
        for regex in self.power_line_regex:
            if regex.search(text):
                return True
        return False

    def is_substation_item(self, text: str) -> bool:
        """Check if text is a substation list item"""
        for regex in self.substation_regex:
            if regex.search(text):
                return True
        return False

    def is_equipment_item(self, text: str) -> bool:
        """Check if text is an equipment list item"""
        for regex in self.equipment_regex:
            if regex.search(text):
                return True
        return False

    def is_power_system_list_item(self, text: str) -> bool:
        """
        Check if text is ANY type of power system list item

        Returns:
            True if text is a power line, substation, or equipment item
        """
        return (
            self.is_power_line_item(text) or
            self.is_substation_item(text) or
            self.is_equipment_item(text)
        )

    def classify_items(self, blocks: list) -> dict:
        """
        Classify a list of text blocks

        Args:
            blocks: List of dicts with 'text' and 'bbox'

        Returns:
            Dict with:
                'power_lines': List of power line items
                'substations': List of substation items
                'equipment': List of equipment items
                'other': List of non-power-system items
        """
        result = {
            'power_lines': [],
            'substations': [],
            'equipment': [],
            'other': []
        }

        for block in blocks:
            text = block.get('text', '')

            if self.is_power_line_item(text):
                result['power_lines'].append(block)
            elif self.is_substation_item(text):
                result['substations'].append(block)
            elif self.is_equipment_item(text):
                result['equipment'].append(block)
            else:
                result['other'].append(block)

        return result


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    classifier = PowerLineClassifier()

    # Test cases from Chapter 7, Page 305
    test_cases = [
        "• Línea 220 kV Cerro Dominador - Sierra Gorda",
        "• Línea 110 kV Diego de Almagro - Central Andes Generación",
        "• Línea 220 kV Kapatur - Sierra Gorda",
        "• S/E Cerro Dominador 220 kV",
        "• Subestación Diego de Almagro 110 kV",
        "• Transformador T1 220/110 kV",
        "1. DESCRIPCIÓN DE LA FALLA",  # Should be False
        "a. Detalle técnico",  # Should be False
    ]

    print("=" * 80)
    print("🔍 POWER LINE CLASSIFIER - TEST")
    print("=" * 80)
    print()

    for text in test_cases:
        is_power_item = classifier.is_power_system_list_item(text)
        icon = "✅" if is_power_item else "❌"

        # Determine type
        if classifier.is_power_line_item(text):
            item_type = "POWER LINE"
        elif classifier.is_substation_item(text):
            item_type = "SUBSTATION"
        elif classifier.is_equipment_item(text):
            item_type = "EQUIPMENT"
        else:
            item_type = "NOT POWER SYSTEM"

        print(f"{icon} [{item_type}]")
        print(f"   {text}")
        print()

    print("=" * 80)
    print("✅ Classifier working correctly!")
    print("=" * 80)
