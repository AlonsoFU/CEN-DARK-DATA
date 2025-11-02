# Complete Docling Configuration Options

**Last Updated**: 2025-10-27
**Purpose**: Reference guide for ALL PdfPipelineOptions parameters

---

## 📋 Current Configuration (Your Setup)

### What You're Using Now:

```python
pipeline_options = PdfPipelineOptions()

# Core settings
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True

# Table settings
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.FAST,  # or ACCURATE
    do_cell_matching=True
)

# GPU settings
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=2,
    device="cuda"
)

# Disabled features (to save VRAM)
pipeline_options.do_picture_classification = False
pipeline_options.do_picture_description = False
pipeline_options.do_code_enrichment = False
pipeline_options.do_formula_enrichment = False
```

**VRAM Usage:**
- FAST tables: ~2000 MB (1600 base + 400 TableFormer)
- ACCURATE tables: ~2400 MB (1600 base + 800 TableFormer)

---

## 🎛️ ALL Available Configuration Options

### 1. Core Processing Options

| Parameter | Type | Default | VRAM Impact | What It Does |
|-----------|------|---------|-------------|--------------|
| **`do_ocr`** | bool | False | +1500 MB | Optical Character Recognition for scanned PDFs/images |
| **`do_table_structure`** | bool | True | +400-800 MB | Table detection and structure extraction |
| **`do_code_enrichment`** | bool | False | +100 MB | Code block detection and syntax highlighting |
| **`do_formula_enrichment`** | bool | False | +300 MB | Mathematical formula extraction (LaTeX) |
| **`do_picture_classification`** | bool | False | +100 MB | Classify images (diagram, photo, chart, etc.) |
| **`do_picture_description`** | bool | False | +200 MB | Generate textual descriptions of images |

**Your current setup:** Only `do_table_structure=True`, others disabled ✅

---

### 2. Table Structure Options

```python
from docling.datamodel.pipeline_options import TableStructureOptions, TableFormerMode

pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.FAST,  # or ACCURATE
    do_cell_matching=True
)
```

| Option | Values | VRAM | Accuracy | Speed | Use When |
|--------|--------|------|----------|-------|----------|
| **FAST** | TableFormerMode.FAST | 400 MB | 90-95% | 150ms/table | Standard documents |
| **ACCURATE** | TableFormerMode.ACCURATE | 800 MB | 97.9% | 300ms/table | Complex tables, merged cells |

**`do_cell_matching`**: Validates table cells against PDF text
- `True`: Higher accuracy, catches errors
- `False`: Faster, less validation

**Your current setup:** FAST mode + cell matching ✅

---

### 3. OCR Options

```python
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    TesseractOcrOptions,
    TesseractCliOcrOptions,
    OcrMacOptions
)

# Option 1: EasyOCR (GPU-optimized, best accuracy)
pipeline_options.ocr_options = EasyOcrOptions(
    lang=["en"],  # Language(s)
    use_gpu=True
)
# VRAM: ~1500 MB
# Accuracy: 95-98%
# Speed: Moderate

# Option 2: Tesseract (CPU, free)
pipeline_options.ocr_options = TesseractOcrOptions(
    lang=["eng"]
)
# VRAM: 0 MB (CPU only)
# Accuracy: 85-90%
# Speed: Slow

# Option 3: Mac OCR (Apple Silicon)
pipeline_options.ocr_options = OcrMacOptions()
# VRAM: 0 MB (Neural Engine)
# Accuracy: 90-95%
# Speed: Fast (on Apple Silicon)
```

**Your current setup:** `do_ocr=False` (not using OCR) ✅

**When to enable:**
- Scanned PDFs (no text layer)
- Images (PNG, JPEG, TIFF)
- Poor quality PDFs

---

### 4. GPU/Accelerator Options

```python
from docling.datamodel.pipeline_options import AcceleratorOptions

pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=2,      # Number of CPU threads (1-4)
    device="cuda"       # "cuda", "cpu", "mps" (Mac)
)
```

| Setting | Options | Impact |
|---------|---------|--------|
| **device** | `"cuda"` | Use NVIDIA GPU (fastest) |
|  | `"cpu"` | Use CPU only (slower, no VRAM) |
|  | `"mps"` | Use Apple Silicon GPU (Mac M1/M2) |
| **num_threads** | 1-4 | More threads = faster (but more RAM) |

**Your current setup:** CUDA + 2 threads ✅

---

### 5. Image Generation Options

```python
# Generate page images
pipeline_options.generate_page_images = True      # Full page renders
pipeline_options.generate_picture_images = True   # Extracted images
pipeline_options.generate_table_images = True     # Table visualizations

# Control image resolution
pipeline_options.images_scale = 2.0  # Higher = better quality, larger files
```

| Parameter | Default | What It Generates | Use Case |
|-----------|---------|-------------------|----------|
| **generate_page_images** | False | PNG of each PDF page | Visual reference, debugging |
| **generate_picture_images** | False | Extracted images as files | Save figures separately |
| **generate_table_images** | False | Table screenshots | Visual table validation |
| **images_scale** | 1.0 | Resolution multiplier | Higher quality exports |

**Your current setup:** All False (not generating images) ✅

**When to enable:**
- Need visual references
- Extracting figures for reports
- Debugging layout issues

---

### 6. Performance & Resource Options

```python
# Maximum processing time
pipeline_options.document_timeout = 600.0  # 10 minutes max

# Process only specific pages
pipeline_options.max_num_pages = 10  # Stop after 10 pages

# Artifacts path (model cache)
pipeline_options.artifacts_path = "/path/to/models"
```

| Parameter | Type | Purpose |
|-----------|------|---------|
| **document_timeout** | float | Max seconds before timeout (prevents hanging) |
| **max_num_pages** | int | Limit pages processed (useful for testing) |
| **artifacts_path** | str/Path | Local model storage (offline mode) |

**Your current setup:** Not set (using defaults) ✅

**When to use:**
- `document_timeout`: Long documents (prevent timeouts)
- `max_num_pages`: Testing (process first N pages only)
- `artifacts_path`: Air-gapped environments (no internet)

---

### 7. Advanced Options

```python
# Force text extraction from PDF backend
pipeline_options.force_backend_text = True

# Enable third-party plugins
pipeline_options.allow_external_plugins = True

# Enable remote service calls
pipeline_options.enable_remote_services = False  # Keep False for privacy!

# Generate parsed page structures
pipeline_options.generate_parsed_pages = True
```

| Parameter | Type | Default | Use When |
|-----------|------|---------|----------|
| **force_backend_text** | bool | False | PDF text extraction issues |
| **allow_external_plugins** | bool | False | Using custom plugins |
| **enable_remote_services** | bool | False | ⚠️ Sends data externally! |
| **generate_parsed_pages** | bool | False | Need page-level outputs |

**Your current setup:** Using defaults (all False) ✅

---

## 🎨 Picture Description Options

```python
from docling.datamodel.pipeline_options import SmolVlmPictureDescriptionOptions

# Enable AI image descriptions
pipeline_options.do_picture_description = True
pipeline_options.picture_description_options = SmolVlmPictureDescriptionOptions()
```

**What it does:** Generates textual descriptions of images using SmolVLM model

**Example output:**
```json
{
  "type": "picture",
  "description": "A bar chart showing monthly sales data from January to December",
  "bbox": {...}
}
```

**VRAM:** ~200 MB
**Accuracy:** Good for general images, diagrams, charts
**Speed:** 1-2 seconds per image

---

## 📊 Recommended Configurations

### Configuration 1: ⭐ OPTIMIZED SAFE (RECOMMENDED for production)

**Best balance of quality and speed - use this for everything!**

```python
pipeline_options.do_ocr = False  # Native PDF text
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,  # 97.9% accuracy
    do_cell_matching=True
)
pipeline_options.do_picture_classification = True   # Classify images
pipeline_options.do_picture_description = True      # Describe images (SmolVLM)
pipeline_options.do_code_enrichment = False         # Not needed for EAF
pipeline_options.do_formula_enrichment = True       # Extract equations
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=2,
    device="cuda"
)
```

**VRAM:** 3030 MB (safe on 4GB GPU with 862 MB headroom)
**Accuracy:** 97.9% tables, excellent image understanding
**Speed (first run):** 129 s/page (includes one-time model downloads)
**Speed (cached):** ⚡ 3.1 s/page (41x faster after models cached!)
**Use for:** ALL production extractions - best quality with minimal speed penalty

**Benchmarks (Chapter 1, 11 pages, GTX 1650 4GB):**
- First run: 1416s (23.6 min) - downloads SmolVLM, TableFormer, etc.
- Second run: 34s (0.57 min) - blazingly fast!
- 399-page document estimate: ~20 minutes (after cache)

**Why recommended:**
- Only 0.4s/page slower than lightweight (15% penalty)
- 8% better table accuracy (97.9% vs 90-95%)
- Picture understanding included (SmolVLM descriptions)
- Formula extraction included
- Minimal extra time for significantly better quality

---

### Configuration 2: Lightweight (legacy - not recommended)

**Use only if you need absolute minimum VRAM**

```python
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.FAST,
    do_cell_matching=True
)
pipeline_options.do_picture_classification = False
pipeline_options.do_picture_description = False
pipeline_options.do_code_enrichment = False
pipeline_options.do_formula_enrichment = False
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=2,
    device="cuda"
)
```

**VRAM:** ~2000 MB
**Accuracy:** 90-95%
**Speed:** ~2.7 s/page
**Use for:** Only if VRAM is severely constrained (not recommended - use Optimized Safe instead)

---

### Configuration 3: Maximum Speed (CPU mode)

```python
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.FAST,
    do_cell_matching=False  # Disable for speed
)
pipeline_options.do_picture_classification = False
pipeline_options.do_picture_description = False
pipeline_options.do_code_enrichment = False
pipeline_options.do_formula_enrichment = False
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=4,
    device="cpu"
)
```

**VRAM:** 0 MB (CPU only)
**RAM:** ~400 MB
**Speed:** 10x slower than GPU
**Use for:** No GPU available, air-gapped systems

---

### Configuration 4: Scanned Documents (OCR enabled)

```python
pipeline_options.do_ocr = True
pipeline_options.ocr_options = EasyOcrOptions(
    lang=["en", "es"],  # English + Spanish
    use_gpu=True
)
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    mode=TableFormerMode.ACCURATE,
    do_cell_matching=True
)
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=2,
    device="cuda"
)
```

**VRAM:** ~3900 MB (fits 4GB with tight margin)
**Accuracy:** 85-95% (depends on scan quality)
**Speed:** Slow (OCR is expensive)
**Use for:** Scanned PDFs, images, poor quality docs

---

## 🧮 VRAM Calculator

**Base Models:**
- Granite-258M (layout): 1200 MB
- PyTorch overhead: 400 MB
- **Subtotal: 1600 MB**

**Optional Features:**
- TableFormer FAST: +400 MB
- TableFormer ACCURATE: +800 MB
- EasyOCR: +1500 MB
- Picture classification: +100 MB
- Picture description: +200 MB
- Code enrichment: +100 MB
- Formula enrichment: +300 MB

**Example calculation (your setup):**
```
1600 (base) + 400 (FAST tables) = 2000 MB ✅ Safe for 4GB GPU
```

**Maximum safe (4GB GPU):**
```
1600 + 800 (ACCURATE) + 300 (formulas) = 2700 MB ✅
1600 + 800 + 1500 (OCR) = 3900 MB ⚠️ Tight!
1600 + 800 + 1500 + 200 = 4100 MB ❌ Exceeds 4GB!
```

---

## 💡 Options You Could Add (with VRAM budget)

**Your current usage:** 2000 MB
**Available budget:** 1400 MB (leaving 3400 MB for safety)

### You Could Add:

1. **Formula enrichment** (+300 MB):
   ```python
   pipeline_options.do_formula_enrichment = True
   # Total: 2300 MB ✅
   ```
   Use if: Your documents have equations

2. **Picture classification** (+100 MB):
   ```python
   pipeline_options.do_picture_classification = True
   # Total: 2100 MB ✅
   ```
   Use if: You want to categorize images (chart, diagram, photo)

3. **Code enrichment** (+100 MB):
   ```python
   pipeline_options.do_code_enrichment = True
   # Total: 2100 MB ✅
   ```
   Use if: Documents contain code snippets

4. **All three above** (+500 MB):
   ```python
   pipeline_options.do_formula_enrichment = True
   pipeline_options.do_picture_classification = True
   pipeline_options.do_code_enrichment = True
   # Total: 2500 MB ✅ Still safe!
   ```

5. **Upgrade to ACCURATE tables** (+400 MB):
   ```python
   pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
   # Total: 2400 MB (instead of 2000) ✅
   ```
   Use if: You have complex tables with merged cells

**NOT recommended for 4GB GPU:**
- ❌ OCR (+1500 MB) → Would reach 3500 MB (risky)
- ❌ Picture description (+200 MB) → Would reach 2700 MB with ACCURATE tables

---

## 📝 Summary

**⭐ RECOMMENDED CONFIGURATION: Optimized Safe**
- ✅ 4GB GPU safe (3030 MB with 862 MB headroom)
- ✅ Native PDF documents
- ✅ ACCURATE tables (97.9% accuracy)
- ✅ Picture classification + descriptions (SmolVLM)
- ✅ Formula enrichment included
- ✅ Blazingly fast after first run (3.1 s/page)

**Performance Benchmarks (GTX 1650 4GB):**
- First run: 23.6 min for 11 pages (one-time model downloads)
- Subsequent runs: 34 seconds for 11 pages (41x speedup!)
- 399-page document: ~20 minutes (after cache)
- Only 15% slower than lightweight (0.4s/page) for 8% better accuracy + all features

**Why Optimized Safe is now recommended:**
- ✅ Minimal speed penalty vs lightweight (3.1s vs 2.7s per page)
- ✅ Much better quality (ACCURATE tables, picture understanding, formulas)
- ✅ Safe VRAM usage on 4GB GPU
- ✅ One-time download penalty, then fast forever
- ✅ Best value for production work

**Legacy lightweight mode (2000 MB) is deprecated:**
- Only use if absolutely need minimum VRAM
- Missing picture understanding and formula support
- Table accuracy 90-95% vs 97.9%
- Not worth the 0.4s/page savings

**For scanned documents:**
- Add OCR (3900 MB total - tight on 4GB GPU)
- Or use CPU mode with OCR (slower but works)

---

**Last Updated**: 2025-10-27 (Updated with optimized safe benchmarks)
**Tested On**: GTX 1650 4GB, EAF Chapter 1 (11 pages)
**Benchmark**: Run 1: 1416s | Run 2: 34s (41x speedup)
**Status**: Production-ready ✅ - Optimized Safe is now default recommendation
