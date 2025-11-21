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

python3 EXTRACT_ANY_CHAPTER.py 1    # Capítulo 1
python3 EXTRACT_ANY_CHAPTER.py 6    # Capítulo 6
```

### Extraer Todos los Capítulos

```bash
for i in {1..11}; do
  python3 EXTRACT_ANY_CHAPTER.py $i
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

El sistema procesa en 4 etapas:

```
PDF → [1. Docling + Monkey Patch] → [2. Smart Reclassification] → [3. Hierarchy] → [4. Metadata] → JSON
```

### 1. Docling + EAF Monkey Patch

Intercepta el pipeline de Docling y aplica:
- Detección de títulos completos desde PyMuPDF
- Detección de nombres de empresas (S.A., Ltda.)
- Clasificación de líneas de poder (kV)
- Continuidad de listas cross-page

### 2. Smart Reclassification (9 partes)

Reclasifica elementos mal detectados:
- Secuencias de bullets
- Patrones enumerados (a, b, c)
- Títulos de zona/área
- Captions de tablas

### 3. Hierarchy Restructure

Construye jerarquía padre-hijo usando patrones:
- `1.`, `2.` → Nivel 1
- `1.1`, `2.3` → Nivel 2
- `a)`, `b)` → Nivel 3
- `a.`, `b.` → Nivel 4

Popula arrays `children[]` con referencias `$ref`.

### 4. Metadata Date Extractor

Extrae fechas a metadata:
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

### Opción A: Mismo Formato (Informe EAF)

1. **Dividir PDF** en capítulos (usar herramienta externa)

2. **Colocar archivos** en:
   ```
   /ruta/base/capitulo_XX/nombre_capitulo_XX_pages_N-M.pdf
   ```

3. **Actualizar** `EXTRACT_ANY_CHAPTER.py`:
   ```python
   # Línea 27-39: Actualizar CHAPTER_RANGES
   CHAPTER_RANGES = {
       1: (1, 15),
       2: (16, 100),
       # ...
   }

   # Línea 72-73: Actualizar ruta base
   base_pdf = Path("/ruta/a/tus/pdfs")
   pdf_path = base_pdf / f"capitulo_{chapter_num:02d}" / f"NUEVO_INFORME_capitulo_{chapter_num:02d}_pages_{start}-{end}.pdf"
   ```

4. **Extraer**:
   ```bash
   for i in {1..N}; do python3 EXTRACT_ANY_CHAPTER.py $i; done
   ```

### Opción B: PDF Único

1. **Modificar** `EXTRACT_ANY_CHAPTER.py`:
   ```python
   # Cambiar líneas 72-73
   pdf_path = Path("/ruta/completa/tu_archivo.pdf")
   ```

2. **Ejecutar** con rango:
   ```bash
   python3 EXTRACT_ANY_CHAPTER.py 1 --pages 1-100
   ```

### Opción C: Script Genérico (Recomendado para Nuevo Desarrollo)

Crear script que acepte cualquier PDF:
```bash
python3 extract_generic.py /ruta/al/archivo.pdf --output ./outputs/
```

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
docling_layout/
├── EXTRACT_ANY_CHAPTER.py          # Script principal de extracción
├── README.md                       # Este archivo
├── DOCLING_COMPLETE_GUIDE.md       # Guía técnica detallada
│
├── eaf_patch/                      # Monkey patch (durante extracción)
│   ├── core/
│   │   ├── eaf_patch_engine.py     # Motor principal
│   │   ├── eaf_title_detector.py   # Detector de títulos
│   │   └── eaf_company_name_detector.py
│   ├── domain/
│   │   └── power_line_classifier.py
│   └── docs/                       # Documentación del patch
│
├── post_processors/                # Post-procesadores (después de extracción)
│   ├── core/
│   │   ├── enumerated_item_fix.py  # Smart Reclassification (9 partes)
│   │   ├── hierarchy_restructure.py # Estructura jerárquica
│   │   └── metadata_date_extractor.py
│   └── docs/
│       └── POST_PROCESSOR_CATALOG.md
│
└── capitulo_01/ ... capitulo_11/   # Salidas por capítulo
    └── outputs/
        ├── layout_WITH_PATCH.json
        └── chapterXX_WITH_PATCH_annotated.pdf
```

---

## Documentación Adicional

- **Post-Processors**: `post_processors/docs/POST_PROCESSOR_CATALOG.md`
- **Monkey Patch**: `eaf_patch/docs/EAF_PATCH_README.md`
- **Guía Técnica**: `DOCLING_COMPLETE_GUIDE.md`

---

## Verificación de Resultados

```bash
# Verificar JSON generado
jq '.texts | length' capitulo_01/outputs/layout_WITH_PATCH.json
jq '.tables | length' capitulo_01/outputs/layout_WITH_PATCH.json

# Ver jerarquía
jq '.texts[] | select(.children | length > 0) | {text: .text[0:50], children: (.children | length)}' capitulo_01/outputs/layout_WITH_PATCH.json
```

---

**Última actualización**: 2025-11-20
