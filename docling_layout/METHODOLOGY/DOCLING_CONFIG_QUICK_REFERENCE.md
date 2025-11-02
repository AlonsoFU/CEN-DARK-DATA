# Docling Configuration Quick Reference

**One-page cheat sheet for Docling configuration**

---

## Configuration Hierarchy

```
DocumentConverter
   │
   └─→ format_options {InputFormat.PDF: PdfFormatOption}
          │
          └─→ pipeline_options: PdfPipelineOptions
                 │
                 ├─→ do_ocr: bool
                 ├─→ do_table_structure: bool
                 │
                 ├─→ table_structure_options: TableStructureOptions
                 │      ├─→ mode: FAST | ACCURATE
                 │      └─→ do_cell_matching: bool
                 │
                 ├─→ ocr_options: EasyOcrOptions
                 │      ├─→ lang: ["en", "es", ...]
                 │      └─→ use_gpu: bool
                 │
                 ├─→ accelerator_options: AcceleratorOptions
                 │      ├─→ num_threads: int
                 │      └─→ device: CUDA | CPU | MPS | AUTO
                 │
                 ├─→ generate_page_images: bool
                 ├─→ generate_picture_images: bool
                 ├─→ generate_table_images: bool
                 └─→ images_scale: float (0.0-1.0)
```

---

## Quick Config Templates

### 1️⃣ Lightweight (4GB GPU) - 1.3 GB VRAM

```python
pipeline_options = PdfPipelineOptions(
    do_ocr=False,  # 💾 -1.5 GB
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,  # 💾 -400 MB
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=4, device=AcceleratorDevice.CUDA
    ),
    generate_page_images=False,
    generate_picture_images=True,
    generate_table_images=False,
    images_scale=0.5  # 💾 -50% image memory
)
```

### 2️⃣ Balanced (6GB GPU) - 2.5 GB VRAM

```python
pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=EasyOcrOptions(lang=["en"]),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=4, device=AcceleratorDevice.CUDA
    ),
)
```

### 3️⃣ Maximum Accuracy (8GB+ GPU) - 4.2 GB VRAM

```python
pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=EasyOcrOptions(lang=["en", "es"]),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.ACCURATE,  # 🎯 97.9% accuracy
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=4, device=AcceleratorDevice.CUDA
    ),
)
```

### 4️⃣ CPU Only (No GPU) - 400 MB RAM

```python
pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=EasyOcrOptions(lang=["en"], use_gpu=False),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=8,  # ⚡ More threads for CPU
        device=AcceleratorDevice.CPU
    ),
)
```

---

## Configuration Decision Tree

```
Start: What GPU do you have?
│
├─→ No GPU / CPU only
│   └─→ Use Template 4 (CPU mode, 400 MB RAM, 10x slower)
│
├─→ 4GB GPU (GTX 1650, RTX 3050)
│   └─→ Use Template 1 (Lightweight, 1.3 GB VRAM)
│
├─→ 6GB GPU (RTX 2060, GTX 1660 Ti)
│   ├─→ Need OCR? → Use Template 2 (Balanced, 2.5 GB)
│   └─→ No OCR? → Use Template 1 (Lightweight, 1.3 GB)
│
└─→ 8GB+ GPU (RTX 3060/3070/4060+)
    ├─→ Need max accuracy? → Use Template 3 (Maximum, 4.2 GB)
    └─→ Want speed? → Use Template 2 (Balanced, 2.5 GB)
```

---

## Memory Budget Breakdown

### Lightweight Mode (1.3 GB)
```
Layout Model (Granite-258M):  1.2 GB
Table Structure (FAST):       0.4 GB
OCR:                          0.0 GB (disabled)
PyTorch overhead:             0.3 GB
Images (scale=0.5):           0.1 GB
────────────────────────────────────
TOTAL:                        ~1.3 GB ✅ Fits 4GB GPU
```

### Balanced Mode (2.5 GB)
```
Layout Model:                 1.2 GB
Table Structure (FAST):       0.4 GB
OCR (English):                1.5 GB
PyTorch overhead:             0.3 GB
Images:                       0.2 GB
────────────────────────────────────
TOTAL:                        ~2.5 GB ✅ Fits 6GB GPU
```

### Maximum Mode (4.2 GB)
```
Layout Model:                 1.2 GB
Table Structure (ACCURATE):   0.8 GB
OCR (En + Es):                1.7 GB
PyTorch overhead:             0.3 GB
Images + artifacts:           0.3 GB
────────────────────────────────────
TOTAL:                        ~4.2 GB ⚠️ Needs 6GB+ GPU
```

---

## Table Mode Comparison

| Metric | FAST | ACCURATE |
|--------|------|----------|
| **Accuracy** | 90-95% | 97.9% |
| **VRAM** | 400 MB | 800 MB |
| **Speed** | 2.5 pages/s | 2.0 pages/s |
| **Merged cells** | Basic | Full |
| **Best for** | Simple tables | Complex tables |

**Rule of thumb**: Use FAST unless you have complex tables with merged cells.

---

## OCR Language Codes

```python
# Single language
lang=["en"]    # English
lang=["es"]    # Spanish
lang=["pt"]    # Portuguese
lang=["fr"]    # French
lang=["de"]    # German

# Multiple languages (auto-detect)
lang=["en", "es"]           # +300 MB
lang=["en", "es", "pt"]     # +600 MB
```

**Memory impact**: ~200-300 MB per additional language

---

## Export Methods Quick Reference

### 1. Complete JSON (Best for data processing)
```python
result.document.save_as_json("output.json", indent=2)
```
**Includes**: Everything (tables, text, coordinates, metadata)

### 2. Markdown (Best for humans)
```python
md = result.document.export_to_markdown(enable_chart_tables=True)
```
**Includes**: Text and tables in markdown format

### 3. Dictionary (Best for Python)
```python
doc_dict = result.document.export_to_dict()
```
**Includes**: Python dict with all data

---

## Performance Tips

### Speed Optimization
```python
# ⚡ +20% faster
table_structure_options=TableStructureOptions(mode=TableFormerMode.FAST)

# ⚡ +10% faster
do_ocr=False  # If PDF has native text

# ⚡ Process fewer pages
page_range=(1, 50)
```

### Memory Optimization
```python
# 💾 -1.5 GB
do_ocr=False

# 💾 -400 MB
table_structure_options=TableStructureOptions(mode=TableFormerMode.FAST)

# 💾 -50%
images_scale=0.5

# 💾 -200 MB
generate_page_images=False
```

---

## Common Pitfalls

### ❌ Don't Do This
```python
# Running multiple instances on 4GB GPU
# 3 × 1.5 GB = 4.5 GB → CRASH!

# Using ACCURATE mode on 4GB GPU with OCR
# 1.2 + 0.8 + 1.5 = 3.5 GB + overhead = CRASH!

# Forgetting page_range with large PDFs
# Processing 1000+ pages will take hours
```

### ✅ Do This Instead
```python
# One instance at a time on 4GB GPU
# Or use lightweight mode (1.3 GB)

# Use FAST mode on 4GB GPU
# Or disable OCR to save 1.5 GB

# Use page_range for testing
result = converter.convert("doc.pdf", page_range=(1, 20))
```

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| CUDA OOM | Out of VRAM | Use lightweight mode or CPU |
| Slow processing | CPU mode | Check GPU with `nvidia-smi` |
| Empty table text | No export | Use `save_as_json()` method |
| Missing tables | Wrong mode | Use ACCURATE for complex tables |

---

## Complete Working Example

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    EasyOcrOptions,
    AcceleratorOptions,
    AcceleratorDevice
)

# Configure pipeline
pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=EasyOcrOptions(lang=["en"]),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.ACCURATE,
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=4,
        device=AcceleratorDevice.CUDA
    ),
)

# Create converter
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)

# Convert document
result = converter.convert("document.pdf", page_range=(1, 50))

# Export results
result.document.save_as_json("output.json", indent=2)
print("✅ Extraction complete!")
```

---

**For detailed explanations, see**: `DOCLING_CONFIGURATION_COMPLETE_GUIDE.md`
