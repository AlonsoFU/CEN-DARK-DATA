#!/usr/bin/env python3
"""
True Interactive Title Detector
- Scans for pages that START with "Anexo" or "INFORME DIARIO" 
- Shows you each page with minimal content (title only)
- You validate each title in real-time with y/n
- Saves validated titles to profiles/anexos_eaf/
"""
import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Installing PyPDF2...")
    os.system("pip install PyPDF2")
    from PyPDF2 import PdfReader

@dataclass
class TitlePage:
    page_number: int
    title_text: str
    full_page_text: str
    word_count: int
    validated: bool = False

class InteractiveTitleDetector:
    def __init__(self, document_path: str):
        self.document_path = Path(document_path)
        self.profile_dir = Path("profiles/anexos_eaf")
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        self.pdf_reader = None
        self.total_pages = 0
        self.validated_titles: List[TitlePage] = []

    def load_document(self) -> bool:
        """Load PDF document"""
        try:
            print(f"📄 Loading: {self.document_path.name}")
            self.pdf_reader = PdfReader(str(self.document_path))
            self.total_pages = len(self.pdf_reader.pages)
            
            file_size = self.document_path.stat().st_size / (1024 * 1024)
            print(f"📊 Loaded: {self.total_pages} pages ({file_size:.1f}MB)")
            return True
            
        except Exception as e:
            print(f"❌ Error loading: {e}")
            return False

    def extract_page_text(self, page_num: int) -> str:
        """Extract text from page (1-indexed)"""
        try:
            if 1 <= page_num <= self.total_pages:
                page = self.pdf_reader.pages[page_num - 1]
                return page.extract_text().strip()
            return ""
        except:
            return ""

    def is_title_page(self, text: str) -> tuple[bool, str]:
        """Check if page matches title criteria"""
        # Clean text
        clean_text = text.strip()
        words = clean_text.split()
        
        # Rule 1: Must start with "Anexo" or "INFORME DIARIO"
        title_patterns = [
            r'^ANEXO\s+N[º°ªo]?\s*\d+',
            r'^INFORME\s+DIARIO'
        ]
        
        starts_with_title = False
        matched_title = ""
        
        for pattern in title_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                starts_with_title = True
                matched_title = match.group(0)
                break
        
        if not starts_with_title:
            return False, ""
        
        # Rule 2: Title-only page (minimal content)
        # Should have low word count (title + maybe subtitle)
        word_count = len(words)
        
        # Title pages typically have < 50 words (just title and maybe date/subtitle)
        is_minimal = word_count < 50
        
        return is_minimal, matched_title

    def scan_for_titles_interactive(self, batch_size: int = 20) -> None:
        """Scan document interactively for title pages"""
        print(f"\n🔍 INTERACTIVE TITLE DETECTION")
        print(f"Looking for pages that:")
        print(f"  ✅ Start with 'Anexo' or 'INFORME DIARIO'")
        print(f"  ✅ Have minimal content (title only)")
        print("=" * 60)
        
        title_candidates = []
        
        # Scan all pages for potential titles
        for page_num in range(1, self.total_pages + 1):
            text = self.extract_page_text(page_num)
            is_title, title_text = self.is_title_page(text)
            
            if is_title:
                candidate = TitlePage(
                    page_number=page_num,
                    title_text=title_text,
                    full_page_text=text,
                    word_count=len(text.split())
                )
                title_candidates.append(candidate)
        
        print(f"\n🎯 Found {len(title_candidates)} potential title pages")
        print("Now validating each one with you...")
        print("=" * 60)
        
        # Interactive validation
        for i, candidate in enumerate(title_candidates, 1):
            self.validate_title_interactive(candidate, i, len(title_candidates))

    def validate_title_interactive(self, candidate: TitlePage, current: int, total: int) -> None:
        """Interactive validation of single title"""
        print(f"\n📖 TITLE CANDIDATE {current}/{total}")
        print("=" * 40)
        print(f"📄 Page: {candidate.page_number}")
        print(f"🏷️  Detected Title: '{candidate.title_text}'")
        print(f"📊 Word Count: {candidate.word_count} words")
        print(f"📝 Full Page Content:")
        print("-" * 30)
        print(candidate.full_page_text)
        print("-" * 30)
        
        # Interactive validation loop
        while True:
            print(f"\n❓ Is this a valid title page?")
            print(f"   y = Yes, this is a title page")
            print(f"   n = No, skip this page")
            print(f"   m = Show more context")
            print(f"   q = Quit and save progress")
            
            response = input("👉 Your choice (y/n/m/q): ").strip().lower()
            
            if response == 'y':
                candidate.validated = True
                self.validated_titles.append(candidate)
                print("✅ Title validated and saved!")
                break
                
            elif response == 'n':
                print("❌ Title rejected")
                break
                
            elif response == 'm':
                # Show surrounding pages for context
                print(f"\n🔍 CONTEXT AROUND PAGE {candidate.page_number}:")
                for context_page in range(max(1, candidate.page_number - 1), 
                                        min(self.total_pages + 1, candidate.page_number + 2)):
                    context_text = self.extract_page_text(context_page)
                    preview = context_text[:200].replace('\n', ' ') if context_text else "[Empty page]"
                    marker = " ← CURRENT" if context_page == candidate.page_number else ""
                    print(f"Page {context_page}: {preview}...{marker}")
                print("-" * 50)
                continue
                
            elif response == 'q':
                print("⏹️  Stopping at your request")
                self.save_progress()
                return
                
            else:
                print("❌ Please enter: y, n, m, or q")
                continue

    def save_progress(self) -> None:
        """Save validated titles to profile"""
        if not self.validated_titles:
            print("⚠️  No validated titles to save")
            return
            
        # Save detailed results
        title_data = {
            "document": str(self.document_path),
            "scan_timestamp": datetime.now().isoformat(),
            "total_pages": self.total_pages,
            "titles_found": len(self.validated_titles),
            "validated_titles": [asdict(title) for title in self.validated_titles]
        }
        
        titles_file = self.profile_dir / "validated_titles.json"
        with open(titles_file, "w", encoding='utf-8') as f:
            json.dump(title_data, f, indent=2, ensure_ascii=False)
        
        # Save simple title list
        titles_list_file = self.profile_dir / "title_structure.txt"
        with open(titles_list_file, "w", encoding='utf-8') as f:
            f.write(f"Anexos EAF - Validated Titles\n")
            f.write(f"Document: {self.document_path.name}\n")
            f.write(f"Validated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total titles: {len(self.validated_titles)}\n\n")
            
            for title in sorted(self.validated_titles, key=lambda x: x.page_number):
                f.write(f"Page {title.page_number:3d}: {title.title_text}\n")
                f.write(f"           ({title.word_count} words)\n\n")
        
        print(f"💾 Titles saved to: {titles_file}")
        print(f"📋 Summary saved to: {titles_list_file}")

    def show_final_results(self) -> None:
        """Show final validation results"""
        print("\n" + "=" * 60)
        print("🎯 TITLE DETECTION COMPLETE")
        print("=" * 60)
        
        if self.validated_titles:
            print(f"✅ Validated {len(self.validated_titles)} titles:")
            print()
            
            for title in sorted(self.validated_titles, key=lambda x: x.page_number):
                print(f"📄 Page {title.page_number:3d}: {title.title_text}")
                print(f"           ({title.word_count} words)")
            
            print(f"\n💾 Results saved to: profiles/anexos_eaf/")
            
            print(f"\n💡 Next Steps:")
            print(f"1. Review saved titles in profiles/anexos_eaf/")
            print(f"2. Phase 2: Develop extraction patterns for each title section")
            print(f"3. Phase 3: Interactive data extraction")
            
        else:
            print("❌ No titles were validated")
            
        print("=" * 60)

def main():
    doc_path = "data/documents/anexos_EAF/raw/Anexos-EAF-089-2025.pdf"
    
    if not Path(doc_path).exists():
        print(f"❌ Document not found: {doc_path}")
        return 1
    
    detector = InteractiveTitleDetector(doc_path)
    
    if not detector.load_document():
        return 1
    
    try:
        print("\n🚀 TRUE INTERACTIVE TITLE DETECTION")
        print("You will validate each potential title page in real-time")
        print("Only pages YOU approve will be saved to profiles/anexos_eaf/")
        
        detector.scan_for_titles_interactive()
        detector.save_progress()
        detector.show_final_results()
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Process interrupted")
        detector.save_progress()
        print("💾 Progress saved")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())