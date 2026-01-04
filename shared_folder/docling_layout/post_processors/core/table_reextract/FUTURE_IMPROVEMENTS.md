# Mejoras Futuras - Table Reextract

## Optimización de Velocidad (Principal)

**Problema actual:** TableFormer procesa ~2000 celdas/página (~1 hora para 143 páginas) y luego PyMuPDF reemplaza esos datos. Trabajo desperdiciado.

**Solución propuesta:** Desactivar TableFormer de Docling
```python
pipeline_options = PdfPipelineOptions(
    do_table_structure=False,  # Solo detecta tablas, no extrae celdas
)
```

- Mantiene detección de bounding boxes (layout analysis)
- Elimina extracción de celdas con TableFormer (el paso lento)
- PyMuPDF extrae todo el contenido de tablas
- **Resultado esperado:** ~10x más rápido

**Otras optimizaciones:**
- Implementar pre-clasificación antes de Docling usando PyMuPDF
- Monkey-patch del modelo TableFormer para saltar tablas específicas
- Usar `TableFormerMode.FAST` en vez de ACCURATE para ciertas tablas

## Clasificación

- Mejorar detección de tablas hidroeléctricas
- Agregar clasificador para tablas de generación/demanda
- Detectar tablas con celdas fusionadas (necesitan TableFormer)
- Clasificación basada en estructura visual (líneas vs sin líneas)

## Extractores Específicos

**Implementados:**
- ✅ `programacion_diaria` - Tablas diarias COORDINADOR ELÉCTRICO (26 cols)
- ✅ `costos_horarios` - Tablas de costos por hora (26 cols)

**Pendientes:**
- Extractor para tablas de centrales térmicas
- Extractor para tablas de transmisión
- Extractor para tablas de balance energético
- Soporte para tablas multi-página

## Paralelización

- Procesar múltiples tablas en paralelo con PyMuPDF
- Usar multiprocessing para re-extracción masiva

## Validadores por Tipo de Extractor

Cada extractor puede tener lógica y validadores especializados:

**programacion_diaria:** ✅ IMPLEMENTADO
- Validar 26 columnas (Concepto + 1-24 + Total)
- Valores numéricos en columnas 1-24
- Detecta tablas con COORDINADOR ELÉCTRICO NACIONAL
- Maneja anomalías (tablas con keywords pero estructura diferente)

**costos_horarios:**
- Validar 26 columnas (Concepto + 1-24 + Total)
- Valores numéricos en columnas 1-24
- Total = suma de horas
- Unidades esperadas (kUSD, MWh, USD/MWh)

**hidroelectricas:**
- Columnas: Central, Potencia, Generación, Factor
- Valores de potencia en rango válido (MW)
- Factor de planta entre 0-100%

**demanda_generacion:**
- Balance: Generación ≈ Demanda + Pérdidas
- Valores positivos
- Consistencia temporal (24 horas)

**Estructura propuesta:**
```python
# custom/costos_horarios.py
def extract(table, pdf_path):
    data = _extract_data(...)
    return data

def validate(data):
    errors = []
    if data["num_cols"] != 26:
        errors.append("Expected 26 columns")
    # más validaciones...
    return {"valid": len(errors) == 0, "errors": errors}
```

## Calidad General

- Métrica de confianza por tabla (0-1)
- Detección automática de errores de extracción
- Reporte de tablas que fallaron validación
- Fallback a otro extractor si validación falla

## Almacenamiento de Errores

Los errores se guardan en el campo `data` de cada tabla:

```json
{
  "data": {
    "extractor": "costos_horarios",
    "headers": [...],
    "rows": [...],
    "num_rows": 8,
    "num_cols": 24,
    "validation": {
      "valid": false,
      "confidence": 0.75,
      "errors": [
        "Expected 26 columns, got 24",
        "Missing 'Total' column"
      ],
      "warnings": [
        "Row 3 has non-numeric value in hour column"
      ]
    }
  }
}
```

**Reporte global** al final de extracción:
```
================================================================================
📋 TABLE VALIDATION REPORT
================================================================================
✅ Valid: 140/153 tables (91.5%)
⚠️  Warnings: 8 tables
❌ Errors: 5 tables

Tables with errors:
  - Table 12 (page 15): Missing columns
  - Table 45 (page 38): Invalid numeric values
  ...
================================================================================
```

**Reporte por capítulo** (si hay errores):
```
outputs/capitulo_XX/table_errors.txt
```

Ejemplo conciso:
```
TABLE ERRORS - Capitulo 11
==========================
Total: 153 tables | Errors: 3

Table 12 (pg 15): 24 cols, expected 26
Table 45 (pg 38): Non-numeric in col 5
Table 89 (pg 67): Empty row 3
```

Solo se genera si hay errores. Sin errores = no archivo.
