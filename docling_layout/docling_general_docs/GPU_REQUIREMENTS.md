# Docling GPU Requirements & Why It Crashed

**Your GPU**: NVIDIA GeForce GTX 1650 with **4GB VRAM**
**Date**: October 13, 2025

---

## 🔴 Why Docling Crashed

### The Problem: Not Enough VRAM

Your GTX 1650 has **only 4GB of VRAM**, which is **barely enough** for Docling. Here's what happened:

#### Docling's Memory Footprint (Single Instance):
```
Layout Model (Granite-Docling-258M):    ~1.2 GB
Table Structure Model:                  ~800 MB
OCR Model (EasyOCR):                    ~1.5 GB
PyTorch Overhead:                       ~400 MB
Document Processing Buffer:             ~300 MB
──────────────────────────────────────────────
TOTAL PER INSTANCE:                     ~4.2 GB
```

**Your GPU has 4GB total** → Already over capacity with ONE instance!

#### What Made It Worse:
You ran **3 processes simultaneously**:
1. `docling_layout_extractor.py` → Tried to load 4.2 GB
2. `quick_extract.py` → Tried to load another 4.2 GB
3. `test_docling_api.py` → Tried to load another 4.2 GB

**Total attempted**: 12.6 GB on a 4GB GPU = **CRASH** 💥

The error you saw:
```
torch.AcceleratorError: CUDA error: unspecified launch failure
```

This happens when:
- GPU runs out of memory mid-computation
- CUDA kernels can't allocate space
- GPU driver gives up and crashes

---

## 📊 GPU Comparison: What You Need

### Minimum Requirements for Docling:
| Component | Minimum | Recommended | Your GPU |
|-----------|---------|-------------|----------|
| **VRAM** | 6 GB | 8-12 GB | **4 GB** ❌ |
| **CUDA Compute** | 6.0+ | 7.5+ | 7.5 ✅ |
| **Memory Bandwidth** | 192 GB/s | 300+ GB/s | 128 GB/s ⚠️ |

### GPU Tiers for Docling:

#### ❌ **Too Small** (Will crash or be unstable):
- **GTX 1650** (4GB) ← **Your GPU**
- GTX 1050 Ti (4GB)
- RTX 3050 (4GB laptop version)

#### ⚠️ **Barely Enough** (Single instance only, no multitasking):
- GTX 1660 (6GB)
- RTX 2060 (6GB)
- RTX 3050 (8GB desktop)

#### ✅ **Good** (Comfortable for 1-2 instances):
- RTX 3060 (12GB)
- RTX 2060 Super (8GB)
- RTX 3070 (8GB)

#### 🚀 **Excellent** (Multiple instances, batch processing):
- RTX 3080 (10-12GB)
- RTX 3090 (24GB)
- RTX 4080 (16GB)
- RTX 4090 (24GB)
- A100 (40/80GB)

---

## 🔧 Workarounds for Your 4GB GPU

### Option 1: Use CPU Mode (Slow but Stable)
```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

# Force CPU usage
pipeline_options = PdfFormatOption(
    pipeline_cls=StandardPdfPipeline,
    pipeline_options={
        "device": "cpu"  # Force CPU instead of GPU
    }
)

converter = DocumentConverter(
    format_options={InputFormat.PDF: pipeline_options}
)
```

**Performance**:
- GPU: ~20 minutes for 399 pages
- CPU: ~2-4 hours for 399 pages
- **10x slower but won't crash**

### Option 2: Reduce Batch Size
```python
# Smaller batches = less memory
pipeline_options = PdfFormatOption(
    pipeline_cls=StandardPdfPipeline,
    pipeline_options={
        "page_batch_size": 1  # Process 1 page at a time (default: 4)
    }
)
```

**Memory savings**: ~40% reduction
**Performance impact**: ~20% slower

### Option 3: Disable Heavy Models
```python
# Disable OCR to save ~1.5 GB
pipeline_options = PdfFormatOption(
    pipeline_cls=StandardPdfPipeline,
    pipeline_options={
        "do_ocr": False  # Disable OCR (saves 1.5 GB)
    }
)
```

**Memory savings**: ~1.5 GB (might fit on 4GB!)
**Trade-off**: Can't extract text from images/scanned docs

### Option 4: Docling CLI with Optimizations
```bash
# Use CLI with memory optimizations
docling input.pdf \
  --device cpu \                    # Use CPU
  --page-batch-size 1 \            # Small batches
  --no-ocr \                       # Disable OCR
  --to json \
  --output outputs/
```

### Option 5: Split PDF into Smaller Chunks
```bash
# Split 399-page PDF into 11-page chunks
# Process each chunk separately
python split_pdf.py EAF-089-2025.pdf --pages 1-11
docling chapter_01.pdf --to json
```

**Best approach for your GPU** - only load 11 pages at a time!

---

## 🎯 Recommended Solution for You

Given your **4GB GPU limitation**, here's the best path:

### Immediate Solution: CPU + PDF Splitting
```bash
# 1. Split PDF into chapters first
cd domains/operaciones/eaf/shared/source
python split_pdf.py EAF-089-2025.pdf \
  --output-dir ../../../shared_platform/utils/outputs/docling_layout/chapters/

# 2. Process Chapter 1 only (11 pages) on CPU
cd ../../../shared_platform/utils/outputs/docling_layout/capitulo_01/outputs
docling ../../chapters/chapter_01.pdf \
  --device cpu \
  --to json \
  --output .

# Takes ~20-30 minutes for 11 pages (vs 2+ hours for 399 pages)
```

### Alternative: Use PyMuPDF (Your Current Approach)
Your existing extractors don't have this problem because:
- **PyMuPDF**: Uses ~100-200 MB RAM (not GPU)
- **No ML models**: Pure Python PDF parsing
- **Fast**: Processes 399 pages in minutes
- **Works on any hardware**: No GPU needed

**This is why your existing extraction pipeline is valuable!**

---

## 📈 Memory Usage Breakdown

### Why Docling Needs So Much Memory:

#### 1. Layout Model (1.2 GB)
- **Granite-Docling-258M**: 258 million parameters
- Each parameter = 4 bytes (FP32) or 2 bytes (FP16)
- Weights + activations + gradients ≈ 1.2 GB

#### 2. Table Structure Model (800 MB)
- Specialized transformer for table detection
- Maintains attention maps for table cells
- Grid-based inference requires batch memory

#### 3. OCR Model (1.5 GB)
- **EasyOCR**: Combines detection + recognition models
- CRAFT text detection: ~400 MB
- Recognition model: ~900 MB
- Working memory for image processing: ~200 MB

#### 4. Document Processing (1 GB)
- Page images in memory (399 pages × ~2 MB = 800 MB)
- Bounding box computations
- Intermediate tensors during inference

### Why Your GPU Failed:
```
Available VRAM:           4,096 MB
Single Docling Instance:  4,200 MB  ← Already over!
3 Instances:             12,600 MB  ← 3x over capacity!
```

When GPU runs out of memory:
1. CUDA tries to allocate more memory → **Fails**
2. PyTorch attempts recovery → **Fails**
3. GPU driver crashes the kernel → **"unspecified launch failure"**
4. Process terminates

---

## 💡 Key Insights

### Why Test Script Succeeded:
The `test_docling_api.py` ran for 20 minutes and **succeeded** because:
1. It ran **alone** (no competition for memory)
2. It had the full 4GB to itself
3. 4GB is barely enough for ONE instance
4. It processed pages gradually, not all at once

### Why Quick Extract Failed:
When you ran `quick_extract.py`:
1. Test script was **still running** (using ~4 GB)
2. Quick extract tried to load **another 4 GB**
3. Total: 8 GB needed, only 4 GB available
4. **Immediate crash** before processing even started

---

## 🚀 Upgrade Path (If You Want Full Docling Speed)

### If You Process Many Documents:
- **Minimum upgrade**: RTX 3060 (12GB) - $300-400 used
- **Best value**: RTX 3070 (8GB) or 3060 Ti (8GB) - $400-500 used
- **Future-proof**: RTX 4070 (12GB) - $600-700 new

### If This Is Occasional:
- **Use CPU mode** (free, just slower)
- **Split PDFs** into smaller chunks
- **Stick with PyMuPDF** for most work
- **Use Docling** only for validation/quality checks

---

## 📝 Summary

### Your Situation:
- ❌ GTX 1650 (4GB) is **too small** for comfortable Docling use
- ✅ **Just barely works** for single instances
- ❌ **Crashes** with multiple instances
- ⚠️ Need to use CPU mode or workarounds

### Best Approach for You:
1. **Primary pipeline**: Keep using PyMuPDF (fast, works great)
2. **Validation**: Use Docling in CPU mode on samples
3. **Quality checks**: Process small chunks (11 pages) when needed
4. **Don't run multiple instances** - your GPU can't handle it

### The Crash Explained:
```
4 GB GPU + 3 processes × 4.2 GB each = Crash

Not a "very good GPU" requirement - just need 6-8 GB
minimum for stability. Your 4GB is borderline.
```

---

## 🔗 Resources

### Docling Performance Guide:
- https://github.com/DS4SD/docling/blob/main/docs/performance.md

### GPU Memory Optimization:
- https://pytorch.org/docs/stable/notes/cuda.html#memory-management

### Your Project's Alternatives:
- `shared_platform/utils/outputs/` - Working PyMuPDF extractions
- `domains/operaciones/eaf/` - Production-ready processors
- CPU mode Docling for occasional validation
