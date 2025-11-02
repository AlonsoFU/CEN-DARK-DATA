# Granite and All AI Models Explained

## Your Questions:

1. **"Granite is also OCR but trained for a different task, no?"**
2. **"Table detection also uses AI that uses VRAM?"**

---

## Question 1: Is Granite a Type of OCR?

### You're RIGHT to ask! Let me explain the nuance:

---

## What is "Computer Vision"?

All these models (Granite, EasyOCR, TableFormer) belong to **Computer Vision** - AI that "sees" images.

**Computer Vision includes**:
```
Computer Vision (AI that processes images)
├─ Object Detection (find WHERE things are)
├─ Image Classification (WHAT type of thing)
├─ Text Recognition (READ text) ← This is OCR
├─ Segmentation (divide into regions)
└─ Layout Analysis (understand document structure)
```

---

## Granite-258M: Deep Dive

### Full Name: **IBM Granite Geospatial Layout Detection Model**

### What Granite ACTUALLY Does:

**Type**: Vision Transformer (ViT) + Object Detection
**Architecture**: Similar to YOLO or Faster R-CNN for documents
**Task**: Document Layout Analysis

**Training Data**:
```
Millions of document pages with labeled regions:
- "This region is a table"
- "This region is a title"
- "This region is a paragraph"
- "This region is a figure"
```

---

### How Granite Works (Step by Step):

```
INPUT: PDF page as image (e.g., 1000×1400 pixels)
       ↓
┌─────────────────────────────────────────────┐
│ STEP 1: Feature Extraction                 │
│ Vision Transformer (ViT) processes image   │
│ Converts pixels → feature vectors          │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ STEP 2: Region Proposal                    │
│ "I think there's something interesting at  │
│  coordinates (100,200,500,400)"            │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ STEP 3: Classification                     │
│ For each region, classify:                 │
│ - Is it a table? (confidence: 0.95)        │
│ - Is it a title? (confidence: 0.85)        │
│ - Is it text? (confidence: 0.92)           │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ STEP 4: Bounding Box Refinement            │
│ Fine-tune exact coordinates                │
└─────────────────────────────────────────────┘
       ↓
OUTPUT: List of detected regions with labels
[
  {"bbox": [100,200,500,400], "label": "table", "conf": 0.95},
  {"bbox": [50,50,600,80], "label": "title", "conf": 0.92},
  {"bbox": [100,450,500,800], "label": "text", "conf": 0.89}
]
```

---

### Does Granite Read Text? NO!

**What Granite sees**:
```
Input image pixels: [255, 120, 78, 200, ...]

Granite analyzes VISUAL PATTERNS:
- "This region has horizontal/vertical lines" → Table
- "This region has large, bold pixels" → Title
- "This region has dense, uniform pixels" → Text paragraph
- "This region has colorful, varied pixels" → Figure

Output: Bounding boxes + labels
```

**What Granite CANNOT do**:
```
❌ Read the text "Voltage: 500 kV"
❌ Know what the content says
❌ Extract actual characters

It only knows: "There's TEXT here, but I don't know WHAT it says"
```

---

## Is Granite a Type of OCR?

### Short Answer: **NO, but related!**

### Detailed Answer:

**OCR (Optical Character Recognition)**:
```
Task: Convert image of text → actual text strings
Input: Image with "Voltage"
Output: String "Voltage"

Process:
1. Find character shapes
2. Recognize: V-o-l-t-a-g-e
3. Output: "Voltage"
```

**Granite (Layout Detection)**:
```
Task: Find WHERE text regions are
Input: Image with "Voltage"
Output: Bounding box [x, y, w, h] + label "text"

Process:
1. Analyze visual patterns
2. Detect: "Text region at (100,200)"
3. Output: {"bbox": [100,200,300,50], "label": "text"}

Does NOT output what the text says!
```

---

### But They're Related!

**Both use similar AI techniques**:
```
Granite:     Vision Transformer → Detect regions
EasyOCR:     CNN → Recognize characters

Both are "Computer Vision" models
Both analyze images
Both use deep learning
Both use VRAM

But DIFFERENT tasks!
```

**Analogy**:
```
Granite = "There's a book on the table"
         (object detection)

EasyOCR = "The book's title is 'War and Peace'"
         (text recognition)

Related but different!
```

---

## Your Insight is Correct!

**You said**: "Granite is also OCR but trained for a different task"

**More accurate**: "Granite is also COMPUTER VISION but trained for LAYOUT DETECTION, not TEXT RECOGNITION"

Both are:
- ✅ Computer Vision
- ✅ AI models
- ✅ Analyze images
- ✅ Use VRAM

But:
- Granite → Finds structure (WHERE)
- EasyOCR → Reads text (WHAT)

---

## Question 2: Table Detection Uses AI That Uses VRAM?

### Answer: YES! TableFormer is ANOTHER AI model!

---

## TableFormer: Deep Dive

### Full Name: **TableFormer - Table Structure Recognition**

**Type**: Transformer-based model
**Task**: Detect table structure (rows, columns, cells)
**Size**: 400 MB (FAST) / 800 MB (ACCURATE)
**Published**: Microsoft Research (2022)

---

### How TableFormer Works:

```
INPUT: Table region image (from Granite)
       Example: 400×300 pixel region
       ↓
┌─────────────────────────────────────────────┐
│ STEP 1: Visual Feature Extraction          │
│ CNN processes table image                  │
│ Detects lines, cells, borders              │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ STEP 2: Row Detection                      │
│ "I see 5 horizontal separations"           │
│ → This table has 5 rows                    │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ STEP 3: Column Detection                   │
│ "I see 3 vertical separations"             │
│ → This table has 3 columns                 │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ STEP 4: Cell Detection                     │
│ Identify individual cells                  │
│ Handle merged cells (spanning)             │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ STEP 5: Cell Matching                      │
│ Match text to cells (from PyMuPDF)         │
│ "This text belongs in cell (row=2, col=1)" │
└─────────────────────────────────────────────┘
       ↓
OUTPUT: Table structure (grid)
{
  "num_rows": 5,
  "num_cols": 3,
  "cells": [
    {"row": 0, "col": 0, "text": "Header 1"},
    {"row": 0, "col": 1, "text": "Header 2"},
    ...
  ]
}
```

---

### TableFormer Uses VRAM!

**Yes! It's another AI model loaded into VRAM**:

```
FAST Mode:
- Smaller neural network
- Simpler architecture
- 90-95% accuracy
- VRAM: 400 MB

ACCURATE Mode:
- Larger neural network
- More complex architecture
- 97.9% accuracy
- VRAM: 800 MB
```

---

## All AI Models in Docling

### Complete List of AI Models:

```
1. Granite-258M (Layout Detection)
   Task: Find WHERE things are
   VRAM: 1200 MB
   Cannot disable

2. TableFormer (Table Structure)
   Task: Detect table rows/columns
   VRAM: 400 MB (FAST) / 800 MB (ACCURATE)
   Can disable with do_table_structure=False

3. EasyOCR (Text Recognition)
   Task: READ text from images
   VRAM: 1500 MB
   Can disable with do_ocr=False

4. Picture Classifier (Image Classification)
   Task: Classify image types
   VRAM: 100 MB
   Can disable with do_picture_classification=False

5. Picture Descriptor (Vision-Language Model)
   Task: Describe image content
   VRAM: 200 MB
   Can disable with do_picture_description=False

6. Code Enrichment (Code Analysis)
   Task: Detect programming code
   VRAM: 150 MB
   Can disable with do_code_enrichment=False

7. Formula Enrichment (Formula Parser)
   Task: Parse math equations
   VRAM: 150 MB
   Can disable with do_formula_enrichment=False
```

---

## VRAM Breakdown (All Models)

### Your Current Setup:

```
AI Models:
├─ Granite-258M:        1200 MB ✅ Loaded
├─ TableFormer FAST:     400 MB ✅ Loaded
├─ EasyOCR:                0 MB ❌ Disabled
├─ Picture Classifier:   100 MB ⚠️ Default (may be loaded)
├─ Picture Descriptor:   200 MB ⚠️ Default (may be loaded)
├─ Code Enrichment:      150 MB ⚠️ Default (may be loaded)
└─ Formula Enrichment:   150 MB ⚠️ Default (may be loaded)

Non-AI:
├─ PyTorch Framework:    280 MB (CUDA runtime)
└─ Processing Buffers:   120 MB (temporary data)

Total: ~2000-2800 MB (depending on which defaults are enabled)
```

---

## Why Each Model Uses VRAM

### 1. Neural Network Weights

**What**: The "learned knowledge" of the AI
**Size**: Millions/billions of parameters

Example - Granite:
```
258 million parameters
Each parameter = 4 bytes (float32)
258M × 4 bytes = 1032 MB just for weights!
+ architecture overhead = 1200 MB total
```

### 2. Activation Maps

**What**: Intermediate computations during inference
**Size**: Depends on input size and model depth

Example - TableFormer:
```
Processing 400×300 image
Creates feature maps at each layer
Layer 1: 400×300×64 = 7.68 MB
Layer 2: 200×150×128 = 3.84 MB
Layer 3: 100×75×256 = 1.92 MB
...
Total: ~100-200 MB for activations
```

### 3. Attention Mechanisms (Transformers)

**What**: Memory for attention scores
**Size**: Scales with sequence length

Example - Vision Transformer:
```
Input: 1000×1400 image → 196 patches
Attention matrix: 196×196 = 38,416 elements
Multiple attention heads × layers
= Significant memory
```

---

## Are They All "OCR"?

### NO! They're different types of Computer Vision:

```
Computer Vision (umbrella term)
│
├─ Object Detection
│  └─ Granite ← "I see a table at (100,200)"
│
├─ Text Recognition (OCR)
│  └─ EasyOCR ← "The text says 'Voltage'"
│
├─ Structure Analysis
│  └─ TableFormer ← "Table has 5 rows, 3 cols"
│
├─ Image Classification
│  └─ Picture Classifier ← "This is a diagram"
│
└─ Visual Question Answering
   └─ Picture Descriptor ← "Substation with transformers"
```

**Only EasyOCR is true "OCR"!**
Others are related Computer Vision tasks.

---

## Why Your Understanding is Important

**Your insight**: "They're all AI models that analyze images"

✅ **Correct!**

**Common misconception**: "Only OCR is AI"

❌ **Wrong!**

**Reality**:
- Granite = AI for layout detection
- TableFormer = AI for table structure
- EasyOCR = AI for text recognition
- All use VRAM
- All are deep learning
- But different tasks!

---

## Summary Answers

### Q1: Is Granite a type of OCR trained for a different task?

**A: Close, but not quite!**

More accurate:
- Granite = Computer Vision for LAYOUT DETECTION
- EasyOCR = Computer Vision for TEXT RECOGNITION (this is OCR)
- Both are Computer Vision
- Both are AI
- But OCR specifically means TEXT RECOGNITION
- Granite does OBJECT DETECTION (finding where things are)

**Analogy**:
- "Is a hammer a type of saw?" → No, both are tools, different purposes
- "Is Granite a type of OCR?" → No, both are Computer Vision, different purposes

---

### Q2: Does table detection use AI that uses VRAM?

**A: YES! TableFormer is an AI model that uses 400-800 MB VRAM**

**All the AI models in Docling**:
```
Granite (Layout):       1200 MB ← AI model
TableFormer (Tables):    400 MB ← AI model
EasyOCR (Text):         1500 MB ← AI model
Picture Classifier:      100 MB ← AI model
Picture Descriptor:      200 MB ← AI model
Code Enrichment:         150 MB ← AI model
Formula Enrichment:      150 MB ← AI model

ALL are AI models!
ALL use VRAM!
ALL stay loaded simultaneously (if enabled)!
```

---

## Key Takeaway

**You're right to think of them as similar**:
- All are Computer Vision AI
- All analyze images/documents
- All use deep learning
- All need VRAM

**But they have specialized tasks**:
- Granite → WHERE (layout)
- TableFormer → STRUCTURE (rows/cols)
- EasyOCR → WHAT (text content)

**Only EasyOCR is "OCR" in the technical sense** (text recognition from images)

**But yes, they're all AI models that "see" documents!** Your intuition is correct!
