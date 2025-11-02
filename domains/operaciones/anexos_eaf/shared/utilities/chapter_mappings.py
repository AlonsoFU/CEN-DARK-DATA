#!/usr/bin/env python3
"""
Chapter Mappings Utility - EAF Documents
========================================

Provides centralized access to chapter definitions and page mappings for EAF document processing.
All chapter metadata, page ranges, and processing information is centralized here.

Usage:
    from domains.operaciones.anexos_eaf.shared.utilities.chapter_mappings import ChapterMappings

    chapters = ChapterMappings()
    page_range = chapters.get_page_range("anexo_02")  # (63, 95)
    is_implemented = chapters.is_implemented("anexo_01")  # True
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


class ChapterMappings:
    """Centralized access to EAF chapter definitions and page mappings"""

    def __init__(self):
        """Load chapter definitions from JSON file"""
        self.definitions_path = Path(__file__).parent.parent / "chapter_definitions.json"
        self.data = self._load_definitions()
        self.chapters = self.data.get("chapters", {})
        self.metadata = self.data.get("document_metadata", {})

    def _load_definitions(self) -> Dict[str, Any]:
        """Load chapter definitions from JSON file"""
        try:
            with open(self.definitions_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Chapter definitions not found: {self.definitions_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in chapter definitions: {e}")

    def get_chapter_info(self, chapter_id: str) -> Dict[str, Any]:
        """Get complete information for a chapter"""
        if chapter_id not in self.chapters:
            raise ValueError(f"Chapter '{chapter_id}' not found. Available: {list(self.chapters.keys())}")
        return self.chapters[chapter_id]

    def get_page_range(self, chapter_id: str) -> Tuple[int, int]:
        """Get page range for a chapter as (start, end) tuple"""
        chapter_info = self.get_chapter_info(chapter_id)
        pages = chapter_info["pages"]
        return (pages["start"], pages["end"])

    def get_page_list(self, chapter_id: str) -> List[int]:
        """Get list of all pages for a chapter"""
        start, end = self.get_page_range(chapter_id)
        return list(range(start, end + 1))

    def get_total_pages(self, chapter_id: str) -> int:
        """Get total number of pages for a chapter"""
        chapter_info = self.get_chapter_info(chapter_id)
        return chapter_info["pages"]["total"]

    def is_implemented(self, chapter_id: str) -> bool:
        """Check if chapter is implemented"""
        chapter_info = self.get_chapter_info(chapter_id)
        return chapter_info["status"] == "implemented"

    def get_processor_name(self, chapter_id: str) -> str:
        """Get processor filename for a chapter"""
        chapter_info = self.get_chapter_info(chapter_id)
        return chapter_info["processor"]

    def get_chapter_name(self, chapter_id: str) -> str:
        """Get human-readable chapter name"""
        chapter_info = self.get_chapter_info(chapter_id)
        return chapter_info["name"]

    def get_chapter_description(self, chapter_id: str) -> str:
        """Get chapter description"""
        chapter_info = self.get_chapter_info(chapter_id)
        return chapter_info["description"]

    def get_content_focus(self, chapter_id: str) -> List[str]:
        """Get content focus areas for a chapter"""
        chapter_info = self.get_chapter_info(chapter_id)
        return chapter_info.get("content_focus", [])

    def get_implemented_chapters(self) -> List[str]:
        """Get list of implemented chapter IDs"""
        return [chapter_id for chapter_id, info in self.chapters.items()
                if info["status"] == "implemented"]

    def get_planned_chapters(self) -> List[str]:
        """Get list of planned chapter IDs"""
        return [chapter_id for chapter_id, info in self.chapters.items()
                if info["status"] == "planned"]

    def get_all_chapters(self) -> List[str]:
        """Get list of all chapter IDs"""
        return list(self.chapters.keys())

    def find_chapter_by_page(self, page_number: int) -> Optional[str]:
        """Find which chapter contains a specific page number"""
        for chapter_id, info in self.chapters.items():
            start, end = info["pages"]["start"], info["pages"]["end"]
            if start <= page_number <= end:
                return chapter_id
        return None

    def get_document_metadata(self) -> Dict[str, Any]:
        """Get document metadata"""
        return self.metadata

    def get_source_document(self) -> str:
        """Get source document name"""
        return self.metadata.get("source", "EAF-089-2025")

    def get_total_document_pages(self) -> int:
        """Get total pages in the document"""
        return self.metadata.get("total_pages", 399)

    def validate_page_range(self, chapter_id: str, page_number: int) -> bool:
        """Validate if a page number is within chapter range"""
        try:
            start, end = self.get_page_range(chapter_id)
            return start <= page_number <= end
        except ValueError:
            return False

    def get_extraction_stats(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """Get extraction statistics for a chapter (if available)"""
        chapter_info = self.get_chapter_info(chapter_id)
        return chapter_info.get("extraction_stats")

    def print_chapter_summary(self, chapter_id: str = None) -> None:
        """Print summary of chapter(s)"""
        if chapter_id:
            chapters_to_show = [chapter_id]
        else:
            chapters_to_show = self.get_all_chapters()

        print("📚 EAF CHAPTER DEFINITIONS")
        print("=" * 50)

        for cid in chapters_to_show:
            info = self.get_chapter_info(cid)
            status_icon = "✅" if info["status"] == "implemented" else "🚧"

            print(f"\n{status_icon} {cid.upper()}: {info['name']}")
            print(f"   📄 Pages: {info['pages']['range']} ({info['pages']['total']} pages)")
            print(f"   📝 Description: {info['description']}")
            print(f"   🔧 Processor: {info['processor']}")
            print(f"   📊 Status: {info['status']}")

            if "extraction_stats" in info:
                stats = info["extraction_stats"]
                print(f"   📈 Stats: {stats.get('plants_extracted', 'N/A')} plants, {stats.get('success_rate', 'N/A')} success")


# Convenience functions for direct import
def get_page_range(chapter_id: str) -> Tuple[int, int]:
    """Quick access to page range"""
    return ChapterMappings().get_page_range(chapter_id)

def get_page_list(chapter_id: str) -> List[int]:
    """Quick access to page list"""
    return ChapterMappings().get_page_list(chapter_id)

def is_implemented(chapter_id: str) -> bool:
    """Quick check if chapter is implemented"""
    return ChapterMappings().is_implemented(chapter_id)

def find_chapter_by_page(page_number: int) -> Optional[str]:
    """Quick lookup of chapter by page number"""
    return ChapterMappings().find_chapter_by_page(page_number)


if __name__ == "__main__":
    # Demo usage
    chapters = ChapterMappings()
    chapters.print_chapter_summary()

    print(f"\n🔍 QUICK LOOKUPS:")
    print(f"   Page 70 belongs to: {find_chapter_by_page(70)}")
    print(f"   ANEXO 2 pages: {get_page_range('anexo_02')}")
    print(f"   INFORME DIARIO implemented: {is_implemented('informe_diario')}")