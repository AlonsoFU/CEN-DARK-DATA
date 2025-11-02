# Complete Text Extraction Pipeline: How Docling Finds Text

---

## Your Question: "How now I am finding text? Just extract data directly from bounding box?"

### Short Answer:

**NO!** Docling uses a sophisticated TWO-STAGE process:

1. **Granite AI detects WHERE** elements are (bounding boxes)
2. **PyMuPDF reads WHAT** the text says (from PDF structure)
3. **Docling matches** text to bounding boxes using spatial algorithms

**You are NOT extracting text by "reading pixels" inside bounding boxes!**

---

## Complete Pipeline (Step by Step)

### Stage 1: Layout Detection (Granite-258M AI Model)

```
INPUT: PDF page as image (e.g., 1000×1400 pixels)
       ↓
┌─────────────────────────────────────────────┐
│ Granite-258M Vision AI                     │
│ Analyzes page VISUALLY (as image)         │
└─────────────────────────────────────────────┘
       ↓
Detects visual patterns:
- "I SEE a text block at (100, 200, 500, 300)"
- "I SEE a table at (50, 350, 550, 600)"
- "I SEE a title at (100, 50, 400, 80)"
       ↓
OUTPUT: Bounding boxes with LABELS (NO TEXT YET!)
[
  {"bbox": [100, 200, 500, 300], "label": "text"},
  {"bbox": [50, 350, 550, 600], "label": "table"},
  {"bbox": [100, 50, 400, 80], "label": "title"}
]
```

**Key Point**: Granite only finds STRUCTURE, not content!

---

### Stage 2: Native PDF Text Extraction (PyMuPDF)

```
INPUT: Same PDF page (NOT as image, as PDF structure)
       ↓
┌─────────────────────────────────────────────┐
│ PyMuPDF Library                            │
│ Reads PDF file structure directly         │
└─────────────────────────────────────────────┘
       ↓
Reads embedded text with EXACT COORDINATES:
- "Voltage: 500 kV" at (110, 210)
- "Frequency: 50 Hz" at (110, 240)
- "Table header" at (60, 360)
       ↓
OUTPUT: Text strings with POSITIONS (NO LABELS YET!)
[
  {"text": "Voltage: 500 kV", "bbox": [110, 210, 200, 230]},
  {"text": "Frequency: 50 Hz", "bbox": [110, 240, 220, 260]},
  {"text": "Table header", "bbox": [60, 360, 150, 380]}
]
```

**Key Point**: PyMuPDF reads actual PDF text, NOT pixels!

---

### Stage 3: Intelligent Matching (Docling Core Logic)

```
INPUT:
- Granite's bounding boxes with LABELS
- PyMuPDF's text with POSITIONS
       ↓
┌─────────────────────────────────────────────┐
│ Docling Spatial Matching Algorithm        │
│ Matches text to boxes using coordinates   │
└─────────────────────────────────────────────┘
       ↓
Matching logic:
1. For each Granite box (e.g., text block at [100, 200, 500, 300])
2. Find all PyMuPDF text inside that box
3. Combine text + label

Example:
Granite box: [100, 200, 500, 300] (label: "text")
PyMuPDF text inside:
  - "Voltage: 500 kV" at (110, 210) ✅ INSIDE
  - "Frequency: 50 Hz" at (110, 240) ✅ INSIDE
       ↓
MATCHED OUTPUT:
{
  "bbox": [100, 200, 500, 300],
  "label": "text",
  "text": "Voltage: 500 kV\nFrequency: 50 Hz"
}
```

**Key Point**: Matching is done by COMPARING COORDINATES, not reading pixels!

---

## Visual Diagram

```
┌─────────────────────────────────────────────────────────┐
│ PDF PAGE                                                │
│                                                         │
│  ┌──────────────────────┐  ← Granite detects box      │
│  │ Voltage: 500 kV      │  ← PyMuPDF reads text       │
│  │ Frequency: 50 Hz     │  ← Docling matches them     │
│  └──────────────────────┘                              │
│                                                         │
│  ┌─────────────────────────────┐                       │
│  │ Header | Value | Unit       │  ← Granite: "table"   │
│  ├─────────────────────────────┤  ← PyMuPDF: cell text │
│  │ V      | 500   | kV         │  ← Docling: combine   │
│  └─────────────────────────────┘                       │
└─────────────────────────────────────────────────────────┘

GRANITE (AI Vision):           PYMUPDF (PDF Reader):
"I SEE a text block here"      "Text says: Voltage: 500 kV"
bbox: [100,200,500,300]        coords: (110, 210)

                 ↓↓↓

DOCLING (Matcher):
"Text at (110,210) is INSIDE box [100,200,500,300]"
"Assign text to box!"

FINAL OUTPUT:
{
  "bbox": [100,200,500,300],
  "label": "text",
  "text": "Voltage: 500 kV"
}
```

---

## Why This Two-Stage Approach?

### Method 1: Only Visual Analysis (No PyMuPDF)
```
❌ Problems:
- Would need OCR to read ALL text (expensive, slow)
- 85-90% accuracy (vs 99.9% for native PDF)
- Costs API calls or GPU memory
- Much slower (100-500ms per block)
```

### Method 2: Only PyMuPDF (No Granite)
```
❌ Problems:
- PyMuPDF gives text but NO LABELS
- Cannot tell if text is in a table, title, or paragraph
- No semantic understanding of layout
- Hard to extract structured data
```

### Method 3: Granite + PyMuPDF (Docling's Approach) ✅
```
✅ Advantages:
- Granite provides STRUCTURE (labels, boxes)
- PyMuPDF provides TEXT (99.9% accurate for native PDFs)
- Matching combines both = Best of both worlds
- Fast (no OCR needed for native PDFs)
- Accurate (AI layout + native text)
```

---

## Detailed Matching Algorithm

### Step 1: Get Granite Boxes
```python
# Granite detected these regions:
granite_boxes = [
    {"bbox": [100, 200, 500, 300], "label": "text"},
    {"bbox": [50, 350, 550, 600], "label": "table"}
]
```

### Step 2: Get PyMuPDF Text
```python
# PyMuPDF extracted this text:
pymupdf_text = [
    {"text": "Voltage: 500 kV", "bbox": [110, 210, 200, 230]},
    {"text": "Frequency: 50 Hz", "bbox": [110, 240, 220, 260]},
    {"text": "Table cell 1", "bbox": [60, 360, 140, 380]},
    {"text": "Table cell 2", "bbox": [150, 360, 240, 380]}
]
```

### Step 3: Match Using Coordinates
```python
# Pseudo-code for matching:
for granite_box in granite_boxes:
    matched_text = []

    for text_item in pymupdf_text:
        # Check if text coordinates are INSIDE granite box
        if is_inside(text_item.bbox, granite_box.bbox):
            matched_text.append(text_item.text)

    # Combine all matched text
    granite_box.text = "\n".join(matched_text)

# Result:
final_output = [
    {
        "bbox": [100, 200, 500, 300],
        "label": "text",
        "text": "Voltage: 500 kV\nFrequency: 50 Hz"
    },
    {
        "bbox": [50, 350, 550, 600],
        "label": "table",
        "text": "Table cell 1\nTable cell 2"
    }
]
```

### Function: `is_inside(text_bbox, granite_bbox)`
```python
def is_inside(text_bbox, granite_bbox):
    """Check if text bounding box is inside granite box"""
    text_x1, text_y1, text_x2, text_y2 = text_bbox
    granite_x1, granite_y1, granite_x2, granite_y2 = granite_bbox

    # Text center point
    text_center_x = (text_x1 + text_x2) / 2
    text_center_y = (text_y1 + text_y2) / 2

    # Check if center is inside granite box
    return (granite_x1 <= text_center_x <= granite_x2 and
            granite_y1 <= text_center_y <= granite_y2)
```

---

## What About OCR?

### OCR is ONLY used when PyMuPDF finds NO text:

```
┌─────────────────────────────────────────────┐
│ Granite detects: "text block at [100,200]" │
└─────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────┐
│ PyMuPDF tries to read text inside          │
└─────────────────────────────────────────────┘
       ↓
   ┌─────────┐
   │ Found?  │
   └─────────┘
       ↓
   YES ←─┴─→ NO
    ↓           ↓
✅ Done    ┌──────────────────────┐
           │ OCR reads image of   │
           │ that bounding box    │
           └──────────────────────┘
                   ↓
           "Voltage: 500 kV"
```

**Your setup**: OCR is DISABLED (`do_ocr=False`)

So if PyMuPDF finds no text, that box stays EMPTY (no OCR fallback).

---

## Example: Table Extraction

### Stage 1: Granite Detects Table
```
Granite AI: "I see a table at [50, 350, 550, 600]"
Output: {"bbox": [50, 350, 550, 600], "label": "table"}
```

### Stage 2: PyMuPDF Reads Cell Text
```
PyMuPDF reads cell coordinates:
- Cell (0,0): "Header 1" at [60, 360, 140, 380]
- Cell (0,1): "Header 2" at [150, 360, 240, 380]
- Cell (1,0): "Value 1" at [60, 390, 140, 410]
- Cell (1,1): "Value 2" at [150, 390, 240, 410]
```

### Stage 3A: Basic Matching (Your Current Setup)
```python
# Simplified extraction (your current scripts)
{
    "bbox": [50, 350, 550, 600],
    "label": "table",
    "text": "Header 1\nHeader 2\nValue 1\nValue 2"
}
```

**Problem**: Loses table structure (rows/columns)!

### Stage 3B: TableFormer Detection (FAST/ACCURATE Mode)
```python
# TableFormer AI analyzes visual structure
TableFormer: "This table has 2 rows, 2 columns"

# Creates grid structure
grid = [
    [
        {"row": 0, "col": 0, "text": "Header 1"},
        {"row": 0, "col": 1, "text": "Header 2"}
    ],
    [
        {"row": 1, "col": 0, "text": "Value 1"},
        {"row": 1, "col": 1, "text": "Value 2"}
    ]
]
```

### Stage 4: Docling Native Export (BEST!)
```python
# Using save_as_json() includes FULL table structure
{
    "bbox": [50, 350, 550, 600],
    "label": "table",
    "data": {
        "grid": [
            [
                {"row": 0, "col": 0, "bbox": [60,360,140,380], "text": "Header 1"},
                {"row": 0, "col": 1, "bbox": [150,360,240,380], "text": "Header 2"}
            ],
            [
                {"row": 1, "col": 0, "bbox": [60,390,140,410], "text": "Value 1"},
                {"row": 1, "col": 1, "bbox": [150,390,240,410], "text": "Value 2"}
            ]
        ],
        "num_rows": 2,
        "num_cols": 2
    }
}
```

**This is why using `save_as_json()` is recommended!**

---

## Summary: Answering Your Question

### "How now I am finding text?"

**Answer**: Three-stage intelligent pipeline:

1. **Granite AI** scans page VISUALLY → Finds bounding boxes + labels
2. **PyMuPDF** reads PDF STRUCTURE → Extracts text with coordinates
3. **Docling** matches text to boxes → Combines structure + content

### "Just extract data directly from bounding box?"

**Answer**: NO! That would be:

```python
# ❌ WRONG APPROACH (pixel-based extraction):
def extract_text_from_bbox(pdf_image, bbox):
    # Crop image region
    region = pdf_image.crop(bbox)
    # OCR the region
    text = ocr_model.read(region)
    return text
```

**Problems with this approach**:
- ❌ Requires OCR for EVERY block (expensive)
- ❌ 85-90% accuracy (vs 99.9% for native)
- ❌ Slow (100-500ms per block)
- ❌ Wastes 1.5 GB VRAM for OCR model

**Correct approach (what Docling does)**:
```python
# ✅ CORRECT APPROACH (coordinate-based matching):
def match_text_to_bbox(pymupdf_text, granite_bbox):
    # Find text whose coordinates are inside bbox
    matched = [t for t in pymupdf_text
               if is_inside(t.coords, granite_bbox)]
    return "\n".join([t.text for t in matched])
```

**Advantages**:
- ✅ No OCR needed (fast, free)
- ✅ 99.9% accuracy (native PDF text)
- ✅ Instant (no AI inference)
- ✅ No extra VRAM

---

## Final Diagram: Complete Flow

```
┌────────────────────────────────────────────────────────────┐
│ PDF DOCUMENT                                               │
└────────────────────────────────────────────────────────────┘
            ↓                           ↓
    ┌───────────────┐          ┌───────────────┐
    │ As IMAGE      │          │ As STRUCTURE  │
    │ (pixels)      │          │ (PDF format)  │
    └───────────────┘          └───────────────┘
            ↓                           ↓
    ┌───────────────┐          ┌───────────────┐
    │ Granite-258M  │          │ PyMuPDF       │
    │ Vision AI     │          │ PDF Reader    │
    └───────────────┘          └───────────────┘
            ↓                           ↓
    ┌───────────────┐          ┌───────────────┐
    │ Bounding boxes│          │ Text strings  │
    │ + Labels      │          │ + Coordinates │
    └───────────────┘          └───────────────┘
            ↓                           ↓
            └───────────┬───────────────┘
                        ↓
            ┌───────────────────────┐
            │ Docling Matcher       │
            │ (Coordinate-based)    │
            └───────────────────────┘
                        ↓
            ┌───────────────────────┐
            │ FINAL OUTPUT          │
            │ Structure + Text      │
            └───────────────────────┘
```

---

## Key Takeaways

1. **Text is NOT extracted from pixels** - it's read from PDF structure (PyMuPDF)
2. **Bounding boxes come from AI vision** - Granite detects layout visually
3. **Matching is coordinate-based** - spatial algorithm, not image analysis
4. **OCR is only fallback** - when PyMuPDF finds no text (disabled in your setup)
5. **Your current approach is OPTIMAL** - native PDF text, no OCR waste
6. **Use `save_as_json()` for tables** - preserves full grid structure

**You are using the BEST method for native PDFs!** ✅
