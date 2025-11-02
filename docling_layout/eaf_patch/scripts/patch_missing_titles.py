#!/usr/bin/env python3
"""
Universal Monkey Patch for Missing Titles and Power Lines
Combines both fixes into a single comprehensive patch

Fixes:
1. Missing titles that Docling's AI fails to detect (e.g., "6.", "a.")
2. Power line misclassifications (section_header → list_item)

Usage:
    from patch_missing_titles import apply_universal_patch
    apply_universal_patch()
    # Now use Docling normally
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from docling.utils.layout_postprocessor import LayoutPostprocessor
from docling.datamodel.base_models import BoundingBox, Cluster
from docling.datamodel.document import DocItemLabel
from power_line_classifier import PowerLineClassifier
from missing_title_detector import MissingTitleDetector


# Store original method
_original_process_regular = LayoutPostprocessor._process_regular_clusters


def _patched_process_regular_clusters(self):
    """
    Universal patched version that fixes:
    1. Missing titles
    2. Power line misclassifications

    Strategy:
    1. Detect missing titles in cells
    2. Detect power lines in cells
    3. Remove misclassified AI clusters
    4. Create correct clusters for both
    5. Merge and call original Docling logic
    """

    print("\n" + "=" * 80)
    print("🐵 [PATCH] Universal Fix: Missing Titles + Power Lines")
    print("=" * 80)

    # ========================================================================
    # STEP 1: Convert cells to blocks
    # ========================================================================
    page_blocks = []
    for cell in self.cells:
        bbox_obj = cell.rect.to_bounding_box()
        page_blocks.append({
            'bbox': {
                'x0': bbox_obj.l,
                'y0': bbox_obj.t,
                'x1': bbox_obj.r,
                'y1': bbox_obj.b
            },
            'text': cell.text,
            'page': self.page.page_no,
            'cell': cell  # Keep reference
        })

    print(f"📊 [PATCH] Analyzing {len(page_blocks)} text blocks...")

    # ========================================================================
    # STEP 2: Detect Missing Titles
    # ========================================================================
    title_detector = MissingTitleDetector()
    missing_titles = []

    for block in page_blocks:
        text = block['text']
        bbox = block['bbox']
        page = block['page']

        if title_detector.should_create_cluster(text, bbox, page):
            result = title_detector.is_missing_title(text)
            missing_titles.append({
                **block,
                'level': result['level']
            })

    print(f"📝 [PATCH] Found {len(missing_titles)} missing titles")
    for title in missing_titles:
        print(f"   ✅ '{title['text']}' (nivel {title['level']})")

    # ========================================================================
    # STEP 3: Detect Power Lines
    # ========================================================================
    power_classifier = PowerLineClassifier()
    power_line_blocks = []

    for block in page_blocks:
        text = block['text']
        if power_classifier.is_power_system_list_item(text):
            power_line_blocks.append(block)

    print(f"⚡ [PATCH] Found {len(power_line_blocks)} power system list items")

    # ========================================================================
    # STEP 4: Identify Misclassified AI Clusters
    # ========================================================================
    misclassified_cluster_ids = set()

    # Check for wrongly classified power lines
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
    # STEP 5: Remove Misclassified Clusters
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
    # STEP 6: Create Clusters for Missing Titles
    # ========================================================================
    custom_clusters = []
    next_id = max((c.id for c in self.regular_clusters), default=0) + 1

    for i, title_block in enumerate(missing_titles):
        bbox_dict = title_block['bbox']

        # Create BoundingBox
        title_bbox = BoundingBox(
            l=bbox_dict['x0'],
            t=bbox_dict['y0'],
            r=bbox_dict['x1'],
            b=bbox_dict['y1']
        )

        # Find overlapping cells
        assigned_cells = []
        for cell in self.cells:
            cell_bbox = cell.rect.to_bounding_box()
            overlap = cell_bbox.intersection_over_self(title_bbox)
            if overlap > 0.5:
                assigned_cells.append(cell)

        if assigned_cells:
            cluster = Cluster(
                id=next_id + i,
                label=DocItemLabel.SECTION_HEADER,  # Titles are section headers
                bbox=title_bbox,
                confidence=0.99,  # Very high confidence (domain rule)
                cells=assigned_cells
            )
            custom_clusters.append(cluster)

    print(f"   ✅ [PATCH] Created {len(custom_clusters)} SECTION_HEADER clusters for missing titles")

    # ========================================================================
    # STEP 7: Create Clusters for Power Lines
    # ========================================================================
    next_id = next_id + len(custom_clusters)

    for i, power_block in enumerate(power_line_blocks):
        bbox_dict = power_block['bbox']

        # Create BoundingBox
        power_bbox = BoundingBox(
            l=bbox_dict['x0'],
            t=bbox_dict['y0'],
            r=bbox_dict['x1'],
            b=bbox_dict['y1']
        )

        # Find overlapping cells
        assigned_cells = []
        for cell in self.cells:
            cell_bbox = cell.rect.to_bounding_box()
            overlap = cell_bbox.intersection_over_self(power_bbox)
            if overlap > 0.5:
                assigned_cells.append(cell)

        if assigned_cells:
            cluster = Cluster(
                id=next_id + i,
                label=DocItemLabel.LIST_ITEM,  # Power lines are list items
                bbox=power_bbox,
                confidence=0.98,  # High confidence (domain rule)
                cells=assigned_cells
            )
            custom_clusters.append(cluster)

    print(f"   ✅ [PATCH] Created {len(power_line_blocks)} LIST_ITEM clusters for power lines")

    # ========================================================================
    # STEP 8: Merge Custom Clusters
    # ========================================================================
    self.regular_clusters.extend(custom_clusters)

    print(f"📊 [PATCH] Total clusters: {len(self.regular_clusters)} (+{len(custom_clusters)} from patch)")
    print("=" * 80 + "\n")

    # ========================================================================
    # STEP 9: Call Original Docling Method
    # ========================================================================
    return _original_process_regular(self)


# ============================================================================
# APPLY MONKEY PATCH
# ============================================================================

def apply_universal_patch():
    """Apply the universal patch (missing titles + power lines)"""
    print("\n🔧 Applying universal patch (missing titles + power lines)...")
    LayoutPostprocessor._process_regular_clusters = _patched_process_regular_clusters
    print("✅ Universal patch applied successfully\n")


def apply_missing_titles_only():
    """Apply only the missing titles patch (no power lines)"""
    # Create a simpler version that only handles titles
    # (You can implement this if needed)
    pass


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║           UNIVERSAL DOCLING PATCH                                  ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║                                                                    ║
    ║  Fixes two common Docling issues:                                 ║
    ║                                                                    ║
    ║  1. MISSING TITLES                                                 ║
    ║     Problem: "6.", "a.", "6.1" not detected by AI                 ║
    ║     Solution: Pattern-based title detection                       ║
    ║                                                                    ║
    ║  2. POWER LINE MISCLASSIFICATION                                  ║
    ║     Problem: "Línea 220 kV..." classified as section_header       ║
    ║     Solution: Force list_item classification                      ║
    ║                                                                    ║
    ║  Usage:                                                            ║
    ║    from patch_missing_titles import apply_universal_patch         ║
    ║    apply_universal_patch()                                        ║
    ║    # Now use Docling normally                                     ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
