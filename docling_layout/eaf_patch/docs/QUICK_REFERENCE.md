# Quick Reference Card - Power Line Classification Patch

## ⚠️ CRITICAL: Use Split PDFs!

**Read**: [`CRITICAL_PDF_PATHS.md`](./CRITICAL_PDF_PATHS.md)

```
Chapter PDFs location: .../claude_ocr/capitulo_XX/EAF-089-2025_capitulo_XX_pages_YYY-ZZZ.pdf
Benefit: 4x faster (5 min vs 22 min for Chapter 6)
```

---

## 🚀 Fast Commands

### Process Chapter 7 with Patch
```bash
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout
python REPROCESS_chapter7_with_patch.py
```

### Monitor Progress
```bash
./monitor_processing.sh
```

### View Annotated PDF
```bash
xdg-open capitulo_07/outputs_WITH_PATCH/chapter7_FIXED_WITH_BBOXES.pdf
```

### Check Power Lines
```bash
cat capitulo_07/outputs_WITH_PATCH/power_lines_ONLY.json | jq '.classification_breakdown'
```

---

## 📁 Key File Locations

### Production Files
```
power_line_classifier.py              ← Pattern detector
patch_power_lines.py                  ← Monkey patch
REPROCESS_chapter7_with_patch.py      ← Main script
```

### Output Files
```
capitulo_07/outputs_WITH_PATCH/
├── layout_WITH_PATCH.json            ← Complete layout (fixed)
├── power_lines_ONLY.json             ← Power lines only
└── chapter7_FIXED_WITH_BBOXES.pdf    ← Annotated PDF
```

### Documentation
```
POWER_LINE_PATCH_README.md            ← 📖 Complete guide (START HERE)
FILE_ORGANIZATION.md                  ← File structure
README.md                             ← Updated main README
```

---

## 🎯 Results

### Before Patch
```json
{
  "classification_breakdown": {
    "section_header": 3,  // 60% ❌
    "list_item": 2        // 40% ✅
  }
}
```

### After Patch
```json
{
  "classification_breakdown": {
    "list_item": 20       // 100% ✅
  }
}
```

---

## 🔧 How It Works (Simple)

```
1. Apply patch BEFORE creating Docling converter
   ↓
2. Docling processes PDF normally
   ↓
3. Patch intercepts layout post-processing
   ↓
4. Detects power lines: "Línea XXX kV"
   ↓
5. Fixes AI misclassifications
   ↓
6. Returns corrected results to Docling
   ↓
7. Final output: 100% consistency!
```

---

## 📊 Statistics

| Element Type | Count | Percentage |
|--------------|-------|------------|
| text | 139 | 39.8% |
| table | 61 | 17.5% |
| picture | 57 | 16.3% |
| **list_item** | **50** | **14.3%** ⭐ |
| section_header | 38 | 10.9% |
| caption | 4 | 1.1% |

**Power lines**: 20 out of 50 list_items (40%)

---

## 🎨 Color Coding

In annotated PDF:
- 🔵 **Blue** - Text
- 🟢 **Green** - Tables
- 🟣 **Magenta** - Pictures
- **🔵🟢 Cyan** - **List items (power lines!)** ⭐
- 🔴 **Red** - Section headers

---

## 🐛 Quick Troubleshooting

### Patch not finding power lines?
```python
# Check patterns in power_line_classifier.py
POWER_LINE_PATTERNS = [
    r'[•·\-\*]\s+Líneas?\s+\d+\s*[kK][vV]',  # With bullet
    r'^\s*Línea\s+\d+\s*[kK][vV]',           # Without bullet
]
```

### Process failing?
```bash
# Check log file
tail -50 chapter7_reprocess_FINAL.log
```

### Need to reprocess?
```bash
# Clean output directory
rm -rf capitulo_07/outputs_WITH_PATCH/*

# Run again
python REPROCESS_chapter7_with_patch.py
```

---

## 📚 Documentation Index

### For Quick Start
1. Read: `POWER_LINE_PATCH_README.md` (sections 1-4)
2. Run: `python REPROCESS_chapter7_with_patch.py`
3. View: Annotated PDF

### For Understanding
1. `MONKEY_PATCH_FLOW_DIAGRAM.md` - Visual diagrams
2. `WHY_MONKEY_PATCH.md` - Concept explanation
3. `POWER_LINE_PATCH_README.md` - Complete technical details

### For Development
1. `power_line_classifier.py` - Add new patterns here
2. `patch_power_lines.py` - Modify patch logic here
3. `FILE_ORGANIZATION.md` - File structure reference

---

## 🔄 Workflow for New Chapters

```bash
# 1. Copy files
cp power_line_classifier.py ../capitulo_08/
cp patch_power_lines.py ../capitulo_08/

# 2. Create processing script
cp REPROCESS_chapter7_with_patch.py ../capitulo_08/REPROCESS_chapter8_with_patch.py

# 3. Update paths in script
# Edit: pdf_path, output_dir, chapter metadata

# 4. Run
cd ../capitulo_08/
python REPROCESS_chapter8_with_patch.py
```

---

## ⚡ Performance

| Task | Time | Resources |
|------|------|-----------|
| Process 82 pages | ~3 min | 1.3 GB GPU |
| Single page test | ~30 sec | 1.3 GB GPU |
| Generate PDF | ~5 sec | Minimal |

---

## 📞 When You Return

**Checklist to resume work:**

- [ ] Read `POWER_LINE_PATCH_README.md`
- [ ] Check `capitulo_07/outputs_WITH_PATCH/` for latest results
- [ ] Review `chapter7_reprocess_FINAL.log` for what happened
- [ ] Test with: `python visualize_page305_with_patch.py`
- [ ] Open annotated PDF to see results

**Remember:**
- Patch is in: `patch_power_lines.py`
- Patterns in: `power_line_classifier.py`
- Main script: `REPROCESS_chapter7_with_patch.py`

---

**Last Updated**: 2025-10-19
**Status**: ✅ Production Ready
**Accuracy**: 100% on Chapter 7 (20 power lines detected)
