# Standard Color Scheme for Docling Visualizations

## Overview

All chapter extraction scripts use a **consistent standard color scheme** to ensure uniformity across all annotated PDFs.

## Standard Colors

| Element Type    | Color      | RGB (0-1)            | Hex     |
|----------------|------------|---------------------|---------|
| text           | Blue       | (0, 0, 1)           | #0000FF |
| section_header | Red        | (1, 0, 0)           | #FF0000 |
| title          | Red        | (1, 0, 0)           | #FF0000 |
| table          | Green      | (0, 0.7, 0)         | #00B300 |
| picture        | Magenta    | (1, 0, 1)           | #FF00FF |
| formula        | Orange     | (1, 0.5, 0)         | #FF8000 |
| list_item      | Cyan       | (0, 0.7, 0.7)       | #00B3B3 |
| caption        | Olive      | (0.5, 0.5, 0)       | #808000 |
| page_header    | Gray       | (0.5, 0.5, 0.5)     | #808080 |
| page_footer    | Gray       | (0.5, 0.5, 0.5)     | #808080 |
| footnote       | Light Gray | (0.7, 0.7, 0.7)     | #B3B3B3 |

## Usage

### In Python Scripts

```python
# Import the standard color scheme
from STANDARD_COLORS import DOCLING_COLORS as COLORS

# Use colors in visualization
elem_type = elem['type']
color = COLORS.get(elem_type, (0.5, 0.5, 0.5))  # Default gray for unknown types
page.draw_rect(rect, color=color, width=1.5)
```

### Consistency Rules

1. **ALL new extraction scripts** must import `STANDARD_COLORS.py`
2. **DO NOT hardcode colors** in individual scripts
3. **DO NOT create custom color schemes** without updating `STANDARD_COLORS.py`
4. If you need to change colors, update `STANDARD_COLORS.py` so ALL chapters update automatically

## Files Using Standard Colors

- ✅ Chapter 1: `capitulo_01/scripts/visualize_cap1_only.py`
- ✅ Chapter 2: (uses same color scheme)
- ✅ Chapter 3: `extract_chapter03_CORRECTED.py`
- ✅ UNIVERSAL script: `UNIVERSAL_extract_any_chapter.py`
- ✅ All future chapters should import from `STANDARD_COLORS.py`

## Why Consistent Colors Matter

1. **Visual consistency**: Easy to compare across different chapters
2. **Predictability**: Users know what each color means
3. **Maintainability**: Change once in `STANDARD_COLORS.py`, affects all scripts
4. **Documentation**: Single source of truth for color definitions

## Difference from Docling Native Colors

**Docling native colors** (from `DocItemLabel.get_color()`) are **pastel colors**:
- text: Yellow pastel `(1.0, 1.0, 0.6)`
- section_header: Light red `(1.0, 0.6, 0.6)`
- table: Light pink `(1.0, 0.8, 0.8)`

**Our standard colors** are **solid/saturated colors** for better visibility:
- text: Blue `(0, 0, 1)`
- section_header: Red `(1, 0, 0)`
- table: Green `(0, 0.7, 0)`

**Rationale**: Solid colors provide better visual distinction and are easier to see in annotated PDFs.

## Updating the Color Scheme

To change colors for ALL chapters:

1. Edit `/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/docling_layout/STANDARD_COLORS.py`
2. Modify the `DOCLING_COLORS` dictionary
3. All scripts that import from `STANDARD_COLORS` will use the new colors automatically

## Testing Color Scheme

```bash
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout
python3 STANDARD_COLORS.py
```

This will print the current color scheme and legend.
