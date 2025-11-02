"""
Zona Classification Post-Processor

Fixes Docling's classification of "Zona ... - Área ..." items.
These items can appear as isolated headers OR sequential list items.

Rule:
- Isolated Zona items → SECTION_HEADER
- Sequential Zona items (2+) → LIST_ITEM with bullet

This runs AFTER Docling completes extraction (document-level processing).
"""
import re
from docling_core.types.doc import DocItemLabel


def apply_zona_fix_to_document(document):
    """
    Apply Zona classification fix at document level (after all pages processed).

    This must be called AFTER converter.convert() completes, because the page-level
    patch can't see items across pages.

    Args:
        document: The Docling document object (result.document)

    Returns:
        Number of items reclassified
    """
    zona_pattern = re.compile(r'^[·•]?\s*Zona\s+.+?\s+-\s+Área\s+.+', re.IGNORECASE)

    print("\n" + "=" * 80)
    print("🔧 [ZONA FIX] Post-processing document for Zona classification")
    print("=" * 80)

    # Collect all items from the document
    all_items = []
    for item, level in document.iterate_items():
        if hasattr(item, 'label') and hasattr(item, 'text') and item.text:
            all_items.append(item)

    print(f"📊 [ZONA FIX] Analyzing {len(all_items)} document items...")

    # Step 1: Find all Zona items
    zona_items = []
    for i, item in enumerate(all_items):
        text = item.text.strip()
        if zona_pattern.match(text):
            zona_items.append({
                'index': i,
                'item': item,
                'text': text,
                'original_label': item.label
            })

    print(f"🔍 [ZONA FIX] Found {len(zona_items)} Zona items in document")

    if len(zona_items) == 0:
        print("⚠️  [ZONA FIX] No Zona items found - skipping fix\n")
        return 0

    # Step 2: Determine which Zona items are sequential (within 3 positions)
    for i, zona_item in enumerate(zona_items):
        has_next_neighbor = (i + 1 < len(zona_items) and
                            zona_items[i + 1]['index'] - zona_item['index'] <= 3)
        has_prev_neighbor = (i > 0 and
                            zona_item['index'] - zona_items[i - 1]['index'] <= 3)

        zona_item['is_sequential'] = has_next_neighbor or has_prev_neighbor

    # Step 3: Apply reclassification
    reclassified_to_header = 0
    reclassified_to_list = 0

    for zona_item in zona_items:
        item = zona_item['item']
        text = zona_item['text']

        if zona_item['is_sequential']:
            # Part of a sequence (2+ items) → Should be LIST_ITEM
            if item.label != DocItemLabel.LIST_ITEM:
                print(f"   🔄 [ZONA FIX] Sequential → list-item: '{text[:60]}'...")
                item.label = DocItemLabel.LIST_ITEM
                reclassified_to_list += 1

            # Ensure it has a bullet
            if not text.startswith(('·', '•')):
                print(f"   📝 [ZONA FIX] Adding bullet: '{text[:50]}'...")
                item.text = f"• {text}"
        else:
            # Isolated item → Should be SECTION_HEADER
            if item.label != DocItemLabel.SECTION_HEADER:
                print(f"   🔄 [ZONA FIX] Isolated → section-header: '{text[:60]}'...")
                item.label = DocItemLabel.SECTION_HEADER
                reclassified_to_header += 1

    total_changed = reclassified_to_header + reclassified_to_list
    if total_changed > 0:
        print(f"\n✅ [ZONA FIX] Reclassified {reclassified_to_header} isolated → section-header")
        print(f"✅ [ZONA FIX] Reclassified {reclassified_to_list} sequential → list-item")
    else:
        print(f"\n⚠️  [ZONA FIX] No reclassification needed - all items already correct")

    print("=" * 80 + "\n")

    return total_changed
