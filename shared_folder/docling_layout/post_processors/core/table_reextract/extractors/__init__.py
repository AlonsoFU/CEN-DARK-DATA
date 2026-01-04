"""
Table Extractors

Different extraction methods for different table types.

- line_based: For tables WITH visible grid lines
- position_based: For tables WITHOUT lines (auto-detects columns from text positions)
- pymupdf: Generic fallback
- tableformer: Keep original Docling/TableFormer result
"""

from . import pymupdf
from . import tableformer
from . import line_based
from . import position_based

__all__ = ['pymupdf', 'tableformer', 'line_based', 'position_based']
