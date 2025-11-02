"""
Standard Color Scheme for Docling Visualizations
=================================================

This module defines the standard color scheme used across ALL chapter extractions
to ensure consistency in annotated PDFs.

Usage:
    from STANDARD_COLORS import DOCLING_COLORS

    color = DOCLING_COLORS.get(elem_type, (0.5, 0.5, 0.5))
    page.draw_rect(rect, color=color, width=1.5)
"""

# Standard color scheme (RGB 0-1 scale)
# Used by Chapters 1, 2, 3, and all future chapters
DOCLING_COLORS = {
    "text": (0, 0, 1),              # Blue
    "section_header": (1, 0, 0),    # Red
    "title": (1, 0, 0),             # Red
    "table": (0, 0.7, 0),           # Green
    "picture": (1, 0, 1),           # Magenta
    "formula": (1, 0.5, 0),         # Orange
    "list_item": (0, 0.7, 0.7),     # Cyan
    "caption": (0.5, 0.5, 0),       # Olive
    "page_header": (0.5, 0.5, 0.5), # Gray
    "page_footer": (0.5, 0.5, 0.5), # Gray
    "footnote": (0.7, 0.7, 0.7),    # Light gray
}

# Color legend for documentation
COLOR_LEGEND = """
Standard Docling Visualization Colors:
======================================
- Blue:          Text (body text, paragraphs)
- Red:           Section headers and titles
- Green:         Tables
- Magenta:       Pictures/images
- Orange:        Formulas/equations
- Cyan:          List items
- Olive:         Captions
- Gray:          Page headers/footers
- Light gray:    Footnotes
"""

if __name__ == "__main__":
    print(COLOR_LEGEND)
    print("\nColor values (RGB 0-1):")
    for elem_type, color in DOCLING_COLORS.items():
        print(f"  {elem_type:20s}: {color}")
