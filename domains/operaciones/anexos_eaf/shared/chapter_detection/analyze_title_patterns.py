#!/usr/bin/env python3
"""
Analyze all title patterns found to create processing rules for technical documents
"""

import sqlite3
import re
from pathlib import Path

def analyze_title_patterns():
    # Default to platform_data/database/dark_data.db relative to project root
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    db_path = project_root / "platform_data" / "database" / "dark_data.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    print("🔍 ANÁLISIS DE PATRONES DE TÍTULOS ENCONTRADOS")
    print("=" * 70)
    
    # Get all detected titles
    cursor = conn.execute("""
        SELECT specific_annex_number, specific_annex_title, annex_theme
        FROM document_chunks 
        WHERE specific_annex_number IS NOT NULL
        ORDER BY CAST(specific_annex_number AS INTEGER)
    """)
    
    annexes = cursor.fetchall()
    
    print(f"📊 TÍTULOS DETECTADOS EN ESTE DOCUMENTO:")
    print("=" * 50)
    
    title_patterns = {}
    
    for annex in annexes:
        num = annex['specific_annex_number']
        title = annex['specific_annex_title']
        theme = annex['annex_theme']
        
        if num not in title_patterns:
            title_patterns[num] = {
                'title': title,
                'theme': theme,
                'format_analysis': analyze_title_format(title)
            }
    
    for num in sorted(title_patterns.keys(), key=int):
        data = title_patterns[num]
        print(f"\n📋 ANEXO {num}:")
        print(f"   📝 \"{data['title']}\"")
        print(f"   🏷️  Tema: {data['theme']}")
        print(f"   📐 Formato: {data['format_analysis']}")
    
    # Analyze patterns across all titles
    print(f"\n🔍 ANÁLISIS DE PATRONES COMUNES:")
    print("=" * 50)
    
    patterns_found = {
        'starts_with_detalle': 0,
        'contains_dias_fecha': 0,
        'contains_sistema': 0,
        'contains_coordinador': 0,
        'contains_empresas': 0,
        'contains_antecedentes': 0,
        'contains_analisis': 0,
        'long_descriptive': 0,
        'short_descriptive': 0
    }
    
    all_titles = [data['title'] for data in title_patterns.values()]
    
    for title in all_titles:
        title_lower = title.lower()
        
        if title_lower.startswith('detalle'):
            patterns_found['starts_with_detalle'] += 1
        if 'días' in title_lower and ('febrero' in title_lower or 'fecha' in title_lower):
            patterns_found['contains_dias_fecha'] += 1
        if 'sistema' in title_lower:
            patterns_found['contains_sistema'] += 1
        if 'coordinador' in title_lower:
            patterns_found['contains_coordinador'] += 1
        if 'empresas' in title_lower:
            patterns_found['contains_empresas'] += 1
        if 'antecedentes' in title_lower:
            patterns_found['contains_antecedentes'] += 1
        if 'análisis' in title_lower or 'analisis' in title_lower:
            patterns_found['contains_analisis'] += 1
        
        if len(title) > 80:
            patterns_found['long_descriptive'] += 1
        elif len(title) > 30:
            patterns_found['short_descriptive'] += 1
    
    print("📊 PATRONES IDENTIFICADOS:")
    for pattern, count in patterns_found.items():
        if count > 0:
            percentage = (count / len(all_titles)) * 100
            print(f"   • {pattern.replace('_', ' ').title()}: {count}/{len(all_titles)} ({percentage:.0f}%)")
    
    # Create processing rules based on patterns
    print(f"\n🛠️  REGLAS DE PROCESAMIENTO PARA DOCUMENTOS TÉCNICOS:")
    print("=" * 60)
    
    processing_rules = create_processing_rules(title_patterns, patterns_found)
    
    for i, rule in enumerate(processing_rules, 1):
        print(f"\n{i}. 📋 {rule['category']}:")
        print(f"   🔍 Patrón: {rule['pattern']}")
        print(f"   🏷️  Tema sugerido: {rule['suggested_theme']}")
        print(f"   📝 Ejemplo: \"{rule['example']}\"")
        if rule['notes']:
            print(f"   💡 Nota: {rule['notes']}")
    
    conn.close()
    return processing_rules

def analyze_title_format(title):
    """Analyze the format characteristics of a title"""
    
    characteristics = []
    
    # Length analysis
    if len(title) > 100:
        characteristics.append("Muy descriptivo")
    elif len(title) > 60:
        characteristics.append("Descriptivo")
    else:
        characteristics.append("Conciso")
    
    # Content analysis
    if title.lower().startswith('detalle'):
        characteristics.append("Inicia con 'Detalle'")
    
    if 'días' in title.lower() and any(fecha in title.lower() for fecha in ['febrero', 'enero', 'marzo']):
        characteristics.append("Incluye fechas específicas")
    
    if any(word in title.lower() for word in ['sistema', 'coordinador', 'empresas']):
        characteristics.append("Menciona entidades institucionales")
    
    if any(word in title.lower() for word in ['programado', 'real', 'forzado']):
        characteristics.append("Especifica tipo de operación")
    
    return " | ".join(characteristics)

def create_processing_rules(title_patterns, patterns_found):
    """Create processing rules based on detected patterns"""
    
    rules = [
        {
            'category': 'ANEXOS DE DETALLE OPERACIONAL',
            'pattern': r'Detalle\s+de\s+la\s+(generación|operación).*días\s+\d+\s+y\s+\d+',
            'suggested_theme': 'generation_programming',
            'example': 'Detalle de la generación programada para los días 25 y 26 de febrero de 2025',
            'notes': 'Común en informes de fallas eléctricas - datos específicos por fecha'
        },
        {
            'category': 'ANEXOS DE MOVIMIENTO/CDC',
            'pattern': r'Detalle.*Movimiento.*Centrales.*CDC',
            'suggested_theme': 'operational_data',
            'example': 'Detalle del Movimiento de Centrales e Informe Diario del CDC correspondientes a los días 25 y 26',
            'notes': 'Centro de Despacho y Control - información operativa crítica'
        },
        {
            'category': 'ANEXOS DE MANTENIMIENTO',
            'pattern': r'Detalle.*mantenimientos?\s+(programados?|forzados?)',
            'suggested_theme': 'equipment_details',
            'example': 'Detalle de los mantenimientos programados y forzados para los días 25 y 26 de febrero de 2025',
            'notes': 'Información de equipos y su estado operativo'
        },
        {
            'category': 'ANEXOS DE INFORMES TÉCNICOS',
            'pattern': r'Informe.*instalaciones.*sistema.*Coordinador.*Nacional',
            'suggested_theme': 'technical_analysis',
            'example': 'Informe de trabajo y falla de instalaciones ingresados en el sistema del Coordinador Eléctrico Nacional',
            'notes': 'Documentos formales del regulador eléctrico'
        },
        {
            'category': 'ANEXOS DE ANTECEDENTES',
            'pattern': r'(Otros\s+)?antecedentes.*empresas.*(involucradas|coordinadas)',
            'suggested_theme': 'communication_logs',
            'example': 'Otros antecedentes aportados por las empresas involucradas en la falla',
            'notes': 'Documentación complementaria de las empresas'
        },
        {
            'category': 'ANEXOS DE ANÁLISIS TÉCNICO ESPECIALIZADO',
            'pattern': r'Análisis.*esquema\s+(EDAC|técnico)',
            'suggested_theme': 'technical_analysis',
            'example': 'Análisis operativo del esquema EDAC',
            'notes': 'EDAC = Esquemas de Desconexión Automática de Carga'
        }
    ]
    
    return rules

def suggest_document_processing_improvements():
    """Suggest improvements for processing similar documents"""
    
    print(f"\n🚀 SUGERENCIAS PARA MEJORAR EL PROCESAMIENTO:")
    print("=" * 60)
    
    improvements = [
        {
            'area': 'Detección de Patrones de Título',
            'suggestion': 'Crear regex específicos para documentos eléctricos chilenos',
            'implementation': 'Buscar "Detalle de..." seguido de fechas específicas (25 y 26 de febrero)',
            'benefit': 'Detectar automáticamente anexos operacionales vs técnicos'
        },
        {
            'area': 'Clasificación Temática Automática',
            'suggestion': 'Usar keywords institucionales (CDC, Coordinador Eléctrico Nacional)',
            'implementation': 'Si contiene "CDC" → operational_data, si contiene "esquema EDAC" → technical_analysis',
            'benefit': 'Clasificación más precisa sin intervención manual'
        },
        {
            'area': 'Detección de Fechas Críticas',
            'suggestion': 'Identificar documentos de eventos específicos por fechas',
            'implementation': 'Patrones como "25 y 26 de febrero de 2025" indican eventos puntuales',
            'benefit': 'Agrupar contenido relacionado al mismo incidente'
        },
        {
            'area': 'Manejo de Contenido Placeholder',
            'suggestion': 'Implementar reprocesamiento de chunks con [X characters]',
            'implementation': 'Identificar y re-extraer contenido de páginas problemáticas',
            'benefit': 'Recuperar 62% del contenido actualmente no accesible'
        },
        {
            'area': 'Estructura Jerárquica',
            'suggestion': 'Establecer relaciones padre-hijo entre anexos y secciones',
            'implementation': 'ANEXO → subsecciones → contenido detallado',
            'benefit': 'Navegación más intuitiva del documento técnico'
        }
    ]
    
    for i, improvement in enumerate(improvements, 1):
        print(f"\n{i}. 🛠️  {improvement['area']}:")
        print(f"   💡 Sugerencia: {improvement['suggestion']}")
        print(f"   🔧 Implementación: {improvement['implementation']}")  
        print(f"   ✅ Beneficio: {improvement['benefit']}")

if __name__ == "__main__":
    rules = analyze_title_patterns()
    suggest_document_processing_improvements()