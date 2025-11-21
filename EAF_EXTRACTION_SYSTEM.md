# Docling EAF Extraction System

Sistema de extracción de documentos PDF de Estudios de Análisis de Fallas (EAF) usando **Docling** con modificaciones especializadas.

---

## 🔄 Arquitectura del Sistema

El sistema de extracción funciona en **DOS ETAPAS** separadas e independientes:

```
┌─────────────────────────────────────────────────────────────┐
│                    📄 PDF INPUT                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 1: MONKEY PATCH (Durante Extracción)                 │
│  ⚙️  Modificaciones runtime del pipeline de Docling         │
│                                                              │
│  📁 Ubicación: eaf_patch/                                   │
│  📖 Documentación: eaf_patch/docs/                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Docling Document Object                         │
│              (con clasificaciones mejoradas)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 2: POST-PROCESSORS (Después de Extracción)           │
│  🔧 Transformaciones a nivel de documento completo          │
│                                                              │
│  📁 Ubicación: post_processors/                             │
│  📖 Documentación: post_processors/docs/                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  📊 JSON OUTPUT                              │
│              (estructura final optimizada)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📖 Documentación Detallada

### 1️⃣ Monkey Patch System (Durante Extracción)

**¿Qué hace?** Modifica el comportamiento de Docling en runtime para mejorar la clasificación de elementos durante la extracción.

**Ubicación:** `eaf_patch/`

**Documentación:**
- 📘 [¿Por qué Monkey Patch?](eaf_patch/docs/WHY_MONKEY_PATCH.md)
- 📘 [Flujo de Monkey Patch](eaf_patch/docs/MONKEY_PATCH_FLOW_DIAGRAM.md)
- 📘 [Catálogo de Patches](eaf_patch/docs/EAF_PATCH_CATALOG.md)
- 📘 [Detección de Nombres de Entidades](eaf_patch/docs/ENTITY_NAME_DETECTION_LOGIC.md)
- 📘 [README del EAF Patch](eaf_patch/docs/EAF_PATCH_README.md)

**Archivos principales:**
```
eaf_patch/core/
├── eaf_patch_engine.py          # Motor principal del monkey patch
├── eaf_page_detector.py          # Detección de páginas especiales
├── eaf_title_detector.py         # Detección de títulos
├── eaf_company_name_detector.py  # Detección de nombres de empresas
└── monkey_patch/                 # Utilidades de monkey patching
```

---

### 2️⃣ Post-Processors (Después de Extracción)

**¿Qué hace?** Aplica transformaciones y correcciones al documento completo después de que Docling termina la extracción.

**Ubicación:** `post_processors/`

**Documentación:**
- 📗 [Catálogo de Post-Processors](post_processors/docs/POST_PROCESSOR_CATALOG.md)
- 📗 [Smart Reclassification (Detallado)](post_processors/docs/SMART_RECLASSIFICATION_POST_PROCESSOR.md)

**Post-processors disponibles:**

| # | Nombre | Archivo | Propósito |
|---|--------|---------|-----------|
| 1 | **Zona Fix** | `zona_fix.py` | Reclasifica patrones "Zona X - Área Y" |
| 2 | **Smart Reclassification** | `enumerated_item_fix.py` | 8 reglas inteligentes de reclasificación |
| 3 | **Metadata Date Extractor** | `metadata_date_extractor.py` | Extrae fechas del documento al metadata |
| 4 | **Isolated List Fix** | `isolated_list_fix.py` | ⚠️ Deprecado (reemplazado por Smart Part 6) |

**Archivos:**
```
post_processors/core/
├── __init__.py
├── zona_fix.py
├── enumerated_item_fix.py
├── metadata_date_extractor.py
└── isolated_list_fix.py
```

---

## 🚀 Uso del Sistema

### Extracción de un Capítulo

```bash
# Ejecutar desde el directorio raíz
python EXTRACT_ANY_CHAPTER.py <número_de_capítulo>

# Ejemplo: Extraer capítulo 1
python EXTRACT_ANY_CHAPTER.py 1
```

### Flujo de Ejecución en el Código

```python
from docling.document_converter import DocumentConverter
from eaf_patch.core.eaf_patch_engine import apply_eaf_patch
from post_processors.core import (
    apply_zona_fix_to_document,
    apply_enumerated_item_fix_to_document,
    apply_date_extraction_to_document
)

# 1. Aplicar monkey patch
apply_eaf_patch()

# 2. Extraer con Docling (el monkey patch actúa automáticamente)
converter = DocumentConverter()
result = converter.convert(pdf_path)
doc = result.document

# 3. Aplicar post-processors
zona_count = apply_zona_fix_to_document(doc)
enum_count = apply_enumerated_item_fix_to_document(doc)
date_metadata = apply_date_extraction_to_document(doc)

# 4. Exportar a JSON
doc_dict = doc.export_to_dict()

# 5. Agregar metadata de fechas
if 'origin' not in doc_dict:
    doc_dict['origin'] = {}
doc_dict['origin']['fecha_emision'] = date_metadata.get('fecha_emision')
doc_dict['origin']['fecha_falla'] = date_metadata.get('fecha_falla')
doc_dict['origin']['hora_falla'] = date_metadata.get('hora_falla')

# 6. Guardar JSON
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(doc_dict, f, indent=2, ensure_ascii=False)
```

---

## 📊 Estructura de Directorios

```
dark-data-docling-extractors/
│
├── EAF_EXTRACTION_SYSTEM.md      ← Este documento
├── EXTRACT_ANY_CHAPTER.py        ← Script principal de extracción
│
├── eaf_patch/                    ← ETAPA 1: Monkey Patch
│   ├── core/
│   │   ├── eaf_patch_engine.py
│   │   ├── eaf_page_detector.py
│   │   ├── eaf_title_detector.py
│   │   ├── eaf_company_name_detector.py
│   │   └── monkey_patch/
│   │
│   ├── docs/                     ← Documentación del Monkey Patch
│   │   ├── WHY_MONKEY_PATCH.md
│   │   ├── MONKEY_PATCH_FLOW_DIAGRAM.md
│   │   ├── EAF_PATCH_CATALOG.md
│   │   ├── ENTITY_NAME_DETECTION_LOGIC.md
│   │   ├── EAF_PATCH_README.md
│   │   └── QUICK_REFERENCE.md
│   │
│   └── scripts/                  ← Scripts de prueba
│
├── post_processors/              ← ETAPA 2: Post-Processors
│   ├── core/
│   │   ├── __init__.py
│   │   ├── zona_fix.py
│   │   ├── enumerated_item_fix.py
│   │   ├── metadata_date_extractor.py
│   │   └── isolated_list_fix.py
│   │
│   └── docs/                     ← Documentación de Post-Processors
│       ├── POST_PROCESSOR_CATALOG.md
│       └── SMART_RECLASSIFICATION_POST_PROCESSOR.md
│
└── capitulo_XX/                  ← Salidas organizadas por capítulo
    ├── outputs/
    │   └── layout_WITH_PATCH.json
    └── scripts/
```

---

## 🎯 Diferencias Clave Entre las Dos Etapas

| Aspecto | ETAPA 1: Monkey Patch | ETAPA 2: Post-Processors |
|---------|----------------------|--------------------------|
| **Cuándo se ejecuta** | Durante la extracción de Docling | Después de que Docling termina |
| **Acceso a datos** | Nivel de página, clusters sin texto | Documento completo, texto disponible |
| **Tipo de modificación** | Modifica el código de Docling en runtime | Transforma el documento ya extraído |
| **Alcance** | Clustering y clasificación inicial | Reclasificación y enriquecimiento |
| **Ejemplos** | Detectar títulos por posición, detección de nombres de empresas | Reclasificar listas aisladas, extraer metadata |

---

## 📝 Notas Importantes

1. **Orden de Ejecución:** El monkey patch DEBE aplicarse ANTES de crear el `DocumentConverter`
2. **Imports:** Los imports ahora apuntan a `post_processors.core` en lugar de `eaf_patch.core.post_processors`
3. **Independencia:** Las dos etapas son independientes - puedes usar una sin la otra
4. **Documentación:** Cada etapa tiene su propia carpeta de documentación para mayor claridad

---

## 🔗 Enlaces Rápidos

- [Referencia Rápida](eaf_patch/docs/QUICK_REFERENCE.md) - Comandos y patrones comunes
- [Catálogo de Monkey Patches](eaf_patch/docs/EAF_PATCH_CATALOG.md) - Lista completa de patches
- [Catálogo de Post-Processors](post_processors/docs/POST_PROCESSOR_CATALOG.md) - Lista completa de post-processors
- [Smart Reclassification](post_processors/docs/SMART_RECLASSIFICATION_POST_PROCESSOR.md) - Documentación detallada del post-processor más complejo

---

**Última actualización:** 2025-11-17
