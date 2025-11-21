#!/usr/bin/env python3
import json
from pathlib import Path

for chapter in range(1, 12):
    json_path = Path(f"capitulo_{chapter:02d}/outputs/layout_WITH_PATCH.json")

    if not json_path.exists():
        print(f"Ch {chapter}: JSON not found")
        continue

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def search_for_title(items, target_prefix, depth=0, max_items=500):
        """Recursively search for chapter title"""
        count = 0
        for item in items:
            if count >= max_items:
                break
            count += 1

            text = item.get('text', '')
            if text and text.strip().startswith(target_prefix):
                return item.get('label', 'NO_LABEL')

            if 'children' in item and depth < 5:
                result = search_for_title(item['children'], target_prefix, depth + 1, max_items - count)
                if result:
                    return result
        return None

    label = None
    if 'body' in data and 'children' in data['body']:
        label = search_for_title(data['body']['children'], f"{chapter}.")

    if label:
        emoji = "✅" if label == "section_header" else "🟡" if label == "title" else "❌"
        print(f"Ch {chapter:2d}: {emoji} {label}")
    else:
        print(f"Ch {chapter:2d}: ❓ Not found")
