# Resumen de la Metodología - Docling + EAF Patch

**Última actualización**: Noviembre 1, 2025

---

## 📋 ¿Qué contiene METHODOLOGY/?

La carpeta `METHODOLOGY/` contiene **documentación completa** sobre cómo procesar PDFs usando **Docling Granite-258M** + **EAF Monkey Patch** para detectar contenido faltante.

---

## 📚 Archivos Principales

### 1. Guías de Inicio
| Archivo | Descripción | Cuándo Leerlo |
|---------|-------------|---------------|
| **README.md** | Índice general de toda la documentación | Primero - vista general |
| **README_METHODOLOGY.md** | Navegación detallada entre documentos | Primero - encontrar lo que necesitas |
| **QUICK_START_GUIDE.md** | Referencia rápida (1 página) | Cuando ya conoces Docling |

### 2. Fundamentos de Docling
| Archivo | Descripción | Importancia |
|---------|-------------|-------------|
| **DOCLING_DESIGN_PHILOSOPHY.md** | ⭐ **MUST READ**: Filosofía de diseño de Docling | **CRÍTICO** - Entender cómo funciona |
| **UNIVERSAL_DOCLING_METHODOLOGY.md** | Guía completa (400+ líneas) | Principal - cubre todo |

### 3. Configuración y Optimización
| Archivo | Descripción |
|---------|-------------|
| **COMPLETE_DOCLING_CONFIG_OPTIONS.md** | TODOS los parámetros de configuración explicados |
| **DOCLING_CONFIG_QUICK_REFERENCE.md** | Referencia rápida de configuración |
| **DOCLING_CONFIGURATION_COMPLETE_GUIDE.md** | Guía completa de configuración |
| **OPTIMIZED_SAFE_BENCHMARKS.md** | Benchmarks de rendimiento (41x speedup) |

### 4. EAF Patch (Monkey Patch)
| Archivo | Descripción |
|---------|-------------|
| **EAF_PATCH_ARCHITECTURE.md** | ⭐ Arquitectura completa del monkey patch |

### 5. Técnicas Avanzadas
| Archivo | Descripción |
|---------|-------------|
| **INTELLIGENT_HIERARCHY_STRATEGIES.md** | Construcción de jerarquía semántica |
| **CHAPTER_3_4_BOUNDARY_FIX.md** | Fix para límites de capítulos |

### 6. Bugs Críticos
| Archivo | Descripción | Importancia |
|---------|-------------|-------------|
| **CRITICAL_PAGE_INDEXING_BUG.md** | ⚠️ **CRÍTICO**: Docling usa índices 1-based, PyMuPDF usa 0-based | **MUST READ** |

---

## 🎯 ¿Qué Aprenderás?

### 1. Tipos de Elementos de Docling (11 tipos)
```
📝 Texto y Estructura:
  - text              → Párrafos normales
  - section_header    → Encabezados de sección
  - title             → Títulos de documentos
  - list_item         → Items de lista

📊 Elementos Especiales:
  - table             → Tablas (97.9% precisión)
  - picture           → Imágenes/diagramas
  - caption           → Pies de figura/tabla
  - formula           → Ecuaciones/fórmulas

📄 Metadatos:
  - footnote          → Notas al pie
  - page_header       → Encabezados de página
  - page_footer       → Pies de página
```

### 2. EAF Monkey Patch - Arquitectura

El monkey patch detecta **automáticamente** contenido que Docling no detectó:

```
┌─────────────────────────────────────────────────────────┐
│ FASE 1: DOCLING EXTRACTION                             │
│ - Docling procesa PDF con AI (Granite-258M)            │
│ - Genera clusters (cajas con clasificación)            │
│ - Retorna: docling_clusters                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 2: MONKEY PATCH INTERCEPTION                      │
│ (se ejecuta DURANTE la extracción de Docling)          │
│                                                         │
│ STEP 1: Extraer TODO el texto con PyMuPDF              │
│ STEP 2: Comparar con boxes de Docling                  │
│ STEP 3: Detectar texto FUERA de clusters:              │
│         ✓ Títulos faltantes (ej: "6. ")                │
│         ✓ Nombres de empresas                          │
│         ✓ Líneas de transmisión                        │
│ STEP 4: Crear clusters sintéticos                      │
│ STEP 5: Fix de list-items aislados                     │
│         (con detección cross-page)                     │
│ STEP 6: Inyectar clusters al final                     │
│         final_clusters = docling + patch               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 3: POST-PROCESSING                                │
│ - Zona fix: Clasificación de "Zona X - Área Y"         │
│ - (Isolated list fix ahora en monkey patch)            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 4: EXPORT                                          │
│ - JSON con bounding boxes                              │
│ - PDF anotado con cajas de colores                     │
│ - Markdown export                                       │
└─────────────────────────────────────────────────────────┘
```

### 3. Detección Automática de Títulos Principales

**Patrón**: `^\d+\.\s+` (Ej: "6. Normalización del servicio")

**Lógica**:
```python
# 1. PyMuPDF extrae líneas del PDF
for line in pdf_lines:
    # 2. Detector verifica si es título
    if is_title_pattern(line.text):
        # 3. Verifica posición
        if line.x0 < 150 and line.width < 500:
            # 4. Para títulos principales, NO verifica duplicados
            if re.match(r'^\d+\.\s+', line.text):
                # ✅ SIEMPRE AGREGAR (bypass duplicate check)
                create_cluster(line)
```

**Características**:
- ✅ Detección automática (no manual)
- ✅ Títulos principales (`^\d+\.`) siempre se agregan
- ✅ No verifica duplicados para títulos de capítulo
- ✅ Funciona cross-page

### 4. Detección Cross-Page de Listas

**Problema**: Listas secuenciales que cruzan páginas se detectaban como "aisladas".

**Solución**:
```python
# Variable global para último cluster de página anterior
_LAST_PAGE_LAST_CLUSTER = None

# Al procesar cada página:
if first_list_item AND previous_page_ended_with_list:
    # ✅ Conexión cross-page detectada
    mark_as_sequential(first_list_item)
else:
    # Solo tiene vecinos en misma página
    check_neighbors_in_current_page()
```

**Resultado**:
- ✅ Listas que cruzan páginas se preservan
- ✅ Items aislados se convierten a `section_header`

---

## 🔧 Configuración para GPUs de 4GB (GTX 1650)

```python
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False                    # -1.5 GB VRAM
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.mode = TableFormerMode.FAST  # -400 MB

# VRAM total: ~1.3 GB (cabe en 4GB GPU)
```

**Modos disponibles**:
- **Lightweight** (1.3 GB): Sin OCR, tablas FAST
- **Balanced** (2.0 GB): OCR solo inglés, tablas FAST
- **Accurate** (4.2 GB): OCR completo, tablas ACCURATE (requiere 6GB+)

---

## 🎨 Colores Estándar para PDFs Anotados

```python
colors = {
    'text':           (0, 0, 1),      # 🔵 Azul
    'section_header': (1, 0, 0),      # 🔴 Rojo
    'title':          (1, 0.5, 0),    # 🟠 Naranja
    'list_item':      (0, 1, 1),      # 🔵🟢 Cyan
    'table':          (0, 1, 0),      # 🟢 Verde
    'picture':        (1, 0, 1),      # 🟣 Magenta
    'caption':        (1, 0.5, 0),    # 🟠 Naranja
    'formula':        (0.5, 0, 0.5),  # 🟣 Púrpura
}
```

---

## 📊 Resultados Verificados

| Capítulo | Páginas | Elementos | Títulos Principales | Estado |
|----------|---------|-----------|---------------------|--------|
| Cap. 1   | 11      | 49        | ✅ "1. ..."         | Completo |
| Cap. 6   | 94      | 452       | ✅ "6. Normalización..." | **Necesita re-extracción** |
| Cap. 7   | 82      | 349       | ✅ "7. Análisis..." | Completo |

**Nota Cap. 6**: El monkey patch detecta el título automáticamente, pero la extracción del 31 Oct no lo incluyó. Requiere re-extracción con código actualizado.

---

## 🚀 Uso Rápido

### ⭐ Script Universal (Recomendado):
```bash
cd shared_platform/utils/outputs/docling_layout

# Extraer cualquier capítulo (solo cambia el número)
/path/to/venv/bin/python3 EXTRACT_ANY_CHAPTER.py 6   # Capítulo 6
/path/to/venv/bin/python3 EXTRACT_ANY_CHAPTER.py 7   # Capítulo 7
/path/to/venv/bin/python3 EXTRACT_ANY_CHAPTER.py 1   # Capítulo 1

# Con rango de páginas personalizado
/path/to/venv/bin/python3 EXTRACT_ANY_CHAPTER.py 6 --pages 172-265

# Genera automáticamente:
#   - JSON: capitulo_XX/outputs/layout_WITH_PATCH.json
#   - PDF anotado: capitulo_XX/outputs/chapterXX_WITH_PATCH_annotated.pdf
```

**✅ Características del script universal:**
- Funciona para TODOS los capítulos (1-11)
- Solo cambia el número de capítulo
- Aplica monkey patch automáticamente
- Genera JSON + PDF anotado
- Muestra estadísticas de elementos
- Configura GPU automáticamente (modo lightweight)

### Procesar todos los capítulos en batch:
```bash
# Procesar todos de una vez
for i in {1..11}; do
  /path/to/venv/bin/python3 EXTRACT_ANY_CHAPTER.py $i
done
```

---

## ⚠️ Errores Comunes

### 1. "ModuleNotFoundError: No module named 'docling'"
**Causa**: Usando Python del sistema en vez del virtualenv.

**Solución**:
```bash
# ❌ Incorrecto
python3 script.py

# ✅ Correcto
/home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/venv/bin/python3 script.py
```

### 2. Título principal no detectado
**Causa**: El monkey patch no está funcionando o versión antigua del código.

**Solución**:
1. Verificar que `eaf_patch_engine.py` tiene la lógica `is_main_chapter_title`
2. Re-extraer el capítulo con código actualizado
3. El título debería aparecer automáticamente

### 3. CUDA out of memory (4GB GPU)
**Causa**: Intentando modo ACCURATE o múltiples instancias.

**Solución**:
```python
# Usar modo lightweight
pipeline_options.do_ocr = False
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
```

### 4. Page indexing mismatch
**Causa**: Docling usa páginas 1-indexed, PyMuPDF usa 0-indexed.

**Solución**:
```python
# Al leer con PyMuPDF
page = doc[page_num - 1]  # Restar 1

# Al guardar en JSON
element['page'] = docling_page_num  # Mantener 1-indexed
```

---

## 📝 Estado del Proyecto

### ✅ Completado:
- [x] Monkey patch con detección automática de títulos
- [x] Detección cross-page de listas secuenciales
- [x] Post-processor para Zona classification
- [x] Documentación completa de metodología
- [x] PDFs anotados para Cap. 1, 7
- [x] Configuración optimizada para 4GB GPU

### 🔄 Pendiente:
- [ ] Re-extraer Capítulo 6 con monkey patch actualizado
- [ ] Generar PDFs anotados para todos los capítulos
- [ ] Validar títulos principales en todos los capítulos
- [ ] Agregar más post-processors según necesidad

---

## 🔗 Archivos Relacionados

```
📄 EXTRACT_ANY_CHAPTER.py            ⭐⭐⭐ SCRIPT UNIVERSAL
                                      Extrae cualquier capítulo (1-11)
                                      Solo cambia el número!

eaf_patch/
├── core/
│   ├── eaf_patch_engine.py          ⭐ Motor principal del monkey patch
│   ├── eaf_title_detector.py        ⭐ Detector de títulos faltantes
│   ├── company_name_detector.py     ⭐ Detector de nombres de empresas
│   ├── power_line_classifier.py     ⭐ Clasificador de líneas eléctricas
│   └── post_processors/
│       ├── zona_fix.py              ⭐ Post-processor para Zona items
│       └── __init__.py
│
└── scripts/                          Scripts auxiliares de prueba

METHODOLOGY/                          📚 Esta carpeta
├── README.md                         Índice general
├── RESUMEN_METODOLOGIA.md           ⭐ Este archivo
├── EAF_PATCH_ARCHITECTURE.md        Arquitectura del patch
└── ... (otros 10 archivos)

capitulo_XX/outputs/                  Outputs por capítulo
├── layout_WITH_PATCH.json           JSON con elementos + bboxes
└── chapterXX_WITH_PATCH_annotated.pdf  PDF con cajas de colores
```

---

## 📞 Preguntas Frecuentes

### ¿El monkey patch es automático?
**SÍ**. Una vez que llamas `apply_universal_patch_with_pdf()`, todo se ejecuta automáticamente durante la extracción de Docling.

### ¿Necesito agregar títulos manualmente?
**NO**. El monkey patch detecta automáticamente títulos que faltan usando PyMuPDF + patrones regex.

### ¿Qué pasa si Docling ya detectó el título?
El monkey patch verifica overlap (IOU > 0.5). Si hay overlap alto:
- Para títulos NO-principales: Skip (evita duplicados)
- Para títulos principales (`^\d+\.`): **Siempre agrega** (bypass duplicate check)

### ¿Cómo funciona la detección cross-page?
Variable global `_LAST_PAGE_LAST_CLUSTER` guarda el último cluster de cada página. Al procesar la siguiente página, verifica si el primer item conecta con el último de la anterior.

### ¿Puedo agregar más post-processors?
**SÍ**. La carpeta `post_processors/` está lista para expansión:
```python
# Ejemplo: agregar nuevo post-processor
from core.post_processors import apply_zona_fix_to_document, apply_my_fix

doc = result.document
apply_zona_fix_to_document(doc)
apply_my_fix(doc)  # Tu nuevo post-processor
```

---

**Fin del Resumen**

Para documentación completa, consulta los archivos individuales en `METHODOLOGY/`.
