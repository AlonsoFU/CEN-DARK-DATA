# Setup - Docling Layout Analysis

Guía rápida de instalación y primeros pasos.

---

## 📦 Instalación

### **1. Instalar Docling**

```bash
pip install docling
```

**Verificar instalación:**
```bash
python -c "from docling.document_converter import DocumentConverter; print('✅ Docling instalado')"
```

### **2. Requisitos del Sistema**

- **Python**: 3.9+ (tu proyecto ya cumple ✅)
- **RAM**: 512MB mínimo, 2GB recomendado
- **CPU**: Cualquier CPU moderna (no requiere GPU)
- **Disco**: ~800MB para modelos

---

## 🚀 Quick Start

### **Test Rápido (1 minuto)**

```bash
cd capitulo_01/scripts/
python test_quick.py
```

**Output esperado:**
```
============================================================
🧪 TEST RÁPIDO - DOCLING LAYOUT
============================================================

1️⃣ Verificando instalación de Docling...
   ✅ Docling instalado correctamente

2️⃣ Verificando PDF fuente...
   ✅ PDF encontrado: EAF-089-2025.pdf

3️⃣ Testeando conversión (solo página 1)...
   ⏳ Esto puede tomar 20-30s la primera vez (carga modelos)...
   ✅ Conversión exitosa!
   📊 Elementos detectados en página 1: 15

4️⃣ Muestra de elementos detectados:
------------------------------------------------------------
   1. [title] Informe de Fallas EAF-089-2025...
   2. [section-header] a. Descripción de la instalación...
   3. [text] El día 15 de enero de 2025 a las...
   4. [table] Nombre | MW | Estado...
   5. [text] La perturbación afectó a...
------------------------------------------------------------

============================================================
✅ TEST COMPLETADO EXITOSAMENTE
============================================================

💡 Siguiente paso:
   python docling_layout_extractor.py
```

---

### **Comparación con PyMuPDF (2 minutos)**

```bash
python compare_pymupdf_vs_docling.py
```

Compara ambos métodos en 3 páginas de prueba.

---

### **Extracción Completa Capítulo 1 (3-5 minutos)**

```bash
python docling_layout_extractor.py
```

**Archivos generados:**
```
../outputs/
├── layout.json          # Estructura + bboxes
├── document.md          # Markdown con contenido
├── document.html        # HTML formateado
├── annotated.pdf        # PDF con boxes visualizados
└── stats.json           # Estadísticas
```

---

## 🔧 Troubleshooting

### **Error: ModuleNotFoundError: No module named 'docling'**

```bash
pip install docling
```

### **Error: No se encuentra PDF**

Verifica que el PDF existe:
```bash
ls -la ../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf
```

Si la ruta es diferente, edita en el script:
```python
pdf_path = Path("TU_RUTA_AQUI/EAF-089-2025.pdf")
```

### **Proceso muy lento la primera vez**

**Normal:** Primera ejecución descarga modelos (~800MB) y los carga en memoria.
- Primera vez: ~30-60 segundos
- Siguientes: ~2-3 segundos/página

### **MemoryError**

Si fallas por memoria:
1. Procesar menos páginas por vez
2. Cerrar otras aplicaciones
3. Mínimo 2GB RAM recomendado

---

## 📁 Estructura de Archivos

```
docling_layout/
├── README.md              # Documentación principal
├── SETUP.md              # Esta guía
├── capitulo_01/
│   ├── scripts/
│   │   ├── docling_layout_extractor.py    # ← Script principal
│   │   ├── test_quick.py                  # ← Test rápido
│   │   └── compare_pymupdf_vs_docling.py  # ← Comparación
│   ├── outputs/                           # ← Resultados aquí
│   │   ├── layout.json
│   │   ├── document.md
│   │   ├── document.html
│   │   ├── annotated.pdf
│   │   └── stats.json
│   └── visualizations/                    # Imágenes extras
└── capitulo_02/...                        # Otros capítulos
```

---

## 💡 Siguientes Pasos

Después del test exitoso:

1. **Revisar outputs**
   ```bash
   cd capitulo_01/outputs/
   ls -lah
   ```

2. **Ver JSON con bboxes**
   ```bash
   cat layout.json | head -100
   ```

3. **Ver Markdown**
   ```bash
   cat document.md | less
   ```

4. **Abrir PDF anotado**
   ```bash
   xdg-open annotated.pdf  # Linux
   open annotated.pdf      # macOS
   ```

5. **Procesar más capítulos**
   - Copiar estructura `capitulo_01/` a `capitulo_02/`
   - Editar páginas en el script
   - Ejecutar

---

## 🎯 Scripts Disponibles

| Script | Propósito | Tiempo | Output |
|--------|-----------|--------|--------|
| `test_quick.py` | Test página 1 | ~30s | Consola |
| `compare_pymupdf_vs_docling.py` | Comparar métodos | ~1-2min | JSON + consola |
| `docling_layout_extractor.py` | Extracción completa | ~3-5min | 5 archivos |

---

## 📞 Soporte

**Documentación oficial:**
- Docling GitHub: https://github.com/docling-project/docling
- Docling Docs: https://docling-project.github.io/docling/

**Problemas comunes:**
- Ver README.md sección "Troubleshooting"
- Issues GitHub: https://github.com/docling-project/docling/issues

---

**¡Listo para empezar!** 🚀

Ejecuta primero `test_quick.py` para verificar que todo funciona.
