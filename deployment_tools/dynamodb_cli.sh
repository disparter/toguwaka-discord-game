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

    echo "Criando a tabela '$TABLE_NAME' no DynamoDB..."

    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions $ATTR_DEFINITIONS \
        --key-schema $KEY_SCHEMA \
        --billing-mode PAY_PER_REQUEST \
        --region us-east-1

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

# Criar esquema de tabelas
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

# Opções do CLI
echo "Bem-vindo ao script de gestão das tabelas DynamoDB para a Academia Tokugawa!"
echo "Escolha uma opção abaixo:"
echo "1) Criar todas as tabelas necessárias"
echo "2) Deletar todas as tabelas"
echo "3) Sair"
read -rp "Digite o número da opção desejada: " OPCAO

case $OPCAO in
    1)
        echo "Criando todas as tabelas necessárias..."
        setup_tabelas
        ;;
    2)
        echo "Deletando todas as tabelas necessárias..."
        deletar_tabela "Jogadores"
        deletar_tabela "Clubes"
        deletar_tabela "Eventos"
        deletar_tabela "Mercado"
        deletar_tabela "Inventario"
        ;;
    3)
        echo "Saindo do script. Até logo!"
        exit 0
        ;;
    *)
        echo "Opção inválida. Tente novamente!"
        ;;
esac