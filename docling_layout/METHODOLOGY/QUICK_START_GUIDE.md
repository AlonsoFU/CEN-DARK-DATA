# Quick Start Guide: Docling + EAF Patch

**For processing ANY PDF with Docling + custom patch**

---

## 🚀 30-Second Start

```bash
# 1. Navigate to your project
cd /path/to/docling_layout

# 2. Create chapter directory
mkdir -p capitulo_XX/outputs

# 3. Copy template script
cp UNIVERSAL_DOCLING_METHODOLOGY.md capitulo_XX/

# 4. Run extraction (see Phase 2 in methodology)
```

---

## 📊 What You Get

### Outputs Created:
1. **`layout_WITH_PATCH.json`** - Complete extraction with Docling labels
2. **`patch_input_to_docling.json`** - What patch gives TO Docling
3. **`patch_input_to_docling.pdf`** - Color-coded visualization
4. **`EXTRACTION_SUMMARY.md`** - Results documentation

### Docling Labels Preserved:
```json
{
  "type": "section_header",  // ← FULL DOCLING LABEL
  "text": "7. Title",
  "page": 0,
  "bbox": {"x0": 56.8, "y0": 123.45, "x1": 538.24, "y1": 135.67}
}
```

---

## 🎨 Standard Colors

| Element | Color | RGB |
|---------|-------|-----|
| `text` | 🔵 Blue | (0, 0, 1) |
| `section_header` | 🔴 Red | (1, 0, 0) |
| `title` | 🟠 Orange | (1, 0.5, 0) |
| `list_item` | 🔷 Cyan | (0, 0.7, 0.7) |
| `table` | 🟢 Green | (0, 0.7, 0) |
| `picture` | 🟣 Magenta | (1, 0, 1) |
| `caption` | 🟤 Brown | (0.8, 0.4, 0) |
| `formula` | 🟡 Yellow | (1, 0.8, 0) |
| `footnote` | 🟤 Brown | (0.8, 0.4, 0) |
| `page_header` | ⚪ Gray | (0.5, 0.5, 0.5) |
| `page_footer` | ⚪ Gray | (0.5, 0.5, 0.5) |

---

## ⚙️ Configuration Template

### ⭐ RECOMMENDED: Optimized Safe Configuration

**Use this for ALL production work** (best quality, minimal speed penalty)

```python
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)

pipeline_options = PdfPipelineOptions()

# Core processing - Optimized Safe (3030 MB VRAM)
pipeline_options.do_ocr = False                       # ❌ Native PDF
pipeline_options.do_table_structure = True            # ✅ ACCURATE mode
pipeline_options.do_picture_classification = True     # ✅ Classify images
pipeline_options.do_picture_description = True        # ✅ Describe with SmolVLM
pipeline_options.do_code_enrichment = False           # ❌ Not needed
pipeline_options.do_formula_enrichment = True         # ✅ Extract equations

# Table settings - ACCURATE mode (97.9% accuracy)
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,
    do_cell_matching=True
)

# GPU settings
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=2,
    device="cuda"
)

# Performance: 3.1 s/page (after first run)
# VRAM: 3030 MB (safe on 4GB GPU)
# Accuracy: 97.9% tables + picture understanding + formulas
```

### Legacy: Lightweight Configuration (not recommended)

**Only use if absolutely need minimum VRAM**

```python
# Lightweight (2000 MB VRAM) - DEPRECATED
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.FAST,  # 90-95% accuracy
    do_cell_matching=True
)
pipeline_options.do_picture_classification = False
pipeline_options.do_picture_description = False
pipeline_options.do_code_enrichment = False
pipeline_options.do_formula_enrichment = False

# Performance: 2.7 s/page
# Not worth the 0.4s/page savings - use Optimized Safe instead
```

### Patch Configuration

```python
PATCH_CONFIG = {
    "enabled": True,
    "coverage_threshold": 0.5,  # 0.3-0.7 range
    "detect_titles": True,
    "detect_custom_patterns": True  # Add your patterns
}
```

---

## 🔧 Key Functions Reference

### 1. Apply Patch
```python
from core.eaf_patch_engine import apply_universal_patch_with_pdf

apply_universal_patch_with_pdf(str(PDF_PATH))
```

### 2. Run Docling
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(PDF_PATH))
```

### 3. Extract with Full Labels
```python
elements.append({
    'type': item.label,  # ← PRESERVES DOCLING LABEL
    'text': item.text,
    'page': page_num,
    'bbox': bbox_dict
})
```

---

## 🎯 Common Customizations

### Add Custom Pattern Detector

```python
# eaf_patch/core/your_detector.py
class YourDetector:
    def __init__(self):
        self.patterns = [
            re.compile(r'your_pattern'),
        ]
    
    def matches(self, text):
        return any(p.match(text) for p in self.patterns)
```

### Adjust Coverage Threshold

```python
# Dense documents (fewer gaps expected)
PATCH_CONFIG['coverage_threshold'] = 0.7

# Sparse documents (more gaps expected)
PATCH_CONFIG['coverage_threshold'] = 0.3
```

### Custom Colors

```python
COLORS = {
    'text': (0, 0, 1),
    'your_custom_type': (0.2, 0.8, 0.5),  # Custom color
}
```

---

## 🐛 Troubleshooting

### Duplicate Clusters
**Fix**: Only process `missing_line_blocks`, not `all_blocks`

### Gray Boxes (No Color)
**Fix**: Normalize label names before color lookup
```python
label = elem['type'].split('.')[-1].lower()
color = COLORS.get(label, (0.5, 0.5, 0.5))
```

### GPU Out of Memory
**Fix**: Optimized Safe should work on 4GB GPU (3030 MB)
- If still failing, check for other GPU processes
- Only fall back to lightweight if absolutely necessary

### First Run is Slow (20+ minutes)
**Normal**: First run downloads models (SmolVLM ~200 MB, etc.)
- Models cached locally after first run
- Second run will be 41x faster (~30 seconds for 11 pages)
- Expected: First run 23.6 min → Subsequent runs 0.57 min

---

## ⚡ Performance Expectations

### Optimized Safe Configuration (Recommended)

**First run** (includes one-time model downloads):
- Chapter 1 (11 pages): 23.6 minutes
- 399-page document: ~140 minutes (2.3 hours)

**Subsequent runs** (models cached):
- Chapter 1 (11 pages): 34 seconds (41x faster!)
- 399-page document: ~20 minutes
- Speed: 3.1 seconds/page

**Quality:**
- Tables: 97.9% accuracy (ACCURATE mode)
- Picture understanding: SmolVLM descriptions
- Formula extraction: LaTeX equations
- VRAM: 3030 MB (safe on 4GB GPU)

---

## 📝 Checklist

- [ ] Read `UNIVERSAL_DOCLING_METHODOLOGY.md`
- [ ] Create chapter directory structure
- [ ] Use **Optimized Safe** configuration (recommended)
- [ ] Run extraction (first run will download models)
- [ ] Subsequent runs will be 41x faster
- [ ] Generate visualization
- [ ] Verify outputs (check JSON + PDF)
- [ ] Document customizations
- [ ] Create `EXTRACTION_SUMMARY.md`

---

## 📚 Full Documentation

See `UNIVERSAL_DOCLING_METHODOLOGY.md` for:
- Complete architecture
- All 11 Docling labels
- EAF patch pipeline details
- Step-by-step workflow
- Code templates
- Best practices

---

**Last Updated**: 2025-10-26  
**Chapter 7 Reference**: 82 pages, 4,719 elements, 0 duplicates ✅
