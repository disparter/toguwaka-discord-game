#!/bin/bash

OUTPUT_FILE="combined.json"
LOG_FILE="invalid_jsons.log"

# Limpa arquivos anteriores
> "$OUTPUT_FILE"
> "$LOG_FILE"

echo "[" > "$OUTPUT_FILE"
FIRST=true

find . -type f -name "*.json" | while read -r file; do
    # Verifica se é JSON válido com jq
    if jq -e . "$file" > /dev/null 2>&1; then
        # Se não é o primeiro, adiciona vírgula
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            echo "," >> "$OUTPUT_FILE"
        fi

        jq -c . "$file" >> "$OUTPUT_FILE"
    else
        echo "❌ Arquivo inválido ignorado: $file" | tee -a "$LOG_FILE"
    fi
done

echo "]" >> "$OUTPUT_FILE"

echo "✅ JSON combinado gerado em: $OUTPUT_FILE"
echo "📄 Arquivos com erro (se houver): $LOG_FILE"
