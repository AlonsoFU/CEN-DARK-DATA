#!/bin/bash
# Extract all chapters (1-11) with EAF patch and standard colors

cd /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/shared_platform/utils/outputs/docling_layout
source /home/alonso/Documentos/Github/Proyecto\ Dark\ Data\ CEN/venv/bin/activate

echo "=========================================="
echo "EXTRACTING ALL CHAPTERS WITH EAF PATCH"
echo "=========================================="
echo ""

for chapter in {1..11}; do
    echo "=========================================="
    echo "Processing Chapter $chapter..."
    echo "=========================================="

    python3 UNIVERSAL_extract_any_chapter.py $chapter

    if [ $? -eq 0 ]; then
        echo "✅ Chapter $chapter complete"
    else
        echo "❌ Chapter $chapter failed"
    fi

    echo ""
done

echo "=========================================="
echo "ALL CHAPTERS PROCESSED"
echo "=========================================="
