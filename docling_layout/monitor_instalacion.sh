#!/bin/bash

# Monitor de Instalación de Docling
# ==================================

echo "=========================================="
echo "📊 MONITOR INSTALACIÓN DOCLING"
echo "=========================================="
echo ""

# Verificar si el proceso pip está corriendo
PIP_PID=$(ps aux | grep "pip install docling" | grep -v grep | awk '{print $2}' | head -1)

if [ -z "$PIP_PID" ]; then
    echo "❌ No hay instalación de pip corriendo"
    echo ""
    echo "Verificando si Docling ya está instalado..."
    cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN
    source venv/bin/activate
    python3 -c "from docling.document_converter import DocumentConverter; print('✅ Docling YA ESTÁ instalado!')" 2>/dev/null && exit 0
    echo "❌ Docling NO está instalado"
    echo ""
    echo "Para iniciar instalación:"
    echo "  cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN"
    echo "  source venv/bin/activate"
    echo "  nohup pip install docling > /tmp/docling_install_full.log 2>&1 &"
    exit 1
fi

echo "✅ Proceso pip activo (PID: $PIP_PID)"
echo ""

# Mostrar tiempo de ejecución
ELAPSED=$(ps -p $PIP_PID -o etime= | tr -d ' ')
echo "⏱️  Tiempo transcurrido: $ELAPSED"
echo ""

# Tamaño del log
LOG_SIZE=$(wc -c /tmp/docling_install_full.log 2>/dev/null | awk '{print $1}')
if [ ! -z "$LOG_SIZE" ]; then
    LOG_SIZE_KB=$((LOG_SIZE / 1024))
    echo "📝 Tamaño log: ${LOG_SIZE_KB} KB"
fi
echo ""

# Últimas 10 líneas del log
echo "📄 Últimas 10 líneas del log:"
echo "----------------------------------------"
tail -10 /tmp/docling_install_full.log 2>/dev/null || echo "No hay log disponible"
echo "----------------------------------------"
echo ""

# Verificar si PyTorch se está descargando
if grep -q "Downloading torch" /tmp/docling_install_full.log 2>/dev/null; then
    echo "⚠️  PyTorch (887.9 MB) se está descargando..."
    echo "   Esto puede tomar 10-20 minutos dependiendo de tu conexión"
    echo ""
fi

# Verificar si hay error
if grep -qi "error" /tmp/docling_install_full.log 2>/dev/null; then
    echo "⚠️  Se detectaron errores en el log"
    echo ""
fi

echo "=========================================="
echo "Para ver el log completo:"
echo "  cat /tmp/docling_install_full.log"
echo ""
echo "Para ver actualizaciones en tiempo real:"
echo "  tail -f /tmp/docling_install_full.log"
echo "=========================================="
