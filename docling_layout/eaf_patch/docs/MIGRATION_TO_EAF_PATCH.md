# Migration Plan: eaf_patch → eaf_patch

**Created**: 2025-10-20
**Status**: ⏳ Ready to Execute
**Estimated Time**: 30-45 minutes
**Risk Level**: Low (all changes are renames/moves)

---

## 🎯 Objectives

**Why rename?**
- Current name "eaf_patch" is misleading
- Patch is EAF-document specific (Chilean electrical failure reports)
- Power line detection is just ONE feature, not the main purpose
- New name should reflect document type (EAF)

**What changes?**
- Directory name: `eaf_patch/` → `eaf_patch/`
- File names: Add "eaf_" prefix to make domain clear
- Documentation: Update all references
- Import paths: Update all Python imports

---

## 📋 Complete Renaming Checklist

### Phase 1: Directory Structure (5 min)

**Current**:
```
docling_layout/
└── eaf_patch/
    ├── scripts/
    └── docs/
```

**New**:
```
docling_layout/
└── eaf_patch/
    ├── core/              # ⭐ NEW - organize by purpose
    ├── domain/            # ⭐ NEW - Chilean grid specific
    ├── docs/
    └── examples/          # ⭐ NEW - usage templates
```

**Commands**:
```bash
cd shared_platform/utils/outputs/docling_layout

# Rename main directory
mv eaf_patch eaf_patch

# Create new subdirectories
mkdir -p eaf_patch/core
mkdir -p eaf_patch/domain
mkdir -p eaf_patch/examples
```

---

### Phase 2: File Renames (10 min)

#### Core Files (Generic Detection Logic)

| Current Location | New Location | Reason |
|------------------|--------------|--------|
| `scripts/eaf_patch_engine.py` | `core/eaf_patch_engine.py` | Main patch - EAF specific |
| `scripts/missing_title_detector.py` | `core/eaf_title_detector.py` | EAF title patterns |
| `scripts/page_number_detector.py` | `core/eaf_page_detector.py` | Spanish page numbers |

**Commands**:
```bash
cd eaf_patch

# Move and rename core files
mv scripts/eaf_patch_engine.py core/eaf_patch_engine.py
mv scripts/missing_title_detector.py core/eaf_title_detector.py
mv scripts/page_number_detector.py core/eaf_page_detector.py
```

#### Domain-Specific Files (Chilean Grid)

| Current Location | New Location | Reason |
|------------------|--------------|--------|
| `scripts/power_line_classifier.py` | `domain/power_line_classifier.py` | Chilean grid terms only |

**Commands**:
```bash
# Move domain-specific files
mv scripts/power_line_classifier.py domain/
```

#### Documentation Files

| Current Filename | New Filename | Reason |
|------------------|--------------|--------|
| `PATCH_IMPROVEMENTS_CATALOG.md` | `EAF_PATCH_CATALOG.md` | EAF-specific improvements |
| `POWER_LINE_PATCH_README.md` | `EAF_PATCH_README.md` | Main README |

**Commands**:
```bash
cd docs

# Rename documentation
mv PATCH_IMPROVEMENTS_CATALOG.md EAF_PATCH_CATALOG.md
mv POWER_LINE_PATCH_README.md EAF_PATCH_README.md

# Update DIRECTORY_STRUCTURE.md (manual edit needed)
```

---

### Phase 3: Update Import Statements (10 min)

#### Files That Import the Patch

**File**: `eaf_patch/core/eaf_patch_engine.py`

**Current imports**:
```python
from missing_title_detector import EAFTitleDetector
from power_line_classifier import PowerLineClassifier
from page_number_detector import EAFPageDetector
```

**New imports**:
```python
from eaf_patch.core.eaf_title_detector import EAFTitleDetector
from eaf_patch.domain.power_line_classifier import PowerLineClassifier
from eaf_patch.core.eaf_page_detector import EAFPageDetector
```

**File**: `capitulo_06/outputs_with_eaf_patch/REPROCESS_chapter6_SPLIT_PDF.py`

**Current import**:
```python
from eaf_patch.scripts.eaf_patch_engine import apply_eaf_patch
```

**New import**:
```python
from eaf_patch.core.eaf_patch_engine import apply_eaf_patch
```

#### Function Renames

**Current**:
```python
def apply_eaf_patch(pdf_path):
    ...
```

**New**:
```python
def apply_eaf_patch(pdf_path):
    """
    Apply EAF-specific patch for Chilean electrical system documents

    Args:
        pdf_path: Path to EAF document PDF
    """
    ...
```

---

### Phase 4: Update Class Names (5 min)

| Current Class | New Class | File |
|---------------|-----------|------|
| `EAFTitleDetector` | `EAFTitleDetector` | `eaf_title_detector.py` |
| `EAFPageDetector` | `EAFPageDetector` | `eaf_page_detector.py` |
| `PowerLineClassifier` | `PowerLineClassifier` | ✅ Keep same (clear purpose) |

**Example**:
```python
# OLD: eaf_patch/core/eaf_title_detector.py
class EAFTitleDetector:
    """Detects chapter/section titles..."""

# NEW: eaf_patch/core/eaf_title_detector.py
class EAFTitleDetector:
    """
    Detects chapter/section titles in EAF documents

    EAF documents use specific hierarchy:
    - Level 1: "6.", "7." (chapter numbers)
    - Level 2: "a.", "b." (section letters)
    - Level 3: "6.1", "6.2.1" (subsections)
    """
```

---

### Phase 5: Update Documentation (10 min)

#### Files to Update

1. **`EAF_PATCH_CATALOG.md`** (renamed from PATCH_IMPROVEMENTS_CATALOG.md)
   - Add header: "EAF Document Patch - Improvement Catalog"
   - Add note: "Specifically designed for Chilean electrical system failure reports (EAF)"
   - Update all function/class references

2. **`EAF_PATCH_README.md`** (renamed from POWER_LINE_PATCH_README.md)
   - Update title
   - Clarify EAF document focus
   - Update import examples

3. **`DIRECTORY_STRUCTURE.md`**
   - Update entire tree structure
   - Update all file paths
   - Update naming conventions

4. **`QUICK_REFERENCE.md`**
   - Update import statements
   - Update function calls
   - Update file paths

5. **`INVESTIGATION_SUMMARY_2025-10-20.md`**
   - Update references to eaf_patch → eaf_patch
   - Update file paths

6. **Chapter-specific files**:
   - `capitulo_06/outputs_with_eaf_patch/README.md`
   - `capitulo_06/outputs_with_eaf_patch/PATCH_MODIFICATIONS_REPORT.md`

---

### Phase 6: Update Chapter Output Directories (5 min)

**Current**:
```
capitulo_06/
└── outputs_WITH_UNIVERSAL_PATCH/
```

**New**:
```
capitulo_06/
└── outputs_with_eaf_patch/
```

**Commands**:
```bash
cd shared_platform/utils/outputs/docling_layout

# Rename chapter output directories
mv capitulo_06/outputs_WITH_UNIVERSAL_PATCH capitulo_06/outputs_with_eaf_patch
```

**Update files inside**:
- JSON references
- PDF filenames (optional - can keep existing)
- Documentation

---

## 🔍 Search & Replace Guide

### Global Text Replacements

**Search for** → **Replace with**:

1. `eaf_patch` → `eaf_patch`
2. `eaf_patch_engine` → `eaf_patch_engine`
3. `apply_eaf_patch` → `apply_eaf_patch`
4. `EAFTitleDetector` → `EAFTitleDetector`
5. `EAFPageDetector` → `EAFPageDetector`
6. `EAF Patch` → `EAF Patch`
7. `EAF patch` → `EAF patch`
8. `outputs_WITH_UNIVERSAL_PATCH` → `outputs_with_eaf_patch`

**Files to update** (grep for references):
```bash
cd shared_platform/utils/outputs/docling_layout

# Find all files mentioning "eaf_patch"
grep -r "eaf_patch" . --include="*.py" --include="*.md"

# Find all files mentioning "universal_patch"
grep -r "universal_patch" . --include="*.py" --include="*.md"

# Find all files mentioning "EAFTitleDetector"
grep -r "EAFTitleDetector" . --include="*.py"
```

---

## ✅ Validation Checklist

After migration, verify:

### Code Functionality
- [ ] All Python files import correctly
- [ ] All detector classes work
- [ ] Patch engine runs without errors
- [ ] Chapter processing scripts work

### Documentation
- [ ] No broken links in markdown files
- [ ] All file paths are correct
- [ ] All class/function names updated
- [ ] Examples use correct imports

### File Organization
- [ ] `eaf_patch/core/` contains generic detection
- [ ] `eaf_patch/domain/` contains Chilean grid specific
- [ ] `eaf_patch/docs/` has all documentation
- [ ] Old `eaf_patch/` directory deleted
- [ ] Old `scripts/` directory deleted

### Testing
- [ ] Run: `python eaf_patch/core/eaf_title_detector.py` (test examples)
- [ ] Run: `python eaf_patch/core/eaf_page_detector.py` (test examples)
- [ ] Process a sample chapter to verify full pipeline

---

## 🔧 Rollback Plan

If issues occur, revert with:

```bash
cd shared_platform/utils/outputs/docling_layout

# Restore from git (if committed)
git checkout eaf_patch/

# Or manual restore
mv eaf_patch eaf_patch
# Undo all renames manually
```

**Recommendation**: Commit current state BEFORE migration:
```bash
git add .
git commit -m "Pre-migration checkpoint: before renaming to eaf_patch"
```

---

## 📊 Impact Assessment

### Files Affected

| Category | Count | Risk |
|----------|-------|------|
| Python files to rename | 4 | Low |
| Python files to update imports | 5-10 | Low |
| Documentation to update | 8 | Low |
| Directory renames | 2 | Low |
| Total changes | ~20 files | Low |

### Testing Required

- Unit tests: All detector classes
- Integration: Full chapter processing
- Documentation: All links work

### Estimated Effort

- Automated (commands): 15 min
- Manual updates: 20 min
- Testing: 10 min
- **Total: 45 min**

---

## 🚀 Quick Start - Execute Migration

**Run these commands in order**:

```bash
#!/bin/bash
# EAF Patch Migration Script
# Run from: shared_platform/utils/outputs/docling_layout

set -e  # Exit on error

echo "🚀 Starting EAF Patch Migration..."

# 1. Create backup
echo "📦 Creating backup..."
cp -r eaf_patch eaf_patch.backup

# 2. Rename main directory
echo "📁 Renaming main directory..."
mv eaf_patch eaf_patch

# 3. Create new structure
echo "🏗️  Creating new directories..."
cd eaf_patch
mkdir -p core domain examples

# 4. Move files
echo "📝 Moving files..."
mv scripts/eaf_patch_engine.py core/eaf_patch_engine.py
mv scripts/missing_title_detector.py core/eaf_title_detector.py
mv scripts/page_number_detector.py core/eaf_page_detector.py
mv scripts/power_line_classifier.py domain/

# 5. Rename documentation
echo "📚 Renaming documentation..."
cd docs
mv PATCH_IMPROVEMENTS_CATALOG.md EAF_PATCH_CATALOG.md
mv POWER_LINE_PATCH_README.md EAF_PATCH_README.md 2>/dev/null || true

# 6. Clean up
echo "🧹 Cleaning up..."
cd ..
rmdir scripts 2>/dev/null || echo "Note: scripts/ not empty, keeping for now"

echo "✅ Migration complete!"
echo "⚠️  Next steps:"
echo "   1. Update import statements in Python files"
echo "   2. Update documentation references"
echo "   3. Test with: python core/eaf_title_detector.py"
echo "   4. Delete backup: rm -rf ../eaf_patch.backup"
```

---

## 📚 Reference: New Structure Summary

**After migration**:

```
eaf_patch/
├── core/                              # Generic detection (EAF patterns)
│   ├── eaf_patch_engine.py            # Main patch
│   ├── eaf_title_detector.py          # EAF title patterns
│   └── eaf_page_detector.py           # Spanish page numbers
│
├── domain/                            # Chilean grid specific
│   └── power_line_classifier.py       # Power infrastructure
│
├── docs/                              # Documentation
│   ├── EAF_PATCH_CATALOG.md           # Improvements list
│   ├── EAF_PATCH_README.md            # Main guide
│   ├── DIRECTORY_STRUCTURE.md         # Updated structure
│   ├── INVESTIGATION_SUMMARY_2025-10-20.md
│   ├── DOCLING_LIMITATION_CELLS_REQUIRED.md
│   └── MIGRATION_TO_EAF_PATCH.md      # This file
│
└── examples/                          # Usage examples
    └── process_eaf_chapter_template.py
```

**Usage after migration**:
```python
from eaf_patch.core.eaf_patch_engine import apply_eaf_patch

# Apply EAF patch
apply_eaf_patch("EAF-089-2025_capitulo_06.pdf")
```

---

**Last Updated**: 2025-10-20
**Ready to Execute**: ✅ Yes
**Next Steps**: Run migration script when ready
