#!/usr/bin/env python3
"""
Path Migration Script
====================
Fixes all path references when moving to new hierarchical structure
"""

import os
import re
from pathlib import Path

def fix_project_root_paths():
    """Fix project root path calculations in all processors"""

    changes = {
        # OLD: 6 levels up from scripts/eaf_workflows/eaf_processing/chapters/anexo_XX/content_extraction/
        # NEW: 5 levels up from domains/operaciones/anexos_eaf/chapters/anexo_XX/processors/
        "Path(__file__).parent.parent.parent.parent.parent.parent": "Path(__file__).parent.parent.parent.parent.parent"
    }

    files_to_fix = [
        "domains/operaciones/anexos_eaf/chapters/anexo_01/processors/anexo_01_processor.py",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/processors/anexo_02_processor.py",
        "domains/operaciones/anexos_eaf/chapters/informe_diario/processors/informe_diario_processor.py"
    ]

    for file_path in files_to_fix:
        if Path(file_path).exists():
            fix_file_paths(file_path, changes)
            print(f"✅ Fixed project root paths in {file_path}")

def fix_import_paths():
    """Fix import statements for moved files"""

    changes = {
        # Schema imports
        "from esquema_universal_chileno import": "from domains.operaciones.shared.utilities.esquema_universal_chileno import",
        "from referencias_cruzadas import": "from domains.operaciones.shared.utilities.referencias_cruzadas import",

        # Chapter detection imports
        "from interactive_chapter_mapper import": "from domains.operaciones.shared.chapter_detection.interactive_chapter_mapper import",
        "from find_all_document_titles import": "from domains.operaciones.shared.chapter_detection.find_all_document_titles import",
    }

    # Fix imports in utilities
    files_to_fix = [
        "domains/operaciones/shared/utilities/extractor_universal_integrado.py",
        "domains/operaciones/shared/utilities/referencias_cruzadas.py",
        "domains/operaciones/shared/utilities/esquema_universal_chileno.py"
    ]

    for file_path in files_to_fix:
        if Path(file_path).exists():
            fix_file_paths(file_path, changes)
            print(f"✅ Fixed import paths in {file_path}")

def fix_data_directory_paths():
    """Fix hardcoded data directory references"""

    changes = {
        # OLD hardcoded paths
        'Path("domains/operaciones/extractions")': 'self._get_chapter_extractions_path()',
        '"domains/operaciones/extractions"': 'self._get_chapter_extractions_path()',

        # Pattern file references
        '"patterns/anexos_eaf/"': '"domains/operaciones/anexos_eaf/chapters/{chapter}/patterns/"',
    }

    files_to_fix = [
        "domains/operaciones/shared/utilities/extractor_universal_integrado.py"
    ]

    for file_path in files_to_fix:
        if Path(file_path).exists():
            fix_file_paths(file_path, changes)
            print(f"✅ Fixed data directory paths in {file_path}")

def fix_file_paths(file_path: str, changes: dict):
    """Apply path changes to a specific file"""

    file_obj = Path(file_path)
    if not file_obj.exists():
        print(f"⚠️ File not found: {file_path}")
        return

    # Read file content
    content = file_obj.read_text()

    # Apply all changes
    modified = False
    for old_path, new_path in changes.items():
        if old_path in content:
            content = content.replace(old_path, new_path)
            modified = True
            print(f"  📝 Replaced: {old_path} → {new_path}")

    # Write back if modified
    if modified:
        file_obj.write_text(content)
        print(f"✅ Updated: {file_path}")
    else:
        print(f"📄 No changes needed: {file_path}")

def add_helper_methods():
    """Add helper methods for dynamic path resolution"""

    helper_code = '''
    def _get_chapter_extractions_path(self, chapter_type: str = None) -> Path:
        """Get extractions path for specific chapter"""
        if chapter_type:
            return Path(f"domains/operaciones/anexos_eaf/chapters/{chapter_type}/data/extractions")
        else:
            return Path("domains/operaciones/anexos_eaf/data/consolidated_extractions")

    def _get_chapter_patterns_path(self, chapter_type: str) -> Path:
        """Get patterns path for specific chapter"""
        return Path(f"domains/operaciones/anexos_eaf/chapters/{chapter_type}/patterns")
    '''

    # Add to extractor_universal_integrado.py
    extractor_file = Path("domains/operaciones/shared/utilities/extractor_universal_integrado.py")
    if extractor_file.exists():
        content = extractor_file.read_text()
        if "_get_chapter_extractions_path" not in content:
            # Add methods to class
            content = content.replace(
                "class ExtractorUniversalIntegrado:",
                f"class ExtractorUniversalIntegrado:{helper_code}"
            )
            extractor_file.write_text(content)
            print("✅ Added helper methods to ExtractorUniversalIntegrado")

def verify_migration():
    """Verify that all critical files exist and have correct paths"""

    critical_files = [
        "domains/operaciones/anexos_eaf/chapters/anexo_01/processors/anexo_01_processor.py",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/processors/anexo_02_processor.py",
        "domains/operaciones/shared/utilities/extractor_universal_integrado.py",
        "domains/operaciones/shared/chapter_detection/interactive_chapter_mapper.py",
    ]

    print("\n🔍 Migration Verification:")
    print("=" * 50)

    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ MISSING: {file_path}")

if __name__ == "__main__":
    print("🚀 Starting Path Migration for Hierarchical Structure")
    print("=" * 60)

    print("\n1️⃣ Fixing project root paths...")
    fix_project_root_paths()

    print("\n2️⃣ Fixing import paths...")
    fix_import_paths()

    print("\n3️⃣ Fixing data directory paths...")
    fix_data_directory_paths()

    print("\n4️⃣ Adding helper methods...")
    add_helper_methods()

    print("\n5️⃣ Verifying migration...")
    verify_migration()

    print("\n✅ Path migration completed!")
    print("🔧 Next steps:")
    print("   1. Move files to new structure manually")
    print("   2. Run this script to fix paths")
    print("   3. Test processors to ensure they work")