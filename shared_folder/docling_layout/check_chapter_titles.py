#!/usr/bin/env python3
"""
Quick script to check how chapter titles are classified across all chapters
"""
import json
from pathlib import Path

def find_chapter_title(chapter_num, json_path):
    """Find the main chapter title and its label"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        def search_recursive(items, depth=0, max_depth=3, max_items=200):
            """Recursively search for chapter title"""
            count = 0
            for item in items:
                if count >= max_items:
                    break
                count += 1

                # Check if this item is the chapter title
                if 'text' in item and item['text'].strip().startswith(f"{chapter_num}."):
                    return {
                        'chapter': chapter_num,
                        'text': item['text'].strip()[:80],
                        'label': item.get('label', 'NO_LABEL')
                    }

                # Recursively search children
                if depth < max_depth and 'children' in item:
                    result = search_recursive(item['children'], depth + 1, max_depth, max_items - count)
                    if result:
                        return result

            return None

        # Search in body.children
        if 'body' in data and 'children' in data['body']:
            return search_recursive(data['body']['children'])

        return None
    except Exception as e:
        print(f"Error reading chapter {chapter_num}: {e}")
        return None

# Check all chapters
print("=" * 100)
print("CHAPTER TITLE CLASSIFICATION ANALYSIS")
print("=" * 100)
print()

for chapter_num in range(1, 12):
    json_path = Path(f"capitulo_{chapter_num:02d}/outputs/layout_WITH_PATCH.json")

    if not json_path.exists():
        print(f"Chapter {chapter_num}: ❌ JSON not found")
        continue

    result = find_chapter_title(chapter_num, json_path)

    if result:
        label = result['label']
        emoji = "🔴" if label == "section_header" else "🟡" if label == "title" else "⚪"
        print(f"Chapter {chapter_num:2d}: {emoji} {label:20s} | {result['text']}")
    else:
        print(f"Chapter {chapter_num:2d}: ❌ Title not found in first 30 items")

print()
print("Legend:")
print("  🔴 section_header (should show red box in PDF)")
print("  🟡 title (should show red box in PDF)")
print("  ⚪ other label (no red box in PDF)")
print("=" * 100)
