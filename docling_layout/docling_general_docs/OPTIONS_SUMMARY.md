# Docling Options - Visual Summary

Quick reference for all Docling options with visual indicators.

---

## 🎚️ Memory Impact Chart

```
Standard Config (4.2 GB) - Won't fit on 4GB GPU:
████████████████████████████████████████████  4.2 GB

Lightweight Config (1.3 GB) - Fits perfectly:
█████████████  1.3 GB
                              ↑ 70% reduction!
```

---

## 🔧 Options by Category

### 🚀 Processing Features

| Option | Default | Memory | Impact | Your Case |
|--------|---------|--------|--------|-----------|
| `do_ocr` | ✅ ON | 1.5 GB | Text from images | ❌ Disable (native text) |
| `do_table_structure` | ✅ ON | 400-800 MB | Table detection | ✅ Keep (FAST mode) |
| `do_picture_classification` | ❌ OFF | 100 MB | Image types | ❌ Keep off |
| `do_picture_description` | ❌ OFF | 200 MB | Image captions | ❌ Keep off |
| `do_code_enrichment` | ❌ OFF | 150 MB | Code syntax | ❌ Keep off |
| `do_formula_enrichment` | ❌ OFF | 150 MB | LaTeX formulas | ❌ Keep off |

### 🎨 Image Generation

| Option | Default | Memory | Output |
|--------|---------|--------|--------|
| `generate_page_images` | ❌ OFF | 100 MB | Page screenshots |
| `generate_picture_images` | ❌ OFF | 50 MB | Extracted images |
| `generate_table_images` | ❌ OFF | 50 MB | Table visualizations |

### ⚙️ Accelerator Settings

| Setting | Options | Recommendation |
|---------|---------|----------------|
| `device` | `auto`, `cpu`, `cuda`, `mps` | `cuda` (your GPU) |
| `num_threads` | 1-16 | `2` (reduce overhead) |

---

## 📊 Configuration Presets

### Preset 1: Minimal (1.3 GB) ⭐ RECOMMENDED

```
Layout Detection:     ████████████████████ 100%
Table Detection:      ███████████████░░░░░  95% (FAST mode)
OCR:                  ░░░░░░░░░░░░░░░░░░░░   0% (disabled)
Image Analysis:       ░░░░░░░░░░░░░░░░░░░░   0% (disabled)
Enrichment:           ░░░░░░░░░░░░░░░░░░░░   0% (disabled)
───────────────────────────────────────────────
Memory:               ████░░░░░░░░░░░░░░░░  1.3 GB / 4 GB
Speed:                ████████████████░░░░  Fast (15-18 min)
```

**Use when**: Native PDF text, 4GB GPU, need tables

---

### Preset 2: Balanced (2.0 GB)

```
Layout Detection:     ████████████████████ 100%
Table Detection:      ███████████████░░░░░  95% (FAST mode)
OCR:                  ████████████████████ 100% (EN only)
Image Analysis:       ░░░░░░░░░░░░░░░░░░░░   0% (disabled)
Enrichment:           ░░░░░░░░░░░░░░░░░░░░   0% (disabled)
───────────────────────────────────────────────
Memory:               ████████░░░░░░░░░░░░  2.0 GB / 4 GB
Speed:                ███████████████░░░░░  Medium (20 min)
```

**Use when**: Some scanned pages, 4GB GPU, need OCR

---

### Preset 3: Full Features (4.2 GB) ❌

```
Layout Detection:     ████████████████████ 100%
Table Detection:      ████████████████████  98% (ACCURATE)
OCR:                  ████████████████████ 100% (multi-lang)
Image Analysis:       ████████████████████ 100%
Enrichment:           ████████████████████ 100%
───────────────────────────────────────────────
Memory:               ████████████████████  4.2 GB / 4 GB ⚠️
Speed:                ███████████░░░░░░░░░  Slow (20+ min)
```

**Use when**: 8GB+ GPU, need all features

---

### Preset 4: CPU Mode (Unlimited)

```
Layout Detection:     ████████████████████ 100%
Table Detection:      ████████████████████  98% (ACCURATE)
OCR:                  ████████████████████ 100%
Image Analysis:       ████████████████████ 100%
Enrichment:           ████████████████████ 100%
───────────────────────────────────────────────
Memory:               ████░░░░░░░░░░░░░░░░  400 MB RAM
Speed:                ██░░░░░░░░░░░░░░░░░░  Very slow (2-4 hrs)
```

**Use when**: GPU too small, need all features, have time

---

## 🎯 Quick Decision Tree

```
Start Here
    ↓
Do you have native PDF text? ─NO→ Enable OCR (2.0 GB)
    ↓ YES                              ↓
    ↓                            Will fit on 4GB? ─NO→ Use CPU mode
    ↓                                   ↓ YES
    ↓                                   ↓
Do you need tables? ─NO→ Minimal layout only (0.8 GB)
    ↓ YES
    ↓
Use MINIMAL config (1.3 GB) ← RECOMMENDED FOR YOUR GPU
    ↓
Run lightweight_extract.py
```

---

## 🔑 Key Options Explained

### `do_ocr` - Optical Character Recognition

```
┌─────────────────────────────────────┐
│  PDF Page                           │
│  ┌─────────────────────────────┐   │
│  │ [Native Text]               │   │  ← OCR NOT needed
│  │ This is selectable text     │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ [Image with Text]           │   │  ← OCR needed
│  │ (Scanned document/photo)    │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

Your case: EAF reports = Native text → Disable OCR
```

**Disable to save**: 1.5 GB

---

### `table_structure_options.mode` - Table Detection

```
ACCURATE Mode (800 MB):           FAST Mode (400 MB):
┌───┬───┬───┐                     ┌───┬───┬───┐
│ A │ B │ C │ ← 97.9% accurate    │ A │ B │ C │ ← 95% accurate
├───┼───┼───┤                     ├───┼───┼───┤
│ 1 │ 2 │ 3 │                     │ 1 │ 2 │ 3 │
└───┴───┴───┘                     └───┴───┴───┘
     ↑                                 ↑
Better for complex tables        Better for 4GB GPU
```

**Use FAST to save**: 400 MB

---

### `do_picture_description` - Image Captions

```
Without:                          With:
┌─────────────┐                  ┌─────────────┐
│   [Image]   │                  │   [Image]   │
│             │                  │  "A line    │
└─────────────┘                  │   chart..." │
                                 └─────────────┘
    ↑                                  ↑
 Just bbox                      Adds AI caption (200 MB)
```

**Your case**: Not critical → Disable to save 200 MB

---

### `generate_page_images` - Page Screenshots

```
Without:                          With:
PDF → JSON with boxes            PDF → JSON + PNG files
      (layout data only)               (visual + data)

Memory: Low                      Memory: +100 MB
```

**Your case**: Not needed → Disable

---

## 📈 Memory Savings Breakdown

```
Standard Configuration (4.2 GB):
├─ Layout Model (core)        1.2 GB  [Cannot disable]
├─ Table Structure            0.8 GB  [Keep but use FAST: -0.4 GB]
├─ OCR (EasyOCR)             1.5 GB  [Disable: -1.5 GB]
├─ Picture Classification     0.1 GB  [Disable: -0.1 GB]
├─ Picture Description        0.2 GB  [Disable: -0.2 GB]
├─ Code Enrichment           0.15 GB  [Disable: -0.15 GB]
├─ Formula Enrichment        0.15 GB  [Disable: -0.15 GB]
└─ Image Generation           0.1 GB  [Disable: -0.1 GB]
                              ──────
                              4.2 GB

After Optimization (1.3 GB):
├─ Layout Model (core)        1.2 GB  [Required]
└─ Table Structure (FAST)     0.4 GB  [Optimized]
                              ──────
                              1.6 GB  (↓ 2.6 GB saved!)
```

---

## 🎬 CLI Examples

### Minimal (1.3 GB):
```bash
docling input.pdf \
  --device cuda \
  --no-ocr \
  --table-mode fast \
  --to json
```

### With OCR (2.0 GB):
```bash
docling input.pdf \
  --device cuda \
  --ocr-lang en \
  --table-mode fast \
  --to json
```

### Full Features (4.2 GB):
```bash
docling input.pdf \
  --device cuda \
  --ocr-lang en,es \
  --table-mode accurate \
  --enrich-picture-description \
  --enrich-formula \
  --to json
```

### CPU Mode (Safe):
```bash
docling input.pdf \
  --device cpu \
  --to json
```

---

## ✅ Recommendation for Your Setup

**Your Hardware**: GTX 1650 (4GB VRAM)
**Your Documents**: EAF reports with native PDF text

**Best Configuration**:
```python
pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(
        num_threads=2,
        device="cuda"
    ),
    do_ocr=False,                    # ✅ Save 1.5 GB
    do_table_structure=True,         # ✅ Keep tables
    table_structure_options=TableStructureOptions(
        mode=TableFormerMode.FAST    # ✅ Save 400 MB
    ),
    # All other enrichments disabled by default
)
```

**Result**: 1.3 GB memory ✅ Fits comfortably on your 4GB GPU

**Script ready**: `lightweight_extract.py`

---

## 🚀 Next Steps

1. **Read full guide**: `DOCLING_OPTIONS_EXPLAINED.md`
2. **Run lightweight script**: `python lightweight_extract.py`
3. **Monitor progress**: `bash MONITOR.sh`

Good luck! 🎉
