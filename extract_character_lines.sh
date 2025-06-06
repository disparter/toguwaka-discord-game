#!/bin/bash

# Diretório inicial para a busca
SEARCH_DIR="."
# Extensões possíveis para arquivos com diálogos
FILE_EXTENSIONS=("*.txt" "*.json" "*.yaml" "*.csv")
# Diretório de saída dos arquivos com falas (será criado automaticamente)
OUTPUT_DIR="./npc_dialogues"

# Função para converter nomes em snake_case
convert_to_snake_case() {
    local name="$1"
    # Converte o nome para letras minúsculas, substitui espaços por underlines e remove caracteres especiais
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed -r 's/[^a-z0-9]+/_/g' | sed -r 's/^_|_$//g'
}

# Cria o diretório de saída, se ainda não existir
mkdir -p "$OUTPUT_DIR"

echo "Buscando falas de NPCs nos arquivos do diretório: $SEARCH_DIR..."
echo "Arquivos gerados serão salvos em: $OUTPUT_DIR"
echo ""

# Itera por todas as extensões especificadas
for EXTENSION in "${FILE_EXTENSIONS[@]}"; do
    echo "Procurando em arquivos com extensão: $EXTENSION"

    # Busca todos os arquivos correspondentes à extensão
    find "$SEARCH_DIR" -type f -name "$EXTENSION" | while read -r FILE; do
        echo "Verificando falas no arquivo: $FILE"

        # Extraia falas de NPCs com "npc" como atributo e "text" como fala
        grep -Po '"npc":\s*"\K[^"]+' "$FILE" | sort -u | while read -r NPC_NAME; do
            SNAKE_CASE_NAME=$(convert_to_snake_case "$NPC_NAME")
            OUTPUT_FILE="$OUTPUT_DIR/${SNAKE_CASE_NAME}.txt"

            # Extrai todas as falas do NPC atual e salva no arquivo
            grep -Pzo '\{[^}]*"npc":\s*"'$NPC_NAME'"\s*,[^}]*\}' "$FILE" |
            grep -Po '"text":\s*"\K([^"]+)' >> "$OUTPUT_FILE"

            # Mensagem de status
            if [ -s "$OUTPUT_FILE" ]; then
                echo "Falas de '$NPC_NAME' encontradas e salvas em: $OUTPUT_FILE"
            fi
        done
    done
done

echo ""
echo "Extração concluída. Todas as falas foram organizadas no diretório: $OUTPUT_DIR"