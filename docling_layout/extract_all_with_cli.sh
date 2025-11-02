#!/bin/bash
# Extract all chapters using docling CLI
# Much faster than Python API for batch processing

set -e

# Paths
VENV="/home/alonso/Documentos/Github/Proyecto Dark Data CEN/venv"
PDF_SOURCE="/home/alonso/Documentos/Github/Proyecto Dark Data CEN/domains/operaciones/eaf/shared/source/EAF-089-2025.pdf"
BASE_DIR="/home/alonso/Documentos/Github/Proyecto Dark Data CEN/shared_platform/utils/outputs/docling_layout"

# Chapter definitions (name:start-end)
declare -A CHAPTERS
CHAPTERS[01]="Descripción_de_la_Perturbación:1-11"
CHAPTERS[02]="Equipamiento_Afectado:12-90"
CHAPTERS[03]="Energía_No_Suministrada:91-153"
CHAPTERS[04]="Configuraciones_de_Falla:154-159"
CHAPTERS[05]="Cronología_de_Eventos:160-171"
CHAPTERS[06]="Normalización_del_Servicio:172-265"
CHAPTERS[07]="Análisis_de_Causas_de_Falla:266-347"
CHAPTERS[08]="Detalle_de_Información:348-348"
CHAPTERS[09]="Análisis_de_Protecciones:349-381"
CHAPTERS[10]="Pronunciamiento_Técnico:382-392"
CHAPTERS[11]="Recomendaciones:393-399"

echo "================================================================================"
echo "🚀 DOCLING CLI BATCH EXTRACTION - All Chapters"
echo "================================================================================"
echo ""
echo "📄 Source PDF: EAF-089-2025.pdf"
echo "📁 Output base: $BASE_DIR"
echo "🔧 Using venv: $VENV"
echo ""

# Activate venv
source "$VENV/bin/activate"

echo "✅ Virtual environment activated"
echo ""

# Process each chapter
SUCCESS=0
TOTAL=${#CHAPTERS[@]}

for CHAPTER_NUM in $(echo "${!CHAPTERS[@]}" | tr ' ' '\n' | sort); do
    INFO="${CHAPTERS[$CHAPTER_NUM]}"
    NAME=$(echo "$INFO" | cut -d: -f1)
    PAGES=$(echo "$INFO" | cut -d: -f2)
    START=$(echo "$PAGES" | cut -d- -f1)
    END=$(echo "$PAGES" | cut -d- -f2)

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📖 Chapter $CHAPTER_NUM: $NAME (pages $START-$END)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Create output directory
    OUTPUT_DIR="$BASE_DIR/capitulo_$CHAPTER_NUM"
    mkdir -p "$OUTPUT_DIR/outputs"
    mkdir -p "$OUTPUT_DIR/scripts"

    # Check if already processed
    if [ -f "$OUTPUT_DIR/outputs/layout_lightweight.json" ]; then
        echo "   ⏭️  Already processed, skipping..."
        echo ""
        ((SUCCESS++))
        continue
    fi

    # Run docling extraction
    echo "   🔍 Extracting with docling CLI..."

    # Docling CLI command with options
    docling "$PDF_SOURCE" \
        --from "$START" \
        --to "$END" \
        --output "$OUTPUT_DIR/outputs" \
        --output-format json \
        --ocr=off \
        --table-mode=fast \
        > "$OUTPUT_DIR/outputs/extraction_cli.log" 2>&1

    if [ $? -eq 0 ]; then
        # Rename output file to standard name
        JSON_FILE=$(find "$OUTPUT_DIR/outputs" -name "*.json" -type f | head -1)
        if [ -n "$JSON_FILE" ] && [ "$JSON_FILE" != "$OUTPUT_DIR/outputs/layout_lightweight.json" ]; then
            mv "$JSON_FILE" "$OUTPUT_DIR/outputs/layout_lightweight.json"
        fi

        echo "   ✅ Extraction complete"
        ((SUCCESS++))
    else
        echo "   ❌ Extraction failed (see extraction_cli.log)"
    fi

    echo ""
done

echo "================================================================================"
echo "✅ BATCH EXTRACTION COMPLETE"
echo "================================================================================"
echo "📊 Processed: $SUCCESS/$TOTAL chapters"
echo ""
echo "📁 Output directories created:"
for CHAPTER_NUM in $(echo "${!CHAPTERS[@]}" | tr ' ' '\n' | sort); do
    echo "   • capitulo_$CHAPTER_NUM/"
done
echo ""
