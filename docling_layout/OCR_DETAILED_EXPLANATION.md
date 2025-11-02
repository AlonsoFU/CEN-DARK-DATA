# OCR Detailed Explanation: What It Does, Models, and Execution

---

## Question 1: What Does OCR Actually Do?

### OCR = Optical Character Recognition = "Reading Text from Images"

### The Problem OCR Solves:

**Scenario**: You have a scanned document (photo/scan of paper):

```
┌─────────────────────────────────────────┐
│                                         │
│  [IMAGE OF TEXT]                        │
│   "Voltage: 500 kV"                     │
│   "Frequency: 50 Hz"                    │
│                                         │
│  This is NOT selectable text!           │
│  It's just pixels in an image.          │
│                                         │
└─────────────────────────────────────────┘
```

**Problem**:
- You can SEE the text with your eyes
- But the computer sees it as an IMAGE (pixels)
- You cannot copy/paste
- Cannot search
- Cannot extract data

**Solution - OCR**:
```
Image → OCR AI Model → Recognized Text
[Pixels] → Deep Learning → "Voltage: 500 kV"
```

---

## How OCR Works (Step by Step)

### Step 1: Image Input
```
OCR receives: Small region of PDF as image
Example: 200x100 pixel rectangle containing text
```

### Step 2: Preprocessing
```
- Convert to grayscale
- Adjust contrast
- Remove noise
- Binarization (black & white)
```

### Step 3: Character Detection
```
AI Model analyzes image:
- "I see characters at these positions"
- Identifies letter shapes
- Finds baselines and word boundaries
```

### Step 4: Character Recognition
```
Deep learning model recognizes:
- This shape = "V"
- This shape = "o"
- This shape = "l"
- This shape = "t"
→ Forms word: "Volt"
```

### Step 5: Text Assembly
```
Combines characters into:
- Words: "Voltage"
- Lines: "Voltage: 500 kV"
- Paragraphs
```

### Output
```
{
  "text": "Voltage: 500 kV",
  "confidence": 0.98,
  "bbox": [10, 20, 150, 40]
}
```

---

## What OCR Does in Docling Specifically

### Docling's OCR Pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Layout Detection (Always runs)                     │
│ Granite-258M finds: "There's a text block at (100,200)"    │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Try Native PDF Text Extraction (Always runs)       │
│ PyMuPDF attempts: "Read text from PDF structure"           │
└─────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────┐
    │ Text found?      │
    └──────────────────┘
           ↓
      YES ←─┴─→ NO
       ↓           ↓
   ✅ Done      ┌──────────────────────────────────┐
                │ STEP 3: OCR (Only if enabled)   │
                │ "Let me READ this region"       │
                └──────────────────────────────────┘
                           ↓
                   ┌──────────────────────────┐
                   │ Extract image of region  │
                   │ (e.g., 200x100 pixels)   │
                   └──────────────────────────┘
                           ↓
                   ┌──────────────────────────┐
                   │ EasyOCR AI Model         │
                   │ Recognizes characters    │
                   └──────────────────────────┘
                           ↓
                   ┌──────────────────────────┐
                   │ Returns recognized text  │
                   │ "Voltage: 500 kV"        │
                   └──────────────────────────┘
```

### Key Points:

1. **OCR is a FALLBACK**: Only runs if native text extraction fails
2. **Not for every block**: Only for blocks with missing/unclear text
3. **Image-based**: Takes screenshot of region, reads it as image
4. **Slower**: AI inference takes time (~100-500ms per block)
5. **Memory intensive**: Loads 1.5 GB model into VRAM

---

## Question 2: Which OCR Models Does Docling Use?

Docling supports **multiple OCR engines**. You choose one:

### Option 1: EasyOCR (Default - Best Accuracy)

**Model**: Deep learning CNN + RNN
**Size**: 1500 MB (English) / 1700 MB (Multi-language)
**Accuracy**: 95-98%
**Speed**: Medium (~200ms per block)
**Languages**: 80+ languages supported

**How it works**:
```
Input Image
    ↓
CNN (Convolutional Neural Network)
    - Detects features (edges, shapes, patterns)
    - Identifies character-like regions
    ↓
RNN (Recurrent Neural Network)
    - Recognizes character sequences
    - Uses context: "Vo" + "lt" = "Volt" (not "Vo1t")
    ↓
Output Text + Confidence Score
```

**Configuration**:
```python
from docling.datamodel.pipeline_options import EasyOcrOptions

ocr_options = EasyOcrOptions(
    lang=["en"],        # Languages
    use_gpu=True,       # GPU acceleration
    paragraph=False,    # Don't merge into paragraphs
    decoder='beamsearch' # Better accuracy
)
```

**Memory breakdown**:
```
Feature Detection Model (CNN):   600 MB
Character Recognition (RNN):     700 MB
Language Models:                 200 MB per language
───────────────────────────────────────
Total (English only):           1500 MB
Total (En + Es):                1700 MB
```

---

### Option 2: Tesseract (Fast - Lower Accuracy)

**Model**: Traditional pattern matching + ML
**Size**: ~50 MB (lightweight!)
**Accuracy**: 85-90%
**Speed**: Fast (~50ms per block)
**Languages**: 100+ languages

**How it works**:
```
Input Image
    ↓
Binarization (convert to pure black/white)
    ↓
Connected Component Analysis
    - Groups pixels into character shapes
    ↓
Pattern Matching + Neural Net
    - Matches shapes to known characters
    ↓
Output Text
```

**Configuration**:
```python
from docling.datamodel.pipeline_options import TesseractOcrOptions

ocr_options = TesseractOcrOptions(
    lang="eng",         # Tesseract language code
    tesseract_cmd="/usr/bin/tesseract"  # Path to tesseract
)
```

**Pros/Cons**:
- ✅ Very lightweight (50 MB vs 1500 MB)
- ✅ Fast processing
- ❌ Lower accuracy (85% vs 95%)
- ❌ Struggles with complex layouts

---

### Option 3: RapidOCR (Fastest - Good Accuracy)

**Model**: Optimized CNN
**Size**: 100 MB
**Accuracy**: 90-93%
**Speed**: Very fast (~30ms per block)

**Configuration**:
```python
from docling.datamodel.pipeline_options import RapidOcrOptions

ocr_options = RapidOcrOptions()
```

---

### Option 4: OCRmyPDF (Batch Processing)

**Model**: Tesseract wrapper
**Size**: ~50 MB
**Best for**: Full document OCR before Docling

---

### Comparison Table

| OCR Engine | Size | Speed | Accuracy | GPU | Best For |
|------------|------|-------|----------|-----|----------|
| **EasyOCR** | 1500 MB | Medium | 95-98% | ✅ | Default choice |
| **Tesseract** | 50 MB | Fast | 85-90% | ❌ | Lightweight |
| **RapidOCR** | 100 MB | Very Fast | 90-93% | ⚠️ | Speed priority |
| **OCRmyPDF** | 50 MB | Slow | 85-90% | ❌ | Batch docs |

**Your setup uses**: None (OCR disabled)
**If you enable**: EasyOCR is default (best accuracy)

---

## Question 3: Does Everything Run in Parallel?

### Answer: NO! Models run SEQUENTIALLY, not in parallel

### Execution Flow (Sequential):

```
TIME →

Step 1: Load Layout Model
├─ Granite-258M loads into VRAM (1200 MB)
└─ Stays loaded for entire document
        ↓
Step 2: Load Table Model
├─ TableFormer loads into VRAM (400 MB)
└─ Stays loaded for entire document
        ↓
Step 3: Load OCR Model (if enabled)
├─ EasyOCR loads into VRAM (1500 MB)
└─ Stays loaded for entire document
        ↓
Step 4: Process Each Page SEQUENTIALLY
├─ Page 1:
│   ├─ Layout Detection (Granite)
│   ├─ Text Extraction (PyMuPDF)
│   ├─ Table Structure (TableFormer)
│   └─ OCR if needed (EasyOCR)
│
├─ Page 2:
│   ├─ Layout Detection
│   ├─ Text Extraction
│   ├─ Table Structure
│   └─ OCR if needed
│
└─ Page 3...
```

### Key Points:

1. **Models load ONCE**: All stay in VRAM together
2. **Pages process SEQUENTIALLY**: One page at a time
3. **Within a page**: Steps run sequentially
4. **VRAM adds up**: All models occupy memory simultaneously

---

## Why Sequential, Not Parallel?

### Memory Constraint:

**If models ran in parallel on different pages**:
```
Thread 1 (Page 1): Uses Granite + TableFormer + OCR
Thread 2 (Page 2): Uses Granite + TableFormer + OCR
Thread 3 (Page 3): Uses Granite + TableFormer + OCR

VRAM needed: 3 × (1200 + 400 + 1500) = 9300 MB!
Your GPU: Only 4096 MB → CRASH!
```

**Sequential processing**:
```
One thread: Granite + TableFormer + OCR = 3100 MB
Process pages one by one
VRAM needed: 3100 MB ✅ Fits!
```

---

## Within-Page Processing (Sequential Steps)

```
PAGE 5 PROCESSING (takes ~2 seconds):

[0.0s - 0.5s] Layout Detection (Granite-258M)
              ↓ Finds: 20 text blocks, 3 tables, 2 figures

[0.5s - 0.8s] Native Text Extraction (PyMuPDF)
              ↓ Reads: Text for 18/20 blocks (2 missing)

[0.8s - 1.2s] Table Structure (TableFormer)
              ↓ Detects: 3 tables, 15 cells each

[1.2s - 1.8s] OCR for Missing Text (if enabled)
              ↓ Reads: 2 blocks that had no text

[1.8s - 2.0s] Post-processing
              ↓ Clean up, merge, finalize

Total: 2 seconds per page
```

**Everything is SEQUENTIAL within a page too!**

---

## Memory Accumulation

### Without OCR:
```
Granite-258M:     1200 MB ┐
TableFormer:       400 MB ├─ All loaded at once
PyTorch:           280 MB │
Buffers:           120 MB ┘
─────────────────────────
Total:            2000 MB (your current usage)
```

### With OCR:
```
Granite-258M:     1200 MB ┐
TableFormer:       400 MB │
EasyOCR:          1500 MB ├─ All loaded at once
PyTorch:           280 MB │
Buffers:           120 MB ┘
─────────────────────────
Total:            3500 MB (risky on 4GB GPU)
```

**All models stay in VRAM simultaneously!**

---

## Can You Run Things in Parallel?

### Option 1: Parallel Document Processing

**Multiple PDFs, one process each**:
```
Process 1: Document A (uses 2000 MB)
Process 2: Document B (uses 2000 MB)
Total: 4000 MB → Will crash on 4GB GPU!
```

❌ **Cannot do this on your GPU**

---

### Option 2: Parallel Page Processing (Experimental)

**One document, multiple pages at once**:
```python
# Docling doesn't support this by default
# Would require custom implementation
# Memory usage = N_pages × model_memory
```

❌ **Not supported, would crash anyway**

---

### Option 3: CPU Fallback for Parallel Processing

**Run Docling on CPU in parallel**:
```bash
# Terminal 1
python extract_doc1.py --device cpu

# Terminal 2
python extract_doc2.py --device cpu

# No GPU memory conflict!
```

✅ **This works!** But 10x slower per document.

---

## OCR Processing Example

### Example: Scanned Table

**Input**: Table region (300×200 pixels) with no native text

**Without OCR** (`do_ocr=False`):
```json
{
  "type": "table",
  "text": "",  // ← EMPTY! No text found
  "bbox": [100, 200, 400, 400]
}
```

**With OCR** (`do_ocr=True`):
```
Step 1: Extract image of region (300×200 px)
Step 2: Send to EasyOCR model
Step 3: EasyOCR processes (~200ms):
        - Detects characters
        - Recognizes: "Voltage | Current"
        - Recognizes: "500 kV | 1200 A"
Step 4: Returns text
```

```json
{
  "type": "table",
  "text": "Voltage | Current\n500 kV | 1200 A",  // ← Filled by OCR!
  "bbox": [100, 200, 400, 400],
  "ocr_confidence": 0.97
}
```

---

## Summary Answers

### Q1: What does OCR do?
**A**: Reads text from IMAGES (scanned pages/unclear regions)
- Uses AI to recognize characters in pixels
- Converts images to selectable text
- Fallback for when native PDF text missing

### Q2: Which model?
**A**: EasyOCR (default - 1500 MB)
- Deep learning CNN + RNN
- 95-98% accuracy
- Supports 80+ languages
- Alternatives: Tesseract (50 MB), RapidOCR (100 MB)

### Q3: Does everything run in parallel?
**A**: NO! Everything is SEQUENTIAL
- All models load into VRAM at once (memory adds up)
- Pages process one at a time
- Within page: sequential steps
- Cannot parallelize on single 4GB GPU

---

## Practical Implications

**Why you're NOT using OCR**:
- Your PDFs have native text (not scanned)
- Saves 1500 MB VRAM (huge savings!)
- Faster processing (no OCR inference)
- Same accuracy for native PDFs

**When you'd need OCR**:
- Scanned documents (images of paper)
- Screenshots embedded in PDF
- Handwritten text
- Very old/degraded PDFs

**Why OCR adds memory**:
- 1500 MB model stays loaded entire time
- Doesn't share memory with other models
- All models occupy VRAM simultaneously
- Sequential processing means models don't take turns

**For your 4GB GPU**:
- ✅ Without OCR: 2000 MB (safe)
- ⚠️ With OCR: 3500 MB (risky)
- ❌ OCR + extras: 4000+ MB (crash)
