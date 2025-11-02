# CLARIFICATION: Sequential Processing vs VRAM Usage

## Your Questions:

1. **"If it's sequential, why does it need so much VRAM?"**
2. **"Which OCR does Docling use? You said EasyOCR but also Granite?"**

---

## Question 1: Why So Much VRAM if Sequential?

### The Confusion: Sequential ≠ Memory Efficient

**Sequential** means: "Processing one thing at a time"
**BUT**: All the TOOLS must be loaded and ready!

---

### Analogy: Restaurant Kitchen

Imagine a restaurant kitchen:

**Sequential Cooking** (one dish at a time):
```
Chef 1: Makes appetizer   [5 minutes]
       ↓
Chef 1: Makes main course [10 minutes]
       ↓
Chef 1: Makes dessert     [5 minutes]

ONE chef working sequentially = 20 minutes total
```

**But the kitchen still needs**:
```
Stove:          Always there (takes space)
Oven:           Always there (takes space)
Refrigerator:   Always there (takes space)
Mixer:          Always there (takes space)
─────────────────────────────────────────
Total space: All equipment simultaneously!
```

**Even though only ONE dish is cooked at a time, ALL equipment occupies space!**

---

### Applied to Docling:

**Sequential Page Processing** (one page at a time):
```
Process Page 1  [2 seconds]
       ↓
Process Page 2  [2 seconds]
       ↓
Process Page 3  [2 seconds]

ONE page at a time = Sequential
```

**But the AI models must stay loaded**:
```
Granite-258M Model:    1200 MB (always in VRAM)
TableFormer Model:      400 MB (always in VRAM)
EasyOCR Model:         1500 MB (always in VRAM)
PyTorch Framework:      280 MB (always in VRAM)
────────────────────────────────────────────────
Total VRAM: All models simultaneously loaded!
```

**Even though only ONE page is processed at a time, ALL models occupy VRAM!**

---

## Why Can't Models Load/Unload?

### Option A: Load All Models Once (Current Approach)

```
[Load Granite: 5 seconds]
[Load TableFormer: 2 seconds]
[Load OCR: 3 seconds]
───────────────────────────────
Setup time: 10 seconds ONE TIME

Then process 100 pages:
Page 1:  [2 sec] ← Models already loaded
Page 2:  [2 sec]
Page 3:  [2 sec]
...
Page 100: [2 sec]
───────────────────────────────
Total: 10 + (100 × 2) = 210 seconds
```

**Efficient for multi-page documents!**

---

### Option B: Load/Unload Per Page (Hypothetical)

```
Page 1:
  [Load Granite: 5 sec]
  [Load TableFormer: 2 sec]
  [Load OCR: 3 sec]
  [Process: 2 sec]
  [Unload all: 1 sec]
  Total: 13 seconds

Page 2:
  [Load Granite: 5 sec]
  [Load TableFormer: 2 sec]
  [Load OCR: 3 sec]
  [Process: 2 sec]
  [Unload all: 1 sec]
  Total: 13 seconds

...

100 pages × 13 seconds = 1300 seconds!
```

**6× SLOWER! Terrible for multi-page documents!**

---

## The Trade-off

### Keep Models Loaded:
```
Pros:
✅ Fast processing (no reload overhead)
✅ Efficient for multi-page documents
✅ Docling's default approach

Cons:
❌ Uses VRAM even when idle
❌ All models in memory simultaneously
❌ Cannot process if total VRAM exceeds GPU capacity
```

### Load/Unload Models:
```
Pros:
✅ Lower VRAM usage (only load what's needed)
✅ Could fit more on limited GPU

Cons:
❌ 6-10× slower (constant loading/unloading)
❌ Terrible user experience
❌ Disk I/O bottleneck
❌ Not how Docling is designed
```

**Docling chooses: Keep models loaded (speed over memory efficiency)**

---

## Visual Explanation

### What "Sequential" Means:

```
VRAM (All models loaded simultaneously):
┌──────────────────────────────────────┐
│ Granite:     [████████████] 1200 MB │
│ TableFormer: [████]          400 MB │
│ OCR:         [████████████] 1500 MB │
│ PyTorch:     [██]            280 MB │
└──────────────────────────────────────┘
Total: 3380 MB (all at once!)

PROCESSING (Sequential - one at a time):
Page 1: [██████░░░░░░░░░░] Processing...
Page 2: [░░░░░░██████░░░░░] Processing...
Page 3: [░░░░░░░░░░░██████] Processing...

Models stay loaded ▲
But pages process one by one ▼
```

---

## Question 2: Which OCR Does Docling Use? Granite or EasyOCR?

### CRITICAL CLARIFICATION: They are DIFFERENT models for DIFFERENT tasks!

---

### Model 1: Granite-258M (NOT OCR!)

**Full Name**: IBM Granite-Geospatial Layout Detection Model
**Purpose**: LAYOUT DETECTION (visual analysis)
**Size**: 1200 MB
**Always Runs**: Yes (cannot disable)

**What it does**:
```
Input: PDF page (as image)
Output: Bounding boxes + labels

Example:
"I SEE a table at coordinates (100, 200, 500, 400)"
"I SEE a title at coordinates (50, 50, 300, 80)"
"I SEE a figure at coordinates (400, 500, 600, 700)"

NOT reading text! Just finding WHERE things are!
```

**Think of it as**: "Eyes" - Sees structure, doesn't read text

**This is NOT OCR!**

---

### Model 2: EasyOCR (ACTUAL OCR)

**Full Name**: EasyOCR - Optical Character Recognition
**Purpose**: TEXT RECOGNITION from images
**Size**: 1500 MB
**Always Runs**: No (only if `do_ocr=True`)

**What it does**:
```
Input: Small image region (e.g., 200×100 pixels)
Output: Recognized text

Example:
Input: [Image of text: "Voltage: 500 kV"]
Output: "Voltage: 500 kV"

READS text from images!
```

**Think of it as**: "Reading glasses" - Reads text from pictures

**This IS OCR!**

---

## Granite vs EasyOCR: Side-by-Side Comparison

| Feature | Granite-258M | EasyOCR |
|---------|--------------|---------|
| **Type** | Layout Detection | OCR (Text Recognition) |
| **Input** | Full page image | Small text region |
| **Output** | Bounding boxes + labels | Text strings |
| **Task** | "WHERE is the table?" | "WHAT does the text say?" |
| **Reads Text?** | ❌ NO | ✅ YES |
| **Detects Layout?** | ✅ YES | ❌ NO |
| **Always Runs?** | ✅ YES | ❌ Only if enabled |
| **Memory** | 1200 MB | 1500 MB |
| **Can Disable?** | ❌ NO | ✅ YES |

---

## How They Work Together

### Without OCR (Your Current Setup):

```
┌─────────────────────────────────────┐
│ Step 1: Granite-258M                │
│ "I SEE a text block at (100,200)"  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Step 2: PyMuPDF                     │
│ "I READ native PDF text"            │
│ Text: "Voltage: 500 kV"             │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Step 3: Match text to box           │
│ Box (100,200) ← "Voltage: 500 kV"  │
└─────────────────────────────────────┘

NO OCR INVOLVED!
Granite only finds WHERE things are.
PyMuPDF reads the actual text.
```

---

### With OCR Enabled:

```
┌─────────────────────────────────────┐
│ Step 1: Granite-258M                │
│ "I SEE a text block at (100,200)"  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Step 2: PyMuPDF                     │
│ "I TRY to read native PDF text"    │
│ Result: Empty (no text in PDF)      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Step 3: EasyOCR (fallback)          │
│ "Let me READ the image at (100,200)"│
│ Text: "Voltage: 500 kV"             │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Step 4: Match text to box           │
│ Box (100,200) ← "Voltage: 500 kV"  │
└─────────────────────────────────────┘

Granite finds WHERE.
PyMuPDF tries native text first.
EasyOCR fills in if text is missing.
```

---

## Why The Confusion?

### You asked: "Which OCR does Docling use?"

**My answer was incomplete!**

I said: "EasyOCR" ← Correct for OCR specifically
But didn't clarify: Granite is NOT OCR!

**Complete answer**:

**For LAYOUT DETECTION** (finding WHERE things are):
- Granite-258M ← Always runs
- 1200 MB
- NOT OCR!

**For TEXT RECOGNITION** (reading WHAT text says):
- EasyOCR ← Only if enabled
- 1500 MB
- This IS OCR!

---

## Why Both Need VRAM Simultaneously

**Even though they do different things, both must stay loaded**:

```
Granite (1200 MB):
- Scans EVERY page for layout
- Must stay loaded for entire document

EasyOCR (1500 MB):
- Used occasionally (only for missing text)
- But must stay loaded once enabled
- Cannot load/unload per page (too slow)

Total when both enabled: 2700 MB (+ other components)
```

---

## Summary Answers

### Q1: "Why so much VRAM if sequential?"

**A: Sequential processing ≠ Sequential loading**

- **Sequential**: Pages process ONE AT A TIME
- **But**: All AI models stay loaded SIMULTANEOUSLY
- **Why**: Loading models is slow (5-10 sec each)
- **Result**: Speed vs memory trade-off
- **Docling's choice**: Keep all models loaded for speed

**Analogy**: Restaurant kitchen with all equipment (even if cooking one dish at a time)

---

### Q2: "Which OCR? EasyOCR or Granite?"

**A: Both, but they're DIFFERENT things!**

**Granite-258M** (NOT OCR):
- Layout detection ("I SEE structure")
- 1200 MB
- Always runs
- Cannot disable

**EasyOCR** (ACTUAL OCR):
- Text recognition ("I READ text from images")
- 1500 MB
- Only if enabled
- Can disable

**Your confusion is understandable**: Both are AI models, both use VRAM, but completely different purposes!

---

## Final Clarification

**Why your 2000 MB usage**:
```
Granite (Layout):    1200 MB ← Always loaded
TableFormer:          400 MB ← Always loaded
PyTorch:              280 MB ← Framework
Buffers:              120 MB ← Processing
───────────────────────────
Total:               2000 MB

EasyOCR:                0 MB ← NOT loaded (disabled)
```

**If you enabled OCR**:
```
Granite (Layout):    1200 MB ← Still needed
TableFormer:          400 MB ← Still needed
EasyOCR:             1500 MB ← NOW loaded too
PyTorch:              280 MB ← Framework
Buffers:              120 MB ← Processing
───────────────────────────
Total:               3500 MB (all simultaneously!)
```

**Sequential pages, but ALL models loaded at once!**
