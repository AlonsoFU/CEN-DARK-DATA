#!/usr/bin/env python3
"""
Data Structure Test
===================
Tests that processors can find data in new structure
"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

def test_anexos_eaf_data_structure():
    """Test that ANEXOS EAF data structure is correct"""
    print("🧪 Testing ANEXOS EAF data structure...")

    base_path = Path("domains/operaciones/anexos_eaf")

    expected_paths = [
        # EAF-level data
        base_path / "data/source_documents",
        base_path / "data/samples_and_tests",
        base_path / "data/consolidated_extractions",

        # Chapter-specific data
        base_path / "chapters/anexo_01/data/extractions",
        base_path / "chapters/anexo_01/data/documentation",
        base_path / "chapters/anexo_02/data/extractions",
        base_path / "chapters/anexo_02/data/documentation",
        base_path / "chapters/informe_diario/data/extractions",
        base_path / "chapters/informe_diario/data/documentation"
    ]

    all_exist = True
    for path in expected_paths:
        if path.exists():
            print(f"✅ {path}")
        else:
            print(f"❌ MISSING: {path}")
            all_exist = False

    return all_exist

def test_shared_data_structure():
    """Test that shared data structure is correct"""
    print("\n🧪 Testing shared data structure...")

    base_path = Path("domains/operaciones/shared")

    expected_paths = [
        # Shared data for future document types
        base_path / "data/compliance_reports",
        base_path / "data/failure_reports",
        base_path / "data/maintenance_logs",

        # Scraped data
        base_path / "scrapers/scraped_data/coordinador_cl",
        base_path / "scrapers/scraped_data/web_data",
        base_path / "scrapers/scraped_data/document_data"
    ]

    all_exist = True
    for path in expected_paths:
        if path.exists():
            print(f"✅ {path}")
        else:
            print(f"❌ MISSING: {path}")
            all_exist = False

    return all_exist

def test_processor_data_paths():
    """Test that processors can find data in new locations"""
    print("\n🧪 Testing processor data paths...")

    # Test paths that processors would look for
    test_paths = [
        # Where processors look for source documents
        "domains/operaciones/anexos_eaf/data/source_documents",
        "domains/operaciones/anexos_eaf/data/samples_and_tests",

        # Where processors store extractions
        "domains/operaciones/anexos_eaf/chapters/anexo_01/data/extractions",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/data/extractions"
    ]

    all_exist = True
    for path_str in test_paths:
        path = Path(path_str)
        if path.exists():
            print(f"✅ Processor can access: {path_str}")
        else:
            print(f"❌ Processor CANNOT access: {path_str}")
            all_exist = False

    return all_exist

def test_data_content_preservation():
    """Test that existing data was preserved during migration"""
    print("\n🧪 Testing data content preservation...")

    # Check that extractions were preserved
    anexo_01_extractions = Path("domains/operaciones/anexos_eaf/chapters/anexo_01/data/extractions")
    anexo_02_extractions = Path("domains/operaciones/anexos_eaf/chapters/anexo_02/data/extractions")

    preservation_results = []

    if anexo_01_extractions.exists():
        anexo_01_files = list(anexo_01_extractions.glob("*.json"))
        print(f"✅ ANEXO 1 extractions preserved: {len(anexo_01_files)} files")
        preservation_results.append(len(anexo_01_files) > 0)
    else:
        print("❌ ANEXO 1 extractions directory missing")
        preservation_results.append(False)

    if anexo_02_extractions.exists():
        anexo_02_files = list(anexo_02_extractions.glob("*.json"))
        print(f"✅ ANEXO 2 extractions preserved: {len(anexo_02_files)} files")
        preservation_results.append(len(anexo_02_files) > 0)
    else:
        print("❌ ANEXO 2 extractions directory missing")
        preservation_results.append(False)

    return all(preservation_results)

def test_documentation_access():
    """Test that documentation is accessible in new locations"""
    print("\n🧪 Testing documentation access...")

    doc_paths = [
        "domains/operaciones/data/README.md",  # New documentation
        "domains/operaciones/anexos_eaf/chapters/anexo_01/data/documentation",
        "domains/operaciones/anexos_eaf/chapters/anexo_02/data/documentation"
    ]

    all_exist = True
    for path_str in doc_paths:
        path = Path(path_str)
        if path.exists():
            print(f"✅ Documentation accessible: {path_str}")
        else:
            print(f"❌ Documentation missing: {path_str}")
            all_exist = False

    return all_exist

if __name__ == "__main__":
    print("🚀 Testing Data Structure After Reorganization")
    print("=" * 60)

    tests = [
        ("ANEXOS EAF Data Structure", test_anexos_eaf_data_structure),
        ("Shared Data Structure", test_shared_data_structure),
        ("Processor Data Paths", test_processor_data_paths),
        ("Data Content Preservation", test_data_content_preservation),
        ("Documentation Access", test_documentation_access)
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
        print("🎉 ALL DATA STRUCTURE TESTS PASSED!")
        print("\n🔧 Data structure successfully reorganized:")
        print("   1. ✅ ANEXOS EAF data aligned with processing structure")
        print("   2. ✅ Chapter-specific data in chapter folders")
        print("   3. ✅ Shared data for cross-domain document types")
        print("   4. ✅ Existing extractions preserved")
        print("   5. ✅ Documentation accessible")
        print("   6. 🚀 Ready for hierarchical processing!")
    else:
        print("⚠️ Some tests failed - check the output above")