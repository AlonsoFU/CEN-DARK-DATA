#!/usr/bin/env python3
"""
File Movement Script
===================
Moves all files from current structure to new hierarchical structure
"""

import os
import shutil
from pathlib import Path

def create_new_directory_structure():
    """Create the new hierarchical directory structure"""

    new_structure = [
        # ANEXOS EAF structure
        "domains/operaciones/anexos_eaf/chapters/anexo_01/processors",
        "domains/operaciones/anexos_eaf/chapters/anexo_01/universal_schema_adapters",
        "domains/operaciones/anexos_eaf/chapters/anexo_01/patterns",
        "domains/operaciones/anexos_eaf/chapters/anexo_01/processing_docs",
        "domains/operaciones/anexos_eaf/chapters/anexo_01/data/extractions",

        "domains/operaciones/anexos_eaf/chapters/anexo_02/processors",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/universal_schema_adapters",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/patterns",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/processing_docs",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/data/extractions",

        "domains/operaciones/anexos_eaf/chapters/informe_diario/processors",
        "domains/operaciones/anexos_eaf/chapters/informe_diario/universal_schema_adapters",
        "domains/operaciones/anexos_eaf/chapters/informe_diario/patterns",
        "domains/operaciones/anexos_eaf/chapters/informe_diario/processing_docs",
        "domains/operaciones/anexos_eaf/chapters/informe_diario/data/extractions",

        "domains/operaciones/anexos_eaf/document_metadata",
        "domains/operaciones/anexos_eaf/workflows",
        "domains/operaciones/anexos_eaf/data/source_documents",
        "domains/operaciones/anexos_eaf/data/consolidated_extractions",

        # Shared structure
        "domains/operaciones/shared/chapter_detection",
        "domains/operaciones/shared/validated_results",
        "domains/operaciones/shared/schemas",
        "domains/operaciones/shared/utilities",
        "domains/operaciones/shared/verification",
        "domains/operaciones/shared/tools/migration_tools",
        "domains/operaciones/shared/tools/experimental"
    ]

    for dir_path in new_structure:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created: {dir_path}")

def move_processors():
    """Move processor files to new locations"""

    moves = [
        # ANEXO 1 processor
        {
            "from": "domains/operaciones/scripts/eaf_workflows/eaf_processing/chapters/anexo_01_generation_programming/content_extraction/extract_anexo1_with_ocr_per_row.py",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_01/processors/anexo_01_processor.py"
        },
        # ANEXO 2 processor
        {
            "from": "domains/operaciones/scripts/eaf_workflows/eaf_processing/chapters/anexo_02_real_generation/content_extraction/extract_anexo2_real_generation.py",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_02/processors/anexo_02_processor.py"
        },
        # Daily report processor
        {
            "from": "domains/operaciones/scripts/eaf_workflows/eaf_processing/chapters/informe_diario_day1/content_extraction/extract_informe_diario_day1.py",
            "to": "domains/operaciones/anexos_eaf/chapters/informe_diario/processors/informe_diario_processor.py"
        }
    ]

    for move in moves:
        move_file_safely(move["from"], move["to"])

def move_chapter_detection():
    """Move chapter detection system to shared"""

    moves = [
        {
            "from": "domains/operaciones/scripts/eaf_workflows/eaf_processing/01_title_detection/phase1_chapter_mapper.py",
            "to": "domains/operaciones/shared/chapter_detection/interactive_chapter_mapper.py"
        },
        {
            "from": "domains/operaciones/scripts/eaf_workflows/eaf_processing/01_title_detection/find_all_document_titles.py",
            "to": "domains/operaciones/shared/chapter_detection/find_all_document_titles.py"
        },
        {
            "from": "domains/operaciones/scripts/eaf_workflows/eaf_processing/01_title_detection/interactive_title_detector.py",
            "to": "domains/operaciones/shared/chapter_detection/interactive_title_detector.py"
        },
        {
            "from": "domains/operaciones/scripts/eaf_workflows/eaf_processing/01_title_detection/analyze_title_patterns.py",
            "to": "domains/operaciones/shared/chapter_detection/analyze_title_patterns.py"
        },
        {
            "from": "domains/operaciones/docs/anexos_eaf/archive/legacy_files/chapter_definitions.json",
            "to": "domains/operaciones/shared/chapter_detection/eaf_chapter_definitions.json"
        }
    ]

    for move in moves:
        move_file_safely(move["from"], move["to"])

def move_schemas_and_utilities():
    """Move schema and utility files to shared"""

    moves = [
        # Universal schema system
        {
            "from": "domains/operaciones/schemas/extractor_universal_integrado.py",
            "to": "domains/operaciones/shared/utilities/extractor_universal_integrado.py"
        },
        {
            "from": "domains/operaciones/schemas/referencias_cruzadas.py",
            "to": "domains/operaciones/shared/utilities/referencias_cruzadas.py"
        },
        {
            "from": "domains/operaciones/schemas/esquema_universal_chileno.py",
            "to": "domains/operaciones/shared/utilities/esquema_universal_chileno.py"
        },
        {
            "from": "domains/operaciones/schemas/configuracion_esquema_universal.json",
            "to": "domains/operaciones/shared/schemas/configuracion_esquema_universal.json"
        }
    ]

    for move in moves:
        move_file_safely(move["from"], move["to"])

def move_patterns():
    """Move pattern files to chapter-specific locations"""

    moves = [
        # ANEXO 1 patterns
        {
            "from": "domains/operaciones/patterns/anexos_eaf/anexo_01_generation_programming",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_01/patterns",
            "type": "directory"
        },
        # ANEXO 2 patterns
        {
            "from": "domains/operaciones/patterns/anexos_eaf/anexo_02_real_generation",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_02/patterns",
            "type": "directory"
        },
        # Informe Diario patterns
        {
            "from": "domains/operaciones/patterns/anexos_eaf/informe_diario_day1",
            "to": "domains/operaciones/anexos_eaf/chapters/informe_diario/patterns",
            "type": "directory"
        }
    ]

    for move in moves:
        if move.get("type") == "directory":
            move_directory_safely(move["from"], move["to"])
        else:
            move_file_safely(move["from"], move["to"])

def move_validated_results():
    """Move validated results to shared"""

    moves = [
        {
            "from": "domains/operaciones/patterns/anexos_eaf/_shared/validated_titles.json",
            "to": "domains/operaciones/shared/validated_results/master_validated_titles.json"
        }
    ]

    for move in moves:
        move_file_safely(move["from"], move["to"])

def move_extractions():
    """Move existing extractions to chapter-specific data folders"""

    moves = [
        {
            "from": "domains/operaciones/extractions/anexos_eaf/anexo_01_generation_programming",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_01/data/extractions",
            "type": "directory"
        },
        {
            "from": "domains/operaciones/extractions/anexos_eaf/anexo_02_real_generation",
            "to": "domains/operaciones/anexos_eaf/chapters/anexo_02/data/extractions",
            "type": "directory"
        },
        {
            "from": "domains/operaciones/extractions/anexos_eaf/informe_diario_day1",
            "to": "domains/operaciones/anexos_eaf/chapters/informe_diario/data/extractions",
            "type": "directory"
        }
    ]

    for move in moves:
        if move.get("type") == "directory":
            move_directory_safely(move["from"], move["to"])

def move_file_safely(from_path: str, to_path: str):
    """Safely move a file, creating backup if target exists"""

    source = Path(from_path)
    target = Path(to_path)

    if not source.exists():
        print(f"⚠️ Source not found: {from_path}")
        return

    # Create target directory
    target.parent.mkdir(parents=True, exist_ok=True)

    # Backup if target exists
    if target.exists():
        backup = target.with_suffix(target.suffix + ".backup")
        shutil.move(str(target), str(backup))
        print(f"📦 Backed up existing file: {backup}")

    # Move file
    shutil.move(str(source), str(target))
    print(f"✅ Moved: {from_path} → {to_path}")

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
        source.rmdir()
    else:
        shutil.move(str(source), str(target))

    print(f"✅ Moved directory: {from_path} → {to_path}")

if __name__ == "__main__":
    print("🚀 Moving Files to New Hierarchical Structure")
    print("=" * 50)

    print("\n1️⃣ Creating directory structure...")
    create_new_directory_structure()

    print("\n2️⃣ Moving processors...")
    move_processors()

    print("\n3️⃣ Moving chapter detection...")
    move_chapter_detection()

    print("\n4️⃣ Moving schemas and utilities...")
    move_schemas_and_utilities()

    print("\n5️⃣ Moving patterns...")
    move_patterns()

    print("\n6️⃣ Moving validated results...")
    move_validated_results()

    print("\n7️⃣ Moving extractions...")
    move_extractions()

    print("\n✅ File movement completed!")
    print("🔧 Next step: Run fix_all_paths.py to update import paths")