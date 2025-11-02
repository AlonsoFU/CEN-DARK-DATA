# CRITICAL BUG: Page Indexing Mismatch (Docling vs PyMuPDF)

**Severity**: ❌ CRITICAL
**Impact**: Bounding boxes appear on wrong pages in annotated PDFs
**Status**: FIXED
**Date Found**: 2025-10-27

---

## 🐛 The Bug

When creating annotated PDFs with bounding boxes, boxes appear **one page too late**:
- Content from page 1 appears on page 2
- Content from page 2 appears on page 3
- etc.

---

## 🔍 Root Cause

**Docling and PyMuPDF use different page numbering systems:**

| System | Page 1 | Page 2 | Page 3 |
|--------|--------|--------|--------|
| **Docling** | `page_num = 1` | `page_num = 2` | `page_num = 3` |
| **PyMuPDF** | `doc_pdf[0]` | `doc_pdf[1]` | `doc_pdf[2]` |

**Docling**: 1-indexed (first page = 1)
**PyMuPDF**: 0-indexed (first page = 0)

---

## ❌ Incorrect Code (BUGGY)

```python
import fitz  # PyMuPDF

doc_pdf = fitz.open("document.pdf")

for elem in elements:
    page_num = elem['page']  # Docling page number (1, 2, 3...)

    # ❌ BUG: Using Docling page number directly in PyMuPDF
    page = doc_pdf[page_num]  # WRONG! Off by one!

    bbox = elem['bbox']
    rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
    page.draw_rect(rect, color=(1, 0, 0))
```

**What happens**:
- Docling element on page 1 (`page_num=1`)
- Gets drawn on PyMuPDF page[1] (which is page 2) ❌

---

## ✅ Correct Code (FIXED)

```python
import fitz  # PyMuPDF

doc_pdf = fitz.open("document.pdf")

for elem in elements:
    page_num = elem['page']  # Docling page number (1, 2, 3...)

    # ✅ CORRECT: Convert Docling page to PyMuPDF index
    pymupdf_page_idx = page_num - 1  # Subtract 1!

    if 0 <= pymupdf_page_idx < len(doc_pdf):
        page = doc_pdf[pymupdf_page_idx]  # CORRECT!

        bbox = elem['bbox']
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
        page.draw_rect(rect, color=(1, 0, 0))
```

**What happens**:
- Docling element on page 1 (`page_num=1`)
- Converts to PyMuPDF index (`pymupdf_page_idx=0`)
- Gets drawn on PyMuPDF page[0] (which is page 1) ✅

---

## 🎯 The Fix

**ALWAYS subtract 1 when converting Docling page numbers to PyMuPDF indices:**

```python
# When reading Docling output
docling_page = elem['page']  # 1, 2, 3, 4, ...

# When drawing on PDF with PyMuPDF
pymupdf_index = docling_page - 1  # 0, 1, 2, 3, ...
page = doc_pdf[pymupdf_index]
```

---

## 📋 Checklist: Preventing This Bug

When writing visualization code, **ALWAYS**:

### ✅ DO:
```python
# ✅ Explicit conversion with comment
pymupdf_page_idx = docling_page_num - 1  # Docling is 1-indexed, PyMuPDF is 0-indexed
page = doc_pdf[pymupdf_page_idx]

# ✅ Bounds checking
if 0 <= pymupdf_page_idx < len(doc_pdf):
    page = doc_pdf[pymupdf_page_idx]

# ✅ Add comment explaining the conversion
# CRITICAL: Docling uses 1-indexed pages, PyMuPDF uses 0-indexed
```

### ❌ DON'T:
```python
# ❌ Using Docling page_num directly
page = doc_pdf[page_num]  # BUG!

# ❌ No conversion
page = doc_pdf[elem['page']]  # BUG!

# ❌ No comment explaining why you subtract 1
page = doc_pdf[page_num - 1]  # Why -1? Not obvious!
```

---

## 🔍 How to Detect This Bug

### Visual Inspection:
1. Open annotated PDF
2. Check page 1 - should have bounding boxes
3. If page 1 is empty but page 2 has boxes → **BUG DETECTED**

### Programmatic Check:
```python
import json

with open('layout.json', 'r') as f:
    data = json.load(f)

# Find first element
first_elem = data['elements'][0]
print(f"First element on Docling page: {first_elem['page']}")

# It should be page 1 (or 0 if already converted)
if first_elem['page'] == 1:
    print("✅ Docling uses 1-indexed pages")
elif first_elem['page'] == 0:
    print("✅ Already converted to 0-indexed")
```

---

## 🛠️ Where This Bug Can Occur

**Any code that:**
1. Reads Docling output (JSON with `page_num`)
2. Opens the same PDF with PyMuPDF (fitz.open)
3. Draws annotations on pages

**Common locations:**
- Visualization scripts (`visualize_*.py`)
- Annotation scripts (`annotate_*.py`)
- PDF generation in extraction scripts
- Comparison tools that overlay boxes

---

## 📚 Technical Details

### Docling Page Numbering:
```python
# Docling internal representation
for item, level in doc.iterate_items():
    page_num = item.prov[0].page_no  # Returns 1, 2, 3, ...
```

### PyMuPDF Page Numbering:
```python
# PyMuPDF internal representation
doc = fitz.open("file.pdf")
doc[0]  # First page
doc[1]  # Second page
doc[2]  # Third page
```

### Conversion Formula:
```python
pymupdf_index = docling_page_num - 1

# Examples:
# Docling page 1 → PyMuPDF index 0
# Docling page 2 → PyMuPDF index 1
# Docling page 3 → PyMuPDF index 2
```

---

## ✅ Files Fixed

**Fixed in this session:**
- `extract_chapter11_WITH_PATCH.py` (line 142-147)

**Check these files for the same bug:**
- All `extract_chapter*.py` files with PDF visualization
- All `visualize_*.py` scripts
- Any script using `fitz.open()` + Docling JSON

---

## 🚨 Action Items

### For New Code:
1. **Always** add comment explaining 1-indexed vs 0-indexed
2. **Always** use explicit variable name: `pymupdf_page_idx`
3. **Always** subtract 1: `pymupdf_page_idx = docling_page - 1`
4. **Always** bounds check: `if 0 <= pymupdf_page_idx < len(doc_pdf)`

### For Existing Code:
1. Search for `doc_pdf[page_num]` or `doc[page_num]`
2. Check if `page_num` comes from Docling output
3. If yes, add `-1` conversion
4. Add explanatory comment

### Testing:
1. Always visually inspect page 1 of annotated PDFs
2. Verify boxes appear on correct pages
3. Check against original PDF to confirm alignment

---

## 📖 References

**Docling Documentation:**
- Page numbers are 1-indexed in `item.prov[0].page_no`
- First page of document = page 1

**PyMuPDF Documentation:**
- Pages are accessed by 0-indexed integer
- `doc[0]` = first page, `doc[1]` = second page

---

**Last Updated**: 2025-10-27
**Priority**: CRITICAL - Check all visualization code
**Status**: FIXED in Chapter 11 extraction
