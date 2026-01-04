"""
Registro Operación SEN Extractor

Extractor for "Registro de Operación del Sistema Eléctrico Nacional" tables.

These tables have:
- 30 columns (mostly empty headers in PDF)
- Data about system operation events
- Multiple rows of operational records
"""

import fitz
import re


def extract(table, pdf_path):
    """
    Extract registro operación SEN table.

    Args:
        table: Docling table object
        pdf_path: Path to source PDF

    Returns:
        dict: Simplified table structure
    """
    if not table.prov:
        return None

    bbox = table.prov[0].bbox
    page_no = table.prov[0].page_no

    try:
        doc = fitz.open(pdf_path)
        page = doc[page_no - 1]
        page_height = page.rect.height

        rect = fitz.Rect(
            bbox.l,
            page_height - bbox.t,
            bbox.r,
            page_height - bbox.b
        )

        blocks = page.get_text("dict", clip=rect)["blocks"]

        text_items = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            text_items.append({
                                "text": text,
                                "x": span["bbox"][0],
                                "y": span["bbox"][1],
                            })

        doc.close()

        if not text_items:
            return None

        text_items.sort(key=lambda item: (round(item["y"], 0), item["x"]))
        rows = _group_into_rows(text_items, tolerance=3)
        data = _process_registro_table(rows)

        if data:
            data["validation"] = validate(data)

        return data

    except Exception as e:
        print(f"      Registro operación SEN extraction error: {e}")
        return None


def validate(data):
    """Validate extracted registro operación table."""
    errors = []
    warnings = []

    # These tables have ~30 columns
    if data["num_cols"] < 15:
        warnings.append(f"Expected ~30 cols, got {data['num_cols']}")

    # Check for date pattern
    date_pattern = re.compile(r'\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2}')
    date_found = False
    for row in data.get("rows", []):
        for cell in row:
            if date_pattern.search(str(cell)):
                date_found = True
                break
        if date_found:
            break

    if not date_found:
        warnings.append("No date values found in data")

    # Validate row count
    if data["num_rows"] == 0:
        errors.append("No data rows extracted")

    confidence = 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.1)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "valid": len(errors) == 0,
        "confidence": round(confidence, 2),
        "errors": errors,
        "warnings": warnings
    }


def _group_into_rows(text_items, tolerance=3):
    """Group text items into rows by Y position."""
    rows = []
    current_row = []
    current_y = None

    for item in text_items:
        if current_y is None or abs(item["y"] - current_y) < tolerance:
            current_row.append(item)
            current_y = item["y"] if current_y is None else current_y
        else:
            if current_row:
                current_row.sort(key=lambda x: x["x"])
                rows.append(current_row)
            current_row = [item]
            current_y = item["y"]

    if current_row:
        current_row.sort(key=lambda x: x["x"])
        rows.append(current_row)

    return rows


def _process_registro_table(rows):
    """Process rows for registro operación format."""
    if not rows:
        return None

    # Standard headers for registro operación
    headers = [
        "Registro", "Fecha", "Hora", "Tipo", "Instalación", "Elemento",
        "Empresa", "Descripción", "Causa", "Efecto", "Acciones",
        "Tiempo_Inicio", "Tiempo_Fin", "Duración", "Estado",
        "Observaciones", "Código", "Referencia", "Usuario", "Sistema",
        "Subsistema", "Zona", "Región", "Tensión", "Potencia",
        "Energía", "Frecuencia", "Voltaje", "Corriente", "Factor"
    ]

    data_rows = []
    detected_cols = 30

    for row in rows:
        texts = [item["text"] for item in row]

        # Skip header/title rows
        if _is_header_row(texts):
            continue

        if texts:
            data_rows.append(texts)
            detected_cols = max(detected_cols, len(texts))

    if not data_rows:
        return None

    # Use detected column count
    final_headers = headers[:detected_cols]
    if len(final_headers) < detected_cols:
        final_headers += [f"Col{i}" for i in range(len(final_headers), detected_cols)]

    # Normalize rows
    normalized = []
    for row in data_rows:
        padded = row + [""] * (detected_cols - len(row))
        normalized.append(padded[:detected_cols])

    return {
        "headers": final_headers,
        "rows": normalized,
        "num_rows": len(normalized),
        "num_cols": detected_cols,
        "extractor": "registro_operacion_sen"
    }


def _is_header_row(texts):
    """Check if row is a header/title."""
    combined = " ".join(texts).lower()
    if "registro de operación" in combined:
        return True
    if "sistema eléctrico nacional" in combined:
        return True
    return False
