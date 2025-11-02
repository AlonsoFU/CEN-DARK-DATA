"""
Post-Processors Module

Post-processing fixes that run AFTER Docling completes extraction.
These operate at document level (can see all pages).

Available Post-Processors:
- zona_fix: Fixes "Zona ... - Área ..." classification

Note: Isolated list-item fix moved to monkey patch (page-level processing)
"""
from .zona_fix import apply_zona_fix_to_document

__all__ = [
    'apply_zona_fix_to_document',
]
