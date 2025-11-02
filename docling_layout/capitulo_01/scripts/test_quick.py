#!/usr/bin/env python3
"""
Quick Test - Docling Layout Extractor
======================================

Prueba rápida de Docling en 1 página para verificar instalación.
"""

from pathlib import Path
import sys

# Agregar proyecto al path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_docling_quick():
    """Test rápido de Docling en página 1."""

    print("="*60)
    print("🧪 TEST RÁPIDO - DOCLING LAYOUT")
    print("="*60)
    print()

    # Verificar instalación
    print("1️⃣ Verificando instalación de Docling...")
    try:
        from docling.document_converter import DocumentConverter
        print("   ✅ Docling instalado correctamente")
    except ImportError:
        print("   ❌ ERROR: Docling no está instalado")
        print("   💡 Instalar con: pip install docling")
        return False

    print()

    # Verificar PDF
    print("2️⃣ Verificando PDF fuente...")
    pdf_path = Path("../../../../../../domains/operaciones/eaf/shared/source/EAF-089-2025.pdf")

    if not pdf_path.exists():
        print(f"   ❌ ERROR: PDF no encontrado en {pdf_path}")
        return False

    print(f"   ✅ PDF encontrado: {pdf_path.name}")
    print()

    # Test conversión página 1
    print("3️⃣ Testeando conversión (solo página 1)...")
    print("   ⏳ Esto puede tomar 20-30s la primera vez (carga modelos)...")

    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))

        # Extraer elementos de página 1
        page_1_elements = []
        for item in result.document.iterate_items():
            if item.prov:
                for prov in item.prov:
                    if prov.page_no == 1:
                        page_1_elements.append({
                            "type": item.label,
                            "text": item.text[:50] if item.text else ""
                        })

        print(f"   ✅ Conversión exitosa!")
        print(f"   📊 Elementos detectados en página 1: {len(page_1_elements)}")
        print()

        # Mostrar primeros 5 elementos
        print("4️⃣ Muestra de elementos detectados:")
        print("-" * 60)
        for i, elem in enumerate(page_1_elements[:5], 1):
            text_preview = elem['text'][:40] + "..." if len(elem['text']) > 40 else elem['text']
            print(f"   {i}. [{elem['type']}] {text_preview}")

        if len(page_1_elements) > 5:
            print(f"   ... y {len(page_1_elements) - 5} elementos más")

        print("-" * 60)
        print()

        # Resumen
        print("="*60)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("="*60)
        print()
        print("💡 Siguiente paso:")
        print("   python docling_layout_extractor.py")
        print()

        return True

    except Exception as e:
        print(f"   ❌ ERROR durante conversión: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_docling_quick()
    sys.exit(0 if success else 1)
