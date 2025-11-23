#!/usr/bin/env python3
"""
PDF Chapter Splitter - Divide un PDF en capítulos

Usage:
    # Con rangos predefinidos
    python3 split_pdf_chapters.py /ruta/EAF-089-2025.pdf --report EAF-089-2025

    # Detección automática de capítulos
    python3 split_pdf_chapters.py /ruta/nuevo.pdf --report EAF-477-2025 --auto
"""
import argparse
from pathlib import Path
import fitz  # PyMuPDF
import re


def detect_chapters_automatically(pdf_path: str):
    """
    Automatically detect chapter boundaries in a PDF.

    Looks for patterns like "1. ", "2. ", etc. at the start of lines.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        dict: Chapter number -> (start_page, end_page) mapping
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Pattern to match chapter headings: "1. Descripción..." (number + capitalized word)
    # Excludes subsections like "9.1" by requiring space after the period
    # and excluding matches where the period is followed by another digit
    chapter_pattern = re.compile(r'^\s*(\d{1,2})\.\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+', re.MULTILINE)

    # Also exclude subsection patterns like "9.1 Incumplimiento"
    subsection_pattern = re.compile(r'^\s*\d+\.\d+\s+', re.MULTILINE)

    # Find all chapter starts
    chapter_starts = {}  # chapter_num -> page_num (1-indexed)

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()

        # Look for chapter headings in full page text
        for match in chapter_pattern.finditer(text):
            chapter_num = int(match.group(1))
            match_text = match.group(0)[:50].replace('\n', ' ')

            # Only record first occurrence of each chapter
            if chapter_num not in chapter_starts:
                chapter_starts[chapter_num] = page_num + 1  # Convert to 1-indexed
                print(f"   📍 Chapter {chapter_num} found on page {page_num + 1}: \"{match_text}...\"")
            else:
                # Show duplicate detections for debugging
                if page_num + 1 != chapter_starts[chapter_num]:
                    print(f"   ⚠️  Chapter {chapter_num} also on page {page_num + 1} (keeping page {chapter_starts[chapter_num]})")

    doc.close()

    if not chapter_starts:
        print("⚠️  No chapters detected automatically")
        return {}

    # Sort chapters and validate
    sorted_chapters = sorted(chapter_starts.keys())

    # Check for gaps
    expected = list(range(1, max(sorted_chapters) + 1))
    missing = set(expected) - set(sorted_chapters)

    if missing:
        print(f"⚠️  Missing chapters detected: {sorted(missing)}")
        print(f"   Found chapters: {sorted_chapters}")
        # Continue anyway, but warn user

    # Build chapter ranges
    chapters = {}
    for i, chapter_num in enumerate(sorted_chapters):
        start_page = chapter_starts[chapter_num]

        # End page is start of next chapter - 1, or end of document
        if i + 1 < len(sorted_chapters):
            next_chapter = sorted_chapters[i + 1]
            next_start = chapter_starts[next_chapter]

            # If next chapter is on same page, this chapter gets only this page
            if next_start == start_page:
                end_page = start_page
            else:
                end_page = next_start - 1
        else:
            end_page = total_pages

        chapters[chapter_num] = (start_page, end_page)

    return chapters

# Default output directory (relative to project root)
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "inputs"

# Chapter definitions per report (page ranges - 1-indexed)
REPORT_CHAPTERS = {
    "EAF-089-2025": {
        1: (1, 11),
        2: (12, 90),
        3: (91, 152),
        4: (153, 159),
        5: (160, 171),
        6: (172, 265),
        7: (266, 347),
        8: (348, 348),
        9: (349, 381),
        10: (382, 392),
        11: (393, 399),
    },
    # Add new reports here:
    # "EAF-090-2026": {
    #     1: (1, 20),
    #     2: (21, 100),
    #     ...
    # },
}


def split_pdf_into_chapters(pdf_path: str, report_id: str, output_dir: Path = None, auto_detect: bool = False):
    """
    Split a PDF into chapters based on predefined or auto-detected page ranges.

    Args:
        pdf_path: Path to the source PDF
        report_id: Report identifier (e.g., "EAF-089-2025")
        output_dir: Directory for output files
        auto_detect: If True, automatically detect chapter boundaries
    """
    # Set defaults
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return False

    # Get chapter definitions
    if auto_detect or report_id not in REPORT_CHAPTERS:
        if not auto_detect:
            print(f"ℹ️  Report {report_id} not in REPORT_CHAPTERS, using auto-detection...")
        print(f"🔍 Auto-detecting chapters in {pdf_path.name}...")
        chapters = detect_chapters_automatically(str(pdf_path))
        if not chapters:
            print("❌ Could not detect chapters automatically")
            return False
        print(f"✅ Detected {len(chapters)} chapters")
        print()
    else:
        chapters = REPORT_CHAPTERS[report_id]

    # Create output directory
    report_output_dir = output_dir / report_id / "capitulos"
    report_output_dir.mkdir(parents=True, exist_ok=True)

    # Also copy the original PDF
    original_dir = output_dir / report_id
    import shutil
    original_copy = original_dir / pdf_path.name
    if not original_copy.exists():
        shutil.copy(pdf_path, original_copy)
        print(f"📋 Original PDF copied to: {original_copy}")

    print("=" * 60)
    print(f"📄 Splitting PDF into chapters")
    print("=" * 60)
    print(f"📥 Input: {pdf_path}")
    print(f"📤 Output: {report_output_dir}")
    print(f"📊 Report: {report_id}")
    print(f"📑 Chapters: {len(chapters)}")
    print("=" * 60)
    print()

    # Open source PDF
    src_doc = fitz.open(pdf_path)
    total_pages = len(src_doc)

    print(f"📖 Source PDF has {total_pages} pages")
    print()

    # Split into chapters
    for chapter_num, (start_page, end_page) in sorted(chapters.items()):
        # Convert to 0-indexed for PyMuPDF
        start_idx = start_page - 1
        end_idx = end_page  # end is exclusive in select()

        # Validate page range
        if start_idx < 0 or end_idx > total_pages:
            print(f"⚠️  Chapter {chapter_num}: Invalid range {start_page}-{end_page} (PDF has {total_pages} pages)")
            continue

        # Create new PDF for this chapter
        chapter_doc = fitz.open()
        chapter_doc.insert_pdf(src_doc, from_page=start_idx, to_page=end_idx-1)

        # Save chapter PDF
        output_filename = f"capitulo_{chapter_num:02d}.pdf"
        output_path = report_output_dir / output_filename
        chapter_doc.save(output_path)
        chapter_doc.close()

        # Get file size
        size_kb = output_path.stat().st_size / 1024
        num_pages = end_page - start_page + 1

        print(f"✅ Chapter {chapter_num:2d}: pages {start_page:3d}-{end_page:3d} ({num_pages:3d} pages) → {output_filename} ({size_kb:.0f} KB)")

    src_doc.close()

    print()
    print("=" * 60)
    print(f"✅ Split complete: {len(chapters)} chapters created")
    print(f"📁 Output: {report_output_dir}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split PDF into chapters')
    parser.add_argument('pdf', type=str, help='Path to source PDF')
    parser.add_argument('--report', type=str, required=True,
                        help='Report ID (e.g., "EAF-089-2025")')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory (default: data/inputs)')
    parser.add_argument('--auto', action='store_true',
                        help='Auto-detect chapter boundaries')

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None

    split_pdf_into_chapters(args.pdf, args.report, output_dir, args.auto)
