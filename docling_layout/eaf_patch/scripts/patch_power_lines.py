#!/usr/bin/env python3
"""
Monkey Patch for Power Line Classification
Fixes Docling's inconsistent classification of power system list items

Problem:
    Lines like "• Línea 220 kV Cerro Dominador - Sierra Gorda" are sometimes
    classified as section_header instead of list_item (inconsistent)

Solution:
    Inject domain-specific rules to force correct classification:
    1. Detect power line patterns
    2. Remove any SECTION_HEADER clusters that match power lines
    3. Create LIST_ITEM clusters for them instead
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


# Store original method
_original_process_regular = LayoutPostprocessor._process_regular_clusters


def _patched_process_regular_clusters(self):
    """
    Patched version that fixes power line classification

    Strategy:
    1. Run custom detectors (titles + power lines)
    2. Identify misclassified power lines in AI clusters
    3. Remove AI's incorrect SECTION_HEADER clusters for power lines
    4. Create correct LIST_ITEM clusters for power lines
    5. Merge everything and call original Docling logic
    """

    print("\n" + "=" * 80)
    print("🐵 [PATCH] Power Line Classification Fix")
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
            'cell': cell  # Keep reference for later
        })

    # ========================================================================
    # STEP 2: Run Power Line Classifier
    # ========================================================================
    print(f"📊 [PATCH] Analyzing {len(page_blocks)} text blocks for power line patterns...")

    classifier = PowerLineClassifier()
    power_line_blocks = []

    for block in page_blocks:
        text = block['text']
        if classifier.is_power_system_list_item(text):
            power_line_blocks.append(block)

    print(f"⚡ [PATCH] Found {len(power_line_blocks)} power system list items")

    # ========================================================================
    # STEP 3: Identify Misclassified AI Clusters
    # ========================================================================
    # Check if AI classified any power lines as SECTION_HEADER
    misclassified_cluster_ids = set()

    for cluster in self.regular_clusters:
        if cluster.label == DocItemLabel.SECTION_HEADER:
            # Check if this cluster overlaps with power line blocks
            for power_block in power_line_blocks:
                power_bbox_dict = power_block['bbox']
                power_bbox = BoundingBox(
                    l=power_bbox_dict['x0'],
                    t=power_bbox_dict['y0'],
                    r=power_bbox_dict['x1'],
                    b=power_bbox_dict['y1']
                )

                # Check overlap
                overlap = cluster.bbox.intersection_over_union(power_bbox)
                if overlap > 0.5:
                    # AI wrongly classified this as SECTION_HEADER!
                    misclassified_cluster_ids.add(cluster.id)
                    print(f"   ❌ [PATCH] AI misclassified as SECTION_HEADER: {power_block['text'][:60]}...")

    # ========================================================================
    # STEP 4: Remove Misclassified Clusters
    # ========================================================================
    if misclassified_cluster_ids:
        original_count = len(self.regular_clusters)
        self.regular_clusters = [
            c for c in self.regular_clusters
            if c.id not in misclassified_cluster_ids
        ]
        removed_count = original_count - len(self.regular_clusters)
        print(f"   🗑️  [PATCH] Removed {removed_count} misclassified SECTION_HEADER clusters")

    # ========================================================================
    # STEP 5: Create Correct LIST_ITEM Clusters for Power Lines
    # ========================================================================
    custom_clusters = []
    next_id = max((c.id for c in self.regular_clusters), default=0) + 1

    for i, power_block in enumerate(power_line_blocks):
        bbox_dict = power_block['bbox']

        # Create BoundingBox
        custom_bbox = BoundingBox(
            l=bbox_dict['x0'],
            t=bbox_dict['y0'],
            r=bbox_dict['x1'],
            b=bbox_dict['y1']
        )

        # Find overlapping cells
        assigned_cells = []
        for cell in self.cells:
            cell_bbox = cell.rect.to_bounding_box()
            overlap = cell_bbox.intersection_over_self(custom_bbox)
            if overlap > 0.5:
                assigned_cells.append(cell)

        # Only create cluster if it has cells
        if assigned_cells:
            cluster = Cluster(
                id=next_id + i,
                label=DocItemLabel.LIST_ITEM,  # ← Correct classification!
                bbox=custom_bbox,
                confidence=0.98,  # High confidence (domain rule)
                cells=assigned_cells
            )
            custom_clusters.append(cluster)

    print(f"   ✅ [PATCH] Created {len(custom_clusters)} LIST_ITEM clusters for power lines")

    # ========================================================================
    # STEP 6: Optionally Add Custom Title Detection
    # ========================================================================
    # You can also add DetailedHeadingDetector here if needed
    # For now, focusing only on power line classification

    # ========================================================================
    # STEP 7: Merge Custom Clusters
    # ========================================================================
    self.regular_clusters.extend(custom_clusters)

    print(f"📊 [PATCH] Total clusters: {len(self.regular_clusters)}")
    print("=" * 80 + "\n")

    # ========================================================================
    # STEP 8: Call Original Docling Method
    # ========================================================================
    return _original_process_regular(self)


# ============================================================================
# APPLY MONKEY PATCH
# ============================================================================

def apply_power_line_patch():
    """Apply the power line classification patch"""
    print("\n🔧 Applying power line classification patch...")
    LayoutPostprocessor._process_regular_clusters = _patched_process_regular_clusters
    print("✅ Power line patch applied successfully\n")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    """
    Example usage:

    from patch_power_lines import apply_power_line_patch

    # Apply patch BEFORE creating DocumentConverter
    apply_power_line_patch()

    # Now use Docling normally
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert("document.pdf")

    # Power lines will now be consistently classified as list_item!
    """
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║           POWER LINE CLASSIFICATION PATCH                          ║
    ╠════════════════════════════════════════════════════════════════════╣
    ║                                                                    ║
    ║  This patch fixes Docling's inconsistent classification of         ║
    ║  power transmission lines.                                         ║
    ║                                                                    ║
    ║  Problem:                                                          ║
    ║    • Línea 220 kV Cerro Dominador - Sierra Gorda                  ║
    ║    Sometimes: section_header ❌                                    ║
    ║    Sometimes: list_item ✅                                         ║
    ║                                                                    ║
    ║  Solution:                                                         ║
    ║    Domain-specific rules force consistent LIST_ITEM classification ║
    ║                                                                    ║
    ║  Usage:                                                            ║
    ║    from patch_power_lines import apply_power_line_patch           ║
    ║    apply_power_line_patch()                                       ║
    ║    # Now use Docling normally                                     ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
