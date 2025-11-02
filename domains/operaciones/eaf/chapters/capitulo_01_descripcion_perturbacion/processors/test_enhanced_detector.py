"""
Test Enhanced Table Detector
Demonstrates how enhanced detection captures multi-line cells
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from smart_content_classifier import SmartContentClassifier, ContentType
from enhanced_table_detector import patch_smart_classifier


def test_comparison():
    """Compare original vs enhanced detection."""

    # Path: processors/ -> capitulo_01/ -> chapters/ -> eaf/ (then go to shared/source/)
    pdf_path = Path(__file__).parent.parent.parent.parent / "shared" / "source" / "EAF-089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return

    print("🔬 TESTING ENHANCED TABLE DETECTOR")
    print("=" * 80)
    print(f"📄 PDF: {pdf_path.name}")
    print("=" * 80)

    # Test page 1 (has the problematic multi-line cells)
    test_page = 1

    print(f"\n{'='*80}")
    print("1️⃣  ORIGINAL DETECTOR (without enhancement)")
    print(f"{'='*80}")

    # Original classifier
    classifier_original = SmartContentClassifier(str(pdf_path))
    blocks_original = classifier_original.classify_page_content(test_page)

    # Find table
    table_original = None
    for block in blocks_original:
        if block.type == ContentType.TABLE:
            table_original = block
            break

    if table_original:
        print(f"\n📊 Table found:")
        print(f"   Rows: {table_original.content['row_count']}")
        print(f"   Cols: {table_original.content['col_count']}")

        print(f"\n   First 15 rows (showing potential issues):")
        for i, row in enumerate(table_original.content['data'][:15], 1):
            # Join columns with →
            row_str = " → ".join(cell[:50] if cell else "" for cell in row[:2])
            # Highlight short rows that might be missing data
            if len(row[1]) < 20 and row[1]:
                print(f"   ⚠️  Row {i:2d}: {row_str}")
            else:
                print(f"      Row {i:2d}: {row_str}")
    else:
        print("❌ No table found!")

    print(f"\n{'='*80}")
    print("2️⃣  ENHANCED DETECTOR (with continuation row detection)")
    print(f"{'='*80}")

    # Enhanced classifier
    classifier_enhanced = SmartContentClassifier(str(pdf_path))
    patch_smart_classifier(classifier_enhanced)
    blocks_enhanced = classifier_enhanced.classify_page_content(test_page)

    # Find table
    table_enhanced = None
    for block in blocks_enhanced:
        if block.type == ContentType.TABLE:
            table_enhanced = block
            break

    if table_enhanced:
        print(f"\n📊 Table found:")
        print(f"   Rows: {table_enhanced.content['row_count']}")
        print(f"   Cols: {table_enhanced.content['col_count']}")

        print(f"\n   First 15 rows:")
        for i, row in enumerate(table_enhanced.content['data'][:15], 1):
            row_str = " → ".join(cell[:70] if cell else "" for cell in row[:2])
            # Highlight rows that look complete
            if len(row[1]) > 50:
                print(f"   ✅ Row {i:2d}: {row_str}")
            else:
                print(f"      Row {i:2d}: {row_str}")
    else:
        print("❌ No table found!")

    print(f"\n{'='*80}")
    print("📈 COMPARISON")
    print(f"{'='*80}")

    if table_original and table_enhanced:
        orig_rows = table_original.content['row_count']
        enh_rows = table_enhanced.content['row_count']

        print(f"   Original rows:  {orig_rows}")
        print(f"   Enhanced rows:  {enh_rows}")
        print(f"   Difference:     {orig_rows - enh_rows} (continuation rows merged)")

        # Check specific problematic row (row 10 - "Nombre de la instalación")
        if orig_rows >= 10 and enh_rows >= 10:
            print(f"\n   🔍 Checking Row 10 (Nombre de la instalación):")
            print(f"\n   Original:")
            print(f"      Campo: {table_original.content['data'][9][0]}")
            print(f"      Valor: {table_original.content['data'][9][1][:80]}...")

            print(f"\n   Enhanced:")
            print(f"      Campo: {table_enhanced.content['data'][9][0]}")
            print(f"      Valor: {table_enhanced.content['data'][9][1][:80]}...")

            # Check length difference
            orig_len = len(table_original.content['data'][9][1])
            enh_len = len(table_enhanced.content['data'][9][1])

            if enh_len > orig_len:
                print(f"\n   ✅ Enhanced version captured {enh_len - orig_len} more characters!")
            else:
                print(f"\n   ⚠️  No improvement detected")


def save_enhanced_output():
    """Save enhanced extraction to JSON."""

    pdf_path = Path(__file__).parent.parent.parent.parent.parent.parent / \
               "anexos_eaf" / "shared" / "data" / "EAF 089-2025.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF not found")
        return

    print(f"\n{'='*80}")
    print("💾 SAVING ENHANCED EXTRACTION")
    print(f"{'='*80}")

    # Enhanced classifier
    classifier = SmartContentClassifier(str(pdf_path))
    patch_smart_classifier(classifier)

    # Process pages 1-11
    result = {
        "document_metadata": {
            "eaf_number": "089/2025",
            "document_title": "Estudio para análisis de falla EAF 089/2025",
            "processing_method": "enhanced_table_detection"
        },
        "entities": [],
        "extraction_timestamp": datetime.now().isoformat()
    }

    for page_num in range(1, 12):
        print(f"   Processing page {page_num}...")
        blocks = classifier.classify_page_content(page_num)

        for block in blocks:
            # Convert to entity format
            entity = {
                "type": block.type.value,
                "page": block.page,
                "bbox": block.bbox,
                "confidence": block.confidence,
                "content": block.content
            }
            result["entities"].append(entity)

    # Save
    output_path = Path(__file__).parent.parent / "outputs" / "universal_json" / \
                  "capitulo_01_enhanced_detection.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n   ✅ Saved to: {output_path.name}")
    print(f"   Total entities: {len(result['entities'])}")


if __name__ == "__main__":
    test_comparison()
    # save_enhanced_output()  # Uncomment to save

    print("\n✨ Done!")
