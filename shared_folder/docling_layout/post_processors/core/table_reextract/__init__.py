"""
Table Re-extraction Post-Processor

Classifies tables and applies the appropriate extractor to replace
failed TableFormer extractions with accurate data.

Uses Docling's correct bounding boxes but re-extracts content using
specialized extractors based on table type.
"""

import time
from .classifier import classify_table
from .extractors import pymupdf, tableformer
from .custom import costos_horarios

# Registry of extractors by table type
EXTRACTORS = {
    # Custom domain-specific extractors
    "costos_horarios": costos_horarios.extract,
    "demanda_generacion": costos_horarios.extract,  # Same 24-hour format
    "hidroelectricas": pymupdf.extract,  # TODO: Create specific extractor

    # Generic extractors
    "sin_lineas_generico": pymupdf.extract,
    "tableformer_ok": tableformer.keep,
    "default": pymupdf.extract,

    # Skip marker (no extraction)
    "skip": None,
}


def apply_table_reextract_to_document(document, pdf_path):
    """
    Re-extract tables using appropriate extractors based on table type.

    Args:
        document: The Docling document object
        pdf_path: Path to the source PDF file

    Returns:
        int: Number of tables re-extracted
    """
    start_time = time.time()

    print("\n" + "=" * 80)
    print("📊 [TABLE REEXTRACT] Re-extracting tables with specialized extractors")
    print("=" * 80)

    if not hasattr(document, 'tables') or not document.tables:
        print("⚠️  [TABLE REEXTRACT] No tables found - skipping")
        print("=" * 80 + "\n")
        return 0

    total_tables = len(document.tables)
    reextracted = 0
    kept = 0

    print(f"📋 [TABLE REEXTRACT] Processing {total_tables} tables...")

    for i, table in enumerate(document.tables):
        # Get table info
        page_no = table.prov[0].page_no if table.prov else "?"
        current_cells = len(table.data.table_cells) if hasattr(table.data, 'table_cells') else 0

        # Classify table type
        table_type, confidence, reason = classify_table(table, pdf_path)

        # Get appropriate extractor
        extractor = EXTRACTORS.get(table_type, EXTRACTORS["default"])

        if table_type == "skip":
            # Skip this table entirely
            print(f"   Table {i} (p.{page_no}): ⏭ Skipped - {reason}")
            continue

        if table_type == "tableformer_ok":
            # Keep original TableFormer result but convert to simplified structure
            try:
                new_data = extractor(table, pdf_path)
                if new_data:
                    table.data = new_data
                kept += 1
                print(f"   Table {i} (p.{page_no}): ✓ Kept TableFormer ({current_cells} cells) - {reason}")
            except Exception as e:
                kept += 1
                print(f"   Table {i} (p.{page_no}): ✓ Kept original - {reason}")
        else:
            # Re-extract with specialized extractor
            try:
                new_data = extractor(table, pdf_path)

                if new_data:
                    # Replace table data with new structure
                    table.data = new_data
                    reextracted += 1

                    new_rows = len(new_data.get('rows', []))
                    new_cols = len(new_data.get('headers', []))
                    print(f"   Table {i} (p.{page_no}): ↻ Re-extracted ({new_rows}x{new_cols}) - {reason}")
                else:
                    kept += 1
                    print(f"   Table {i} (p.{page_no}): ⚠ Extraction failed, kept original")

            except Exception as e:
                kept += 1
                print(f"   Table {i} (p.{page_no}): ❌ Error: {str(e)[:50]}")

    elapsed = time.time() - start_time

    print(f"\n✅ [TABLE REEXTRACT] Re-extracted: {reextracted}, Kept: {kept}")
    print(f"⏱️  [TABLE REEXTRACT] Processing time: {elapsed:.3f} seconds")
    print("=" * 80 + "\n")

    return reextracted
