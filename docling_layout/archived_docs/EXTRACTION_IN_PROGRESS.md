# Docling Sequential Extraction - IN PROGRESS

## Status: ✅ RUNNING

**Started**: October 15, 2025 at 22:54
**Mode**: Sequential (one chapter at a time)
**Chapters to Process**: 4 remaining (2, 3, 4, 7)
**Memory Usage**: ~1.2 GB (lightweight mode)
**Device**: CUDA GPU (GTX 1650 with Max-Q)
**Estimated Completion**: ~5.8 hours (~04:48 AM Oct 16)

---

## 📊 Extraction Plan

### Chapters Status:
1. ✅ **Chapter 1** - Already completed (11 pages)
2. 🔄 **Chapter 2** - Processing/queued (79 pages, ~2.0 hours)
3. 🔄 **Chapter 3** - Queued (63 pages, ~1.6 hours)
4. 🔄 **Chapter 4** - Queued (6 pages, ~0.2 hours)
5. ✅ **Chapter 5** - Already completed (12 pages)
6. ✅ **Chapter 6** - Already completed (94 pages)
7. 🔄 **Chapter 7** - Queued (82 pages, ~2.1 hours)
8. ✅ **Chapter 8** - Already completed (1 page)
9. ✅ **Chapter 9** - Already completed (33 pages)
10. ✅ **Chapter 10** - Already completed (11 pages)
11. ✅ **Chapter 11** - Already completed (7 pages)

**Total to Process**: 4 chapters (230 pages)
**Already Completed**: 7 chapters (169 pages)

---

## Expected Timeline

| Chapter | Pages | Duration | Completion (Est.) |
|---------|-------|----------|-------------------|
| 2 | 79 | ~2.0h | ~00:54 |
| 3 | 63 | ~1.6h | ~02:30 |
| 4 | 6 | ~0.2h | ~02:42 |
| 7 | 82 | ~2.1h | ~04:48 |

**Final completion**: ~04:48 AM (October 16, 2025)

---

## What You'll Get

Once complete, these files will be generated in `capitulo_01/outputs/`:

1. **`layout.json`** - Complete structure with bounding boxes
   ```json
   {
     "type": "title",
     "text": "Informe de Fallas...",
     "page": 1,
     "bbox": {"x0": 150.5, "y0": 50.2, "x1": 445.3, "y1": 80.5}
   }
   ```

2. **`document.md`** - Markdown export of content

3. **`document.html`** - HTML formatted version

4. **`annotated.pdf`** - PDF with colored bounding boxes drawn

5. **`stats.json`** - Statistics by element type and page

---

## 🔍 Monitoring Progress

### Option 1: Run the monitoring script
```bash
cd shared_platform/utils/outputs/docling_layout
./monitor_extraction.sh
```

### Option 2: Check the log file
```bash
tail -f shared_platform/utils/outputs/docling_layout/docling_sequential.log
```

### Option 3: Check GPU usage
```bash
nvidia-smi
# Currently using ~1.2 GB of 3.8 GB available (30%)
```

### Option 4: Check completed chapters
```bash
ls -lh shared_platform/utils/outputs/docling_layout/capitulo_*/outputs/layout_lightweight.json
```

---

## Element Types Detected

Docling will automatically detect:
- ✅ **title** - Main titles
- ✅ **section-header** - Section headings
- ✅ **text** - Paragraphs and text blocks
- ✅ **table** - Tables (97.9% accuracy)
- ✅ **picture** - Images and figures
- ✅ **formula** - Mathematical equations (96.4% accuracy)
- ✅ **list-item** - Bulleted/numbered lists
- ✅ **caption** - Figure/table captions
- ✅ **page-header** - Page headers
- ✅ **page-footer** - Page footers
- ✅ **footnote** - Footnotes

---

## Next Steps (After Completion)

1. **Review outputs**:
   ```bash
   cd shared_platform/utils/outputs/docling_layout/capitulo_01/outputs/
   ls -lah
   ```

2. **View JSON structure**:
   ```bash
   cat layout.json | jq '.elements[0:5]'  # First 5 elements
   ```

3. **Open annotated PDF**:
   ```bash
   xdg-open annotated.pdf  # Linux
   ```

4. **Compare with PyMuPDF**:
   ```bash
   cd ../scripts/
   python compare_pymupdf_vs_docling.py
   ```

5. **Process remaining chapters**:
   - Copy `capitulo_01/` structure to `capitulo_02/`
   - Update page ranges in script
   - Run extraction

---

## Comparison: Docling vs PyMuPDF

| Feature | PyMuPDF (current) | Docling (this) |
|---------|-------------------|----------------|
| **Speed** | 0.5-2s/page | 2.5s/page |
| **Table accuracy** | 85-90% | **97.9%** |
| **Equation detection** | Manual | **96.4%** |
| **Types detected** | 3 (manual) | **11 (automatic)** |
| **Bounding boxes** | Manual | **Automatic** |
| **Setup** | Already done | First-time loading |

---

## If Process Fails

Check the log for errors:
```bash
cat shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/extraction.log
```

Kill and restart:
```bash
pkill -f docling_layout_extractor
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/
source ../../../../../../venv/bin/activate
python docling_layout_extractor.py
```

---

**Note**: This is the first run, so model loading takes time. Subsequent runs will be much faster (~2.5s per page).

**Estimated completion**: ~12:35 PM (10-15 minutes from start)
