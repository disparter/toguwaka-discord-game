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
   echo "$name" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g' | sed -E 's/^_|_$//g'
}

# Cria o diretório de saída, se ainda não existir
mkdir -p "$OUTPUT_DIR"

echo "Buscando falas de NPCs nos arquivos do diretório: $SEARCH_DIR..."
echo "Arquivos gerados serão salvos em: $OUTPUT_DIR"
echo ""

# Itera por todas as extensões especificadas
for EXTENSION in "${FILE_EXTENSIONS[@]}"; do
   echo "Procurando nos arquivos com extensão: $EXTENSION"

   find "$SEARCH_DIR" -type f -name "$EXTENSION" | while read -r FILE; do
       echo "Verificando falas no arquivo: $FILE"

       # Extrai os NPCs encontrados no arquivo (baseado no campo "npc")
       grep -o '"npc"[[:space:]]*:[[:space:]]*"[^"]*"' "$FILE" | sed -E 's/"npc"[[:space:]]*:[[:space:]]*"([^"]*)"/\1/' | sort -u | while read -r NPC_NAME; do
           # Converte o nome do NPC para snake_case
           SNAKE_CASE_NAME=$(convert_to_snake_case "$NPC_NAME")
           OUTPUT_FILE="$OUTPUT_DIR/${SNAKE_CASE_NAME}.txt"

           # Extrai todas as falas do NPC atual e salva no arquivo (baseado no campo "text")
           grep -E '"npc"[[:space:]]*:[[:space:]]*"'$NPC_NAME'".*?"text"[[:space:]]*:[[:space:]]*"' "$FILE" | \
           grep -o '"text"[[:space:]]*:[[:space:]]*"[^"]*"' | \
           sed -E 's/"text"[[:space:]]*:[[:space:]]*"([^"]*)"/\1/' >> "$OUTPUT_FILE"

           # Mensagem de status
           if [ -s "$OUTPUT_FILE" ]; then
               echo "Falas de '$NPC_NAME' encontradas e salvas em: $OUTPUT_FILE"
           else
               rm -f "$OUTPUT_FILE" # Remove arquivos vazios
           fi
       done
   done
done

echo ""
echo "Extração concluída. Todas as falas foram organizadas no diretório: $OUTPUT_DIR"