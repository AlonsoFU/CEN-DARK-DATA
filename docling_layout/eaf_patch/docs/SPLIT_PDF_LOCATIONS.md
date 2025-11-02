# Split PDF Locations for EAF-089-2025

⭐ **IMPORTANT**: All chapters are available as individual split PDFs. Always use these instead of processing the full 399-page PDF.

## Split PDF Directory

**Base Path**: `/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/`

## Individual Chapter PDFs

| Chapter | Pages (Original) | Page Count | Split PDF Path |
|---------|-----------------|-----------|----------------|
| 1 | 1-11 | 11 | `claude_ocr/capitulo_01/EAF-089-2025_capitulo_01_pages_1-11.pdf` |
| 2 | 12-90 | 79 | `claude_ocr/capitulo_02/EAF-089-2025_capitulo_02_pages_12-90.pdf` |
| 3 | 91-153 | 63 | `claude_ocr/capitulo_03/EAF-089-2025_capitulo_03_pages_91-153.pdf` |
| 4 | 154-159 | 6 | `claude_ocr/capitulo_04/EAF-089-2025_capitulo_04_pages_154-159.pdf` |
| 5 | 160-171 | 12 | `claude_ocr/capitulo_05/EAF-089-2025_capitulo_05_pages_160-171.pdf` |
| 6 | 172-265 | 94 | `claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf` |
| 7 | 266-347 | 82 | `claude_ocr/capitulo_07/EAF-089-2025_capitulo_07_pages_266-347.pdf` |
| 8 | 348-348 | 1 | `claude_ocr/capitulo_08/EAF-089-2025_capitulo_08_pages_348-348.pdf` |
| 9 | 349-381 | 33 | `claude_ocr/capitulo_09/EAF-089-2025_capitulo_09_pages_349-381.pdf` |
| 10 | 382-392 | 11 | `claude_ocr/capitulo_10/EAF-089-2025_capitulo_10_pages_382-392.pdf` |
| 11 | 393-399 | 7 | `claude_ocr/capitulo_11/EAF-089-2025_capitulo_11_pages_393-399.pdf` |

**Total**: 399 pages across 11 chapters

## Processing Time Comparison

### Using Full PDF (EAF-089-2025.pdf - 399 pages)
- Processing time: **~20-25 minutes**
- Docling must process all pages then filter
- GPU/CPU usage for entire duration
- Inefficient for single chapter extraction

### Using Split PDFs
- Processing time per chapter: **~2-5 minutes** (depending on chapter size)
- Only processes relevant pages
- Faster iteration during development
- **10x faster** for single-chapter work

## Example: Chapter 6

### ❌ Wrong Way (Full PDF)
```python
PDF_PATH = Path("/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")
# Processing time: ~20-25 minutes
# Must filter pages 172-265 after processing all 399 pages
```

### ✅ Right Way (Split PDF)
```python
PDF_PATH = Path("/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
# Processing time: ~2-3 minutes
# Only processes 94 pages
```

**Speed improvement**: 7-10x faster

## Updated Script Templates

### Generic Chapter Processing Template

```python
# ⭐ ALWAYS USE SPLIT PDF
CHAPTER_NUM = 6
BASE_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr")
PDF_PATH = BASE_PATH / f"capitulo_{CHAPTER_NUM:02d}" / f"EAF-089-2025_capitulo_{CHAPTER_NUM:02d}_pages_*.pdf"

# Or use direct path
PDF_PATH = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr/capitulo_06/EAF-089-2025_capitulo_06_pages_172-265.pdf")
```

## Chapter Characteristics

| Chapter | Type | Key Content |
|---------|------|-------------|
| 1 | Intro | Failure description (11 pages) |
| 2 | Data | Affected equipment (79 pages - largest!) |
| 3 | Data | Unsupplied energy (63 pages) |
| 4 | Data | Failure configurations (6 pages - smallest except ch8) |
| 5 | Timeline | Event chronology (12 pages) |
| 6 | Data | **Service normalization (94 pages - 2nd largest)** |
| 7 | Analysis | Failure cause analysis (82 pages - 3rd largest) |
| 8 | Misc | Detailed information (1 page - smallest!) |
| 9 | Technical | Protection analysis (33 pages) |
| 10 | Official | Technical statement (11 pages) |
| 11 | Recommendations | Recommendations (7 pages) |

## When to Use Full PDF vs Split PDF

### Use Split PDF (Default)
- ✅ Processing individual chapters
- ✅ Development and testing
- ✅ Iterating on extraction logic
- ✅ GPU memory limited (4GB)
- ✅ Fast turnaround needed

### Use Full PDF (Rare)
- ⚠️ Cross-chapter analysis requiring unified page numbering
- ⚠️ Batch processing all chapters sequentially
- ⚠️ Generating reports spanning multiple chapters

**Recommendation**: 95% of the time, use split PDFs. They're faster and easier to work with.

## Finding Split PDFs

### Quick Command
```bash
# List all split chapter PDFs
find /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/claude_ocr \
  -name "EAF-089-2025_capitulo*.pdf" | sort

# Get specific chapter
CHAPTER=6
find /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/claude_ocr \
  -name "EAF-089-2025_capitulo_${CHAPTER}_*.pdf"
```

### Python Helper
```python
from pathlib import Path

def get_chapter_pdf(chapter_num: int) -> Path:
    """Get split PDF path for a chapter"""
    base = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN")
    chapter_dir = base / "shared_platform/utils/outputs/claude_ocr" / f"capitulo_{chapter_num:02d}"
    
    # Find the split PDF
    pdfs = list(chapter_dir.glob(f"EAF-089-2025_capitulo_{chapter_num:02d}_pages_*.pdf"))
    
    if not pdfs:
        raise FileNotFoundError(f"No split PDF found for chapter {chapter_num}")
    
    return pdfs[0]

# Usage
chapter_6_pdf = get_chapter_pdf(6)
print(f"Chapter 6 PDF: {chapter_6_pdf}")
# Output: .../EAF-089-2025_capitulo_06_pages_172-265.pdf
```

## Migration Checklist

When updating existing scripts to use split PDFs:

- [ ] Update `PDF_PATH` to point to split PDF location
- [ ] Remove page filtering logic (split PDF contains only chapter pages)
- [ ] Update processing time estimates in comments/prints
- [ ] Update page number extraction (split PDFs start at page 1, not original page number)
- [ ] Test with split PDF to verify output matches
- [ ] Update documentation to reference split PDF usage

## Notes

1. **Page Numbers**: Split PDFs renumber pages starting from 1. If you need original page numbers, add the chapter start offset.
2. **File Naming**: Pattern is `EAF-089-2025_capitulo_{chapter:02d}_pages_{start}-{end}.pdf`
3. **Location**: All split PDFs are in `claude_ocr/capitulo_XX/` directories
4. **Git**: These PDFs are `.gitignored` - they won't be committed to version control

---

**Generated**: 2025-10-22
**Source**: EAF-089-2025.pdf (399 pages)
**Split Tool**: PyMuPDF-based PDF splitter
