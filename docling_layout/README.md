# Docling Layout Extraction with EAF Monkey Patch

**Last Updated**: 2025-10-26
**Status**: Production-Ready ✅

---

## 🎯 Quick Summary

This directory contains **standardized Docling extraction** for EAF chapters using the **EAF Monkey Patch** (Method A).

### Completed Chapters

- ✅ **Chapter 6**: 366 elements (baseline reference)
- ✅ **Chapter 7**: 366 elements (standardized with patch)

### What the EAF Patch Does

The patch **intercepts Docling's pipeline** and applies domain-specific fixes:

1. **🔗 Title Merging**: Replaces short titles ("6.", "7.1") with complete lines from PyMuPDF
2. **✅ Missing Detection**: Finds titles Docling completely missed
3. **⚡ Power Lines**: Classifies power system equipment as `list_item`
4. **🔄 Zona Sequential**: Distinguishes isolated (headers) vs sequential (lists) Zona items

---

## 📊 Chapter 7 Results (WITH PATCH)

**File**: `capitulo_07/outputs/layout_WITH_PATCH.json`
**Total Elements**: 366

| Type | Count | Description |
|------|-------|-------------|
| text | 139 | Regular paragraphs |
| list_item | 72 | Bulleted/numbered lists + power lines |
| table | 61 | Tables detected |
| picture | 57 | Figures/diagrams |
| section_header | 33 | Titles/headings (merged + detected) |
| caption | 4 | Figure captions |

**Annotated PDF**: `capitulo_07/outputs/chapter7_WITH_PATCH.pdf` (3.1 MB)

---

## 🚀 Processing New Chapters

### Quick Start (2 commands per chapter)

```bash
# 1. Extract with patch
python3 extract_chapter{N}_WITH_PATCH.py

# 2. Create visualization
python3 visualize_chapter{N}_WITH_PATCH.py
```

### Batch Process All Chapters (2-11)

```bash
python3 BATCH_process_chapters_2_to_11.py
```

**Time**: ~60-90 minutes for all 9 chapters

---

## 📚 Documentation

- **Complete Guide**: `STANDARD_EXTRACTION_WORKFLOW.md` - Full workflow with templates
- **Docling Details**: `README_DOCLING.md` - IBM Docling technical documentation
- **GPU Requirements**: `GPU_REQUIREMENTS.md` - Hardware constraints (4GB+ GPU)
- **Lightweight Modes**: `LIGHTWEIGHT_MODES.md` - Memory optimization

---

## 📁 File Structure

```
docling_layout/
├── eaf_patch/                          # EAF monkey patch code
│   ├── core/
│   │   └── eaf_patch_engine.py        # Main patch engine
│   └── domain/
│       └── power_line_classifier.py   # Power system detection
│
├── capitulo_06/                        # Chapter 6 (reference)
│   └── outputs/
│       ├── layout_WITH_PATCH.json
│       └── chapter6_WITH_PATCH.pdf
│
├── capitulo_07/                        # Chapter 7 (standardized)
│   └── outputs/
│       ├── layout_WITH_PATCH.json     # Extraction data
│       ├── chapter7_WITH_PATCH.pdf    # Annotated PDF
│       └── layout_lightweight*.json   # Old Docling outputs (deprecated)
│
├── extract_chapter6_patched_only.py   # Chapter 6 extraction
├── extract_chapter7_WITH_PATCH.py     # Chapter 7 extraction (template)
├── visualize_chapter7_WITH_PATCH.py   # Chapter 7 visualization (template)
│
├── BATCH_process_chapters_2_to_11.py  # Batch processing script
└── STANDARD_EXTRACTION_WORKFLOW.md    # Complete workflow guide
```

---

## 🎨 Visualization Color Scheme

All annotated PDFs use the same color scheme:

- 🔵 **Blue** = text (regular paragraphs)
- 🔴 **Red** = section_header / title
- 🟢 **Green** = table
- 🔵🟢 **Cyan** = list_item
- 🟣 **Magenta** = picture
- 🟠 **Orange** = formula
- ⚪ **Gray** = page_header / page_footer

---

## ⚙️ Technical Details

### Method A: Monkey Patch (Used in Chapters 6-7)

**How it works**:
1. Replaces `LayoutPostprocessor._process_regular_clusters()` before Docling runs
2. Extracts text from PDF using PyMuPDF (independent of Docling)
3. Detects missing elements (titles, power lines) from PyMuPDF data
4. Creates synthetic clusters with cells (complete text from PyMuPDF)
5. Docling processes modified + new clusters normally
6. Result: Complete extraction with domain-specific fixes

**Why it's better than post-processing**:
- ✅ Docling extracts the modified content (not just relabeled)
- ✅ Creates new elements Docling never saw
- ✅ Preserves all metadata and relationships
- ✅ Consistent with Docling's internal structure

### Method B: Post-Processing (Deprecated)

**What it was**:
- Modify JSON after Docling completes
- Change `list_item` → `section_header` labels
- Cannot add missing elements
- Only used in early Chapter 7 experiments

**Why we switched to Method A**:
- Post-processing can't create missing titles
- Can't inject complete lines from PyMuPDF
- Limited to relabeling existing elements

---

## 🔍 Quality Comparison

### Before Patch (Plain Docling)

Chapter 7 first page:
- ❌ Title: "7." (incomplete - missing full text)
- ❌ Missing: 6 power system list items
- ❌ Zona items: Inconsistent classification

### After Patch (Method A)

Chapter 7 first page:
- ✅ Title: "7. Análisis de las causas de la falla..." (complete from PyMuPDF)
- ✅ Detected: 6 power system list items
- ✅ Zona items: Properly classified (sequential vs isolated)

**Total across 82 pages**:
- Created **33 section headers** (merged + detected)
- Classified **72 list items** (including power lines)
- Fixed **all Zona items** with sequential detection

---

## 🚨 Important Notes

### File Naming Convention

**Use**:
- ✅ `layout_WITH_PATCH.json` - Extraction data
- ✅ `chapter{N}_WITH_PATCH.pdf` - Annotated PDF
- ✅ `extract_chapter{N}_WITH_PATCH.py` - Extraction script
- ✅ `visualize_chapter{N}_WITH_PATCH.py` - Visualization script

**Deprecated** (do not use):
- ❌ `layout_clean.json`
- ❌ `layout_clean_zona_fixed.json`
- ❌ `layout_WITH_ZONA_FIX.json`
- ❌ Post-processing scripts

### GPU Requirements

- **Minimum**: 4GB VRAM (GTX 1650, RTX 2060)
- **Recommended**: 6GB+ VRAM (RTX 3060, RTX 4060)
- **CPU fallback**: Works but 10x slower

### Processing Time

| Pages | GPU (4GB+) | CPU Only |
|-------|-----------|----------|
| 30    | 2 min     | 20 min   |
| 50    | 3-4 min   | 35 min   |
| 82    | 5-7 min   | 60 min   |

---

## 📖 Next Steps

1. **Read**: `STANDARD_EXTRACTION_WORKFLOW.md` for complete guide
2. **Process**: Chapters 2-11 using templates or batch script
3. **Verify**: Visual inspection of annotated PDFs
4. **Document**: Update this README with new chapter results

---

**Version**: 1.0
**Method**: EAF Monkey Patch (Method A)
**Status**: Production-Ready ✅
