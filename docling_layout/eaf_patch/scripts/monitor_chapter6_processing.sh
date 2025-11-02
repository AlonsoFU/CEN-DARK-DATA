#!/bin/bash
# Monitor Chapter 6 processing progress

LOG_FILE="chapter6_universal_patch.log"

echo "=========================================="
echo "Chapter 6 Processing Monitor"
echo "=========================================="
echo

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "   Processing may not have started yet"
    exit 1
fi

echo "📄 Log file: $LOG_FILE"
echo

# Show latest output
echo "📊 Latest output:"
echo "----------------------------------------"
tail -20 "$LOG_FILE"
echo "----------------------------------------"
echo

# Count patches applied
echo "🐵 Patch activity:"
grep -c "\[PATCH\]" "$LOG_FILE" 2>/dev/null && echo " patch operations logged" || echo "No patch operations yet"

# Check for completion
if grep -q "PROCESSING COMPLETE" "$LOG_FILE" 2>/dev/null; then
    echo
    echo "✅ PROCESSING COMPLETE!"
    echo
    echo "📁 Check output directory:"
    echo "   capitulo_06/outputs_WITH_UNIVERSAL_PATCH/"
else
    echo
    echo "⏳ Still processing..."
    echo "   Use: tail -f $LOG_FILE"
    echo "   to monitor in real-time"
fi
