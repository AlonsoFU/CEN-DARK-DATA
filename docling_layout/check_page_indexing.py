#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

# Check page numbering in Chapter 1 JSON
json_path = Path('capitulo_01/outputs/layout_WITH_PATCH.json')
with open(json_path) as f:
    data = json.load(f)

# Show first 5 elements with their page numbers
print('First 5 elements from Chapter 1 JSON:')
for i, elem in enumerate(data['elements'][:5]):
    print(f'  Element {i}: page={elem["page"]}, type={elem["type"]}, text={elem["text"][:50]}...')

# Check page distribution
pages = [e['page'] for e in data['elements']]
page_counts = Counter(pages)
print(f'\nPage distribution (first 5): {sorted(page_counts.items())[:5]}')
print(f'Min page: {min(pages)}, Max page: {max(pages)}')
