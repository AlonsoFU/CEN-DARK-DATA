#!/usr/bin/env python3
"""
Universal Monkey Patch with Direct PDF Extraction
Handles ALL missing elements that Docling fails to extract

Version: 2.1 (Company Name Detection + Previous Improvements)

📋 COMPLETE LIST OF IMPROVEMENTS:
See: power_line_patch/docs/PATCH_IMPROVEMENTS_CATALOG.md

Quick Summary (11 improvements):
1. LINE-LEVEL TEXT EXTRACTION - Merges spans into complete lines
2. BOX COVERAGE DETECTION - Compares against ALL Docling boxes
3. MISSING TITLE DETECTION - Pattern-based title detection
4. PAGE NUMBER DETECTION - Headers/footers detection
5. COMPANY NAME DETECTION - Chilean company names as section headers (NEW!)
6. POWER LINE CLASSIFICATION - Domain-specific reclassification
7. MISCLASSIFICATION REMOVAL - Corrects AI errors
8. SYNTHETIC CELL CREATION - Makes missing content visible
9. BOUNDING BOX VALIDATION - Quality control
10. POST-PIPELINE INJECTION - Bypasses Docling filtering
11. COORDINATE SYSTEM CONVERSION - Handles different origins

This is the MOST ROBUST solution - it finds elements even if Docling completely
missed them during initial extraction.
"""
import re
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.utils.layout_postprocessor import LayoutPostprocessor
from docling.datamodel.base_models import BoundingBox, Cluster, TextCell
from docling.datamodel.document import DocItemLabel
from docling_core.types.doc.page import BoundingRectangle, ColorRGBA, TextDirection, CoordOrigin

# Import from same package using parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from domain.power_line_classifier import PowerLineClassifier
from core.eaf_title_detector import EAFTitleDetector
from core.eaf_company_name_detector import EAFCompanyNameDetector

# Global variable to store PDF path (set by user)
_PDF_PATH = None

# Global variable to store last cluster from previous page (for cross-page list detection)
_LAST_PAGE_LAST_CLUSTER = None

# Store original method
_original_process_regular = LayoutPostprocessor._process_regular_clusters


def _patched_process_regular_clusters(self):
    """
    Universal patched version with direct PDF extraction

    Strategy:
    1. Extract ALL text from PDF directly (for comparison)
    2. Detect missing titles (e.g., "6.") that Docling didn't cluster
    3. Detect power lines misclassified as titles
    4. Remove misclassified AI clusters
    5. Create NEW clusters with synthetic cells for missing elements
    6. VERIFY all clusters have valid bounding boxes
    7. Merge with existing clusters and call original Docling logic

    Key Insight:
    - We create clusters WITH cells (not empty clusters)
    - Docling will accept these clusters and include them in output
    - This bypasses the "empty cluster removal" in Docling's pipeline
    """

    print("\n" + "=" * 80)
    print("🐵 [PATCH] Universal Fix with Direct PDF Extraction")
    print("=" * 80)

    # ========================================================================
    # STEP 0: Import PyMuPDF and verify PDF path
    # ========================================================================
    try:
        import fitz
    except ImportError:
        print("⚠️  [PATCH] PyMuPDF not available - skipping PDF extraction")
        print("   Install with: pip install PyMuPDF")
        return _original_process_regular(self)

    if _PDF_PATH is None:
        print("⚠️  [PATCH] PDF path not set - skipping PDF extraction")
        print("   Call set_pdf_path() before processing")
        return _original_process_regular(self)

    # ========================================================================
    # STEP 1: Extract ALL text from PDF at LINE level (smarter!)
    # ========================================================================
    try:
        doc = fitz.open(_PDF_PATH)
        pdf_page = doc[self.page.page_no]

        # Get all text blocks from PDF
        pdf_blocks = pdf_page.get_text("dict")["blocks"]

        all_pdf_lines = []
        for block in pdf_blocks:
            if block['type'] == 0:  # Text block
                for line in block.get('lines', []):
                    # Merge all spans on this line into a single text
                    line_text_parts = []
                    line_bbox = None
                    line_font = None
                    line_size = None

                    for span in line.get('spans', []):
                        text = span['text'].strip()
                        if text:
                            line_text_parts.append(text)

                            # Expand line bbox to include this span
                            span_bbox = span['bbox']
                            if line_bbox is None:
                                line_bbox = list(span_bbox)
                            else:
                                line_bbox[0] = min(line_bbox[0], span_bbox[0])  # x0
                                line_bbox[1] = min(line_bbox[1], span_bbox[1])  # y0
                                line_bbox[2] = max(line_bbox[2], span_bbox[2])  # x1
                                line_bbox[3] = max(line_bbox[3], span_bbox[3])  # y1

                            # Use first span's font/size
                            if line_font is None:
                                line_font = span['font']
                                line_size = span['size']

                    # Add complete line
                    if line_text_parts and line_bbox:
                        all_pdf_lines.append({
                            'text': ' '.join(line_text_parts),  # Complete line text!
                            'bbox': {
                                'x0': line_bbox[0],
                                'y0': line_bbox[1],
                                'x1': line_bbox[2],
                                'y1': line_bbox[3]
                            },
                            'size': line_size,
                            'font': line_font
                        })

        print(f"📄 [PATCH] Extracted {len(all_pdf_lines)} text lines from PDF")
        doc.close()

    except Exception as e:
        print(f"⚠️  [PATCH] Error reading PDF: {e}")
        print("   Continuing with Docling's cells only...")
        all_pdf_lines = []

    # ========================================================================
    # STEP 2: Get ALL Docling bboxes (clusters + cells) for comparison
    # ========================================================================
    docling_boxes = []

    # ========================================================================
    # FIX: Replace short title clusters with complete PyMuPDF lines
    # ========================================================================
    # If Docling cluster is a short title like "6.", replace with complete line
    for cluster in self.regular_clusters:
        if hasattr(cluster, 'text') and cluster.text:
            text = cluster.text.strip()

            # Check if short title pattern (e.g., "6.", "a.", "6.1")
            if len(text) <= 5 and ('.' in text or text.isdigit()):
                # Search for matching complete PyMuPDF line
                for pdf_line in all_pdf_lines:
                    pdf_text = pdf_line['text'].strip()

                    # Check if PDF line starts with this short title
                    if pdf_text.startswith(text):
                        # Check position match (same location within 5pts Y, 2pts X)
                        y_diff = abs(cluster.bbox.t - pdf_line['bbox']['y0'])
                        x_diff = abs(cluster.bbox.l - pdf_line['bbox']['x0'])

                        if y_diff <= 5 and x_diff <= 2:
                            print(f"   🔗 [PATCH] Replacing short title cluster with complete PyMuPDF line:")
                            print(f"      Before: '{text}' (width={cluster.bbox.r - cluster.bbox.l:.1f})")
                            print(f"      After: '{pdf_text}' (width={pdf_line['bbox']['x1'] - pdf_line['bbox']['x0']:.1f})")

                            # REPLACE cluster text and bbox with complete line!
                            cluster.text = pdf_text
                            cluster.bbox.l = pdf_line['bbox']['x0']
                            cluster.bbox.t = pdf_line['bbox']['y0']
                            cluster.bbox.r = pdf_line['bbox']['x1']
                            cluster.bbox.b = pdf_line['bbox']['y1']
                            break

    # Add all cluster bboxes
    for cluster in self.regular_clusters:
        if cluster.bbox:
            docling_boxes.append({
                'bbox': {
                    'x0': cluster.bbox.l,
                    'y0': cluster.bbox.t,
                    'x1': cluster.bbox.r,
                    'y1': cluster.bbox.b
                },
                'source': 'cluster',
                'label': cluster.label
            })

    # Add all cell bboxes
    docling_blocks = []
    for cell in self.cells:
        bbox_obj = cell.rect.to_bounding_box()
        bbox_dict = {
            'x0': bbox_obj.l,
            'y0': bbox_obj.t,
            'x1': bbox_obj.r,
            'y1': bbox_obj.b
        }
        docling_boxes.append({
            'bbox': bbox_dict,
            'source': 'cell',
            'text': cell.text
        })
        docling_blocks.append({
            'bbox': bbox_dict,
            'text': cell.text,
            'page': self.page.page_no,
            'cell': cell
        })

    print(f"📊 [PATCH] Docling has {len(docling_boxes)} boxes ({len(self.regular_clusters)} clusters + {len(self.cells)} cells)")

    # ========================================================================
    # STEP 3: Find lines with NO coverage by ANY Docling box
    # ========================================================================
    missing_lines = []

    def bbox_overlap_ratio(bbox1, bbox2):
        """Calculate how much of bbox1 is covered by bbox2"""
        x_left = max(bbox1['x0'], bbox2['x0'])
        x_right = min(bbox1['x1'], bbox2['x1'])
        y_top = max(bbox1['y0'], bbox2['y0'])
        y_bottom = min(bbox1['y1'], bbox2['y1'])

        if x_right < x_left or y_bottom < y_top:
            return 0.0  # No overlap

        intersection = (x_right - x_left) * (y_bottom - y_top)
        bbox1_area = (bbox1['x1'] - bbox1['x0']) * (bbox1['y1'] - bbox1['y0'])

        if bbox1_area == 0:
            return 0.0

        return intersection / bbox1_area

    for pdf_line in all_pdf_lines:
        # Check if this line has significant coverage by ANY Docling box
        max_coverage = 0.0

        for docling_box in docling_boxes:
            coverage = bbox_overlap_ratio(pdf_line['bbox'], docling_box['bbox'])
            max_coverage = max(max_coverage, coverage)

        # DEBUG: Print lines containing "6." to see coverage
        if "6." in pdf_line['text'][:10]:
            print(f"   🔍 DEBUG: Line '{pdf_line['text'][:40]}...' has {max_coverage*100:.1f}% coverage")

        # If less than 50% coverage by any Docling box → it's missing!
        if max_coverage < 0.5:
            missing_lines.append(pdf_line)

    if missing_lines:
        print(f"🔍 [PATCH] Found {len(missing_lines)} text lines that Docling has NO boxes for:")
        for line in missing_lines[:5]:  # Show first 5
            print(f"   - '{line['text'][:60]}...' at ({line['bbox']['x0']:.1f}, {line['bbox']['y0']:.1f})")
        if len(missing_lines) > 5:
            print(f"   ... and {len(missing_lines) - 5} more")

    # ========================================================================
    # STEP 4: Add missing lines to blocks for processing
    # ========================================================================
    # We'll process these as "pseudo-blocks" since we can't modify self.cells directly
    # (Docling's cells are already processed)
    all_blocks = docling_blocks + [
        {
            'bbox': line['bbox'],
            'text': line['text'],
            'page': self.page.page_no,
            'cell': None,  # No Docling cell for this
            'font': line['font'],
            'size': line['size']
        }
        for line in missing_lines
    ]

    print(f"📦 [PATCH] Total blocks to analyze: {len(all_blocks)} ({len(docling_blocks)} Docling + {len(missing_lines)} missing)")

    # ========================================================================
    # STEP 5: Detect Missing Titles (ONLY in missing lines!)
    # ========================================================================
    # FIX: Only check missing_lines to avoid creating duplicate boxes
    # Docling's boxes are the SOURCE OF TRUTH - we only add what's missing
    # ========================================================================
    title_detector = EAFTitleDetector()
    missing_titles = []

    # Check ONLY missing lines for title patterns (not all PDF lines!)
    for pdf_line in missing_lines:
        text = pdf_line['text']
        bbox = pdf_line['bbox']
        page = self.page.page_no

        if title_detector.should_create_cluster(text, bbox, page):
            result = title_detector.is_missing_title(text)
            missing_titles.append({
                'bbox': bbox,
                'text': text,
                'page': page,
                'cell': None,
                'font': pdf_line['font'],
                'size': pdf_line['size'],
                'level': result['level']
            })

    print(f"📝 [PATCH] Found {len(missing_titles)} missing titles (before merging)")
    for title in missing_titles:
        print(f"   ✅ '{title['text']}' (nivel {title['level']})")

    # ========================================================================
    # STEP 5.5: Merge Adjacent Title Blocks (FIX for split titles)
    # ========================================================================
    # Problem: Titles like "6. Normalización del servicio" may be detected as
    # separate blocks ("6." and "Normalización del servicio")
    # Solution: Merge adjacent blocks on the same line into complete titles

    def _merge_adjacent_titles(titles_list):
        """Merge adjacent blocks that form complete titles"""
        if len(titles_list) <= 1:
            return titles_list

        merged = []
        skip_indices = set()

        # Sort by page and y-coordinate for easier adjacency detection
        sorted_titles = sorted(titles_list, key=lambda t: (t['page'], t['bbox']['y0'], t['bbox']['x0']))

        for i, title in enumerate(sorted_titles):
            if i in skip_indices:
                continue

            text = title['text'].strip()

            # Check if this is a short title (just number/letter: "6.", "a.", "6.1")
            is_short_title = len(text) <= 5 and ('.' in text or text.isdigit())

            if not is_short_title:
                merged.append(title)
                continue

            # Look for adjacent continuation block
            found_continuation = False
            for j in range(i + 1, len(sorted_titles)):
                if j in skip_indices:
                    continue

                next_block = sorted_titles[j]

                # Must be on same page
                if title['page'] != next_block['page']:
                    continue

                # Must be on same line (Y coordinates within 5 pts)
                y_diff = abs(title['bbox']['y0'] - next_block['bbox']['y0'])
                if y_diff > 5:
                    continue

                # Must be horizontally adjacent (gap < 20 pts)
                x_gap = next_block['bbox']['x0'] - title['bbox']['x1']
                if x_gap < 0 or x_gap > 20:
                    continue

                # MERGE: Combine text and bbox
                merged_text = text + ' ' + next_block['text'].strip()
                merged_bbox = {
                    'x0': title['bbox']['x0'],
                    'y0': min(title['bbox']['y0'], next_block['bbox']['y0']),
                    'x1': next_block['bbox']['x1'],
                    'y1': max(title['bbox']['y1'], next_block['bbox']['y1'])
                }

                merged.append({
                    **title,  # Keep all other properties
                    'text': merged_text,
                    'bbox': merged_bbox
                })

                skip_indices.add(j)
                found_continuation = True

                print(f"   🔗 [PATCH] Merged adjacent title blocks:")
                print(f"      '{text}' (x0={title['bbox']['x0']:.1f}) + '{next_block['text'].strip()}' (x0={next_block['bbox']['x0']:.1f})")
                print(f"      → '{merged_text}' (width={merged_bbox['x1']-merged_bbox['x0']:.1f} pts)")
                break

            if not found_continuation:
                merged.append(title)

        return merged

    # Apply merging
    missing_titles = _merge_adjacent_titles(missing_titles)
    print(f"📝 [PATCH] After merging: {len(missing_titles)} complete titles")

    # ========================================================================
    # STEP 5.7: Detect Entity Names (companies, orgs, facilities as headers)
    # ========================================================================
    # GENERIC DETECTION - Not country-specific!
    # Uses structural characteristics: capitalization, length, position
    company_detector = EAFCompanyNameDetector()
    company_headers = []

    # Check missing lines for entity names (only those with <50% coverage)
    for pdf_line in missing_lines:
        block = {
            'bbox': pdf_line['bbox'],
            'text': pdf_line['text'],
            'page': self.page.page_no,
            'cell': None,
            'font': pdf_line['font'],
            'size': pdf_line['size']
        }
        text = block['text']
        bbox = block['bbox']
        page = block['page']

        if company_detector.should_create_cluster(text, bbox, page):
            result = company_detector.is_company_name_header(text, bbox)

            # Store detection details
            company_headers.append({
                **block,
                'detection_method': result.get('detection_method', 'generic_structural'),
                'confidence': result.get('confidence', 'medium'),
                'confidence_score': result.get('confidence_score', 0.0),
                'features': result.get('features', {})
            })

    print(f"🏢 [PATCH] Found {len(company_headers)} entity name headers (generic detection)")
    for company in company_headers:
        features = company.get('features', {})
        print(f"   ✅ '{company['text']}' "
              f"(confidence: {company['confidence']}, "
              f"score: {company['confidence_score']:.2f}, "
              f"legal_suffix: {features.get('has_legal_suffix', False)})")

    # ========================================================================
    # STEP 6: Detect Power Lines (ONLY in missing lines, not Docling blocks!)
    # ========================================================================
    power_classifier = PowerLineClassifier()
    power_line_blocks = []

    # BUG FIX: Only check missing_lines for power lines, not all_blocks
    # This prevents creating duplicate clusters for content Docling already has
    for pdf_line in missing_lines:
        block = {
            'bbox': pdf_line['bbox'],
            'text': pdf_line['text'],
            'page': self.page.page_no,
            'cell': None,
            'font': pdf_line['font'],
            'size': pdf_line['size']
        }
        text = block['text']
        if power_classifier.is_power_system_list_item(text):
            power_line_blocks.append(block)

    print(f"⚡ [PATCH] Found {len(power_line_blocks)} power system list items")

    # ========================================================================
    # STEP 7: Identify Misclassified AI Clusters
    # ========================================================================
    misclassified_cluster_ids = set()

    for cluster in self.regular_clusters:
        if cluster.label == DocItemLabel.SECTION_HEADER:
            for power_block in power_line_blocks:
                power_bbox_dict = power_block['bbox']
                power_bbox = BoundingBox(
                    l=power_bbox_dict['x0'],
                    t=power_bbox_dict['y0'],
                    r=power_bbox_dict['x1'],
                    b=power_bbox_dict['y1']
                )

                overlap = cluster.bbox.intersection_over_union(power_bbox)
                if overlap > 0.5:
                    misclassified_cluster_ids.add(cluster.id)
                    print(f"   ❌ [PATCH] AI misclassified power line: {power_block['text'][:60]}...")

    # ========================================================================
    # STEP 8: Remove Misclassified Clusters
    # ========================================================================
    if misclassified_cluster_ids:
        original_count = len(self.regular_clusters)
        self.regular_clusters = [
            c for c in self.regular_clusters
            if c.id not in misclassified_cluster_ids
        ]
        removed_count = original_count - len(self.regular_clusters)
        print(f"   🗑️  [PATCH] Removed {removed_count} misclassified clusters")

    # ========================================================================
    # STEP 9: Create Clusters for Missing Titles
    # ========================================================================
    custom_clusters = []
    next_id = max((c.id for c in self.regular_clusters), default=0) + 1

    for i, title_block in enumerate(missing_titles):
        bbox_dict = title_block['bbox']
        text = title_block['text']

        # ========== FIX: Replace short titles with complete PyMuPDF lines ==========
        # If creating cluster for short title like "6.", replace with complete line
        if len(text.strip()) <= 5 and ('.' in text or text.strip().isdigit()):
            # Search for matching complete PyMuPDF line
            for pdf_line in all_pdf_lines:
                pdf_text = pdf_line['text'].strip()

                # Check if PDF line starts with this short title
                if pdf_text.startswith(text.strip()):
                    # Check position match (same location within 5pts Y, 2pts X)
                    y_diff = abs(bbox_dict['y0'] - pdf_line['bbox']['y0'])
                    x_diff = abs(bbox_dict['x0'] - pdf_line['bbox']['x0'])

                    if y_diff <= 5 and x_diff <= 2:
                        print(f"   🔗 [PATCH] Replacing short title with complete PyMuPDF line:")
                        print(f"      Before: '{text}' (width={bbox_dict['x1'] - bbox_dict['x0']:.1f})")
                        print(f"      After: '{pdf_text}' (width={pdf_line['bbox']['x1'] - pdf_line['bbox']['x0']:.1f})")

                        # REPLACE with complete line!
                        text = pdf_text
                        bbox_dict = pdf_line['bbox']
                        break
        # ===========================================================================

        # VERIFY bbox is valid
        if not _is_valid_bbox(bbox_dict):
            print(f"   ⚠️  [PATCH] Skipping title '{text}' - invalid bbox")
            continue

        # Create BoundingBox
        title_bbox = BoundingBox(
            l=bbox_dict['x0'],
            t=bbox_dict['y0'],
            r=bbox_dict['x1'],
            b=bbox_dict['y1']
        )

        # ========== CHECK FOR DUPLICATE: Skip if Docling already has this content ==========
        # Check if any existing Docling cluster overlaps significantly with this title
        # Check against ALL labels (SECTION_HEADER, LIST_ITEM, TEXT) to avoid partial boxes
        # BUT: For main chapter titles (matches pattern like "6. "), always add them
        #      because Docling sometimes filters them out even though it detected them
        skip_duplicate = False
        import re as regex_module
        is_main_chapter_title = bool(regex_module.match(r'^\d+\.\s+', text))  # Matches "6. ", "7. ", etc.

        if not is_main_chapter_title:  # Only check duplicates for non-chapter titles
            for cluster in self.regular_clusters:
                # Check against ALL labels (not just SECTION_HEADER)
                if cluster.label in [DocItemLabel.SECTION_HEADER, DocItemLabel.LIST_ITEM, DocItemLabel.TEXT]:
                    overlap = cluster.bbox.intersection_over_union(title_bbox)
                    if overlap > 0.5:
                        docling_label = cluster.label.value
                        print(f"   ⚠️  [PATCH] Skipping duplicate (Docling already has it as {docling_label}):")
                        print(f"      '{text[:60]}{'...' if len(text) > 60 else ''}'")
                        print(f"      Overlap: {overlap*100:.1f}%")
                        skip_duplicate = True
                        break
        else:
            print(f"   🎯 [PATCH] Main chapter title detected - forcing add (not checking duplicates):")
            print(f"      '{text[:60]}{'...' if len(text) > 60 else ''}'")

        if skip_duplicate:
            continue
        # ==================================================================================

        # ========== CRITICAL FIX: Always create synthetic cell with corrected text ==========
        # Docling's iterate_items() gets text from cells, not from cluster
        # We must create a new cell with the CORRECTED text (not reuse old "6." cell)
        synthetic_cell = TextCell(
            index=next_id + i,
            rgba=ColorRGBA(r=0, g=0, b=0, a=1.0),  # Black text
            rect=_create_bounding_rectangle(bbox_dict),
            text=text,  # ← Corrected text from replacement!
            orig=text,
            text_direction=TextDirection.LEFT_TO_RIGHT,
            confidence=0.99,
            from_ocr=False
        )
        assigned_cells = [synthetic_cell]
        print(f"   🔧 [PATCH] Created cell for '{text}'")

        # Create cluster WITH CELLS (required for iterate_items to see it!)
        cluster = Cluster(
            id=next_id + i,
            label=DocItemLabel.SECTION_HEADER,
            bbox=title_bbox,
            confidence=0.99,
            cells=assigned_cells  # ← Now guaranteed to have cells!
        )
        custom_clusters.append(cluster)

    print(f"   ✅ [PATCH] Created {len(custom_clusters)} SECTION_HEADER clusters (titles)")

    # ========================================================================
    # STEP 9.5: Create Clusters for Company Name Headers
    # ========================================================================
    next_id = next_id + len(custom_clusters)

    for i, company_block in enumerate(company_headers):
        bbox_dict = company_block['bbox']
        text = company_block['text']

        # VERIFY bbox is valid
        if not _is_valid_bbox(bbox_dict):
            print(f"   ⚠️  [PATCH] Skipping company header '{text}' - invalid bbox")
            continue

        # Create BoundingBox
        company_bbox = BoundingBox(
            l=bbox_dict['x0'],
            t=bbox_dict['y0'],
            r=bbox_dict['x1'],
            b=bbox_dict['y1']
        )

        # ========== CHECK FOR DUPLICATE: Skip if Docling already has this company name ==========
        skip_duplicate = False
        for cluster in self.regular_clusters:
            if cluster.label == DocItemLabel.SECTION_HEADER:
                overlap = cluster.bbox.intersection_over_union(company_bbox)
                if overlap > 0.5:
                    print(f"   ⚠️  [PATCH] Skipping duplicate company name (Docling already has it):")
                    print(f"      '{text[:60]}{'...' if len(text) > 60 else ''}'")
                    print(f"      Overlap: {overlap*100:.1f}%")
                    skip_duplicate = True
                    break

        if skip_duplicate:
            continue
        # ==================================================================================

        # Create synthetic cell for company name
        synthetic_cell = TextCell(
            index=next_id + i,
            rgba=ColorRGBA(r=0, g=0, b=0, a=1.0),
            rect=_create_bounding_rectangle(bbox_dict),
            text=text,
            orig=text,
            text_direction=TextDirection.LEFT_TO_RIGHT,
            confidence=0.95,  # High confidence for company names
            from_ocr=False
        )
        assigned_cells = [synthetic_cell]
        print(f"   🔧 [PATCH] Created cell for company '{text}'")

        # Create cluster WITH CELLS (as section_header)
        cluster = Cluster(
            id=next_id + i,
            label=DocItemLabel.SECTION_HEADER,  # Companies are section headers!
            bbox=company_bbox,
            confidence=0.95,
            cells=assigned_cells
        )
        custom_clusters.append(cluster)

    print(f"   ✅ [PATCH] Created {len(company_headers)} SECTION_HEADER clusters (company names)")

    # ========================================================================
    # STEP 10: Create Clusters for Power Lines
    # ========================================================================
    next_id = next_id + len(custom_clusters)

    for i, power_block in enumerate(power_line_blocks):
        bbox_dict = power_block['bbox']
        text = power_block['text']

        # VERIFY bbox is valid
        if not _is_valid_bbox(bbox_dict):
            print(f"   ⚠️  [PATCH] Skipping power line '{text[:40]}...' - invalid bbox")
            continue

        # Create BoundingBox
        power_bbox = BoundingBox(
            l=bbox_dict['x0'],
            t=bbox_dict['y0'],
            r=bbox_dict['x1'],
            b=bbox_dict['y1']
        )

        # ========== CHECK FOR DUPLICATE: Skip if Docling already has this power line ==========
        skip_duplicate = False
        for cluster in self.regular_clusters:
            if cluster.label == DocItemLabel.LIST_ITEM:
                overlap = cluster.bbox.intersection_over_union(power_bbox)
                if overlap > 0.5:
                    print(f"   ⚠️  [PATCH] Skipping duplicate power line (Docling already has it):")
                    print(f"      '{text[:60]}{'...' if len(text) > 60 else ''}'")
                    print(f"      Overlap: {overlap*100:.1f}%")
                    skip_duplicate = True
                    break

        if skip_duplicate:
            continue
        # ==================================================================================

        # Find overlapping cells
        assigned_cells = []
        if power_block.get('cell') is not None:
            assigned_cells = [power_block['cell']]
        else:
            for cell in self.cells:
                cell_bbox = cell.rect.to_bounding_box()
                overlap = cell_bbox.intersection_over_self(power_bbox)
                if overlap > 0.5:
                    assigned_cells.append(cell)

        # ========== CRITICAL FIX: Create synthetic cell if no cells found ==========
        if not assigned_cells:
            synthetic_cell = TextCell(
                index=next_id + i,
                rgba=ColorRGBA(r=0, g=0, b=0, a=1.0),  # Black text
                rect=_create_bounding_rectangle(bbox_dict),
                text=text,  # ← Text from PyMuPDF!
                orig=text,
                text_direction=TextDirection.LEFT_TO_RIGHT,
                confidence=0.98,
                from_ocr=False
            )
            assigned_cells = [synthetic_cell]
            print(f"   🔧 [PATCH] Created synthetic cell for power line '{text[:40]}...'")

        # Create cluster WITH CELLS
        cluster = Cluster(
            id=next_id + i,
            label=DocItemLabel.LIST_ITEM,
            bbox=power_bbox,
            confidence=0.98,
            cells=assigned_cells  # ← Now guaranteed to have cells!
        )
        custom_clusters.append(cluster)

    total_power_clusters = len(power_line_blocks)
    print(f"   ✅ [PATCH] Created {total_power_clusters} LIST_ITEM clusters")

    # ========================================================================
    # STEP 11: VERIFY All Clusters Have Valid Bounding Boxes
    # ========================================================================
    valid_clusters = []
    invalid_count = 0

    for cluster in custom_clusters:
        if cluster.bbox is not None:
            # Check bbox has valid dimensions
            bbox = cluster.bbox
            if hasattr(bbox, 'l') and hasattr(bbox, 't') and hasattr(bbox, 'r') and hasattr(bbox, 'b'):
                if bbox.r > bbox.l and bbox.b > bbox.t:
                    valid_clusters.append(cluster)
                else:
                    invalid_count += 1
            else:
                invalid_count += 1
        else:
            invalid_count += 1

    if invalid_count > 0:
        print(f"   ⚠️  [PATCH] Discarded {invalid_count} clusters with invalid bboxes")

    # ========================================================================
    # STEP 12: Get Docling's Processed Clusters FIRST
    # ========================================================================
    # Call original method to let Docling process its clusters normally
    docling_clusters = _original_process_regular(self)

    print(f"📊 [PATCH] Docling processed: {len(docling_clusters)} clusters")

    # ========================================================================
    # POST-PROCESS: Fix Zona classification based on sequential list detection
    # ========================================================================
    # Rule: If a list-item is ISOLATED (not followed by another list), it's actually a HEADER
    # Rule: If 2+ list-items appear sequentially, they ARE list-items
    import re
    zona_pattern = re.compile(r'^[·•]?\s*Zona\s+.+?\s+-\s+Área\s+.+', re.IGNORECASE)

    # Step 1: Find all Zona items and mark which ones have sequential neighbors
    zona_items = []
    for i, cluster in enumerate(docling_clusters):
        if hasattr(cluster, 'label') and hasattr(cluster, 'text') and cluster.text:
            text = cluster.text.strip()

            if zona_pattern.match(text):
                zona_items.append({
                    'index': i,
                    'cluster': cluster,
                    'text': text,
                    'original_label': cluster.label
                })

    # Step 2: Determine which Zona items are part of sequential groups (2+ items)
    for i, item in enumerate(zona_items):
        has_next_neighbor = (i + 1 < len(zona_items) and
                            zona_items[i + 1]['index'] - item['index'] <= 3)  # Within 3 positions
        has_prev_neighbor = (i > 0 and
                            item['index'] - zona_items[i - 1]['index'] <= 3)

        item['is_sequential'] = has_next_neighbor or has_prev_neighbor

    # Step 3: Apply reclassification based on sequential detection
    reclassified_to_header = 0
    reclassified_to_list = 0

    for item in zona_items:
        cluster = item['cluster']
        text = item['text']

        if item['is_sequential']:
            # Part of a sequence (2+ items) → Should be LIST_ITEM
            if cluster.label != DocItemLabel.LIST_ITEM:
                print(f"   🔄 [PATCH] Sequential item → list-item:")
                print(f"      '{text[:60]}{'...' if len(text) > 60 else ''}'")
                cluster.label = DocItemLabel.LIST_ITEM
                reclassified_to_list += 1

            # Ensure it has a bullet
            if not text.startswith(('·', '•')):
                print(f"   📝 [PATCH] Adding bullet to sequential list-item:")
                print(f"      '{text[:50]}...'")
                cluster.text = f"• {text}"
        else:
            # Isolated item → Should be SECTION_HEADER
            if cluster.label != DocItemLabel.SECTION_HEADER:
                print(f"   🔄 [PATCH] Isolated item → section-header:")
                print(f"      '{text[:60]}{'...' if len(text) > 60 else ''}'")
                cluster.label = DocItemLabel.SECTION_HEADER
                reclassified_to_header += 1

    if reclassified_to_header > 0:
        print(f"✅ [PATCH] Reclassified {reclassified_to_header} isolated item(s) to section-header")
    if reclassified_to_list > 0:
        print(f"✅ [PATCH] Reclassified {reclassified_to_list} sequential item(s) to list-item")

    # ========================================================================
    # POST-PROCESS: Reclassify Company Names (TEXT → SECTION_HEADER)
    # ========================================================================
    # This runs AFTER clusters have text, so we can check content
    # Example: "AR Pampa SpA." classified as TEXT should be SECTION_HEADER

    company_detector = EAFCompanyNameDetector()
    company_reclassification_log = []

    for cluster in docling_clusters:
        if hasattr(cluster, 'label') and hasattr(cluster, 'text') and cluster.text:
            # Only check TEXT clusters (potential misclassifications)
            if cluster.label == DocItemLabel.TEXT:
                text = cluster.text.strip()

                # Skip empty or very short text
                if not text or len(text) < 5:
                    continue

                # Run company name detection
                detection = company_detector.is_company_name_header(text)

                if detection.get('is_company_header'):
                    # RECLASSIFY: Change label from TEXT to SECTION_HEADER
                    old_label = cluster.label
                    cluster.label = DocItemLabel.SECTION_HEADER

                    # Log the change
                    company_reclassification_log.append({
                        'text': text,
                        'old_label': old_label.value,
                        'new_label': DocItemLabel.SECTION_HEADER.value,
                        'confidence': detection.get('confidence'),
                        'score': detection.get('confidence_score'),
                        'features': detection.get('features', {})
                    })

    if len(company_reclassification_log) > 0:
        print(f"✅ [PATCH] Reclassified {len(company_reclassification_log)} company name(s) (TEXT → SECTION_HEADER)")
        for item in company_reclassification_log:
            features = item.get('features', {})
            print(f"   ✏️  '{item['text'][:60]}' "
                  f"(confidence: {item['confidence']}, "
                  f"score: {item['score']:.2f}, "
                  f"legal_suffix: {features.get('has_legal_suffix', False)})")

    # ========================================================================
    # Note: Short company name reclassification moved to post-processor
    # (enumerated_item_fix.py) because clusters don't have text at this stage
    # ========================================================================

    print(f"📊 [PATCH] Adding from patch: {len(valid_clusters)} clusters")

    # ========================================================================
    # STEP 12.5: Fix Isolated List-Items in Docling's Clusters
    # ========================================================================
    # Run BEFORE combining with patch clusters
    # Detect isolated list-items on THIS PAGE and reclassify as section headers
    # INCLUDES CROSS-PAGE DETECTION: Check if first item connects to previous page's last item

    global _LAST_PAGE_LAST_CLUSTER

    print("\n" + "=" * 80)
    print("🔍 [PATCH] Detecting Isolated List Items (with cross-page detection)")
    print("=" * 80)

    # Helper function to detect marker type
    def get_marker_type(text, cluster):
        """Returns 'bullet' or 'enumerated' based on marker"""
        # Check cluster marker attribute if available
        marker = getattr(cluster, 'marker', '')
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

    # Step 1: Find all LIST_ITEM clusters in Docling's output
    list_items = []
    for i, cluster in enumerate(docling_clusters):
        if hasattr(cluster, 'label') and cluster.label == DocItemLabel.LIST_ITEM:
            text = cluster.text.strip() if hasattr(cluster, 'text') and cluster.text else '(no text)'
            marker_type = get_marker_type(text, cluster)
            list_items.append({
                'index': i,
                'cluster': cluster,
                'text': text,
                'marker_type': marker_type
            })

    print(f"📋 [PATCH] Found {len(list_items)} list-items on this page")

    # Check cross-page connection
    # Only connect if markers match (same list type)
    first_item_connects_to_prev_page = False
    if len(list_items) > 0 and _LAST_PAGE_LAST_CLUSTER is not None:
        # Check if previous page's last cluster was a list-item
        if hasattr(_LAST_PAGE_LAST_CLUSTER, 'label') and _LAST_PAGE_LAST_CLUSTER.label == DocItemLabel.LIST_ITEM:
            # Compare markers - only connect if they match
            prev_text = _LAST_PAGE_LAST_CLUSTER.text.strip() if hasattr(_LAST_PAGE_LAST_CLUSTER, 'text') and _LAST_PAGE_LAST_CLUSTER.text else ''
            prev_marker_type = get_marker_type(prev_text, _LAST_PAGE_LAST_CLUSTER)
            first_marker_type = list_items[0]['marker_type']

            if prev_marker_type == first_marker_type:
                # Markers match - can connect
                first_item_connects_to_prev_page = True
                print(f"🔗 [PATCH] Cross-page connection: Markers match ({prev_marker_type}), connecting lists")
            else:
                # Markers don't match - different lists
                print(f"⏭️  [PATCH] Cross-page skip: Different markers ({prev_marker_type} vs {first_marker_type}), not connecting")

    if len(list_items) > 0:
        # Step 2: Determine which are isolated vs sequential
        # Different rules for bullets vs enumerated:
        # - Bullets (-, •, *, ·): must be adjacent (distance = 1)
        # - Enumerated (a), b), 1), 2)): can have gaps (distance ≤ 3)
        for i, item in enumerate(list_items):
            marker_type = item['marker_type']
            max_distance = 1 if marker_type == 'bullet' else 3

            # Check next neighbor
            has_next_neighbor = False
            if i + 1 < len(list_items):
                distance = list_items[i + 1]['index'] - item['index']
                has_next_neighbor = distance <= max_distance

            # Check previous neighbor (within this page OR cross-page for first item)
            has_prev_neighbor = False
            if i == 0:
                # First item: check cross-page connection
                has_prev_neighbor = first_item_connects_to_prev_page
            else:
                # Not first item: check within this page
                distance = item['index'] - list_items[i - 1]['index']
                has_prev_neighbor = distance <= max_distance

            item['is_sequential'] = has_next_neighbor or has_prev_neighbor

        # Step 3: Reclassify isolated items to SECTION_HEADER
        # BUT skip if item appears after table/picture OR doesn't end with punctuation
        isolated_count = 0
        sequential_count = 0
        skipped_after_table_count = 0

        for item in list_items:
            cluster = item['cluster']
            text = item['text']
            index = item['index']

            if not item['is_sequential']:
                # Check if previous cluster is a table or picture
                is_after_table_or_picture = False
                if index > 0:
                    prev_cluster = docling_clusters[index - 1]
                    if hasattr(prev_cluster, 'label') and prev_cluster.label in [DocItemLabel.TABLE, DocItemLabel.PICTURE]:
                        is_after_table_or_picture = True

                # Check punctuation:
                # - Headers typically end with ':' (colon)
                # - Items ending with '.' (period) are LESS likely to be headers
                ends_with_colon = text.endswith(':')
                ends_with_period = text.endswith('.')

                if is_after_table_or_picture:
                    # Skip conversion - likely a caption or note
                    print(f"   ⏭️  [PATCH] Skipping isolated item after table/picture (likely caption):")
                    print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                    skipped_after_table_count += 1
                elif ends_with_period:
                    # Skip conversion - ends with period, less likely to be header
                    print(f"   ⏭️  [PATCH] Skipping isolated item ending with period (likely text, not header):")
                    print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                    skipped_after_table_count += 1
                elif ends_with_colon:
                    # Isolated item with colon → Should be SECTION_HEADER
                    print(f"   🔄 [PATCH] Isolated list-item → section-header:")
                    print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                    cluster.label = DocItemLabel.SECTION_HEADER
                    isolated_count += 1
                else:
                    # No strong punctuation hint - keep as list_item
                    print(f"   ⏭️  [PATCH] Skipping isolated item without colon (no clear header marker):")
                    print(f"      '{text[:70]}{'...' if len(text) > 70 else ''}'")
                    skipped_after_table_count += 1
            else:
                # Part of sequence → Keep as LIST_ITEM
                sequential_count += 1

        if isolated_count > 0:
            print(f"\n✅ [PATCH] Reclassified {isolated_count} isolated list-item(s) → section-header")
        if sequential_count > 0:
            print(f"ℹ️  [PATCH] Kept {sequential_count} sequential list-item(s) as list-items")
        if skipped_after_table_count > 0:
            print(f"ℹ️  [PATCH] Skipped {skipped_after_table_count} isolated item(s) after table/picture or without punctuation")
    else:
        print("⚠️  [PATCH] No list-items found on this page")

    print("=" * 80 + "\n")

    # ========================================================================
    # STEP 13: Combine Docling's Clusters (now with fixed list-items) with Our Custom Clusters
    # ========================================================================
    # Note: Smart enumerated item reclassification has been moved to post-processor
    # (enumerated_item_fix.py) because clusters don't have text populated at this stage
    # ========================================================================
    # Add our clusters AFTER Docling's processing to bypass filtering
    final_clusters = docling_clusters + valid_clusters

    print(f"📊 [PATCH] Total final clusters: {len(final_clusters)}")

    # ========================================================================
    # STEP 14: Save last cluster for next page's cross-page detection
    # ========================================================================
    # Note: global declaration already at top of function
    if len(final_clusters) > 0:
        _LAST_PAGE_LAST_CLUSTER = final_clusters[-1]
    else:
        _LAST_PAGE_LAST_CLUSTER = None

    print("=" * 80 + "\n")

    return final_clusters


def _create_bounding_rectangle(bbox_dict):
    """
    Create a BoundingRectangle from a bbox dict

    BoundingRectangle requires 4 corners (r_x0-r_x3, r_y0-r_y3) representing
    a rotated rectangle. For axis-aligned rectangles, we set the corners as:
    - (r_x0, r_y0): top-left
    - (r_x1, r_y1): top-right
    - (r_x2, r_y2): bottom-right
    - (r_x3, r_y3): bottom-left

    PyMuPDF uses TOP-LEFT origin (y increases downward)
    Docling expects TOP-LEFT origin for consistency with existing cells

    Args:
        bbox_dict: dict with x0, y0, x1, y1 (axis-aligned bbox from PyMuPDF)

    Returns:
        BoundingRectangle with all required fields
    """
    x0 = bbox_dict['x0']
    y0 = bbox_dict['y0']
    x1 = bbox_dict['x1']
    y1 = bbox_dict['y1']

    return BoundingRectangle(
        # Top-left corner
        r_x0=x0,
        r_y0=y0,
        # Top-right corner
        r_x1=x1,
        r_y1=y0,
        # Bottom-right corner
        r_x2=x1,
        r_y2=y1,
        # Bottom-left corner
        r_x3=x0,
        r_y3=y1,
        # Coordinate origin - MUST match Docling's existing cells!
        coord_origin=CoordOrigin.TOPLEFT  # PyMuPDF uses top-left, Docling expects this
    )


def _is_valid_bbox(bbox_dict):
    """
    Verify bounding box is valid

    Args:
        bbox_dict: dict with x0, y0, x1, y1

    Returns:
        bool: True if valid
    """
    try:
        x0 = float(bbox_dict['x0'])
        y0 = float(bbox_dict['y0'])
        x1 = float(bbox_dict['x1'])
        y1 = float(bbox_dict['y1'])

        # Check values are finite
        if not all(isinstance(v, (int, float)) and not (v != v) for v in [x0, y0, x1, y1]):
            return False

        # Check dimensions are positive
        if x1 <= x0 or y1 <= y0:
            return False

        # Check values are reasonable (not too large)
        if any(abs(v) > 10000 for v in [x0, y0, x1, y1]):
            return False

        return True

    except (KeyError, TypeError, ValueError):
        return False


# ============================================================================
# APPLY MONKEY PATCH
# ============================================================================

def set_pdf_path(pdf_path):
    """
    Set the PDF path for the patch to use

    MUST be called before using DocumentConverter!

    Also resets cross-page state for new document.

    Args:
        pdf_path: Path to PDF file
    """
    global _PDF_PATH, _LAST_PAGE_LAST_CLUSTER
    _PDF_PATH = str(pdf_path)
    _LAST_PAGE_LAST_CLUSTER = None  # Reset cross-page state for new document
    print(f"📄 [PATCH] PDF path set: {pdf_path}")


def apply_universal_patch_with_pdf(pdf_path):
    """
    Apply the universal patch with PDF extraction

    Args:
        pdf_path: Path to PDF file to process
    """
    print("\n🔧 Applying universal patch with PDF extraction...")
    set_pdf_path(pdf_path)
    LayoutPostprocessor._process_regular_clusters = _patched_process_regular_clusters
    print("✅ Universal patch applied successfully\n")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║     UNIVERSAL DOCLING PATCH WITH PDF EXTRACTION                    ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║                                                                    ║
    ║  The MOST ROBUST solution for Docling extraction issues:          ║
    ║                                                                    ║
    ║  1. EXTRACTS MISSING CELLS FROM PDF                                ║
    ║     - Bypasses Docling's cell extraction                           ║
    ║     - Finds text Docling completely missed                         ║
    ║     - Direct PyMuPDF extraction                                    ║
    ║                                                                    ║
    ║  2. DETECTS MISSING TITLES                                         ║
    ║     - "6.", "a.", "6.1", etc.                                      ║
    ║     - Pattern-based detection                                      ║
    ║     - Works even if Docling never saw them                         ║
    ║                                                                    ║
    ║  3. FIXES POWER LINE MISCLASSIFICATION                             ║
    ║     - "Línea 220 kV..." → list_item                                ║
    ║     - Domain-specific rules                                        ║
    ║                                                                    ║
    ║  4. VERIFIES ALL BOUNDING BOXES                                    ║
    ║     - Checks bbox validity before creating clusters                ║
    ║     - Discards invalid/malformed boxes                             ║
    ║     - Ensures downstream pipeline won't crash                      ║
    ║                                                                    ║
    ║  Usage:                                                            ║
    ║    from universal_patch_with_pdf_extraction import \\              ║
    ║        apply_universal_patch_with_pdf                              ║
    ║                                                                    ║
    ║    # MUST set PDF path before converting                           ║
    ║    apply_universal_patch_with_pdf("document.pdf")                  ║
    ║                                                                    ║
    ║    # Now use Docling normally                                      ║
    ║    from docling.document_converter import DocumentConverter        ║
    ║    converter = DocumentConverter()                                 ║
    ║    result = converter.convert("document.pdf")                      ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)


# ============================================================================
# POST-PROCESSORS (Document-Level Fixes)
# ============================================================================
# POST-PROCESSORS
# These run AFTER Docling completes extraction
# They are now in a separate module: post_processors/
# Called from EXTRACT_ANY_CHAPTER.py, not from this monkey patch engine
# ============================================================================
