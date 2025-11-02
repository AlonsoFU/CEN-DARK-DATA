# Docling Options - Cheat Sheet

Quick reference for all Docling configuration options.

---

## 🎛️ Main Processing Options

### Boolean Switches (Enable/Disable Features)

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions(
    # ═══════════════════════════════════════════════════════
    # TEXT & OCR
    # ═══════════════════════════════════════════════════════
    do_ocr=False,                    # Extract text from images (1.5 GB)
    force_backend_text=False,        # Use PDF's native text instead of processed

    # ═══════════════════════════════════════════════════════
    # TABLES
    # ═══════════════════════════════════════════════════════
    do_table_structure=True,         # Detect table structure (400-800 MB)

    # ═══════════════════════════════════════════════════════
    # IMAGE ANALYSIS
    # ═══════════════════════════════════════════════════════
    do_picture_classification=False, # Classify images (chart/photo/etc) (100 MB)
    do_picture_description=False,    # Generate AI image captions (200 MB)

    # ═══════════════════════════════════════════════════════
    # ENRICHMENT
    # ═══════════════════════════════════════════════════════
    do_code_enrichment=False,        # Syntax highlight code blocks (150 MB)
    do_formula_enrichment=False,     # Extract formulas as LaTeX (150 MB)

    # ═══════════════════════════════════════════════════════
    # IMAGE GENERATION
    # ═══════════════════════════════════════════════════════
    generate_page_images=False,      # Create page screenshots (100 MB)
    generate_picture_images=False,   # Extract embedded images (50 MB)
    generate_table_images=False,     # Visualize table detection (50 MB)
    generate_parsed_pages=False,     # Generate parsed page objects

    # ═══════════════════════════════════════════════════════
    # IMAGE SETTINGS
    # ═══════════════════════════════════════════════════════
    images_scale=1.0,                # Image scaling factor (0.5 = half size)
)
```

---

## ⚙️ Sub-Options (Detailed Configuration)

### 1. Accelerator Options (GPU/CPU Control)

```python
from docling.datamodel.accelerator_options import AcceleratorOptions

accelerator_options = AcceleratorOptions(
    device="cuda",                   # "auto", "cpu", "cuda", "mps"
    num_threads=4,                   # CPU threads (1-16)
    cuda_use_flash_attention2=False  # Faster attention (experimental)
)

pipeline_options = PdfPipelineOptions(
    accelerator_options=accelerator_options
)
```

**Device Options**:
- `"auto"` - Auto-detect best device
- `"cpu"` - Force CPU (slow, stable)
- `"cuda"` - Force NVIDIA GPU (fast, needs VRAM)
- `"mps"` - Apple Silicon GPU (M1/M2/M3)

---

### 2. Table Structure Options

```python
from docling.datamodel.pipeline_options import TableStructureOptions, TableFormerMode

table_options = TableStructureOptions(
    mode=TableFormerMode.FAST,       # FAST or ACCURATE
    do_cell_matching=True            # Match cells to layout
)

pipeline_options = PdfPipelineOptions(
    do_table_structure=True,
    table_structure_options=table_options
)
```

**Modes**:
- `TableFormerMode.ACCURATE` - 97.9% accuracy, 800 MB memory
- `TableFormerMode.FAST` - ~95% accuracy, 400 MB memory

---

### 3. OCR Options

```python
from docling.datamodel.pipeline_options import EasyOcrOptions

ocr_options = EasyOcrOptions(
    lang=['en'],                     # Languages: 'en', 'es', 'fr', 'de', etc.
    force_full_page_ocr=False,       # OCR entire page vs only images
    bitmap_area_threshold=0.05,      # Min area to trigger OCR (5%)
    use_gpu=True,                    # Use GPU for OCR
    confidence_threshold=0.5,        # Min confidence (0-1)
    model_storage_directory=None,    # Custom model path
    recog_network='standard',        # Recognition network
)

pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=ocr_options
)
```

**Common Languages**:
- `'en'` - English
- `'es'` - Spanish
- `'fr'` - French
- `'de'` - German
- `'pt'` - Portuguese
- `'zh_sim'` - Chinese Simplified

---

### 4. Picture Description Options

```python
from docling.datamodel.pipeline_options import PictureDescriptionVlmOptions

picture_options = PictureDescriptionVlmOptions(
    batch_size=8,                    # Process N images at once
    scale=2,                         # Image resolution
    picture_area_threshold=0.05,     # Min size (5% of page)
    repo_id='HuggingFaceTB/SmolVLM-256M-Instruct',  # Model
    prompt='Describe this image in a few sentences.',
    generation_config={'max_new_tokens': 200, 'do_sample': False}
)

pipeline_options = PdfPipelineOptions(
    do_picture_description=True,
    picture_description_options=picture_options
)
```

---

### 5. Layout Options

```python
from docling.datamodel.pipeline_options import LayoutOptions

layout_options = LayoutOptions(
    create_orphan_clusters=True,     # Cluster elements without parent
    keep_empty_clusters=False,       # Keep empty layout regions
    skip_cell_assignment=False       # Skip cell-to-layout assignment
)

pipeline_options = PdfPipelineOptions(
    layout_options=layout_options
)
```

---

### 6. Document-Level Options

```python
pipeline_options = PdfPipelineOptions(
    document_timeout=None,           # Timeout per document (seconds)
    enable_remote_services=False,    # Allow remote API calls
    allow_external_plugins=False,    # Load third-party plugins
    artifacts_path=None,             # Custom model storage path
)
```

---

## 📋 Complete Option List

| Category | Option | Type | Default | Memory Impact |
|----------|--------|------|---------|---------------|
| **OCR** | `do_ocr` | bool | True | 1.5 GB |
| | `ocr_options` | EasyOcrOptions | auto | - |
| | `force_backend_text` | bool | False | 0 |
| **Tables** | `do_table_structure` | bool | True | 400-800 MB |
| | `table_structure_options` | TableStructureOptions | ACCURATE | - |
| **Images** | `do_picture_classification` | bool | False | 100 MB |
| | `do_picture_description` | bool | False | 200 MB |
| | `picture_description_options` | PictureDescriptionVlmOptions | auto | - |
| | `generate_page_images` | bool | False | 100 MB |
| | `generate_picture_images` | bool | False | 50 MB |
| | `generate_table_images` | bool | False | 50 MB |
| | `generate_parsed_pages` | bool | False | - |
| | `images_scale` | float | 1.0 | varies |
| **Enrichment** | `do_code_enrichment` | bool | False | 150 MB |
| | `do_formula_enrichment` | bool | False | 150 MB |
| **Accelerator** | `accelerator_options` | AcceleratorOptions | auto | - |
| **Layout** | `layout_options` | LayoutOptions | defaults | - |
| **Document** | `document_timeout` | float | None | - |
| | `enable_remote_services` | bool | False | - |
| | `allow_external_plugins` | bool | False | - |
| | `artifacts_path` | Path/str | None | - |

---

## 🎯 Quick Configurations

### Minimal (1.3 GB) - For 4GB GPU ⭐

```python
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(num_threads=2, device="cuda"),
    do_ocr=False,
    do_table_structure=True,
    table_structure_options=TableStructureOptions(mode=TableFormerMode.FAST),
    do_picture_classification=False,
    do_picture_description=False,
    do_code_enrichment=False,
    do_formula_enrichment=False,
    generate_page_images=False,
    generate_picture_images=False,
    generate_table_images=False,
)
```

### Balanced (2.0 GB) - With OCR

```python
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(num_threads=2, device="cuda"),
    do_ocr=True,
    ocr_options=EasyOcrOptions(lang=['en'], use_gpu=True),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(mode=TableFormerMode.FAST),
    do_picture_classification=False,
    do_picture_description=False,
    do_code_enrichment=False,
    do_formula_enrichment=False,
    generate_page_images=False,
    generate_picture_images=False,
    generate_table_images=False,
)
```

### Full (4.2 GB) - All Features

```python
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(num_threads=4, device="cuda"),
    do_ocr=True,
    ocr_options=EasyOcrOptions(lang=['en', 'es', 'fr', 'de'], use_gpu=True),
    do_table_structure=True,
    table_structure_options=TableStructureOptions(mode=TableFormerMode.ACCURATE),
    do_picture_classification=True,
    do_picture_description=True,
    do_code_enrichment=True,
    do_formula_enrichment=True,
    generate_page_images=True,
    generate_picture_images=True,
)
```

### CPU Mode - Safe

```python
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(num_threads=4, device="cpu"),
    # All other options can be enabled - runs on RAM
)
```

---

## 🖥️ CLI Options

### Core Options:
```bash
--device cuda|cpu|mps|auto       # Accelerator device
--num-threads N                  # CPU threads
--to json|md|html|text           # Output format
--output DIR                     # Output directory
```

### Processing Options:
```bash
--ocr / --no-ocr                 # Enable/disable OCR
--force-ocr                      # Force full-page OCR
--ocr-lang en,es,fr              # OCR languages
--ocr-engine easyocr             # OCR engine
--tables / --no-tables           # Enable/disable tables
--table-mode fast|accurate       # Table detection mode
```

### Enrichment Options:
```bash
--enrich-picture-classification  # Enable image classification
--enrich-picture-description     # Enable image captions
--enrich-code                    # Enable code highlighting
--enrich-formula                 # Enable formula extraction
```

### Image Options:
```bash
--show-layout                    # Generate layout images
--image-export-mode embedded|referenced|placeholder
```

### Other Options:
```bash
--document-timeout N             # Timeout in seconds
--enable-remote-services         # Allow remote APIs
--allow-external-plugins         # Load third-party plugins
--artifacts-path PATH            # Custom model path
--verbose / -v / -vv             # Logging level
```

---

## 💡 Memory Guide

**Total Available**: 4 GB (your GTX 1650)

**Core (Cannot Disable)**: 1.2 GB
- Layout model

**Optional (Can Configure)**:
- OCR: 1.5 GB (disable if native text)
- Table ACCURATE: 800 MB (use FAST: 400 MB)
- Table FAST: 400 MB
- Picture Description: 200 MB
- Code Enrichment: 150 MB
- Formula Enrichment: 150 MB
- Picture Classification: 100 MB
- Image Generation: 200 MB

**Recommended for 4GB GPU**:
- Core: 1.2 GB
- Table FAST: 0.4 GB
- Everything else: OFF
- **Total: 1.6 GB** ✅

---

## 🚀 Ready to Use

Your script with optimal settings:
```bash
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts
source ../../../../../../venv/bin/activate
python lightweight_extract.py
```

This uses the **Minimal (1.3 GB)** configuration perfect for your GPU!

---

**Quick Links**:
- Full details: `DOCLING_OPTIONS_EXPLAINED.md`
- Visual guide: `OPTIONS_SUMMARY.md`
- Quick start: `QUICK_START.md`
