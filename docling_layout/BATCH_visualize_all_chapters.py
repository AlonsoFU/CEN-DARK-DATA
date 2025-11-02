#!/usr/bin/env python3
"""
BATCH Visualization - Create annotated PDFs for all 11 chapters
Following METHODOLOGY color standards
"""
import json
import fitz
from pathlib import Path
import time

# Standard Docling colors (from METHODOLOGY)
COLORS = {
    'text': (0, 0, 1),
    'section_header': (1, 0, 0),
    'title': (1, 0.5, 0),
    'list_item': (0, 0.7, 0.7),
    'table': (0, 0.7, 0),
    'picture': (1, 0, 1),
    'caption': (0.8, 0.4, 0),
    'formula': (1, 0.8, 0),
    'footnote': (0.8, 0.4, 0),
    'page_header': (0.5, 0.5, 0.5),
    'page_footer': (0.5, 0.5, 0.5),
}

COLOR_NAMES = {
    (1, 0, 0): "Red",
    (0, 0.7, 0.7): "Cyan",
    (0, 0.7, 0): "Green",
    (0, 0, 1): "Blue",
    (0.8, 0.4, 0): "Brown",
    (1, 0.5, 0): "Orange",
    (1, 0, 1): "Magenta",
    (1, 0.8, 0): "Yellow",
    (0.5, 0.5, 0.5): "Gray"
}

# Chapter definitions
# CORRECTED: Chapter 3 = 91-152, Chapter 4 = 153-159 (page 153 is Chapter 4 title!)
CHAPTERS = [
    {"num": 1, "pages": "1-11"},
    {"num": 2, "pages": "12-90"},
    {"num": 3, "pages": "91-152"},  # CORRECTED: was 91-153
    {"num": 4, "pages": "153-159"},  # CORRECTED: was 154-159
    {"num": 5, "pages": "160-171"},
    {"num": 6, "pages": "172-265"},
    {"num": 7, "pages": "266-347"},
    {"num": 8, "pages": "348-348"},
    {"num": 9, "pages": "349-381"},
    {"num": 10, "pages": "382-392"},
    {"num": 11, "pages": "393-399"},
]

BASE_PATH = Path(__file__).parent
PDF_BASE = Path("/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/claude_ocr")

print("=" * 80)
print("🎨 BATCH VISUALIZATION: Creating Annotated PDFs for All Chapters")
print("=" * 80)
print(f"Total chapters to visualize: {len(CHAPTERS)}\n")

success_count = 0
failed_count = 0
results = []

for chapter in CHAPTERS:
    num = chapter['num']
    pages = chapter['pages']

    print("=" * 80)
    print(f"🎨 CHAPTER {num}")
    print("=" * 80)

    start_time = time.time()

    try:
        # Paths
        chapter_dir = BASE_PATH / f"capitulo_{num:02d}"
        json_path = chapter_dir / "outputs" / "layout_WITH_PATCH.json"
        pdf_path = PDF_BASE / f"capitulo_{num:02d}" / f"EAF-089-2025_capitulo_{num:02d}_pages_{pages}.pdf"
        output_pdf = chapter_dir / "outputs" / f"capitulo_{num:02d}_annotated.pdf"

        # Check files exist
        if not json_path.exists():
            print(f"❌ JSON not found: {json_path}")
            failed_count += 1
            results.append({"chapter": num, "status": "FAILED", "reason": "JSON not found"})
            continue

        if not pdf_path.exists():
            print(f"❌ PDF not found: {pdf_path}")
            failed_count += 1
            results.append({"chapter": num, "status": "FAILED", "reason": "PDF not found"})
            continue

        # Load JSON
        with open(json_path) as f:
            data = json.load(f)

        elements = data['elements']
        print(f"📄 Loading {len(elements)} elements...")

        # Open PDF
        doc = fitz.open(pdf_path)
        print(f"📄 PDF has {len(doc)} pages")

        # Draw boxes
        boxes_drawn = 0
        color_counts = {}

        for elem in elements:
            if not elem.get('bbox'):
                continue

            bbox = elem['bbox']
            page_num_json = elem['page']

            # JSON uses 1-indexed pages, PyMuPDF uses 0-indexed
            page_idx = page_num_json - 1

            if 0 <= page_idx < len(doc):
                page = doc[page_idx]

                # Extract label name
                label = elem['type']
                if isinstance(label, str) and '.' in label:
                    label = label.split('.')[-1].lower()
                else:
                    label = str(label).lower()

                # Get color
                color = COLORS.get(label, (0.5, 0.5, 0.5))

                # Count
                color_counts[label] = color_counts.get(label, 0) + 1

                # Draw rectangle
                rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
                page.draw_rect(rect, color=color, width=2)

                boxes_drawn += 1

        print(f"\n✅ Drew {boxes_drawn} boxes")
        print("\n📊 Elements by type:")
        for label, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
            color = COLORS.get(label, (0.5, 0.5, 0.5))
            color_name = COLOR_NAMES.get(color, "Unknown")
            print(f"   {label:<20} ({color_name:<8}): {count:>4} boxes")

        # Add legend on first page
        page = doc[0]
        legend_x = 420
        legend_y = 30
        legend_height = min(15 + len(color_counts) * 12, 120)
        legend_rect = fitz.Rect(legend_x - 5, legend_y - 5, legend_x + 160, legend_y + legend_height)
        page.draw_rect(legend_rect, color=(0, 0, 0), fill=(1, 1, 1), width=1)
        page.insert_text(fitz.Point(legend_x, legend_y), f"Chapter {num}:", fontsize=9, color=(0, 0, 0))

        y_offset = legend_y + 15
        for label in sorted(color_counts.keys(), key=lambda x: color_counts[x], reverse=True)[:6]:
            color = COLORS.get(label, (0.5, 0.5, 0.5))
            color_rect = fitz.Rect(legend_x, y_offset - 8, legend_x + 10, y_offset)
            page.draw_rect(color_rect, color=color, fill=color, width=0)
            page.insert_text(fitz.Point(legend_x + 15, y_offset), f"{label} ({color_counts[label]})", fontsize=7, color=(0, 0, 0))
            y_offset += 12

        # Save
        doc.save(output_pdf)
        doc.close()

        elapsed = time.time() - start_time
        print(f"\n✅ Saved: {output_pdf}")
        print(f"⏱️  Time: {elapsed:.1f}s")

        success_count += 1
        results.append({
            "chapter": num,
            "status": "SUCCESS",
            "elements": len(elements),
            "boxes": boxes_drawn,
            "time": f"{elapsed:.1f}s"
        })

    except Exception as e:
        print(f"\n❌ Error: {e}")
        failed_count += 1
        results.append({"chapter": num, "status": "FAILED", "reason": str(e)})

# Summary
print("\n" + "=" * 80)
print("📊 BATCH VISUALIZATION SUMMARY")
print("=" * 80)

for result in results:
    if result["status"] == "SUCCESS":
        print(f"✅ Chapter {result['chapter']:2d}: {result['boxes']:4d} boxes in {result['time']:>6s} - SUCCESS")
    else:
        print(f"❌ Chapter {result['chapter']:2d}: {result['reason']} - FAILED")

print("\n" + "=" * 80)
print(f"✅ Completed: {success_count}/{len(CHAPTERS)} chapters")
print(f"❌ Failed: {failed_count}/{len(CHAPTERS)} chapters")
print("=" * 80)
