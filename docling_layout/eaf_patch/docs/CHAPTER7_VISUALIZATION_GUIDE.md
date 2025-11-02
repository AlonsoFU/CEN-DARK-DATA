# Chapter 7 Visualization Guide

## 🎯 What's Being Generated

The script `visualize_chapter7_with_patch.py` is processing **Chapter 7 (Análisis de Causas de Falla)** with the power line classification patch applied.

### Chapter 7 Details:
- **Pages**: 266-347 (82 pages total)
- **Content**: Analysis of failure causes in the electrical system
- **Special elements**: Power transmission lines, substations, equipment lists

---

## 📁 Output Files

All files will be created in: `chapter7_visualization/`

### 1. **Annotated PDF**
`chapter_7_annotated_pages_266-347.pdf`

- **What it is**: Complete Chapter 7 PDF with colored bounding boxes drawn on each element
- **Colors**:
  - 🔵 **Blue** - Text blocks
  - 🔴 **Red** - Section headers / titles
  - 🟢 **Green** - Tables
  - 🔵🟢 **Cyan** - List items (includes power lines!) ⚡
  - 🟣 **Magenta** - Pictures/figures
  - 🟠 **Orange** - Formulas
  - ⚪ **Gray** - Headers/footers

- **Legend**: First page (266) has a legend showing all element types and counts

### 2. **Layout JSON**
`chapter_7_layout.json`

```json
{
  "metadata": {
    "chapter": "Chapter 7 - Análisis de Causas de Falla",
    "pages": "266-347",
    "total_elements": 1234,
    "power_line_items": 156,
    "patch_applied": "power_line_classification_patch"
  },
  "statistics": {
    "list_item": 450,
    "text": 320,
    "section_header": 45,
    ...
  },
  "elements": [
    {
      "type": "list_item",
      "text": "• Línea 220 kV Cerro Dominador - Sierra Gorda",
      "page": 305,
      "bbox": {"x0": 50.2, "y0": 123.4, "x1": 540.8, "y1": 138.2},
      "page_dimensions": {"width": 612, "height": 792}
    },
    ...
  ]
}
```

### 3. **Bounding Boxes CSV**
`chapter_7_bounding_boxes.csv`

Spreadsheet format with all coordinates:
```csv
type,page,x0,y0,x1,y1,page_width,page_height,text
list_item,305,50.20,123.40,540.80,138.20,612,792,"• Línea 220 kV..."
section_header,305,50.00,85.30,300.50,102.10,612,792,"7.1 Análisis..."
...
```

### 4. **Power Lines Only**
`chapter_7_power_lines.json`

Filtered list of ONLY power transmission lines:
```json
{
  "metadata": {
    "chapter": "Chapter 7",
    "total_power_lines": 156,
    "classification": "list_item (corrected by patch)"
  },
  "power_lines": [
    {
      "type": "list_item",
      "text": "• Línea 220 kV Cerro Dominador - Sierra Gorda",
      "page": 305,
      "bbox": {...}
    },
    ...
  ]
}
```

---

## ⏱️ Processing Time

**Estimated time**: 5-10 minutes for 82 pages

The script will show progress:
```
🔧 APPLYING POWER LINE CLASSIFICATION PATCH
✅ Power line patch applied successfully

📖 CHAPTER 7: Análisis de Causas de Falla
Pages: 266-347

🔍 Converting Chapter 7 (pages 266-347)...
   ⚠️  This will take ~5-10 minutes for 82 pages

🐵 [PATCH] Power Line Classification Fix
⚡ [PATCH] Found 15 power system list items
   ❌ [PATCH] AI misclassified as SECTION_HEADER: • Línea 220 kV...
   🗑️  [PATCH] Removed 3 misclassified SECTION_HEADER clusters
   ✅ [PATCH] Created 15 LIST_ITEM clusters for power lines

[This repeats for each page...]

✅ Conversion complete
📊 Extracting elements...
✅ Extracted 1234 elements

📊 STATISTICS:
   list_item            │  450 │ ████████████...
   text                 │  320 │ ████████...
   section_header       │   45 │ ████...
   table                │   89 │ ████...
   ...

⚡ Power line items: 156

🎨 Creating annotated PDF with bounding boxes...
📦 Drew 1234 bounding boxes
✅ Annotated PDF saved
✅ JSON saved
✅ CSV saved
⚡ Power lines extracted

✅ VISUALIZATION COMPLETE
```

---

## 🔍 What The Patch Does

### Before Patch (Inconsistent):
```
Page 305:
• Línea 220 kV Cerro Dominador → section_header ❌
• Línea 110 kV Diego de Almagro → list_item ✅
• Línea 220 kV Kapatur → section_header ❌

Result: INCONSISTENT!
```

### After Patch (Consistent):
```
Page 305:
• Línea 220 kV Cerro Dominador → list_item ✅ (corrected!)
• Línea 110 kV Diego de Almagro → list_item ✅
• Línea 220 kV Kapatur → list_item ✅ (corrected!)

Result: 100% CONSISTENT!
```

---

## 📊 Expected Statistics

Based on Chapter 7 content, you should see approximately:

| Element Type | Count (approx) | Description |
|--------------|----------------|-------------|
| `list_item` | 400-500 | Lists (including power lines) |
| `text` | 300-400 | Regular text blocks |
| `section_header` | 40-60 | Section titles |
| `table` | 80-100 | Tables |
| `picture` | 20-40 | Figures/diagrams |
| `formula` | 10-20 | Equations |

**Power line items**: 100-200 (all classified as `list_item` ✅)

---

## ✅ How To Verify Success

### 1. Check the annotated PDF:
Open `chapter_7_annotated_pages_266-347.pdf`

- Go to page 305 (PDF page 305)
- Look for lines starting with `• Línea XXX kV`
- **All should have CYAN boxes** (list_item color)
- **None should have RED boxes** (section_header color)

### 2. Check the statistics:
```bash
cd chapter7_visualization
cat chapter_7_layout.json | grep -A 5 "metadata"
```

Should show:
```json
"metadata": {
  "power_line_items": 156,  // Should be > 0
  "patch_applied": "power_line_classification_patch"
}
```

### 3. Check power lines file:
```bash
cat chapter_7_power_lines.json | grep -c "Línea"
```

Should return a number > 100

### 4. Verify no misclassifications:
Search the JSON for power lines classified as section_header:
```bash
grep -E "section_header.*Línea.*kV" chapter_7_layout.json
```

**Should return NOTHING** (empty result = success!)

---

## 🚀 Next Steps

Once the visualization is complete:

1. **Open the annotated PDF** and visually inspect pages with power lines
2. **Check the power_lines.json** to see all detected power transmission lines
3. **Use the CSV** to analyze patterns or import into Excel/Pandas
4. **Compare with PyMuPDF results** to validate improvements

---

## 💡 Tips

### Find specific pages with power lines:
```bash
cd chapter7_visualization
grep -o '"page": [0-9]*' chapter_7_power_lines.json | sort -u
```

### Count power lines per page:
```bash
python3 << 'EOF'
import json
with open('chapter7_visualization/chapter_7_power_lines.json') as f:
    data = json.load(f)

pages = {}
for line in data['power_lines']:
    page = line['page']
    pages[page] = pages.get(page, 0) + 1

for page in sorted(pages.keys()):
    print(f"Page {page}: {pages[page]} power lines")
EOF
```

### Extract all unique power line texts:
```bash
python3 << 'EOF'
import json
with open('chapter7_visualization/chapter_7_power_lines.json') as f:
    data = json.load(f)

for line in data['power_lines']:
    text = line['text'].strip()
    if text:
        print(text)
EOF
```

---

## ⚠️ Troubleshooting

### If the script takes too long (>15 min):
- **Normal for 82 pages** - each page takes ~5-10 seconds
- Check GPU usage: `nvidia-smi`
- If GPU crashes, script will fall back to CPU (much slower)

### If no power lines are found:
- Check that patch was applied (look for patch messages in output)
- Verify PDF contains power line text patterns
- Try a specific page known to have power lines (e.g., page 305)

### If some power lines are still misclassified:
- Check `power_line_classifier.py` patterns
- May need to add more regex patterns for edge cases
- Review the misclassified text to identify patterns

---

**Status**: Script is currently running... Check progress with:
```bash
ps aux | grep visualize_chapter7
```

Expected completion: ~5-10 minutes from start time.
