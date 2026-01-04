# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF extraction system for Chilean electrical system documents (EAF reports - Estudio de Análisis de Falla) using IBM Docling with domain-specific enhancements. The system extracts structured data from technical PDFs and outputs JSON conforming to Docling's native schema.

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Extract a single chapter (from shared_folder/docling_layout/)
python3 EXTRACT_ANY_CHAPTER.py 1 --report EAF-089-2025

# Extract all chapters
for i in {1..11}; do python3 EXTRACT_ANY_CHAPTER.py $i --report EAF-089-2025; done

# Verify extraction output
jq '.texts | length' data/outputs/EAF-089-2025/capitulo_01/layout_WITH_PATCH.json

# Run tests
pytest

# Monitor GPU during extraction
watch -n 1 nvidia-smi
```

## Architecture

### Two-Phase Extraction Pipeline

```
PDF → [Docling + Monkey Patch] → [Post-Processors] → JSON
         (page-level)              (document-level)
```

**Phase 1: Docling + EAF Monkey Patch** (`shared_folder/docling_layout/eaf_patch/`)
- Intercepts Docling's `LayoutPostprocessor._process_regular_clusters()` method
- Extracts missing text directly from PDF using PyMuPDF when Docling fails
- Detects: missing titles, company names, power line references
- Applies during page-by-page processing

**Phase 2: Post-Processors** (`shared_folder/docling_layout/post_processors/core/`)
- Run after full document extraction
- `enumerated_item_fix.py` - Smart reclassification (10 parts: bullets, enumerations, captions, isolated items)
- `table_reextract/` - Re-extracts failed tables using PyMuPDF with modular extractors:
  - `classifier.py` - Pre-scans tables with PyMuPDF and classifies by content keywords
  - `extractors/` - Generic extractors (pymupdf, tableformer, line_based, position_based)
  - `custom/` - Domain-specific extractors (see list below)
  - Each extractor includes validation with confidence scores and error tracking
- `table_continuation_merger.py` - Merges split tables across pages (detects same headers + consecutive pages)
- `hierarchy_restructure.py` - Builds parent-child relationships using numbered patterns
- `metadata_date_extractor.py` - Extracts emission/failure dates to metadata

### Key Files

- `shared_folder/docling_layout/EXTRACT_ANY_CHAPTER.py` - Main extraction script
- `shared_folder/docling_layout/eaf_patch/core/eaf_patch_engine.py` - Monkey patch engine
- `shared_folder/docling_layout/post_processors/core/__init__.py` - Post-processor exports

### Domain Processing (`domains/`)

- `domains/operaciones/eaf/` - Individual EAF report processors
- `domains/operaciones/anexos_eaf/` - EAF annexes processing
- Each domain has: `chapters/`, `shared/`, processors, and schema adapters

### Data Flow

```
data/inputs/{report_id}/capitulos/capitulo_XX.pdf
    ↓
shared_folder/docling_layout/EXTRACT_ANY_CHAPTER.py
    ↓
data/outputs/{report_id}/capitulo_XX/
    ├── layout_WITH_PATCH.json    # Docling native format with modifications
    ├── chapterXX_DOCLING.pdf     # Annotated PDF (before post-processors)
    └── chapterXX_FINAL.pdf       # Annotated PDF (after post-processors)
```

## Configuration

The extraction uses optimized settings for 4GB GPU:
- `do_ocr = False` - Uses PDF text layer instead
- `TableFormerMode.ACCURATE` - Best table detection
- `force_backend_text = True` - Faster, more accurate text extraction

Chapter page ranges are defined in `REPORT_CHAPTERS` dict in `EXTRACT_ANY_CHAPTER.py`.

## Adding Table Extractors

Custom extractors go in `post_processors/core/table_reextract/custom/`:

```python
# custom/my_extractor.py
def extract(table, pdf_path):
    """Extract table data using PyMuPDF."""
    # Get bbox and page from table.prov[0]
    # Extract text with fitz.open(pdf_path)
    data = {
        "headers": ["Col1", "Col2", ...],
        "rows": [["val1", "val2", ...], ...],
        "num_rows": N,
        "num_cols": M,
        "extractor": "my_extractor"
    }
    data["validation"] = validate(data)
    return data

def validate(data):
    """Validate extracted data."""
    errors = []
    warnings = []
    # Add validation logic
    return {
        "valid": len(errors) == 0,
        "confidence": 0.9,
        "errors": errors,
        "warnings": warnings
    }
```

Register in `classifier.py`:
1. Add `_is_my_table_type(text)` function with keyword detection
2. Add classification rule in `classify_table()`
3. Import in `custom/__init__.py`
4. Add to `EXTRACTORS` dict in `table_reextract/__init__.py`

### Current Custom Extractors

| Extractor | Table Type | Description |
|-----------|------------|-------------|
| `programacion_diaria` | 26-col hourly | Daily programming (Concepto\|1-24\|Total) |
| `costos_horarios` | 26-col hourly | Marginal costs |
| `horario_tecnologia` | 26-col hourly | TÉRMICAS/HIDRÁULICAS/EÓLICAS by region |
| `movimientos_despacho` | Operation | Dispatch movements with timestamps |
| `registro_operacion_sen` | Operation | SEN operation records |
| `reporte_desconexion` | Operation | Disconnection reports |
| `centrales_desvio` | Generation | Central\|Prog\|Real\|Desv%\|Estado |
| `centrales_grandes` | Generation | Large plants (≥100 MW) availability |
| `indicador_compacto` | Indicators | Cotas, Inercia, etc. |
| `eventos_hora` | Events | Hora\|Centro Control\|Observación |
| `scada_alarmas` | Events | SCADA alarm logs |

## Output Format

Uses Docling's native `DoclingDocument` schema with additions:
- `origin.fecha_emision`, `origin.fecha_falla`, `origin.hora_falla` (extracted dates)
- `texts[].children[]` (hierarchy references using `$ref`)
- `tables[].data` - Re-extracted table structure:
  ```json
  {
    "extractor": "programacion_diaria",
    "headers": ["Concepto", "1", "2", ..., "24", "Total"],
    "rows": [["Central X", "100", "105", ...]],
    "num_rows": 15,
    "num_cols": 26,
    "validation": {
      "valid": true,
      "confidence": 0.9,
      "errors": [],
      "warnings": []
    },
    "is_continuation": false
  }
  ```
