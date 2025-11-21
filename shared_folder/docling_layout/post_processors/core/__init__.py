"""
Post-Processors Module

Post-processing fixes that run AFTER Docling completes extraction.
These operate at document level (can see all pages).

Available Post-Processors:
- enumerated_item_fix: Smart reclassification with 9 parts:
    1. Company names
    2. Bullet point sequences
    3. Summary captions
    4. Isolated power lines
    5. Enumerated items (a), b), c)
    6. Isolated list items (general)
    6.5. Title pattern recognition
    7. Cross-page continuations
    8. PAGE_HEADER to SECTION_HEADER
    9. Zona classification fix
- hierarchy_restructure: Restructures JSON by header hierarchy (parent-child nesting)
- metadata_date_extractor: Extracts emission date and failure date from headers

Note: Isolated list-item fix moved to monkey patch (page-level processing)
"""
from .enumerated_item_fix import apply_enumerated_item_fix_to_document
from .hierarchy_restructure import apply_hierarchy_restructure_to_document
from .metadata_date_extractor import apply_date_extraction_to_document

__all__ = [
    'apply_enumerated_item_fix_to_document',
    'apply_hierarchy_restructure_to_document',
    'apply_date_extraction_to_document',
]
