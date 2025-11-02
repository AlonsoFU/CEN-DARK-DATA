"""
Isolated List-Item Post-Processor

GENERAL algorithm that detects ANY list-item appearing isolated
(not part of a sequence) and reclassifies it as a section header.

NOT pattern-specific - works for power lines, Zona items, or any other content.

Rule:
- Isolated list-item (no neighbors within 3 positions) → SECTION_HEADER
- Sequential list-items (has neighbors) → Keep as LIST_ITEM

This runs AFTER Docling completes extraction (document-level processing).
"""
from docling_core.types.doc import DocItemLabel


def apply_isolated_list_fix_to_document(document):
    """
    Apply isolated list-item fix at document level (after all pages processed).

    This is a GENERAL algorithm (not pattern-specific) that detects ANY list-item
    that appears isolated (not part of a sequence) and reclassifies it as section_header.

    This must be called AFTER converter.convert() completes.

    Args:
        document: The Docling document object (result.document)

    Returns:
        Number of items reclassified
    """
    print("\n" + "=" * 80)
    print("🔍 [ISOLATED LIST FIX] Post-processing document for isolated list-items")
    print("=" * 80)

    # Collect all items from the document
    all_items = []
    for item, level in document.iterate_items():
        if hasattr(item, 'label') and hasattr(item, 'text') and item.text:
            all_items.append(item)

    print(f"📊 [ISOLATED LIST FIX] Analyzing {len(all_items)} document items...")

    # Step 1: Find all LIST_ITEM items
    list_items = []
    for i, item in enumerate(all_items):
        if item.label == DocItemLabel.LIST_ITEM:
            list_items.append({
                'index': i,
                'item': item,
                'text': item.text.strip()
            })

    print(f"📋 [ISOLATED LIST FIX] Found {len(list_items)} list-item elements")

    if len(list_items) == 0:
        print("⚠️  [ISOLATED LIST FIX] No list-items found - skipping fix\n")
        return 0

    # Step 2: Determine which list-items are sequential (within 3 positions)
    for i, list_item in enumerate(list_items):
        has_next_neighbor = (i + 1 < len(list_items) and
                            list_items[i + 1]['index'] - list_item['index'] <= 3)
        has_prev_neighbor = (i > 0 and
                            list_item['index'] - list_items[i - 1]['index'] <= 3)

        list_item['is_sequential'] = has_next_neighbor or has_prev_neighbor

    # Step 3: Reclassify isolated items to SECTION_HEADER
    isolated_count = 0
    sequential_count = 0

    for list_item in list_items:
        item = list_item['item']
        text = list_item['text']

        if not list_item['is_sequential']:
            # Isolated item → Should be SECTION_HEADER
            print(f"   🔄 [ISOLATED LIST FIX] Isolated list-item → section-header:")
            print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
            item.label = DocItemLabel.SECTION_HEADER
            isolated_count += 1
        else:
            # Part of sequence → Keep as LIST_ITEM
            sequential_count += 1

    if isolated_count > 0:
        print(f"\n✅ [ISOLATED LIST FIX] Reclassified {isolated_count} isolated list-item(s) → section-header")
    if sequential_count > 0:
        print(f"ℹ️  [ISOLATED LIST FIX] Kept {sequential_count} sequential list-item(s) as list-items")

    if isolated_count == 0:
        print(f"\n⚠️  [ISOLATED LIST FIX] No isolated list-items found - all are sequential")

    print("=" * 80 + "\n")

    return isolated_count
