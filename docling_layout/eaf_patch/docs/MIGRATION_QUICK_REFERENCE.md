# EAF Patch Migration - Quick Reference

**⏱️ Time**: 30-45 minutes | **🎯 Goal**: Rename to `eaf_patch` | **📅 Execute**: When ready

---

## 🚀 One-Command Migration

```bash
cd shared_platform/utils/outputs/docling_layout

# Execute automated migration script
bash eaf_patch/docs/migration_script.sh
```

---

## 📋 Manual Migration (Step-by-Step)

### 1. Backup (1 min)
```bash
cp -r eaf_patch eaf_patch.backup
git add . && git commit -m "Pre-migration: before eaf_patch rename"
```

### 2. Rename Directory (1 min)
```bash
mv eaf_patch eaf_patch
```

### 3. Create Structure (1 min)
```bash
cd eaf_patch
mkdir -p core domain examples
```

### 4. Move Files (5 min)
```bash
# Core files
mv scripts/eaf_patch_engine.py core/eaf_patch_engine.py
mv scripts/missing_title_detector.py core/eaf_title_detector.py
mv scripts/page_number_detector.py core/eaf_page_detector.py

# Domain files
mv scripts/power_line_classifier.py domain/

# Docs
cd docs
mv PATCH_IMPROVEMENTS_CATALOG.md EAF_PATCH_CATALOG.md
mv POWER_LINE_PATCH_README.md EAF_PATCH_README.md
```

### 5. Update Imports (10 min)

**In `core/eaf_patch_engine.py`**:
```python
# OLD
from missing_title_detector import EAFTitleDetector

# NEW
from eaf_patch.core.eaf_title_detector import EAFTitleDetector
```

**In processing scripts**:
```python
# OLD
from eaf_patch.scripts.eaf_patch_engine import apply_eaf_patch

# NEW
from eaf_patch.core.eaf_patch_engine import apply_eaf_patch
```

### 6. Update Class Names (5 min)
```python
# In eaf_title_detector.py
class EAFTitleDetector:  → class EAFTitleDetector:

# In eaf_page_detector.py
class EAFPageDetector:    → class EAFPageDetector:
```

### 7. Update Documentation (10 min)
- Search/replace in all .md files: `eaf_patch` → `eaf_patch`
- Update file path references
- Update import examples

### 8. Rename Chapter Outputs (2 min)
```bash
mv capitulo_06/outputs_WITH_UNIVERSAL_PATCH capitulo_06/outputs_with_eaf_patch
```

### 9. Test (5 min)
```bash
python eaf_patch/core/eaf_title_detector.py  # Run tests
python eaf_patch/core/eaf_page_detector.py   # Run tests
```

---

## 🔍 Search & Replace List

| Find | Replace |
|------|---------|
| `eaf_patch` | `eaf_patch` |
| `eaf_patch_engine` | `eaf_patch_engine` |
| `apply_eaf_patch` | `apply_eaf_patch` |
| `EAFTitleDetector` | `EAFTitleDetector` |
| `EAFPageDetector` | `EAFPageDetector` |
| `outputs_WITH_UNIVERSAL_PATCH` | `outputs_with_eaf_patch` |

---

## ✅ Validation Checklist

- [ ] `eaf_patch/` directory exists
- [ ] `core/`, `domain/`, `docs/` subdirectories exist
- [ ] All files moved correctly
- [ ] All imports updated
- [ ] All class names updated
- [ ] Documentation updated
- [ ] Test scripts run successfully
- [ ] Chapter outputs renamed
- [ ] Old `eaf_patch/` deleted

---

## 📁 Before → After

### Directory Structure
```
BEFORE:                          AFTER:
eaf_patch/                eaf_patch/
├── scripts/                     ├── core/
│   ├── universal_patch...       │   ├── eaf_patch_engine.py
│   ├── missing_title...         │   ├── eaf_title_detector.py
│   └── page_number...           │   └── eaf_page_detector.py
└── docs/                        ├── domain/
                                 │   └── power_line_classifier.py
                                 ├── docs/
                                 └── examples/
```

### Import Paths
```
BEFORE:                          AFTER:
from eaf_patch.scripts    from eaf_patch.core
  .universal_patch...              .eaf_patch_engine

from missing_title_detector      from eaf_patch.core
                                   .eaf_title_detector
```

---

## 🔄 Rollback

If issues occur:
```bash
rm -rf eaf_patch
mv eaf_patch.backup eaf_patch
# Or: git checkout eaf_patch/
```

---

## 📞 Help

**Full guide**: `MIGRATION_TO_EAF_PATCH.md`

**Questions?** Check:
1. Full migration plan (detailed steps)
2. DIRECTORY_STRUCTURE.md (new structure)
3. Git history (if issues)

---

**Status**: ⏳ Ready to execute when needed
