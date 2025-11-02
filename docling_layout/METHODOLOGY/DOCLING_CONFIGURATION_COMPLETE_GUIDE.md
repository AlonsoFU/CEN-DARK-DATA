# Docling Configuration Complete Guide

**Everything you need to know about configuring Docling for PDF extraction**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Pipeline Configuration](#pipeline-configuration)
3. [Table Extraction Options](#table-extraction-options)
4. [OCR Configuration](#ocr-configuration)
5. [Accelerator Options (GPU/CPU)](#accelerator-options)
6. [Image Processing](#image-processing)
7. [Page Range and Limits](#page-range-and-limits)
8. [Export Configuration](#export-configuration)
9. [Complete Examples](#complete-examples)
10. [Performance Tuning](#performance-tuning)

---

## Architecture Overview

Docling uses a **pipeline architecture** with modular components:

```
PDF Input
   ↓
DocumentConverter (main entry point)
   ↓
PdfFormatOption (format-specific config)
   ↓
PdfPipelineOptions (processing pipeline)
   ├─→ Layout Detection (Granite-258M model)
   ├─→ Table Structure (TableFormer model)
   ├─→ OCR (EasyOCR/Tesseract/etc)
   ├─→ Image Processing
   └─→ Enrichment (optional)
   ↓
DoclingDocument (output)
   ├─→ export_to_json()
   ├─→ export_to_markdown()
   └─→ export_to_dict()
```

---

## Pipeline Configuration

### Basic Structure

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Create pipeline options
pipeline_options = PdfPipelineOptions()

# Configure converter with pipeline
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)
```

### PdfPipelineOptions - All Parameters

```python
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    EasyOcrOptions,
    AcceleratorOptions,
    AcceleratorDevice
)

pipeline_options = PdfPipelineOptions(
    # ═══════════════════════════════════════════════════════════
    # LAYOUT DETECTION
    # ═══════════════════════════════════════════════════════════
    do_ocr=True,  # Enable OCR for scanned documents
    do_table_structure=True,  # Extract table structure

    # ═══════════════════════════════════════════════════════════
    # TABLE EXTRACTION (see detailed section below)
    # ═══════════════════════════════════════════════════════════
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.ACCURATE,  # FAST or ACCURATE
        do_cell_matching=True
    ),

    # ═══════════════════════════════════════════════════════════
    # OCR CONFIGURATION (see detailed section below)
    # ═══════════════════════════════════════════════════════════
    ocr_options=EasyOcrOptions(
        lang=["en"],  # Language codes
        use_gpu=True
    ),

    # ═══════════════════════════════════════════════════════════
    # GPU/CPU ACCELERATION (see detailed section below)
    # ═══════════════════════════════════════════════════════════
    accelerator_options=AcceleratorOptions(
        num_threads=4,
        device=AcceleratorDevice.CUDA  # or CPU, MPS (Mac)
    ),

    # ═══════════════════════════════════════════════════════════
    # IMAGE PROCESSING
    # ═══════════════════════════════════════════════════════════
    generate_page_images=False,  # Save page images
    generate_picture_images=True,  # Extract pictures
    generate_table_images=False,  # Save table images
    images_scale=1.0,  # Image scaling (0.5 = half size)

    # ═══════════════════════════════════════════════════════════
    # PERFORMANCE TUNING
    # ═══════════════════════════════════════════════════════════
    artifacts_path=None,  # Where to save artifacts
)
```

---

## Table Extraction Options

### TableStructureOptions - Complete Configuration

```python
from docling.datamodel.pipeline_options import (
    TableStructureOptions,
    TableFormerMode
)

table_options = TableStructureOptions(
    # ═══════════════════════════════════════════════════════════
    # MODE SELECTION
    # ═══════════════════════════════════════════════════════════
    mode=TableFormerMode.ACCURATE,  # or TableFormerMode.FAST

    # ═══════════════════════════════════════════════════════════
    # CELL MATCHING
    # ═══════════════════════════════════════════════════════════
    do_cell_matching=True,  # Match text to table cells
)
```

### TableFormer Modes Comparison

| Feature | FAST Mode | ACCURATE Mode |
|---------|-----------|---------------|
| **Accuracy** | 90-95% | 97.9% |
| **Speed** | ~2.5 pages/sec | ~2.0 pages/sec |
| **VRAM Usage** | ~400 MB | ~800 MB |
| **Best for** | Simple tables | Complex tables |
| **Merged cells** | Basic support | Full support |
| **Nested tables** | Limited | Good |

**When to use FAST**:
- Simple tables with clear boundaries
- Need maximum speed
- Limited GPU memory (4GB)
- Tables without merged cells

**When to use ACCURATE**:
- Complex table structures
- Tables with merged cells
- Nested or spanning cells
- Maximum accuracy required
- 6GB+ GPU available

### Example: Table Configuration

```python
# Lightweight mode (saves ~400 MB VRAM)
table_options_light = TableStructureOptions(
    mode=TableFormerMode.FAST,
    do_cell_matching=True
)

# Maximum accuracy mode
table_options_accurate = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,
    do_cell_matching=True
)

# Disable table extraction entirely
pipeline_options = PdfPipelineOptions(
    do_table_structure=False  # No table processing
)
```

---

## OCR Configuration

### EasyOcrOptions - Complete Configuration

```python
from docling.datamodel.pipeline_options import EasyOcrOptions

ocr_options = EasyOcrOptions(
    # ═══════════════════════════════════════════════════════════
    # LANGUAGE SELECTION
    # ═══════════════════════════════════════════════════════════
    lang=["en"],  # English only
    # lang=["es"],  # Spanish
    # lang=["en", "es"],  # English + Spanish
    # lang=["en", "es", "fr", "de"],  # Multiple languages

    # ═══════════════════════════════════════════════════════════
    # GPU ACCELERATION
    # ═══════════════════════════════════════════════════════════
    use_gpu=True,  # Use GPU if available

    # ═══════════════════════════════════════════════════════════
    # MEMORY IMPACT
    # ═══════════════════════════════════════════════════════════
    # OCR uses ~1.5 GB VRAM with one language
    # Add ~200-300 MB per additional language
)
```

### Supported OCR Engines

Docling supports multiple OCR backends:

```python
# 1. EasyOCR (default, best accuracy)
from docling.datamodel.pipeline_options import EasyOcrOptions
ocr_options = EasyOcrOptions(lang=["en"])

# 2. Tesseract (faster, less accurate)
from docling.datamodel.pipeline_options import TesseractOcrOptions
ocr_options = TesseractOcrOptions(lang="eng")

# 3. RapidOCR (fastest, good accuracy)
from docling.datamodel.pipeline_options import RapidOcrOptions
ocr_options = RapidOcrOptions()

# 4. Disable OCR (for native PDF text only)
pipeline_options = PdfPipelineOptions(
    do_ocr=False  # Saves ~1.5 GB VRAM
)
```

### OCR Language Codes

Common language codes for EasyOCR:

```python
# English
lang=["en"]

# Spanish
lang=["es"]

# Portuguese
lang=["pt"]

# French
lang=["fr"]

# German
lang=["de"]

# Multiple languages (OCR will auto-detect)
lang=["en", "es", "pt"]  # English, Spanish, Portuguese
```

**Memory impact**: Each language adds ~200-300 MB to VRAM usage.

---

## Accelerator Options (GPU/CPU)

### AcceleratorOptions - Complete Configuration

```python
from docling.datamodel.pipeline_options import (
    AcceleratorOptions,
    AcceleratorDevice
)

# ═══════════════════════════════════════════════════════════
# GPU ACCELERATION (CUDA)
# ═══════════════════════════════════════════════════════════
accelerator_gpu = AcceleratorOptions(
    num_threads=4,  # CPU threads for parallel processing
    device=AcceleratorDevice.CUDA  # Use NVIDIA GPU
)

# ═══════════════════════════════════════════════════════════
# CPU MODE (No GPU)
# ═══════════════════════════════════════════════════════════
accelerator_cpu = AcceleratorOptions(
    num_threads=8,  # More threads for CPU-only
    device=AcceleratorDevice.CPU  # CPU only
)

# ═══════════════════════════════════════════════════════════
# APPLE SILICON (Mac M1/M2/M3)
# ═══════════════════════════════════════════════════════════
accelerator_mps = AcceleratorOptions(
    num_threads=4,
    device=AcceleratorDevice.MPS  # Metal Performance Shaders
)

# ═══════════════════════════════════════════════════════════
# AUTO DETECTION (default)
# ═══════════════════════════════════════════════════════════
accelerator_auto = AcceleratorOptions(
    num_threads=4,
    device=AcceleratorDevice.AUTO  # Docling picks best device
)
```

### Device Selection Strategy

```python
# Check available devices
import torch

if torch.cuda.is_available():
    device = AcceleratorDevice.CUDA
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM available: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
elif torch.backends.mps.is_available():
    device = AcceleratorDevice.MPS
    print("Using Apple Silicon GPU")
else:
    device = AcceleratorDevice.CPU
    print("Using CPU (slower but always works)")
```

### Performance Comparison

| Device | Speed (pages/sec) | Memory | When to Use |
|--------|------------------|---------|-------------|
| **CUDA (6GB+ GPU)** | 2.0-2.5 | 4-6 GB VRAM | Best performance |
| **CUDA (4GB GPU)** | 2.0-2.5 | Use lightweight mode | Limited VRAM |
| **MPS (Mac M1/M2)** | 1.5-2.0 | Unified memory | Apple Silicon |
| **CPU** | 0.2-0.3 | 400 MB RAM | No GPU, 10x slower |

---

## Image Processing

### Image-Related Options

```python
pipeline_options = PdfPipelineOptions(
    # ═══════════════════════════════════════════════════════════
    # IMAGE GENERATION
    # ═══════════════════════════════════════════════════════════
    generate_page_images=False,  # Save entire page as image
    generate_picture_images=True,  # Extract pictures from PDF
    generate_table_images=False,  # Save tables as images

    # ═══════════════════════════════════════════════════════════
    # IMAGE SCALING (memory optimization)
    # ═══════════════════════════════════════════════════════════
    images_scale=1.0,  # Full resolution
    # images_scale=0.5,  # Half resolution (saves memory)
    # images_scale=0.25,  # Quarter resolution

    # ═══════════════════════════════════════════════════════════
    # ARTIFACTS PATH
    # ═══════════════════════════════════════════════════════════
    artifacts_path=None,  # Don't save artifacts
    # artifacts_path=Path("./artifacts"),  # Save to folder
)
```

### Memory Impact

| Option | VRAM/RAM Impact | Use Case |
|--------|----------------|----------|
| `generate_page_images=True` | +200-500 MB | Need page screenshots |
| `generate_picture_images=True` | +50-100 MB | Extract diagrams/photos |
| `generate_table_images=True` | +50-100 MB | Table visualization |
| `images_scale=0.5` | -50% image memory | 4GB GPU optimization |
| `artifacts_path=None` | No disk space | Don't need image files |

---

## Page Range and Limits

### DocumentConverter.convert() Parameters

```python
result = converter.convert(
    source="document.pdf",  # PDF path

    # ═══════════════════════════════════════════════════════════
    # PAGE RANGE
    # ═══════════════════════════════════════════════════════════
    page_range=(1, 50),  # Process pages 1-50
    # page_range=(10, 20),  # Process pages 10-20

    # ═══════════════════════════════════════════════════════════
    # LIMITS
    # ═══════════════════════════════════════════════════════════
    max_num_pages=100,  # Maximum pages to process
    max_file_size=100_000_000,  # Max file size (100 MB)

    # ═══════════════════════════════════════════════════════════
    # ERROR HANDLING
    # ═══════════════════════════════════════════════════════════
    raises_on_error=True,  # Raise exception on error
    # raises_on_error=False,  # Continue on error
)
```

### Filtering After Extraction

```python
# Extract entire document
result = converter.convert("document.pdf")

# Filter specific pages from results
chapter_1_items = []
for item, level in result.document.iterate_items():
    if hasattr(item, 'prov') and item.prov:
        for prov in item.prov:
            if 1 <= prov.page_no <= 11:  # Chapter 1 pages
                chapter_1_items.append(item)
                break
```

---

## Export Configuration

### 1. JSON Export

```python
result.document.save_as_json(
    filename="output.json",

    # ═══════════════════════════════════════════════════════════
    # FORMATTING
    # ═══════════════════════════════════════════════════════════
    indent=2,  # Pretty print (None = compact)

    # ═══════════════════════════════════════════════════════════
    # PRECISION
    # ═══════════════════════════════════════════════════════════
    coord_precision=2,  # Decimal places for coordinates
    confid_precision=2,  # Decimal places for confidence

    # ═══════════════════════════════════════════════════════════
    # IMAGE HANDLING
    # ═══════════════════════════════════════════════════════════
    image_mode=ImageRefMode.EMBEDDED,  # Embed images in JSON
    # image_mode=ImageRefMode.REFERENCED,  # Reference external files
    # image_mode=ImageRefMode.PLACEHOLDER,  # Placeholder text

    # ═══════════════════════════════════════════════════════════
    # ARTIFACTS
    # ═══════════════════════════════════════════════════════════
    artifacts_dir=None,  # No artifacts folder
    # artifacts_dir=Path("./images"),  # Save images here
)
```

### 2. Markdown Export

```python
markdown = result.document.export_to_markdown(
    # ═══════════════════════════════════════════════════════════
    # CONTENT SELECTION
    # ═══════════════════════════════════════════════════════════
    page_no=None,  # All pages
    # page_no=5,  # Only page 5

    from_element=0,  # Start from first element
    to_element=9999999,  # To last element

    labels=None,  # All element types
    # labels={DocItemLabel.TEXT, DocItemLabel.TABLE},  # Only text and tables

    # ═══════════════════════════════════════════════════════════
    # FORMATTING
    # ═══════════════════════════════════════════════════════════
    delim="\n\n",  # Delimiter between elements
    strict_text=False,  # Include formatting
    indent=4,  # Indentation spaces
    text_width=-1,  # No text wrapping (-1 = disabled)

    # ═══════════════════════════════════════════════════════════
    # TABLES
    # ═══════════════════════════════════════════════════════════
    enable_chart_tables=True,  # Include tables

    # ═══════════════════════════════════════════════════════════
    # ESCAPING
    # ═══════════════════════════════════════════════════════════
    escape_html=True,  # Escape HTML characters
    escape_underscores=True,  # Escape underscores

    # ═══════════════════════════════════════════════════════════
    # IMAGES
    # ═══════════════════════════════════════════════════════════
    image_placeholder="<!-- image -->",  # Image placeholder
    image_mode=ImageRefMode.PLACEHOLDER,

    # ═══════════════════════════════════════════════════════════
    # PAGE BREAKS
    # ═══════════════════════════════════════════════════════════
    page_break_placeholder=None,  # No page breaks
    # page_break_placeholder="\n---\n",  # Page break marker
)
```

### 3. Dictionary Export

```python
doc_dict = result.document.export_to_dict(
    # ═══════════════════════════════════════════════════════════
    # MODE
    # ═══════════════════════════════════════════════════════════
    mode='json',  # JSON-compatible dict
    # mode='python',  # Python native types

    # ═══════════════════════════════════════════════════════════
    # OPTIONS
    # ═══════════════════════════════════════════════════════════
    by_alias=True,  # Use field aliases
    exclude_none=True,  # Skip null values

    # ═══════════════════════════════════════════════════════════
    # PRECISION
    # ═══════════════════════════════════════════════════════════
    coord_precision=2,
    confid_precision=2,
)
```

---

## Complete Examples

### Example 1: Lightweight Mode (4GB GPU)

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions,
    AcceleratorDevice
)

# Lightweight configuration (uses ~1.3 GB VRAM)
pipeline_options = PdfPipelineOptions(
    do_ocr=False,  # Disable OCR (saves 1.5 GB)
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,  # FAST mode (saves 400 MB)
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=4,
        device=AcceleratorDevice.CUDA
    ),
    generate_page_images=False,
    generate_picture_images=True,
    generate_table_images=False,
    images_scale=0.5,  # Half resolution
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("document.pdf")
result.document.save_as_json("output.json")
```

### Example 2: Maximum Accuracy Mode (6GB+ GPU)

```python
# Maximum accuracy configuration (uses ~4.2 GB VRAM)
pipeline_options = PdfPipelineOptions(
    do_ocr=True,  # Enable OCR
    ocr_options=EasyOcrOptions(lang=["en"]),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.ACCURATE,  # 97.9% accuracy
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=4,
        device=AcceleratorDevice.CUDA
    ),
    generate_page_images=False,
    generate_picture_images=True,
    generate_table_images=True,  # Save table images
    images_scale=1.0,  # Full resolution
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("document.pdf")
result.document.save_as_json("output.json", indent=2)
```

### Example 3: CPU-Only Mode (No GPU)

```python
# CPU-only configuration (uses ~400 MB RAM, 10x slower)
pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=EasyOcrOptions(lang=["en"], use_gpu=False),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,
        do_cell_matching=True
    ),
    accelerator_options=AcceleratorOptions(
        num_threads=8,  # More threads for CPU
        device=AcceleratorDevice.CPU
    ),
    generate_page_images=False,
    generate_picture_images=True,
    generate_table_images=False,
    images_scale=0.5,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("document.pdf", page_range=(1, 50))
```

### Example 4: Multi-Language OCR (Spanish + English)

```python
pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=EasyOcrOptions(
        lang=["es", "en"],  # Spanish + English
        use_gpu=True
    ),
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

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("documento_español.pdf")
```

---

## Performance Tuning

### Memory Optimization Strategies

| Configuration | VRAM Usage | Speed Impact | Use Case |
|--------------|------------|--------------|----------|
| **Disable OCR** | -1.5 GB | None | Native PDF text only |
| **FAST tables** | -400 MB | +20% faster | Simple tables |
| **Disable page images** | -200 MB | None | Don't need page screenshots |
| **Disable table images** | -50 MB | None | Don't need table images |
| **images_scale=0.5** | -50% | None | Reduce image resolution |
| **lang=["en"] only** | -600 MB | None | Single language vs 3 |

### Speed Optimization Strategies

| Configuration | Speed Gain | Accuracy Impact |
|--------------|------------|-----------------|
| **FAST table mode** | +20% | 90-95% vs 97.9% |
| **Disable OCR** | +10% | None (native text) |
| **page_range** | Linear | None |
| **CPU threads=8** | +30% (CPU) | None |
| **Batch processing** | N/A | Use parallel workers |

### Recommended Configurations

**4GB GPU (GTX 1650, RTX 3050)**:
```python
do_ocr=False, table_mode=FAST, images_scale=0.5
# Uses: ~1.3 GB VRAM
```

**6GB GPU (RTX 2060, GTX 1660 Ti)**:
```python
do_ocr=True, lang=["en"], table_mode=FAST
# Uses: ~2.5 GB VRAM
```

**8GB+ GPU (RTX 3060, 3070, 4060)**:
```python
do_ocr=True, lang=["en", "es"], table_mode=ACCURATE
# Uses: ~4.2 GB VRAM
```

**CPU Only (No GPU)**:
```python
device=CPU, num_threads=8, table_mode=FAST, images_scale=0.5
# Uses: ~400 MB RAM, 10x slower
```

---

## Summary: Key Configuration Points

### 1. Table Extraction
- **FAST mode**: 90-95% accuracy, saves 400 MB
- **ACCURATE mode**: 97.9% accuracy, uses 800 MB
- Use `do_cell_matching=True` for cell text

### 2. OCR
- Disable for native PDF text (saves 1.5 GB)
- Use `lang=["en"]` for single language
- Each language adds ~200-300 MB

### 3. GPU/CPU
- **CUDA**: Best performance, needs NVIDIA GPU
- **MPS**: Apple Silicon (M1/M2/M3)
- **CPU**: Fallback, 10x slower, always works

### 4. Export
- `save_as_json()`: Complete data (best)
- `export_to_markdown()`: Human-readable
- `export_to_dict()`: Python processing

### 5. Memory
- Lightweight: ~1.3 GB (4GB GPU)
- Standard: ~2.5 GB (6GB GPU)
- Maximum: ~4.2 GB (8GB+ GPU)
- CPU: ~400 MB RAM

---

**Last Updated**: 2025-10-26
**Docling Version**: Latest (Granite-258M + TableFormer)
