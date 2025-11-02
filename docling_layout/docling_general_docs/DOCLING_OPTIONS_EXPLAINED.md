# Docling Options - Complete Guide

A comprehensive explanation of all Docling configuration options, what they do, and how they affect memory, speed, and output quality.

---

## 📋 Table of Contents

1. [Core Processing Options](#core-processing-options)
2. [Accelerator Options](#accelerator-options)
3. [OCR Options](#ocr-options)
4. [Table Options](#table-options)
5. [Image Options](#image-options)
6. [Enrichment Options](#enrichment-options)
7. [Layout Options](#layout-options)
8. [Practical Examples](#practical-examples)

---

## Core Processing Options

### `do_ocr` (bool, default=True)

**What it does**: Performs Optical Character Recognition on images and scanned text.

**Memory**: ~1.5 GB (EasyOCR model)

**When to use**:
- ✅ Scanned PDFs (images of documents)
- ✅ Screenshots in documents
- ✅ Images with embedded text
- ✅ Hand-written text (limited accuracy)

**When to disable**:
- ❌ Native PDF text (searchable PDFs)
- ❌ Limited GPU memory (biggest memory saver!)
- ❌ Speed is critical

**Your case**: EAF reports have **native PDF text** → Can disable to save 1.5 GB

```python
pipeline_options = PdfPipelineOptions(
    do_ocr=False  # ← Saves 1.5 GB!
)
```

**CLI**:
```bash
docling input.pdf --no-ocr
```

---

### `do_table_structure` (bool, default=True)

**What it does**: Detects tables and extracts their structure (rows, columns, cells).

**Memory**: ~800 MB (ACCURATE mode) or ~400 MB (FAST mode)

**When to use**:
- ✅ Documents with tables (your case!)
- ✅ Need structured data extraction
- ✅ CSV/Excel export from tables

**When to disable**:
- ❌ No tables in document
- ❌ Only need layout detection

**Accuracy**: 97.9% (ACCURATE mode), ~95% (FAST mode)

```python
pipeline_options = PdfPipelineOptions(
    do_table_structure=True,  # Keep this for EAF reports
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST  # ← Use FAST to save 400 MB
    )
)
```

**CLI**:
```bash
docling input.pdf --tables           # Enable (default)
docling input.pdf --no-tables        # Disable
docling input.pdf --table-mode fast  # Fast mode
```

---

### `force_backend_text` (bool, default=False)

**What it does**: Uses raw PDF text from backend instead of Docling's processed text.

**Memory**: No impact

**When to use**:
- ✅ Trust PDF's embedded text more than OCR
- ✅ Faster processing
- ✅ Native PDF text is high quality

**When to disable**:
- ❌ PDF text has encoding issues
- ❌ Need Docling's text cleanup

```python
pipeline_options = PdfPipelineOptions(
    force_backend_text=True  # Use native PDF text
)
```

---

## Accelerator Options

Controls GPU/CPU usage and threading.

### `AcceleratorOptions`

```python
from docling.datamodel.accelerator_options import AcceleratorOptions

accelerator_options = AcceleratorOptions(
    num_threads=4,              # Number of CPU threads (default: 4)
    device="auto",              # "auto", "cpu", "cuda", "mps"
    cuda_use_flash_attention2=False  # Use Flash Attention v2 (faster)
)

pipeline_options = PdfPipelineOptions(
    accelerator_options=accelerator_options
)
```

#### `device` Options:

| Device | Use When | Performance |
|--------|----------|-------------|
| `"auto"` | Default - auto-detect GPU | Best available |
| `"cuda"` | Force NVIDIA GPU | Fast (needs 2-6 GB VRAM) |
| `"cpu"` | No GPU or GPU too small | Slow but stable |
| `"mps"` | Apple Silicon (M1/M2/M3) | Fast on Mac |

#### `num_threads`:
- **Default**: 4 threads
- **Lower** (1-2): Reduces CPU load, slower
- **Higher** (8-16): Faster if you have CPU cores
- **Your case**: Use 2 threads to reduce overhead

```python
# For 4GB GPU
accelerator_options = AcceleratorOptions(
    num_threads=2,    # Lower overhead
    device="cuda"     # Use GPU
)
```

**CLI**:
```bash
docling input.pdf --device cuda      # Force GPU
docling input.pdf --device cpu       # Force CPU
docling input.pdf --num-threads 2    # Reduce threads
```

**Environment variable**:
```bash
export OMP_NUM_THREADS=2  # Set before running
docling input.pdf
```

---

## OCR Options

### `ocr_options` (OcrOptions)

Controls OCR engine behavior when `do_ocr=True`.

```python
from docling.datamodel.pipeline_options import EasyOcrOptions

ocr_options = EasyOcrOptions(
    lang=['en'],                    # Languages (default: ['en', 'es', 'fr', 'de'])
    force_full_page_ocr=False,      # OCR entire page vs only images
    bitmap_area_threshold=0.05,     # Min area to trigger OCR (5%)
    use_gpu=True,                   # Use GPU for OCR
    confidence_threshold=0.5,       # Min confidence (0-1)
)

pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=ocr_options
)
```

#### Key Parameters:

**`lang`** (list of strings):
- Available: `'en'`, `'es'`, `'fr'`, `'de'`, `'pt'`, `'it'`, `'zh_sim'`, etc.
- **Memory impact**: More languages = more memory
- **Recommendation**: Use only languages in your documents

```python
# English only (saves memory)
ocr_options = EasyOcrOptions(lang=['en'])

# Spanish + English
ocr_options = EasyOcrOptions(lang=['es', 'en'])
```

**`force_full_page_ocr`** (bool, default=False):
- `False`: OCR only image regions (efficient)
- `True`: OCR entire page even if text exists (slow, memory-heavy)

**`use_gpu`** (bool/None, default=None):
- `None`: Auto-detect
- `True`: Force GPU (faster)
- `False`: Force CPU (slower but stable)

**CLI**:
```bash
docling input.pdf --ocr-lang en,es     # Multiple languages
docling input.pdf --force-ocr          # Force full-page OCR
docling input.pdf --ocr-engine easyocr # Choose engine
```

---

## Table Options

### `table_structure_options` (TableStructureOptions)

```python
from docling.datamodel.pipeline_options import TableStructureOptions, TableFormerMode

table_options = TableStructureOptions(
    do_cell_matching=True,          # Match cells to layout
    mode=TableFormerMode.ACCURATE   # ACCURATE or FAST
)

pipeline_options = PdfPipelineOptions(
    do_table_structure=True,
    table_structure_options=table_options
)
```

#### `mode` - TableFormerMode:

| Mode | Memory | Accuracy | Speed | Use When |
|------|--------|----------|-------|----------|
| `ACCURATE` | 800 MB | 97.9% | Slower | Production, complex tables |
| `FAST` | 400 MB | ~95% | Faster | Limited GPU, simple tables |

**Difference**: 2.9% accuracy, 400 MB memory, 10-20% speed

```python
# For 4GB GPU - use FAST
table_options = TableStructureOptions(
    mode=TableFormerMode.FAST  # ← Saves 400 MB
)
```

#### `do_cell_matching` (bool, default=True):
- `True`: Match detected cells to layout boxes (more accurate)
- `False`: Skip cell matching (faster, less accurate)

**CLI**:
```bash
docling input.pdf --table-mode accurate  # High accuracy
docling input.pdf --table-mode fast      # Lower memory
```

---

## Image Options

### Image Generation Flags

```python
pipeline_options = PdfPipelineOptions(
    generate_page_images=False,      # Generate page image files
    generate_picture_images=False,   # Generate picture image files
    generate_table_images=False,     # Generate table image files (deprecated)
    generate_parsed_pages=False,     # Generate parsed page objects
    images_scale=1.0                 # Image scaling factor (0.5 = half size)
)
```

#### Memory Impact:

| Option | Memory per page | Use When |
|--------|-----------------|----------|
| `generate_page_images=True` | ~100 MB | Need page screenshots |
| `generate_picture_images=True` | ~50 MB | Extract embedded images |
| `generate_table_images=True` | ~50 MB | Visualize table detection |
| All disabled | Saves ~200 MB | Don't need images |

#### `images_scale` (float, default=1.0):
- `1.0`: Original size
- `0.5`: Half size (saves memory)
- `2.0`: Double size (high quality screenshots)

```python
# For 4GB GPU - disable all
pipeline_options = PdfPipelineOptions(
    generate_page_images=False,
    generate_picture_images=False,
    generate_table_images=False,
    images_scale=0.5  # If you do need images, scale down
)
```

**CLI**:
```bash
docling input.pdf --no-show-layout     # Don't generate layout images
```

---

## Enrichment Options

These add extra processing on top of basic extraction.

### `do_picture_classification` (bool, default=False)

**What it does**: Classifies images (chart, diagram, photo, illustration, etc.)

**Memory**: ~100 MB

**Output**: Adds `classification` field to image elements

```python
pipeline_options = PdfPipelineOptions(
    do_picture_classification=True  # Enable image classification
)
```

**CLI**:
```bash
docling input.pdf --enrich-picture-classification
```

---

### `do_picture_description` (bool, default=False)

**What it does**: Generates text descriptions of images using VLM (Vision Language Model)

**Memory**: ~200 MB (SmolVLM-256M model)

**Output**: Adds `description` field with image caption

**Example output**: "A bar chart showing monthly sales data from January to December"

```python
pipeline_options = PdfPipelineOptions(
    do_picture_description=True,
    picture_description_options=PictureDescriptionVlmOptions(
        batch_size=8,                   # Process 8 images at once
        scale=2,                        # Image resolution
        picture_area_threshold=0.05,    # Min size (5% of page)
        repo_id='HuggingFaceTB/SmolVLM-256M-Instruct',
        prompt='Describe this image in a few sentences.',
        generation_config={'max_new_tokens': 200}
    )
)
```

**CLI**:
```bash
docling input.pdf --enrich-picture-description
```

---

### `do_code_enrichment` (bool, default=False)

**What it does**: Detects and highlights code blocks with syntax

**Memory**: ~150 MB

**Languages**: Auto-detects Python, JavaScript, Java, C++, etc.

```python
pipeline_options = PdfPipelineOptions(
    do_code_enrichment=True  # Enable code detection
)
```

**CLI**:
```bash
docling input.pdf --enrich-code
```

**Your case**: EAF reports have no code → Disable to save 150 MB

---

### `do_formula_enrichment` (bool, default=False)

**What it does**: Extracts mathematical formulas and converts to LaTeX

**Memory**: ~150 MB

**Output**: Formulas as LaTeX code (e.g., `$E = mc^2$`)

```python
pipeline_options = PdfPipelineOptions(
    do_formula_enrichment=True  # Enable formula extraction
)
```

**CLI**:
```bash
docling input.pdf --enrich-formula
```

**Your case**: EAF reports have some equations, but PyMuPDF can extract → Optional

---

## Layout Options

### `layout_options` (LayoutOptions)

Advanced layout detection configuration.

```python
from docling.datamodel.pipeline_options import LayoutOptions

layout_options = LayoutOptions(
    create_orphan_clusters=True,   # Cluster elements without clear parent
    keep_empty_clusters=False,     # Keep empty layout regions
    skip_cell_assignment=False     # Skip assigning cells to layouts
)

pipeline_options = PdfPipelineOptions(
    layout_options=layout_options
)
```

**Usually don't need to change these** - defaults work well.

---

## Document-Level Options

### `document_timeout` (float, default=None)

**What it does**: Timeout in seconds for processing each document

```python
pipeline_options = PdfPipelineOptions(
    document_timeout=1800  # 30 minutes max
)
```

**CLI**:
```bash
docling input.pdf --document-timeout 1800
```

---

### `enable_remote_services` (bool, default=False)

**What it does**: Allow models to connect to remote APIs (e.g., cloud-based VLMs)

**Security**: Disable for sensitive documents

```python
pipeline_options = PdfPipelineOptions(
    enable_remote_services=False  # No external API calls
)
```

**CLI**:
```bash
docling input.pdf --enable-remote-services  # Enable
```

---

### `artifacts_path` (Path/str, default=None)

**What it does**: Custom path for model storage

**Default**: `~/.cache/docling/`

```python
pipeline_options = PdfPipelineOptions(
    artifacts_path="/path/to/models"  # Custom model location
)
```

**CLI**:
```bash
docling input.pdf --artifacts-path /path/to/models
```

---

## Practical Examples

### Example 1: Lightweight (1.3 GB) - For 4GB GPU

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)

pipeline_options = PdfPipelineOptions(
    # GPU settings
    accelerator_options=AcceleratorOptions(
        num_threads=2,
        device="cuda",
    ),

    # Disable heavy models
    do_ocr=False,                      # ← Saves 1.5 GB
    do_picture_classification=False,   # Saves 100 MB
    do_picture_description=False,      # Saves 200 MB
    do_code_enrichment=False,          # Saves 150 MB
    do_formula_enrichment=False,       # Saves 150 MB

    # Fast table mode
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,     # ← Saves 400 MB
        do_cell_matching=True,
    ),

    # No image generation
    generate_page_images=False,        # Saves 100 MB
    generate_picture_images=False,     # Saves 50 MB
    generate_table_images=False,       # Saves 50 MB
    images_scale=0.5,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("document.pdf")
```

**Total memory**: ~1.3 GB ✅ Fits on 4GB GPU

---

### Example 2: Balanced (2.0 GB) - With OCR

```python
pipeline_options = PdfPipelineOptions(
    # GPU settings
    accelerator_options=AcceleratorOptions(
        num_threads=2,
        device="cuda",
    ),

    # Keep OCR (English only)
    do_ocr=True,
    ocr_options=EasyOcrOptions(
        lang=['en'],                   # ← Only English saves memory
        force_full_page_ocr=False,
        use_gpu=True,
    ),

    # Fast tables
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST,
        do_cell_matching=True,
    ),

    # Disable enrichment
    do_picture_classification=False,
    do_picture_description=False,
    do_code_enrichment=False,
    do_formula_enrichment=False,

    # No images
    generate_page_images=False,
    generate_picture_images=False,
    generate_table_images=False,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

**Total memory**: ~2.0 GB ✅ Might fit on 4GB GPU

---

### Example 3: Full Features (4.2 GB) - Needs 8GB+ GPU

```python
pipeline_options = PdfPipelineOptions(
    # GPU settings
    accelerator_options=AcceleratorOptions(
        num_threads=4,
        device="cuda",
    ),

    # All features enabled
    do_ocr=True,
    ocr_options=EasyOcrOptions(
        lang=['en', 'es', 'fr', 'de'],  # Multiple languages
        force_full_page_ocr=False,
        use_gpu=True,
    ),

    # Accurate tables
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.ACCURATE,  # ← Best accuracy
        do_cell_matching=True,
    ),

    # All enrichment
    do_picture_classification=True,
    do_picture_description=True,
    do_code_enrichment=True,
    do_formula_enrichment=True,

    # Generate images
    generate_page_images=True,
    generate_picture_images=True,
    images_scale=1.0,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

**Total memory**: ~4.2 GB ❌ Won't fit on 4GB GPU

---

### Example 4: CPU Mode (Slow but Safe)

```python
pipeline_options = PdfPipelineOptions(
    # CPU only
    accelerator_options=AcceleratorOptions(
        num_threads=4,
        device="cpu",  # ← Force CPU
    ),

    # All features work on CPU
    do_ocr=True,
    do_table_structure=True,
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.ACCURATE,
    ),
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

**Memory**: ~400 MB RAM (not VRAM)
**Speed**: 10x slower than GPU
**Stability**: 100% reliable

---

## CLI Quick Reference

### Memory-Saving Options:
```bash
--no-ocr                              # Disable OCR (saves 1.5 GB)
--table-mode fast                     # Fast tables (saves 400 MB)
--no-enrich-picture-classification    # Disable image classification (saves 100 MB)
--no-enrich-picture-description       # Disable image captions (saves 200 MB)
--no-enrich-code                      # Disable code highlighting (saves 150 MB)
--no-enrich-formula                   # Disable formula extraction (saves 150 MB)
```

### Device Options:
```bash
--device cuda       # Force GPU
--device cpu        # Force CPU
--device auto       # Auto-detect
--num-threads 2     # Reduce CPU threads
```

### Output Options:
```bash
--to json           # JSON output
--to md             # Markdown output
--to html           # HTML output
--output dir/       # Output directory
```

### Full Lightweight Command:
```bash
docling document.pdf \
  --device cuda \
  --no-ocr \
  --table-mode fast \
  --no-enrich-picture-classification \
  --no-enrich-picture-description \
  --no-enrich-code \
  --no-enrich-formula \
  --to json \
  --output outputs/
```

---

## Summary Table

| Option | Memory Saved | When to Disable |
|--------|--------------|-----------------|
| `do_ocr=False` | **1.5 GB** ⭐ | Native PDF text |
| `table FAST mode` | **400 MB** | Simple tables |
| `do_picture_description=False` | **200 MB** | Don't need captions |
| `do_code_enrichment=False` | **150 MB** | No code in docs |
| `do_formula_enrichment=False` | **150 MB** | No formulas |
| `generate_*_images=False` | **200 MB** | Don't need images |
| `do_picture_classification=False` | **100 MB** | Don't need image types |
| **Total possible savings** | **2.9 GB** | From 4.2 GB → 1.3 GB |

---

## Recommendations for Your 4GB GPU

### ✅ Use This Configuration:

```python
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(num_threads=2, device="cuda"),
    do_ocr=False,                      # Your PDFs have native text
    do_table_structure=True,           # Keep for EAF tables
    table_structure_options=TableStructureOptions(mode=TableFormerMode.FAST),
    do_picture_classification=False,
    do_picture_description=False,
    do_code_enrichment=False,          # No code in EAF reports
    do_formula_enrichment=False,
    generate_page_images=False,
    generate_picture_images=False,
    generate_table_images=False,
)
```

**Result**: 1.3 GB memory usage ✅ Perfect for 4GB GPU!

---

Ready to use? Run `lightweight_extract.py` which uses this exact configuration! 🚀
