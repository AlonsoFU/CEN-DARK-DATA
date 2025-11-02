# How to Restore GPU for Docling

Your GPU crashed and needs to be reset. Here are the steps:

---

## 🚨 Current Issue

**Error**: `CUDA unknown error - incorrectly set up environment`
**Cause**: Multiple Docling processes exhausted GPU memory
**Solution**: Reset NVIDIA driver or reboot

---

## 🔧 Solution Options

### Option 1: Reboot (Easiest, Most Reliable) ⭐

This is the **cleanest** way to restore GPU:

```bash
# Save any work first!
sudo reboot
```

**After reboot:**
```bash
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts
source ../../../../../../venv/bin/activate
python lightweight_extract.py
```

**Time**: Reboot ~2 min + Extraction ~20 min = **22 minutes total**

---

### Option 2: Restart Display Manager (Faster, Might Work)

This restarts the graphics system without full reboot:

```bash
# This will close all GUI applications!
sudo systemctl restart display-manager
```

**Warning**: This will:
- Log you out
- Close all windows
- Restart GUI session

**After restart:**
- Log back in
- Open terminal
- Run the extraction command

---

### Option 3: Reload NVIDIA Modules (Advanced, Risky)

This tries to reload just the NVIDIA drivers:

```bash
# Stop all GPU processes first
sudo fuser -k /dev/nvidia*

# Unload NVIDIA modules
sudo rmmod nvidia_uvm
sudo rmmod nvidia_drm
sudo rmmod nvidia_modeset
sudo rmmod nvidia

# Reload modules
sudo modprobe nvidia
sudo modprobe nvidia_modeset
sudo modprobe nvidia_drm
sudo modprobe nvidia_uvm

# Test if it worked
nvidia-smi
```

**If you see GPU info**: Success! Run extraction.
**If you see errors**: Reboot is needed.

---

## ✅ After GPU Restore - Run This

```bash
# Navigate to scripts directory
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts

# Activate virtual environment
source ../../../../../../venv/bin/activate

# Verify GPU is available
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Should print: CUDA available: True

# Run lightweight extraction (will use GPU now!)
python lightweight_extract.py
```

**Expected output:**
```
🪶 LIGHTWEIGHT DOCLING EXTRACTION - Optimized for 4GB GPU
════════════════════════════════════════════════════════
📄 PDF: EAF-089-2025.pdf
📑 Pages: 1-11

💾 Memory Optimizations:
   ✓ OCR disabled (saves ~1.5 GB)
   ✓ Table mode: FAST (saves ~400 MB)
   ...
   📊 Expected usage: ~1.3 GB (fits on 4GB GPU!)

🔧 Initializing lightweight converter...
2025-XX-XX XX:XX:XX,XXX - INFO - Accelerator device: 'cuda:0'  ← GPU working!
✅ Converter ready

🔍 Converting document (this will take ~15-18 minutes)...
```

---

## 🎯 Recommended Steps (Right Now)

### Step 1: Clean up background processes

Open a terminal and run:
```bash
# List all Docling processes
ps aux | grep -E "(docling|lightweight_extract|quick_extract|test_docling)" | grep -v grep

# Kill them (they're stuck anyway)
pkill -f "docling_layout_extractor"
pkill -f "quick_extract"
pkill -f "test_docling_api"
pkill -f "lightweight_extract"
```

### Step 2: Reboot

```bash
sudo reboot
```

### Step 3: After reboot, verify GPU

```bash
nvidia-smi

# Should show your GTX 1650 with 4GB
# Memory usage should be near 0
```

### Step 4: Run extraction

```bash
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout/capitulo_01/scripts
source ../../../../../../venv/bin/activate
python lightweight_extract.py
```

### Step 5: Monitor

In another terminal:
```bash
# Watch GPU usage
watch -n 1 nvidia-smi

# Or tail the log
tail -f /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/lightweight_extract.log
```

---

## ⏱️ Timeline with GPU

Once GPU is restored:
- **Model loading**: 30-60 seconds
- **Processing 399 pages**: ~15-18 minutes
- **Extracting Chapter 1**: Instant (filtered from full doc)
- **Saving outputs**: 10-20 seconds
- **Total**: ~18-20 minutes

---

## 🔍 How to Know GPU is Working

### Before running extraction:
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

**Good**: `CUDA: True`
**Bad**: `CUDA: False` → Reboot needed

### During extraction:
```bash
nvidia-smi
```

**Good**: Shows ~1200-1500 MB used on GPU
**Bad**: Shows 0 MB → Using CPU instead

---

## 💡 Why This Happened

Running 3+ Docling instances simultaneously:
1. First process loads ~4 GB
2. Second process tries to load another 4 GB
3. **Total**: 8+ GB on a 4GB GPU
4. **Result**: GPU driver crashes
5. **Recovery**: Only reboot clears it

**Prevention for future**:
- ✅ Run ONE Docling instance at a time
- ✅ Kill previous processes before starting new ones
- ✅ Use lightweight config on 4GB GPU
- ❌ Never run multiple Docling instances simultaneously

---

## 📋 Quick Commands Reference

```bash
# Check GPU status
nvidia-smi

# Check CUDA availability in Python
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Kill Docling processes
pkill -f docling

# Reboot
sudo reboot

# After reboot - run extraction
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout/capitulo_01/scripts
source ../../../../../../venv/bin/activate
python lightweight_extract.py

# Monitor progress
tail -f lightweight_extract.log

# Or watch GPU
watch -n 1 nvidia-smi
```

---

## ✅ Summary

**To use GPU, you need to:**
1. **Reboot** your machine (easiest solution)
2. **Verify** GPU is available with `nvidia-smi`
3. **Run** `lightweight_extract.py`
4. **Wait** ~20 minutes for completion

**Current status**: GPU is crashed, CPU extraction running (2-4 hours)

**Your choice**:
- Reboot now → Results in 20 minutes
- Wait → Results in 2-4 hours (CPU)

---

**Ready to reboot?** Let me know when you're back and I'll help you run the extraction! 🚀
