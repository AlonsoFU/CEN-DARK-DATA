# EAF Patch Core Architecture

**Last Updated**: 2025-10-30
**Version**: 3.1 (Reorganized Structure)

---

## 📁 Directory Structure

```
eaf_patch/core/
├── monkey_patch/              # ⚙️ Monkey Patch Logic (runs DURING Docling)
│   └── (future: split eaf_patch_engine.py here)
│
├── post_processors/           # 🔧 Post-Processors (run AFTER Docling)
│   ├── __init__.py
│   ├── zona_fix.py           # Zona classification fix
│   └── isolated_list_fix.py  # Isolated list-item fix
│
├── eaf_patch_engine.py        # 🐵 Main Monkey Patch Engine
└── README_ARCHITECTURE.md     # 📖 This file
```

---

## 🔄 Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. SETUP: apply_universal_patch_with_pdf(pdf_path)         │
│     - Installs monkey patch into Docling                    │
│     - Sets global PDF path                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. EXTRACTION: converter.convert(pdf_path)                 │
│     ⚙️  MONKEY PATCH RUNS (page-by-page):                   │
│     - Extract PDF text with PyMuPDF                         │
│     - Detect missing titles                                 │
│     - Detect missing company names                          │
│     - Detect power line references                          │
│     - Create synthetic clusters                             │
│     - Add to Docling's output (post-pipeline injection)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. POST-PROCESSING: Fix document-level issues              │
│     🔧 POST-PROCESSORS RUN (document-level):                │
│     a) apply_zona_fix_to_document(doc)                      │
│        - Fixes Zona ... - Área ... classification           │
│     b) apply_isolated_list_fix_to_document(doc)             │
│        - Reclassifies isolated list-items                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. EXPORT: JSON, Markdown, etc.                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐵 Monkey Patch (Page-Level)

**File**: `eaf_patch_engine.py`

**What it does**: Intercepts Docling's internal processing pipeline and adds missing content that the AI didn't detect.

**When it runs**: DURING Docling extraction (page-by-page)

**How it works**:
1. Patches `TableFormer._process_regular_clusters()` method
2. For each page:
   - Extracts all text with PyMuPDF
   - Compares against Docling's detected boxes
   - Finds missing content (titles, company names, power lines)
   - Creates synthetic clusters with proper bounding boxes
   - Injects clusters AFTER Docling's filtering

**Key Functions**:
- `apply_universal_patch_with_pdf(pdf_path)` - Activates the patch
- `_patched_process_regular_clusters(self)` - The monkey-patched method
- `_create_bounding_rectangle(bbox_dict)` - Helper for bbox creation
- `_is_valid_bbox(bbox_dict)` - Bbox validation

**Limitations**:
- ❌ Can only see ONE page at a time
- ❌ Cannot compare items across pages
- ❌ Cannot fix sequential/isolated detection (needs document-level view)

---

## 🔧 Post-Processors (Document-Level)

**Location**: `post_processors/` module

**What they do**: Fix classification issues that require seeing the ENTIRE document.

**When they run**: AFTER Docling completes extraction (document-level)

**How to use**:
```python
from core.post_processors import (
    apply_zona_fix_to_document,
    apply_isolated_list_fix_to_document
)

# After extraction
result = converter.convert("document.pdf")
doc = result.document

# Apply post-processors
apply_zona_fix_to_document(doc)
apply_isolated_list_fix_to_document(doc)
```

### Available Post-Processors

#### 1. `zona_fix.py` - Zona Classification Fix

**Problem**: "Zona ... - Área ..." items can be isolated headers OR sequential list items, but you need to see multiple pages to know.

**Solution**:
- Collects ALL Zona items from entire document
- Detects if each is isolated or part of a sequence (within 3 positions)
- Isolated → SECTION_HEADER
- Sequential → LIST_ITEM (with bullet added)

**Example**:
```
Page 5:  "Zona Norte Grande - Área Arica"
Page 5:  "Zona Norte Grande - Área Iquique"
Page 5:  "Zona Norte Grande - Área Tarapacá"
→ All sequential, keep as list-items

Page 12: "Zona Centro - Área Itahue"
→ Isolated, change to section-header
```

#### 2. `isolated_list_fix.py` - Isolated List-Item Fix

**Problem**: Docling classifies standalone title-like content as `list_item` when it should be `section_header`.

**Solution** (GENERAL algorithm, not pattern-specific):
- Collects ALL list-items from entire document
- Detects if each is isolated or sequential (within 3 positions)
- Isolated → SECTION_HEADER
- Sequential → Keep as LIST_ITEM

**Example**:
```
Page 40: "Línea 220 kV Calama Nueva - Lasana"
→ No other list-items nearby, change to section-header

Page 4:  "'Bad_quality_Ln1_87L_I_DIFF_I_diff._phs_A_77'"
Page 4:  "'Bad_quality_Ln1_87L_I_DIFF_I_diff._phs_B_78'"
Page 4:  "'Bad_quality_Ln1_87L_I_DIFF_I_diff._phs_C_79'"
→ Sequential, keep as list-items
```

---

## 🔀 Monkey Patch vs Post-Processors

| Feature | Monkey Patch | Post-Processors |
|---------|-------------|-----------------|
| **When** | DURING extraction | AFTER extraction complete |
| **Scope** | Page-by-page | Entire document |
| **Purpose** | Add MISSING content | Fix MISCLASSIFIED content |
| **Visibility** | One page at a time | All pages at once |
| **Speed** | Fast (per-page) | Fast (single pass) |
| **Use Cases** | - Missing titles<br>- Missing company names<br>- Missing power lines | - Sequential vs isolated<br>- Cross-page patterns<br>- Document-level rules |

**Why separate?**

1. **Monkey Patch** cannot see across pages → Cannot detect "isolated vs sequential"
2. **Post-Processors** operate on final document → Can analyze all items together
3. **Clear separation** → Easier to maintain and debug

---

## 📝 Usage Example

```python
from pathlib import Path
from docling.document_converter import DocumentConverter
from core.eaf_patch_engine import apply_universal_patch_with_pdf
from core.post_processors import (
    apply_zona_fix_to_document,
    apply_isolated_list_fix_to_document
)

# 1. Setup monkey patch
pdf_path = Path("document.pdf")
apply_universal_patch_with_pdf(str(pdf_path))

# 2. Extract with Docling (monkey patch runs automatically)
converter = DocumentConverter()
result = converter.convert(pdf_path)

# 3. Apply post-processors
doc = result.document
apply_zona_fix_to_document(doc)
apply_isolated_list_fix_to_document(doc)

# 4. Export
# ... export to JSON, Markdown, etc.
```

---

## 🧪 Testing

```bash
# Test imports
python3 -c "
from core.eaf_patch_engine import apply_universal_patch_with_pdf
from core.post_processors import apply_zona_fix_to_document, apply_isolated_list_fix_to_document
print('✅ All imports working')
"

# Test extraction with full pipeline
python3 COMPLETE_REPROCESS_ALL_CHAPTERS.py
```

---

## 📚 Related Documentation

- **Main Guide**: `eaf_patch/docs/EAF_PATCH_README.md`
- **Improvements Catalog**: `eaf_patch/docs/EAF_PATCH_CATALOG.md`
- **Quick Reference**: `eaf_patch/docs/QUICK_REFERENCE.md`
- **Duplicate Detection**: `eaf_patch/DUPLICATE_DETECTION_SUMMARY.md`
- **IOU Algorithm**: `eaf_patch/IOU_OVERLAP_LOGIC_EXPLAINED.md`

---

## 🔮 Future Improvements

### Planned Reorganization

```
eaf_patch/core/
├── monkey_patch/
│   ├── __init__.py
│   ├── patch_engine.py          # Main patching logic
│   ├── pdf_extractor.py         # PyMuPDF text extraction
│   ├── missing_content_detector.py  # Title/company/power line detection
│   └── cluster_builder.py       # Synthetic cluster creation
│
└── post_processors/
    ├── __init__.py
    ├── zona_fix.py             # ✅ Already separated
    ├── isolated_list_fix.py    # ✅ Already separated
    └── (future processors here)
```

### Additional Post-Processors

- [ ] `table_header_fix.py` - Fix table header detection
- [ ] `title_hierarchy_fix.py` - Fix hierarchical title levels
- [ ] `duplicate_removal.py` - Remove cross-page duplicates

---

**Last Updated**: 2025-10-30
**Version**: 3.1
**Status**: ✅ Post-Processors Separated
