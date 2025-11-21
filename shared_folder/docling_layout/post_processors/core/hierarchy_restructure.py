"""
Hierarchy Restructure Post-Processor

Automatically detects numbering patterns in SECTION_HEADERs and populates
their children[] arrays to reflect semantic hierarchy.

Populates existing children arrays with $ref pointers:
- Does NOT move items
- Does NOT modify body.children structure
- Only ADDS references to existing children[] arrays

Supports common numbering patterns:
- Main chapters: 1., 2., 3.
- Subsections: 1.1, 1.2, 2.1
- Enumerated: a), b), c)
- Sub-enumerated: a., b., c.
- Roman numerals: i., ii., iii.
"""
import re
from docling_core.types.doc import DocItemLabel
import time


# Numbering pattern definitions (ordered by specificity)
HIERARCHY_PATTERNS = [
    # Level 1: Main chapters (1., 2., 10.)
    (r'^\s*(\d+)\.\s+', 1),

    # Level 2: Subsections (1.1, 2.3, 10.2)
    (r'^\s*(\d+)\.(\d+)\s+', 2),

    # Level 3: Sub-subsections (1.1.1, 2.3.4)
    (r'^\s*(\d+)\.(\d+)\.(\d+)\s+', 3),

    # Level 3: Enumerated lowercase with parenthesis (a), b), c))
    (r'^\s*([a-z])\)\s+', 3),

    # Level 4: Sub-enumerated with period (a., b., c.)
    (r'^\s*([a-z])\.\s+', 4),

    # Level 4: Enumerated uppercase (A), B), C))
    (r'^\s*([A-Z])\)\s+', 4),

    # Level 5: Roman numerals lowercase (i., ii., iii.)
    (r'^\s*([ivxlcdm]+)\.\s+', 5),

    # Level 5: Roman numerals uppercase (I., II., III.)
    (r'^\s*([IVXLCDM]+)\.\s+', 5),
]


def detect_header_level(text):
    """
    Detect hierarchy level from section header numbering.

    Args:
        text: Header text (e.g., "1.1 Descripción del evento")

    Returns:
        int: Hierarchy level (1-5), or 0 if no pattern detected
    """
    if not text:
        return 0

    # Try each pattern in order (most specific first)
    for pattern, level in HIERARCHY_PATTERNS:
        if re.match(pattern, text):
            return level

    return 0  # No numbering detected


def extract_numbering(text):
    """
    Extract the numbering portion from header text.

    Args:
        text: Header text (e.g., "1.1 Descripción")

    Returns:
        str: Just the numbering part (e.g., "1.1")
    """
    for pattern, _ in HIERARCHY_PATTERNS:
        match = re.match(pattern, text)
        if match:
            return match.group(0).strip()
    return ""


def apply_hierarchy_restructure_to_document(document):
    """
    Populate children[] arrays in section headers to reflect semantic hierarchy.

    This analyzes numbering patterns in SECTION_HEADER items and populates
    their children arrays with $ref pointers to child items.

    Args:
        document: The Docling document object (result.document)

    Returns:
        int: Number of headers with detected hierarchy
    """
    start_time = time.time()

    print("\n" + "=" * 80)
    print("🌳 [HIERARCHY] Building semantic hierarchy in children[] arrays")
    print("=" * 80)

    # Work with document.texts which contains actual items
    if not hasattr(document, 'texts') or not document.texts:
        print("⚠️  [HIERARCHY] No texts found - skipping restructure")
        print("=" * 80 + "\n")
        return 0

    all_items = list(document.texts)
    print(f"📊 [HIERARCHY] Analyzing {len(all_items)} items...")

    # Step 1: Find all section headers and detect their levels
    headers = []
    for i, item in enumerate(all_items):
        if hasattr(item, 'label') and item.label == DocItemLabel.SECTION_HEADER:
            if hasattr(item, 'text') and item.text:
                level = detect_header_level(item.text)
                if level > 0:
                    headers.append({
                        'index': i,
                        'item': item,
                        'level': level,
                        'numbering': extract_numbering(item.text),
                        'self_ref': f"#/texts/{i}"
                    })

    if not headers:
        print("⚠️  [HIERARCHY] No numbered headers found - skipping restructure")
        print("=" * 80 + "\n")
        return 0

    # Count headers by level
    level_counts = {}
    for h in headers:
        level_counts[h['level']] = level_counts.get(h['level'], 0) + 1

    print(f"🔍 [HIERARCHY] Found {len(headers)} numbered headers:")
    for level in sorted(level_counts.keys()):
        print(f"   Level {level}: {level_counts[level]} headers")

    # Step 2: Build parent-child relationships using a stack
    print("\n🔧 [HIERARCHY] Building parent-child relationships...")

    stack = []  # Stack of (header_info, level) tuples

    for h_idx, header_info in enumerate(headers):
        current_level = header_info['level']
        current_index = header_info['index']

        # Pop stack until we find an appropriate parent (lower level)
        while stack and stack[-1]['level'] >= current_level:
            stack.pop()

        # Determine range of items that belong to this header
        # Items belong to this header if they come after it and before the next header of same/lower level
        start_idx = current_index + 1

        # Find end index (next header of same or lower level, or end of document)
        end_idx = len(all_items)
        for next_h_idx in range(h_idx + 1, len(headers)):
            if headers[next_h_idx]['level'] <= current_level:
                end_idx = headers[next_h_idx]['index']
                break

        # Clear existing children array and populate with new references
        if not hasattr(header_info['item'], 'children'):
            header_info['item'].children = []
        else:
            header_info['item'].children.clear()

        # Add all items in range as children (using $ref format)
        for item_idx in range(start_idx, end_idx):
            ref_dict = {'$ref': f"#/texts/{item_idx}"}
            header_info['item'].children.append(ref_dict)

        # If this header has a parent in stack, add this header as child of parent
        if stack:
            parent = stack[-1]
            # The parent's children should include this header (already added in the range loop above)

        # Push current header to stack - it can be a parent for subsequent headers
        stack.append(header_info)

    elapsed = time.time() - start_time

    # Summary
    total_children = sum(len(h['item'].children) if hasattr(h['item'], 'children') else 0
                        for h in headers)

    print(f"\n✅ [HIERARCHY] Populated {len(headers)} headers with {total_children} child references")
    print(f"⏱️  [HIERARCHY] Processing time: {elapsed:.3f} seconds")
    print("=" * 80 + "\n")

    return len(headers)
