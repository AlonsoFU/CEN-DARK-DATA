#!/bin/bash
# Monitor Docling sequential extraction progress

echo "================================"
echo "📊 DOCLING EXTRACTION MONITOR"
echo "================================"
echo

# GPU Status
echo "🖥️  GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader
echo

# Check which chapters are completed
echo "✅ Completed Chapters:"
for i in {1..11}; do
    json_file="capitulo_$(printf '%02d' $i)/outputs/layout_lightweight.json"
    if [ -f "$json_file" ]; then
        elements=$(jq '.metadata.total_elements' "$json_file" 2>/dev/null || echo "?")
        echo "   Chapter $i: $elements elements"
    fi
done
echo

# Latest log output
echo "📜 Latest Log Output (last 15 lines):"
echo "----------------------------------------"
tail -15 docling_sequential.log 2>/dev/null || echo "No log file yet"
echo

# Process status
echo "🔍 Process Status:"
if pgrep -f "process_sequential.py" > /dev/null; then
    echo "   ✅ Extraction is RUNNING"
    echo "   PID: $(pgrep -f 'process_sequential.py')"
else
    echo "   ⏹️  Extraction is NOT running"
fi
echo

echo "💡 TIP: Run this script periodically to check progress"
echo "   ./monitor_extraction.sh"
echo
