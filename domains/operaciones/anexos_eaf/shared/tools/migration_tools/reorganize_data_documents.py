#!/usr/bin/env python3
"""
Data Documents Reorganization Script
=====================================
Reorganizes data/documents to align with new hierarchical structure
"""

import os
import shutil
from pathlib import Path

def create_new_data_structure():
    """Create new hierarchical data structure"""

    base_path = Path("domains/operaciones")

    new_structure = [
        # ANEXOS EAF data structure (aligned with processing structure)
        "anexos_eaf/data/source_documents",                    # Original EAF PDFs
        "anexos_eaf/data/samples_and_tests",                   # Test documents
        "anexos_eaf/data/consolidated_extractions",            # Cross-chapter results

        # Chapter-specific documentation moved to chapter folders
        # (these will link to existing chapter/data/extractions)

        # Future document types (only create when needed)
        "shared/data/compliance_reports/raw",
        "shared/data/compliance_reports/processed",
        "shared/data/compliance_reports/annotations",

        "shared/data/failure_reports/raw",
        "shared/data/failure_reports/processed",
        "shared/data/failure_reports/annotations",

        "shared/data/maintenance_logs/raw",
        "shared/data/maintenance_logs/processed",
        "shared/data/maintenance_logs/annotations",

        # Scraped data (moved from old scraped directory)
        "shared/scrapers/scraped_data/coordinador_cl",
        "shared/scrapers/scraped_data/web_data",
        "shared/scrapers/scraped_data/document_data"
    ]

    for dir_path in new_structure:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created: {dir_path}")

def move_anexos_eaf_data():
    """Move ANEXOS EAF data to new structure"""

    moves = [
        # Move main EAF document storage
        {
            "from": "domains/operaciones/data/documents/anexos_EAF/source_documents",
            "to": "domains/operaciones/anexos_eaf/data/source_documents",
            "type": "directory"
        },
        {
            "from": "domains/operaciones/data/documents/anexos_EAF/samples_and_tests",
            "to": "domains/operaciones/anexos_eaf/data/samples_and_tests",
            "type": "directory"
        },

        # Move chapter documentation to chapter-specific folders
        {
            "from": "domains/operaciones/data/documents/anexos_EAF/documentation/anexo_01_generation_programming",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_01/data/documentation",
            "type": "directory"
        },
        {
            "from": "domains/operaciones/data/documents/anexos_EAF/documentation/anexo_02_real_generation",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_02/data/documentation",
            "type": "directory"
        },
        {
            "from": "domains/operaciones/data/documents/anexos_EAF/documentation/informe_diario_day1",
            "to": "domains/operaciones/anexos_eaf/chapters/informe_diario/data/documentation",
            "type": "directory"
        }
    ]

    print("\n📦 Moving ANEXOS EAF data...")
    for move in moves:
        if move.get("type") == "directory":
            move_directory_safely(move["from"], move["to"])

def move_other_document_types():
    """Move other document types to shared data"""

    moves = [
        # Compliance reports
        {
            "from": "domains/operaciones/data/documents/compliance_reports",
            "to": "domains/operaciones/shared/data/compliance_reports",
            "type": "directory"
        },

        # Failure reports
        {
            "from": "domains/operaciones/data/documents/failure_reports",
            "to": "domains/operaciones/shared/data/failure_reports",
            "type": "directory"
        },

        # Maintenance logs
        {
            "from": "domains/operaciones/data/documents/maintenance_logs",
            "to": "domains/operaciones/shared/data/maintenance_logs",
            "type": "directory"
        }
    ]

    print("\n📦 Moving other document types to shared...")
    for move in moves:
        if move.get("type") == "directory":
            move_directory_safely(move["from"], move["to"])

def move_scraped_data():
    """Move scraped data to shared scrapers"""

    scraped_source = Path("domains/operaciones/scraped")
    scraped_target = Path("domains/operaciones/shared/scrapers/scraped_data")

    if scraped_source.exists():
        print(f"\n📦 Moving scraped data...")
        move_directory_safely(str(scraped_source), str(scraped_target / "legacy_scraped"))

def create_documentation_links():
    """Create documentation explaining the new structure"""

    readme_content = """# Data Documents Structure

## New Hierarchical Organization

This directory has been reorganized to align with the new hierarchical processing structure:

### ANEXOS EAF Data
```
anexos_eaf/data/
├── source_documents/           # Original EAF PDF files
├── samples_and_tests/         # Test documents for development
└── consolidated_extractions/  # Cross-chapter analysis results
```

### Chapter-Specific Data
```
anexos_eaf/chapters/anexo_XX/data/
├── extractions/              # Processed extraction results
└── documentation/            # Chapter-specific documentation
```

### Shared Data (Future Document Types)
```
shared/data/
├── compliance_reports/       # Compliance document storage
├── failure_reports/          # Failure report storage
├── maintenance_logs/         # Maintenance log storage
└── scrapers/scraped_data/    # Web-scraped data storage
```

## Data Flow

1. **Source documents** → stored in appropriate document type folder
2. **Processing** → chapter-specific processors extract data
3. **Results** → stored in chapter-specific data/extractions
4. **Consolidation** → cross-chapter analysis in consolidated_extractions

## Migration Notes

- Chapter documentation moved from `data/documents/anexos_EAF/documentation/` to `anexos_eaf/chapters/*/data/documentation/`
- Future document types moved to `shared/data/` for cross-domain access
- Scraped data centralized in `shared/scrapers/scraped_data/`
"""

    readme_path = Path("domains/operaciones/data/README.md")
    readme_path.write_text(readme_content)
    print(f"📝 Created documentation: {readme_path}")

def move_directory_safely(from_path: str, to_path: str):
    """Safely move a directory"""

    source = Path(from_path)
    target = Path(to_path)

    if not source.exists():
        print(f"⚠️ Source directory not found: {from_path}")
        return

    # Create parent directory
    target.parent.mkdir(parents=True, exist_ok=True)

    # Move directory
    if target.exists():
        print(f"⚠️ Target directory exists, merging: {to_path}")
        # Merge directories
        for item in source.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(source)
                target_file = target / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(target_file))

        # Remove empty source directory
        try:
            source.rmdir()
        except OSError:
            print(f"⚠️ Could not remove source directory (not empty): {from_path}")
    else:
        shutil.move(str(source), str(target))

    print(f"✅ Moved directory: {from_path} → {to_path}")

def cleanup_old_structure():
    """Clean up old empty directories"""

    old_dirs_to_remove = [
        "domains/operaciones/data/documents/anexos_EAF/documentation",
        "domains/operaciones/data/documents/anexos_EAF",
        "domains/operaciones/data/documents/EAF",
        "domains/operaciones/scraped"
    ]

    print("\n🧹 Cleaning up old directories...")
    for old_dir in old_dirs_to_remove:
        old_path = Path(old_dir)
        if old_path.exists() and not any(old_path.iterdir()):  # Only remove if empty
            old_path.rmdir()
            print(f"🗑️ Removed empty directory: {old_dir}")

if __name__ == "__main__":
    print("🚀 Reorganizing Data Documents Structure")
    print("=" * 50)

    print("\n1️⃣ Creating new directory structure...")
    create_new_data_structure()

    print("\n2️⃣ Moving ANEXOS EAF data...")
    move_anexos_eaf_data()

    print("\n3️⃣ Moving other document types...")
    move_other_document_types()

    print("\n4️⃣ Moving scraped data...")
    move_scraped_data()

    print("\n5️⃣ Creating documentation...")
    create_documentation_links()

    print("\n6️⃣ Cleaning up old structure...")
    cleanup_old_structure()

    print("\n✅ Data documents reorganization completed!")
    print("🔧 New structure aligns with hierarchical processing architecture")