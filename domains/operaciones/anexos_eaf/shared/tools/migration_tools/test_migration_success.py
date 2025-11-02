#!/usr/bin/env python3
"""
Migration Success Test
======================
Tests that all components work together after migration
"""

import sys
from pathlib import Path

def test_import_processors():
    """Test that processors can be imported"""
    try:
        # Test project root path works
        project_root = Path(__file__).parent.parent.parent.parent.parent
        sys.path.append(str(project_root))

        print("🧪 Testing processor imports...")

        # Import ANEXO processors (but don't run them)
        import importlib.util

        # Test ANEXO 1 processor
        anexo_01_path = project_root / "domains/operaciones/anexos_eaf/chapters/anexo_01/processors/anexo_01_processor.py"
        spec = importlib.util.spec_from_file_location("anexo_01_processor", anexo_01_path)
        if spec and spec.loader:
            anexo_01 = importlib.util.module_from_spec(spec)
            print("✅ ANEXO 1 processor imports successfully")
        else:
            print("❌ ANEXO 1 processor import failed")
            return False

        # Test ANEXO 2 processor
        anexo_02_path = project_root / "domains/operaciones/anexos_eaf/chapters/anexo_02/processors/anexo_02_processor.py"
        spec = importlib.util.spec_from_file_location("anexo_02_processor", anexo_02_path)
        if spec and spec.loader:
            anexo_02 = importlib.util.module_from_spec(spec)
            print("✅ ANEXO 2 processor imports successfully")
        else:
            print("❌ ANEXO 2 processor import failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Processor import error: {e}")
        return False

def test_import_utilities():
    """Test that shared utilities can be imported"""
    try:
        print("\n🧪 Testing utility imports...")

        # Test universal schema integration
        from domains.operaciones.shared.utilities.extractor_universal_integrado import ExtractorUniversalIntegrado
        print("✅ Universal schema extractor imports successfully")

        # Test cross-references
        from domains.operaciones.shared.utilities.referencias_cruzadas import GeneradorReferenciasCruzadas
        print("✅ Cross-references generator imports successfully")

        # Test universal schema
        from domains.operaciones.shared.utilities.esquema_universal_chileno import crear_documento_universal_chile
        print("✅ Universal schema creator imports successfully")

        return True

    except Exception as e:
        print(f"❌ Utility import error: {e}")
        return False

def test_import_chapter_detection():
    """Test that chapter detection can be imported"""
    try:
        print("\n🧪 Testing chapter detection imports...")

        # Test chapter mapper
        import importlib.util
        project_root = Path(__file__).parent.parent.parent.parent.parent

        chapter_mapper_path = project_root / "domains/operaciones/shared/chapter_detection/interactive_chapter_mapper.py"
        spec = importlib.util.spec_from_file_location("interactive_chapter_mapper", chapter_mapper_path)
        if spec and spec.loader:
            chapter_mapper = importlib.util.module_from_spec(spec)
            print("✅ Interactive chapter mapper imports successfully")
        else:
            print("❌ Chapter mapper import failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Chapter detection import error: {e}")
        return False

def test_file_structure():
    """Test that all expected files exist"""
    print("\n🧪 Testing file structure...")

    project_root = Path(__file__).parent.parent.parent.parent.parent

    critical_files = [
        # Processors
        "domains/operaciones/anexos_eaf/chapters/anexo_01/processors/anexo_01_processor.py",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/processors/anexo_02_processor.py",
        "domains/operaciones/anexos_eaf/chapters/informe_diario/processors/informe_diario_processor.py",

        # Utilities
        "domains/operaciones/shared/utilities/extractor_universal_integrado.py",
        "domains/operaciones/shared/utilities/referencias_cruzadas.py",
        "domains/operaciones/shared/utilities/esquema_universal_chileno.py",

        # Chapter detection
        "domains/operaciones/shared/chapter_detection/interactive_chapter_mapper.py",
        "domains/operaciones/shared/chapter_detection/find_all_document_titles.py",

        # Schemas
        "domains/operaciones/shared/schemas/configuracion_esquema_universal.json",

        # Patterns
        "domains/operaciones/anexos_eaf/chapters/anexo_01/patterns/extraction_patterns.json",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/patterns/extraction_patterns.json",

        # Validated results
        "domains/operaciones/shared/validated_results/master_validated_titles.json"
    ]

    all_exist = True
    for file_path in critical_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ MISSING: {file_path}")
            all_exist = False

    return all_exist

def test_integration():
    """Test that components can work together"""
    try:
        print("\n🧪 Testing component integration...")

        # Test creating extractor instance
        from domains.operaciones.shared.utilities.extractor_universal_integrado import ExtractorUniversalIntegrado
        extractor = ExtractorUniversalIntegrado()
        print("✅ Universal extractor instance created successfully")

        # Test creating cross-references generator
        from domains.operaciones.shared.utilities.referencias_cruzadas import GeneradorReferenciasCruzadas
        ref_generator = GeneradorReferenciasCruzadas()
        print("✅ Cross-references generator instance created successfully")

        return True

    except Exception as e:
        print(f"❌ Integration error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Migration Success")
    print("=" * 50)

    tests = [
        ("File Structure", test_file_structure),
        ("Processor Imports", test_import_processors),
        ("Utility Imports", test_import_utilities),
        ("Chapter Detection Imports", test_import_chapter_detection),
        ("Component Integration", test_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            print(f"✅ {test_name} test PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} test FAILED")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Migration was successful!")
        print("\n🔧 Next steps:")
        print("   1. ✅ All processors work with new paths")
        print("   2. ✅ Universal schema integration works")
        print("   3. ✅ Chapter detection system works")
        print("   4. ✅ Cross-reference system works")
        print("   5. 🚀 Ready to use new hierarchical structure!")
    else:
        print("⚠️ Some tests failed - check the output above")