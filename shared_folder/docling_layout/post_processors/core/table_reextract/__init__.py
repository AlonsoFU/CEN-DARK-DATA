"""
Table Re-extraction Post-Processor

Classifies tables and applies the appropriate extractor to replace
failed TableFormer extractions with accurate data.

Uses Docling's correct bounding boxes but re-extracts content using
specialized extractors based on table type.
"""

import time
from .classifier import classify_table
from .extractors import pymupdf, tableformer, line_based, position_based
from .custom import (
    costos_horarios,
    programacion_diaria,
    centrales_desvio,
    centrales_grandes,
    movimientos_despacho,
    registro_operacion_sen,
    reporte_desconexion,
    horario_tecnologia,
    indicador_compacto,
    eventos_hora,
    scada_alarmas,
)

# Registry of extractors by table type
EXTRACTORS = {
    # === HOURLY TABLES (26 cols: X|1-24|Total) ===
    "programacion_diaria": programacion_diaria.extract,  # Concepto|1-24|Total
    "costos_horarios": costos_horarios.extract,          # Costos marginales
    "demanda_generacion": costos_horarios.extract,       # Same 24-hour format
    "horario_tecnologia": horario_tecnologia.extract,    # TÉRMICAS/HIDRÁULICAS/EÓLICAS

    # === OPERATION TABLES ===
    "movimientos_despacho": movimientos_despacho.extract,      # Dispatch movements
    "registro_operacion_sen": registro_operacion_sen.extract,  # SEN operation records
    "reporte_desconexion": reporte_desconexion.extract,        # Disconnection reports

    # === GENERATION TABLES ===
    "centrales_desvio": centrales_desvio.extract,        # Central|Prog|Real|Desv%|Estado
    "centrales_grandes": centrales_grandes.extract,      # CENTRAL ≥100 MW|Disp|Obs
    "hidroelectricas": pymupdf.extract,                  # Legacy - uses generic

    # === INDICATOR TABLES ===
    "indicador_compacto": indicador_compacto.extract,    # Cotas, Inercia, etc.

    # === EVENT TABLES ===
    "eventos_hora": eventos_hora.extract,                # Hora|Centro Control|Obs
    "scada_alarmas": scada_alarmas.extract,              # SCADA logs
    "infraestructura_sen": pymupdf.extract,              # Infrastructure status

    # === LINE-BASED EXTRACTOR ===
    "line_based": line_based.extract,  # Tables with visible grid lines

    # === POSITION-BASED EXTRACTOR ===
    "position_based": position_based.extract,  # Tables without lines (auto-detect columns)

    # === GENERIC EXTRACTORS ===
    "sin_lineas_generico": position_based.extract,  # Changed from pymupdf to position_based
    "tableformer_ok": tableformer.keep,
    "default": pymupdf.extract,

    # Skip marker (no extraction)
    "skip": None,
}


def apply_table_reextract_to_document(document, pdf_path, force_pymupdf=False):
    """
    Re-extract tables using appropriate extractors based on table type.

    Args:
        document: The Docling document object
        pdf_path: Path to the source PDF file
        force_pymupdf: If True, always use PyMuPDF extraction instead of TableFormer

    Returns:
        int: Number of tables re-extracted
    """
    start_time = time.time()

    print("\n" + "=" * 80)
    mode = "PyMuPDF only" if force_pymupdf else "Smart classification"
    print(f"📊 [TABLE REEXTRACT] Re-extracting tables ({mode})")
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
        if force_pymupdf:
            # Force PyMuPDF extraction, but still classify for custom extractors
            table_type, confidence, reason = classify_table(table, pdf_path)
            # Override tableformer_ok to use pymupdf instead
            if table_type == "tableformer_ok":
                table_type = "default"
                reason = "Forced PyMuPDF mode"
        else:
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
