# Universal Docling Extraction Script - Usage Guide

## 🎯 Overview

**ONE script for ALL chapters** - just change the chapter number!

No need for separate `extract_chapter03.py`, `extract_chapter04.py`, etc.

---

## 🚀 Quick Start

### Extract Any Chapter:

```bash
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout

# Extract Chapter 5
python3 UNIVERSAL_extract_any_chapter.py 5

# Extract Chapter 8
python3 UNIVERSAL_extract_any_chapter.py 8

# Extract Chapter 10
python3 UNIVERSAL_extract_any_chapter.py 10
```

### Extract with Default Chapter (5):

```bash
python3 UNIVERSAL_extract_any_chapter.py
```

---

## 📋 What It Does

The script automatically:

1. ✅ **Applies EAF Monkey Patch** (fills gaps Docling missed)
2. ✅ **Runs Docling extraction** (layout detection + text extraction)
3. ✅ **Applies Zona fix** (reclassifies sequential vs isolated items)
4. ✅ **Exports to JSON** (structured data with metadata)
5. ✅ **Generates annotated PDF** (color-coded bounding boxes)
6. ✅ **Fixes page indexing bug** (1-indexed → 0-indexed conversion)

---

## 📁 Output Files

For each chapter, you get:

```
capitulo_{N:02d}/outputs/
├── layout_WITH_PATCH.json        # Structured extraction data
└── capitulo_{N:02d}_annotated.pdf # Color-coded visualization
```

### Example: Chapter 5
```
capitulo_05/outputs/
├── layout_WITH_PATCH.json
└── capitulo_05_annotated.pdf
```

---

## 🎨 Color Scheme (Standard)

| Color | Element Type | RGB |
|-------|--------------|-----|
| 🔴 Red | section_header | (1, 0, 0) |
| 🔵 Blue | text | (0, 0, 1) |
| 🟢 Green | table | (0, 0.7, 0) |
| 🔵 Cyan | list_item | (0, 0.7, 0.7) |
| 🟣 Magenta | picture | (1, 0, 1) |
| 🟠 Orange | title | (1, 0.5, 0) |
| 🟤 Brown | caption/footnote | (0.8, 0.4, 0) |
| 🟡 Yellow | formula | (1, 0.8, 0) |
| ⚪ Gray | page_header/footer | (0.5, 0.5, 0.5) |

---

## ⚙️ Configuration

### Option 1: Edit Script (Line 36-68)

Change the `CHAPTER_NUM` variable:

```python
# Default chapter
CHAPTER_NUM = 5  # Change this!
```

### Option 2: Pass as Argument (Recommended)

```bash
python3 UNIVERSAL_extract_any_chapter.py 7  # Extract Chapter 7
```

### Option 3: Edit config_chapters.json

Modify `config_chapters.json` to add new chapters or change settings:

```json
{
  "chapters": {
    "12": {
      "name": "New Chapter",
      "pages": 20,
      "page_range": "465-484"
    }
  }
}
```

---

## 📊 Chapter Information (All 11 Chapters)

| # | Name | Pages | Page Range |
|---|------|-------|------------|
| 1 | Descripción de la perturbación | 11 | 65-75 |
| 2 | Equipamiento afectado | 79 | 76-154 |
| 3 | Energía no suministrada | 63 | 155-217 |
| 4 | Configuraciones previo y posterior | 7 | 218-224 |
| 5 | Cronología de eventos | 12 | 225-236 |
| 6 | Normalización del servicio | 94 | 237-330 |
| 7 | Análisis de las causas de la falla | 82 | 331-412 |
| 8 | Detalle de información | 1 | 413-413 |
| 9 | Análisis de protecciones | 33 | 414-446 |
| 10 | Pronunciamiento técnico | 11 | 447-457 |
| 11 | Recomendaciones | 7 | 458-464 |

---

## 🔧 Advanced Configuration

### Docling Settings (Line 102-107)

```python
DOCLING_CONFIG = {
    "do_ocr": False,                    # True for scanned PDFs
    "do_table_structure": True,          # Always True
    "table_mode": "ACCURATE",            # ACCURATE (slower) or FAST
    "do_picture_classification": True,   # Classify images
    "do_formula_enrichment": False       # Extract LaTeX formulas
}
```

### Patch Settings (Line 110-113)

```python
PATCH_CONFIG = {
    "enabled": True,          # Set False to disable patch
    "apply_zona_fix": True    # Set False to skip Zona fix
}
```

---

## 🐛 Critical Bug Fix (Included)

The script automatically fixes the **page indexing bug**:

```python
# Line 301: Correct conversion
pymupdf_page_idx = page_num - 1  # Docling (1-indexed) → PyMuPDF (0-indexed)
```

This ensures bounding boxes appear on the **correct pages**.

---

## 📈 Performance

| Pages | GPU (4GB+) | CPU Only |
|-------|-----------|----------|
| 10 | ~30 sec | ~5 min |
| 30 | ~2 min | ~20 min |
| 50 | ~3-4 min | ~35 min |
| 80 | ~5-7 min | ~60 min |

**Note**: First run downloads models (~200 MB), subsequent runs are 40x faster.

---

## ✅ Requirements

1. **PDF file exists** in `../claude_ocr/capitulo_{N:02d}/`
2. **EAF patch** directory at `eaf_patch/`
3. **Python packages**: docling, PyMuPDF, pathlib

---

## 🎯 Examples

### Extract Chapter 3 (Energy not supplied)

```bash
python3 UNIVERSAL_extract_any_chapter.py 3
```

**Output:**
```
📖 UNIVERSAL DOCLING EXTRACTION
Chapter 3: Energía no suministrada
Pages: 63 (range 155-217)
✅ PDF found: 5.1 MB

🐵 Applying EAF Monkey Patch...
⚙️  Configuring Docling Pipeline...
🔄 Processing Chapter 3...
⏱️  Estimated time: 3.2 minutes (63 pages)

✅ Docling extraction complete
✅ Zona fix applied (4 items reclassified)
✅ Saved JSON: layout_WITH_PATCH.json
📊 Total elements: 88

📊 Elements by type:
   table               :   63 ( 71.6%)
   list_item           :   11 ( 12.5%)
   text                :    7 (  8.0%)

✅ Drew 88 bounding boxes
✅ Saved PDF: capitulo_03_annotated.pdf

✅ CHAPTER 3 EXTRACTION COMPLETE!
```

### Extract Multiple Chapters

```bash
# Extract chapters 5, 8, 10 sequentially
for chapter in 5 8 10; do
    python3 UNIVERSAL_extract_any_chapter.py $chapter
done
```

---

## 🆚 Old vs New Approach

### ❌ Old Way (Chapter-Specific Scripts):

```bash
python3 extract_chapter03_CORRECTED.py  # Only Chapter 3
python3 extract_chapter04_CORRECTED.py  # Only Chapter 4
python3 extract_chapter05_CORRECTED.py  # Only Chapter 5
# ... 11 different scripts!
```

### ✅ New Way (Universal Script):

```bash
python3 UNIVERSAL_extract_any_chapter.py 3  # Chapter 3
python3 UNIVERSAL_extract_any_chapter.py 4  # Chapter 4
python3 UNIVERSAL_extract_any_chapter.py 5  # Chapter 5
# ... ONE script for all!
```

---

## 🔍 Troubleshooting

### Error: "PDF not found"

**Solution**: Check that PDF exists at expected location:
```bash
ls ../claude_ocr/capitulo_05/EAF-089-2025_capitulo_05_pages_*.pdf
```

### Error: "Chapter not found in configuration"

**Solution**: Add chapter to `CHAPTER_INFO` dictionary (line 40-90)

### Error: "No module named 'core.eaf_patch_engine'"

**Solution**: Verify `eaf_patch/` directory exists with patch files

### GPU out of memory

**Solution**: Use CPU mode by editing line 104:
```python
"do_ocr": False,  # Disable OCR to reduce memory
```

---

## 📚 Related Files

- `UNIVERSAL_extract_any_chapter.py` - Main extraction script
- `config_chapters.json` - Chapter configuration (optional)
- `eaf_patch/core/eaf_patch_engine.py` - Monkey patch implementation
- `METHODOLOGY/UNIVERSAL_DOCLING_METHODOLOGY.md` - Complete methodology guide

---

## 🎓 Learn More

For complete methodology and technical details, see:
- `METHODOLOGY/DOCLING_DESIGN_PHILOSOPHY.md` - Understanding Docling
- `METHODOLOGY/UNIVERSAL_DOCLING_METHODOLOGY.md` - Complete guide (400+ lines)
- `METHODOLOGY/QUICK_START_GUIDE.md` - One-page reference
- `STANDARD_EXTRACTION_WORKFLOW.md` - Production workflow

---

**Version**: 1.0
**Last Updated**: 2025-10-28
**Status**: Production-ready ✅
