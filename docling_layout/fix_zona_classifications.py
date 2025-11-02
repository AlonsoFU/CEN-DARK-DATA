#!/usr/bin/env python3
"""
Post-process clean extraction to fix Zona item classifications
Reclassify all "Zona...Área" items from list_item to section_header
"""
import json
from pathlib import Path

json_path = Path(__file__).parent / "capitulo_07/outputs/layout_clean.json"
output_path = Path(__file__).parent / "capitulo_07/outputs/layout_clean_zona_fixed.json"

print("=" * 80)
print("Fixing Zona Classifications")
print("=" * 80)
print(f"\nInput:  {json_path}")
print(f"Output: {output_path}")

# Load JSON
with open(json_path, 'r') as f:
    data = json.load(f)

# Fix classifications
fixed_count = 0
for elem in data['elements']:
    text = elem.get('text', '').strip()
    elem_type = elem.get('type')

    # Check if this is a Zona item that needs fixing
    if 'Zona' in text and 'Área' in text and elem_type == 'list_item':
        elem['type'] = 'section_header'
        fixed_count += 1
        print(f"✅ Fixed: {text[:60]}")

# Save fixed JSON
with open(output_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n📊 Fixed {fixed_count} Zona items (list_item → section_header)")
print(f"✅ Saved: {output_path}")
print("=" * 80)
