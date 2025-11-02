#!/bin/bash
# Quick progress checker for batch reprocessing

echo "=========================================="
echo "📊 BATCH REPROCESSING PROGRESS"
echo "=========================================="
echo ""

# Check which chapters have outputs
echo "✅ Chapters completed:"
for i in {01..11}; do
    json_file="capitulo_$i/outputs/layout_WITH_PATCH.json"
    pdf_file="capitulo_$i/outputs/capitulo_${i}_annotated_WITH_PATCH.pdf"

    if [ -f "$json_file" ] && [ -f "$pdf_file" ]; then
        # Get element count from JSON
        elements=$(jq '.total_elements' "$json_file" 2>/dev/null || echo "?")
        duration=$(jq '.extraction_time_minutes' "$json_file" 2>/dev/null || echo "?")
        echo "  ✓ Chapter $i: $elements elements (${duration} min)"
    fi
done

echo ""
echo "⏳ Chapters pending:"
for i in {01..11}; do
    json_file="capitulo_$i/outputs/layout_WITH_PATCH.json"
    pdf_file="capitulo_$i/outputs/capitulo_${i}_annotated_WITH_PATCH.pdf"

    if [ ! -f "$json_file" ] || [ ! -f "$pdf_file" ]; then
        echo "  ⌛ Chapter $i"
    fi
done

echo ""
echo "=========================================="

# Check if process is still running
if pgrep -f "COMPLETE_REPROCESS_ALL_CHAPTERS.py" > /dev/null; then
    echo "🔄 Batch processing is RUNNING"
    echo ""
    echo "Monitor live output:"
    echo "  tail -f reprocess_log.txt"
else
    echo "✅ Batch processing COMPLETED or NOT RUNNING"
    echo ""
    echo "Check final summary:"
    echo "  cat COMPLETE_REPROCESS_SUMMARY.json"
fi

echo "=========================================="
