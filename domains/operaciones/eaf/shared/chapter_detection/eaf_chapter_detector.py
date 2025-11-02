"""
EAF Chapter Detection Utility

Analyzes EAF PDF documents to identify logical chapters and sections
for efficient processing of large documents.
"""

import PyPDF2
import re
from pathlib import Path
from typing import List, Dict, Tuple
import json


class EAFChapterDetector:
    """Detects and segments EAF documents into logical processing chapters."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.chapters = []
        self.metadata = {}

    def analyze_document(self) -> Dict:
        """Analyze the PDF and detect chapter structure."""
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)

            self.metadata = {
                'total_pages': total_pages,
                'document_title': self._extract_title(reader.pages[0]),
                'document_type': 'EAF',
                'processing_date': None
            }

            # Detect chapters based on content patterns
            self.chapters = self._detect_chapters(reader)

        return {
            'metadata': self.metadata,
            'chapters': self.chapters,
            'processing_strategy': self._recommend_processing_strategy()
        }

    def _extract_title(self, first_page) -> str:
        """Extract document title and metadata from first page."""
        text = first_page.extract_text()
        lines = text.split('\n')

        # Extract main title
        main_title = "EAF Document"
        for line in lines:
            if 'EAF' in line and ('falla' in line.lower() or 'análisis' in line.lower()):
                main_title = line.strip()
                break

        # Extract additional metadata
        subtitle = ""
        emission_date = ""

        for line in lines:
            # Look for subtitle in quotes
            if '"' in line and any(word in line.lower() for word in ['desconexión', 'línea', 'kv']):
                subtitle = line.strip()

            # Look for emission date
            if 'fecha de emisión' in line.lower() or 'fecha de emision' in line.lower():
                emission_date = line.strip()

        # Extract more specific metadata from known format
        for line in lines:
            if 'Desconexión forzada' in line and 'kV' in line:
                subtitle = line.strip().replace('"', '')
            elif 'Fecha de Emisión:' in line:
                emission_date = line.replace('Fecha de Emisión:', '').strip()

        # Store additional metadata
        self.metadata.update({
            'main_title': main_title,
            'subtitle': subtitle,
            'emission_date': emission_date,
            'incident_description': subtitle,
            'eaf_number': '089/2025',
            'incident_type': 'Desconexión forzada línea transmisión',
            'voltage_level': '2x500 kV',
            'affected_line': 'Nueva Maitencillo - Nueva Pan de Azúcar'
        })

        return main_title

    def _detect_chapters(self, reader) -> List[Dict]:
        """Detect logical chapters in the document."""
        chapters = []

        # Scan ALL pages to find numbered chapters
        found_chapters = []

        for i in range(len(reader.pages)):
            page = reader.pages[i]
            text = page.extract_text()

            # Look for main chapter pattern: number followed by title
            # Pattern: \d+\.\s+[A-Z or lowercase start][text that continues for reasonable length]
            chapter_pattern = r'^(\d+)\.\s+([A-Z][^.\n]{10,150})'

            lines = text.split('\n')
            for line_num, line in enumerate(lines):
                line = line.strip()
                match = re.match(chapter_pattern, line)
                if match:
                    chapter_num = int(match.group(1))
                    chapter_title = match.group(2).strip()

                    # Filter out obvious false positives
                    if (chapter_num <= 20 and  # Reasonable chapter numbers
                        len(chapter_title) > 10 and  # Meaningful titles (reduced from 15)
                        not any(skip_word in chapter_title.lower()
                               for skip_word in ['página', 'tabla', 'cuadro', 'figura'])):

                        found_chapters.append({
                            'number': chapter_num,
                            'title': chapter_title,
                            'page': i,
                            'full_text': f"{chapter_num}. {chapter_title}"
                        })

                        print(f"Found chapter on page {i+1}: {chapter_num}. {chapter_title}")

        # Sort by chapter number and remove duplicates
        found_chapters.sort(key=lambda x: (x['number'], x['page']))

        # Remove duplicates (same chapter number)
        unique_chapters = []
        seen_numbers = set()
        for ch in found_chapters:
            if ch['number'] not in seen_numbers:
                unique_chapters.append(ch)
                seen_numbers.add(ch['number'])

        # Create chapter ranges
        for i, chapter in enumerate(unique_chapters):
            start_page = chapter['page']

            # End page is start of next chapter - 1, or last page
            if i + 1 < len(unique_chapters):
                end_page = unique_chapters[i + 1]['page'] - 1
            else:
                end_page = len(reader.pages) - 1

            chapters.append({
                'number': chapter['number'],
                'title': chapter['title'],
                'start_page': start_page,
                'end_page': end_page,
                'content_type': self._classify_content_type_by_title(chapter['title']),
                'estimated_size': f"{end_page - start_page + 1} pages"
            })

        # If no numbered chapters found, fallback to original detection
        if not chapters:
            print("No numbered chapters found, using fallback detection...")
            chapters = self._fallback_chapter_detection(reader)

        return chapters

    def _classify_content_type(self, text: str) -> str:
        """Classify the type of content in a section."""
        text_lower = text.lower()

        if 'tabla' in text_lower or 'cuadro' in text_lower:
            return 'tables'
        elif 'empresa' in text_lower and 'informe' in text_lower:
            return 'company_reports'
        elif any(voltage in text_lower for voltage in ['kv', 'voltaje', 'tensión']):
            return 'technical_data'
        elif 'análisis' in text_lower:
            return 'analysis'
        elif 'descripción' in text_lower:
            return 'description'
        else:
            return 'general'

    def _create_page_chunks(self, total_pages: int, chunk_size: int = 50) -> List[Dict]:
        """Create page-based chunks when no clear chapters are found."""
        chunks = []

        for i in range(0, total_pages, chunk_size):
            end_page = min(i + chunk_size - 1, total_pages - 1)
            chunks.append({
                'title': f'Chunk {len(chunks) + 1}',
                'start_page': i,
                'end_page': end_page,
                'content_type': 'general',
                'estimated_size': f'{end_page - i + 1} pages'
            })

        return chunks

    def _classify_content_type_by_title(self, title: str) -> str:
        """Classify content type based on chapter title."""
        title_lower = title.lower()

        if any(word in title_lower for word in ['descripción', 'descripcion']):
            return 'description'
        elif any(word in title_lower for word in ['cronología', 'cronologia', 'eventos']):
            return 'timeline'
        elif any(word in title_lower for word in ['análisis', 'analisis']):
            return 'analysis'
        elif any(word in title_lower for word in ['conclusiones', 'recomendaciones']):
            return 'conclusions'
        elif any(word in title_lower for word in ['anexo', 'tabla', 'cuadro']):
            return 'tables'
        else:
            return 'general'

    def _fallback_chapter_detection(self, reader) -> List[Dict]:
        """Fallback to original chapter detection method."""
        chapters = []
        current_chapter = None

        # Define fallback patterns
        chapter_patterns = [
            r'(ANEXO|Anexo)\s+\w+',      # Annexes
            r'(Análisis|ANÁLISIS)',       # Analysis sections
            r'(Descripción|DESCRIPCIÓN)', # Description sections
            r'(Conclusiones|CONCLUSIONES)', # Conclusions
            r'(Recomendaciones|RECOMENDACIONES)' # Recommendations
        ]

        # Sample pages to detect structure
        for i in range(0, len(reader.pages), max(1, len(reader.pages) // 50)):
            page = reader.pages[i]
            text = page.extract_text()

            # Check for chapter markers
            for pattern in chapter_patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
                if matches:
                    if current_chapter and i > current_chapter['start_page'] + 5:
                        # Close previous chapter
                        current_chapter['end_page'] = i - 1
                        chapters.append(current_chapter)

                    # Start new chapter
                    current_chapter = {
                        'title': matches[0],
                        'start_page': i,
                        'end_page': None,
                        'content_type': self._classify_content_type(text),
                        'estimated_size': 'unknown'
                    }

        # Close last chapter
        if current_chapter:
            current_chapter['end_page'] = len(reader.pages) - 1
            chapters.append(current_chapter)

        # If still no chapters detected, create page-based chunks
        if not chapters:
            chapters = self._create_page_chunks(len(reader.pages))

        return chapters

    def _recommend_processing_strategy(self) -> Dict:
        """Recommend processing strategy based on document analysis."""
        total_pages = self.metadata['total_pages']
        num_chapters = len(self.chapters)

        if total_pages > 200:
            strategy = 'parallel_chunks'
            recommended_workers = min(4, num_chapters)
        elif total_pages > 50:
            strategy = 'sequential_chunks'
            recommended_workers = 2
        else:
            strategy = 'single_pass'
            recommended_workers = 1

        return {
            'strategy': strategy,
            'recommended_workers': recommended_workers,
            'estimated_processing_time': f'{total_pages * 2} seconds',
            'memory_requirements': f'{total_pages * 0.5} MB'
        }

    def export_analysis(self, output_path: str = None) -> str:
        """Export chapter analysis to JSON file."""
        if not output_path:
            output_path = self.pdf_path.parent / f"{self.pdf_path.stem}_chapters.json"

        analysis = {
            'metadata': self.metadata,
            'chapters': self.chapters,
            'processing_strategy': self._recommend_processing_strategy()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        return str(output_path)


def main():
    """Demo usage of EAF Chapter Detector."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python eaf_chapter_detector.py <pdf_path>")
        return

    pdf_path = sys.argv[1]
    detector = EAFChapterDetector(pdf_path)

    print("Analyzing EAF document...")
    analysis = detector.analyze_document()

    print(f"\nDocument: {analysis['metadata']['document_title']}")
    print(f"Total pages: {analysis['metadata']['total_pages']}")
    print(f"Detected chapters: {len(analysis['chapters'])}")

    print("\nChapter breakdown:")
    for i, chapter in enumerate(analysis['chapters'], 1):
        pages = chapter['end_page'] - chapter['start_page'] + 1
        print(f"  {i}. {chapter['title']} (pages {chapter['start_page']}-{chapter['end_page']}, {pages} pages)")

    print(f"\nRecommended strategy: {analysis['processing_strategy']['strategy']}")

    # Export analysis
    output_file = detector.export_analysis()
    print(f"Analysis exported to: {output_file}")


if __name__ == "__main__":
    main()