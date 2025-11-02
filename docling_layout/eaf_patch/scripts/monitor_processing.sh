#!/bin/bash
# Monitor Chapter 6 processing progress

LOG_FILE="chapter6_processing.log"

echo "==================================================================="
echo "📊 CHAPTER 6 PROCESSING MONITOR"
echo "==================================================================="
echo ""

# Check if process is running
if pgrep -f "REPROCESS_chapter6_with_universal_patch.py" > /dev/null; then
    echo "✅ Processing is RUNNING"
    PID=$(pgrep -f "REPROCESS_chapter6_with_universal_patch.py")
    echo "   PID: $PID"
    echo ""
else
    echo "⚠️  Processing is NOT running"
    echo ""
fi

# Show log file size
if [ -f "$LOG_FILE" ]; then
    SIZE=$(du -h "$LOG_FILE" | cut -f1)
    LINES=$(wc -l < "$LOG_FILE")
    echo "📄 Log file: $SIZE ($LINES lines)"
    echo ""
fi

# Count patch executions (one per page)
if [ -f "$LOG_FILE" ]; then
    PAGES_PROCESSED=$(grep -c "🐵 \[PATCH\] Universal Fix with Direct PDF Extraction" "$LOG_FILE")
    echo "📑 Pages processed: $PAGES_PROCESSED / 94"
    echo ""
fi

# Show latest patch statistics
echo "🔍 Latest page statistics:"
echo "-------------------------------------------------------------------"
tail -30 "$LOG_FILE" | grep -E "(PATCH\]|✅|❌|📊)" | tail -20
echo ""

# Show completion status
if grep -q "✅ PROCESSING COMPLETE" "$LOG_FILE" 2>/dev/null; then
    echo "==================================================================="
    echo "🎉 PROCESSING COMPLETED!"
    echo "==================================================================="

    # Show final statistics
    echo ""
    grep -A 10 "📊 STATISTICS:" "$LOG_FILE" | tail -15

    echo ""
    echo "📁 Output files:"
    ls -lh ../capitulo_06/outputs_with_eaf_patch/ 2>/dev/null | grep -v "^total" | awk '{print "   " $9 " (" $5 ")"}'
else
    echo "⏳ Processing in progress..."
    echo ""
    echo "💡 Run this script again to check progress:"
    echo "   bash monitor_processing.sh"
fi

echo "==================================================================="
