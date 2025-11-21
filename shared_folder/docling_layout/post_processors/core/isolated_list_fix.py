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

    # Helper function to detect marker type
    def get_marker_type(text, item):
        """Returns 'bullet' or 'enumerated' based on marker"""
        # Check item marker attribute if available
        marker = getattr(item, 'marker', '')
        if not marker:
            # Detect from text
            text_stripped = text.strip()
            if text_stripped:
                first_char = text_stripped[0]
                # Bullet markers: -, •, *, ·
                if first_char in ['-', '•', '*', '·']:
                    return 'bullet'
                # Enumerated: a), b), 1), 2), etc.
                if len(text_stripped) > 1 and text_stripped[1] == ')':
                    return 'enumerated'
        else:
            # Check marker value
            if marker in ['-', '•', '*', '·']:
                return 'bullet'
            elif marker and (marker.endswith(')') or marker[0].isalnum()):
                return 'enumerated'

        return 'bullet'  # Default to bullet

    # Step 1: Find all LIST_ITEM items
    list_items = []
    for i, item in enumerate(all_items):
        if item.label == DocItemLabel.LIST_ITEM:
            text = item.text.strip()
            marker_type = get_marker_type(text, item)
            list_items.append({
                'index': i,
                'item': item,
                'text': text,
                'marker_type': marker_type
            })

    print(f"📋 [ISOLATED LIST FIX] Found {len(list_items)} list-item elements")

    if len(list_items) == 0:
        print("⚠️  [ISOLATED LIST FIX] No list-items found - skipping fix\n")
        return 0

    # Step 2: Determine which list-items are sequential
    # Different rules for bullets vs enumerated:
    # - Bullets (-, •, *, ·): must be adjacent (distance = 1)
    # - Enumerated (a), b), 1), 2)): can have gaps (distance ≤ 3)
    for i, list_item in enumerate(list_items):
        marker_type = list_item['marker_type']
        max_distance = 1 if marker_type == 'bullet' else 3

        has_next_neighbor = (i + 1 < len(list_items) and
                            list_items[i + 1]['index'] - list_item['index'] <= max_distance)
        has_prev_neighbor = (i > 0 and
                            list_item['index'] - list_items[i - 1]['index'] <= max_distance)

        list_item['is_sequential'] = has_next_neighbor or has_prev_neighbor

    # Step 3: Reclassify isolated items to SECTION_HEADER
    # BUT skip if the item appears right after a table or picture (likely caption/note)
    isolated_count = 0
    sequential_count = 0
    skipped_after_table_count = 0

    for list_item in list_items:
        item = list_item['item']
        text = list_item['text']
        index = list_item['index']

        if not list_item['is_sequential']:
            # Check if previous item is a table or picture
            is_after_table_or_picture = False
            if index > 0:
                prev_item = all_items[index - 1]
                if hasattr(prev_item, 'label') and prev_item.label in [DocItemLabel.TABLE, DocItemLabel.PICTURE]:
                    is_after_table_or_picture = True

            # Check punctuation:
            # - Headers typically end with ':' (colon)
            # - Items ending with '.' (period) are LESS likely to be headers
            ends_with_colon = text.endswith(':')
            ends_with_period = text.endswith('.')

            if is_after_table_or_picture:
                # Skip conversion - likely a caption or note
                print(f"   ⏭️  [ISOLATED LIST FIX] Skipping isolated item after table/picture (likely caption):")
                print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                skipped_after_table_count += 1
            elif ends_with_period:
                # Skip conversion - ends with period, less likely to be header
                print(f"   ⏭️  [ISOLATED LIST FIX] Skipping isolated item ending with period (likely text, not header):")
                print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                skipped_after_table_count += 1
            elif ends_with_colon:
                # Isolated item with colon → Should be SECTION_HEADER
                print(f"   🔄 [ISOLATED LIST FIX] Isolated list-item → section-header:")
                print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                item.label = DocItemLabel.SECTION_HEADER
                isolated_count += 1
            else:
                # No strong punctuation hint - keep as list_item
                print(f"   ⏭️  [ISOLATED LIST FIX] Skipping isolated item without colon (no clear header marker):")
                print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                skipped_after_table_count += 1
        else:
            # Part of sequence → Keep as LIST_ITEM
            sequential_count += 1

    if isolated_count > 0:
        print(f"\n✅ [ISOLATED LIST FIX] Reclassified {isolated_count} isolated list-item(s) → section-header")
    if sequential_count > 0:
        print(f"ℹ️  [ISOLATED LIST FIX] Kept {sequential_count} sequential list-item(s) as list-items")
    if skipped_after_table_count > 0:
        print(f"ℹ️  [ISOLATED LIST FIX] Skipped {skipped_after_table_count} isolated item(s) after table/picture (likely captions)")

    if isolated_count == 0 and skipped_after_table_count == 0:
        print(f"\n⚠️  [ISOLATED LIST FIX] No isolated list-items found - all are sequential")

    print("=" * 80 + "\n")

    return isolated_count
