#!/usr/bin/env python3
"""
Find ALL types of titles in individual pages - not just ANEXOS
"""

import sqlite3
import re
from pathlib import Path

def find_all_document_titles():
    # Default to platform_data/database/dark_data.db relative to project root
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    db_path = project_root / "platform_data" / "database" / "dark_data.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    print("🔍 BUSCANDO TODOS LOS TÍTULOS DE PÁGINAS INDIVIDUALES")
    print("=" * 70)
    print("No solo ANEXOS, también secciones como:")
    print("- INFORME DIARIO + fecha")
    print("- RESUMEN EJECUTIVO") 
    print("- CRONOLOGÍA")
    print("- ANTECEDENTES")
    print("- etc.")
    
    # Strategy: Look for chunks that could be title pages
    # Title pages typically have:
    # 1. Short content (titles don't have much text)
    # 2. Specific patterns (dates, institutional names)
    # 3. Capital letters format
    
    cursor = conn.execute("""
        SELECT id, page_range, content, content_length
        FROM document_chunks 
        WHERE content IS NOT NULL
          AND content NOT LIKE '[%characters]'  -- Skip placeholder content
          AND content_length BETWEEN 20 AND 1000  -- Title pages are usually short-medium
        ORDER BY content_length
    """)
    
    potential_title_chunks = cursor.fetchall()
    
    print(f"📄 Analizando {len(potential_title_chunks)} chunks potenciales para títulos...")
    
    found_titles = []
    
    # Patterns to look for different types of document sections
    title_patterns = [
        # Document sections
        {
            'type': 'INFORME_DIARIO',
            'patterns': [
                r'INFORME\s+DIARIO',
                r'Informe\s+Diario'
            ],
            'date_patterns': [
                r'(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+\d+\s+de\s+\w+\s+del?\s+\d{4}',
                r'\d+\s+de\s+(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)\s+del?\s+\d{4}'
            ]
        },
        # Executive sections
        {
            'type': 'RESUMEN_EJECUTIVO',
            'patterns': [
                r'RESUMEN\s+EJECUTIVO',
                r'Resumen\s+Ejecutivo',
                r'EXECUTIVE\s+SUMMARY'
            ],
            'date_patterns': []
        },
        # Timeline sections
        {
            'type': 'CRONOLOGIA',
            'patterns': [
                r'CRONOLOGÍA',
                r'Cronología',
                r'CRONOLOGÍA\s+DE\s+EVENTOS',
                r'TIMELINE'
            ],
            'date_patterns': []
        },
        # Background sections
        {
            'type': 'ANTECEDENTES',
            'patterns': [
                r'ANTECEDENTES',
                r'Antecedentes',
                r'BACKGROUND'
            ],
            'date_patterns': []
        },
        # Analysis sections
        {
            'type': 'ANALISIS_FALLA',
            'patterns': [
                r'ANÁLISIS\s+DE\s+LA\s+FALLA',
                r'Análisis\s+de\s+la\s+Falla',
                r'FAILURE\s+ANALYSIS'
            ],
            'date_patterns': []
        },
        # Conclusions
        {
            'type': 'CONCLUSIONES',
            'patterns': [
                r'CONCLUSIONES',
                r'Conclusiones',
                r'CONCLUSIONS'
            ],
            'date_patterns': []
        },
        # Recommendations
        {
            'type': 'RECOMENDACIONES',
            'patterns': [
                r'RECOMENDACIONES',
                r'Recomendaciones',
                r'RECOMMENDATIONS'
            ],
            'date_patterns': []
        },
        # Still look for ANEXOS too
        {
            'type': 'ANEXO',
            'patterns': [
                r'ANEXO\s+N?[ºo°]?\s*\d+',
                r'Anexo\s+N?[ºo°]?\s*\d+'
            ],
            'date_patterns': []
        }
    ]
    
    for chunk in potential_title_chunks:
        content = chunk['content'] or ''
        lines = content.split('\n')
        
        # Look for title patterns in this chunk
        for pattern_group in title_patterns:
            title_type = pattern_group['type']
            patterns = pattern_group['patterns']
            date_patterns = pattern_group['date_patterns']
            
            for pattern in patterns:
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    
                    # Skip page markers
                    if line_clean.startswith('[Page') or line_clean.startswith('Página'):
                        continue
                    
                    if re.search(pattern, line_clean, re.IGNORECASE):
                        # Found a potential title!
                        title_info = {
                            'type': title_type,
                            'main_title': line_clean,
                            'chunk_id': chunk['id'],
                            'page_range': chunk['page_range'],
                            'content_length': chunk['content_length'],
                            'additional_lines': [],
                            'dates_found': []
                        }
                        
                        # Look for additional information (like dates) in surrounding lines
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j].strip()
                            
                            if not next_line or next_line.startswith('['):
                                continue
                            
                            # Check if it's a date
                            is_date = False
                            for date_pattern in date_patterns:
                                if re.search(date_pattern, next_line, re.IGNORECASE):
                                    title_info['dates_found'].append(next_line)
                                    is_date = True
                                    break
                            
                            # If it's not a date but looks like part of title (short line)
                            if not is_date and len(next_line) < 80 and not re.match(r'^\d+\.', next_line):
                                title_info['additional_lines'].append(next_line)
                        
                        found_titles.append(title_info)
                        
                        print(f"\n🎯 {title_type} ENCONTRADO")
                        print(f"   📋 Chunk #{chunk['id']} (Página {chunk['page_range']}, {chunk['content_length']} chars)")
                        print(f"   📝 Título principal: \"{line_clean}\"")
                        
                        if title_info['dates_found']:
                            print(f"   📅 Fechas encontradas:")
                            for date in title_info['dates_found']:
                                print(f"      • \"{date}\"")
                        
                        if title_info['additional_lines']:
                            print(f"   📝 Líneas adicionales:")
                            for add_line in title_info['additional_lines'][:3]:  # Max 3
                                print(f"      • \"{add_line}\"")
                        
                        # Show context
                        print(f"   📄 Contexto:")
                        start_ctx = max(0, i-1)
                        end_ctx = min(len(lines), i+4)
                        for k in range(start_ctx, end_ctx):
                            ctx_line = lines[k].strip()
                            if ctx_line and not ctx_line.startswith('['):
                                marker = "    >>> " if k == i else "        "
                                print(f"   {marker}{ctx_line[:80]}...")
                        
                        break  # Found this pattern, move to next pattern
                break  # Found this pattern group, move to next chunk
    
    # Summary
    print(f"\n✅ RESUMEN DE TODOS LOS TÍTULOS ENCONTRADOS:")
    print("=" * 60)
    
    by_type = {}
    for title in found_titles:
        title_type = title['type']
        if title_type not in by_type:
            by_type[title_type] = []
        by_type[title_type].append(title)
    
    print(f"📊 Total títulos encontrados: {len(found_titles)}")
    print(f"📊 Tipos diferentes: {len(by_type)}")
    
    for title_type, titles in by_type.items():
        print(f"\n📋 {title_type}: {len(titles)} encontrados")
        
        for i, title in enumerate(titles, 1):
            complete_title = title['main_title']
            if title['dates_found']:
                complete_title += " " + " ".join(title['dates_found'][:1])
            elif title['additional_lines']:
                complete_title += " " + " ".join(title['additional_lines'][:1])
            
            print(f"   {i}. \"{complete_title[:80]}...\" (Chunk #{title['chunk_id']})")
    
    # Show what patterns we should look for in future documents
    print(f"\n🛠️  PATRONES PARA FUTUROS DOCUMENTOS TÉCNICOS:")
    print("=" * 50)
    
    if by_type:
        print("✅ Patrones detectados que funcionan:")
        for title_type in by_type.keys():
            pattern_desc = {
                'INFORME_DIARIO': 'INFORME DIARIO + día de la semana + fecha',
                'ANEXO': 'ANEXO Nº[número] + título descriptivo',
                'RESUMEN_EJECUTIVO': 'RESUMEN EJECUTIVO',
                'CRONOLOGIA': 'CRONOLOGÍA / CRONOLOGÍA DE EVENTOS',
                'ANTECEDENTES': 'ANTECEDENTES',
                'ANALISIS_FALLA': 'ANÁLISIS DE LA FALLA',
                'CONCLUSIONES': 'CONCLUSIONES',
                'RECOMENDACIONES': 'RECOMENDACIONES'
            }.get(title_type, 'Patrón no definido')
            
            print(f"   • {title_type}: {pattern_desc}")
    
    conn.close()
    return found_titles

if __name__ == "__main__":
    titles = find_all_document_titles()