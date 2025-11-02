#!/bin/bash
# Verify that Chapter 6 title "6. Normalización del servicio" was detected

echo "=========================================="
echo "🔍 VERIFYING CHAPTER 6 TITLE DETECTION"
echo "=========================================="
echo ""

JSON_FILE="capitulo_06/outputs/layout_WITH_PATCH.json"
PDF_FILE="capitulo_06/outputs/capitulo_06_annotated_WITH_PATCH.pdf"

if [ ! -f "$JSON_FILE" ]; then
    echo "❌ JSON file not found yet: $JSON_FILE"
    echo "⏳ Chapter 6 is still being processed..."
    exit 1
fi

echo "✅ JSON file exists: $JSON_FILE"
echo ""

# Check if the title exists in the JSON
if grep -q "Normalización del servicio" "$JSON_FILE"; then
    echo "✅ TITLE FOUND IN JSON!"
    echo ""
    echo "📄 Extracting title element..."
    jq '.elements[] | select(.text | contains("Normalización del servicio"))' "$JSON_FILE"
else
    echo "❌ TITLE NOT FOUND IN JSON"
    echo "   The title '6. Normalización del servicio' is missing from extraction"
fi

echo ""
echo "=========================================="
echo "📊 CHAPTER 6 STATISTICS"
echo "=========================================="

# Total elements
total=$(jq '.total_elements' "$JSON_FILE")
echo "Total elements: $total"

# Elements by type on page 1
echo ""
echo "Page 1 elements:"
jq '.elements[] | select(.page == 1) | "\(.type): \(.text[:50])"' "$JSON_FILE" -r | head -10

# Check if PDF exists
echo ""
if [ -f "$PDF_FILE" ]; then
    echo "✅ Annotated PDF ready: $PDF_FILE"
    echo "   Size: $(ls -lh "$PDF_FILE" | awk '{print $5}')"
    echo ""
    echo "🎨 You can now view the PDF to see the cluster boxes!"
    echo "   Open: $PDF_FILE"
else
    echo "⏳ Annotated PDF not ready yet"
fi

echo "=========================================="
