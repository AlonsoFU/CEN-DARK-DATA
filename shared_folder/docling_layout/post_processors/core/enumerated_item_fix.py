"""
Enumerated Item Smart Reclassification Post-Processor

Intelligently reclassifies enumerated items (a), b), c) or a. b. c.) based on:
1. Text length (>200 chars → always LIST_ITEM)
2. Alphabetical sequence (a→b→c → LIST_ITEM)
3. Isolated + short → SECTION_HEADER

Also reclassifies short company names with legal suffixes to SECTION_HEADER.

This runs AFTER Docling completes extraction (document-level processing).
"""
import re
from docling_core.types.doc import DocItemLabel


def apply_enumerated_item_fix_to_document(document):
    """
    Apply smart enumerated item reclassification at document level.

    Args:
        document: The Docling document object (result.document)

    Returns:
        Number of items reclassified
    """
    print("\n" + "=" * 80)
    print("🧠 [SMART RECLASS] Smart Enumerated Item Reclassification")
    print("=" * 80)

    # ========================================================================
    # PART 1: Reclassify short company names with legal suffixes
    # ========================================================================

    legal_suffixes = [
        r'S\.A\.',  # Sociedad Anónima
        r'S\.p\.A\.',  # Sociedad por Acciones
        r'Ltda\.',  # Limitada
        r'SpA\.',  # Sociedad por Acciones (sin puntos)
        r'Inc\.',  # Incorporated
        r'Corp\.',  # Corporation
        r'LLC',  # Limited Liability Company
    ]
    suffix_pattern = re.compile(r'(' + '|'.join(legal_suffixes) + r')', re.IGNORECASE)

    # Collect all items (including tables, pictures, etc. that don't have text)
    # We need ALL items to properly detect context (e.g., isolated list after table)
    all_items = []
    for item, level in document.iterate_items():
        if hasattr(item, 'label'):
            all_items.append(item)

    print(f"📊 [SMART RECLASS] Analyzing {len(all_items)} document items...")

    # Fix company names
    company_fixes = 0
    for item in all_items:
        if item.label == DocItemLabel.TEXT:
            text = item.text.strip()
            # Short text (<50 chars) with legal suffix
            if len(text) < 50 and suffix_pattern.search(text):
                print(f"   🔄 [SMART RECLASS] Company name TEXT → SECTION_HEADER: '{text}'")
                item.label = DocItemLabel.SECTION_HEADER
                company_fixes += 1

    if company_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Reclassified {company_fixes} company name(s) → SECTION_HEADER")
    else:
        print(f"ℹ️  [SMART RECLASS] No company names to reclassify")

    # ========================================================================
    # PART 2: Reclassify bullet point items ("-" prefix)
    # ========================================================================

    # Pattern for bullet points: "-Text" or "- Text"
    bullet_pattern = re.compile(r'^-\s*\S+')

    # Find all bullet point items
    bullet_items = []
    for i, item in enumerate(all_items):
        if item.label in [DocItemLabel.SECTION_HEADER, DocItemLabel.TEXT]:
            text = item.text.strip()
            if bullet_pattern.match(text):
                bullet_items.append({
                    'index': i,
                    'item': item
                })

    # Reclassify bullet points in sequences
    bullet_fixes = 0
    if len(bullet_items) >= 2:  # At least 2 items in sequence
        for bullet_item in bullet_items:
            item = bullet_item['item']
            if item.label != DocItemLabel.LIST_ITEM:
                print(f"   🔄 [SMART RECLASS] Bullet point {item.label.value} → LIST_ITEM:")
                print(f"      Text: '{item.text[:70]}{'...' if len(item.text) > 70 else ''}'")
                item.label = DocItemLabel.LIST_ITEM
                bullet_fixes += 1

    if bullet_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Reclassified {bullet_fixes} bullet point(s) → LIST_ITEM")

    # ========================================================================
    # PART 3: Reclassify summary captions to text
    # ========================================================================

    # Pattern for summary lines: "Total:", "Totales:", "Suma:", etc.
    summary_pattern = re.compile(r'^(Total|Totales|Suma|Resumen)[:.\s]', re.IGNORECASE)

    caption_fixes = 0
    for item in all_items:
        if item.label == DocItemLabel.CAPTION:
            text = item.text.strip()
            if summary_pattern.match(text):
                print(f"   🔄 [SMART RECLASS] Summary CAPTION → TEXT:")
                print(f"      Text: '{text[:70]}{'...' if len(text) > 70 else ''}'")
                item.label = DocItemLabel.TEXT
                caption_fixes += 1

    if caption_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Reclassified {caption_fixes} summary caption(s) → TEXT")

    # ========================================================================
    # PART 4: Reclassify isolated power line items to section_header
    # ========================================================================

    # Pattern for power lines: "Línea XXX kV..."
    power_line_pattern = re.compile(r'^Línea\s+\d+.*kV', re.IGNORECASE)

    # Find all list_item that match power line pattern
    power_line_items = []
    for i, item in enumerate(all_items):
        if item.label == DocItemLabel.LIST_ITEM:
            text = item.text.strip()
            if power_line_pattern.match(text):
                power_line_items.append({
                    'index': i,
                    'item': item,
                    'text': text
                })

    # Check if isolated (no other list_item within 5 positions before/after)
    line_fixes = 0
    for power_item in power_line_items:
        idx = power_item['index']

        # Check if isolated: no other list_item nearby
        has_nearby_list = False
        for j in range(max(0, idx - 5), min(len(all_items), idx + 6)):
            if j != idx and all_items[j].label == DocItemLabel.LIST_ITEM:
                # Check if nearby item is also a power line
                nearby_text = all_items[j].text.strip()
                if not power_line_pattern.match(nearby_text):
                    has_nearby_list = True
                    break

        # If isolated, reclassify to section_header
        if not has_nearby_list:
            item = power_item['item']
            text = power_item['text']
            print(f"   🔄 [SMART RECLASS] Isolated power line LIST_ITEM → SECTION_HEADER:")
            print(f"      Text: '{text[:70]}{'...' if len(text) > 70 else ''}'")
            item.label = DocItemLabel.SECTION_HEADER
            line_fixes += 1

    if line_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Reclassified {line_fixes} isolated power line(s) → SECTION_HEADER")

    # ========================================================================
    # PART 5: Smart reclassification of enumerated items
    # ========================================================================

    # Pattern for enumerated items: "a.", "b." OR "a)", "b)"
    enum_pattern = re.compile(r'^\s*([a-z])[\.\)]\s+', re.IGNORECASE)

    # Find all enumerated items
    enum_items = []
    for i, item in enumerate(all_items):
        if item.label in [DocItemLabel.LIST_ITEM, DocItemLabel.SECTION_HEADER]:
            text = item.text.strip()

            # Check 1: Marker in text (regex)
            match = enum_pattern.match(text)

            # Check 2: Marker in property (Docling stores it separately)
            marker_prop = getattr(item, 'marker', None)
            marker_match = re.match(r'^([a-z])[\.\)]$', marker_prop, re.IGNORECASE) if marker_prop else None

            marker = None
            if match:
                marker = match.group(1).lower()
            elif marker_match:
                marker = marker_match.group(1).lower()

            if marker:
                enum_items.append({
                    'index': i,
                    'item': item,
                    'text': text,
                    'length': len(text),
                    'marker': marker,
                    'original_label': item.label
                })

    print(f"\n🔍 [SMART RECLASS] Found {len(enum_items)} enumerated items (a), b), or a., b., ...)")

    if len(enum_items) == 0:
        print("⚠️  [SMART RECLASS] No enumerated items found")
        total_enum_fixes = 0
        # Skip PART 5 enumeration logic, continue to PART 6 and PART 7
    else:
            # STEP 1: Group items into sequences
        sequences = []
        processed = set()
    
        for i, enum_item in enumerate(enum_items):
            if i in processed:
                continue
    
            # Start a new sequence
            sequence = [i]
            marker = enum_item['marker']
    
            # Look forward for consecutive markers
            current_marker = marker
            for j in range(i + 1, len(enum_items)):
                next_expected = chr(ord(current_marker) + 1)
                if enum_items[j]['marker'] == next_expected:
                    if enum_items[j]['index'] - enum_items[sequence[-1]]['index'] <= 10:
                        sequence.append(j)
                        current_marker = next_expected
                        processed.add(j)
    
            sequences.append(sequence)
            processed.add(i)
    
        # STEP 2: Analyze each sequence and apply smart reclassification
        reclassified_to_list = 0
        reclassified_to_header = 0
    
        for sequence in sequences:
            # Calculate sequence properties
            sequence_items = [enum_items[idx] for idx in sequence]
            max_length = max(item['length'] for item in sequence_items)
            all_short = all(item['length'] < 100 for item in sequence_items)
            is_isolated = len(sequence) == 1
    
            # Check if sequence is isolated from OTHER list_items (not in this sequence)
            sequence_indices = set(item['index'] for item in sequence_items)
            has_external_list_items = False
    
            for seq_item in sequence_items:
                seq_idx = seq_item['index']
                # Check within 5 positions
                for j in range(max(0, seq_idx - 5), min(len(all_items), seq_idx + 6)):
                    if j not in sequence_indices and all_items[j].label == DocItemLabel.LIST_ITEM:
                        has_external_list_items = True
                        break
                if has_external_list_items:
                    break
    
            # Decision logic:
            # 0. If sequence is isolated from OTHER list_items → ALL SECTION_HEADER
            if not has_external_list_items and not is_isolated:
                # Sequence isolated from other list content → subsection titles
                desired_label = DocItemLabel.SECTION_HEADER
                reason = f"isolated enumerated sequence ({len(sequence)} items, no external list_items nearby)"
            # 1. ANY item >200 chars → ALL LIST_ITEM (detailed list content)
            elif max_length > 200:
                # At least one long item → all are list items
                desired_label = DocItemLabel.LIST_ITEM
                reason = f"sequence with long content (max {max_length} chars)"
            elif not is_isolated and all_short:
                # Sequence of short items → subsection titles
                desired_label = DocItemLabel.SECTION_HEADER
                reason = f"short subsection titles (all <100 chars, sequence of {len(sequence)})"
            elif not is_isolated:
                # Sequence with medium-length items (100-200 chars)
                desired_label = DocItemLabel.LIST_ITEM
                reason = f"sequence of medium-length items (max {max_length} chars)"
            elif max_length > 200:
                # Isolated long item
                desired_label = DocItemLabel.LIST_ITEM
                reason = f"long isolated item ({max_length} chars)"
            else:
                # Isolated short item
                desired_label = DocItemLabel.SECTION_HEADER
                reason = f"short isolated item ({max_length} chars)"
    
            # Apply the classification to all items in the sequence
            for idx in sequence:
                enum_item = enum_items[idx]
                item = enum_item['item']
                text = enum_item['text']
                length = enum_item['length']
                marker = enum_item['marker']
                current_label = item.label
    
                if current_label != desired_label:
                    old_label_name = "SECTION_HEADER" if current_label == DocItemLabel.SECTION_HEADER else "LIST_ITEM"
                    new_label_name = "SECTION_HEADER" if desired_label == DocItemLabel.SECTION_HEADER else "LIST_ITEM"
    
                    print(f"   🔄 [SMART RECLASS] {old_label_name} → {new_label_name}:")
                    print(f"      Marker: '{marker})' | Length: {length} chars")
                    print(f"      Reason: {reason}")
                    print(f"      Text: '{text[:70]}{'...' if len(text) > 70 else ''}'")
    
                    item.label = desired_label
    
                    if desired_label == DocItemLabel.LIST_ITEM:
                        reclassified_to_list += 1
                    else:
                        reclassified_to_header += 1
    
        total_enum_fixes = reclassified_to_list + reclassified_to_header
        if total_enum_fixes > 0:
            print(f"\n✅ [SMART RECLASS] Reclassified {reclassified_to_list} item(s) → LIST_ITEM")
            print(f"✅ [SMART RECLASS] Reclassified {reclassified_to_header} item(s) → SECTION_HEADER")
        else:
            print(f"\n⚠️  [SMART RECLASS] No enumerated items needed reclassification")
    
    # ========================================================================
    # PART 6: Reclassify isolated list_item to section_header
    # ========================================================================

    # Pattern for enumerated items (reuse from PART 5)
    enum_pattern = re.compile(r'^\s*([a-z])[\.\)]\s+', re.IGNORECASE)

    # Helper function to detect marker type
    def get_marker_type(text, item):
        """Returns 'bullet' or 'enumerated' based on marker"""
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

    # Find all list_item that are truly isolated (text → list_item → text)
    isolated_list_fixes = 0
    processed_sequences = set()

    for i, item in enumerate(all_items):
        if i in processed_sequences or item.label != DocItemLabel.LIST_ITEM:
            continue

        text = item.text.strip()

        # Detect marker type: bullets must be adjacent (distance=1), enumerated can have gaps (distance=3)
        marker_type = get_marker_type(text, item)
        max_distance = 1 if marker_type == 'bullet' else 3

        # Check if truly isolated: no other list_item within max_distance positions
        has_nearby_list = False
        for j in range(max(0, i - max_distance), min(len(all_items), i + max_distance + 1)):
            if j != i and all_items[j].label == DocItemLabel.LIST_ITEM:
                has_nearby_list = True
                break

        # ONLY if truly isolated (text → list_item → text)
        if not has_nearby_list:
                # EXCEPTION: If previous element is a SECTION_HEADER, keep as list_item (don't convert to section_header)
                # A section_header followed by list_item is a common structure (header + list of items)
                # Skip page_footer/page_header to find the actual previous content item
                prev_is_section_header = False
                if i > 0:
                    # Look backward skipping page_footer and page_header
                    for j in range(i - 1, -1, -1):
                        prev_item = all_items[j]
                        # Skip furniture items (page headers/footers)
                        if prev_item.label in [DocItemLabel.PAGE_FOOTER, DocItemLabel.PAGE_HEADER]:
                            continue
                        # Found a content item - check if it's a section_header
                        prev_is_section_header = prev_item.label == DocItemLabel.SECTION_HEADER
                        break

                # EXCEPTION to the exception: If current item is a "Zona ... Área ..." pattern,
                # DO NOT apply section_header protection (these are always section headers, not list items)
                # Zona patterns like "Zona Norte Grande - Área Centro" are geographical section titles
                zona_pattern = re.compile(r'^[·•]?\s*Zona\s+.+?\s+-\s+Área\s+.+', re.IGNORECASE)
                is_zona_pattern = zona_pattern.match(text)

                if prev_is_section_header and not is_zona_pattern:
                    print(f"   ⏭️  [SMART RECLASS] Skipping isolated list after SECTION_HEADER (keeping as list_item):")
                    print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                    continue

                # Check if it's an enumerated item (a), b), c))
                # Check both: marker in text AND marker property
                match = enum_pattern.match(text)
                marker_prop = getattr(item, 'marker', None)
                marker_match = re.match(r'^([a-z])[\.\)]$', marker_prop, re.IGNORECASE) if marker_prop else None

                marker = None
                if match:
                    marker = match.group(1).lower()
                elif marker_match:
                    marker = marker_match.group(1).lower()

                if marker:
                    # It's enumerated! Find the full sequence (a, b, c)
                    sequence_items = [(i, item, marker)]

                    # Search backward for earlier markers (if this is c, find b and a)
                    current_marker = marker
                    for j in range(i - 1, max(0, i - 15), -1):
                        if all_items[j].label == DocItemLabel.LIST_ITEM:
                            prev_text = all_items[j].text.strip()
                            prev_match = enum_pattern.match(prev_text)
                            prev_marker_prop = getattr(all_items[j], 'marker', None)
                            prev_marker_match = re.match(r'^([a-z])[\.\)]$', prev_marker_prop, re.IGNORECASE) if prev_marker_prop else None

                            prev_marker = None
                            if prev_match:
                                prev_marker = prev_match.group(1).lower()
                            elif prev_marker_match:
                                prev_marker = prev_marker_match.group(1).lower()

                            if prev_marker:
                                expected_prev = chr(ord(current_marker) - 1)
                                if prev_marker == expected_prev:
                                    sequence_items.insert(0, (j, all_items[j], prev_marker))
                                    current_marker = prev_marker

                    # Search forward for later markers (if this is a, find b and c)
                    current_marker = marker
                    for j in range(i + 1, min(len(all_items), i + 15)):
                        if all_items[j].label == DocItemLabel.LIST_ITEM:
                            next_text = all_items[j].text.strip()
                            next_match = enum_pattern.match(next_text)
                            next_marker_prop = getattr(all_items[j], 'marker', None)
                            next_marker_match = re.match(r'^([a-z])[\.\)]$', next_marker_prop, re.IGNORECASE) if next_marker_prop else None

                            next_marker = None
                            if next_match:
                                next_marker = next_match.group(1).lower()
                            elif next_marker_match:
                                next_marker = next_marker_match.group(1).lower()

                            if next_marker:
                                expected_next = chr(ord(current_marker) + 1)
                                if next_marker == expected_next:
                                    sequence_items.append((j, all_items[j], next_marker))
                                    current_marker = next_marker

                    # Reclassify ALL items in the sequence to section_header
                    print(f"   🔄 [SMART RECLASS] Enumerated sequence (isolated) → SECTION_HEADER:")
                    for idx, seq_item, seq_marker in sequence_items:
                        seq_text = seq_item.text.strip()
                        print(f"      {seq_marker}) '{seq_text[:60]}{'...' if len(seq_text) > 60 else ''}'")
                        seq_item.label = DocItemLabel.SECTION_HEADER
                        processed_sequences.add(idx)
                        isolated_list_fixes += 1
                else:
                    # Not enumerated, just a single isolated bullet item

                    # RULE: Don't convert to SECTION_HEADER if ends with period
                    # EXCEPTION: Allow conversion if ends with company legal suffixes (S.A., C.I., Ltda., etc.)
                    company_suffixes = ['S.A.', 'S. A.', 'C.I.', 'C. I.', 'Ltda.', 'S.R.L.', 'S. R. L.', 'Inc.', 'Corp.', 'Ltd.']
                    ends_with_period = text.endswith('.')
                    ends_with_company_suffix = any(text.upper().endswith(suffix.upper()) for suffix in company_suffixes)

                    # Skip conversion if ends with regular period (not company suffix)
                    if ends_with_period and not ends_with_company_suffix:
                        print(f"   ⏭️  [SMART RECLASS] Skipping isolated list ending with period (keeping as list_item):")
                        print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                        continue

                    # RULE: Don't convert to SECTION_HEADER if contains conjugated verbs
                    # Titles are NOMINAL (nouns), content has VERBS
                    # Detect reflexive verbs (se + verb) and common verbs
                    text_lower = text.lower()
                    verb_patterns = [
                        r'\bse\s+\w+(e|a|en|an|ó|ió|aba|ía)\b',  # se concluye, se presume, se determina
                        r'\b(hay|existe|resulta|muestra|indica|alcanza|alcanzó)\b',  # common verbs
                        r'\bno\s+(hay|se|existe|cuenta|dispone)\b',  # negations
                    ]

                    has_verb = any(re.search(pattern, text_lower) for pattern in verb_patterns)

                    if has_verb:
                        print(f"   ⏭️  [SMART RECLASS] Skipping isolated list with conjugated verb (keeping as list_item):")
                        print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                        continue

                    # Otherwise convert to section_header
                    print(f"   🔄 [SMART RECLASS] Isolated LIST_ITEM → SECTION_HEADER (isolated bullet):")
                    print(f"      Text: '{text[:70]}{'...' if len(text) > 70 else ''}'")
                    print(f"      Length: {len(text)} chars")
                    item.label = DocItemLabel.SECTION_HEADER
                    isolated_list_fixes += 1


    if isolated_list_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Reclassified {isolated_list_fixes} isolated list_item(s) → SECTION_HEADER")

    print("=" * 80 + "\n")

    # ============================================================================
    # PART 6.5: Reclassify ALL list_items with title pattern (not just isolated)
    # ============================================================================
    print("=" * 80)
    print("PART 6.5: Reclassifying ALL list_items with title pattern...")
    print("=" * 80)

    # Pattern 1: Geographic/structural titles (requires dash)
    # Examples: "Zona Norte - Área 1", "Sistema A - Central B"
    title_pattern_with_dash = re.compile(
        r'^[−•\*·\-]?\s*(Zona|Área|Sistema|Central|Subestación|S/E)\s+.+\s+-\s+',
        re.IGNORECASE
    )

    # Pattern 2: Electrical infrastructure (requires voltage)
    # Examples: "Barras 220 kV del sistema", "Línea 110 kV Calama"
    infrastructure_pattern = re.compile(
        r'^[−•\*·\-]?\s*(Barra|Barras|Línea|Líneas)\s+\d+.*kV',
        re.IGNORECASE
    )

    title_pattern_fixes = 0

    for i, item in enumerate(all_items):
        if item.label == DocItemLabel.LIST_ITEM:
            text = item.text.strip()

            # Check both patterns
            matches_title = title_pattern_with_dash.match(text)
            matches_infrastructure = infrastructure_pattern.match(text)

            if matches_title or matches_infrastructure:
                pattern_type = "title" if matches_title else "infrastructure"
                print(f"   🔄 [SMART RECLASS] {pattern_type.capitalize()} pattern LIST_ITEM → SECTION_HEADER:")
                print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                item.label = DocItemLabel.SECTION_HEADER
                title_pattern_fixes += 1

    if title_pattern_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Reclassified {title_pattern_fixes} list_item(s) with title pattern → SECTION_HEADER")

    print("=" * 80 + "\n")

    # ============================================================================
    # PART 7: Cross-Page Continuation Fix
    # ============================================================================
    print("=" * 80)
    print("PART 7: Detecting cross-page continuations...")
    print("=" * 80)

    continuation_fixes = 0

    for i in range(1, len(all_items)):
        current_item = all_items[i]
        prev_item = all_items[i - 1]

        # Get page numbers
        current_prov = getattr(current_item, 'prov', [])
        prev_prov = getattr(prev_item, 'prov', [])

        if not current_prov or not prev_prov:
            continue

        current_page = current_prov[0].page_no if hasattr(current_prov[0], 'page_no') else 0
        prev_page = prev_prov[0].page_no if hasattr(prev_prov[0], 'page_no') else 0

        # Check if this is first item on a new page
        if current_page != prev_page and current_page == prev_page + 1:
            # Skip if current item is a header - don't treat headers as continuations
            if current_item.label in [DocItemLabel.SECTION_HEADER, DocItemLabel.PAGE_HEADER]:
                continue

            # If previous item is a page footer, check the item before that
            check_item = prev_item
            if prev_item.label == DocItemLabel.PAGE_FOOTER and i >= 2:
                check_item = all_items[i - 2]

            # Skip if either item doesn't have text (e.g., tables, pictures)
            if not hasattr(check_item, 'text') or not check_item.text:
                continue
            if not hasattr(current_item, 'text') or not current_item.text:
                continue

            # Check if the item to check doesn't end with period
            check_text = check_item.text.strip()
            current_text = current_item.text.strip()

            # Skip continuation if current item starts with a bullet marker
            # Bullets should NOT be continuations (they start new list items)
            current_starts_with_bullet = current_text and current_text[0] in ['-', '•', '*', '·']

            # Check if current text starts with lowercase letter
            # This is a STRONG signal of continuation (mid-sentence)
            current_starts_lowercase = current_text and current_text[0].islower()

            # Cross-page continuation rules:
            # ONLY apply continuation if there are STRONG signals

            # STRONG signal: Current starts with lowercase (clearly mid-sentence)
            # This is the PRIMARY indicator of continuation
            is_strong_continuation = current_starts_lowercase

            # WEAK signal: Previous doesn't end with period
            # But this alone is NOT enough if current starts with uppercase

            # Apply continuation ONLY if:
            # 1. Current starts with lowercase (STRONG signal), OR
            # 2. Previous doesn't end with period AND current is same type (both list_item, both text, etc)

            prev_label = check_item.label
            current_label = current_item.label
            same_type = prev_label == current_label

            # For now, ONLY apply if starts with lowercase
            # This is the safest and most reliable signal
            should_apply_continuation = is_strong_continuation

            if check_text and not check_text.endswith('.') and not current_starts_with_bullet and should_apply_continuation:
                # This looks like a continuation!
                # Copy classification from the item we checked
                old_label = current_item.label
                new_label = check_item.label

                if old_label != new_label:
                    check_prov = getattr(check_item, 'prov', [])
                    check_page = check_prov[0].page_no if check_prov and hasattr(check_prov[0], 'page_no') else 0
                    print(f"   🔄 [SMART RECLASS] Cross-page continuation {old_label} → {new_label}:")
                    print(f"      Prev page {check_page}: '{check_text[-60:]}' (no period)")
                    print(f"      Page {current_page}: '{current_text[:70]}{'...' if len(current_text) > 70 else ''}'")
                    current_item.label = new_label
                    continuation_fixes += 1

    if continuation_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Fixed {continuation_fixes} cross-page continuation(s)")

    print("=" * 80 + "\n")

    # ============================================================================
    # PART 8: Convert chapter title PAGE_HEADER to SECTION_HEADER
    # ============================================================================
    print("=" * 80)
    print("PART 8: Converting chapter title PAGE_HEADER → SECTION_HEADER...")
    print("=" * 80)

    header_fixes = 0

    # Pattern for chapter and section titles:
    # - Main chapters: "1. Title", "6. Normalización" → ^\d+\.\s+\w
    # - Subsections: "d.3 Reiteración", "a.1 Title" → ^[a-z]\.\d+\s+\w
    chapter_title_pattern = re.compile(r'^(\d+\.\s+\w|[a-z]\.\d+\s+\w)')

    # Try accessing document.texts (which is what gets exported to JSON)
    if hasattr(document, 'texts') and document.texts:
        print(f"   Checking document.texts ({len(document.texts)} items)...")
        for item in document.texts:
            if hasattr(item, 'label') and item.label == DocItemLabel.PAGE_HEADER:
                if hasattr(item, 'text') and item.text:
                    item_text = item.text.strip()
                    # Only convert if it looks like a chapter title
                    if chapter_title_pattern.match(item_text):
                        print(f"   🔄 [SMART RECLASS] PAGE_HEADER → SECTION_HEADER: '{item_text[:70]}{'...' if len(item_text) > 70 else ''}'")
                        item.label = DocItemLabel.SECTION_HEADER
                        header_fixes += 1
    else:
        print("   ⚠️  document.texts not available")

    # Also check furniture layer
    if hasattr(document, 'furniture') and document.furniture:
        print(f"   Checking furniture layer...")
        furniture_items = []
        if hasattr(document.furniture, 'children'):
            furniture_items = document.furniture.children
        elif hasattr(document.furniture, '__iter__'):
            furniture_items = list(document.furniture)

        for item in furniture_items:
            if hasattr(item, 'label') and item.label == DocItemLabel.PAGE_HEADER:
                if hasattr(item, 'text') and item.text:
                    item_text = item.text.strip()
                    # Only convert if it looks like a chapter title
                    if chapter_title_pattern.match(item_text):
                        print(f"   🔄 [SMART RECLASS] PAGE_HEADER → SECTION_HEADER (furniture): '{item_text[:70]}{'...' if len(item_text) > 70 else ''}'")
                        item.label = DocItemLabel.SECTION_HEADER
                        header_fixes += 1

    # Also check if any PAGE_HEADER slipped into main content
    for item in all_items:
        if item.label == DocItemLabel.PAGE_HEADER:
            item_text = item.text.strip()
            # Only convert if it looks like a chapter title
            if chapter_title_pattern.match(item_text):
                print(f"   🔄 [SMART RECLASS] PAGE_HEADER → SECTION_HEADER (body): '{item_text[:70]}{'...' if len(item_text) > 70 else ''}'")
                item.label = DocItemLabel.SECTION_HEADER
                header_fixes += 1

    if header_fixes > 0:
        print(f"\n✅ [SMART RECLASS] Converted {header_fixes} chapter title PAGE_HEADER(s) to SECTION_HEADER")
    else:
        print("   ℹ️  No chapter title PAGE_HEADER items found")

    print("=" * 80 + "\n")

    # ============================================================================
    # PART 9: Zona Classification Fix
    # ============================================================================
    print("=" * 80)
    print("PART 9: Reclassifying 'Zona ... - Área ...' patterns...")
    print("=" * 80)

    zona_pattern = re.compile(r'^[·•]?\s*Zona\s+.+?\s+-\s+Área\s+.+', re.IGNORECASE)

    # Step 1: Find all Zona items
    zona_items = []
    for i, item in enumerate(all_items):
        if not hasattr(item, 'text') or not item.text:
            continue
        text = item.text.strip()
        if zona_pattern.match(text):
            zona_items.append({
                'index': i,
                'item': item,
                'text': text,
                'original_label': item.label
            })

    print(f"🔍 [SMART RECLASS] Found {len(zona_items)} Zona items in document")

    zona_fixes = 0

    if len(zona_items) > 0:
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
                    print(f"   🔄 [SMART RECLASS] Sequential Zona → list-item: '{text[:60]}{'...' if len(text) > 60 else ''}'")
                    item.label = DocItemLabel.LIST_ITEM
                    reclassified_to_list += 1

                # Ensure it has a bullet
                if not text.startswith(('·', '•')):
                    print(f"   📝 [SMART RECLASS] Adding bullet to Zona: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                    item.text = f"• {text}"
            else:
                # Isolated item → Should be SECTION_HEADER
                if item.label != DocItemLabel.SECTION_HEADER:
                    print(f"   🔄 [SMART RECLASS] Isolated Zona → section-header: '{text[:60]}{'...' if len(text) > 60 else ''}'")
                    item.label = DocItemLabel.SECTION_HEADER
                    reclassified_to_header += 1

        zona_fixes = reclassified_to_header + reclassified_to_list

        if zona_fixes > 0:
            print(f"\n✅ [SMART RECLASS] Reclassified {reclassified_to_header} isolated Zona → section-header")
            print(f"✅ [SMART RECLASS] Reclassified {reclassified_to_list} sequential Zona → list-item")
        else:
            print(f"\n⚠️  [SMART RECLASS] No Zona reclassification needed - all items already correct")
    else:
        print("⚠️  [SMART RECLASS] No Zona items found - skipping fix")

    print("=" * 80 + "\n")

    return company_fixes + bullet_fixes + caption_fixes + line_fixes + total_enum_fixes + isolated_list_fixes + continuation_fixes + header_fixes + zona_fixes
