#!/usr/bin/env python3
"""
Corrección manual de tablas-imagen en páginas 285-286
Sin dependencias de Docling - solo corrección del JSON
"""
import json
from pathlib import Path

# Rutas
script_dir = Path(__file__).parent
cap7_dir = script_dir.parent

json_original = cap7_dir / "outputs" / "layout_lightweight.json"
json_corregido = cap7_dir / "outputs" / "layout_lightweight_FIXED.json"

print("=" * 80)
print("🔧 CORRECCIÓN MANUAL: TABLAS-IMAGEN (Páginas 285-286)")
print("=" * 80)
print()

# Cargar layout original
print("📖 Cargando layout original...")
with open(json_original, 'r') as f:
    layout = json.load(f)

elementos = layout['elements']
print(f"✅ {len(elementos)} elementos cargados")
print()

# Analizar páginas problemáticas
print("🔍 Estado actual:")
print("-" * 60)

elem_285 = [e for e in elementos if e['page'] == 285]
elem_286 = [e for e in elementos if e['page'] == 286]

print(f"Página 285: {len(elem_285)} elementos")
for e in elem_285:
    print(f"  - {e['type']:<15} | BBox: ({e['bbox']['x0']:.1f}, {e['bbox']['y0']:.1f})")

print(f"\nPágina 286: {len(elem_286)} elementos")
for e in elem_286:
    print(f"  - {e['type']:<15} | BBox: ({e['bbox']['x0']:.1f}, {e['bbox']['y0']:.1f})")

# CORRECCIÓN: Añadir elemento 'table' para página 285
print("\n" + "=" * 80)
print("🔧 Aplicando corrección...")
print("=" * 80)

# Encontrar el picture en página 285
picture_285 = next((e for e in elem_285 if e['type'] == 'picture'), None)

if picture_285:
    # Crear nuevo elemento tabla con el mismo bbox que la imagen
    tabla_nueva = {
        'type': 'table',
        'page': 285,
        'bbox': picture_285['bbox'].copy(),
        'confidence': 0.90,  # Confianza alta (manual)
        'source': 'manual_correction_image_table'
    }

    # Añadir tabla nueva
    elementos.append(tabla_nueva)

    print(f"✅ Añadida tabla en página 285")
    print(f"   BBox: {tabla_nueva['bbox']}")
    print(f"   (Mismo bbox que picture detectado)")
else:
    print("⚠️  No se encontró picture en página 285")

# Verificar página 286 (ya tiene tabla y picture)
tabla_286 = next((e for e in elem_286 if e['type'] == 'table'), None)
if tabla_286:
    print(f"\n✅ Página 286 ya tiene tabla (OK)")
else:
    print(f"\n⚠️  Página 286 no tiene tabla detectada")

# Ordenar elementos por página y posición
elementos_ordenados = sorted(elementos, key=lambda x: (x['page'], x['bbox']['y0'], x['bbox']['x0']))

# Guardar layout corregido
layout_corregido = {
    'elements': elementos_ordenados,
    'metadata': {
        'source': 'docling_lightweight_granite',
        'fixes_applied': [
            {
                'page': 285,
                'issue': 'table_detected_as_image_only',
                'fix': 'added_table_element_with_picture_bbox',
                'date': '2025-01-17'
            }
        ],
        'note': 'Tablas en páginas 285-286 están incrustadas como imágenes en el PDF'
    }
}

with open(json_corregido, 'w') as f:
    json.dump(layout_corregido, f, indent=2)

print("\n" + "=" * 80)
print("💾 GUARDADO")
print("=" * 80)
print(f"Archivo: {json_corregido}")
print(f"Total elementos: {len(elementos_ordenados)} (antes: {len(layout['elements'])})")
print()

# Verificación final
print("=" * 80)
print("✅ VERIFICACIÓN FINAL")
print("=" * 80)

elem_285_new = [e for e in elementos_ordenados if e['page'] == 285]
elem_286_new = [e for e in elementos_ordenados if e['page'] == 286]

tablas_285 = [e for e in elem_285_new if e['type'] == 'table']
pictures_285 = [e for e in elem_285_new if e['type'] == 'picture']

tablas_286 = [e for e in elem_286_new if e['type'] == 'table']
pictures_286 = [e for e in elem_286_new if e['type'] == 'picture']

print(f"\nPágina 285:")
print(f"  - Tablas: {len(tablas_285)} {'✅ (CORREGIDO: 0 → 1)' if len(tablas_285) > 0 else '❌'}")
print(f"  - Pictures: {len(pictures_285)}")
if tablas_285:
    print(f"    Tabla bbox: {tablas_285[0]['bbox']}")

print(f"\nPágina 286:")
print(f"  - Tablas: {len(tablas_286)} {'✅' if len(tablas_286) > 0 else '❌'}")
print(f"  - Pictures: {len(pictures_286)}")

print("\n" + "=" * 80)
print("🎯 CORRECCIÓN COMPLETA")
print("=" * 80)
print()
print("📋 Resumen:")
print(f"  ✅ Página 285: tabla-imagen ahora detectada como tabla + picture")
print(f"  ✅ Página 286: sin cambios (ya estaba correcto)")
print()
print("📁 Archivos:")
print(f"  Original:  {json_original}")
print(f"  Corregido: {json_corregido}")
print()
print("💡 Próximos pasos:")
print("  1. Revisar visualización del PDF anotado")
print("  2. Usar json_corregido para procesamiento posterior")
print("  3. Considerar re-generar PDF anotado con correcciones")
print()
