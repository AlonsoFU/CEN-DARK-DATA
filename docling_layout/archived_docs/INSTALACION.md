# Instalación de Docling

## ⚠️ Instalación Manual Requerida

La instalación automática ha fallado debido al tamaño de PyTorch (887.9 MB). Por favor, sigue estos pasos **manualmente**:

---

## 📦 Pasos de Instalación

### **Opción 1: Instalación Estándar (Recomendada)**

```bash
# 1. Activar virtual environment
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
source venv/bin/activate

# 2. Instalar Docling (puede tomar 10-15 minutos)
pip install docling

# Espera a que termine la descarga de PyTorch (887.9 MB)
# La salida mostrará: "Downloading torch-2.8.0-cp312-cp312-manylinux_2_28_x86_64.whl (887.9 MB)"
```

**Tiempo estimado**: 10-15 minutos dependiendo de tu conexión a internet.

---

### **Opción 2: Instalación en Background (Si quieres seguir trabajando)**

```bash
# 1. Activar virtual environment
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
source venv/bin/activate

# 2. Instalar en background con log
nohup pip install docling > /tmp/docling_install.log 2>&1 &

# 3. Monitorear progreso
tail -f /tmp/docling_install.log

# 4. Verificar cuando termine
python3 -c "from docling.document_converter import DocumentConverter; print('✅ Instalado')"
```

---

### **Opción 3: Instalación Sin PyTorch (Más Rápida, Solo CPU)**

Si solo necesitas probar rápido y no te importa el rendimiento:

```bash
# Instalar solo las dependencias básicas (sin PyTorch)
pip install docling --no-deps
pip install pydantic pypdfium2 pydantic-settings requests certifi beautifulsoup4 pillow
```

⚠️ **Limitación**: Esta opción puede fallar si Docling requiere PyTorch obligatoriamente.

---

## 🧪 Verificar Instalación

Una vez que la instalación complete:

```bash
# Activar venv
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
source venv/bin/activate

# Verificar
python3 -c "from docling.document_converter import DocumentConverter; print('✅ Docling instalado correctamente')"
```

**Output esperado**:
```
✅ Docling instalado correctamente
```

---

## 🚀 Ejecutar Scripts

Una vez instalado Docling, ejecuta los scripts:

### **1. Test Rápido (RECOMENDADO PRIMERO)**

```bash
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/
python3 test_quick.py
```

**Tiempo**: ~30-60 segundos primera vez (carga modelos AI), luego 2-3s

---

### **2. Comparación con PyMuPDF**

```bash
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/
python3 compare_pymupdf_vs_docling.py
```

**Tiempo**: ~1-2 minutos

---

### **3. Extracción Completa Capítulo 1**

```bash
cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/
python3 docling_layout_extractor.py
```

**Tiempo**: ~3-5 minutos (11 páginas)

**Outputs generados**:
```
capitulo_01/outputs/
├── layout.json          # 📊 Estructura + bounding boxes
├── document.md          # 📝 Markdown
├── document.html        # 🌐 HTML
├── annotated.pdf        # 🎨 PDF con boxes visualizados
└── stats.json           # 📈 Estadísticas
```

---

## ❓ Troubleshooting

### **Error: "ModuleNotFoundError: No module named 'docling'"**

```bash
# Verificar que estás en el venv
which python3
# Debería mostrar: /home/alonso/Documentos/Github/Proyecto Dark Data CEN/venv/bin/python3

# Si no estás en venv:
source venv/bin/activate
```

---

### **Instalación muy lenta**

**Normal**: PyTorch es 887.9 MB. Con conexión de 10 Mbps toma ~12 minutos.

```bash
# Monitorear progreso
tail -f /tmp/docling_install.log

# Si se atascó, matar e intentar de nuevo
pkill -f "pip install docling"
pip install docling
```

---

### **Error: "externally-managed-environment"**

Asegúrate de estar en el virtual environment:

```bash
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
source venv/bin/activate
pip install docling
```

---

## 📞 Soporte

- **Documentación Docling**: https://docling-project.github.io/docling/
- **GitHub Issues**: https://github.com/docling-project/docling/issues
- **README Principal**: `shared_platform/utils/outputs/docling_layout/README.md`
- **Setup Rápido**: `shared_platform/utils/outputs/docling_layout/SETUP.md`

---

**Estado**: ⏳ Esperando instalación manual de Docling

**Siguiente paso**: Ejecutar `test_quick.py` después de instalar
