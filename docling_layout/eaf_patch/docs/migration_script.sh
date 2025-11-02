#!/bin/bash
# EAF Patch Migration Script
# Created: 2025-10-21
# Purpose: Automated migration from power_line_patch to eaf_patch
# Run from: shared_platform/utils/outputs/docling_layout

set -e  # Exit on error

echo "🚀 Starting EAF Patch Migration..."
echo ""

# Verify we're in the correct directory
if [ ! -d "power_line_patch" ]; then
    echo "❌ Error: power_line_patch directory not found"
    echo "   Please run this script from: shared_platform/utils/outputs/docling_layout"
    exit 1
fi

# Step 1: Create backup
echo "📦 Step 1/9: Creating backup..."
cp -r power_line_patch power_line_patch.backup
git add . && git commit -m "Pre-migration: before eaf_patch rename" || echo "   (No git changes to commit)"
echo "   ✅ Backup created at: power_line_patch.backup"
echo ""

# Step 2: Rename main directory
echo "📁 Step 2/9: Renaming main directory..."
mv power_line_patch eaf_patch
echo "   ✅ Renamed: power_line_patch → eaf_patch"
echo ""

# Step 3: Create new structure
echo "🏗️  Step 3/9: Creating new directory structure..."
cd eaf_patch
mkdir -p core domain examples
echo "   ✅ Created: core/, domain/, examples/"
echo ""

# Step 4: Move files
echo "📝 Step 4/9: Moving and renaming files..."

# Core files
if [ -f "scripts/universal_patch_with_pdf_extraction.py" ]; then
    mv scripts/universal_patch_with_pdf_extraction.py core/eaf_patch_engine.py
    echo "   ✅ Moved: universal_patch_with_pdf_extraction.py → core/eaf_patch_engine.py"
fi

if [ -f "scripts/missing_title_detector.py" ]; then
    mv scripts/missing_title_detector.py core/eaf_title_detector.py
    echo "   ✅ Moved: missing_title_detector.py → core/eaf_title_detector.py"
fi

if [ -f "scripts/page_number_detector.py" ]; then
    mv scripts/page_number_detector.py core/eaf_page_detector.py
    echo "   ✅ Moved: page_number_detector.py → core/eaf_page_detector.py"
fi

# Domain files
if [ -f "scripts/power_line_classifier.py" ]; then
    mv scripts/power_line_classifier.py domain/
    echo "   ✅ Moved: power_line_classifier.py → domain/"
fi

echo ""

# Step 5: Rename documentation
echo "📚 Step 5/9: Renaming documentation..."
cd docs

if [ -f "PATCH_IMPROVEMENTS_CATALOG.md" ]; then
    mv PATCH_IMPROVEMENTS_CATALOG.md EAF_PATCH_CATALOG.md
    echo "   ✅ Renamed: PATCH_IMPROVEMENTS_CATALOG.md → EAF_PATCH_CATALOG.md"
fi

if [ -f "POWER_LINE_PATCH_README.md" ]; then
    mv POWER_LINE_PATCH_README.md EAF_PATCH_README.md
    echo "   ✅ Renamed: POWER_LINE_PATCH_README.md → EAF_PATCH_README.md"
fi

cd ..
echo ""

# Step 6: Clean up empty scripts directory
echo "🧹 Step 6/9: Cleaning up..."
if [ -d "scripts" ]; then
    rmdir scripts 2>/dev/null && echo "   ✅ Removed empty scripts/ directory" || echo "   ⚠️  scripts/ not empty, keeping for now"
fi
echo ""

# Step 7: Update import statements in core files
echo "🔧 Step 7/9: Updating import statements..."

# Update eaf_patch_engine.py imports
if [ -f "core/eaf_patch_engine.py" ]; then
    sed -i 's/from missing_title_detector/from eaf_patch.core.eaf_title_detector/g' core/eaf_patch_engine.py
    sed -i 's/from power_line_classifier/from eaf_patch.domain.power_line_classifier/g' core/eaf_patch_engine.py
    sed -i 's/from page_number_detector/from eaf_patch.core.eaf_page_detector/g' core/eaf_patch_engine.py
    sed -i 's/MissingTitleDetector/EAFTitleDetector/g' core/eaf_patch_engine.py
    sed -i 's/PageNumberDetector/EAFPageDetector/g' core/eaf_patch_engine.py
    echo "   ✅ Updated imports in: eaf_patch_engine.py"
fi

# Update class names
if [ -f "core/eaf_title_detector.py" ]; then
    sed -i 's/class MissingTitleDetector/class EAFTitleDetector/g' core/eaf_title_detector.py
    echo "   ✅ Updated class name: MissingTitleDetector → EAFTitleDetector"
fi

if [ -f "core/eaf_page_detector.py" ]; then
    sed -i 's/class PageNumberDetector/class EAFPageDetector/g' core/eaf_page_detector.py
    echo "   ✅ Updated class name: PageNumberDetector → EAFPageDetector"
fi

echo ""

# Step 8: Update documentation references
echo "📖 Step 8/9: Updating documentation references..."
cd docs

# Update all markdown files
for file in *.md; do
    if [ -f "$file" ]; then
        sed -i 's/power_line_patch/eaf_patch/g' "$file"
        sed -i 's/universal_patch_with_pdf_extraction/eaf_patch_engine/g' "$file"
        sed -i 's/apply_universal_patch_with_pdf/apply_eaf_patch/g' "$file"
        sed -i 's/MissingTitleDetector/EAFTitleDetector/g' "$file"
        sed -i 's/PageNumberDetector/EAFPageDetector/g' "$file"
        sed -i 's/Universal Patch/EAF Patch/g' "$file"
        sed -i 's/universal patch/EAF patch/g' "$file"
        echo "   ✅ Updated: $file"
    fi
done

cd ..
echo ""

# Step 9: Update chapter output directories
echo "📂 Step 9/9: Updating chapter output directories..."
cd ../..

# Rename chapter output directories
for dir in capitulo_*/outputs_WITH_UNIVERSAL_PATCH; do
    if [ -d "$dir" ]; then
        new_dir="${dir%outputs_WITH_UNIVERSAL_PATCH}outputs_with_eaf_patch"
        mv "$dir" "$new_dir" 2>/dev/null && echo "   ✅ Renamed: $dir → $new_dir" || true
    fi
done

echo ""
echo "✅ Migration Complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Test the patch:"
echo "      cd eaf_patch"
echo "      python core/eaf_title_detector.py"
echo "      python core/eaf_page_detector.py"
echo ""
echo "   2. Update processing scripts to use new imports:"
echo "      from eaf_patch.core.eaf_patch_engine import apply_eaf_patch"
echo ""
echo "   3. Delete backup when satisfied:"
echo "      rm -rf power_line_patch.backup"
echo ""
echo "   4. Commit changes:"
echo "      git add ."
echo "      git commit -m \"Migrate power_line_patch → eaf_patch\""
echo ""
echo "🔄 To rollback:"
echo "   rm -rf eaf_patch"
echo "   mv power_line_patch.backup power_line_patch"
echo ""
