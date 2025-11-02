#!/usr/bin/env python3
"""
Semantic Hierarchy Builder for Docling JSON

Enhances Docling's flat structure with semantic parent-child relationships.

This post-processor:
1. Detects section headers (patterns: "a.", "1.", "7.2", etc.)
2. Groups content under headers (tables, text, figures)
3. Builds hierarchical relationships
4. Adds semantic context

Usage:
    python build_semantic_hierarchy.py <docling_json> <output_json>

Example:
    python build_semantic_hierarchy.py docling_complete.json docling_hierarchical.json
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class HierarchyBuilder:
    """Builds semantic hierarchy from flat Docling JSON"""

    # Header patterns (ordered by specificity)
    HEADER_PATTERNS = [
        r'^([a-z])\.\s+(.+)',           # a. Title
        r'^(\d+)\.\s+(.+)',             # 1. Title
        r'^([a-z])\.(\d+)\s+(.+)',      # a.1 Title
        r'^(\d+)\.(\d+)\s+(.+)',        # 1.2 Title
        r'^(\d+)\.(\d+)\.(\d+)\s+(.+)', # 1.2.3 Title
    ]

    def __init__(self, docling_json: Dict[str, Any]):
        """
        Initialize with Docling JSON

        Args:
            docling_json: Complete Docling JSON output
        """
        self.data = docling_json
        self.body = docling_json.get('body', {})
        self.children_refs = self.body.get('children', [])

        # Content arrays
        self.texts = {t['self_ref']: t for t in docling_json.get('texts', [])}
        self.tables = {t['self_ref']: t for t in docling_json.get('tables', [])}
        self.pictures = {p['self_ref']: p for p in docling_json.get('pictures', [])}

        # Hierarchy result
        self.hierarchy = []
        self.current_section = None

    def is_header(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Check if text is a section header

        Args:
            text: Text content to check

        Returns:
            Dict with header info if matched, None otherwise
        """
        text = text.strip()

        for pattern in self.HEADER_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                number = '.'.join(groups[:-1])  # Everything except title
                title = groups[-1].strip()

                # Determine level by number of dots
                level = number.count('.') + 1

                return {
                    'number': number,
                    'title': title,
                    'level': level,
                    'full_text': text
                }

        return None

    def get_item_by_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """Get item by reference"""
        ref_str = ref.get('$ref', '')

        if ref_str in self.texts:
            return {'type': 'text', 'item': self.texts[ref_str]}
        elif ref_str in self.tables:
            return {'type': 'table', 'item': self.tables[ref_str]}
        elif ref_str in self.pictures:
            return {'type': 'picture', 'item': self.pictures[ref_str]}

        return None

    def build_hierarchy(self) -> List[Dict[str, Any]]:
        """
        Build semantic hierarchy from flat structure

        Returns:
            List of sections with children
        """
        hierarchy = []
        current_section = None

        for ref in self.children_refs:
            item_data = self.get_item_by_ref(ref)

            if not item_data:
                continue

            item_type = item_data['type']
            item = item_data['item']

            # Check if this is a header
            if item_type == 'text':
                text_content = item.get('text', '')
                header_info = self.is_header(text_content)

                if header_info:
                    # This is a section header - create new section
                    current_section = {
                        'section_header': header_info,
                        'header_ref': item['self_ref'],
                        'header_bbox': item.get('prov', [{}])[0].get('bbox'),
                        'header_page': item.get('prov', [{}])[0].get('page_no'),
                        'children': [],
                        'content_summary': {
                            'texts': 0,
                            'tables': 0,
                            'pictures': 0
                        }
                    }
                    hierarchy.append(current_section)
                    continue

            # Not a header - add to current section if exists
            if current_section is not None:
                child_entry = {
                    'type': item_type,
                    'ref': item['self_ref'],
                    'page': item.get('prov', [{}])[0].get('page_no'),
                    'bbox': item.get('prov', [{}])[0].get('bbox')
                }

                # Add type-specific info
                if item_type == 'text':
                    child_entry['text'] = item.get('text', '')
                    current_section['content_summary']['texts'] += 1

                elif item_type == 'table':
                    cells = item.get('data', {}).get('table_cells', [])
                    child_entry['cell_count'] = len(cells)
                    child_entry['preview'] = cells[0].get('text', '') if cells else ''
                    current_section['content_summary']['tables'] += 1

                elif item_type == 'picture':
                    current_section['content_summary']['pictures'] += 1

                current_section['children'].append(child_entry)

        return hierarchy

    def build_enhanced_json(self) -> Dict[str, Any]:
        """
        Build enhanced JSON with hierarchy

        Returns:
            Enhanced Docling JSON with semantic_hierarchy added
        """
        hierarchy = self.build_hierarchy()

        # Clone original data
        enhanced = dict(self.data)

        # Add hierarchy
        enhanced['semantic_hierarchy'] = {
            'version': '1.0',
            'description': 'Semantic parent-child relationships extracted from document structure',
            'sections': hierarchy,
            'metadata': {
                'total_sections': len(hierarchy),
                'section_levels': sorted(set(s['section_header']['level'] for s in hierarchy))
            }
        }

        return enhanced


def build_hierarchy_from_file(input_path: Path, output_path: Path):
    """
    Build semantic hierarchy from Docling JSON file

    Args:
        input_path: Path to docling_complete.json
        output_path: Path to save enhanced JSON
    """
    print("=" * 80)
    print("SEMANTIC HIERARCHY BUILDER")
    print("=" * 80)
    print(f"\n📄 Input: {input_path}")
    print(f"📁 Output: {output_path}")

    # Load Docling JSON
    print("\n🔄 Loading Docling JSON...")
    with open(input_path) as f:
        docling_json = json.load(f)

    # Build hierarchy
    print("🔨 Building semantic hierarchy...")
    builder = HierarchyBuilder(docling_json)
    enhanced_json = builder.build_enhanced_json()

    # Statistics
    hierarchy = enhanced_json['semantic_hierarchy']
    sections = hierarchy['sections']

    print(f"\n✅ Hierarchy built successfully!")
    print(f"\n📊 Statistics:")
    print(f"   Total sections: {len(sections)}")

    # Show section summary
    print(f"\n📋 Sections found:")
    for i, section in enumerate(sections[:10], 1):  # Show first 10
        header = section['section_header']
        summary = section['content_summary']
        print(f"   {i}. [{header['number']}] {header['title']}")
        print(f"      Level: {header['level']} | "
              f"Page: {section['header_page']} | "
              f"Content: {summary['texts']} texts, {summary['tables']} tables, {summary['pictures']} pictures")

    if len(sections) > 10:
        print(f"   ... and {len(sections) - 10} more sections")

    # Save enhanced JSON
    print(f"\n💾 Saving enhanced JSON...")
    with open(output_path, 'w') as f:
        json.dump(enhanced_json, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Saved: {output_path}")
    print(f"   Size: {file_size_mb:.2f} MB")

    print("\n" + "=" * 80)
    print("✅ SEMANTIC HIERARCHY COMPLETE")
    print("=" * 80)
    print("\n📊 Enhanced JSON now includes:")
    print("   • Original Docling data (texts, tables, pictures)")
    print("   • Semantic hierarchy (sections with children)")
    print("   • Parent-child relationships")
    print("   • Content summaries per section")

    # Example usage
    print("\n💡 Usage example:")
    print("""
    import json

    with open('docling_hierarchical.json') as f:
        data = json.load(f)

    # Access semantic hierarchy
    sections = data['semantic_hierarchy']['sections']

    # Find section "a. Fecha y Hora"
    for section in sections:
        if section['section_header']['number'] == 'a':
            print(f"Section: {section['section_header']['title']}")
            print(f"Children: {len(section['children'])}")

            for child in section['children']:
                if child['type'] == 'table':
                    print(f"  → Table with {child['cell_count']} cells")
    """)


def main():
    """Command-line interface"""
    import sys

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)

    try:
        build_hierarchy_from_file(input_path, output_path)
    except Exception as e:
        print(f"\n❌ Error building hierarchy: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
