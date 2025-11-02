# EAF Patch - Directory Structure

**Last Updated**: 2025-10-20
**Purpose**: Documentation of all files, folders, and their organization

---

## 📂 Complete Directory Tree

```
shared_platform/utils/outputs/docling_layout/
│
├── eaf_patch/                    # ⭐ MAIN PATCH DIRECTORY
│   │
│   ├── scripts/                          # Executable Python scripts
│   │   ├── eaf_patch_engine.py  # ⭐ MAIN PATCH
│   │   ├── missing_title_detector.py               # Title detection
│   │   ├── power_line_classifier.py                # Power line detection
│   │   ├── page_number_detector.py                 # Page number detection (NEW)
│   │   ├── REPROCESS_chapter6_SPLIT_PDF.py         # Chapter 6 processor
│   │   └── (other processing scripts)
│   │
│   └── docs/                             # Documentation
│       ├── PATCH_IMPROVEMENTS_CATALOG.md           # ⭐ Complete improvements list
│       ├── INVESTIGATION_SUMMARY_2025-10-20.md     # Investigation process
│       ├── DOCLING_LIMITATION_CELLS_REQUIRED.md    # Technical analysis
│       ├── CRITICAL_PDF_PATHS.md                   # Split PDF documentation
│       ├── QUICK_REFERENCE.md                      # Quick usage guide
│       ├── POWER_LINE_PATCH_README.md              # Main README
│       └── DIRECTORY_STRUCTURE.md                  # ⭐ This file
│
├── capitulo_01/                          # Chapter 1 outputs
│   ├── outputs_lightweight/              # Lightweight mode results
│   │   ├── layout_lightweight.json
│   │   ├── document_lightweight.md
│   │   └── annotated_capitulo_01_only.pdf
│   └── scripts/
│       ├── lightweight_extract.py
│       └── visualize_cap1_only.py
│
├── capitulo_06/                          # Chapter 6 outputs
│   ├── outputs_WITH_UNIVERSAL_PATCH/     # ⭐ EAF Patch results
│   │   ├── layout_WITH_UNIVERSAL_PATCH.json        # Complete extraction
│   │   ├── chapter6_DUAL_VISUALIZATION.pdf         # ⭐ Dual-color PDF
│   │   ├── chapter6_WITH_UNIVERSAL_PATCH_ANNOTATED.pdf  # Standard annotated
│   │   ├── create_dual_visualization.py            # Visualization script
│   │   ├── REPROCESS_chapter6_SPLIT_PDF.py         # Reprocessing script
│   │   ├── PATCH_MODIFICATIONS_REPORT.md           # Statistics & analysis
│   │   └── README.md                               # Chapter 6 guide
│   │
│   └── outputs_baseline/                 # Baseline Docling (if exists)
│       └── (baseline comparison files)
│
├── capitulo_07/                          # Chapter 7 outputs (planned)
├── capitulo_08/                          # Chapter 8 outputs (planned)
│   ... (chapters 7-11)
│
└── README_DOCLING.md                     # ⭐ Master Docling guide

```

---

## 📋 File Registry

### Core Patch Files

| File | Location | Purpose | Status |
|------|----------|---------|--------|
| **eaf_patch_engine.py** | `eaf_patch/scripts/` | Main monkey patch | ✅ Active |
| **missing_title_detector.py** | `eaf_patch/scripts/` | Title pattern detection | ✅ Active |
| **power_line_classifier.py** | `eaf_patch/scripts/` | Power line classification | ✅ Active |
| **page_number_detector.py** | `eaf_patch/scripts/` | Page number detection | ✅ NEW |

### Documentation Files

| File | Location | Purpose | Status |
|------|----------|---------|--------|
| **PATCH_IMPROVEMENTS_CATALOG.md** | `eaf_patch/docs/` | Complete improvements list | ✅ NEW |
| **DIRECTORY_STRUCTURE.md** | `eaf_patch/docs/` | This file | ✅ NEW |
| **INVESTIGATION_SUMMARY_2025-10-20.md** | `eaf_patch/docs/` | Investigation process | ✅ Complete |
| **DOCLING_LIMITATION_CELLS_REQUIRED.md** | `eaf_patch/docs/` | Technical deep dive | ✅ Complete |
| **CRITICAL_PDF_PATHS.md** | `eaf_patch/docs/` | Split PDF guide | ✅ Complete |
| **QUICK_REFERENCE.md** | `eaf_patch/docs/` | Quick usage | ✅ Complete |
| **POWER_LINE_PATCH_README.md** | `eaf_patch/docs/` | Main README | ✅ Complete |

### Chapter-Specific Files

| File | Location | Purpose | Status |
|------|----------|---------|--------|
| **layout_WITH_UNIVERSAL_PATCH.json** | `capitulo_06/outputs_WITH_UNIVERSAL_PATCH/` | Extraction results | ✅ Complete |
| **chapter6_DUAL_VISUALIZATION.pdf** | `capitulo_06/outputs_WITH_UNIVERSAL_PATCH/` | Dual-color viz | ✅ Complete |
| **create_dual_visualization.py** | `capitulo_06/outputs_WITH_UNIVERSAL_PATCH/` | Viz generator | ✅ Reusable |
| **PATCH_MODIFICATIONS_REPORT.md** | `capitulo_06/outputs_WITH_UNIVERSAL_PATCH/` | Chapter 6 stats | ✅ Complete |
| **README.md** | `capitulo_06/outputs_WITH_UNIVERSAL_PATCH/` | Chapter 6 guide | ✅ Complete |

---

## 🗂️ Directory Purpose Guide

### `/eaf_patch/` - Main Patch Directory

**Purpose**: Central location for all patch-related code and documentation

**Why separate from chapters?**
- Patch is reusable across ALL chapters
- Single source of truth for patch logic
- Easy to version and maintain
- Documentation stays with code

**Subdirectories**:
- `scripts/` - Executable Python modules
- `docs/` - All documentation files

---

### `/eaf_patch/scripts/` - Executable Code

**Contents**:
1. **Core patch** - `eaf_patch_engine.py`
2. **Detectors** - Pattern matching classes
3. **Processors** - Chapter-specific scripts (optional)

**Naming conventions**:
- Detectors: `*_detector.py`
- Classifiers: `*_classifier.py`
- Processors: `REPROCESS_*.py` or `process_*.py`

**Import path**:
```python
from eaf_patch.scripts.eaf_patch_engine import apply_eaf_patch
```

---

### `/eaf_patch/docs/` - Documentation

**Contents**:
- Investigation reports
- Technical analyses
- Usage guides
- Structure documentation (this file)

**Documentation hierarchy**:
1. **Master catalog**: `PATCH_IMPROVEMENTS_CATALOG.md` ⭐
2. **Quick start**: `QUICK_REFERENCE.md`
3. **Deep dives**: Investigation & limitation docs
4. **Structure**: This file

**When to add new docs**:
- New feature → Update catalog
- New investigation → Create dated summary
- New limitation discovered → Technical doc
- Directory changes → Update this file

---

### `/capitulo_XX/outputs_WITH_UNIVERSAL_PATCH/` - Chapter Results

**Purpose**: Stores results for each chapter processed with the patch

**Standard files**:
1. **`layout_WITH_UNIVERSAL_PATCH.json`** - Extraction data
2. **`chapter{X}_DUAL_VISUALIZATION.pdf`** - Visual verification (recommended)
3. **`chapter{X}_WITH_UNIVERSAL_PATCH_ANNOTATED.pdf`** - Standard annotated
4. **`PATCH_MODIFICATIONS_REPORT.md`** - Statistics & analysis
5. **`README.md`** - Chapter-specific guide
6. **`create_dual_visualization.py`** - Visualization script (reusable)

**Optional files**:
- **`REPROCESS_chapter{X}_SPLIT_PDF.py`** - Reprocessing script
- **`*_FIXED_*.pdf`** - Historical/debug files

**Naming convention**:
- Chapter number in filename: `chapter6_*` or `capitulo_06_*`
- Patch indicator: `*_WITH_UNIVERSAL_PATCH*`
- Purpose suffix: `*_DUAL_VISUALIZATION.pdf`, `*_ANNOTATED.pdf`

---

## 📍 File Location Decision Tree

**Question**: Where should I put this file?

```
┌─────────────────────────────────────────────┐
│ Is it PATCH CODE (Python)?                  │
└─────────────────────────────────────────────┘
           │                    │
          YES                  NO
           │                    │
           ↓                    ↓
    ┌─────────────┐      ┌─────────────┐
    │ Reusable    │      │ Chapter     │
    │ across all  │      │ specific?   │
    │ chapters?   │      └─────────────┘
    └─────────────┘            │
           │                   │
          YES                 NO
           │                   │
           ↓                   ↓
    eaf_patch/   capitulo_XX/
       scripts/         outputs_WITH_UNIVERSAL_PATCH/


┌─────────────────────────────────────────────┐
│ Is it DOCUMENTATION?                         │
└─────────────────────────────────────────────┘
           │                    │
          YES                  NO
           │                    │
           ↓                    ↓
    ┌─────────────┐      ┌─────────────┐
    │ General     │      │ It's a      │
    │ patch docs? │      │ data file   │
    └─────────────┘      └─────────────┘
           │                   │
          YES                  ↓
           │              capitulo_XX/
           ↓              outputs_WITH_UNIVERSAL_PATCH/
    eaf_patch/
       docs/
```

---

## 🔄 File Lifecycle

### 1. Development Phase

**New detector class**:
```
1. Create in: eaf_patch/scripts/{detector_name}.py
2. Add tests in __main__ section
3. Import in eaf_patch_engine.py
4. Update PATCH_IMPROVEMENTS_CATALOG.md
```

**New chapter processing**:
```
1. Create output dir: capitulo_XX/outputs_WITH_UNIVERSAL_PATCH/
2. Copy create_dual_visualization.py template
3. Run processing
4. Generate PATCH_MODIFICATIONS_REPORT.md
5. Create chapter README.md
```

### 2. Testing Phase

**Test files go in**:
- `capitulo_XX/outputs_WITH_UNIVERSAL_PATCH/` (chapter-specific tests)
- `eaf_patch/scripts/test_*.py` (unit tests for detectors)

### 3. Production Phase

**Keep**:
- All Python scripts
- Final JSON outputs
- Dual visualization PDFs
- Documentation

**Archive/Delete**:
- `*_FIXED_*` files (historical debugging)
- Multiple versions of same file
- Intermediate test outputs

---

## 📊 Directory Size Guide

**Expected sizes** (per chapter):

| Directory | Typical Size | Main Contributors |
|-----------|--------------|-------------------|
| `eaf_patch/scripts/` | ~500 KB | Python code |
| `eaf_patch/docs/` | ~200 KB | Markdown files |
| `capitulo_XX/outputs_*/` | 1-5 MB | PDFs (1-2 MB each) |
| JSON files | 50-500 KB | Extraction data |

**Total for 11 chapters**: ~15-30 MB (without baseline comparisons)

---

## 🚀 Quick Navigation

### "I want to..."

**...understand how the patch works**
→ `eaf_patch/docs/PATCH_IMPROVEMENTS_CATALOG.md`

**...use the patch on a new chapter**
→ `eaf_patch/docs/QUICK_REFERENCE.md`

**...see Chapter 6 results**
→ `capitulo_06/outputs_WITH_UNIVERSAL_PATCH/README.md`

**...modify the patch code**
→ `eaf_patch/scripts/eaf_patch_engine.py`

**...add a new detector**
→ Create in `eaf_patch/scripts/`, import in main patch

**...understand why "6." was missing**
→ `eaf_patch/docs/INVESTIGATION_SUMMARY_2025-10-20.md`

**...see what Docling can't do**
→ `eaf_patch/docs/DOCLING_LIMITATION_CELLS_REQUIRED.md`

**...understand split PDF performance**
→ `eaf_patch/docs/CRITICAL_PDF_PATHS.md`

**...understand the directory structure**
→ You're reading it! 😊

---

## 🔧 Maintenance Guidelines

### Adding New Files

**Checklist**:
- [ ] Choose correct directory (use decision tree above)
- [ ] Follow naming conventions
- [ ] Add entry to this file (File Registry section)
- [ ] Update relevant documentation

### Renaming/Moving Files

**Process**:
1. Update this file first (document the change)
2. Update import statements
3. Update documentation references
4. Test all affected scripts
5. Commit with clear message

### Deleting Files

**Before deleting**:
- [ ] Confirm not referenced in documentation
- [ ] Confirm not imported by other scripts
- [ ] Archive if historical value (don't delete)
- [ ] Update this file (mark as archived)

---

## 📝 Naming Conventions

### Files

| Type | Convention | Example |
|------|------------|---------|
| Detector classes | `*_detector.py` | `missing_title_detector.py` |
| Classifier classes | `*_classifier.py` | `power_line_classifier.py` |
| Processing scripts | `REPROCESS_*.py` or `process_*.py` | `REPROCESS_chapter6_SPLIT_PDF.py` |
| Visualization | `create_*.py` or `visualize_*.py` | `create_dual_visualization.py` |
| Documentation | `UPPERCASE_*.md` | `PATCH_IMPROVEMENTS_CATALOG.md` |
| Chapter guides | `README.md` | (in chapter output dir) |

### Directories

| Type | Convention | Example |
|------|------------|---------|
| Chapter outputs | `capitulo_{XX}/outputs_*` | `capitulo_06/outputs_WITH_UNIVERSAL_PATCH/` |
| Patch components | lowercase | `scripts/`, `docs/` |
| Method suffix | `outputs_{METHOD}` | `outputs_WITH_UNIVERSAL_PATCH/` |

---

## 🎯 Future Structure Plans

### Planned Additions

1. **`/tests/`** directory
   - Unit tests for all detectors
   - Integration tests for patch
   - Regression tests vs baseline

2. **`/benchmarks/`** directory
   - Performance metrics
   - Accuracy comparisons
   - Chapter-by-chapter stats

3. **`/templates/`** directory
   - Chapter processing template
   - Visualization template
   - Documentation template

4. **Version control**
   - `patch_v1.0/`, `patch_v2.0/`
   - Keep backward compatibility
   - Migration guides

---

## ✅ Structure Validation

**Run this check** to verify structure:

```bash
# Check all required directories exist
cd shared_platform/utils/outputs/docling_layout

# Core directories
[ -d "eaf_patch/scripts" ] && echo "✅ scripts/" || echo "❌ scripts/ missing"
[ -d "eaf_patch/docs" ] && echo "✅ docs/" || echo "❌ docs/ missing"

# Core files
[ -f "eaf_patch/scripts/eaf_patch_engine.py" ] && echo "✅ Main patch" || echo "❌ Main patch missing"
[ -f "eaf_patch/docs/PATCH_IMPROVEMENTS_CATALOG.md" ] && echo "✅ Catalog" || echo "❌ Catalog missing"
[ -f "eaf_patch/docs/DIRECTORY_STRUCTURE.md" ] && echo "✅ This file" || echo "❌ This file missing"
```

---

**Last Updated**: 2025-10-20
**Maintained By**: Claude Code
**Version**: 1.0
