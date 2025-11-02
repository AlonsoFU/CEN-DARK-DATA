# Dark Data - Docling Extractors

**Focused repository for PDF extraction using IBM Docling Granite-258M**

This is a lightweight extraction repository containing only:
- **Docling extraction tools** (EAF monkey patch, universal scripts)
- **Domain processors** (operaciones, mercados, legal)
- **Minimal dependencies** for Claude Code efficiency

---

## 📁 Structure

```
dark-data-docling-extractors/
├── docling_layout/              # Docling extraction infrastructure
│   ├── eaf_patch/               # EAF monkey patch engine
│   │   ├── core/                # Patch engine, detectors, classifiers
│   │   └── scripts/             # Testing scripts
│   ├── METHODOLOGY/             # Complete methodology docs
│   ├── EXTRACT_ANY_CHAPTER.py   # ⭐ Universal extraction script
│   ├── capitulo_XX/             # Chapter outputs (gitignored)
│   └── README.md                # Docling documentation
│
├── domains/                     # Domain-specific processors
│   ├── operaciones/
│   │   ├── anexos_eaf/          # EAF annexes (ANEXO 1, 2, etc.)
│   │   ├── eaf/                 # Individual EAF reports
│   │   └── shared/              # Shared utilities
│   ├── mercados/                # Energy markets (planned)
│   └── legal/                   # Legal compliance (planned)
│
├── requirements.txt             # Python dependencies
├── .gitignore                   # Ignore PDFs, outputs, venv
└── README.md                    # This file
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone <repo-url> dark-data-docling-extractors
cd dark-data-docling-extractors

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Extract a Chapter (Universal Script)

```bash
cd docling_layout

# Extract any chapter (1-11)
python3 EXTRACT_ANY_CHAPTER.py 6   # Chapter 6
python3 EXTRACT_ANY_CHAPTER.py 7   # Chapter 7
python3 EXTRACT_ANY_CHAPTER.py 1   # Chapter 1

# Outputs generated:
# - capitulo_XX/outputs/layout_WITH_PATCH.json
# - capitulo_XX/outputs/chapterXX_WITH_PATCH_annotated.pdf
```

### 3. Batch Process All Chapters

```bash
# Process chapters 1-11
for i in {1..11}; do
  python3 EXTRACT_ANY_CHAPTER.py $i
done
```

---

## 📚 Documentation

### Complete Methodology

See **`docling_layout/METHODOLOGY/`** for full documentation:

- **RESUMEN_METODOLOGIA.md** - Quick summary (this is the starting point)
- **EAF_PATCH_ARCHITECTURE.md** - Monkey patch architecture
- **UNIVERSAL_DOCLING_METHODOLOGY.md** - Complete guide (400+ lines)
- **QUICK_START_GUIDE.md** - 1-page reference

### Key Concepts

1. **Docling Granite-258M**: AI layout analysis (97.9% table accuracy)
2. **EAF Monkey Patch**: Automatic detection of missing content
3. **Universal Script**: One script for all chapters (only change number)
4. **Post-Processors**: Document-level fixes after extraction

---

## 🔧 Configuration

### GPU Requirements

```python
# Lightweight mode (1.3 GB VRAM) - Fits 4GB GPU
pipeline_options.do_ocr = False
pipeline_options.table_structure_options.mode = TableFormerMode.FAST

# Standard mode (4.2 GB VRAM) - Requires 6GB+ GPU
pipeline_options.do_ocr = True
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
```

See `docling_layout/METHODOLOGY/COMPLETE_DOCLING_CONFIG_OPTIONS.md` for all options.

---

## 🎯 What This Repo Does

✅ **PDF Extraction** with Docling Granite-258M
✅ **Automatic Title Detection** (monkey patch)
✅ **Cross-Page List Detection**
✅ **Universal Schema** export to JSON
✅ **Annotated PDFs** with colored bounding boxes

---

## 🚫 What This Repo Does NOT Include

❌ MCP servers (see `dark-data-platform` repo)
❌ Database infrastructure
❌ Web dashboard
❌ AI platform tools

---

## 📊 Example Output

```json
{
  "elements": [
    {
      "type": "section_header",
      "text": "6. Normalización del servicio",
      "page": 1,
      "bbox": {
        "x0": 56.64,
        "y0": 60.07,
        "x1": 204.97,
        "y1": 70.98
      }
    }
  ]
}
```

---

## 🛠️ Dependencies

**Core:**
- `docling==2.17.0` - IBM Docling layout analysis
- `PyMuPDF==1.25.1` - PDF text extraction
- `torch==2.5.1` - AI model inference

**Optional:**
- `anthropic==0.40.0` - Claude API (for validation)
- `pandas==2.2.3` - Data processing

See `requirements.txt` for complete list.

---

## 📝 Common Tasks

### Extract Chapter with Custom Pages
```bash
python3 EXTRACT_ANY_CHAPTER.py 6 --pages 172-265
```

### Monitor GPU Usage
```bash
watch -n 1 nvidia-smi
```

### Verify Extraction
```bash
# Check JSON
jq '.elements | length' capitulo_06/outputs/layout_WITH_PATCH.json

# Check title detection
jq '.elements[0]' capitulo_06/outputs/layout_WITH_PATCH.json
```

---

## 🐛 Troubleshooting

### ModuleNotFoundError: docling
```bash
# Use virtualenv Python
/path/to/venv/bin/python3 script.py
```

### CUDA out of memory (4GB GPU)
```python
# Use lightweight mode in script
pipeline_options.do_ocr = False
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
```

### Title not detected
- Verify monkey patch is applied
- Check `eaf_patch/core/eaf_patch_engine.py` has latest code
- Re-extract with updated code

---

## 📄 License

Internal project - Chilean Electrical System Dark Data Platform

---

## 🔗 Related Repositories

- **dark-data-platform**: MCP servers, database, web UI
- **dark-data-docs**: Public documentation (optional)

---

**For questions or issues, see documentation in `docling_layout/METHODOLOGY/`**
