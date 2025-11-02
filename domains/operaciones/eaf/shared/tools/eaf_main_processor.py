"""
EAF Main Processor

Coordinates processing of large EAF documents by chapters following the dataflow pattern.
Implements: PDF → JSON → SQLite → MCP → AI Access
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List
import PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

# Import the chapter detector using relative path
eaf_root = Path(__file__).parent.parent
sys.path.append(str(eaf_root))

from chapter_detection.eaf_chapter_detector import EAFChapterDetector


class EAFMainProcessor:
    """Main processor for EAF documents with chapter-based processing."""

    def __init__(self, pdf_path: str, output_dir: str = None):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir) if output_dir else self.pdf_path.parent / "processed"
        self.project_root = project_root
        self.db_path = self.project_root / "platform_data" / "database" / "dark_data.db"

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize chapter detector
        self.detector = EAFChapterDetector(str(self.pdf_path))
        self.chapters_info = None

        # Processing results
        self.results = {
            'metadata': {},
            'chapters': [],
            'processing_stats': {}
        }

    def process_document(self) -> Dict:
        """Process the complete EAF document."""
        self.logger.info(f"Starting EAF document processing: {self.pdf_path.name}")

        # Step 1: Analyze document structure
        self.logger.info("Step 1: Analyzing document structure...")
        self.chapters_info = self.detector.analyze_document()
        self.results['metadata'] = self.chapters_info['metadata']

        # Step 2: Create output directories
        self.logger.info("Step 2: Setting up output directories...")
        self._setup_output_directories()

        # Step 3: Process chapters
        self.logger.info("Step 3: Processing chapters...")
        if self.chapters_info['processing_strategy']['strategy'] == 'parallel_chunks':
            self._process_chapters_parallel()
        else:
            self._process_chapters_sequential()

        # Step 4: Transform to universal JSON
        self.logger.info("Step 4: Transforming to universal JSON...")
        self._transform_to_universal_json()

        # Step 5: Ingest to database
        self.logger.info("Step 5: Ingesting to database...")
        self._ingest_to_database()

        # Step 6: Generate summary report
        self.logger.info("Step 6: Generating summary report...")
        self._generate_summary_report()

        self.logger.info("EAF document processing completed!")
        return self.results

    def _setup_output_directories(self):
        """Create necessary output directories."""
        self.output_dir.mkdir(exist_ok=True)

        # Create chapter-specific directories
        for i, chapter in enumerate(self.chapters_info['chapters']):
            chapter_name = f"chapter_{i+1}_{chapter['title'].lower().replace(' ', '_')}"
            chapter_dir = self.output_dir / chapter_name
            chapter_dir.mkdir(exist_ok=True)

            # Create subdirectories
            (chapter_dir / "raw_extractions").mkdir(exist_ok=True)
            (chapter_dir / "validated_extractions").mkdir(exist_ok=True)
            (chapter_dir / "universal_json").mkdir(exist_ok=True)

    def _process_chapters_parallel(self):
        """Process chapters in parallel."""
        max_workers = min(4, len(self.chapters_info['chapters']))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chapter processing tasks
            future_to_chapter = {
                executor.submit(self._process_single_chapter, i, chapter): (i, chapter)
                for i, chapter in enumerate(self.chapters_info['chapters'])
            }

            # Collect results as they complete
            for future in as_completed(future_to_chapter):
                chapter_idx, chapter_info = future_to_chapter[future]
                try:
                    result = future.result()
                    self.results['chapters'].append(result)
                    self.logger.info(f"Completed chapter {chapter_idx + 1}: {chapter_info['title']}")
                except Exception as exc:
                    self.logger.error(f"Chapter {chapter_idx + 1} generated an exception: {exc}")

    def _process_chapters_sequential(self):
        """Process chapters sequentially."""
        for i, chapter in enumerate(self.chapters_info['chapters']):
            try:
                result = self._process_single_chapter(i, chapter)
                self.results['chapters'].append(result)
                self.logger.info(f"Completed chapter {i + 1}: {chapter['title']}")
            except Exception as exc:
                self.logger.error(f"Chapter {i + 1} failed: {exc}")

    def _process_single_chapter(self, chapter_idx: int, chapter_info: Dict) -> Dict:
        """Process a single chapter."""
        chapter_name = f"chapter_{chapter_idx+1}_{chapter_info['title'].lower().replace(' ', '_')}"

        # Extract text from PDF pages
        chapter_text = self._extract_chapter_text(
            chapter_info['start_page'],
            chapter_info['end_page']
        )

        # Save raw extraction
        raw_file = self.output_dir / chapter_name / "raw_extractions" / f"{chapter_name}_raw.txt"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(chapter_text)

        # Process based on content type
        processed_data = self._process_by_content_type(chapter_text, chapter_info['content_type'])

        # Save processed data
        processed_file = self.output_dir / chapter_name / "validated_extractions" / f"{chapter_name}_processed.json"
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)

        return {
            'chapter_idx': chapter_idx,
            'title': chapter_info['title'],
            'content_type': chapter_info['content_type'],
            'pages': f"{chapter_info['start_page']}-{chapter_info['end_page']}",
            'raw_file': str(raw_file),
            'processed_file': str(processed_file),
            'record_count': len(processed_data.get('records', [])),
            'status': 'completed'
        }

    def _extract_chapter_text(self, start_page: int, end_page: int) -> str:
        """Extract text from specific page range."""
        text_parts = []

        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            for page_num in range(start_page, min(end_page + 1, len(reader.pages))):
                page = reader.pages[page_num]
                text = page.extract_text()
                text_parts.append(f"=== PAGE {page_num + 1} ===\n{text}\n")

        return '\n'.join(text_parts)

    def _process_by_content_type(self, text: str, content_type: str) -> Dict:
        """Process text based on its content type."""
        base_data = {
            'content_type': content_type,
            'processing_timestamp': None,
            'records': []
        }

        if content_type == 'technical_data':
            return self._extract_technical_data(text, base_data)
        elif content_type == 'company_reports':
            return self._extract_company_reports(text, base_data)
        elif content_type == 'analysis':
            return self._extract_analysis_data(text, base_data)
        elif content_type == 'tables':
            return self._extract_table_data(text, base_data)
        else:
            return self._extract_general_data(text, base_data)

    def _extract_technical_data(self, text: str, base_data: Dict) -> Dict:
        """Extract technical electrical data."""
        import re

        records = []

        # Extract voltage references
        voltage_pattern = r'(\d+(?:\.\d+)?)\s*k?V'
        voltages = re.findall(voltage_pattern, text, re.IGNORECASE)

        for voltage in voltages:
            records.append({
                'type': 'voltage_reference',
                'value': voltage,
                'unit': 'kV'
            })

        # Extract equipment references
        equipment_pattern = r'(interruptor|transformador|línea|subestación)\s+([A-Z0-9\-/]+)'
        equipment_matches = re.findall(equipment_pattern, text, re.IGNORECASE)

        for equip_type, equip_id in equipment_matches:
            records.append({
                'type': 'equipment',
                'equipment_type': equip_type.lower(),
                'equipment_id': equip_id
            })

        base_data['records'] = records
        return base_data

    def _extract_company_reports(self, text: str, base_data: Dict) -> Dict:
        """Extract company and report data."""
        import re

        records = []

        # Extract company names (simplified pattern)
        company_pattern = r'([A-Z][A-Z\s&\.]+(?:S\.A\.|SPA|LTDA))'
        companies = re.findall(company_pattern, text)

        for company in set(companies):  # Remove duplicates
            if len(company.strip()) > 5:  # Filter out noise
                records.append({
                    'type': 'company',
                    'name': company.strip()
                })

        # Extract time references
        time_pattern = r'(\d{1,2}:\d{2})'
        times = re.findall(time_pattern, text)

        for time_ref in set(times):
            records.append({
                'type': 'time_reference',
                'time': time_ref
            })

        base_data['records'] = records
        return base_data

    def _extract_analysis_data(self, text: str, base_data: Dict) -> Dict:
        """Extract analysis and conclusions."""
        records = []

        # Extract key phrases indicating analysis
        analysis_keywords = ['análisis', 'conclusión', 'recomendación', 'causa', 'efecto']

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in analysis_keywords):
                if len(line) > 20:  # Meaningful content
                    records.append({
                        'type': 'analysis_statement',
                        'content': line
                    })

        base_data['records'] = records
        return base_data

    def _extract_table_data(self, text: str, base_data: Dict) -> Dict:
        """Extract structured table data."""
        # This is a simplified table extraction
        # In practice, you'd use more sophisticated table detection

        records = []
        lines = text.split('\n')

        for line in lines:
            # Look for lines that might be table rows (multiple spaces/tabs)
            if '\t' in line or '  ' in line:
                parts = [part.strip() for part in line.split() if part.strip()]
                if len(parts) >= 3:  # Likely a table row
                    records.append({
                        'type': 'table_row',
                        'data': parts
                    })

        base_data['records'] = records
        return base_data

    def _extract_general_data(self, text: str, base_data: Dict) -> Dict:
        """Extract general data from unclassified content."""
        records = []

        # Extract dates
        import re
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        dates = re.findall(date_pattern, text)

        for date_ref in set(dates):
            records.append({
                'type': 'date_reference',
                'date': date_ref
            })

        base_data['records'] = records
        return base_data

    def _transform_to_universal_json(self):
        """Transform processed data to universal JSON schema."""
        universal_data = {
            'document_metadata': self.results['metadata'],
            'extraction_timestamp': None,
            'chapters': [],
            'cross_references': [],
            'entities': []
        }

        for chapter_result in self.results['chapters']:
            # Load processed data
            with open(chapter_result['processed_file'], 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)

            # Transform to universal format
            universal_chapter = {
                'chapter_id': f"eaf_089_2025_ch_{chapter_result['chapter_idx']+1}",
                'title': chapter_result['title'],
                'content_type': chapter_result['content_type'],
                'page_range': chapter_result['pages'],
                'entities': self._extract_entities_from_records(chapter_data['records']),
                'relationships': [],
                'metadata': {
                    'processing_date': None,
                    'record_count': chapter_result['record_count']
                }
            }

            universal_data['chapters'].append(universal_chapter)

            # Save universal JSON for this chapter
            chapter_name = f"chapter_{chapter_result['chapter_idx']+1}_{chapter_result['title'].lower().replace(' ', '_')}"
            universal_file = self.output_dir / chapter_name / "universal_json" / f"{chapter_name}_universal.json"

            with open(universal_file, 'w', encoding='utf-8') as f:
                json.dump(universal_chapter, f, indent=2, ensure_ascii=False)

        # Save complete universal JSON
        universal_file = self.output_dir / "eaf_089_2025_universal.json"
        with open(universal_file, 'w', encoding='utf-8') as f:
            json.dump(universal_data, f, indent=2, ensure_ascii=False)

        self.results['universal_json_file'] = str(universal_file)

    def _extract_entities_from_records(self, records: List[Dict]) -> List[Dict]:
        """Extract entities from processed records."""
        entities = []

        for record in records:
            if record['type'] == 'company':
                entities.append({
                    'type': 'organization',
                    'name': record['name'],
                    'category': 'company'
                })
            elif record['type'] == 'equipment':
                entities.append({
                    'type': 'equipment',
                    'name': record['equipment_id'],
                    'category': record['equipment_type']
                })
            elif record['type'] == 'voltage_reference':
                entities.append({
                    'type': 'technical_parameter',
                    'name': f"{record['value']} {record['unit']}",
                    'category': 'voltage'
                })

        return entities

    def _ingest_to_database(self):
        """Ingest processed data to SQLite database."""
        # This would connect to the main database and ingest the universal JSON
        # For now, we'll just log the action
        self.logger.info(f"Database ingestion would process: {self.results.get('universal_json_file', 'No file')}")

        # In a full implementation, this would:
        # 1. Connect to dark_data.db
        # 2. Insert document metadata
        # 3. Insert chapters and entities
        # 4. Create cross-references

        self.results['database_ingestion'] = 'simulated'

    def _generate_summary_report(self):
        """Generate processing summary report."""
        total_records = sum(ch['record_count'] for ch in self.results['chapters'])

        summary = {
            'document': self.pdf_path.name,
            'total_pages': self.results['metadata']['total_pages'],
            'chapters_processed': len(self.results['chapters']),
            'total_records_extracted': total_records,
            'processing_strategy': self.chapters_info['processing_strategy']['strategy'],
            'output_directory': str(self.output_dir)
        }

        # Save summary
        summary_file = self.output_dir / "processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        self.results['summary'] = summary
        self.results['summary_file'] = str(summary_file)

        # Print summary
        print("\n" + "="*60)
        print("EAF PROCESSING SUMMARY")
        print("="*60)
        print(f"Document: {summary['document']}")
        print(f"Total Pages: {summary['total_pages']}")
        print(f"Chapters Processed: {summary['chapters_processed']}")
        print(f"Records Extracted: {summary['total_records_extracted']}")
        print(f"Strategy: {summary['processing_strategy']}")
        print(f"Output Directory: {summary['output_directory']}")
        print("="*60)


def main():
    """Demo usage of EAF Main Processor."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python eaf_main_processor.py <pdf_path> [output_dir]")
        return

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    processor = EAFMainProcessor(pdf_path, output_dir)
    results = processor.process_document()

    print(f"\nProcessing completed! Results saved to: {processor.output_dir}")


if __name__ == "__main__":
    main()