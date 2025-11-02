#!/usr/bin/env python3
"""
Universal Extraction Script - Complete Docling JSON + Metadata

This script is the STANDARD extraction method for all chapters.
It exports:
1. Complete Docling JSON (with all table data, validation, etc.)
2. Metadata file (summary statistics)

Usage:
    python extract_with_complete_json.py <pdf_path> <output_dir> [--patch]

Arguments:
    pdf_path: Path to PDF file
    output_dir: Directory to save outputs
    --patch: Optional - apply EAF monkey patch

Example:
    python extract_with_complete_json.py EAF-089-2025_cap1.pdf ./capitulo_01/outputs
    python extract_with_complete_json.py EAF-089-2025_cap7.pdf ./capitulo_07/outputs --patch
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

# Add eaf_patch to path if it exists
eaf_patch_path = Path(__file__).parent.parent / "eaf_patch"
if eaf_patch_path.exists():
    sys.path.insert(0, str(eaf_patch_path))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorOptions
)
from docling.datamodel.base_models import InputFormat


def extract_complete(pdf_path, output_dir, use_patch=False, use_accurate_tables=False):
    """
    Extract PDF using Docling with complete JSON export

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save outputs
        use_patch: Whether to apply EAF monkey patch
        use_accurate_tables: Use ACCURATE mode (800 MB) vs FAST (400 MB)

    Returns:
        dict: Extraction metadata
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("DOCLING COMPLETE EXTRACTION")
    print("=" * 80)
    print(f"\n📄 PDF: {pdf_path}")
    print(f"📁 Output: {output_dir}")
    print(f"🐵 Patch: {'ENABLED' if use_patch else 'DISABLED'}")
    print(f"📊 Tables: {'ACCURATE (97.9%)' if use_accurate_tables else 'FAST (90-95%)'}")

    # ========================================================================
    # STEP 1: Apply Patch (Optional)
    # ========================================================================
    if use_patch:
        print("\n" + "=" * 80)
        print("🐵 STEP 1: Applying EAF Monkey Patch")
        print("=" * 80)

        try:
            from core.eaf_patch_engine import apply_universal_patch_with_pdf, apply_zona_fix_to_document
            apply_universal_patch_with_pdf(pdf_path)
            print("✅ EAF patch applied")
        except ImportError:
            print("⚠️  Warning: EAF patch not found, skipping")
            use_patch = False

    # ========================================================================
    # STEP 2: Configure Docling
    # ========================================================================
    print("\n" + "=" * 80)
    print("⚙️  STEP 2: Configuring Docling Pipeline")
    print("=" * 80)

    pipeline_options = PdfPipelineOptions()

    # Core settings
    pipeline_options.do_ocr = False  # Native PDFs don't need OCR
    pipeline_options.do_table_structure = True

    # Table settings
    pipeline_options.table_structure_options = TableStructureOptions(
        mode=TableFormerMode.ACCURATE if use_accurate_tables else TableFormerMode.FAST,
        do_cell_matching=True  # Enable validation
    )

    # GPU settings
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=2,
        device="cuda"
    )

    # Disable unnecessary features (save VRAM)
    pipeline_options.do_picture_classification = False
    pipeline_options.do_picture_description = False
    pipeline_options.do_code_enrichment = False
    pipeline_options.do_formula_enrichment = False

    print(f"✅ OCR: Disabled (native PDF text)")
    print(f"✅ Tables: {pipeline_options.table_structure_options.mode.value} mode")
    print(f"✅ Cell matching: Enabled (validation)")
    print(f"✅ GPU: CUDA with 2 threads")

    # Calculate expected VRAM usage
    vram_usage = 1600  # Base (Granite + PyTorch + buffers)
    vram_usage += 800 if use_accurate_tables else 400  # TableFormer
    print(f"\n💾 Expected VRAM: {vram_usage} MB")

    # ========================================================================
    # STEP 3: Convert PDF
    # ========================================================================
    print("\n" + "=" * 80)
    print("🔄 STEP 3: Processing PDF with Docling")
    print("=" * 80)

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = datetime.now()
    result = converter.convert(str(pdf_path))
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()

    print(f"\n✅ Extraction complete in {processing_time:.1f} seconds")

    # ========================================================================
    # STEP 4: Apply Post-Processing (if patch enabled)
    # ========================================================================
    if use_patch:
        print("\n" + "=" * 80)
        print("🔧 STEP 4: Applying Document-Level Zona Fix")
        print("=" * 80)

        try:
            doc = result.document
            reclassified_count = apply_zona_fix_to_document(doc)
            print(f"✅ Zona fix applied ({reclassified_count} items reclassified)")
        except Exception as e:
            print(f"⚠️  Warning: Zona fix failed: {e}")

    # ========================================================================
    # STEP 5: Generate Metadata
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 STEP 5: Generating Metadata")
    print("=" * 80)

    doc = result.document

    # Count elements by type
    element_counts = Counter()
    native_text_count = 0
    image_text_count = 0
    empty_count = 0

    for item in doc.iterate_items():
        # Count by type
        if hasattr(item, 'label'):
            element_counts[item.label.value] += 1

        # Check text source
        if hasattr(item, 'prov') and item.prov:
            charspan = item.prov[0].charspan if hasattr(item.prov[0], 'charspan') else None
            if charspan is not None:
                native_text_count += 1
            elif hasattr(item, 'text') and item.text:
                image_text_count += 1
            else:
                empty_count += 1

    # Table-specific stats
    table_count = element_counts.get('table', 0)
    tables_with_text = 0
    tables_empty = 0

    for item in doc.iterate_items():
        if hasattr(item, 'label') and item.label.value == 'table':
            if hasattr(item, 'text') and item.text:
                tables_with_text += 1
            else:
                tables_empty += 1

    metadata = {
        "extraction_info": {
            "pdf_file": pdf_path.name,
            "pdf_path": str(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "processing_time_seconds": round(processing_time, 2),
            "patch_applied": use_patch,
            "table_mode": "ACCURATE" if use_accurate_tables else "FAST",
            "vram_usage_mb": vram_usage
        },
        "document_stats": {
            "total_pages": len(doc.pages),
            "total_elements": sum(element_counts.values())
        },
        "elements_by_type": dict(element_counts),
        "text_quality": {
            "native_pdf_text": native_text_count,
            "image_based_text": image_text_count,
            "empty_elements": empty_count,
            "native_percentage": round(100 * native_text_count / max(sum(element_counts.values()), 1), 1)
        },
        "table_stats": {
            "total_tables": table_count,
            "tables_with_text": tables_with_text,
            "tables_empty": tables_empty,
            "extraction_rate": round(100 * tables_with_text / max(table_count, 1), 1)
        },
        "configuration": {
            "ocr_enabled": False,
            "table_mode": pipeline_options.table_structure_options.mode.value,
            "cell_matching": True,
            "gpu_device": "cuda",
            "num_threads": 2
        }
    }

    # Print summary
    print(f"\n📊 Document Statistics:")
    print(f"   Total pages: {metadata['document_stats']['total_pages']}")
    print(f"   Total elements: {metadata['document_stats']['total_elements']}")
    print(f"\n📋 Elements by type:")
    for elem_type, count in sorted(element_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {elem_type:<20}: {count:>4}")
    print(f"\n✅ Text quality:")
    print(f"   Native PDF text: {native_text_count} ({metadata['text_quality']['native_percentage']}%)")
    print(f"   Image-based: {image_text_count}")
    print(f"   Empty: {empty_count}")

    if table_count > 0:
        print(f"\n📊 Table extraction:")
        print(f"   Total tables: {table_count}")
        print(f"   With text: {tables_with_text} ({metadata['table_stats']['extraction_rate']}%)")
        print(f"   Empty: {tables_empty}")

    # ========================================================================
    # STEP 6: Save Outputs
    # ========================================================================
    print("\n" + "=" * 80)
    print("💾 STEP 6: Saving Outputs")
    print("=" * 80)

    # 1. Complete Docling JSON
    output_json = output_dir / "docling_complete.json"
    result.document.save_as_json(str(output_json), indent=2)
    json_size_mb = output_json.stat().st_size / (1024 * 1024)
    print(f"✅ Saved: {output_json}")
    print(f"   Size: {json_size_mb:.2f} MB")
    print(f"   Contains: All table data, grid structure, validation metadata")

    # 2. Metadata
    metadata_json = output_dir / "extraction_metadata.json"
    with open(metadata_json, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Saved: {metadata_json}")
    print(f"   Contains: Statistics and extraction info")

    # 3. Markdown (optional, for review)
    output_md = output_dir / "document.md"
    markdown = result.document.export_to_markdown(enable_chart_tables=True)
    with open(output_md, 'w') as f:
        f.write(markdown)
    md_size_kb = output_md.stat().st_size / 1024
    print(f"✅ Saved: {output_md}")
    print(f"   Size: {md_size_kb:.1f} KB")
    print(f"   Contains: Human-readable format")

    print("\n" + "=" * 80)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"\n📁 Output directory: {output_dir}")
    print(f"   1. docling_complete.json - Complete extraction data")
    print(f"   2. extraction_metadata.json - Statistics and info")
    print(f"   3. document.md - Human-readable format")

    return metadata


def main():
    """Command-line interface"""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    use_patch = '--patch' in sys.argv
    use_accurate = '--accurate' in sys.argv

    if not Path(pdf_path).exists():
        print(f"❌ Error: PDF not found: {pdf_path}")
        sys.exit(1)

    try:
        metadata = extract_complete(pdf_path, output_dir, use_patch, use_accurate)
        print(f"\n✅ Success! Processed {metadata['document_stats']['total_elements']} elements")
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
