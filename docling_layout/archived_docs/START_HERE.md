# ⚡ START HERE - Quick Commands for Next Session

**Last updated**: October 13, 2025

---

## 🚀 Copy-Paste This After Reboot

```bash
# Step 1: Verify GPU is back online
nvidia-smi

# Step 2: Navigate to project
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN

# Step 3: Go to scripts directory
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts

# Step 4: Activate virtual environment
source ../../../../../../venv/bin/activate

# Step 5: Verify CUDA works
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
# Should print: CUDA available: True

# Step 6: Run extraction
python lightweight_extract.py

# ⏱️ Wait ~20 minutes
# 📁 Check outputs in: ../outputs/
```

---

## ✅ Expected Results

After ~20 minutes, you'll have in `../outputs/`:
- `layout_lightweight.json` - All elements with bounding boxes
- `document_lightweight.md` - Markdown export
- `document_lightweight.html` - HTML export
- `stats_lightweight.json` - Statistics

---

## 🔍 Monitor Progress (Optional)

Open a second terminal:
```bash
# Option 1: Watch GPU usage
watch -n 1 nvidia-smi

# Option 2: Watch log file
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts
tail -f lightweight_extract.log
```

---

## ⚠️ Important Reminders

1. **Only run ONE Docling instance at a time** (or GPU will crash)
2. **Memory usage**: ~1.3 GB (safe for your 4GB GPU)
3. **Don't interrupt**: Let it complete fully (~20 min)
4. **If it crashes again**: Reboot and retry

---

## 📖 Need Help?

- **Full guide**: `README_DOCLING.md`
- **Quick start**: `QUICK_START.md`
- **Options reference**: `DOCLING_OPTIONS_CHEATSHEET.md`
- **Why reboot?**: `WHY_REBOOT_NEEDED.md`

---

## 🎯 What This Does

Extracts Chapter 1 (pages 1-11) from EAF-089-2025.pdf with:
- ✅ Layout detection (titles, paragraphs, tables, lists, figures)
- ✅ Bounding boxes for all elements
- ✅ Table structure (FAST mode, 95% accuracy)
- ❌ OCR disabled (not needed, saves memory)

---

**That's it! Just reboot and run these commands.** 🚀
