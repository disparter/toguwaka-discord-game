#!/bin/bash

# Validar se o AWS CLI está instalado
if ! command -v aws &>/dev/null; then
    echo "AWS CLI não encontrado. Instale-o para usar este script."
    exit 1
fi

# Função para criar uma tabela no DynamoDB
function criar_tabela() {
    local TABLE_NAME=$1
    local ATTR_DEFINITIONS=$2
    local KEY_SCHEMA=$3
    local GSI_DEFINITIONS=$4

    echo "Criando a tabela '$TABLE_NAME' no DynamoDB..."

    if [ -z "$GSI_DEFINITIONS" ]; then
        # Criar tabela sem índices secundários globais
        aws dynamodb create-table \
            --table-name "$TABLE_NAME" \
            --attribute-definitions $ATTR_DEFINITIONS \
            --key-schema $KEY_SCHEMA \
            --billing-mode PAY_PER_REQUEST \
            --region us-east-1
    else
        # Criar tabela com índices secundários globais
        aws dynamodb create-table \
            --table-name "$TABLE_NAME" \
            --attribute-definitions $ATTR_DEFINITIONS \
            --key-schema $KEY_SCHEMA \
            --global-secondary-indexes $GSI_DEFINITIONS \
            --billing-mode PAY_PER_REQUEST \
            --region us-east-1
    fi

    if [ $? -eq 0 ]; then
        echo "Tabela '$TABLE_NAME' criada com sucesso!"
    else
        echo "Falha ao criar a tabela '$TABLE_NAME'. Verifique se já existe ou se há erros na configuração."
    fi
}

# Função para deletar uma tabela no DynamoDB
function deletar_tabela() {
    local TABLE_NAME=$1

    echo "Deletando a tabela '$TABLE_NAME' no DynamoDB..."

    aws dynamodb delete-table \
        --table-name "$TABLE_NAME" \
        --region us-east-1

    if [ $? -eq 0 ]; then
        echo "Tabela '$TABLE_NAME' deletada com sucesso!"
    else
        echo "Falha ao deletar a tabela '$TABLE_NAME'."
    fi
}

# Criar esquema de tabelas separadas (modelo antigo)
function setup_tabelas() {
    # Tabela principal dos jogadores
    criar_tabela "Jogadores" \
        "AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S" \
        "AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE"

    # Tabela para clubes (nome do clube como chave principal)
    criar_tabela "Clubes" \
        "AttributeName=NomeClube,AttributeType=S" \
        "AttributeName=NomeClube,KeyType=HASH"

    # Tabela de eventos e progressos no jogo
    criar_tabela "Eventos" \
        "AttributeName=EventoID,AttributeType=S AttributeName=Tipo,AttributeType=S" \
        "AttributeName=EventoID,KeyType=HASH AttributeName=Tipo,KeyType=RANGE"

    # Tabela do mercado de itens (compra e venda entre jogadores)
    criar_tabela "Mercado" \
        "AttributeName=ItemID,AttributeType=S AttributeName=VendedorID,AttributeType=S" \
        "AttributeName=ItemID,KeyType=HASH AttributeName=VendedorID,KeyType=RANGE"

    # Tabela do inventário dos jogadores
    criar_tabela "Inventario" \
        "AttributeName=JogadorID,AttributeType=S AttributeName=ItemID,AttributeType=S" \
        "AttributeName=JogadorID,KeyType=HASH AttributeName=ItemID,KeyType=RANGE"

    echo "Todas as tabelas foram configuradas!"
}

# Criar esquema de tabela única (novo modelo)
function setup_tabela_unica() {
    # Definição dos atributos
    local ATTR_DEFINITIONS='[
        {"AttributeName": "PK", "AttributeType": "S"},
        {"AttributeName": "SK", "AttributeType": "S"},
        {"AttributeName": "GSI1PK", "AttributeType": "S"},
        {"AttributeName": "GSI1SK", "AttributeType": "S"}
    ]'

    # Definição do esquema de chaves
    local KEY_SCHEMA='[
        {"AttributeName": "PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"}
    ]'

    # Definição dos índices secundários globais
    local GSI_DEFINITIONS='[
        {
            "IndexName": "GSI1",
            "KeySchema": [
                {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
            ],
            "Projection": {
                "ProjectionType": "ALL"
            }
        }
    ]'

    # Criar a tabela única
    criar_tabela "AcademiaTokugawa" "$ATTR_DEFINITIONS" "$KEY_SCHEMA" "$GSI_DEFINITIONS"

    echo "Tabela única 'AcademiaTokugawa' configurada com sucesso!"
}

# Opções do CLI
echo "Bem-vindo ao script de gestão das tabelas DynamoDB para a Academia Tokugawa!"
echo "Escolha uma opção abaixo:"
echo "1) Criar tabela única (novo modelo)"
echo "2) Criar tabelas separadas (modelo antigo)"
echo "3) Deletar tabela única (novo modelo)"
echo "4) Deletar tabelas separadas (modelo antigo)"
echo "5) Sair"
read -rp "Digite o número da opção desejada: " OPCAO

case $OPCAO in
    1)
        echo "Criando tabela única (novo modelo)..."
        setup_tabela_unica
        ;;
    2)
        echo "Criando tabelas separadas (modelo antigo)..."
        setup_tabelas
        ;;
    3)
        echo "Deletando tabela única (novo modelo)..."
        deletar_tabela "AcademiaTokugawa"
        ;;
    4)
        echo "Deletando tabelas separadas (modelo antigo)..."
        deletar_tabela "Jogadores"
        deletar_tabela "Clubes"
        deletar_tabela "Eventos"
        deletar_tabela "Mercado"
        deletar_tabela "Inventario"
        ;;
    5)
        echo "Saindo do script. Até logo!"
        exit 0
        ;;
    *)
        echo "Opção inválida. Tente novamente!"
        ;;
esac
