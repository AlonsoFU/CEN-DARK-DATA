# Universal Docling + EAF Patch Methodology

**Purpose**: Standard methodology for extracting any PDF using Docling + custom patches  
**Last Updated**: 2025-10-26  
**Status**: Production-ready ✅

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Docling Label System](#docling-label-system)
4. [EAF Patch Pipeline](#eaf-patch-pipeline)
5. [Step-by-Step Workflow](#step-by-step-workflow)
6. [Customization Guide](#customization-guide)
7. [Code Templates](#code-templates)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Methodology Does

1. **Runs Docling extraction** - IBM Docling Granite-258M layout model
2. **Applies custom patch** - Fills gaps in Docling extraction using PyMuPDF
3. **Generates visualizations** - Color-coded PDFs with bounding boxes
4. **Produces JSON outputs** - Structured data with all elements

### When to Use This

✅ **Use for**:
- Multi-page technical documents (reports, manuals, specifications)
- Documents with complex layouts (tables, lists, formulas)
- Documents needing precise bounding box coordinates
- Documents where 100% extraction accuracy is critical

⚠️ **Consider alternatives for**:
- Simple single-page documents (use PyMuPDF directly)
- Scanned documents without OCR (enable Docling OCR first)
- Documents >1000 pages (batch processing required)

---

## Core Architecture

### Component Stack

```
┌─────────────────────────────────────────────────┐
│  PDF Document (Any format)                       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Docling Granite-258M Layout Model              │
│  - Detects 11 element types                     │
│  - Provides bounding boxes                       │
│  - 97.9% table accuracy                          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  EAF Monkey Patch (Intercepts during extraction)│
│  - Compares Docling vs PyMuPDF                  │
│  - Detects missing content (<50% coverage)      │
│  - Creates synthetic clusters for gaps          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Output: JSON + Annotated PDF                   │
│  - Complete element list                        │
│  - Bounding box coordinates                      │
│  - Color-coded visualization                     │
└─────────────────────────────────────────────────┘
```

### File Structure Template

```
your_document/
├── outputs/
│   ├── layout_native.json           # Docling without patch
│   ├── layout_patched.json          # Docling with patch
│   ├── patch_input_to_docling.json  # What patch gives TO Docling
│   ├── patch_input_to_docling.pdf   # Visual bounding boxes
│   └── EXTRACTION_SUMMARY.md        # Results documentation
├── scripts/
│   ├── extract_WITH_PATCH.py        # Main extraction script
│   ├── visualize_extraction.py      # PDF visualization
│   └── regenerate_colored_pdf.py    # Re-color existing PDF
└── docs/
    └── extraction_config.json        # Document-specific settings
```

---

## Docling Label System

### All 11 Docling Element Types

Docling's Granite-258M model detects these element types:

| Label | Enum Value | Description | Typical Use |
|-------|------------|-------------|-------------|
| `text` | `DocItemLabel.TEXT` | Regular paragraph text | Body content, descriptions |
| `section_header` | `DocItemLabel.SECTION_HEADER` | Section/subsection headers | "1. Introduction", "3.2 Methods" |
| `title` | `DocItemLabel.TITLE` | Document/page titles | Main document title |
| `list_item` | `DocItemLabel.LIST_ITEM` | Bulleted/numbered list items | "• Item 1", "a) Option A" |
| `table` | `DocItemLabel.TABLE` | Tables and grids | Data tables, comparison charts |
| `picture` | `DocItemLabel.PICTURE` | Images and figures | Photos, diagrams, illustrations |
| `caption` | `DocItemLabel.CAPTION` | Figure/table captions | "Figure 1: System diagram" |
| `formula` | `DocItemLabel.FORMULA` | Mathematical equations | LaTeX formulas, expressions |
| `footnote` | `DocItemLabel.FOOTNOTE` | Footnotes | Bottom-of-page references |
| `page_header` | `DocItemLabel.PAGE_HEADER` | Page headers | Running headers, chapter names |
| `page_footer` | `DocItemLabel.PAGE_FOOTER` | Page footers | Page numbers, copyright |

### Color Mapping (Standard)

```python
DOCLING_COLORS = {
    'text': (0, 0, 1),                 # Blue - Body text
    'section_header': (1, 0, 0),       # Red - Headers
    'title': (1, 0.5, 0),              # Orange - Titles
    'list_item': (0, 0.7, 0.7),        # Cyan - Lists
    'table': (0, 0.7, 0),              # Green - Tables
    'picture': (1, 0, 1),              # Magenta - Images
    'caption': (0.8, 0.4, 0),          # Brown - Captions
    'formula': (1, 0.8, 0),            # Yellow - Formulas
    'footnote': (0.8, 0.4, 0),         # Brown - Footnotes
    'page_header': (0.5, 0.5, 0.5),    # Gray - Headers
    'page_footer': (0.5, 0.5, 0.5),    # Gray - Footers
}
```

### JSON Structure (Docling Output)

```json
{
  "metadata": {
    "chapter": "Document Name",
    "extractor": "Docling + EAF Patch v2.0",
    "extraction_date": "2025-10-26T02:08:01.748498",
    "total_elements": 4719
  },
  "elements": [
    {
      "type": "section_header",
      "text": "7. Análisis de las causas de la falla",
      "page": 0,
      "bbox": {
        "x0": 56.8,
        "y0": 123.45,
        "x1": 538.24,
        "y1": 135.67
      }
    },
    {
      "type": "text",
      "text": "El presente análisis considera...",
      "page": 0,
      "bbox": {
        "x0": 56.8,
        "y0": 145.23,
        "x1": 538.24,
        "y1": 167.89
      }
    }
  ]
}
```

---

## EAF Patch Pipeline

### Patch Architecture

The EAF patch **monkey-patches** Docling's internal layout processor:

```python
# BEFORE: Docling's original method
LayoutPostprocessor._process_regular_clusters(self)
  → Returns clusters detected by Docling

# AFTER: Patched method (intercepts during processing)
def _patched_process_regular_clusters(self):
    # 1. Let Docling process normally
    docling_clusters = original_method(self)
    
    # 2. Extract text from PDF using PyMuPDF
    pymupdf_lines = extract_text_with_pymupdf(page)
    
    # 3. Calculate coverage (what % of PyMuPDF is in Docling)
    for line in pymupdf_lines:
        coverage = calculate_overlap_with_docling(line, docling_clusters)
        if coverage < 50%:
            missing_lines.append(line)
    
    # 4. Detect special patterns in missing lines ONLY
    missing_titles = detect_titles(missing_lines)
    missing_power_lines = detect_power_lines(missing_lines)
    
    # 5. Create synthetic clusters for missing content
    synthetic_clusters = create_clusters(missing_titles, missing_power_lines)
    
    # 6. Return combined list
    return docling_clusters + synthetic_clusters
```

### Key Functions

#### 1. `apply_universal_patch_with_pdf(pdf_path)`

**Location**: `eaf_patch/core/eaf_patch_engine.py`

**Purpose**: Applies monkey patch to Docling

**Usage**:
```python
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Apply patch BEFORE running Docling
apply_universal_patch_with_pdf("/path/to/document.pdf")

# Now run Docling (patch intercepts automatically)
converter = DocumentConverter(format_options=format_options)
result = converter.convert("/path/to/document.pdf")
```

#### 2. `bbox_overlap_ratio(pymupdf_bbox, docling_bbox)`

**Location**: `eaf_patch/core/eaf_patch_engine.py:100-120`

**Purpose**: Calculates what % of PyMuPDF line is covered by Docling box

**Algorithm**:
```python
def bbox_overlap_ratio(line_bbox, cluster_bbox):
    """
    Returns: 0.0 to 1.0 (percentage of line covered by cluster)
    
    Example:
      Line:    [100, 200, 500, 220]  (400 pixels wide)
      Cluster: [150, 195, 350, 225]  (200 pixels overlap)
      Result:  200/400 = 0.5 (50% coverage)
    """
    intersection = get_intersection_area(line_bbox, cluster_bbox)
    line_area = get_area(line_bbox)
    return intersection / line_area if line_area > 0 else 0.0
```

#### 3. `EafTitleDetector.is_missing_title(text)`

**Location**: `eaf_patch/core/eaf_title_detector.py:50-150`

**Purpose**: Detects numbered section headers

**Patterns Detected**:
```python
title_patterns = [
    r'^\s*(\d+)\.\s+.+',           # "7. Title"
    r'^\s*(\d+\.\d+)\s+.+',        # "7.1 Subtitle"
    r'^\s*(\d+\.\d+\.\d+)\s+.+',   # "7.1.1 Sub-subtitle"
    r'^\s*([a-z])\.\s+.+',         # "a. Item"
    r'^\s*([a-z]\.\d+)\s+.+',      # "a.1 Sub-item"
]
```

**Example**:
```python
detector = EafTitleDetector()
result = detector.is_missing_title("7.2 Análisis de causas")
# Returns: {'is_title': True, 'level': 2, 'number': '7.2'}
```

#### 4. `PowerLineClassifier.is_power_system_list_item(text)`

**Location**: `eaf_patch/core/eaf_power_line_classifier.py:80-120`

**Purpose**: Detects electrical system elements

**Patterns Detected**:
```python
power_patterns = [
    r'\d+x\d+\s*kV',                    # "2x220 kV"
    r'línea.*\d+\s*kV',                 # "línea 220 kV"
    r'S/E\s+[\w\s]+',                   # "S/E Maitencillo"
    r'subestación\s+[\w\s]+',           # "subestación Pan de Azúcar"
    r'transformador.*\d+\s*MVA',        # "transformador 100 MVA"
]
```

---

## Step-by-Step Workflow

### Phase 1: Setup (5 minutes)

#### 1.1 Directory Structure
```bash
cd /path/to/project
mkdir -p your_document/{outputs,scripts,docs}
```

#### 1.2 Configuration File

Create `your_document/docs/extraction_config.json`:

```json
{
  "document": {
    "name": "Your Document Name",
    "pdf_path": "/full/path/to/document.pdf",
    "total_pages": 100,
    "page_range": "1-100"
  },
  "docling": {
    "do_ocr": false,
    "do_table_structure": true,
    "table_mode": "FAST"
  },
  "patch": {
    "enabled": true,
    "coverage_threshold": 0.5,
    "detect_titles": true,
    "detect_custom_patterns": true,
    "custom_patterns": {
      "patterns": [],
      "description": "Document-specific patterns to detect"
    }
  },
  "visualization": {
    "colors": "standard",
    "legend_position": "top-right",
    "custom_colors": {}
  }
}
```

### Phase 2: Extraction (10-20 minutes)

#### 2.1 Basic Extraction Script

Create `your_document/scripts/extract_WITH_PATCH.py`:

```python
#!/usr/bin/env python3
"""
Universal Docling + Patch Extraction Script
Customize the configuration section for your document
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add eaf_patch to path
eaf_patch_path = Path(__file__).parent.parent.parent / "eaf_patch"
sys.path.insert(0, str(eaf_patch_path))

# ============================================================================
# CONFIGURATION - Customize for your document
# ============================================================================

DOCUMENT_NAME = "Your Document Name"
PDF_PATH = Path("/full/path/to/your/document.pdf")
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Docling configuration
DOCLING_CONFIG = {
    "do_ocr": False,           # Enable if scanned document
    "do_table_structure": True,
    "table_mode": "FAST"       # Options: FAST, ACCURATE
}

# Patch configuration
PATCH_CONFIG = {
    "enabled": True,
    "coverage_threshold": 0.5,  # 50% - lines with less coverage = missing
    "detect_titles": True,
    "detect_custom_patterns": True
}

# ============================================================================
# EXTRACTION LOGIC (Don't modify unless needed)
# ============================================================================

print("=" * 80)
print(f"🔄 EXTRACTING: {DOCUMENT_NAME}")
print("=" * 80)

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from core.eaf_patch_engine import apply_universal_patch_with_pdf

# Apply patch if enabled
if PATCH_CONFIG['enabled']:
    print("\n🐵 Applying EAF patch...")
    apply_universal_patch_with_pdf(str(PDF_PATH))
else:
    print("\n⚠️  Running WITHOUT patch (native Docling only)")

# Configure Docling
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = DOCLING_CONFIG['do_ocr']
pipeline_options.do_table_structure = DOCLING_CONFIG['do_table_structure']

if DOCLING_CONFIG['table_mode'] == 'ACCURATE':
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
else:
    pipeline_options.table_structure_options.mode = TableFormerMode.FAST

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# Run extraction
print("\n🔄 Running Docling extraction...")
converter = DocumentConverter(format_options=format_options)
result = converter.convert(str(PDF_PATH))

print("✅ Extraction complete")

# Extract elements
elements = []
for item, level in result.document.iterate_items():
    page_num = None
    if hasattr(item, 'prov') and item.prov:
        page_num = item.prov[0].page_no if item.prov else None
    
    if page_num is not None:
        bbox_dict = None
        if hasattr(item, 'prov') and item.prov:
            prov = item.prov[0]
            if hasattr(prov, 'bbox'):
                if page_num in result.document.pages:
                    page = result.document.pages[page_num]
                    bbox_tl = prov.bbox.to_top_left_origin(page_height=page.size.height)
                    bbox_dict = {
                        'x0': bbox_tl.l,
                        'y0': bbox_tl.t,
                        'x1': bbox_tl.r,
                        'y1': bbox_tl.b
                    }
        
        elements.append({
            'type': item.label,  # PRESERVES FULL DOCLING LABEL
            'text': item.text if hasattr(item, 'text') else '',
            'page': page_num,
            'bbox': bbox_dict,
            'level': level
        })

# Save JSON
output_json = OUTPUT_DIR / "layout_WITH_PATCH.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'document': DOCUMENT_NAME,
            'extractor': 'Docling + EAF Patch v2.0' if PATCH_CONFIG['enabled'] else 'Docling Native',
            'extraction_date': datetime.now().isoformat(),
            'total_elements': len(elements),
            'config': {
                'docling': DOCLING_CONFIG,
                'patch': PATCH_CONFIG
            }
        },
        'elements': elements
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved: {output_json.name}")
print(f"📊 Total elements: {len(elements)}")

# Statistics
stats = {}
for elem in elements:
    elem_type = elem['type']
    stats[elem_type] = stats.get(elem_type, 0) + 1

print("\n📊 Elements by type:")
for elem_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f"   {elem_type:<30}: {count:>4}")

print("=" * 80)
```

#### 2.2 Run Extraction
```bash
cd your_document/scripts
python3 extract_WITH_PATCH.py
```

### Phase 3: Visualization (5 minutes)

Create `your_document/scripts/visualize_extraction.py`:

```python
#!/usr/bin/env python3
"""
Universal PDF Visualization Script
Creates color-coded PDF with bounding boxes
"""
import json
import fitz
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

PDF_PATH = Path("/full/path/to/your/document.pdf")
INPUT_JSON = Path(__file__).parent.parent / "outputs" / "layout_WITH_PATCH.json"
OUTPUT_PDF = Path(__file__).parent.parent / "outputs" / "annotated_document.pdf"

# Standard Docling colors (customize if needed)
COLORS = {
    'text': (0, 0, 1),
    'section_header': (1, 0, 0),
    'title': (1, 0.5, 0),
    'list_item': (0, 0.7, 0.7),
    'table': (0, 0.7, 0),
    'picture': (1, 0, 1),
    'caption': (0.8, 0.4, 0),
    'formula': (1, 0.8, 0),
    'footnote': (0.8, 0.4, 0),
    'page_header': (0.5, 0.5, 0.5),
    'page_footer': (0.5, 0.5, 0.5),
}

# ============================================================================
# VISUALIZATION LOGIC
# ============================================================================

print("=" * 80)
print("🎨 Creating Annotated PDF")
print("=" * 80)

# Load JSON
with open(INPUT_JSON) as f:
    data = json.load(f)

elements = data['elements']
print(f"\n📄 Loading {len(elements)} elements...")

# Open PDF
doc = fitz.open(PDF_PATH)

# Group elements by page
pages_data = {}
for elem in elements:
    page = elem['page']
    if page not in pages_data:
        pages_data[page] = []
    pages_data[page].append(elem)

# Draw boxes on each page
boxes_drawn = 0
color_counts = {}

for page_num, page_elements in pages_data.items():
    if page_num < 0 or page_num >= len(doc):
        continue
    
    page = doc[page_num]
    
    for elem in page_elements:
        if not elem.get('bbox'):
            continue
        
        bbox = elem['bbox']
        # Extract label name (handles both "text" and "DocItemLabel.TEXT")
        label = elem['type']
        if isinstance(label, str) and '.' in label:
            label = label.split('.')[-1].lower()
        else:
            label = str(label).lower()
        
        # Get color
        color = COLORS.get(label, (0.5, 0.5, 0.5))
        
        # Count colors
        color_counts[label] = color_counts.get(label, 0) + 1
        
        # Draw rectangle
        rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
        page.draw_rect(rect, color=color, width=2)
        
        boxes_drawn += 1

print(f"\n✅ Drew {boxes_drawn} boxes")
print("\n📊 Elements by type:")
for label, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
    color = COLORS.get(label, (0.5, 0.5, 0.5))
    print(f"   {label:<20}: {count:>4} boxes")

# Add legend on first page
page = doc[0]
legend_x = 450
legend_y = 600
legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 160, legend_y + 120)
page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
page.insert_text(fitz.Point(legend_x, legend_y), "Element Types:", fontsize=9, color=(0, 0, 0))

y_offset = legend_y + 15
for label in sorted(color_counts.keys()):
    color = COLORS.get(label, (0.5, 0.5, 0.5))
    color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
    page.draw_rect(color_rect, color=color, fill=color, width=0)
    page.insert_text(fitz.Point(legend_x + 15, y_offset), f"{label} ({color_counts[label]})", fontsize=7, color=(0, 0, 0))
    y_offset += 10

# Save PDF
doc.save(OUTPUT_PDF)
doc.close()

print(f"\n✅ Saved: {OUTPUT_PDF}")
print("=" * 80)
```

Run visualization:
```bash
python3 visualize_extraction.py
```

---

## Customization Guide

### Document-Specific Patterns

To add custom patterns for YOUR document type:

1. **Create pattern detector** in `eaf_patch/core/your_document_detector.py`:

```python
class YourDocumentDetector:
    """Detects patterns specific to your document type"""
    
    def __init__(self):
        self.patterns = [
            # Add your patterns here
            re.compile(r'your_pattern_here'),
        ]
    
    def is_your_pattern(self, text):
        """
        Returns True if text matches your pattern
        """
        for pattern in self.patterns:
            if pattern.match(text.strip()):
                return True
        return False
```

2. **Import in patch engine** (`eaf_patch_engine.py`):

```python
from core.your_document_detector import YourDocumentDetector

# In _patched_process_regular_clusters():
your_detector = YourDocumentDetector()

for block in missing_line_blocks:
    if your_detector.is_your_pattern(block['text']):
        your_pattern_blocks.append(block)
```

3. **Create clusters** for your patterns:

```python
for block in your_pattern_blocks:
    cluster = create_synthetic_cluster(
        text=block['text'],
        bbox=block['bbox'],
        label=DocItemLabel.YOUR_LABEL  # Choose appropriate label
    )
    synthetic_clusters.append(cluster)
```

### Coverage Threshold

Adjust coverage threshold in extraction config:

```python
PATCH_CONFIG = {
    "coverage_threshold": 0.3,  # Lower = more sensitive (catches more)
                                 # Higher = less sensitive (catches less)
}
```

**Guidelines**:
- `0.3` (30%) - Very sensitive, catches partial overlaps
- `0.5` (50%) - Default, balanced
- `0.7` (70%) - Conservative, only catches clearly missing content

### Custom Colors

Override default colors in visualization config:

```python
COLORS = {
    'text': (0, 0, 1),           # Blue
    'section_header': (1, 0, 0), # Red
    # Add custom colors for your document
    'custom_type': (0.2, 0.8, 0.5),  # Custom green
}
```

---

## Code Templates

### Template 1: Batch Processing Multiple Documents

```python
#!/usr/bin/env python3
"""
Batch process multiple documents with same methodology
"""
from pathlib import Path
import subprocess

DOCUMENTS = [
    {
        "name": "Chapter 2",
        "pdf": "/path/to/chapter_02.pdf",
        "output_dir": "chapter_02/outputs"
    },
    {
        "name": "Chapter 3",
        "pdf": "/path/to/chapter_03.pdf",
        "output_dir": "chapter_03/outputs"
    },
]

for doc in DOCUMENTS:
    print(f"\n{'='*80}")
    print(f"Processing: {doc['name']}")
    print(f"{'='*80}")
    
    # Run extraction
    subprocess.run([
        "python3", "extract_WITH_PATCH.py",
        "--pdf", doc['pdf'],
        "--output", doc['output_dir'],
        "--name", doc['name']
    ])
    
    # Run visualization
    subprocess.run([
        "python3", "visualize_extraction.py",
        "--json", f"{doc['output_dir']}/layout_WITH_PATCH.json",
        "--pdf", doc['pdf'],
        "--output", f"{doc['output_dir']}/annotated.pdf"
    ])

print("\n✅ Batch processing complete!")
```

### Template 2: Compare Native vs Patched

```python
#!/usr/bin/env python3
"""
Compare Docling native extraction vs patched extraction
"""
import json

# Load both JSONs
with open('outputs/layout_native.json') as f:
    native = json.load(f)

with open('outputs/layout_WITH_PATCH.json') as f:
    patched = json.load(f)

native_elements = native['elements']
patched_elements = patched['elements']

# Find additions
native_texts = {(e['text'].strip(), e['page']) for e in native_elements}
patched_texts = {(e['text'].strip(), e['page']) for e in patched_elements}
additions = patched_texts - native_texts

print(f"Native: {len(native_elements)} elements")
print(f"Patched: {len(patched_elements)} elements")
print(f"Patch added: {len(additions)} elements")

# Show additions
if additions:
    patch_additions = [e for e in patched_elements if (e['text'].strip(), e['page']) in additions]
    print("\n🔴 Patch additions:")
    for i, elem in enumerate(patch_additions[:10], 1):
        print(f"   {i}. [{elem['type']}] Page {elem['page']}: {elem['text'][:60]}...")
```

---

## Troubleshooting

### Issue 1: Duplicate Clusters

**Symptom**: Elements appearing twice, "boxes inside boxes"

**Cause**: Patch processing content Docling already extracted

**Fix**: Ensure patch only processes `missing_line_blocks`, NOT `all_blocks`

```python
# WRONG
for block in all_blocks:  # Includes Docling blocks!
    detect_patterns(block)

# CORRECT
for block in missing_line_blocks:  # Only truly missing content
    detect_patterns(block)
```

### Issue 2: Missing Colors in PDF

**Symptom**: All boxes are gray

**Cause**: Label name mismatch (uppercase vs lowercase, enum format)

**Fix**: Normalize label names before color lookup

```python
# Handle all label formats
label = elem['type']
if isinstance(label, str) and '.' in label:
    label = label.split('.')[-1].lower()  # "DocItemLabel.TEXT" → "text"
else:
    label = str(label).lower()

color = COLORS.get(label, (0.5, 0.5, 0.5))
```

### Issue 3: GPU Out of Memory

**Symptom**: CUDA error, process crashes

**Cause**: Docling models too large for GPU

**Solutions**:
1. Use lightweight mode (1.3 GB):
```python
pipeline_options.do_ocr = False
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
```

2. Use CPU mode (slower but works):
```python
import torch
torch.set_default_device('cpu')
```

3. Process in batches (split PDF into smaller parts)

### Issue 4: Low Coverage Detection

**Symptom**: Patch creates too many/too few synthetic clusters

**Cause**: Coverage threshold not tuned for document

**Fix**: Adjust threshold based on document type

```python
# For dense technical documents (less gaps expected)
PATCH_CONFIG['coverage_threshold'] = 0.7  # 70%

# For sparse documents (more gaps expected)
PATCH_CONFIG['coverage_threshold'] = 0.3  # 30%
```

---

## Best Practices

### 1. Always Preserve Docling Labels

✅ **DO**:
```python
elements.append({
    'type': item.label,  # Full Docling label
    'text': item.text,
    'page': page_num,
    'bbox': bbox_dict
})
```

❌ **DON'T**:
```python
elements.append({
    'type': 'text',  # Hardcoded - loses Docling classification!
})
```

### 2. Test on Sample Pages First

Before processing entire document:
```python
# Test on first 5 pages
result = converter.convert(str(PDF_PATH), pages=[0, 1, 2, 3, 4])
```

### 3. Version Control Configuration

Track document-specific settings:
```bash
git add your_document/docs/extraction_config.json
git commit -m "Add extraction config for Document X"
```

### 4. Document Customizations

Always document what you changed:
```python
# your_document/docs/CUSTOMIZATIONS.md

## Document-Specific Customizations

1. **Coverage Threshold**: Set to 0.3 (lower than default)
   - Reason: Document has many small gaps
   
2. **Custom Pattern**: Added detection for "Article X.Y" format
   - Location: custom_article_detector.py
   - Pattern: r'^Article\s+\d+\.\d+'
```

---

## Next Steps

After running this methodology:

1. ✅ **Verify outputs** - Check JSON and PDF for accuracy
2. ✅ **Compare native vs patched** - See what patch added
3. ✅ **Adjust threshold** - Tune for your document type
4. ✅ **Add custom patterns** - Document-specific detectors
5. ✅ **Document results** - Create EXTRACTION_SUMMARY.md
6. ✅ **Apply to similar documents** - Reuse configuration

---

**Last Updated**: 2025-10-26  
**Tested On**: EAF Chapter 7 (82 pages, 4,719 elements)  
**Status**: Production-ready ✅
