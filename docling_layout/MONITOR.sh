#!/bin/bash
# Monitor Docling extraction processes

echo "════════════════════════════════════════════════════════════════════════"
echo "  DOCLING EXTRACTION MONITOR"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Check running processes
echo "📊 RUNNING PROCESSES:"
echo "────────────────────────────────────────────────────────────────────────"
ps aux | grep -E "(docling_layout_extractor|quick_extract|test_docling_api)" | grep -v grep | \
  awk '{printf "  %-30s | PID: %-7s | Time: %-8s | CPU: %s%% | Mem: %s%%\n", $11, $2, $10, $3, $4}'
echo ""

# Check log files
echo "📁 LOG FILES:"
echo "────────────────────────────────────────────────────────────────────────"
cd capitulo_01/scripts/ 2>/dev/null || cd shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/

for log in extraction.log quick_extract.log test_api.log; do
  if [ -f "$log" ]; then
    lines=$(wc -l < "$log")
    size=$(du -h "$log" | cut -f1)
    last_update=$(stat -c %y "$log" 2>/dev/null | cut -d'.' -f1 || stat -f "%Sm" "$log" 2>/dev/null)
    echo "  $log: $lines lines, $size, updated: $last_update"
    echo "    └─ Last 2 lines:"
    tail -2 "$log" | sed 's/^/       /'
    echo ""
  fi
done

echo "────────────────────────────────────────────────────────────────────────"
echo "💡 Commands:"
echo "  Watch test API log:  tail -f capitulo_01/scripts/test_api.log"
echo "  Kill all processes:  pkill -f 'docling_layout|quick_extract|test_docling'"
echo "  Re-run monitor:      bash MONITOR.sh"
echo "════════════════════════════════════════════════════════════════════════"
