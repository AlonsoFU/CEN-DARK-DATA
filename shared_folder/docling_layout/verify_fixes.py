#!/usr/bin/env python3
"""
Verify the 5 specific fix cases across chapters
"""
import json
from pathlib import Path

def get_page_items(doc_dict, page_num):
    """Extract all items from a specific page"""
    items = []

    def traverse(node, depth=0):
        if isinstance(node, dict):
            # Check if this item is on the target page
            if 'prov' in node and node['prov']:
                prov = node['prov'][0] if isinstance(node['prov'], list) else node['prov']
                if isinstance(prov, dict) and prov.get('page_no') == page_num:
                    text = node.get('text', '')
                    label = node.get('label', 'unknown')
                    marker = node.get('marker', '')
                    items.append({
                        'text': text,
                        'label': label,
                        'marker': marker,
                        'page': page_num
                    })

            # Traverse children
            if 'children' in node:
                for child in node['children']:
                    traverse(child, depth + 1)

    if 'body' in doc_dict:
        traverse(doc_dict['body'])

    return items

def check_chapter_2_page_10():
    """Case 1: Two consecutive dash bullets should both be list_item"""
    json_path = Path("capitulo_02/outputs/layout_WITH_PATCH.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    items = get_page_items(doc, 10)

    # Find items starting with dash
    dash_items = [item for item in items if item['text'].strip().startswith('-')]

    print("✅ Caso 1: Cap 2 Pág 10 - Dos bullets consecutivos con '-':")
    for item in dash_items[:2]:  # Check first 2
        status = "✅" if item['label'] == 'list_item' else "🔴"
        print(f"   {status} [{item['label']:15s}] {item['text'][:60]}...")
    print()

    return all(item['label'] == 'list_item' for item in dash_items[:2])

def check_chapter_4_page_4():
    """Case 2: Long text without bullet should be text, not list_item"""
    json_path = Path("capitulo_04/outputs/layout_WITH_PATCH.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    items = get_page_items(doc, 4)

    # Find the long text at the beginning (first non-header item)
    long_text = None
    for item in items:
        text = item['text'].strip()
        if len(text) > 500 and not text.startswith(('4.', 'Capítulo')):
            long_text = item
            break

    print("✅ Caso 2: Cap 4 Pág 4 - Texto largo sin bullet:")
    if long_text:
        status = "✅" if long_text['label'] == 'text' else "🔴"
        print(f"   {status} [{long_text['label']:15s}] {long_text['text'][:60]}... ({len(long_text['text'])} chars)")
        print(f"   Marker: '{long_text['marker']}'")
        result = long_text['label'] == 'text'
    else:
        print("   ⚠️  No se encontró texto largo sin bullet")
        result = False
    print()

    return result

def check_chapter_6_page_53():
    """Case 3: Short text 'ERS nuevamente.' should be list_item (continuation)"""
    json_path = Path("capitulo_06/outputs/layout_WITH_PATCH.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    items = get_page_items(doc, 53)

    # Find "ERS nuevamente" or similar continuation text
    continuation_item = None
    for item in items:
        text = item['text'].strip()
        if 'ERS' in text and 'nuevamente' in text:
            continuation_item = item
            break

    print("✅ Caso 3: Cap 6 Pág 53 - Texto corto continuación:")
    if continuation_item:
        status = "✅" if continuation_item['label'] == 'list_item' else "🔴"
        print(f"   {status} [{continuation_item['label']:15s}] {continuation_item['text'][:60]}... ({len(continuation_item['text'])} chars)")
        result = continuation_item['label'] == 'list_item'
    else:
        print("   ⚠️  No se encontró 'ERS nuevamente'")
        result = False
    print()

    return result

def check_chapter_7_zona_quinta():
    """Case 4: 'Zona Quinta - Área Costa' should be section_header"""
    json_path = Path("capitulo_07/outputs/layout_WITH_PATCH.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    # Search all pages
    zona_item = None
    for page in range(1, 100):
        items = get_page_items(doc, page)
        for item in items:
            if 'Zona Quinta' in item['text'] and 'Área Costa' in item['text']:
                zona_item = item
                break
        if zona_item:
            break

    print("✅ Caso 4: Cap 7 - 'Zona Quinta - Área Costa' aislado:")
    if zona_item:
        status = "✅" if zona_item['label'] == 'section_header' else "🔴"
        print(f"   {status} [{zona_item['label']:15s}] {zona_item['text'][:60]}")
        print(f"   Página: {zona_item['page']}")
        result = zona_item['label'] == 'section_header'
    else:
        print("   ⚠️  No se encontró 'Zona Quinta - Área Costa'")
        result = False
    print()

    return result

def check_chapter_7_page_5():
    """Case 5: Text without matching marker should be text"""
    json_path = Path("capitulo_07/outputs/layout_WITH_PATCH.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    items = get_page_items(doc, 5)

    # Find first text item (likely the one without matching marker)
    first_text = None
    for item in items:
        text = item['text'].strip()
        if len(text) > 100 and not text.startswith(('7.', 'Capítulo')):
            first_text = item
            break

    print("✅ Caso 5: Cap 7 Pág 5 - Texto sin marcador coincidente:")
    if first_text:
        status = "✅" if first_text['label'] == 'text' else "🔴"
        print(f"   {status} [{first_text['label']:15s}] {first_text['text'][:60]}... ({len(first_text['text'])} chars)")
        print(f"   Marker: '{first_text['marker']}'")
        result = first_text['label'] == 'text'
    else:
        print("   ⚠️  No se encontró texto sin marcador")
        result = False
    print()

    return result

if __name__ == "__main__":
    print("=" * 80)
    print("VERIFICACIÓN DE FIXES - 5 CASOS ESPECÍFICOS")
    print("=" * 80)
    print()

    results = []
    results.append(check_chapter_2_page_10())
    results.append(check_chapter_4_page_4())
    results.append(check_chapter_6_page_53())
    results.append(check_chapter_7_zona_quinta())
    results.append(check_chapter_7_page_5())

    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Casos correctos: {passed}/{total}")

    if passed == total:
        print("✅ TODOS LOS CASOS PASARON")
    else:
        print(f"🔴 {total - passed} casos fallaron")
    print("=" * 80)
