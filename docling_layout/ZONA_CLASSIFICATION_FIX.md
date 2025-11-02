# Zona Classification Fix

## Problem

In Chapter 7, Docling inconsistently classifies "Zona [Name] - Área [Name]" items:

- `• Zona Centro - Área Itahue` → ✅ Classified as **list-item** (correct)
- `• Zona Centro - Área Alto Jahuel` → ❌ Classified as **section-header** (wrong!)

**Root Cause:** When Docling doesn't find 2+ sequential list items with similar formatting, it wrongly classifies isolated list items as section-headers.

## Solution Implemented

Added two fixes to `eaf_patch/core/eaf_patch_engine.py`:

### Fix 1: Reclassify section-headers to list-items (lines 189-214)

```python
# ========================================================================
# FIX: Reclassify section-headers to list-items for "Zona" pattern
# ========================================================================
# Docling misclassifies isolated list items as section-headers when it
# doesn't find 2+ sequential list items. Fix: reclassify section-headers
# that start with bullet and match "Zona [Name] - Área [Name]" pattern
import re
zona_pattern = re.compile(r'^[·•]\s*Zona\s+.+?\s+-\s+Área\s+.+', re.IGNORECASE)

reclassified_count = 0
for cluster in self.regular_clusters:
    if hasattr(cluster, 'label') and cluster.label == DocItemLabel.SECTION_HEADER:
        if hasattr(cluster, 'text') and cluster.text:
            text = cluster.text.strip()

            # Check if matches "Zona" pattern with bullet
            if zona_pattern.match(text):
                print(f"   🔄 [PATCH] Reclassifying section-header → list-item:")
                print(f"      '{text[:60]}{'...' if len(text) > 60 else ''}'")

                # Change label to LIST_ITEM
                cluster.label = DocItemLabel.LIST_ITEM
                reclassified_count += 1

if reclassified_count > 0:
    print(f"✅ [PATCH] Reclassified {reclassified_count} section-header(s) to list-item")
```

### Fix 2: Add missing bullets to list-items (lines 216-240)

```python
# ========================================================================
# FIX: Add missing bullets to list-items that match "Zona" pattern
# ========================================================================
# Some list-items are correctly classified but missing the bullet prefix
zona_pattern_no_bullet = re.compile(r'^Zona\s+.+?\s+-\s+Área\s+.+', re.IGNORECASE)

bullet_added_count = 0
for cluster in self.regular_clusters:
    if hasattr(cluster, 'label') and cluster.label == DocItemLabel.LIST_ITEM:
        if hasattr(cluster, 'text') and cluster.text:
            text = cluster.text.strip()

            # Check if matches "Zona" pattern WITHOUT bullet
            if zona_pattern_no_bullet.match(text) and not text.startswith(('·', '•')):
                print(f"   📝 [PATCH] Adding missing bullet to list-item:")
                print(f"      Before: '{text[:60]}{'...' if len(text) > 60 else ''}'")

                # Add bullet prefix
                cluster.text = f"• {text}"
                bullet_added_count += 1

                print(f"      After: '{cluster.text[:60]}{'...' if len(cluster.text) > 60 else ''}'")

if bullet_added_count > 0:
    print(f"✅ [PATCH] Added bullets to {bullet_added_count} list-item(s)")
```

## Expected Results

**Before Fix (from existing Chapter 7 extraction):**

Section Headers (WRONG):
- `· Zona Norte Grande - Área Arica`
- `· Zona Norte Grande - Área Iquique`
- `· Zona Norte Grande - Área Tarapacá`
- `· Zona Norte Grande - Área Centro`
- `· Zona Interconexión`
- `· Zona Quinta - Área Valle`
- `· Zona Centro - Área Alto Jahuel` ← THIS ONE
- `· Zona Sur - Área Bio Bío`
- `· Zona Sur - Área Araucanía`

List Items (CORRECT but missing bullets):
- `Zona Norte Grande - Área Cordillera` (no bullet)
- `Zona Norte Grande - Área O´Higgins` (no bullet)
- `Zona Norte Grande - Área Capricornio` (no bullet)
- `Zona Norte Chico - Área Diego de Almagro` (no bullet)
- `Zona Norte Chico - Área Cardones` (no bullet)
- `Zona Norte Chico - Área Pan de Azúcar` (no bullet)
- `Zona Quinta - Área Costa` (no bullet)
- `Zona Centro - Área Cerro Navia` (no bullet)
- `Zona Centro - Área Itahue` (no bullet) ← THIS ONE

**After Fix:**

Section Headers: 0 items ✅

List Items (ALL with bullets):
- `• Zona Norte Grande - Área Arica`
- `• Zona Norte Grande - Área Iquique`
- `• Zona Norte Grande - Área Tarapacá`
- `• Zona Norte Grande - Área Centro`
- `• Zona Interconexión`
- `• Zona Quinta - Área Valle`
- `• Zona Centro - Área Alto Jahuel` ← FIXED!
- `• Zona Sur - Área Bio Bío`
- `• Zona Sur - Área Araucanía`
- `• Zona Norte Grande - Área Cordillera` ← Bullet added!
- `• Zona Norte Grande - Área O´Higgins` ← Bullet added!
- `• Zona Norte Grande - Área Capricornio` ← Bullet added!
- `• Zona Norte Chico - Área Diego de Almagro` ← Bullet added!
- `• Zona Norte Chico - Área Cardones` ← Bullet added!
- `• Zona Norte Chico - Área Pan de Azúcar` ← Bullet added!
- `• Zona Quinta - Área Costa` ← Bullet added!
- `• Zona Centro - Área Cerro Navia` ← Bullet added!
- `• Zona Centro - Área Itahue` ← Bullet added!

## Testing

To test this fix:

```bash
cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout

# 1. Reprocess Chapter 7 with the patch
python3 extract_chapter7_patched.py

# 2. Verify all Zona items are list-items
python3 -c "
import json
with open('capitulo_07/outputs/layout_patched.json', 'r') as f:
    data = json.load(f)

section_headers = []
list_items = []

for item in data['elements']:
    text = item.get('text', '').strip()
    item_type = item.get('type')

    if 'Zona' in text and 'Área' in text:
        if item_type == 'section_header':
            section_headers.append(text)
        elif item_type == 'list_item':
            list_items.append(text)

print(f'Section headers: {len(section_headers)} (should be 0)')
print(f'List items: {len(list_items)} (should be ~18)')
print(f'All have bullets: {all(t.startswith((\"·\", \"•\")) for t in list_items)}')
"
```

## Impact

This fix ensures consistent classification of Zona location items across all EAF documents:
- ✅ All Zona items classified as list-items (not section-headers)
- ✅ All list-items have bullet prefixes for visual consistency
- ✅ Improves downstream text extraction and analysis
- ✅ Makes the data structure more predictable for AI processing

## Files Modified

- `eaf_patch/core/eaf_patch_engine.py` (lines 189-240)
  - Added Zona pattern regex matching
  - Added section-header → list-item reclassification
  - Added bullet prefix addition for list-items without bullets

## Related Issues

This is part of a larger effort to fix Docling's inconsistent classification of similar items. Other related fixes:
- Split title fix (lines 156-187): Replaces short titles like "6." with complete lines "6. Normalización del servicio"
- Power line classification: Reclassifies power line listings as LIST_ITEM instead of SECTION_HEADER
