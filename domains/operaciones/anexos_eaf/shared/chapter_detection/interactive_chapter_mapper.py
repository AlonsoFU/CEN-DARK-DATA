#!/usr/bin/env python3
"""
Phase 1: Interactive Chapter Mapper
- Scans full document for chapter boundaries  
- Shows you each potential chapter in real-time
- You validate: y/n for each chapter boundary
- Saves validated structure to profiles/anexos_eaf/
"""
import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Installing PyPDF2...")
    os.system("pip install PyPDF2")
    from PyPDF2 import PdfReader

@dataclass
class ChapterCandidate:
    page: int
    title: str
    pattern_matched: str
    confidence: str
    preview_text: str
    validated: bool = False
    chapter_type: str = "unknown"

class InteractiveChapterMapper:
    def __init__(self, document_path: str):
        self.document_path = Path(document_path)
        self.profile_dir = Path("profiles/anexos_eaf")
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        self.pdf_reader = None
        self.total_pages = 0
        self.chapter_candidates: List[ChapterCandidate] = []
        self.validated_chapters: List[ChapterCandidate] = []
        
        # Enhanced chapter detection patterns
        self.chapter_patterns = {
            # Anexos sections
            r"ANEXO\s*N[º°ªo]?\s*\d+": "anexo_section",
            
            # Main EAF report sections
            r"(?:RESUMEN\s*EJECUTIVO|SÍNTESIS\s*EJECUTIVA)": "executive_summary",
            r"(?:CRONOLOGÍA|SECUENCIA|TIMELINE|DESARROLLO\s*CRONOLÓGICO)": "chronology",
            r"(?:EMPRESA|INFORME\s*DE\s*LA\s*EMPRESA|COMPAÑÍAS?\s*AFECTADAS)": "company_reports",
            r"(?:ANÁLISIS\s*TÉCNICO|EVALUACIÓN\s*TÉCNICA|ESPECIFICACIONES\s*TÉCNICAS)": "technical_analysis",
            r"(?:EQUIPOS?\s*DE\s*PROTECCIÓN|ELEMENTOS?\s*FALLADOS?)": "equipment_analysis",
            r"(?:CAUSAS?\s*DE\s*LA\s*FALLA|ANÁLISIS\s*DE\s*CAUSAS?)": "root_cause_analysis",
            r"(?:RECOMENDACIONES|MEDIDAS\s*CORRECTIVAS|PROPUESTAS)": "recommendations",
            r"(?:CONCLUSIONES|SÍNTESIS\s*FINAL)": "conclusions",
            r"(?:ANTECEDENTES|INFORMACIÓN\s*GENERAL)": "background",
            
            # Technical content indicators
            r"(?:SISTEMA\s*ELÉCTRICO|RED\s*DE\s*TRANSMISIÓN)": "electrical_system",
            r"(?:GENERACIÓN|UNIDADES?\s*GENERADORAS?)": "generation_units",
            r"(?:DEMANDA|CONSUMO\s*ELÉCTRICO)": "demand_analysis",
            r"(?:COORDINACIÓN|COORDINADOR\s*ELÉCTRICO)": "coordination",
            
            # Data sections
            r"(?:TABLA|CUADRO|LISTADO)": "data_table",
            r"(?:GRÁFICO|DIAGRAMA|ESQUEMA)": "diagram",
        }

    def load_document(self) -> bool:
        """Load document and prepare for scanning"""
        try:
            print(f"📄 Loading document: {self.document_path.name}")
            self.pdf_reader = PdfReader(str(self.document_path))
            self.total_pages = len(self.pdf_reader.pages)
            
            file_size = self.document_path.stat().st_size / (1024 * 1024)
            print(f"📊 Document loaded: {self.total_pages} pages ({file_size:.1f}MB)")
            print(f"🎯 Starting interactive chapter mapping...")
            print("=" * 70)
            return True
            
        except Exception as e:
            print(f"❌ Error loading document: {e}")
            return False

    def extract_page_text(self, page_num: int) -> str:
        """Extract text from single page (1-indexed)"""
        try:
            if 1 <= page_num <= self.total_pages:
                page = self.pdf_reader.pages[page_num - 1]
                return page.extract_text()
            return ""
        except:
            return ""

    def scan_for_chapters(self, batch_size: int = 10) -> None:
        """Scan document in batches for chapter boundaries"""
        print(f"🔍 Scanning {self.total_pages} pages for chapters...")
        print(f"📦 Processing in batches of {batch_size} pages")
        print("=" * 70)
        
        for batch_start in range(1, self.total_pages + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, self.total_pages)
            
            print(f"\n📦 BATCH: Pages {batch_start}-{batch_end}")
            print("-" * 40)
            
            batch_candidates = []
            
            for page_num in range(batch_start, batch_end + 1):
                candidates = self.analyze_page_for_chapters(page_num)
                batch_candidates.extend(candidates)
            
            if batch_candidates:
                print(f"\n🎯 Found {len(batch_candidates)} potential chapters in this batch:")
                self.validate_batch_candidates(batch_candidates)
            else:
                print("📝 No chapter boundaries detected in this batch")
            
            # Ask to continue
            if batch_end < self.total_pages:
                print(f"\n📊 Progress: {batch_end}/{self.total_pages} pages scanned")
                continue_scan = input("➡️  Continue to next batch? (y/n/save): ").strip().lower()
                
                if continue_scan == 'n':
                    print("⏹️  Stopping scan at your request")
                    break
                elif continue_scan == 'save':
                    self.save_progress()
                    print("💾 Progress saved. Continue scanning? (y/n): ", end="")
                    if input().strip().lower() != 'y':
                        break

    def analyze_page_for_chapters(self, page_num: int) -> List[ChapterCandidate]:
        """Analyze single page for chapter indicators"""
        text = self.extract_page_text(page_num)
        candidates = []
        
        # Look for chapter patterns
        for pattern, chapter_type in self.chapter_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            for match in matches:
                # Extract title context (surrounding text)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 100)
                context = text[start:end].replace('\n', ' ').strip()
                
                # Get preview of page content
                preview = text[:200].replace('\n', ' ').strip()
                if len(text) > 200:
                    preview += "..."
                
                # Determine confidence based on context
                confidence = self.calculate_confidence(text, match, chapter_type)
                
                candidate = ChapterCandidate(
                    page=page_num,
                    title=match.group(0),
                    pattern_matched=pattern,
                    confidence=confidence,
                    preview_text=preview,
                    chapter_type=chapter_type
                )
                
                candidates.append(candidate)
        
        return candidates

    def calculate_confidence(self, text: str, match, chapter_type: str) -> str:
        """Calculate confidence level for chapter detection"""
        # Factors that increase confidence
        factors = []
        
        # Position-based confidence
        if match.start() < 200:  # Near beginning of page
            factors.append("start_of_page")
        
        # Formatting indicators
        if re.search(r'\n\s*' + re.escape(match.group(0)) + r'\s*\n', text):
            factors.append("standalone_line")
        
        # Content length (chapters usually have substantial content)
        if len(text.split()) > 100:
            factors.append("substantial_content")
        
        # Calculate confidence
        if len(factors) >= 3:
            return "HIGH"
        elif len(factors) >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def validate_batch_candidates(self, candidates: List[ChapterCandidate]) -> None:
        """Interactive validation of chapter candidates"""
        for i, candidate in enumerate(candidates, 1):
            print(f"\n📖 CHAPTER CANDIDATE {i}/{len(candidates)}:")
            print(f"📄 Page: {candidate.page}")
            print(f"🏷️  Title: '{candidate.title}'")
            print(f"📊 Type: {candidate.chapter_type}")
            print(f"🎯 Confidence: {candidate.confidence}")
            print(f"📝 Preview: {candidate.preview_text}")
            print("-" * 50)
            
            while True:
                response = input("❓ Is this a chapter start? (y/n/skip/preview): ").strip().lower()
                
                if response == 'y':
                    candidate.validated = True
                    self.validated_chapters.append(candidate)
                    print("✅ Chapter validated and saved!")
                    break
                    
                elif response == 'n':
                    print("❌ Chapter rejected")
                    break
                    
                elif response == 'skip':
                    print("⏩ Skipped")
                    break
                    
                elif response == 'preview':
                    # Show more context
                    full_text = self.extract_page_text(candidate.page)
                    extended_preview = full_text[:800].replace('\n', ' ')
                    print(f"\n📖 EXTENDED PREVIEW (page {candidate.page}):")
                    print("-" * 50)
                    print(extended_preview)
                    print("-" * 50)
                    continue
                    
                else:
                    print("Please enter: y, n, skip, or preview")
                    continue

    def save_progress(self) -> None:
        """Save current progress to profile"""
        progress_data = {
            "document": str(self.document_path),
            "scan_timestamp": datetime.now().isoformat(),
            "total_pages": self.total_pages,
            "chapters_found": len(self.validated_chapters),
            "chapter_structure": [asdict(ch) for ch in self.validated_chapters]
        }
        
        # Save to profile
        profile_file = self.profile_dir / "chapter_structure.json"
        with open(profile_file, "w", encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Progress saved to: {profile_file}")
        
        # Also save a summary
        summary_file = self.profile_dir / "chapter_summary.txt"
        with open(summary_file, "w", encoding='utf-8') as f:
            f.write(f"Anexos EAF Chapter Structure\n")
            f.write(f"Document: {self.document_path.name}\n")
            f.write(f"Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total pages: {self.total_pages}\n")
            f.write(f"Chapters found: {len(self.validated_chapters)}\n\n")
            
            f.write("Chapter Structure:\n")
            f.write("=" * 50 + "\n")
            
            for ch in sorted(self.validated_chapters, key=lambda x: x.page):
                f.write(f"Page {ch.page:3d}: {ch.title} ({ch.chapter_type})\n")
        
        print(f"📋 Summary saved to: {summary_file}")

    def show_final_summary(self) -> None:
        """Show final chapter mapping results"""
        print("\n" + "=" * 70)
        print("🎯 CHAPTER MAPPING COMPLETE")
        print("=" * 70)
        
        if self.validated_chapters:
            print(f"✅ Found {len(self.validated_chapters)} validated chapters:")
            print()
            
            for ch in sorted(self.validated_chapters, key=lambda x: x.page):
                print(f"📄 Page {ch.page:3d}: {ch.title}")
                print(f"    Type: {ch.chapter_type}")
                print(f"    Confidence: {ch.confidence}")
                print()
            
            # Save final results
            self.save_progress()
            
            print("💡 Next Steps:")
            print("1. Review saved chapter structure in profiles/anexos_eaf/")
            print("2. Run Phase 2: Pattern development for each chapter")
            print("3. Begin interactive data extraction")
            
        else:
            print("❌ No chapters were validated")
            print("💡 Try scanning different page ranges or adjusting patterns")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 1: Interactive Chapter Mapper")
    parser.add_argument("document", help="Path to PDF document")
    parser.add_argument("--batch-size", type=int, default=10, help="Pages per batch")
    
    args = parser.parse_args()
    
    if not Path(args.document).exists():
        print(f"❌ Document not found: {args.document}")
        return 1
    
    mapper = InteractiveChapterMapper(args.document)
    
    if not mapper.load_document():
        return 1
    
    try:
        print("\n🚀 PHASE 1: INTERACTIVE CHAPTER MAPPING")
        print("You'll validate each potential chapter boundary in real-time")
        print("Your validated chapters will be saved to profiles/anexos_eaf/")
        print("")
        
        mapper.scan_for_chapters(args.batch_size)
        mapper.show_final_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Mapping interrupted by user")
        if mapper.validated_chapters:
            mapper.save_progress()
            print("💾 Validated chapters saved")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())