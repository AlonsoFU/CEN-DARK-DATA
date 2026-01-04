# EAF Document Extraction System

Sistema de extracción de documentos PDF para informes EAF (Estudio de Análisis de Falla) del sistema eléctrico chileno usando Docling con mejoras domain-specific.

**Status**: Production-Ready ✅

---

## Tabla de Contenidos

1. [Overview](#overview)
2. [Requisitos](#requisitos)
3. [Setup](#setup)
4. [Cómo Usar](#cómo-usar)
5. [Pipeline de Procesamiento](#pipeline-de-procesamiento)
6. [Formato de Salida](#formato-de-salida)
7. [Procesar Nuevo Informe](#procesar-nuevo-informe)
8. [Troubleshooting](#troubleshooting)
9. [Estructura del Proyecto](#estructura-del-proyecto)

---

## Overview

Este sistema extrae contenido estructurado de PDFs usando:

1. **Docling** - Extracción base con IA (layout analysis, table detection)
2. **EAF Monkey Patch** - Mejoras domain-specific durante extracción
3. **Post-Processors** - Refinamientos después de extracción
   - Smart Reclassification (9 partes)
   - Hierarchy Restructure (estructura padre-hijo)
   - Metadata Date Extractor

### Resultados del Informe EAF-089-2025

| Capítulo | Páginas | Texts | Tables | Pictures |
|----------|---------|-------|--------|----------|
| 1 | 11 | 50 | 12 | 0 |
| 2 | 79 | 1307 | 81 | 7 |
| 3 | 62 | 774 | 63 | 3 |
| 4 | 7 | 57 | 0 | 4 |
| 5 | 12 | 14 | 12 | 0 |
| 6 | 94 | 466 | 81 | 0 |
| 7 | 82 | 628 | 61 | 57 |
| 8 | 1 | 10 | 1 | 0 |
| 9 | 33 | 712 | 7 | 0 |
| 10 | 11 | 164 | 0 | 0 |
| 11 | 7 | 128 | 0 | 0 |
| **TOTAL** | **399** | **4310** | **318** | **71** |

---

## Requisitos

### Hardware
- **GPU**: 4GB+ VRAM (recomendado 6GB+)
- **RAM**: 8GB+ sistema
- **CPU fallback**: Funciona pero 10x más lento

### Software
- Python 3.11+
- CUDA (para GPU)

---

## Setup

### 1. Crear Virtual Environment

```bash
cd /home/alonso/Documentos/Github/dark-data-docling-extractors
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar Dependencias

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Primera Ejecución

La primera vez descarga modelos (~2GB, 20-30 min). Ejecuciones posteriores son 40x más rápidas.

---

## Cómo Usar

### Extraer Un Capítulo

```bash
cd shared_folder/docling_layout
source ../../venv/bin/activate

# Básico (usa defaults)
python3 EXTRACT_ANY_CHAPTER.py 1

# Especificando report
python3 EXTRACT_ANY_CHAPTER.py 1 --report EAF-089-2025

# Con rutas personalizadas
python3 EXTRACT_ANY_CHAPTER.py 1 --report EAF-090-2026 --input ./data/inputs --output ./data/outputs
```

### Extraer Todos los Capítulos

```bash
for i in {1..11}; do
  python3 EXTRACT_ANY_CHAPTER.py $i --report EAF-089-2025
done
```

### Con Rango de Páginas Personalizado

```bash
python3 EXTRACT_ANY_CHAPTER.py 1 --pages 1-50
```

### Tiempo Estimado

- ~6 segundos por página con GPU
- ~40 minutos total para 399 páginas

---

## Pipeline de Procesamiento

El sistema procesa en 6 etapas:

```
PDF → [1. Docling + Patch] → [2. Reclassification] → [3. Isolated Fix] → [4. Table Reextract] → [5. Hierarchy] → [6. Metadata] → JSON
```

### 1. Docling + EAF Monkey Patch

Intercepta el pipeline de Docling y aplica:
- Detección de títulos completos desde PyMuPDF
- Detección de nombres de empresas (S.A., Ltda.)
- Clasificación de líneas de poder (kV)
- Continuidad de listas cross-page

### 2. Smart Reclassification (10 partes)

Reclasifica elementos mal detectados (`enumerated_item_fix.py`):
- PART 1-3: Secuencias de bullets y numeración
- PART 4-6: Patrones enumerados (a, b, c)
- PART 7-8: Títulos de zona/área y captions
- PART 9: Listas aisladas
- PART 10: Normalización de headers similares

### 3. Isolated List Fix

Corrige listas que quedaron aisladas sin contexto (`isolated_list_fix.py`).

### 4. Table Re-extraction ⭐ NUEVO

Re-extrae contenido de tablas usando PyMuPDF (`table_reextract/`):
- Usa bounding boxes correctos de Docling
- Reemplaza extracción fallida de TableFormer
- Clasifica tipo de tabla y aplica extractor específico
- Genera estructura simplificada para LLMs:
  ```json
  {
    "extractor": "pymupdf",
    "headers": ["Col1", "Col2", ...],
    "rows": [["val1", "val2", ...], ...],
    "num_rows": 8,
    "num_cols": 26
  }
  ```

**Extractores disponibles:**
- `costos_horarios` - Tablas de costos por hora (1-24)
- `pymupdf` - Extractor genérico para tablas sin líneas
- `tableformer` - Mantiene resultado original de Docling

**Parámetro `force_pymupdf`:**
- Por defecto: `True`
- Fuerza uso de PyMuPDF incluso cuando TableFormer funciona bien
- Garantiza estructura simplificada consistente

**Resultados EAF-477-2025 Cap 11 (153 tablas):**
- `costos_horarios`: 27 tablas
- `pymupdf`: 54 tablas
- `tableformer`: 72 tablas
- **81 tablas (53%) re-extraídas con PyMuPDF**

**Ejemplo de mejora:**
- Tabla 0 antes: 2 celdas (TableFormer falló)
- Tabla 0 después: 8×26 = 208 valores correctos

### 5. Hierarchy Restructure

Construye jerarquía padre-hijo usando patrones (`hierarchy_restructure.py`):
- `1.`, `2.` → Nivel 1
- `1.1`, `2.3` → Nivel 2
- `a)`, `b)` → Nivel 3
- `a.`, `b.` → Nivel 4

Popula arrays `children[]` con referencias `$ref`.

### 6. Metadata Date Extractor

Extrae fechas a metadata (`metadata_date_extractor.py`):
- `fecha_emision`
- `fecha_falla`
- `hora_falla`

---

## Formato de Salida

### Archivos Generados

```
capitulo_XX/outputs/
├── layout_WITH_PATCH.json           # JSON estructurado
└── chapterXX_WITH_PATCH_annotated.pdf  # PDF anotado visual
```

### Estructura JSON (Docling Nativo)

```json
{
  "schema_name": "DoclingDocument",
  "version": "1.0.0",
  "name": "archivo.pdf",
  "origin": {
    "fecha_emision": "18-03-2025",
    "fecha_falla": "21-02-2025",
    "hora_falla": "10:28:41"
  },
  "body": {
    "children": [{"$ref": "#/texts/0"}, ...]
  },
  "texts": [
    {
      "label": "section_header",
      "text": "1. Descripción...",
      "children": [{"$ref": "#/texts/1"}, {"$ref": "#/texts/2"}]
    }
  ],
  "tables": [...],
  "pictures": [...]
}
```

### Colores del PDF Anotado

- 🔴 **Rojo** = section_header / title
- 🔵 **Azul** = text
- 🟢 **Verde** = table
- 🔵🟢 **Cyan** = list_item
- 🟣 **Magenta** = picture
- 🟠 **Orange** = caption

---

## Procesar Nuevo Informe

### Paso 1: Preparar Archivos

1. **Crear carpeta** para el nuevo report en `data/inputs/`:
   ```bash
   mkdir -p data/inputs/EAF-090-2026
   ```

2. **Colocar PDFs** divididos por capítulo:
   ```
   data/inputs/EAF-090-2026/
   ├── capitulo_01.pdf
   ├── capitulo_02.pdf
   └── ...
   ```

   O con el nombre alternativo:
   ```
   EAF-090-2026_capitulo_01_pages_1-20.pdf
   ```

### Paso 2: Configurar Capítulos

Agregar el nuevo report en `EXTRACT_ANY_CHAPTER.py`:

```python
REPORT_CHAPTERS = {
    "EAF-089-2025": {...},  # Existente
    "EAF-090-2026": {       # Nuevo
        1: (1, 20),
        2: (21, 100),
        3: (101, 150),
        # ...
    },
}
```

### Paso 3: Extraer

```bash
cd shared_folder/docling_layout
source ../../venv/bin/activate

for i in {1..N}; do
  python3 EXTRACT_ANY_CHAPTER.py $i --report EAF-090-2026
done
```

### Resultados

Los outputs van a:
```
data/outputs/EAF-090-2026/
├── capitulo_01/
│   ├── layout_WITH_PATCH.json
│   └── chapter01_WITH_PATCH_annotated.pdf
├── capitulo_02/
└── ...

---

## Troubleshooting

### CUDA out of memory

El script usa ~3GB VRAM. Si falla:
- Cerrar otras aplicaciones GPU
- Reducir batch size en el código
- Usar CPU (más lento)

### Primera ejecución muy lenta (20+ min)

Normal - descarga modelos (~2GB). Segunda ejecución será ~34 segundos.

### GPU no detectada

```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# Debe imprimir: True
```

Si es False, verifica instalación CUDA.

### Quiero re-procesar un capítulo

```bash
rm capitulo_XX/outputs/layout_WITH_PATCH.json
rm capitulo_XX/outputs/chapterXX_WITH_PATCH_annotated.pdf
python3 EXTRACT_ANY_CHAPTER.py XX
```

### Boxes desalineados en PDF

Verificar conversión de coordenadas:
```python
bbox_tl = bbox.to_top_left_origin(page_height=page.size.height)
```

---

## Estructura del Proyecto

```
dark-data-docling-extractors/
│
├── data/                           # Datos (git-ignored)
│   ├── inputs/                     # PDFs de entrada
│   │   └── EAF-089-2025/
│   │       ├── capitulo_01.pdf
│   │       └── ...
│   └── outputs/                    # Resultados
│       └── EAF-089-2025/
│           └── capitulo_01/
│               ├── layout_WITH_PATCH.json
│               └── chapter01_WITH_PATCH_annotated.pdf
│
└── shared_folder/docling_layout/   # Código (tracked en git)
    ├── EXTRACT_ANY_CHAPTER.py      # Script principal
    ├── README.md                   # Este archivo
    ├── DOCLING_COMPLETE_GUIDE.md   # Guía técnica
    │
    ├── eaf_patch/                  # Monkey patch
    │   ├── core/                   # Código
    │   └── docs/                   # Documentación
    │
    └── post_processors/            # Post-procesadores
        ├── core/
        │   ├── __init__.py
        │   ├── enumerated_item_fix.py      # 2. Smart Reclassification
        │   ├── isolated_list_fix.py        # 3. Isolated List Fix
        │   ├── table_reextract/            # 4. Table Re-extraction ⭐
        │   │   ├── __init__.py             # Entry point
        │   │   ├── classifier.py           # Clasifica tipo de tabla
        │   │   ├── extractors/             # Extractores genéricos
        │   │   │   ├── pymupdf.py          # Tablas sin líneas
        │   │   │   └── tableformer.py      # Mantiene Docling
        │   │   └── custom/                 # Extractores específicos
        │   │       └── costos_horarios.py  # Tablas 24 horas
        │   ├── hierarchy_restructure.py    # 5. Hierarchy
        │   └── metadata_date_extractor.py  # 6. Metadata
        └── docs/
            └── POST_PROCESSOR_CATALOG.md
```

---

## Documentación Adicional

- **Post-Processors**: `post_processors/docs/POST_PROCESSOR_CATALOG.md`
- **Table Reextract**: `post_processors/core/table_reextract/FUTURE_IMPROVEMENTS.md`
- **Monkey Patch**: `eaf_patch/docs/EAF_PATCH_README.md`
- **Guía Técnica**: `DOCLING_COMPLETE_GUIDE.md`

---

## Verificación de Resultados

```bash
# Verificar JSON generado
jq '.texts | length' data/outputs/EAF-089-2025/capitulo_01/layout_WITH_PATCH.json
jq '.tables | length' data/outputs/EAF-089-2025/capitulo_01/layout_WITH_PATCH.json

# Ver jerarquía
jq '.texts[] | select(.children | length > 0) | {text: .text[0:50], children: (.children | length)}' data/outputs/EAF-089-2025/capitulo_01/layout_WITH_PATCH.json
```

---

**Última actualización**: 2025-11-23
